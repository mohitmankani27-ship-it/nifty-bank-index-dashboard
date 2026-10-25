# ==============================================================================
# MODULE: MOMENTUMSYS WEEKLY SECTOR BACKTEST ENGINE (sector_backtest.py)
# ==============================================================================
import json
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ------------------------------------------------------------------------------
# MODULE 1: WEEKLY DATA LOADER & IPO-SAFE EQUAL-WEIGHT INDEX BUILDER
# ------------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def build_weekly_sector_data(_raw_ohlc, sectors_json, cache_ts_key):
    """
    1. Resamples daily Open & Close to weekly (W-FRI):
       - Weekly Open  = first valid trading day's Open in that week (Monday Open)
       - Weekly Close = last valid trading day's Close in that week (Friday Close)
    2. Applies the 52-week IPO history gate: a stock is excluded from all index
       returns and breadth until it has at least 52 prior weeks of trading history.
    3. Clips extreme single-stock weekly outliers (> +100% or < -80%) caused by
       unadjusted splits in yfinance.
    4. Chains weekly equal-weight returns for all 27 sectors + Full Universe EW Index.
    """
    sectors_dict = json.loads(sectors_json)

    # Forward-fill short holiday gaps up to 5 days on daily frames, but do NOT
    # drop 'failed_stale' stocks so historical delistings stay in past years.
    daily_close = _raw_ohlc["Close"].dropna(how="all").ffill(limit=5)
    daily_open = _raw_ohlc["Open"].reindex(daily_close.index).fillna(daily_close)

    # Weekly Friday Close & Weekly Monday (first trading day) Open
    w_close = daily_close.resample("W-FRI").last().dropna(how="all")
    w_open = daily_open.resample("W-FRI").first().reindex(w_close.index).fillna(w_close)

    # Component returns for each individual stock:
    # 1) Close-to-Close: C[t] / C[t-1] - 1 (for holding through the week)
    # 2) Weekend Gap:    O[t] / C[t-1] - 1 (Friday Close t-1 -> Monday Open t)
    # 3) Intra-week:     C[t] / O[t]   - 1 (Monday Open t    -> Friday Close t)
    prev_c = w_close.shift(1)
    ret_cc = (w_close / prev_c) - 1.0
    ret_gap = (w_open / prev_c) - 1.0
    ret_intra = (w_close / w_open) - 1.0

    # IPO & 52-Week History Gate:
    # Stock must have a valid price at week t AND week t-52, plus >=40 valid weeks in last 52w
    stock_52w_ret = (w_close / w_close.shift(52)) - 1.0
    valid_weeks_52 = w_close.notna().rolling(52, min_periods=40).sum() >= 40
    valid_return_bounds = (ret_cc <= 1.0) & (ret_cc >= -0.80)

    eligible_mask = (
        w_close.notna()
        & prev_c.notna()
        & stock_52w_ret.notna()
        & valid_weeks_52
        & valid_return_bounds
    )

    # Mask out ineligible stock-weeks (convert bool to float before masking to avoid object dtype)
    ret_cc_clean = ret_cc.where(eligible_mask)
    ret_gap_clean = ret_gap.where(eligible_mask).clip(-0.50, 0.50)
    ret_intra_clean = ret_intra.where(eligible_mask).clip(-0.80, 1.0)
    pos_52w_clean = (stock_52w_ret > 0.0).astype(float).where(eligible_mask)

    weeks = w_close.index
    sector_names = list(sectors_dict.keys())

    sec_close_idx = pd.DataFrame(index=weeks, columns=sector_names, dtype=float)
    sec_ret_cc = pd.DataFrame(index=weeks, columns=sector_names, dtype=float)
    sec_ret_gap = pd.DataFrame(index=weeks, columns=sector_names, dtype=float)
    sec_ret_intra = pd.DataFrame(index=weeks, columns=sector_names, dtype=float)
    sec_breadth = pd.DataFrame(index=weeks, columns=sector_names, dtype=float)
    sec_active_cnt = pd.DataFrame(index=weeks, columns=sector_names, dtype=int)

    for sec, tickers in sectors_dict.items():
        cols = [t for t in tickers if t in ret_cc_clean.columns]
        if not cols:
            continue

        # Equal-weight average across eligible stocks in week t
        r_cc = ret_cc_clean[cols].mean(axis=1)
        r_gap = ret_gap_clean[cols].mean(axis=1)
        r_in = ret_intra_clean[cols].mean(axis=1)
        brd = pos_52w_clean[cols].mean(axis=1)  # Fraction of eligible stocks with 52w ret > 0
        cnt = eligible_mask[cols].sum(axis=1).astype(int)

        # Chain-link weekly close index starting at 100.0 from first valid week
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

    # Full Universe Equal-Weight Composite Index (for Regime Filter & Benchmark)
    uni_r_cc = ret_cc_clean.mean(axis=1)
    first_u = uni_r_cc.first_valid_index()
    uni_close_idx = pd.Series(index=weeks, dtype=float)
    if first_u is not None:
        uni_close_idx.loc[first_u:] = 100.0 * (1.0 + uni_r_cc.loc[first_u:].fillna(0.0)).cumprod()

    # Drop early warmup weeks where no sector has valid 52-week history yet
    non_empty_idx = sec_close_idx.dropna(how="all").index
    valid_start = non_empty_idx.min() if len(non_empty_idx) > 0 else weeks[0]

    return {
        "close_idx": sec_close_idx.loc[valid_start:],
        "ret_cc": sec_ret_cc.loc[valid_start:],
        "ret_gap": sec_ret_gap.loc[valid_start:],
        "ret_intra": sec_ret_intra.loc[valid_start:],
        "breadth": sec_breadth.loc[valid_start:],
        "active_cnt": sec_active_cnt.loc[valid_start:],
        "universe_idx": uni_close_idx.loc[valid_start:],
        "universe_ret_cc": uni_r_cc.loc[valid_start:]
    }


