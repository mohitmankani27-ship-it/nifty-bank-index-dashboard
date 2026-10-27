# ==============================================================================
# MODULE: MOMENTUMSYS SECTOR & STOCK SCOREBOARD (sector_backtest.py)
# ==============================================================================
import json
import numpy as np
import pandas as pd
import streamlit as st


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
    - Computes weekly Close-to-Close returns for equal-weight sector indices.
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
    w_close = daily_close.resample("W-FRI").last().dropna(how="all")
    w_bad_days_22d = bad_days_22d.resample("W-FRI").last().reindex(w_close.index).fillna(0.0)

    # Stock-level weekly return matrices
    prev_c = w_close.shift(1)
    stk_ret_cc = (w_close / prev_c) - 1.0

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

    # Clean stock return matrices for index chaining
    ret_cc_clean = stk_ret_cc.where(stk_ipo_eligible)
    pos_52w_clean = (stk_ret_52w > 0.0).astype(float).where(stk_ipo_eligible)

    weeks = w_close.index
    sector_names = list(sectors_dict.keys())

    sec_close_idx = pd.DataFrame(index=weeks, columns=sector_names, dtype=float)
    sec_breadth = pd.DataFrame(index=weeks, columns=sector_names, dtype=float)
    sec_active_cnt = pd.DataFrame(index=weeks, columns=sector_names, dtype=int)
    sec_peer_median_52w = pd.DataFrame(index=weeks, columns=sector_names, dtype=float)

    for sec, tickers in sectors_dict.items():
        cols = [t for t in tickers if t in ret_cc_clean.columns]
        if not cols:
            continue

        r_cc = ret_cc_clean[cols].mean(axis=1)
        brd = pos_52w_clean[cols].mean(axis=1)
        cnt = stk_ipo_eligible[cols].sum(axis=1).astype(int)
        peer_med = stk_ret_52w.where(stk_ipo_eligible)[cols].median(axis=1)

        first_valid = r_cc.first_valid_index()
        if first_valid is not None:
            r_cc_filled = r_cc.loc[first_valid:].fillna(0.0)
            idx_series = 100.0 * (1.0 + r_cc_filled).cumprod()
            sec_close_idx.loc[idx_series.index, sec] = idx_series

        sec_breadth[sec] = brd
        sec_active_cnt[sec] = cnt
        sec_peer_median_52w[sec] = peer_med

    non_empty_idx = sec_close_idx.dropna(how="all").index
    valid_start = non_empty_idx.min() if len(non_empty_idx) > 0 else weeks[0]

    return {
        "close_idx": sec_close_idx.loc[valid_start:],
        "breadth": sec_breadth.loc[valid_start:],
        "active_cnt": sec_active_cnt.loc[valid_start:],
        "peer_median_52w": sec_peer_median_52w.loc[valid_start:],
        # Stock-level weekly matrices
        "stk_close": w_close.loc[valid_start:],
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
def compute_stock_indicators(_weekly_data, sectors_json, cache_ts_key, rsi_period=14, rsi_ma_period=20):
    """
    Precomputes stock-level technical indicators, the 5 sector-independent
    score components (out of 87.5 pts), and the vectorized per-sector C1,
    total score, and 1W/2W/3W lagged score matrices so score_stocks_in_sector_at_week
    requires zero per-ticker or per-week loops.
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
    sectors_dict = json.loads(sectors_json)
    stk_close = _weekly_data["stk_close"]
    stk_elig = _weekly_data["stk_ipo_eligible"]
    stk_ret_52w = _weekly_data["stk_ret_52w"]
    peer_med_df = _weekly_data["peer_median_52w"]

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

    # Precompute vectorized C1, total score, and shifted (-1W, -2W, -3W) matrices per sector
    c1_by_sec = {}
    score_by_sec = {}
    score_m1w_by_sec = {}
    score_m2w_by_sec = {}
    score_m3w_by_sec = {}

    for sec, tickers in sectors_dict.items():
        cols = [t for t in tickers if t in stk_close.columns]
        if not cols:
            continue
        med_s = peer_med_df[sec]
        c1_df = (
            stk_ret_52w[cols].gt(med_s, axis=0)
            & stk_elig[cols]
            & med_s.notna().values[:, None]
        ).astype(float) * 12.5
        sc_mat = base_score_875[cols] + c1_df
        c1_by_sec[sec] = c1_df
        score_by_sec[sec] = sc_mat
        score_m1w_by_sec[sec] = sc_mat.shift(1)
        score_m2w_by_sec[sec] = sc_mat.shift(2)
        score_m3w_by_sec[sec] = sc_mat.shift(3)

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
        "c1_by_sec": c1_by_sec,
        "score_by_sec": score_by_sec,
        "score_m1w_by_sec": score_m1w_by_sec,
        "score_m2w_by_sec": score_m2w_by_sec,
        "score_m3w_by_sec": score_m3w_by_sec,
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
    Uses precomputed vectorized score and lag matrices (zero per-ticker loops).
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

    if sec_name in stk_ind.get("score_by_sec", {}):
        c1_pts = stk_ind["c1_by_sec"][sec_name].loc[dt_sig, tickers]
        tot_score = stk_ind["score_by_sec"][sec_name].loc[dt_sig, tickers]
        sc_m1w = stk_ind["score_m1w_by_sec"][sec_name].loc[dt_sig, tickers]
        sc_m2w = stk_ind["score_m2w_by_sec"][sec_name].loc[dt_sig, tickers]
        sc_m3w = stk_ind["score_m3w_by_sec"][sec_name].loc[dt_sig, tickers]
    else:
        c1_pts = ((ret_52w_s > peer_med) & elig_s & pd.notna(peer_med)).astype(float) * 12.5
        tot_score = (stk_ind["base_score_875"].loc[dt_sig, tickers] + c1_pts).where(elig_s, np.nan)
        sc_m1w = pd.Series(np.nan, index=tickers)
        sc_m2w = pd.Series(np.nan, index=tickers)
        sc_m3w = pd.Series(np.nan, index=tickers)

    c2_pts = stk_ind["c2_rsi_60"].loc[dt_sig, tickers]
    c3_pts = stk_ind["c3_rsi_above_ma"].loc[dt_sig, tickers]
    c4_pts = stk_ind["c4_gap_4w"].loc[dt_sig, tickers]
    c5_pts = stk_ind["c5_recent_high"].loc[dt_sig, tickers]
    c6_pts = stk_ind["c6_near_high"].loc[dt_sig, tickers]

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
        "Score_-1W": sc_m1w.values,
        "Score_-2W": sc_m2w.values,
        "Score_-3W": sc_m3w.values,
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
# 3. STREAMLIT RENDERER: FAST SECTOR & STOCK DRILL-SCOREBOARDS (NO BACKTEST LOOP)
# ------------------------------------------------------------------------------
def render_backtest_tab(raw_disk_ohlc, sectors_dict, cache_ts_key, fetch_benchmark_fn=None):
    st.subheader("🏛️ MomentumSys — Sector & Stock Drill-Scoreboard")
    st.caption(
        "Instant Vectorized Scoring (Backtest Loop Removed for Zero Lag) | "
        "IPO Gate (≥52W) + 22D Circuit Filter (O=C=H or O=C=L ≤ 6 Days)"
    )

    sectors_json = json.dumps(sectors_dict, sort_keys=True)

    with st.spinner("Computing weekly sector & stock score matrices..."):
        weekly_data = build_weekly_master_data(
            raw_disk_ohlc,
            sectors_json,
            cache_ts_key
        )
        stk_ind = compute_stock_indicators(weekly_data, sectors_json, cache_ts_key, rsi_period=14, rsi_ma_period=20)
        sec_score_bundle = compute_sector_scores(weekly_data, rsi_period=14, rsi_ma_period=20)

    valid_score_weeks = sec_score_bundle["score"].dropna(how="all").index
    if len(valid_score_weeks) == 0:
        st.info("No valid sector scores available.")
        return

    # Optional Friday selector so you can inspect the latest week or any historical Friday instantaneously
    col_mode, col_date = st.columns([1, 2])
    with col_mode:
        view_mode = st.radio(
            "Scoreboard Week:",
            ["🟢 Latest Completed Friday", "⏪ Pick Historical Friday"],
            horizontal=False
        )
    with col_date:
        if "Latest" in view_mode:
            selected_w = valid_score_weeks[-1]
            st.info(f"🔒 **As-Of Latest Completed Friday Close: `{str(selected_w.date())}`**")
        else:
            week_labels = [str(d.date()) for d in valid_score_weeks]
            chosen_w_str = st.select_slider(
                "Select Historical Friday Close:",
                options=week_labels,
                value=week_labels[-1]
            )
            selected_w = pd.Timestamp(chosen_w_str)
            st.success(f"🔒 **Viewing Historical Scoreboard As Of Friday Close: `{str(selected_w.date())}`**")

    drill_tab, score_tab = st.tabs([
        "🔍 1. Sector & Stock Drill-Scoreboard",
        "🔢 2. Current Week 100-Point Sector Scoreboard"
    ])

    # ==========================================================================
    # SUB-TAB 1: SECTOR & STOCK DRILL-SCOREBOARD
    # ==========================================================================
    with drill_tab:
        st.markdown("### 🔍 Sector & Stock Drill-Scoreboard")
        st.caption(f"Signal Week Ending: **{str(selected_w.date())}**")

        summary_rows = []
        sec_drill_dfs = {}

        for sec_name in sec_score_bundle["score"].columns:
            sec_df = score_stocks_in_sector_at_week(sec_name, selected_w, sectors_dict, weekly_data, stk_ind)
            if not sec_df.empty:
                sec_df_sorted = sec_df.sort_values(
                    by=["Stock_Score", "_ret26_raw"],
                    ascending=[False, False]
                ).reset_index(drop=True)
                n75 = int((sec_df_sorted["Stock_Score"] >= 75.0).sum())
                n100 = int((sec_df_sorted["Stock_Score"] >= 99.9).sum())
            else:
                sec_df_sorted = sec_df
                n75, n100 = 0, 0

            sec_drill_dfs[sec_name] = sec_df_sorted
            summary_rows.append({
                "Sector": sec_name,
                "Sector Rank": sec_score_bundle["rank"].loc[selected_w, sec_name],
                "Sector Score": sec_score_bundle["score"].loc[selected_w, sec_name],
                "Stocks ≥ 75": n75,
                "Stocks = 100": n100,
                "_ret26": sec_score_bundle["ret_26w"].loc[selected_w, sec_name]
            })

        sum_df = pd.DataFrame(summary_rows)
        sum_df_by_score = sum_df.sort_values(
            by=["Sector Score", "_ret26"],
            ascending=[False, False]
        ).reset_index(drop=True)

        st.dataframe(
            sum_df_by_score[["Sector", "Sector Rank", "Sector Score", "Stocks ≥ 75", "Stocks = 100"]],
            use_container_width=True,
            hide_index=True
        )

        only_100 = st.toggle("Show only stocks scoring 100", value=False)

        sum_df_by_rank = sum_df.sort_values(
            by=["Sector Rank", "Sector Score", "_ret26"],
            ascending=[True, False, False]
        ).reset_index(drop=True)

        for _, srow in sum_df_by_rank.iterrows():
            sec_name = srow["Sector"]
            n75 = int(srow["Stocks ≥ 75"])
            n100 = int(srow["Stocks = 100"])
            exp_label = f"📂 {sec_name} | ≥75: {n75} | =100: {n100}"

            with st.expander(exp_label, expanded=False):
                sdf = sec_drill_dfs.get(sec_name, pd.DataFrame())
                if not sdf.empty:
                    if only_100:
                        filt_df = sdf[sdf["Stock_Score"] >= 99.9].copy()
                    else:
                        filt_df = sdf[sdf["Stock_Score"] >= 75.0].copy()
                else:
                    filt_df = pd.DataFrame()

                if not filt_df.empty:
                    filt_df = filt_df.rename(columns={
                        "Pct_From_52W_High (%)": "Proximity to 52W High (%)",
                        "26W_Ret (%)": "26W Return (%)"
                    })
                    drill_cols = [
                        "Ticker", "Stock_Score", "Score_-1W", "Score_-2W", "Score_-3W",
                        "Proximity to 52W High (%)", "26W Return (%)",
                        "RSI(14)", "Close", "Entry_Filter_OK", "Bad_Days_22D"
                    ]
                    st.dataframe(filt_df[drill_cols], use_container_width=True, hide_index=True)
                else:
                    if only_100:
                        st.caption("No stocks in this sector scored 100 this week.")
                    else:
                        st.caption("No stocks in this sector scored ≥ 75 this week.")

    # ==========================================================================
    # SUB-TAB 2: CURRENT WEEK 100-POINT SECTOR SCOREBOARD
    # ==========================================================================
    with score_tab:
        st.markdown("### 🔢 100-Point Sector Scoreboard")
        cur_board = pd.DataFrame({
            "Sector": sec_score_bundle["score"].columns,
            "Rank": sec_score_bundle["rank"].loc[selected_w].values,
            "Score (100)": sec_score_bundle["score"].loc[selected_w].values,
            "52W Return (%)": (sec_score_bundle["ret_52w"].loc[selected_w].values * 100.0).round(2),
            "26W Return (%)": (sec_score_bundle["ret_26w"].loc[selected_w].values * 100.0).round(2),
            "RSI(14)": sec_score_bundle["rsi"].loc[selected_w].values.round(1),
            "RSI-MA": sec_score_bundle["rsi_ma"].loc[selected_w].values.round(1),
            "Breadth (% > 0)": (weekly_data["breadth"].loc[selected_w].values * 100.0).round(1),
            "Eligible Stocks (≥52W)": weekly_data["active_cnt"].loc[selected_w].values
        }).sort_values(["Score (100)", "26W Return (%)"], ascending=[False, False])
        st.caption(f"Signal Week Ending: **{str(selected_w.date())}**")
        st.dataframe(cur_board, use_container_width=True, hide_index=True)
