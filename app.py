import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Equal-Weighted Sector Indices", layout="wide", page_icon="📈")

st.title("🏛️ Custom Equal-Weighted Index Dashboard")
st.caption("15-Year Historical Candlestick Charts with Quarterly Rebalancing | Built from Scratch")

# 1. Initialize Custom Sectors in Session State (persists during your session)
DEFAULT_SECTORS = {
    "Nifty Bank Equal-Weight": [
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS",
        "PNB.NS", "UNIONBANK.NS", "BANKBARODA.NS", "CANBK.NS", "FEDERALBNK.NS",
        "AUBANK.NS", "IDFCFIRSTB.NS", "YESBANK.NS"
    ],
    "Nifty IT Equal-Weight": [
        "TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS", "LTIM.NS", "PERSISTENT.NS", "COFORGE.NS"
    ],
    "Nifty Auto Equal-Weight": [
        "TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "EICHERMOT.NS", "TVSMOTOR.NS"
    ],
    "Nifty Pharma Equal-Weight": [
        "SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "LUPIN.NS", "AUROPHARMA.NS", "TORNTPHARM.NS"
    ]
}

if "sectors" not in st.session_state:
    st.session_state.sectors = {k: list(v) for k, v in DEFAULT_SECTORS.items()}

# Helper function to ensure .NS suffix
def format_nse_ticker(raw_sym):
    sym = raw_sym.strip().upper()
    if not sym.endswith(".NS") and not sym.endswith(".BO"):
        sym += ".NS"
    return sym

# --- SIDEBAR CONTROLS ---
st.sidebar.header("⚙️ Index Controls")

# Sector Selection
sector_options = list(st.session_state.sectors.keys())
selected_sector = st.sidebar.selectbox("Choose Sector Index", sector_options)

# Form to Create a Brand-New Sector Directly in the UI
with st.sidebar.expander("✨ Create New Custom Sector"):
    new_sec_name = st.text_input("New Sector Name (e.g. Defense)").strip()
    new_sec_tickers_raw = st.text_area("Stocks (comma-separated, e.g. HAL, BEL, MAZDOCK)").strip()
    if st.button("Create Sector"):
        if new_sec_name and new_sec_tickers_raw:
            parsed_tickers = [format_nse_ticker(t) for t in new_sec_tickers_raw.replace("\n", ",").split(",") if t.strip()]
            if parsed_tickers:
                st.session_state.sectors[new_sec_name] = parsed_tickers
                st.success(f"Created '{new_sec_name}' with {len(parsed_tickers)} stocks!")
                st.rerun()
        else:
            st.error("Please provide both a sector name and at least one stock.")

# Constituents Multiselect for Selected Sector
current_constituents = st.session_state.sectors[selected_sector]
selected_stocks = st.sidebar.multiselect(
    "Constituents (Toggle Stocks)",
    options=current_constituents,
    default=current_constituents
)

# Quick Form to Add a Single Stock to the Current Sector
with st.sidebar.expander(f"➕ Add Stock to '{selected_sector}'"):
    new_stock_input = st.text_input("Enter NSE Ticker (e.g. INDUSINDBK or BANDHANBNK)").strip()
    if st.button("Add to Current Sector"):
        if new_stock_input:
            formatted_stock = format_nse_ticker(new_stock_input)
            if formatted_stock not in current_constituents:
                st.session_state.sectors[selected_sector].append(formatted_stock)
                st.success(f"Added {formatted_stock}!")
                st.rerun()
            else:
                st.info(f"{formatted_stock} is already in this sector.")

base_value = st.sidebar.number_input("Starting Base Value", min_value=100.0, max_value=50000.0, value=1000.0, step=100.0)

if not selected_stocks:
    st.warning("Please select at least one stock to calculate the index.")
    st.stop()

