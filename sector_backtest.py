# ==============================================================================
# MODULE: MOMENTUMSYS SECTOR + STOCK TIME MACHINE & BACKTEST (sector_backtest.py)
# ==============================================================================
import json
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ------------------------------------------------------------------------------
# 1. WEEKLY DATA LOADER, IPO GATE & 22-DAY (O==C==H OR O==C==L) CIRCUIT FILTER
# ------------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def build_weekly_master_data(_raw_ohlc, sectors_json, cache_ts_key):
    """
    Builds both Sector-Level and Stock-Level weekly matrices:
    - Enforces strict Friday Close cutoff (drops any incomplete in-progress week).
    - 52-week IPO history gate (stock must have >=52w history and >=40 valid bars).
    - 22-Day Circuit Filter: counts days in last 22 trading days where the stock
      was locked at one price all day: (Open == Close == High) OR (Open == Close == Low).
      Passes if count <= 6, fails if count > 6.
    - Computes weekly Close-to-Close, Friday-to-Monday Gap, and Monday-to-Friday Intra returns.
    """
    sectors_dict = json.loads(sectors_json)

    daily_close_raw = _raw_ohlc["Close"].dropna(how="all")
    daily_open_raw = _raw_ohlc["Open"].reindex(daily_close_raw.index).fillna(daily_close_raw)
    daily_high_raw = _raw_ohlc["High"].reindex(daily_close_raw.index).fillna(daily_close_raw)
    daily_low_raw = _raw_ohlc["Low"].reindex(daily_close_raw.index).fillna(daily_close_raw)

    # Strict Completed-Friday Cutoff: never include an in-progress Mon-Thu week
    last_daily_dt = daily_close_raw.index.max()
    if last_daily_dt.weekday() < 4:  # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri
        days_since_fri = (last_daily_dt.weekday() - 4) % 7
        strict_friday_cutoff = last_daily_dt - pd.Timedelta(days=days_since_fri)
        daily_close_raw = daily_close_raw.loc[:strict_friday_cutoff]
        daily_open_raw = daily_open_raw.loc[:strict_friday_cutoff]
        daily_high_raw = daily_high_raw.loc[:strict_friday_cutoff]
        daily_low_raw = daily_low_raw.loc[:strict_friday_cutoff]

    # 22-Trading-Day Circuit Filter BEFORE forward-filling holidays:
    # A day counts as a circuit day only if locked at one price all day:
    # (Open == Close == High) OR (Open == Close == Low) on valid trading days
    valid_day = daily_close_raw.notna()
    open_eq_close = np.isclose(daily_open_raw, daily_close_raw, rtol=1e-5, atol=1e-4)
    close_eq_high = np.isclose(daily_close_raw, daily_high_raw, rtol=1e-5, atol=1e-4)
    open_eq_high = np.isclose(daily_open_raw, daily_high_raw, rtol=1e-5, atol=1e-4)
    close_eq_low = np.isclose(daily_close_raw, daily_low_raw, rtol=1e-5, atol=1e-4)
    open_eq_low = np.isclose(daily_open_raw, daily_low_raw, rtol=1e-5, atol=1e-4)

    locked_high = open_eq_close & close_eq_high & open_eq_high
    locked_low = open_eq_close & close_eq_low & open_eq_low
    circuit_day = (locked_high | locked_low) & valid_day
    bad_days_22d = (
        pd.DataFrame(circuit_day, index=daily_close_raw.index, columns=daily_close_raw.columns)
        .astype(float)
        .rolling(22, min_periods=1)
        .sum()
    )

    # Forward-fill short holiday gaps up to 5 days for weekly resampling
    daily_close = daily_close_raw.ffill(limit=5)
    daily_open = daily_open_raw.ffill(limit=5).fillna(daily_close)

    w_close = daily_close.resample("W-FRI").last().dropna(how="all")
    w_open = daily_open.resample("W-FRI").first().reindex(w_close.index).fillna(w_close)
    w_bad_days_22d = bad_days_22d.resample("W-FRI").last().reindex(w_close.index).fillna(0.0)

    # Stock-level weekly return matrices
    prev_c = w_close.shift(1)
    stk_ret_cc = (w_close / prev_c) - 1.0
    stk_ret_gap = (w_open / prev_c) - 1.0
    stk_ret_intra = (w_close / w_open) - 1.0

    # 52-Week IPO History Gate & Outlier Protection
    stk_ret_52w = (w_close / w_close.shift(52)) - 1.0
    stk_ret_26w = (w_close / w_close.shift(26)) - 1.0
    valid_weeks_52 = w_close.notna().rolling(52, min_periods=40).sum() >= 40
    valid_return_bounds = (stk_ret_cc <= 1.0) & (stk_ret_cc >= -0.80)

    stk_ipo_eligible = (
        w_close.notna()
        & prev_c.notna()
        & stk_ret_52w.notna()
        & valid_weeks_52
        & valid_return_bounds
    )

    # Entry Filter for Stocks: IPO Eligible + <= 6 circuit days in 22 trading days
    stk_entry_filter_ok = stk_ipo_eligible & (w_bad_days_22d <= 6.0)

    # Clean stock return matrices for index chaining & stock simulation
    ret_cc_clean = stk_ret_cc.where(stk_ipo_eligible)
    ret_gap_clean = stk_ret_gap.where(stk_ipo_eligible).clip(-0.50, 0.50)
    ret_intra_clean = stk_ret_intra.where(stk_ipo_eligible).clip(-0.80, 1.0)
    pos_52w_clean = (stk_ret_52w > 0.0).astype(float).where(stk_ipo_eligible)

    weeks = w_close.index
    sector_names = list(sectors_dict.keys())

    sec_close_idx = pd.DataFrame(index=weeks, columns=sector_names, dtype=float)
    sec_ret_cc = pd.DataFrame(index=weeks, columns=sector_names, dtype=float)
    sec_ret_gap = pd.DataFrame(index=weeks, columns=sector_names, dtype=float)
    sec_ret_intra = pd.DataFrame(index=weeks, columns=sector_names, dtype=float)
    sec_breadth = pd.DataFrame(index=weeks, columns=sector_names, dtype=float)
    sec_active_cnt = pd.DataFrame(index=weeks, columns=sector_names, dtype=int)
    sec_peer_median_52w = pd.DataFrame(index=weeks, columns=sector_names, dtype=float)

    for sec, tickers in sectors_dict.items():
        cols = [t for t in tickers if t in ret_cc_clean.columns]
        if not cols:
            continue

        r_cc = ret_cc_clean[cols].mean(axis=1)
        r_gap = ret_gap_clean[cols].mean(axis=1)
        r_in = ret_intra_clean[cols].mean(axis=1)
        brd = pos_52w_clean[cols].mean(axis=1)
        cnt = stk_ipo_eligible[cols].sum(axis=1).astype(int)
        peer_med = stk_ret_52w.where(stk_ipo_eligible)[cols].median(axis=1)

        first_valid = r_cc.first_valid_index()
        if first_valid is not None:
            r_cc_filled = r_cc.loc[first_valid:].fillna(0.0)
            idx_series = 100.0 * (1.0 + r_cc_filled).cumprod()
            sec_close_idx.loc[idx_series.index, sec] = idx_series

        sec_ret_cc[sec] = r_cc
        sec_ret_gap[sec] = r_gap
        sec_ret_intra[sec] = r_in
        sec_breadth[sec] = brd
        sec_active_cnt[sec] = cnt
        sec_peer_median_52w[sec] = peer_med

    # Full Universe Equal-Weight Composite Index
    uni_r_cc = ret_cc_clean.mean(axis=1)
    first_u = uni_r_cc.first_valid_index()
    uni_close_idx = pd.Series(index=weeks, dtype=float)
    if first_u is not None:
        uni_close_idx.loc[first_u:] = 100.0 * (1.0 + uni_r_cc.loc[first_u:].fillna(0.0)).cumprod()

    non_empty_idx = sec_close_idx.dropna(how="all").index
    valid_start = non_empty_idx.min() if len(non_empty_idx) > 0 else weeks[0]

    return {
        "close_idx": sec_close_idx.loc[valid_start:],
        "ret_cc": sec_ret_cc.loc[valid_start:],
        "ret_gap": sec_ret_gap.loc[valid_start:],
        "ret_intra": sec_ret_intra.loc[valid_start:],
        "breadth": sec_breadth.loc[valid_start:],
        "active_cnt": sec_active_cnt.loc[valid_start:],
        "peer_median_52w": sec_peer_median_52w.loc[valid_start:],
        "universe_idx": uni_close_idx.loc[valid_start:],
        "universe_ret_cc": uni_r_cc.loc[valid_start:],
        # Stock-level weekly matrices
        "stk_close": w_close.loc[valid_start:],
        "stk_open": w_open.loc[valid_start:],
        "stk_ret_cc": ret_cc_clean.loc[valid_start:],
        "stk_ret_gap": ret_gap_clean.loc[valid_start:],
        "stk_ret_intra": ret_intra_clean.loc[valid_start:],
        "stk_ret_52w": stk_ret_52w.where(stk_ipo_eligible).loc[valid_start:],
        "stk_ret_26w": stk_ret_26w.where(stk_ipo_eligible).loc[valid_start:],
        "stk_ipo_eligible": stk_ipo_eligible.loc[valid_start:],
        "stk_entry_filter_ok": stk_entry_filter_ok.loc[valid_start:],
        "stk_bad_days_22d": w_bad_days_22d.loc[valid_start:]
    }