# ------------------------------------------------------------------------------
# MODULE 2: VECTORIZED 100-POINT BINARY SCORER
# ------------------------------------------------------------------------------
def compute_wilder_rsi(close_df, period=14):
    """Computes standard Wilder RSI across all sector columns simultaneously."""
    delta = close_df.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


def compute_sector_scores(weekly_data, rsi_period=14, rsi_ma_period=20):
    """
    Computes the 7 binary conditions (100 points total) on weekly close indices:
      1. 10 pts: 52w return > median of the 27 sectors
      2. 20 pts: RSI(14) > 60
      3. 10 pts: RSI > RSI-MA (20-period)
      4. 10 pts: (RSI - RSI-MA) has risen 4 weeks in a row (no sign condition)
      5. 20 pts: Breadth >= 50% of eligible constituents positive (52w return > 0)
      6. 15 pts: New 52w high made within the last 7 weeks (weekly close basis)
      7. 15 pts: Weekly close within 10% of the 52w high
    Also computes 26-week return for tie-breaking and overall weekly ranks.
    """
    close_idx = weekly_data["close_idx"]
    breadth = weekly_data["breadth"]

    # 52-week and 26-week returns of the sector indices
    ret_52w = (close_idx / close_idx.shift(52)) - 1.0
    ret_26w = (close_idx / close_idx.shift(26)) - 1.0

    # Condition 1: 52w return above cross-sectional median of active sectors (10 pts)
    median_52w = ret_52w.median(axis=1)
    c1_rel_ret = ret_52w.gt(median_52w, axis=0).astype(float) * 10.0

    # Condition 2: RSI(14) > 60 (20 pts)
    rsi = compute_wilder_rsi(close_idx, period=rsi_period)
    c2_rsi_60 = (rsi > 60.0).astype(float) * 20.0

    # Condition 3: RSI > RSI-MA (10 pts)
    rsi_ma = rsi.rolling(rsi_ma_period, min_periods=rsi_ma_period).mean()
    c3_rsi_above_ma = (rsi > rsi_ma).astype(float) * 10.0

    # Condition 4: (RSI - RSI-MA) risen 4 weeks in a row (10 pts)
    rsi_gap = rsi - rsi_ma
    gap_rising_1w = (rsi_gap > rsi_gap.shift(1)).fillna(False)
    c4_gap_4w = (
        gap_rising_1w
        & gap_rising_1w.shift(1, fill_value=False)
        & gap_rising_1w.shift(2, fill_value=False)
        & gap_rising_1w.shift(3, fill_value=False)
    ).astype(float) * 10.0

    # Condition 5: Breadth >= 50% (20 pts)
    c5_breadth = (breadth >= 0.50).astype(float) * 20.0

    # Condition 6 & 7: 52-week high on weekly closes (52 bars = current + 51 prior weeks)
    high_52w = close_idx.rolling(52, min_periods=52).max()
    is_new_high = ((close_idx >= high_52w) & high_52w.notna()).astype(float)
    c6_recent_high = (is_new_high.rolling(7, min_periods=1).max() > 0.0).astype(float) * 15.0
    c7_near_high = ((close_idx >= 0.90 * high_52w) & high_52w.notna()).astype(float) * 15.0

    # Total Score (0 to 100), valid only when 52w index return is available
    valid_sector_mask = ret_52w.notna()
    total_score = (
        c1_rel_ret + c2_rsi_60 + c3_rsi_above_ma + c4_gap_4w
        + c5_breadth + c6_recent_high + c7_near_high
    ).where(valid_sector_mask, np.nan)

    # Ranking with 26-week return tie-breaker:
    # We add a tiny epsilon proportional to the 26w return rank so ties in integer score
    # are deterministically broken by higher 26w return.
    tie_breaker = ret_26w.rank(axis=1, ascending=True, pct=True).fillna(0.0) * 0.01
    composite_for_rank = total_score + tie_breaker
    weekly_rank = composite_for_rank.rank(axis=1, ascending=False, method="min")

    return {
        "score": total_score,
        "rank": weekly_rank,
        "ret_52w": ret_52w,
        "ret_26w": ret_26w,
        "rsi": rsi,
        "rsi_ma": rsi_ma
    }