# --- FAST CACHED DATA LOADER ---
@st.cache_data(ttl=3600)
def fetch_sector_data(tickers):
    data_dict = {}
    for t in tickers:
        try:
            df = yf.Ticker(t).history(period="15y", auto_adjust=True)
            if not df.empty and "Close" in df.columns:
                df = df[["Open", "High", "Low", "Close"]]
                df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
                data_dict[t] = df
        except Exception:
            pass
    return data_dict

with st.spinner("Loading market data and computing index..."):
    all_data = fetch_sector_data(tuple(selected_stocks))

# Validate that data was fetched
valid_stocks = [t for t in selected_stocks if t in all_data and not all_data[t].empty]
if not valid_stocks:
    st.error("Could not retrieve market data for the selected stocks. Please verify the ticker symbols.")
    st.stop()

# Align Prices
close_df = pd.DataFrame({t: all_data[t]["Close"] for t in valid_stocks}).sort_index().ffill()
open_df  = pd.DataFrame({t: all_data[t]["Open"]  for t in valid_stocks}).sort_index().fillna(close_df)
high_df  = pd.DataFrame({t: all_data[t]["High"]  for t in valid_stocks}).sort_index().fillna(close_df)
low_df   = pd.DataFrame({t: all_data[t]["Low"]   for t in valid_stocks}).sort_index().fillna(close_df)

# Quarterly Rebalancing Engine
quarter_labels = close_df.index.to_period("Q")
unique_q = quarter_labels.unique()

index_records = []
current_val = float(base_value)

for q in unique_q:
    q_mask = (quarter_labels == q)
    dates = close_df.index[q_mask]
    first_prices = close_df.loc[dates[0]].dropna()
    active = first_prices.index
    
    if len(active) == 0:
        continue
        
    pts = current_val / len(active)
    shares = pts / first_prices
    
    q_o = open_df.loc[dates, active].multiply(shares, axis=1).sum(axis=1)
    q_h = high_df.loc[dates, active].multiply(shares, axis=1).sum(axis=1)
    q_l = low_df.loc[dates, active].multiply(shares, axis=1).sum(axis=1)
    q_c = close_df.loc[dates, active].multiply(shares, axis=1).sum(axis=1)
    
    for d in dates:
        index_records.append({
            "Date": d,
            "Open": round(q_o.loc[d], 2),
            "High": round(q_h.loc[d], 2),
            "Low": round(q_l.loc[d], 2),
            "Close": round(q_c.loc[d], 2),
        })
    current_val = q_c.iloc[-1]

index_df = pd.DataFrame(index_records).set_index("Date")

# Calculate Overall 15-Year Metrics
start_val = index_df["Close"].iloc[0]
latest_val = index_df["Close"].iloc[-1]
tot_return = ((latest_val - start_val) / start_val) * 100

peak = index_df["Close"].cummax()
dd = (index_df["Close"] - peak) / peak
max_dd = dd.min() * 100

# Top Metric Cards
m1, m2, m3, m4 = st.columns(4)
m1.metric("Current Index Value", f"{latest_val:,.2f}")
m2.metric("Total 15Y Return", f"{tot_return:+,.1f}%")
m3.metric("Max 15Y Drawdown", f"{max_dd:.1f}%")
m4.metric("Active Constituents", f"{len(valid_stocks)} Stocks")

# --- TRADINGVIEW-STYLE TABS ---
tab_custom, tab_macro, tab_constituents = st.tabs([
    "⏱️ Custom Window (Weeks / Range)",
    "🌐 Full 15-Year Macro (Monthly)",
    "⚖️ Constituent Stock Breakdown"
])