# ------------------------------------------------------------------------------
# 2. VECTORIZED SECTOR SCORER (100 PTS) & STOCK SCORER (RESCALED 100 PTS)
# ------------------------------------------------------------------------------
def compute_wilder_rsi(close_df, period=14):
    """Computes standard Wilder RSI across all columns simultaneously."""
    delta = close_df.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    return 100.0 - (100.0 / (1.0 + rs))


def compute_sector_scores(weekly_data, rsi_period=14, rsi_ma_period=20):
    """Computes all 7 binary sector conditions (100 pts) and weekly sector ranks."""
    close_idx = weekly_data["close_idx"]
    breadth = weekly_data["breadth"]

    ret_52w = (close_idx / close_idx.shift(52)) - 1.0
    ret_26w = (close_idx / close_idx.shift(26)) - 1.0
    median_52w = ret_52w.median(axis=1)

    c1_rel_ret = ret_52w.gt(median_52w, axis=0).astype(float) * 10.0

    rsi = compute_wilder_rsi(close_idx, period=rsi_period)
    c2_rsi_60 = (rsi > 60.0).astype(float) * 20.0

    rsi_ma = rsi.rolling(rsi_ma_period, min_periods=rsi_ma_period).mean()
    c3_rsi_above_ma = (rsi > rsi_ma).astype(float) * 10.0

    rsi_gap = rsi - rsi_ma
    gap_rising_1w = (rsi_gap > rsi_gap.shift(1)).fillna(False)
    c4_gap_4w = (
        gap_rising_1w
        & gap_rising_1w.shift(1, fill_value=False)
        & gap_rising_1w.shift(2, fill_value=False)
        & gap_rising_1w.shift(3, fill_value=False)
    ).astype(float) * 10.0

    c5_breadth = (breadth >= 0.50).astype(float) * 20.0

    high_52w = close_idx.rolling(52, min_periods=52).max()
    is_new_high = ((close_idx >= high_52w) & high_52w.notna()).astype(float)
    c6_recent_high = (is_new_high.rolling(7, min_periods=1).max() > 0.0).astype(float) * 15.0
    c7_near_high = ((close_idx >= 0.90 * high_52w) & high_52w.notna()).astype(float) * 15.0

    valid_sector_mask = ret_52w.notna()
    total_score = (
        c1_rel_ret + c2_rsi_60 + c3_rsi_above_ma + c4_gap_4w
        + c5_breadth + c6_recent_high + c7_near_high
    ).where(valid_sector_mask, np.nan)

    tie_breaker = ret_26w.rank(axis=1, ascending=True, pct=True).fillna(0.0) * 0.01
    weekly_rank = (total_score + tie_breaker).rank(axis=1, ascending=False, method="min")

    return {
        "score": total_score,
        "rank": weekly_rank,
        "ret_52w": ret_52w,
        "ret_26w": ret_26w,
        "median_52w": median_52w,
        "rsi": rsi,
        "rsi_ma": rsi_ma,
        "c1_rel_ret": c1_rel_ret,
        "c2_rsi_60": c2_rsi_60,
        "c3_rsi_above_ma": c3_rsi_above_ma,
        "c4_gap_4w": c4_gap_4w,
        "c5_breadth": c5_breadth,
        "c6_recent_high": c6_recent_high,
        "c7_near_high": c7_near_high
    }


@st.cache_data(ttl=3600, show_spinner=False)
def compute_stock_indicators(_weekly_data, cache_ts_key, rsi_period=14, rsi_ma_period=20):
    """
    Precomputes stock-level technical indicators and the 5 sector-independent
    score components (out of 87.5 pts). The 6th component (12.5 pts: Stock 52w
    return > Sector Peer Median) is added dynamically per sector.
    Stock Weights (Rescaled 80 -> 100 via x1.25):
      - C1 (Peer Rel 52w Return): 12.5 pts
      - C2 (RSI > 60):            25.0 pts
      - C3 (RSI > RSI-MA):        12.5 pts
      - C4 (RSI Gap Rising 4w):   12.5 pts
      - C5 (New 52w High in 7w):  18.75 pts
      - C6 (Close >= 90% 52w Hi): 18.75 pts
    Stock Exit Rule (ONLY stock exit):
      - RSI < RSI-MA AND RSI < 50 on Friday close.
    """
    stk_close = _weekly_data["stk_close"]
    stk_elig = _weekly_data["stk_ipo_eligible"]

    rsi = compute_wilder_rsi(stk_close, period=rsi_period)
    rsi_ma = rsi.rolling(rsi_ma_period, min_periods=rsi_ma_period).mean()
    rsi_gap = rsi - rsi_ma

    c2_rsi_60 = (rsi > 60.0).astype(float) * 25.0
    c3_rsi_above_ma = (rsi > rsi_ma).astype(float) * 12.5

    gap_rising_1w = (rsi_gap > rsi_gap.shift(1)).fillna(False)
    c4_gap_4w = (
        gap_rising_1w
        & gap_rising_1w.shift(1, fill_value=False)
        & gap_rising_1w.shift(2, fill_value=False)
        & gap_rising_1w.shift(3, fill_value=False)
    ).astype(float) * 12.5

    high_52w = stk_close.rolling(52, min_periods=40).max()
    is_new_high = ((stk_close >= high_52w) & high_52w.notna()).astype(float)
    c5_recent_high = (is_new_high.rolling(7, min_periods=1).max() > 0.0).astype(float) * 18.75
    c6_near_high = ((stk_close >= 0.90 * high_52w) & high_52w.notna()).astype(float) * 18.75

    base_score_875 = (
        c2_rsi_60 + c3_rsi_above_ma + c4_gap_4w + c5_recent_high + c6_near_high
    ).where(stk_elig, np.nan)

    # Stock-level exit condition: RSI < RSI-MA AND RSI < 50 (NO 10-week low anywhere)
    stk_exit_signal = (rsi < rsi_ma) & (rsi < 50.0)

    return {
        "rsi": rsi,
        "rsi_ma": rsi_ma,
        "rsi_gap": rsi_gap,
        "high_52w": high_52w,
        "c2_rsi_60": c2_rsi_60,
        "c3_rsi_above_ma": c3_rsi_above_ma,
        "c4_gap_4w": c4_gap_4w,
        "c5_recent_high": c5_recent_high,
        "c6_near_high": c6_near_high,
        "base_score_875": base_score_875,
        "stk_exit_signal": stk_exit_signal
    }


def score_stocks_in_sector_at_week(
    sec_name,
    dt_sig,
    sectors_dict,
    weekly_data,
    stk_ind
):
    """
    Computes the exact 100-point Stock Score & 6-component breakdown for all
    constituents of `sec_name` as of Friday close `dt_sig`.
    """
    tickers = [t for t in sectors_dict.get(sec_name, []) if t in weekly_data["stk_close"].columns]
    if not tickers:
        return pd.DataFrame()

    elig_s = weekly_data["stk_ipo_eligible"].loc[dt_sig, tickers]
    entry_ok_s = weekly_data["stk_entry_filter_ok"].loc[dt_sig, tickers]
    bad_days_s = weekly_data["stk_bad_days_22d"].loc[dt_sig, tickers]
    ret_52w_s = weekly_data["stk_ret_52w"].loc[dt_sig, tickers]
    ret_26w_s = weekly_data["stk_ret_26w"].loc[dt_sig, tickers]
    close_s = weekly_data["stk_close"].loc[dt_sig, tickers]
    high52_s = stk_ind["high_52w"].loc[dt_sig, tickers]

    peer_med = weekly_data["peer_median_52w"].loc[dt_sig, sec_name]
    c1_pts = ((ret_52w_s > peer_med) & elig_s & pd.notna(peer_med)).astype(float) * 12.5

    c2_pts = stk_ind["c2_rsi_60"].loc[dt_sig, tickers]
    c3_pts = stk_ind["c3_rsi_above_ma"].loc[dt_sig, tickers]
    c4_pts = stk_ind["c4_gap_4w"].loc[dt_sig, tickers]
    c5_pts = stk_ind["c5_recent_high"].loc[dt_sig, tickers]
    c6_pts = stk_ind["c6_near_high"].loc[dt_sig, tickers]

    tot_score = (c1_pts + c2_pts + c3_pts + c4_pts + c5_pts + c6_pts).where(elig_s, np.nan)
    rsi_s = stk_ind["rsi"].loc[dt_sig, tickers]
    rsi_ma_s = stk_ind["rsi_ma"].loc[dt_sig, tickers]
    exit_sig_s = stk_ind["stk_exit_signal"].loc[dt_sig, tickers]

    df = pd.DataFrame({
        "Ticker": tickers,
        "Sector": sec_name,
        "IPO_Eligible": elig_s.values,
        "Circuit_OK (<=6/22D)": (bad_days_s.values <= 6.0),
        "Bad_Days_22D": bad_days_s.values.astype(int),
        "Entry_Filter_OK": entry_ok_s.values,
        "Stock_Score": tot_score.values,
        "C1_Rel_52W (12.5)": c1_pts.values,
        "C2_RSI>60 (25)": c2_pts.values,
        "C3_RSI>MA (12.5)": c3_pts.values,
        "C4_Gap_4W (12.5)": c4_pts.values,
        "C5_NewHi_7W (18.75)": c5_pts.values,
        "C6_NearHi_10% (18.75)": c6_pts.values,
        "52W_Ret (%)": (ret_52w_s.values * 100.0).round(2),
        "Peer_Median_52W (%)": round(float(peer_med * 100.0), 2) if pd.notna(peer_med) else np.nan,
        "26W_Ret (%)": (ret_26w_s.values * 100.0).round(2),
        "RSI(14)": rsi_s.values.round(2),
        "RSI_MA(20)": rsi_ma_s.values.round(2),
        "RSI_Gap": (rsi_s.values - rsi_ma_s.values).round(2),
        "Close": close_s.values.round(2),
        "Pct_From_52W_High (%)": (((close_s.values / high52_s.values) - 1.0) * 100.0).round(2),
        "Exit_Signal (RSI<MA & <50)": exit_sig_s.values,
        "_ret26_raw": ret_26w_s.fillna(-999.0).values
    })

    df = df.sort_values(
        by=["Entry_Filter_OK", "Stock_Score", "_ret26_raw"],
        ascending=[False, False, False]
    ).reset_index(drop=True)
    return df