# ------------------------------------------------------------------------------
# MODULE 3: PORTFOLIO STATE MACHINE (4 INDEPENDENT SLOTS, NO REBALANCING)
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
    """
    Simulates the 4-slot sector strategy week by week:
    - Each slot starts with initial_capital / 4 (₹2.5L) and compounds independently.
    - Signals are evaluated at Friday Close t; trades execute at Monday Open t+1.
    - Exits:
        (a) Score < exit_threshold (50) for 2 consecutive weeks (t and t-1), OR
        (b) Rank > 4 AND Score < entry_threshold (75) at week t (Grey-zone rule).
    - Entries:
        Open slots buy the highest-ranked unheld sectors with Score >= entry_threshold (75),
        provided the optional 40-week MA regime filter is True at week t.
    """
    scores = score_bundle["score"]
    ranks = score_bundle["rank"]
    ret_26w = score_bundle["ret_26w"]

    ret_cc = weekly_data["ret_cc"]
    ret_gap = weekly_data["ret_gap"]
    ret_intra = weekly_data["ret_intra"]

    # First week where at least 10 sectors have a valid 52-week score
    valid_weeks = scores.dropna(thresh=10).index
    if start_date is not None:
        valid_weeks = valid_weeks[valid_weeks >= pd.Timestamp(start_date)]
    if end_date is not None:
        valid_weeks = valid_weeks[valid_weeks <= pd.Timestamp(end_date)]

    if len(valid_weeks) < 2:
        return None

    one_way_cost = round_trip_cost / 2.0
    weekly_cash_ret = (1.0 + cash_rate_annual) ** (1.0 / 52.0) - 1.0

    # Compute 40-week SMA regime gate if a regime series is provided
    if regime_series is not None and not regime_series.dropna().empty:
        reg_aligned = regime_series.reindex(weekly_data["close_idx"].index).ffill()
        reg_ma40 = reg_aligned.rolling(40, min_periods=40).mean()
        regime_bullish = (reg_aligned > reg_ma40).reindex(valid_weeks).fillna(True)
    else:
        regime_bullish = pd.Series(True, index=valid_weeks)

    # Initialize independent slots
    slot_cap = [initial_capital / float(num_slots) for _ in range(num_slots)]
    slot_sec = [None for _ in range(num_slots)]
    slot_entry_dt = [None for _ in range(num_slots)]
    slot_entry_cap = [0.0 for _ in range(num_slots)]

    equity_records = []
    trade_log = []
    total_turnover_notional = 0.0

    # Record initial state at valid_weeks[0]
    equity_records.append({
        "Date": valid_weeks[0],
        "Total_Equity": initial_capital,
        "Active_Slots": 0,
        "Cash_Pct": 100.0,
        "Held_Sectors": "100% Cash",
        "Regime_Bullish": bool(regime_bullish.iloc[0])
    })

    # Step forward from week t (signal week) to week t+1 (execution & return week)
    for idx in range(len(valid_weeks) - 1):
        dt_sig = valid_weeks[idx]
        dt_prev = valid_weeks[idx - 1] if idx > 0 else dt_sig
        dt_next = valid_weeks[idx + 1]

        sc_t = scores.loc[dt_sig]
        sc_prev = scores.loc[dt_prev]
        rk_t = ranks.loc[dt_sig]
        r26_t = ret_26w.loc[dt_sig]
        is_bull = bool(regime_bullish.loc[dt_sig])

        # ------------------------------------------------------------------
        # STEP 1: Evaluate Exits at Friday Close dt_sig (Executed Monday Open dt_next)
        # ------------------------------------------------------------------
        exiting_slots = []
        staying_slots = []

        for s in range(num_slots):
            sec = slot_sec[s]
            if sec is None:
                continue

            cur_sc = sc_t.get(sec, np.nan)
            prv_sc = sc_prev.get(sec, np.nan)
            cur_rk = rk_t.get(sec, 999.0)

            # Exit triggers:
            # 1) Missing data, OR
            # 2) Below 50 for 2 consecutive weeks, OR
            # 3) Fell out of top 4 (Rank > 4) AND score < 75 (Grey-zone rule)
            cond_2w_below_50 = bool(pd.notna(cur_sc) and pd.notna(prv_sc) and (cur_sc < exit_threshold) and (prv_sc < exit_threshold))
            cond_grey_zone = bool(pd.notna(cur_sc) and (cur_rk > num_slots) and (cur_sc < entry_threshold))

            if pd.isna(cur_sc) or cond_2w_below_50 or cond_grey_zone:
                exiting_slots.append((s, sec, "2w < 50" if cond_2w_below_50 else "Rank > 4 & Score < 75"))
            else:
                staying_slots.append(s)

        # Process continuing holdings across full week dt_sig -> dt_next
        for s in staying_slots:
            sec = slot_sec[s]
            r_week = ret_cc.loc[dt_next, sec]
            if pd.notna(r_week):
                slot_cap[s] *= (1.0 + float(r_week))

        # Process exits at Monday Open of dt_next
        for s, old_sec, reason in exiting_slots:
            gap_r = ret_gap.loc[dt_next, old_sec]
            if pd.notna(gap_r):
                slot_cap[s] *= (1.0 + float(gap_r))
            # Deduct one-way sell cost at Monday Open
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

        # ------------------------------------------------------------------
        # STEP 2: Evaluate New Entries for Empty Slots at Monday Open dt_next
        # ------------------------------------------------------------------
        open_slots = [s for s in range(num_slots) if slot_sec[s] is None]
        currently_held = {slot_sec[s] for s in range(num_slots) if slot_sec[s] is not None}

        if open_slots and is_bull:
            # Eligible unheld sectors with Score >= 75, sorted by Score desc, 26w return desc
            candidates = []
            for sec in sc_t.index:
                if sec not in currently_held and pd.notna(sc_t[sec]) and sc_t[sec] >= entry_threshold:
                    r26_val = r26_t.get(sec, np.nan)
                    r26_clean = float(r26_val) if pd.notna(r26_val) else -999.0
                    candidates.append((sec, float(sc_t[sec]), r26_clean))

            candidates.sort(key=lambda x: (x[1], x[2]), reverse=True)

            for s, (new_sec, _, _) in zip(open_slots, candidates):
                # Buy at Monday Open of dt_next: deduct entry cost, then earn intra-week return
                slot_entry_cap[s] = slot_cap[s]
                slot_entry_dt[s] = dt_sig
                slot_sec[s] = new_sec

                slot_cap[s] *= (1.0 - one_way_cost)
                total_turnover_notional += slot_cap[s]

                in_r = ret_intra.loc[dt_next, new_sec]
                if pd.notna(in_r):
                    slot_cap[s] *= (1.0 + float(in_r))

        # ------------------------------------------------------------------
        # STEP 3: Compound Idle Cash Slots at 6% p.a. Equivalent
        # ------------------------------------------------------------------
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

    return {
        "equity_df": eq_df,
        "trades_df": trades_df,
        "metrics": metrics
    }