# --- TAB 1: CUSTOM TIMEFRAME BY NUMBER OF WEEKS ---
with tab_custom:
    st.subheader("🎯 Zoom Into a Specific Window")
    
    col_ctrl1, col_ctrl2 = st.columns([2, 1])
    
    with col_ctrl1:
        num_weeks = st.slider(
            "Select Lookback Window (in Weeks):",
            min_value=1,
            max_value=260,
            value=12,
            step=1,
            help="Choose how many weeks of history to display (e.g., 4 weeks = 1 month, 52 weeks = 1 year)."
        )
        
    with col_ctrl2:
        candle_type = st.radio(
            "Candle Granularity for this Window:",
            ["Daily Candlesticks", "Weekly Candlesticks"],
            index=0
        )
    
    # Filter data to ONLY the chosen number of weeks
    cutoff_date = index_df.index.max() - pd.Timedelta(weeks=num_weeks)
    window_df = index_df[index_df.index >= cutoff_date]
    
    if "Weekly" in candle_type:
        chart_window_data = window_df.resample("W-FRI").agg({
            "Open": "first", "High": "max", "Low": "min", "Close": "last"
        }).dropna()
    else:
        chart_window_data = window_df

    # Window-specific metrics
    win_start_val = window_df["Close"].iloc[0]
    win_end_val = window_df["Close"].iloc[-1]
    win_return = ((win_end_val - win_start_val) / win_start_val) * 100
    win_high = window_df["High"].max()
    win_low = window_df["Low"].min()
    
    w1, w2, w3, w4 = st.columns(4)
    w1.metric(f"Return (Last {num_weeks} Weeks)", f"{win_return:+,.2f}%")
    w2.metric("Window High", f"{win_high:,.2f}")
    w3.metric("Window Low", f"{win_low:,.2f}")
    w4.metric("Candles Displayed", f"{len(chart_window_data)}")
    
    # Render Custom Candlestick Chart
    fig_custom = go.Figure(data=[
        go.Candlestick(
            x=chart_window_data.index,
            open=chart_window_data["Open"],
            high=chart_window_data["High"],
            low=chart_window_data["Low"],
            close=chart_window_data["Close"],
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
            name=f"{selected_sector} (Last {num_weeks} W)"
        )
    ])
    
    fig_custom.update_layout(
        title=f"{selected_sector} — Candlesticks for Last {num_weeks} Weeks ({str(cutoff_date.date())} to {str(index_df.index.max().date())})",
        template="plotly_dark",
        yaxis_title="Index Value",
        xaxis_rangeslider_visible=False,
        height=600,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    st.plotly_chart(fig_custom, use_container_width=True)

# --- TAB 2: FULL 15-YEAR MONTHLY MACRO ---
with tab_macro:
    st.subheader("🌐 Complete 15-Year Macro Overview (Monthly Candles)")
    monthly_data = index_df.resample("ME").agg({
        "Open": "first", "High": "max", "Low": "min", "Close": "last"
    }).dropna()
    
    fig_macro = go.Figure(data=[
        go.Candlestick(
            x=monthly_data.index,
            open=monthly_data["Open"],
            high=monthly_data["High"],
            low=monthly_data["Low"],
            close=monthly_data["Close"],
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
            name="15Y Monthly"
        )
    ])
    
    fig_macro.update_layout(
        title=f"{selected_sector} — 15-Year Historical Macro ({len(monthly_data)} Monthly Candlesticks)",
        template="plotly_dark",
        yaxis_title="Index Value",
        xaxis_rangeslider_visible=False,
        height=600,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig_macro, use_container_width=True)

# --- TAB 3: CONSTITUENTS BREAKDOWN ---
with tab_constituents:
    st.subheader(f"⚖️ {selected_sector} Constituents")
    breakdown_list = []
    for t in valid_stocks:
        if t in all_data and not all_data[t].empty:
            stk_first = all_data[t]["Close"].iloc[0]
            stk_latest = all_data[t]["Close"].iloc[-1]
            stk_ret = ((stk_latest - stk_first) / stk_first) * 100
            breakdown_list.append({
                "Ticker": t,
                "Latest Close (Rs)": round(stk_latest, 2),
                "Historical Return (%)": round(stk_ret, 1),
                "First Available Date": str(all_data[t].index[0].date()),
                "Target Weight": f"{round(100/len(valid_stocks), 2)}%"
            })
    
    st.dataframe(pd.DataFrame(breakdown_list), use_container_width=True)