# ------------------------------------------------------------------------------
# 3. SECTOR-ONLY PORTFOLIO ENGINE (4 SLOTS)
# ------------------------------------------------------------------------------
def run_portfolio_backtest(
    weekly_data,
    score_bundle,
    regime_series=None,
    entry_threshold=75.0,
    exit_threshold=50.0,
    num_slots=4,
    initial_capital=1_000_000.0,
    round_trip_cost=0.0025,
    cash_rate_annual=0.06,
    start_date=None,
    end_date=None
):
    """Runs the 4-slot Sector Index backtest."""
    scores = score_bundle["score"]
    ranks = score_bundle["rank"]
    ret_26w = score_bundle["ret_26w"]

    ret_cc = weekly_data["ret_cc"]
    ret_gap = weekly_data["ret_gap"]
    ret_intra = weekly_data["ret_intra"]

    valid_weeks = scores.dropna(thresh=10).index
    if start_date is not None:
        valid_weeks = valid_weeks[valid_weeks >= pd.Timestamp(start_date)]
    if end_date is not None:
        valid_weeks = valid_weeks[valid_weeks <= pd.Timestamp(end_date)]

    if len(valid_weeks) < 2:
        return None

    one_way_cost = round_trip_cost / 2.0
    weekly_cash_ret = (1.0 + cash_rate_annual) ** (1.0 / 52.0) - 1.0

    if regime_series is not None and not regime_series.dropna().empty:
        reg_aligned = regime_series.reindex(weekly_data["close_idx"].index).ffill()
        reg_ma40 = reg_aligned.rolling(40, min_periods=40).mean()
        regime_bullish = (reg_aligned > reg_ma40).reindex(valid_weeks).fillna(True)
    else:
        regime_bullish = pd.Series(True, index=valid_weeks)

    slot_cap = [initial_capital / float(num_slots) for _ in range(num_slots)]
    slot_sec = [None for _ in range(num_slots)]
    slot_entry_dt = [None for _ in range(num_slots)]
    slot_entry_cap = [0.0 for _ in range(num_slots)]

    equity_records = []
    trade_log = []
    total_turnover_notional = 0.0

    equity_records.append({
        "Date": valid_weeks[0],
        "Total_Equity": initial_capital,
        "Active_Slots": 0,
        "Cash_Pct": 100.0,
        "Held_Sectors": "100% Cash",
        "Regime_Bullish": bool(regime_bullish.iloc[0])
    })

    for idx in range(len(valid_weeks) - 1):
        dt_sig = valid_weeks[idx]
        dt_prev = valid_weeks[idx - 1] if idx > 0 else dt_sig
        dt_next = valid_weeks[idx + 1]

        sc_t = scores.loc[dt_sig]
        sc_prev = scores.loc[dt_prev]
        rk_t = ranks.loc[dt_sig]
        r26_t = ret_26w.loc[dt_sig]
        is_bull = bool(regime_bullish.loc[dt_sig])

        exiting_slots = []
        staying_slots = []

        for s in range(num_slots):
            sec = slot_sec[s]
            if sec is None:
                continue
            cur_sc = sc_t.get(sec, np.nan)
            prv_sc = sc_prev.get(sec, np.nan)
            cur_rk = rk_t.get(sec, 999.0)

            cond_2w_below_50 = bool(pd.notna(cur_sc) and pd.notna(prv_sc) and (cur_sc < exit_threshold) and (prv_sc < exit_threshold))
            cond_grey_zone = bool(pd.notna(cur_sc) and (cur_rk > num_slots) and (cur_sc < entry_threshold))

            if pd.isna(cur_sc) or cond_2w_below_50 or cond_grey_zone:
                exiting_slots.append((s, sec, "2w < 50" if cond_2w_below_50 else "Rank > 4 & Score < 75"))
            else:
                staying_slots.append(s)

        for s in staying_slots:
            sec = slot_sec[s]
            r_week = ret_cc.loc[dt_next, sec]
            if pd.notna(r_week):
                slot_cap[s] *= (1.0 + float(r_week))

        for s, old_sec, reason in exiting_slots:
            gap_r = ret_gap.loc[dt_next, old_sec]
            if pd.notna(gap_r):
                slot_cap[s] *= (1.0 + float(gap_r))
            slot_cap[s] *= (1.0 - one_way_cost)
            total_turnover_notional += slot_cap[s]

            hold_weeks = int(round((dt_next - slot_entry_dt[s]).days / 7.0))
            trade_ret = ((slot_cap[s] / slot_entry_cap[s]) - 1.0) * 100.0 if slot_entry_cap[s] > 0 else 0.0
            trade_log.append({
                "Slot": s + 1,
                "Sector": old_sec,
                "Entry_Week_Close": str(slot_entry_dt[s].date()),
                "Exit_Week_Close": str(dt_sig.date()),
                "Holding_Weeks": max(1, hold_weeks),
                "Entry_Capital": round(slot_entry_cap[s], 2),
                "Exit_Capital": round(slot_cap[s], 2),
                "Return_Pct": round(trade_ret, 2),
                "Exit_Reason": reason
            })
            slot_sec[s] = None
            slot_entry_dt[s] = None
            slot_entry_cap[s] = 0.0

        open_slots = [s for s in range(num_slots) if slot_sec[s] is None]
        currently_held = {slot_sec[s] for s in range(num_slots) if slot_sec[s] is not None}

        if open_slots and is_bull:
            candidates = []
            for sec in sc_t.index:
                if sec not in currently_held and pd.notna(sc_t[sec]) and sc_t[sec] >= entry_threshold:
                    r26_val = r26_t.get(sec, np.nan)
                    r26_clean = float(r26_val) if pd.notna(r26_val) else -999.0
                    candidates.append((sec, float(sc_t[sec]), r26_clean))
            candidates.sort(key=lambda x: (x[1], x[2]), reverse=True)

            for s, (new_sec, _, _) in zip(open_slots, candidates):
                slot_entry_cap[s] = slot_cap[s]
                slot_entry_dt[s] = dt_sig
                slot_sec[s] = new_sec
                slot_cap[s] *= (1.0 - one_way_cost)
                total_turnover_notional += slot_cap[s]
                in_r = ret_intra.loc[dt_next, new_sec]
                if pd.notna(in_r):
                    slot_cap[s] *= (1.0 + float(in_r))

        for s in range(num_slots):
            if slot_sec[s] is None:
                slot_cap[s] *= (1.0 + weekly_cash_ret)

        tot_eq = float(sum(slot_cap))
        active_cnt = sum(1 for x in slot_sec if x is not None)
        cash_cap = sum(slot_cap[s] for s in range(num_slots) if slot_sec[s] is None)
        cash_pct = (cash_cap / tot_eq) * 100.0 if tot_eq > 0 else 100.0
        held_names = [slot_sec[s].split(".")[1].strip() if "." in slot_sec[s] else slot_sec[s]
                      for s in range(num_slots) if slot_sec[s] is not None]

        equity_records.append({
            "Date": dt_next,
            "Total_Equity": tot_eq,
            "Active_Slots": active_cnt,
            "Cash_Pct": round(cash_pct, 1),
            "Held_Sectors": " | ".join(held_names) if held_names else "100% Cash",
            "Regime_Bullish": is_bull
        })

    eq_df = pd.DataFrame(equity_records).set_index("Date")
    trades_df = pd.DataFrame(trade_log)
    metrics = compute_performance_metrics(eq_df, trades_df, total_turnover_notional, cash_rate_annual)
    return {"equity_df": eq_df, "trades_df": trades_df, "metrics": metrics}