# ------------------------------------------------------------------------------
# MODULE 4: PERFORMANCE METRICS & BENCHMARK HELPERS
# ------------------------------------------------------------------------------
def compute_performance_metrics(eq_df, trades_df, total_turnover_notional, rf_annual=0.06):
    """Calculates CAGR, Max Drawdown, Sharpe, Calmar, Win Rate, Holding Period & Turnover."""
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
# MODULE 5: STREAMLIT BACKTEST TAB RENDERER
# ------------------------------------------------------------------------------
def render_backtest_tab(raw_disk_ohlc, sectors_dict, cache_ts_key, fetch_benchmark_fn):
    st.subheader("🧪 MomentumSys — Weekly Sectoral Indices Backtest Engine")
    st.caption(
        "52-Week IPO-Gated Equal-Weight Indices | 100-Point Binary Score | "
        "4 Independent Slots (No Rebalancing) | Monday Open Execution + 0.25% Round-Trip Cost"
    )

    with st.spinner("Building IPO-gated weekly sector indices & 100-point score matrices..."):
        weekly_data = build_weekly_sector_data(
            raw_disk_ohlc,
            json.dumps(sectors_dict, sort_keys=True),
            cache_ts_key
        )
        # Fetch Nifty 50 (^NSEI) weekly closes for comparison & regime filter
        nifty_daily, _ = fetch_benchmark_fn(period="15y")
        if nifty_daily is not None and not nifty_daily.empty:
            nifty_weekly = nifty_daily.resample("W-FRI").last().reindex(weekly_data["close_idx"].index).ffill()
        else:
            nifty_weekly = pd.Series(dtype=float, index=weekly_data["close_idx"].index)

    # Interactive Controls
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        period_mode = st.selectbox(
            "Walk-Forward Period:",
            [
                "Full Period (All Available Years)",
                "In-Sample Tuning (2010 – 2019)",
                "Out-of-Sample Test (2020 – Present)"
            ],
            index=0
        )
    with c2:
        entry_th = st.select_slider("Entry Threshold (Score ≥):", options=[65, 70, 75, 80, 85, 90, 95], value=75)
    with c3:
        exit_th = st.select_slider("2-Week Exit Threshold (Score <):", options=[35, 40, 45, 50, 55, 60], value=50)
    with c4:
        rsi_ma_len = st.radio("RSI Moving Average Window:", [20, 10], horizontal=True)

    start_dt, end_dt = None, None
    if "2010 – 2019" in period_mode:
        start_dt, end_dt = "2010-01-01", "2019-12-31"
    elif "2020 – Present" in period_mode:
        start_dt, end_dt = "2020-01-01", None

    score_bundle = compute_sector_scores(weekly_data, rsi_period=14, rsi_ma_period=int(rsi_ma_len))

    # Run all 3 Regime Variants simultaneously for comparison
    res_ew_reg = run_portfolio_backtest(
        weekly_data, score_bundle, regime_series=weekly_data["universe_idx"],
        entry_threshold=entry_th, exit_threshold=exit_th, start_date=start_dt, end_date=end_dt
    )
    res_n50_reg = run_portfolio_backtest(
        weekly_data, score_bundle, regime_series=nifty_weekly,
        entry_threshold=entry_th, exit_threshold=exit_th, start_date=start_dt, end_date=end_dt
    )
    res_no_reg = run_portfolio_backtest(
        weekly_data, score_bundle, regime_series=None,
        entry_threshold=entry_th, exit_threshold=exit_th, start_date=start_dt, end_date=end_dt
    )

    if res_ew_reg is None or res_n50_reg is None or res_no_reg is None:
        st.warning("Not enough historical weekly data after applying the 52-week lookback gate.")
        return

    # Build Benchmark Equity Curves over the exact same date range
    bt_dates = res_ew_reg["equity_df"].index
    ew_uni_slice = weekly_data["universe_idx"].reindex(bt_dates).ffill().bfill()
    ew_uni_eq = 1_000_000.0 * (ew_uni_slice / ew_uni_slice.iloc[0]) if not ew_uni_slice.dropna().empty else pd.Series(1_000_000.0, index=bt_dates)

    n50_slice = nifty_weekly.reindex(bt_dates).ffill().bfill()
    n50_eq = 1_000_000.0 * (n50_slice / n50_slice.iloc[0]) if not n50_slice.dropna().empty else pd.Series(1_000_000.0, index=bt_dates)

    # Summary Comparison Table
    comp_rows = [
        {"Strategy / Benchmark": "1. MomentumSys (EW Universe 40w MA Filter)", **res_ew_reg["metrics"]},
        {"Strategy / Benchmark": "2. MomentumSys (Nifty 50 ^NSEI 40w MA Filter)", **res_n50_reg["metrics"]},
        {"Strategy / Benchmark": "3. MomentumSys (Unfiltered — No Regime Gate)", **res_no_reg["metrics"]},
    ]
    st.markdown("### 📊 Strategy Variants vs Benchmarks Summary")
    st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)

    # Plot Equity Curve + Drawdown + Cash Allocation
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
        row_heights=[0.52, 0.24, 0.24],
        subplot_titles=(
            "Portfolio Equity Curve (₹10 Lakh Base, Log Scale)",
            "Underwater Drawdown (%)",
            "Cash Allocation (%) & Active Slots"
        )
    )

    for label, res_obj, color, dash in [
        ("MomentumSys (EW 40w Filter)", res_ew_reg, "#00C853", "solid"),
        ("MomentumSys (^NSEI 40w Filter)", res_n50_reg, "#2962FF", "solid"),
        ("MomentumSys (No Filter)", res_no_reg, "#AA00FF", "dot")
    ]:
        eq_s = res_obj["equity_df"]["Total_Equity"]
        dd_s = ((eq_s - eq_s.cummax()) / eq_s.cummax()) * 100.0
        fig.add_trace(go.Scatter(x=eq_s.index, y=eq_s, name=label, line=dict(color=color, width=2.4, dash=dash)), row=1, col=1)
        fig.add_trace(go.Scatter(x=dd_s.index, y=dd_s, name=f"{label} DD", line=dict(color=color, width=1.6, dash=dash), showlegend=False), row=2, col=1)

    fig.add_trace(go.Scatter(x=ew_uni_eq.index, y=ew_uni_eq, name="EW Full Universe Buy & Hold", line=dict(color="#FF6D00", width=2.0, dash="dash")), row=1, col=1)
    fig.add_trace(go.Scatter(x=n50_eq.index, y=n50_eq, name="Nifty 50 (^NSEI) Buy & Hold", line=dict(color="#9E9E9E", width=1.8, dash="dash")), row=1, col=1)

    cash_s = res_ew_reg["equity_df"]["Cash_Pct"]
    fig.add_trace(go.Scatter(x=cash_s.index, y=cash_s, name="Cash % (EW Filter)", fill="tozeroy", line=dict(color="#00B8D4", width=1.5)), row=3, col=1)

    # Vertical Walk-Forward Split Line at 2020-01-01 if visible
    split_dt = pd.Timestamp("2020-01-01")
    if bt_dates.min() < split_dt < bt_dates.max():
        fig.add_vline(x=str(split_dt.date()), line_width=1.5, line_dash="dash", line_color="#FFD600")

    fig.update_yaxes(type="log", title_text="Equity (₹)", row=1, col=1)
    fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)
    fig.update_yaxes(title_text="Cash (%)", range=[0, 105], row=3, col=1)
    fig.update_layout(template="plotly_dark", height=780, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # Sensitivity Grid & Trade Log Tabs
    sub_t1, sub_t2, sub_t3 = st.tabs([
        "🎛️ Parameter Sensitivity Grid (65/75/85/95 × RSI-MA 10/20)",
        "📜 Closed Trade Log & Sector Attribution",
        "🔢 Current Week 100-Point Sector Scoreboard"
    ])

    with sub_t1:
        sens_rows = []
        for r_ma in [10, 20]:
            sb = compute_sector_scores(weekly_data, rsi_period=14, rsi_ma_period=r_ma)
            for e_th in [65, 75, 85, 95]:
                for x_th in [40, 50, 60]:
                    r_bt = run_portfolio_backtest(
                        weekly_data, sb, regime_series=weekly_data["universe_idx"],
                        entry_threshold=e_th, exit_threshold=x_th, start_date=start_dt, end_date=end_dt
                    )
                    if r_bt:
                        sens_rows.append({
                            "RSI-MA Weeks": r_ma,
                            "Entry Score ≥": e_th,
                            "Exit Score <": x_th,
                            **r_bt["metrics"]
                        })
        st.dataframe(pd.DataFrame(sens_rows), use_container_width=True, hide_index=True)

    with sub_t2:
        t_df = res_ew_reg["trades_df"]
        if not t_df.empty:
            st.dataframe(t_df.sort_values("Entry_Week_Close", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("No closed trades in the selected window.")

    with sub_t3:
        valid_score_weeks = score_bundle["score"].dropna(how="all").index
        if len(valid_score_weeks) > 0:
            last_w = valid_score_weeks[-1]
            cur_board = pd.DataFrame({
                "Sector": score_bundle["score"].columns,
                "Rank": score_bundle["rank"].loc[last_w].values,
                "Score (100)": score_bundle["score"].loc[last_w].values,
                "52W Return (%)": (score_bundle["ret_52w"].loc[last_w].values * 100.0).round(2),
                "26W Return (%)": (score_bundle["ret_26w"].loc[last_w].values * 100.0).round(2),
                "RSI(14)": score_bundle["rsi"].loc[last_w].values.round(1),
                "RSI-MA": score_bundle["rsi_ma"].loc[last_w].values.round(1),
                "Breadth (% > 0)": (weekly_data["breadth"].loc[last_w].values * 100.0).round(1),
                "Eligible Stocks (≥52W)": weekly_data["active_cnt"].loc[last_w].values
            }).sort_values(["Score (100)", "26W Return (%)"], ascending=[False, False])
            st.caption(f"Latest Signal Week Ending: **{str(last_w.date())}**")
            st.dataframe(cur_board, use_container_width=True, hide_index=True)
        else:
            st.info("No valid sector scores available.")
