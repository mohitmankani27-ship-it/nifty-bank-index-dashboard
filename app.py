import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Equal-Weighted Sector Indices", layout="wide", page_icon="📈")

st.title("🏛️ Custom Equal-Weighted Sector Dashboard")
st.caption("26 Indian Sector Indices | 15-Year Historical Candlesticks | Built from Scratch")

# 1. Master Sector Directory (26 Sectors + Jewellery)
DEFAULT_SECTORS = {
    "1. Banking (PSU & Private)": [
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS",
        "PNB.NS", "UNIONBANK.NS", "BANKBARODA.NS", "CANBK.NS", "FEDERALBNK.NS",
        "AUBANK.NS", "IDFCFIRSTB.NS", "YESBANK.NS", "INDUSINDBK.NS", "BANDHANBNK.NS",
        "RBLBANK.NS", "CUB.NS", "KARURVYSYA.NS", "SOUTHBANK.NS", "J&KBANK.NS",
        "MAHABANK.NS", "CENTRALBK.NS", "PSB.NS", "IOB.NS", "UCOBANK.NS",
        "CSBBANK.NS", "KTKBANK.NS", "EQUITASBNK.NS", "JSFB.NS", "UTKARSHBNK.NS",
        "SURYODAY.NS", "ESAFSFB.NS", "UJJIVANSFB.NS"
    ],
    "2. Information Technology": [
        "TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS",
        "LTM.NS", "PERSISTENT.NS", "COFORGE.NS", "MPHASIS.NS", "TATAELXSI.NS",
        "LTTS.NS", "OFSS.NS", "CYIENT.NS", "BSOFT.NS", "KPITTECH.NS",
        "ZENSARTECH.NS", "SONATSOFTW.NS", "MASTEK.NS", "FSL.NS", "SAKSOFT.NS",
        "SASKEN.NS", "NEWGEN.NS", "RSYSTEMS.NS", "HAPPSTMNDS.NS", "E2E.NS",
        "ECLERX.NS", "DATAMATICS.NS", "NUCLEUS.NS", "RAMCOSYS.NS", "INFOBEAN.NS"
    ],
    "3. Automobile (OEMs & EVs)": [
        "MARUTI.NS", "M&M.NS", "TATAMOTORS.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS",
        "TVSMOTOR.NS", "EICHERMOT.NS", "ASHOKLEY.NS", "HYUNDAI.NS", "FORCEMOT.NS",
        "TMPV.NS", "TMCV.NS", "OLAELEC.NS", "ATHERENERG.NS", "ESCORTS.NS",
        "SMLMAH.NS", "VSTTILLERS.NS"
    ],
    "4. Auto Components & Ancillaries": [
        "MOTHERSON.NS", "BHARATFORG.NS", "BOSCHLTD.NS", "UNOMINDA.NS", "ENDURANCE.NS",
        "SONACOMS.NS", "MRF.NS", "BALKRISIND.NS", "CEATLTD.NS", "APOLLOTYRE.NS",
        "JKTYRE.NS", "EXIDEIND.NS", "AMBER.NS", "SCHAEFFLER.NS", "SKFINDIA.NS",
        "CRAFTSMAN.NS", "SANSERA.NS", "TIMKEN.NS", "GABRIEL.NS", "CIEINDIA.NS",
        "LUMAXIND.NS", "LUMAXTECH.NS", "FIEMIND.NS", "ROLEXRINGS.NS", "GNA.NS",
        "AUTOAXLES.NS", "RACLGEAR.NS", "TALBROAUTO.NS", "PRICOLLTD.NS", "SUBROS.NS",
        "SURYAROSNI.NS", "BALUFORGE.NS", "SHARDAMOTR.NS", "HAPPYFORGE.NS", "MSUMI.NS"
    ],
    "5. Pharmaceuticals & Formulations": [
        "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "LUPIN.NS", "TORNTPHARM.NS",
        "AUROPHARMA.NS", "ZYDUSLIFE.NS", "MANKIND.NS", "ALKEM.NS", "GLENMARK.NS",
        "LAURUSLABS.NS", "IPCALAB.NS", "BIOCON.NS", "AJANTPHARM.NS", "GLAXO.NS",
        "PFIZER.NS", "SANOFI.NS", "ABBOTINDIA.NS", "NATCOPHARM.NS", "ERIS.NS",
        "JUBLPHARMA.NS", "STAR.NS", "MARKSANS.NS", "FDC.NS", "UNICHEMLAB.NS",
        "CORONA.NS", "WOCKPHARMA.NS", "CAPLIPOINT.NS"
    ],
    "6. Healthcare, Hospitals & Diagnostics": [
        "APOLLOHOSP.NS", "MAXHEALTH.NS", "FORTIS.NS", "MEDANTA.NS", "NH.NS",
        "KIMS.NS", "ASTERDM.NS", "RAINBOW.NS", "LALPATHLAB.NS", "METROPOLIS.NS",
        "VIJAYA.NS", "THYROCARE.NS", "ARTEMISMED.NS", "KOVAI.NS", "YATHARTH.NS",
        "JLHL.NS", "KRSNAA.NS", "SURAKSHA.NS", "DRAGARWQ.NS"
    ],
    "7. API, CDMO & Life Sciences": [
        "DIVISLAB.NS", "LAURUSLABS.NS", "SYNGENE.NS", "SOLARA.NS", "SMSPHARMA.NS",
        "GRANULES.NS", "NEULANDLAB.NS", "AARTIPHARM.NS", "SUPRIYA.NS", "SUDEEPPHRM.NS",
        "ANTHEM.NS", "SAILIFE.NS", "ALIVUS.NS", "RPGLIFE.NS", "NGLFINE.NS",
        "GUJTHEM.NS", "VIYASH.NS", "CONCORDBIO.NS"
    ],
    "8. Chemicals & Petrochemicals": [
        "SRF.NS", "DEEPAKNTR.NS", "PIIND.NS", "TATACHEM.NS", "AARTIIND.NS",
        "NAVINFLUOR.NS", "FLUOROCHEM.NS", "ATUL.NS", "FINEORG.NS", "SUMICHEM.NS",
        "VINATIORGA.NS", "ALKYLAMINE.NS", "BALAMINES.NS", "NOCIL.NS", "HSCL.NS",
        "CLEAN.NS", "ANURAS.NS", "AETHER.NS", "ROSSARI.NS", "EPIGRAL.NS",
        "PRIVISCL.NS", "CAMLINFINE.NS", "PCBL.NS", "GUJALKALI.NS", "GRAUWEIL.NS"
    ],
    "9. Agrochemicals & Fertilizers": [
        "UPL.NS", "PIIND.NS", "COROMANDEL.NS", "BAYERCROP.NS", "SUMICHEM.NS",
        "FACT.NS", "RCF.NS", "GNFC.NS", "GSFC.NS", "CHAMBLFERT.NS",
        "DEEPAKFERT.NS", "SHARDACROP.NS", "DHANUKA.NS", "INSECTICID.NS", "BHARATRAS.NS",
        "NACLIND.NS", "NFL.NS", "MBAPL.NS", "PARADEEP.NS"
    ],
    "10. Metals, Mining & Steel": [
        "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "JINDALSTEL.NS", "VEDL.NS",
        "SAIL.NS", "NMDC.NS", "COALINDIA.NS", "NATIONALUM.NS", "HINDZINC.NS",
        "HINDCOPPER.NS", "JSL.NS", "APLAPOLLO.NS", "WELCORP.NS", "JINDALSAW.NS",
        "RATNAMANI.NS", "GPIL.NS", "SHYAMMETL.NS", "KSL.NS", "MAHASTEEL.NS",
        "PRAKASH.NS", "MOIL.NS", "KIOCL.NS", "ORISSAMINE.NS"
    ],
    "11. Cement & Building Materials": [
        "ULTRACEMCO.NS", "AMBUJACEM.NS", "ACC.NS", "SHREECEM.NS", "DALBHARAT.NS",
        "JSWCEMENT.NS", "RAMCOCEM.NS", "JKCEMENT.NS", "JKLAKSHMI.NS", "HEIDELBERG.NS",
        "STARCEMENT.NS", "MANGLMCEM.NS", "BIRLACORPN.NS", "SAGCEM.NS", "KCP.NS",
        "PRSMJOHNSN.NS", "ORIENTCEM.NS", "ASIANPAINT.NS", "BERGEPAINT.NS", "INDIGOPNTS.NS", "KANSAINER.NS"
    ],
    "12. Real Estate & Urban Developers": [
        "DLF.NS", "LODHA.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "PRESTIGE.NS",
        "PHOENIXLTD.NS", "BRIGADE.NS", "SOBHA.NS", "SIGNATURE.NS", "ANANTRAJ.NS",
        "MAHLIFE.NS", "SUNTECK.NS", "PURVA.NS", "KOLTEPATIL.NS", "ASHIANA.NS",
        "OMAXE.NS", "MARATHON.NS", "AJMERA.NS", "HUBTOWN.NS", "ARKADE.NS",
        "RUSTOMJEE.NS", "MAXESTATES.NS"
    ],
    "13. Infrastructure, EPC & Rail": [
        "LT.NS", "RVNL.NS", "IRCON.NS", "NCC.NS", "NBCC.NS",
        "PNCINFRA.NS", "GRINFRA.NS", "DBL.NS", "KNRCON.NS", "HCC.NS",
        "AFCONS.NS", "ASHOKA.NS", "HGINFRA.NS", "CEIGALL.NS", "PSPPROJECT.NS",
        "AHLUCONT.NS", "JKIL.NS", "PATELENG.NS", "GPTINFRA.NS", "BAJEL.NS",
        "TRANSRAILL.NS", "TITAGARH.NS", "TEXRAIL.NS"
    ],
    "14. Power Generation & Utilities": [
        "NTPC.NS", "TATAPOWER.NS", "JSWENERGY.NS", "POWERGRID.NS", "ADANIPOWER.NS",
        "ADANIENSOL.NS", "NHPC.NS", "SJVN.NS", "CESC.NS", "TORNTPOWER.NS",
        "NLCINDIA.NS", "RTNPOWER.NS", "JPPOWER.NS", "BGRENERGY.NS", "GIPCL.NS",
        "GMRP&UI.NS", "PTC.NS"
    ],
    "15. Renewable Energy & Green Transition": [
        "ADANIGREEN.NS", "SUZLON.NS", "INOXWIND.NS", "WAAREEENER.NS", "WAAREERTL.NS",
        "PREMIERENE.NS", "IREDA.NS", "NTPCGREEN.NS", "KPIGREEN.NS", "SWSOLAR.NS",
        "BORORENEW.NS", "INOXGREEN.NS", "VIKRAMSOLR.NS", "CLEANMAX.NS", "WEBELSOLAR.NS",
        "SAATVIKGL.NS", "UEL.NS"
    ],
    "16. Electrical Equipment & Cables": [
        "ABB.NS", "SIEMENS.NS", "BHEL.NS", "CGPOWER.NS", "POWERINDIA.NS",
        "GVT&D.NS", "HAVELLS.NS", "POLYCAB.NS", "KEI.NS", "FINCABLES.NS",
        "RRKABEL.NS", "VOLTAMP.NS", "TARIL.NS", "ENRIN.NS", "SCHNEIDER.NS",
        "HPL.NS", "GENUSPOWER.NS", "INDOTECH.NS", "QPOWER.NS", "TDPOWERSYS.NS",
        "SPECTRUM.NS", "DIACABS.NS"
    ],
    "17. Defense, Aerospace & Space Tech": [
        "HAL.NS", "BEL.NS", "BDL.NS", "MAZDOCK.NS", "COCHINSHIP.NS",
        "GRSE.NS", "BEML.NS", "PARAS.NS", "DATAPATTNS.NS", "MTARTECH.NS",
        "ZENTEC.NS", "IDEAFORGE.NS", "APOLLO.NS", "KRISHNADEF.NS", "SWANDEF.NS",
        "SIKA.NS", "ROSSTECH.NS", "UNIMECH.NS", "DYNAMATECH.NS", "AZAD.NS"
    ],
    "18. Oil, Gas & Energy Distribution": [
        "RELIANCE.NS", "ONGC.NS", "IOC.NS", "BPCL.NS", "HINDPETRO.NS",
        "GAIL.NS", "PETRONET.NS", "IGL.NS", "MGL.NS", "ATGL.NS",
        "OIL.NS", "MRPL.NS", "CHENNPETRO.NS", "AEGISLOG.NS", "GULFOILLUB.NS",
        "CASTROLIND.NS", "CONFIPET.NS", "HINDOILEXP.NS"
    ],
    "19. NBFCs & Retail Lending": [
        "BAJFINANCE.NS", "BAJAJFINSV.NS", "CHOLAFIN.NS", "SHRIRAMFIN.NS", "MUTHOOTFIN.NS",
        "POONAWALLA.NS", "M&MFIN.NS", "SUNDARMFIN.NS", "LTF.NS", "IIFL.NS",
        "MANAPPURAM.NS", "AADHARHFC.NS", "CANFINHOME.NS", "HOMEFIRST.NS", "APTUS.NS",
        "LICHSGFIN.NS", "HUDCO.NS", "PNBHOUSING.NS", "FIVESTAR.NS", "CREDITACC.NS",
        "FUSION.NS", "ARMANFIN.NS", "SPANDANA.NS", "SBFC.NS", "PAISALO.NS",
        "SATIN.NS", "SGFIN.NS"
    ],
    "20. Capital Markets, Exchanges & Wealth": [
        "BSE.NS", "MCX.NS", "CDSL.NS", "CAMS.NS", "KFINTECH.NS",
        "ANGELONE.NS", "360ONE.NS", "NUVAMA.NS", "MOTILALOFS.NS", "ANANDRATHI.NS",
        "GEOJITFSL.NS", "SMCGLOBAL.NS", "SHAREINDIA.NS", "IEX.NS", "HDFCAMC.NS",
        "UTIAMC.NS", "NAM-INDIA.NS", "CRAMC.NS", "SBIFUNDS.NS", "CRISIL.NS",
        "ICRA.NS", "CARERATING.NS"
    ],
    "21. FMCG & Packaged Foods": [
        "HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS",
        "GODREJCP.NS", "MARICO.NS", "TATACONSUM.NS", "VBL.NS", "COLPAL.NS",
        "PATANJALI.NS", "EMAMILTD.NS", "PGHH.NS", "GILLETTE.NS", "JYOTHYLAB.NS",
        "HONASA.NS", "ZYDUSWELL.NS", "BIKAJI.NS", "DODLA.NS", "HATSUN.NS",
        "HERITGFOOD.NS", "PARAGMILK.NS", "LTFOODS.NS", "KRBL.NS", "AVADHSUGAR.NS",
        "BALRAMCHIN.NS", "RENUKA.NS", "BANARISUG.NS", "DALMIASUG.NS"
    ],
    "22. Retail, Consumer Brands & Footwear": [
        "DMART.NS", "TRENT.NS", "V2RETAIL.NS", "VMM.NS", "STYLEBAAZA.NS",
        "CANTABIL.NS", "SHOPERSTOP.NS", "NYKAA.NS", "SWIGGY.NS", "NAUKRI.NS",
        "CARTRADE.NS", "MEESHO.NS", "FIRSTCRY.NS", "URBANCO.NS", "ZAGGLE.NS",
        "BATAINDIA.NS", "RELAXO.NS", "CAMPUS.NS", "METROBRAND.NS", "REDTAPE.NS",
        "SAFARI.NS", "VIPIND.NS", "CELLO.NS", "STOVEKRAFT.NS", "TTKPRESTIG.NS",
        "HAWKINCOOK.NS", "CROMPTON.NS", "VOLTAS.NS", "BLUESTARCO.NS", "WHIRLPOOL.NS",
        "IFBIND.NS", "LGEINDIA.NS", "DIXON.NS"
    ],
    "23. Hotels, Hospitality & Travel": [
        "INDHOTEL.NS", "EIHOTEL.NS", "THELEELA.NS", "CHALET.NS", "LEMONTREE.NS",
        "PARKHOTELS.NS", "SAMHI.NS", "JUNIPER.NS", "EIHAHOTELS.NS", "ITDC.NS",
        "TAJGVK.NS", "VENTIVE.NS", "BRIGHOTEL.NS", "WONDERLA.NS", "CORDELIA.NS",
        "TRAVELFOOD.NS", "YATRA.NS", "IXIGO.NS", "TBOTEK.NS", "INDIGO.NS", "EASEMYTRIP.NS"
    ],
    "24. Logistics, Shipping & Transportation": [
        "ADANIPORTS.NS", "CONCOR.NS", "DELHIVERY.NS", "BLUEDART.NS", "INDIGO.NS",
        "SCI.NS", "GESHIP.NS", "TCI.NS", "TCIEXP.NS", "VRLLOG.NS",
        "MAHLOG.NS", "ALLCARGO.NS", "JSWINFRA.NS", "GPPL.NS", "GMRAIRPORT.NS",
        "SHADOWFAX.NS", "SHIPROCKET.NS", "LEAPIND.NS", "SEAMECLTD.NS", "TVSSCS.NS"
    ],
    "25. Textiles, Apparel & Innerwear": [
        "PAGEIND.NS", "RAYMOND.NS", "RAYMONDLSL.NS", "ABFRL.NS", "ARVINDFASN.NS",
        "ARVIND.NS", "KPRMILL.NS", "TRIDENT.NS", "WELSPUNLIV.NS", "VTL.NS",
        "NITINSPIN.NS", "KITEX.NS", "GOKEX.NS", "SPAL.NS", "KKCL.NS",
        "LUXIND.NS", "DOLLAR.NS", "SIYSIL.NS", "SANGAMIND.NS", "FILATEX.NS",
        "INDORAMA.NS", "JINDWORLD.NS", "SPORTKING.NS", "AYMSYNTEX.NS"
    ],
    "26. Telecom & Digital Communications": [
        "BHARTIARTL.NS", "BHARTIHEXA.NS", "IDEA.NS", "INDUSTOWER.NS", "TATACOMM.NS",
        "TEJASNET.NS", "HFCL.NS", "ROUTE.NS", "TANLA.NS", "STLTECH.NS",
        "OPTIEMUS.NS", "VINDHYATEL.NS", "TTML.NS", "HATHWAY.NS"
    ],
    "27. Nifty Jewellery Equal-Weight": [
        "TITAN.NS", "KALYANKJIL.NS", "LALITHAA.NS", "SKYGOLD.NS", "PCJEWELLER.NS",
        "THANGAMAYL.NS", "BLUESTONE.NS", "PNGJL.NS", "TIMEX.NS", "ETHOSLTD.NS",
        "SENCO.NS", "DPABHUSHAN.NS", "TBZ.NS", "GOLDIAM.NS", "KDDL.NS",
        "VAIBHAVGBL.NS", "MOTISONS.NS", "RGL.NS", "RAJESHEXPO.NS", "MVGJL.NS"
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

# Sector Selection Dropdown
sector_options = list(st.session_state.sectors.keys())
selected_sector = st.sidebar.selectbox("Choose Sector Index", sector_options)

# In-App Form to Create a Brand-New Sector
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

# In-App Quick Form to Add a Stock to the Current Sector
with st.sidebar.expander(f"➕ Add Stock to '{selected_sector}'"):
    new_stock_input = st.text_input("Enter NSE Ticker (e.g. INDUSINDBK)").strip()
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