# ------------------------------------------------------------------------------
# 4. STOCK-LEVEL PORTFOLIO & TIME MACHINE ENGINE (4x3 = 12 SLOTS, 6M REBALANCE)
# ------------------------------------------------------------------------------
def run_stock_portfolio_and_timemachine(
    weekly_data,
    sec_score_bundle,
    stk_ind,
    sectors_dict,
    regime_series=None,
    sec_entry_th=75.0,
    sec_exit_th=50.0,
    stk_entry_th=75.0,
    num_sectors=4,
    stocks_per_sector=3,
    rebalance_weeks=26,
    initial_capital=1_000_000.0,
    round_trip_cost=0.0025,
    cash_rate_annual=0.06,
    start_date=None,
    end_date=None
):
    """
    Runs the complete Top-Down Sector + Stock Strategy AND records every single
    week's portfolio state for the Time Machine:
    - 4 Sector Slots x 3 Stock Sub-Slots = 12 Independent Stock Slots.
    - Stock Exits (Evaluated Friday Close t, Executed Monday Open t+1):
        1) Parent Sector Exits -> all held stocks in that sector exit immediately.
        2) Stock RSI < RSI-MA AND RSI < 50 on Friday close.
        (Zero 10-week low rules anywhere).
    - Open Sub-Slots in active sectors are filled at Monday Open t+1 by the
      highest-ranked unheld qualifying stocks (Score >= 75, IPO + <=6/22 circuit OK),
      with strict deduplication across all 12 slots.
    - Every 26 weeks (6 months), total portfolio capital is re-equalized across
      all 12 slots at Monday Open (charging one-way cost only on the net delta).
    """
    sec_scores = sec_score_bundle["score"]
    sec_ranks = sec_score_bundle["rank"]
    sec_ret26 = sec_score_bundle["ret_26w"]

    stk_ret_cc = weekly_data["stk_ret_cc"]
    stk_ret_gap = weekly_data["stk_ret_gap"]
    stk_ret_intra = weekly_data["stk_ret_intra"]

    valid_weeks = sec_scores.dropna(thresh=10).index
    if start_date is not None:
        valid_weeks = valid_weeks[valid_weeks >= pd.Timestamp(start_date)]
    if end_date is not None:
        valid_weeks = valid_weeks[valid_weeks <= pd.Timestamp(end_date)]

    if len(valid_weeks) < 2:
        return None

    total_slots = num_sectors * stocks_per_sector
    one_way_cost = round_trip_cost / 2.0
    weekly_cash_ret = (1.0 + cash_rate_annual) ** (1.0 / 52.0) - 1.0

    if regime_series is not None and not regime_series.dropna().empty:
        reg_aligned = regime_series.reindex(weekly_data["close_idx"].index).ffill()
        reg_ma40 = reg_aligned.rolling(40, min_periods=40).mean()
        regime_bullish = (reg_aligned > reg_ma40).reindex(valid_weeks).fillna(True)
    else:
        regime_bullish = pd.Series(True, index=valid_weeks)

    # State variables:
    # 4 sector slots, each owning 3 stock sub-slots (indexed s*3 + k)
    sec_slots = [None for _ in range(num_sectors)]
    sub_cap = [initial_capital / float(total_slots) for _ in range(total_slots)]
    sub_tk = [None for _ in range(total_slots)]
    sub_entry_dt = [None for _ in range(total_slots)]
    sub_entry_cap = [0.0 for _ in range(total_slots)]

    equity_records = []
    stock_trade_log = []
    weekly_snapshots = {}
    ledger_rows = []
    total_turnover_notional = 0.0

    equity_records.append({
        "Date": valid_weeks[0],
        "Total_Equity": initial_capital,
        "Active_Slots": 0,
        "Cash_Pct": 100.0,
        "Held_Stocks": "100% Cash",
        "Regime_Bullish": bool(regime_bullish.iloc[0])
    })

    # Loop across every signal Friday (including the final Friday for Live Mode!)
    for idx in range(len(valid_weeks)):
        dt_sig = valid_weeks[idx]
        dt_prev = valid_weeks[idx - 1] if idx > 0 else dt_sig
        has_next_week = (idx < len(valid_weeks) - 1)
        dt_next = valid_weeks[idx + 1] if has_next_week else None

        sc_t = sec_scores.loc[dt_sig]
        sc_prev = sec_scores.loc[dt_prev]
        rk_t = sec_ranks.loc[dt_sig]
        r26_t = sec_ret26.loc[dt_sig]
        is_bull = bool(regime_bullish.loc[dt_sig])

        # Snapshot holdings BEFORE Friday close signal evaluation
        holdings_before = [
            {
                "Global_Slot": g + 1,
                "Sector_Slot": (g // stocks_per_sector) + 1,
                "Sub_Slot": (g % stocks_per_sector) + 1,
                "Sector": sec_slots[g // stocks_per_sector],
                "Ticker": sub_tk[g],
                "Capital_Fri_Close": round(sub_cap[g], 2),
                "Entry_Friday": str(sub_entry_dt[g].date()) if sub_entry_dt[g] is not None else "—"
            }
            for g in range(total_slots)
        ]

        # ------------------------------------------------------------------
        # A. EVALUATE SECTOR EXITS & ENTRIES AT FRIDAY CLOSE dt_sig
        # ------------------------------------------------------------------
        sec_exits_this_week = {}
        for s in range(num_sectors):
            sec = sec_slots[s]
            if sec is None:
                continue
            cur_sc = sc_t.get(sec, np.nan)
            prv_sc = sc_prev.get(sec, np.nan)
            cur_rk = rk_t.get(sec, 999.0)

            cond_2w_50 = bool(pd.notna(cur_sc) and pd.notna(prv_sc) and (cur_sc < sec_exit_th) and (prv_sc < sec_exit_th))
            cond_grey = bool(pd.notna(cur_sc) and (cur_rk > num_sectors) and (cur_sc < sec_entry_th))
            if pd.isna(cur_sc) or cond_2w_50 or cond_grey:
                reason = "Parent Sector < 50 (2w)" if cond_2w_50 else "Parent Sector Rank > 4 & Score < 75"
                sec_exits_this_week[s] = (sec, reason)
                sec_slots[s] = None

        open_sec_slots = [s for s in range(num_sectors) if sec_slots[s] is None]
        held_secs_now = {sec_slots[s] for s in range(num_sectors) if sec_slots[s] is not None}
        sec_entries_this_week = {}

        if open_sec_slots and is_bull:
            sec_cands = []
            for sec in sc_t.index:
                if sec not in held_secs_now and pd.notna(sc_t[sec]) and sc_t[sec] >= sec_entry_th:
                    r26_v = r26_t.get(sec, np.nan)
                    sec_cands.append((sec, float(sc_t[sec]), float(r26_v) if pd.notna(r26_v) else -999.0))
            sec_cands.sort(key=lambda x: (x[1], x[2]), reverse=True)
            for s, (new_sec, _, _) in zip(open_sec_slots, sec_cands):
                sec_slots[s] = new_sec
                sec_entries_this_week[s] = new_sec

        # ------------------------------------------------------------------
        # B. EVALUATE STOCK EXITS AT FRIDAY CLOSE dt_sig
        # ------------------------------------------------------------------
        exiting_sub_slots = []  # (g, old_tk, old_sec, reason)
        staying_sub_slots = []

        for g in range(total_slots):
            s = g // stocks_per_sector
            tk = sub_tk[g]
            if tk is None:
                continue

            # Trigger 1: Did the parent sector exit this week?
            if s in sec_exits_this_week:
                old_sec, sec_reason = sec_exits_this_week[s]
                exiting_sub_slots.append((g, tk, old_sec, f"Parent Sector Exited ({sec_reason})"))
                continue

            # Trigger 2: Stock RSI < RSI-MA AND RSI < 50 on Friday close
            cur_sec = sec_slots[s]
            stk_exit_now = bool(stk_ind["stk_exit_signal"].loc[dt_sig].get(tk, False))
            stk_close_now = weekly_data["stk_close"].loc[dt_sig].get(tk, np.nan)

            if pd.isna(stk_close_now) or stk_exit_now:
                rsi_v = stk_ind["rsi"].loc[dt_sig].get(tk, np.nan)
                rma_v = stk_ind["rsi_ma"].loc[dt_sig].get(tk, np.nan)
                reason_str = (
                    f"Stock RSI ({rsi_v:.1f}) < RSI-MA ({rma_v:.1f}) & RSI < 50"
                    if stk_exit_now else "Missing Price Data"
                )
                exiting_sub_slots.append((g, tk, cur_sec, reason_str))
            else:
                staying_sub_slots.append(g)

        # Mark exited sub-slots as empty so open sub-slots can be filled for Monday Open
        exited_tk_map = {}
        for g, old_tk, old_sec, reason in exiting_sub_slots:
            exited_tk_map[g] = (old_tk, old_sec, reason, sub_entry_dt[g], sub_entry_cap[g])
            sub_tk[g] = None

        # ------------------------------------------------------------------
        # C. SCORE ALL ACTIVE SECTORS & FILL OPEN SUB-SLOTS FOR MONDAY OPEN
        # ------------------------------------------------------------------
        already_held_tickers = {sub_tk[g] for g in range(total_slots) if sub_tk[g] is not None}
        entering_sub_slots = []  # (g, new_tk, sec_name, score_val, r26_val)
        sector_stock_tables = {}
        qualified_excluded_rows = []
        near_miss_rows = []

        # Process active sectors in order of their current weekly sector rank
        active_s_indices = [s for s in range(num_sectors) if sec_slots[s] is not None]
        active_s_indices.sort(key=lambda s: float(rk_t.get(sec_slots[s], 999.0)))

        for s in active_s_indices:
            sec_name = sec_slots[s]
            sec_df = score_stocks_in_sector_at_week(sec_name, dt_sig, sectors_dict, weekly_data, stk_ind)
            sector_stock_tables[sec_name] = sec_df
            if sec_df.empty:
                continue

            sub_indices = [s * stocks_per_sector + k for k in range(stocks_per_sector)]
            open_subs = [g for g in sub_indices if sub_tk[g] is None]
            held_in_sec = {sub_tk[g] for g in sub_indices if sub_tk[g] is not None}

            # Qualifying stocks in this sector (Entry Filter OK & Score >= stk_entry_th)
            qual_df = sec_df[sec_df["Entry_Filter_OK"] & (sec_df["Stock_Score"] >= stk_entry_th)].copy()

            selected_this_sec = set(held_in_sec)
            if open_subs and is_bull and not qual_df.empty:
                avail_df = qual_df[~qual_df["Ticker"].isin(already_held_tickers)]
                for g, (_, row) in zip(open_subs, avail_df.iterrows()):
                    new_tk = row["Ticker"]
                    sub_tk[g] = new_tk
                    already_held_tickers.add(new_tk)
                    selected_this_sec.add(new_tk)
                    entering_sub_slots.append((
                        g, new_tk, sec_name, float(row["Stock_Score"]), float(row["26W_Ret (%)"])
                    ))

            # Build Qualified-But-Excluded list (scored >= stk_entry_th, Entry Filter OK, but missed top 3)
            if not qual_df.empty:
                cutoff_score = qual_df["Stock_Score"].iloc[min(len(qual_df) - 1, stocks_per_sector - 1)]
                cutoff_r26 = qual_df["26W_Ret (%)"].iloc[min(len(qual_df) - 1, stocks_per_sector - 1)]
                for _, row in qual_df.iterrows():
                    if row["Ticker"] not in selected_this_sec:
                        qualified_excluded_rows.append({
                            "Sector": sec_name,
                            "Ticker": row["Ticker"],
                            "Stock_Score": row["Stock_Score"],
                            "26W_Ret (%)": row["26W_Ret (%)"],
                            "Score_Gap_to_Top3": round(float(row["Stock_Score"] - cutoff_score), 2),
                            "26W_Ret_Gap_to_Top3 (%)": round(float(row["26W_Ret (%)"] - cutoff_r26), 2),
                            "Reason_Excluded": "Held in another sector" if row["Ticker"] in already_held_tickers else "Missed Top-3 Sector Cutoff / Tie-break"
                        })

            # Build Near-Miss list (62.5 <= Score < stk_entry_th or failed circuit filter with Score >= stk_entry_th)
            nm_df = sec_df[
                ((sec_df["Stock_Score"] >= 62.5) & (sec_df["Stock_Score"] < stk_entry_th))
                | ((sec_df["Stock_Score"] >= stk_entry_th) & (~sec_df["Entry_Filter_OK"]))
            ]
            for _, row in nm_df.iterrows():
                near_miss_rows.append({
                    "Sector": sec_name,
                    "Ticker": row["Ticker"],
                    "Stock_Score": row["Stock_Score"],
                    "Points_Short_of_75": round(max(0.0, float(stk_entry_th - row["Stock_Score"])), 2),
                    "Circuit_OK (<=6/22D)": row["Circuit_OK (<=6/22D)"],
                    "Bad_Days_22D": row["Bad_Days_22D"],
                    "RSI(14)": row["RSI(14)"],
                    "26W_Ret (%)": row["26W_Ret (%)"]
                })

        # Build Exit-Warning Watchlist for stocks staying in the portfolio
        exit_warning_rows = []
        for g in range(total_slots):
            tk = sub_tk[g]
            if tk is None:
                continue
            s = g // stocks_per_sector
            sec_name = sec_slots[s]
            rsi_v = float(stk_ind["rsi"].loc[dt_sig].get(tk, np.nan))
            rma_v = float(stk_ind["rsi_ma"].loc[dt_sig].get(tk, np.nan))
            gap_v = rsi_v - rma_v
            sec_sc_v = float(sc_t.get(sec_name, np.nan))

            # Flag if RSI is within 5 pts of 50 (RSI < 55) or RSI-Gap < +3.0 or Sector Score < 60
            if (rsi_v < 55.0) or (gap_v < 3.0) or (sec_sc_v < 60.0):
                warn_reasons = []
                if rsi_v < 55.0:
                    warn_reasons.append(f"RSI near 50 ({rsi_v:.1f})")
                if gap_v < 3.0:
                    warn_reasons.append(f"RSI near RSI-MA (Gap {gap_v:+.1f})")
                if sec_sc_v < 60.0:
                    warn_reasons.append(f"Parent Sector Score Low ({sec_sc_v:.0f})")
                exit_warning_rows.append({
                    "Global_Slot": g + 1,
                    "Sector": sec_name,
                    "Ticker": tk,
                    "Stock_RSI(14)": round(rsi_v, 2),
                    "Stock_RSI_MA(20)": round(rma_v, 2),
                    "RSI_minus_MA": round(gap_v, 2),
                    "Parent_Sector_Score": round(sec_sc_v, 1),
                    "Warning_Trigger": " | ".join(warn_reasons)
                })

        # Check if a 6-Month (26-Week) Capital Rebalance occurs at Monday Open of dt_next
        is_6m_rebalance = (idx > 0) and (rebalance_weeks > 0) and (idx % rebalance_weeks == 0)

        # Save complete Time Machine snapshot for Friday `dt_sig`
        active_post_list = [
            {
                "Global_Slot": g + 1,
                "Sector_Slot": (g // stocks_per_sector) + 1,
                "Sub_Slot": (g % stocks_per_sector) + 1,
                "Sector": sec_slots[g // stocks_per_sector] or "Cash (No Sector)",
                "Ticker": sub_tk[g] or "CASH",
                "Action_Monday_Open": (
                    "NEW BUY (Mon Open)" if any(x[0] == g for x in entering_sub_slots)
                    else ("HOLD" if sub_tk[g] is not None else "IDLE CASH")
                ),
                "Slot_Capital (₹)": round(sub_cap[g], 2),
                "Entry_Signal_Fri": str(dt_sig.date()) if any(x[0] == g for x in entering_sub_slots) else (
                    str(sub_entry_dt[g].date()) if sub_entry_dt[g] is not None else "—"
                )
            }
            for g in range(total_slots)
        ]

        weekly_snapshots[dt_sig] = {
            "dt_sig": dt_sig,
            "dt_next": dt_next,
            "regime_bullish": is_bull,
            "is_6m_rebalance": is_6m_rebalance,
            "active_sectors": list(sec_slots),
            "holdings_before": holdings_before,
            "portfolio_monday_open": active_post_list,
            "exits_monday_open": [
                {
                    "Global_Slot": g + 1,
                    "Sector": old_sec,
                    "Exited_Ticker": old_tk,
                    "Exit_Reason": reason
                }
                for g, old_tk, old_sec, reason in exiting_sub_slots
            ],
            "entries_monday_open": [
                {
                    "Global_Slot": g + 1,
                    "Sector": sec_name,
                    "Entered_Ticker": new_tk,
                    "Stock_Score": sc_v,
                    "26W_Ret (%)": r26_v
                }
                for g, new_tk, sec_name, sc_v, r26_v in entering_sub_slots
            ],
            "sector_stock_tables": sector_stock_tables,
            "qualified_excluded": pd.DataFrame(qualified_excluded_rows),
            "near_misses": pd.DataFrame(near_miss_rows),
            "exit_warnings": pd.DataFrame(exit_warning_rows)
        }

        # ------------------------------------------------------------------
        # D. EXECUTE MONDAY OPEN TRADES & ADVANCE CAPITAL TO dt_next (IF EXISTS)
        # ------------------------------------------------------------------
        if not has_next_week:
            break

        # 1) Exited slots earn weekend gap (Fri Close -> Mon Open) and pay sell cost
        for g, (old_tk, old_sec, reason, ent_dt, ent_cap) in exited_tk_map.items():
            gap_r = stk_ret_gap.loc[dt_next].get(old_tk, np.nan)
            if pd.notna(gap_r):
                sub_cap[g] *= (1.0 + float(gap_r))
            sub_cap[g] *= (1.0 - one_way_cost)
            total_turnover_notional += sub_cap[g]

            hold_w = int(round((dt_next - ent_dt).days / 7.0)) if ent_dt is not None else 1
            t_ret = ((sub_cap[g] / ent_cap) - 1.0) * 100.0 if ent_cap > 0 else 0.0
            stock_trade_log.append({
                "Global_Slot": g + 1,
                "Sector": old_sec,
                "Ticker": old_tk,
                "Entry_Signal_Fri": str(ent_dt.date()) if ent_dt is not None else "—",
                "Exit_Signal_Fri": str(dt_sig.date()),
                "Holding_Weeks": max(1, hold_w),
                "Entry_Capital (₹)": round(ent_cap, 2),
                "Exit_Capital (₹)": round(sub_cap[g], 2),
                "Return_Pct": round(t_ret, 2),
                "Exit_Reason": reason
            })
            sub_entry_dt[g] = None
            sub_entry_cap[g] = 0.0

        # 2) Staying slots earn Friday Close -> Monday Open gap before optional 6M rebalance
        for g in staying_sub_slots:
            tk = sub_tk[g]
            gap_r = stk_ret_gap.loc[dt_next].get(tk, np.nan)
            if pd.notna(gap_r):
                sub_cap[g] *= (1.0 + float(gap_r))

        # 3) Optional 6-Month (26-Week) Equal-Weight Rebalance across all 12 slots at Monday Open
        if is_6m_rebalance:
            tot_mon_open = float(sum(sub_cap))
            target_per_slot = tot_mon_open / float(total_slots)
            for g in range(total_slots):
                delta = abs(sub_cap[g] - target_per_slot)
                # Only active stock slots incur transaction costs when trimmed/topped up
                if sub_tk[g] is not None and not any(x[0] == g for x in entering_sub_slots):
                    rebal_cost = delta * one_way_cost
                    total_turnover_notional += delta
                else:
                    rebal_cost = 0.0
                sub_cap[g] = target_per_slot - rebal_cost

        # 4) Staying slots earn Monday Open -> Friday Close intra-week return
        for g in staying_sub_slots:
            tk = sub_tk[g]
            in_r = stk_ret_intra.loc[dt_next].get(tk, np.nan)
            if pd.notna(in_r):
                sub_cap[g] *= (1.0 + float(in_r))

        # 5) Entering slots pay Monday Open entry cost and earn Monday Open -> Friday Close return
        for g, new_tk, sec_name, _, _ in entering_sub_slots:
            sub_entry_cap[g] = sub_cap[g]
            sub_entry_dt[g] = dt_sig
            sub_cap[g] *= (1.0 - one_way_cost)
            total_turnover_notional += sub_cap[g]
            in_r = stk_ret_intra.loc[dt_next].get(new_tk, np.nan)
            if pd.notna(in_r):
                sub_cap[g] *= (1.0 + float(in_r))

        # 6) Idle cash sub-slots earn 6% p.a. weekly interest
        for g in range(total_slots):
            if sub_tk[g] is None:
                sub_cap[g] *= (1.0 + weekly_cash_ret)

        tot_eq = float(sum(sub_cap))
        active_cnt = sum(1 for x in sub_tk if x is not None)
        cash_cap = sum(sub_cap[g] for g in range(total_slots) if sub_tk[g] is None)
        cash_pct = (cash_cap / tot_eq) * 100.0 if tot_eq > 0 else 100.0
        held_tks = [sub_tk[g].replace(".NS", "") for g in range(total_slots) if sub_tk[g] is not None]
        held_secs_short = [sec_slots[s].split(".")[1].strip() if (sec_slots[s] and "." in sec_slots[s]) else (sec_slots[s] or "Cash")
                           for s in range(num_sectors)]

        equity_records.append({
            "Date": dt_next,
            "Total_Equity": tot_eq,
            "Active_Slots": active_cnt,
            "Cash_Pct": round(cash_pct, 1),
            "Held_Stocks": ", ".join(held_tks) if held_tks else "100% Cash",
            "Regime_Bullish": is_bull
        })

        ledger_rows.append({
            "Signal_Friday": str(dt_sig.date()),
            "Execution_Week_Ending": str(dt_next.date()),
            "Regime_40W": "Bullish" if is_bull else "Bearish (No New Entries)",
            "6M_Rebalance": "Yes" if is_6m_rebalance else "No",
            "Active_Stock_Slots": f"{active_cnt} / {total_slots}",
            "Cash (%)": round(cash_pct, 1),
            "Total_Equity (₹)": round(tot_eq, 0),
            "Active_Sectors (4 Slots)": " | ".join(held_secs_short),
            "Held_Stocks (Up to 12)": ", ".join(held_tks) if held_tks else "100% Cash"
        })

    eq_df = pd.DataFrame(equity_records).set_index("Date")
    trades_df = pd.DataFrame(stock_trade_log)
    ledger_df = pd.DataFrame(ledger_rows)
    metrics = compute_performance_metrics(eq_df, trades_df, total_turnover_notional, cash_rate_annual)

    return {
        "equity_df": eq_df,
        "trades_df": trades_df,
        "ledger_df": ledger_df,
        "snapshots": weekly_snapshots,
        "metrics": metrics
    }


def compute_fast_forward_table(dt_sig, snap, weekly_data):
    """
    Computes Next +1W, +4W, and +12W returns from Monday Open (t+1) for all
    held/entered stocks at Friday close `dt_sig`.
    """
    all_weeks = weekly_data["stk_close"].index
    if dt_sig not in all_weeks:
        return pd.DataFrame(), 0

    idx = all_weeks.get_loc(dt_sig)
    avail_future_weeks = len(all_weeks) - 1 - idx
    if avail_future_weeks < 1:
        return pd.DataFrame(), 0

    dt_mon_week = all_weeks[idx + 1]
    open_next = weekly_data["stk_open"].loc[dt_mon_week]

    rows = []
    for item in snap["portfolio_monday_open"]:
        tk = item["Ticker"]
        if tk == "CASH" or tk not in open_next.index:
            continue
        entry_open_px = open_next.get(tk, np.nan)
        if pd.isna(entry_open_px) or entry_open_px <= 0:
            continue

        out = {
            "Global_Slot": item["Global_Slot"],
            "Sector": item["Sector"],
            "Ticker": tk,
            "Action_Mon_Open": item["Action_Monday_Open"],
            "Mon_Open_Price": round(float(entry_open_px), 2)
        }
        for w_ahead, label in [(1, "+1W Return (%)"), (4, "+4W Return (%)"), (12, "+12W Return (%)")]:
            if idx + w_ahead < len(all_weeks):
                c_fut = weekly_data["stk_close"].iloc[idx + w_ahead].get(tk, np.nan)
                out[label] = round(((float(c_fut) / float(entry_open_px)) - 1.0) * 100.0, 2) if pd.notna(c_fut) else np.nan
            else:
                out[label] = np.nan
        rows.append(out)

    return pd.DataFrame(rows), avail_future_weeks


# ------------------------------------------------------------------------------
# 5. PERFORMANCE METRICS HELPER
# ------------------------------------------------------------------------------
def compute_performance_metrics(eq_df, trades_df, total_turnover_notional, rf_annual=0.06):
    eq = eq_df["Total_Equity"].dropna()
    if len(eq) < 2:
        return {}

    n_weeks = len(eq) - 1
    years = n_weeks / 52.0
    cagr = ((eq.iloc[-1] / eq.iloc[0]) ** (1.0 / max(years, 0.01)) - 1.0) * 100.0

    w_ret = eq.pct_change().dropna()
    ann_vol = float(w_ret.std() * np.sqrt(52.0) * 100.0) if len(w_ret) > 1 else 0.0
    sharpe = ((cagr / 100.0) - rf_annual) / (ann_vol / 100.0) if ann_vol > 0 else 0.0

    peak = eq.cummax()
    dd = ((eq - peak) / peak) * 100.0
    max_dd = float(dd.min())
    calmar = cagr / abs(max_dd) if max_dd < 0 else 0.0

    avg_cash_pct = float(eq_df["Cash_Pct"].mean())
    time_in_mkt = float((eq_df["Active_Slots"] > 0).mean() * 100.0)

    if not trades_df.empty:
        win_rate = float((trades_df["Return_Pct"] > 0).mean() * 100.0)
        avg_hold_w = float(trades_df["Holding_Weeks"].mean())
        n_trades = len(trades_df)
    else:
        win_rate, avg_hold_w, n_trades = 0.0, 0.0, 0

    avg_equity = float(eq.mean())
    ann_turnover_pct = ((total_turnover_notional / 2.0) / avg_equity / max(years, 0.01)) * 100.0

    return {
        "CAGR (%)": round(cagr, 2),
        "Max Drawdown (%)": round(max_dd, 2),
        "Sharpe Ratio": round(sharpe, 2),
        "Calmar Ratio": round(calmar, 2),
        "Ann. Volatility (%)": round(ann_vol, 2),
        "Win Rate (%)": round(win_rate, 1),
        "Avg Holding (Weeks)": round(avg_hold_w, 1),
        "Closed Trades": n_trades,
        "Avg Cash (%)": round(avg_cash_pct, 1),
        "Time in Market (%)": round(time_in_mkt, 1),
        "Annual Turnover (%)": round(ann_turnover_pct, 1),
        "Ending Equity (₹)": round(float(eq.iloc[-1]), 0)
    }


# ------------------------------------------------------------------------------
# 6. STREAMLIT RENDERER: TIME MACHINE FIRST, THEN STOCK & SECTOR BACKTESTS
# ------------------------------------------------------------------------------
def render_backtest_tab(raw_disk_ohlc, sectors_dict, cache_ts_key, fetch_benchmark_fn):
    st.subheader("🏛️ MomentumSys — Stock & Sector Time Machine + 15Y Backtest Engine")
    st.caption(
        "4 Sectors × 3 Stocks = 12 Stock Slots | 6-Month (26W) Rebalance | "
        "IPO Gate (≥52W) + 22D Circuit Filter (O=C=H or O=C=L ≤ 6 Days) | "
        "Exit ONLY on Parent Sector Exit or Stock (RSI < RSI-MA & RSI < 50)"
    )

    with st.spinner("Computing weekly IPO-gated sector & stock matrices (strict completed Friday cutoff)..."):
        weekly_data = build_weekly_master_data(
            raw_disk_ohlc,
            json.dumps(sectors_dict, sort_keys=True),
            cache_ts_key
        )
        stk_ind = compute_stock_indicators(weekly_data, cache_ts_key, rsi_period=14, rsi_ma_period=20)
        sec_score_bundle = compute_sector_scores(weekly_data, rsi_period=14, rsi_ma_period=20)

        nifty_daily, _ = fetch_benchmark_fn(period="15y")
        if nifty_daily is not None and not nifty_daily.empty:
            nifty_weekly = nifty_daily.resample("W-FRI").last().reindex(weekly_data["close_idx"].index).ffill()
        else:
            nifty_weekly = pd.Series(dtype=float, index=weekly_data["close_idx"].index)

    # Top-level controls shared across Time Machine & Backtest
    ctrl1, ctrl2, ctrl3, ctrl4 = st.columns(4)
    with ctrl1:
        regime_choice = st.selectbox(
            "Active Regime Filter (40W MA):",
            [
                "EW Full Universe 40W MA (Default)",
                "Nifty 50 (^NSEI) 40W MA",
                "Unfiltered (No Regime Gate)"
            ],
            index=0
        )
    with ctrl2:
        rebal_choice = st.selectbox(
            "Stock Slot Rebalance Frequency:",
            ["Every 6 Months (26 Weeks)", "No Rebalancing (Pure Slot Drift)"],
            index=0
        )
    with ctrl3:
        stk_entry_th = st.select_slider(
            "Stock Entry Cutoff (Score ≥):",
            options=[62.5, 68.75, 75.0, 81.25, 87.5],
            value=75.0
        )
    with ctrl4:
        period_mode = st.selectbox(
            "Backtest Window:",
            [
                "Full Period (All Available Years)",
                "In-Sample (2010 – 2019)",
                "Out-of-Sample (2020 – Present)"
            ],
            index=0
        )

    start_dt, end_dt = None, None
    if "2010 – 2019" in period_mode:
        start_dt, end_dt = "2010-01-01", "2019-12-31"
    elif "2020 – Present" in period_mode:
        start_dt, end_dt = "2020-01-01", None

    rebal_w = 26 if "26 Weeks" in rebal_choice else 0
    if "EW Full Universe" in regime_choice:
        active_reg_series = weekly_data["universe_idx"]
    elif "Nifty 50" in regime_choice:
        active_reg_series = nifty_weekly
    else:
        active_reg_series = None

    with st.spinner("Running 12-Slot Stock Engine & building week-by-week Time Machine snapshots..."):
        stk_run = run_stock_portfolio_and_timemachine(
            weekly_data, sec_score_bundle, stk_ind, sectors_dict,
            regime_series=active_reg_series,
            sec_entry_th=75.0, sec_exit_th=50.0, stk_entry_th=float(stk_entry_th),
            num_sectors=4, stocks_per_sector=3, rebalance_weeks=rebal_w,
            start_date=start_dt, end_date=end_dt
        )

    if stk_run is None or not stk_run["snapshots"]:
        st.warning("Not enough historical weekly data in the selected window.")
        return

    # Build Order: 1. Time Machine & Live Mode FIRST, 2. Stock & Sector Backtest Tearsheet SECOND
    tm_tab, bt_tab, ledger_tab, score_tab = st.tabs([
        "🕰️ 1. Time Machine & Live Mode (Week-by-Week Portfolio Audit)",
        "📈 2. Stock vs Sector Backtest Tearsheet & Trade Log",
        "🗂️ 3. Every-Week Historical Portfolio Holdings Ledger",
        "🔢 4. Current Week 100-Point Sector Scoreboard"
    ])

    # ==========================================================================
    # SUB-TAB 1: TIME MACHINE & LIVE MODE
    # ==========================================================================
    with tm_tab:
        snap_dates = sorted(stk_run["snapshots"].keys())
        latest_fri = snap_dates[-1]

        mode_col, date_col = st.columns([1, 2])
        with mode_col:
            tm_mode = st.radio(
                "Time Machine Mode:",
                ["🟢 Live Mode (Latest Completed Friday)", "⏪ Historical Friday Replay"],
                horizontal=False
            )
        with date_col:
            if "Live Mode" in tm_mode:
                selected_fri = latest_fri
                st.info(
                    f"🔒 **LIVE MODE — STRICT AS-OF CUTOFF: Friday, {str(selected_fri.date())}**  \n"
                    f"In-progress weekday bars after {str(selected_fri.date())} are strictly excluded. "
                    f"Orders below are for the **upcoming Monday Open**."
                )
            else:
                date_labels = [str(d.date()) for d in snap_dates]
                chosen_str = st.select_slider(
                    "Select Any Historical Friday Close to Freeze Time:",
                    options=date_labels,
                    value=date_labels[max(0, len(date_labels) - 25)]
                )
                selected_fri = pd.Timestamp(chosen_str)
                st.success(
                    f"🔒 **HISTORICAL TIME MACHINE — DATA FROZEN AS OF: Friday, {str(selected_fri.date())}**  \n"
                    f"All scores, peer medians, and portfolio slots below use ONLY data up to {str(selected_fri.date())}."
                )

        snap = stk_run["snapshots"][selected_fri]

        # Summary KPI row for the selected Friday
        k1, k2, k3, k4 = st.columns(4)
        active_stk_cnt = sum(1 for x in snap["portfolio_monday_open"] if x["Ticker"] != "CASH")
        active_sec_cnt = sum(1 for x in snap["active_sectors"] if x is not None)
        k1.metric("As-Of Friday Close", str(selected_fri.date()))
        k2.metric("Active Sectors / Stocks", f"{active_sec_cnt}/4 Sectors | {active_stk_cnt}/12 Stocks")
        k3.metric("40-Week MA Regime", "🟢 Bullish (Entries Allowed)" if snap["regime_bullish"] else "🔴 Bearish (Cash Protection)")
        k4.metric("6-Month Rebalance Week?", "🔄 YES (Re-equalizing 12 Slots)" if snap["is_6m_rebalance"] else "No (Pure Slot Drift)")

        # 1. Current 12-Slot Portfolio & Monday Open Actions
        st.markdown(f"#### 📋 12-Slot Portfolio Holdings & Action Plan (Signal Friday: `{str(selected_fri.date())}`)")
        st.dataframe(pd.DataFrame(snap["portfolio_monday_open"]), use_container_width=True, hide_index=True)

        # 2. Weekly Holdings Diff (Entries & Exits vs Prior Week)
        diff_col1, diff_col2 = st.columns(2)
        with diff_col1:
            st.markdown("##### 🟢 Monday Open New Buys (Vs Prior Week)")
            if snap["entries_monday_open"]:
                st.dataframe(pd.DataFrame(snap["entries_monday_open"]), use_container_width=True, hide_index=True)
            else:
                st.caption("No new stock entries triggered this week.")
        with diff_col2:
            st.markdown("##### 🔴 Monday Open Exits & Exact Rule Triggered")
            if snap["exits_monday_open"]:
                st.dataframe(pd.DataFrame(snap["exits_monday_open"]), use_container_width=True, hide_index=True)
            else:
                st.caption("No stock exits triggered this week.")

        # 3. Exit-Warning Watchlist & Qualified-But-Excluded / Near-Misses
        warn_col, excl_col = st.columns(2)
        with warn_col:
            st.markdown("##### ⚠️ Exit-Warning Watchlist (Held Stocks Near Exit)")
            if not snap["exit_warnings"].empty:
                st.dataframe(snap["exit_warnings"], use_container_width=True, hide_index=True)
            else:
                st.caption("All held stocks have comfortable RSI & Sector Score cushions.")
        with excl_col:
            st.markdown("##### 🚫 Qualified-But-Excluded (Scored ≥ 75, Missed Top 3)")
            if not snap["qualified_excluded"].empty:
                st.dataframe(snap["qualified_excluded"], use_container_width=True, hide_index=True)
            else:
                st.caption("No excess qualifying stocks were excluded this week.")

        with st.expander(
            f"🔍 View Near-Miss Stocks in Active Sectors (Scored 62.5 to below the entry cutoff ({stk_entry_th:g}), or Failed 22D Circuit Gate)"
        ):
            if not snap["near_misses"].empty:
                st.dataframe(snap["near_misses"], use_container_width=True, hide_index=True)
            else:
                st.caption("No near-miss stocks in the active sectors this week.")

        # 4. Per-Stock 6-Component Breakdown Inside Active Sectors
        st.markdown("#### 🧮 Per-Stock 100-Point Component Breakdown (Active Sectors)")
        active_secs_non_null = [s for s in snap["active_sectors"] if s is not None]
        if active_secs_non_null:
            chosen_inspect_sec = st.selectbox(
                "Select Active Sector to Inspect Every Constituent's 6 Binary Score Components:",
                options=active_secs_non_null,
                index=0
            )
            sec_detail_df = snap["sector_stock_tables"].get(chosen_inspect_sec, pd.DataFrame())
            if not sec_detail_df.empty:
                display_cols = [
                    "Ticker", "Entry_Filter_OK", "Stock_Score",
                    "C1_Rel_52W (12.5)", "C2_RSI>60 (25)", "C3_RSI>MA (12.5)",
                    "C4_Gap_4W (12.5)", "C5_NewHi_7W (18.75)", "C6_NearHi_10% (18.75)",
                    "52W_Ret (%)", "Peer_Median_52W (%)", "26W_Ret (%)",
                    "RSI(14)", "RSI_MA(20)", "Bad_Days_22D", "Exit_Signal (RSI<MA & <50)"
                ]
                st.dataframe(sec_detail_df[display_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No active sectors scored ≥ 75 on this Friday (Portfolio is 100% Cash).")

        # 5. Fast-Forward Audit Panel (+1W, +4W, +12W from Monday Open)
        st.markdown("#### ⏩ Fast-Forward Outcome Audit (+1W / +4W / +12W from Monday Open Entry)")
        ff_df, avail_w = compute_fast_forward_table(selected_fri, snap, weekly_data)
        if avail_w == 0:
            st.caption("You are viewing the latest completed Friday (Live Mode) — future bars have not happened yet.")
        elif ff_df.empty:
            st.caption("Portfolio was in 100% Cash on this week.")
        else:
            st.caption(f"Showing forward performance from **Monday Open** following `{str(selected_fri.date())}` ({avail_w} future weeks available in cache):")
            st.dataframe(ff_df, use_container_width=True, hide_index=True)

    # ==========================================================================
    # SUB-TAB 2: FULL 15-YEAR STOCK-LEVEL VS SECTOR-LEVEL BACKTEST TEARSHEET
    # ==========================================================================
    with bt_tab:
        with st.spinner("Running comparison variants (EW Filter, ^NSEI Filter, Unfiltered & 4-Slot Sector Index)..."):
            stk_n50 = run_stock_portfolio_and_timemachine(
                weekly_data, sec_score_bundle, stk_ind, sectors_dict,
                regime_series=nifty_weekly,
                sec_entry_th=75.0, sec_exit_th=50.0, stk_entry_th=float(stk_entry_th),
                num_sectors=4, stocks_per_sector=3, rebalance_weeks=rebal_w,
                start_date=start_dt, end_date=end_dt
            )
            stk_unfilt = run_stock_portfolio_and_timemachine(
                weekly_data, sec_score_bundle, stk_ind, sectors_dict,
                regime_series=None,
                sec_entry_th=75.0, sec_exit_th=50.0, stk_entry_th=float(stk_entry_th),
                num_sectors=4, stocks_per_sector=3, rebalance_weeks=rebal_w,
                start_date=start_dt, end_date=end_dt
            )
            sec_only_run = run_portfolio_backtest(
                weekly_data, sec_score_bundle, regime_series=active_reg_series,
                entry_threshold=75.0, exit_threshold=50.0,
                start_date=start_dt, end_date=end_dt
            )

        bt_dates = stk_run["equity_df"].index
        ew_uni_slice = weekly_data["universe_idx"].reindex(bt_dates).ffill().bfill()
        ew_uni_eq = 1_000_000.0 * (ew_uni_slice / ew_uni_slice.iloc[0]) if not ew_uni_slice.dropna().empty else pd.Series(1_000_000.0, index=bt_dates)

        n50_slice = nifty_weekly.reindex(bt_dates).ffill().bfill()
        n50_eq = 1_000_000.0 * (n50_slice / n50_slice.iloc[0]) if not n50_slice.dropna().empty else pd.Series(1_000_000.0, index=bt_dates)

        comp_rows = [
            {"Strategy / Layer": f"1. 12-Stock Portfolio ({regime_choice})", **stk_run["metrics"]},
            {"Strategy / Layer": "2. 12-Stock Portfolio (Nifty 50 ^NSEI 40W MA)", **(stk_n50["metrics"] if stk_n50 else {})},
            {"Strategy / Layer": "3. 12-Stock Portfolio (Unfiltered — No Regime Gate)", **(stk_unfilt["metrics"] if stk_unfilt else {})},
            {"Strategy / Layer": f"4. 4-Sector Index Portfolio ({regime_choice})", **(sec_only_run["metrics"] if sec_only_run else {})}
        ]
        st.markdown("### 📊 12-Stock Layer vs 4-Sector Index Layer Performance Summary")
        st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)

        fig = make_subplots(
            rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
            row_heights=[0.52, 0.24, 0.24],
            subplot_titles=(
                "Equity Curve Comparison (₹10 Lakh Base, Log Scale)",
                "Underwater Drawdown (%)",
                "Stock Portfolio Cash Allocation (%)"
            )
        )

        for label, r_obj, color, dash in [
            ("12-Stock Portfolio (Active Filter)", stk_run, "#00C853", "solid"),
            ("12-Stock Portfolio (Unfiltered)", stk_unfilt, "#AA00FF", "dot"),
            ("4-Sector Index Portfolio", sec_only_run, "#2962FF", "solid")
        ]:
            if r_obj is not None:
                eq_s = r_obj["equity_df"]["Total_Equity"]
                dd_s = ((eq_s - eq_s.cummax()) / eq_s.cummax()) * 100.0
                fig.add_trace(go.Scatter(x=eq_s.index, y=eq_s, name=label, line=dict(color=color, width=2.4, dash=dash)), row=1, col=1)
                fig.add_trace(go.Scatter(x=dd_s.index, y=dd_s, name=f"{label} DD", line=dict(color=color, width=1.6, dash=dash), showlegend=False), row=2, col=1)

        fig.add_trace(go.Scatter(x=ew_uni_eq.index, y=ew_uni_eq, name="EW Full Universe Buy & Hold", line=dict(color="#FF6D00", width=2.0, dash="dash")), row=1, col=1)
        fig.add_trace(go.Scatter(x=n50_eq.index, y=n50_eq, name="Nifty 50 (^NSEI) Buy & Hold", line=dict(color="#9E9E9E", width=1.8, dash="dash")), row=1, col=1)

        cash_s = stk_run["equity_df"]["Cash_Pct"]
        fig.add_trace(go.Scatter(x=cash_s.index, y=cash_s, name="Stock Cash %", fill="tozeroy", line=dict(color="#00B8D4", width=1.5)), row=3, col=1)

        split_dt = pd.Timestamp("2020-01-01")
        if bt_dates.min() < split_dt < bt_dates.max():
            fig.add_vline(x=str(split_dt.date()), line_width=1.5, line_dash="dash", line_color="#FFD600")

        fig.update_yaxes(type="log", title_text="Equity (₹)", row=1, col=1)
        fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)
        fig.update_yaxes(title_text="Cash (%)", range=[0, 105], row=3, col=1)
        fig.update_layout(template="plotly_dark", height=780, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 📜 Complete Closed Stock Trades Log")
        if not stk_run["trades_df"].empty:
            st.dataframe(
                stk_run["trades_df"].sort_values("Entry_Signal_Fri", ascending=False),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No closed stock trades in the selected window.")

        st.markdown("### 📜 Closed Sector Trade Log")
        if sec_only_run is not None and not sec_only_run["trades_df"].empty:
            st.dataframe(
                sec_only_run["trades_df"].sort_values("Entry_Week_Close", ascending=False),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No closed sector trades in the selected window.")

    # ==========================================================================
    # SUB-TAB 3: EVERY-WEEK HISTORICAL PORTFOLIO HOLDINGS LEDGER
    # ==========================================================================
    with ledger_tab:
        st.markdown("### 🗂️ Master Week-by-Week Portfolio Holdings Ledger (Every Week Since Backtest Start)")
        st.caption(
            "Inspect or download the exact stocks and sectors held by your portfolio during every single week of the backtest."
        )
        led_df = stk_run["ledger_df"]
        if not led_df.empty:
            st.dataframe(led_df.iloc[::-1], use_container_width=True, hide_index=True)
            csv_led = led_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download Full Weekly Holdings Ledger (CSV)",
                data=csv_led,
                file_name="momentumsys_weekly_holdings_ledger.csv",
                mime="text/csv"
            )

    # ==========================================================================
    # SUB-TAB 4: CURRENT WEEK 100-POINT SECTOR SCOREBOARD
    # ==========================================================================
    with score_tab:
        st.markdown("### 🔢 Current Week 100-Point Sector Scoreboard")
        valid_score_weeks = sec_score_bundle["score"].dropna(how="all").index
        if len(valid_score_weeks) > 0:
            last_w = valid_score_weeks[-1]
            cur_board = pd.DataFrame({
                "Sector": sec_score_bundle["score"].columns,
                "Rank": sec_score_bundle["rank"].loc[last_w].values,
                "Score (100)": sec_score_bundle["score"].loc[last_w].values,
                "52W Return (%)": (sec_score_bundle["ret_52w"].loc[last_w].values * 100.0).round(2),
                "26W Return (%)": (sec_score_bundle["ret_26w"].loc[last_w].values * 100.0).round(2),
                "RSI(14)": sec_score_bundle["rsi"].loc[last_w].values.round(1),
                "RSI-MA": sec_score_bundle["rsi_ma"].loc[last_w].values.round(1),
                "Breadth (% > 0)": (weekly_data["breadth"].loc[last_w].values * 100.0).round(1),
                "Eligible Stocks (≥52W)": weekly_data["active_cnt"].loc[last_w].values
            }).sort_values(["Score (100)", "26W Return (%)"], ascending=[False, False])
            st.caption(f"Latest Signal Week Ending: **{str(last_w.date())}**")
            st.dataframe(cur_board, use_container_width=True, hide_index=True)
        else:
            st.info("No valid sector scores available.")
