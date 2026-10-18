import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Equal-Weighted Sector Indices", layout="wide", page_icon="📈")

st.title("🏛️ Custom Equal-Weighted Index Dashboard")
st.caption("15-Year Historical Candlestick Charts with Quarterly Rebalancing | Built from Scratch")

# Sector Presets (Editable)
SECTORS = {
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

# Sidebar Controls
st.sidebar.header("⚙️ Index Controls")
selected_sector = st.sidebar.selectbox("Choose Sector Index", list(SECTORS.keys()))
default_constituents = SECTORS[selected_sector]

selected_stocks = st.sidebar.multiselect(
    "Constituents (Add/Remove Stocks)",
    options=default_constituents,
    default=default_constituents
)

base_value = st.sidebar.number_input("Starting Base Value", min_value=100.0, max_value=50000.0, value=1000.0, step=100.0)
timeframe = st.sidebar.radio("Candlestick Timeframe", ["Monthly (15-Year Macro — Cleanest)", "Weekly (Medium-Term)", "Daily (Recent)"])

if not selected_stocks:
    st.warning("Please select at least one stock to calculate the index.")
    st.stop()

# Fast Data Loader with 1-hour cache
@st.cache_data(ttl=3600)
def fetch_sector_data(tickers):
    data_dict = {}
    for t in tickers:
        df = yf.Ticker(t).history(period="15y", auto_adjust=True)
        if not df.empty:
            df = df[["Open", "High", "Low", "Close"]]
            df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
            data_dict[t] = df
    return data_dict

with st.spinner("Loading market data and computing index..."):
    all_data = fetch_sector_data(tuple(selected_stocks))

# Align Prices
close_df = pd.DataFrame({t: all_data[t]["Close"] for t in selected_stocks if t in all_data}).sort_index().ffill()
open_df  = pd.DataFrame({t: all_data[t]["Open"]  for t in selected_stocks if t in all_data}).sort_index().fillna(close_df)
high_df  = pd.DataFrame({t: all_data[t]["High"]  for t in selected_stocks if t in all_data}).sort_index().fillna(close_df)
low_df   = pd.DataFrame({t: all_data[t]["Low"]   for t in selected_stocks if t in all_data}).sort_index().fillna(close_df)

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

# Calculate Performance Metrics
start_val = index_df["Close"].iloc[0]
latest_val = index_df["Close"].iloc[-1]
tot_return = ((latest_val - start_val) / start_val) * 100

peak = index_df["Close"].cummax()
dd = (index_df["Close"] - peak) / peak
max_dd = dd.min() * 100

# Metric Cards
m1, m2, m3, m4 = st.columns(4)
m1.metric("Current Index Value", f"{latest_val:,.2f}")
m2.metric("Total Return", f"{tot_return:+,.1f}%")
m3.metric("Max Drawdown", f"{max_dd:.1f}%")
m4.metric("Active Constituents", f"{len(selected_stocks)} Stocks")

# Resample based on user choice
if "Monthly" in timeframe:
    chart_data = index_df.resample("ME").agg({"Open":"first","High":"max","Low":"min","Close":"last"}).dropna()
elif "Weekly" in timeframe:
    chart_data = index_df.resample("W-FRI").agg({"Open":"first","High":"max","Low":"min","Close":"last"}).dropna()
else:
    chart_data = index_df

# Interactive Candlestick Chart
fig = go.Figure(data=[
    go.Candlestick(
        x=chart_data.index,
        open=chart_data["Open"],
        high=chart_data["High"],
        low=chart_data["Low"],
        close=chart_data["Close"],
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350",
        name=selected_sector
    )
])

fig.update_layout(
    template="plotly_dark",
    yaxis_title="Index Value",
    xaxis_rangeslider_visible=False,
    height=600,
    margin=dict(l=10, r=10, t=30, b=10)
)

st.plotly_chart(fig, use_container_width=True)
