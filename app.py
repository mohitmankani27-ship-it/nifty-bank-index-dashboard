import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Equal-Weighted Sector Analytics", layout="wide", page_icon="📈")

st.title("🏛️ Quantitative Sector & Equal-Weight Dashboard")
st.caption("27 Sector Indices | Momentum & Trend Quality Leaderboard | Nifty 500 Benchmarking")

# --- 1. MASTER SECTOR DIRECTORY ---
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
    "27. Nifty Jewellery & Watches Equal-Weight": [
        "TITAN.NS", "KALYANKJIL.NS", "LALITHAA.NS", "SKYGOLD.NS", "PCJEWELLER.NS",
        "THANGAMAYL.NS", "BLUESTONE.NS", "PNGJL.NS", "TIMEX.NS", "ETHOSLTD.NS",
        "SENCO.NS", "DPABHUSHAN.NS", "TBZ.NS", "GOLDIAM.NS", "KDDL.NS"
    ]
}

if "sectors" not in st.session_state:
    st.session_state.sectors = {k: list(v) for k, v in DEFAULT_SECTORS.items()}

def format_nse_ticker(raw_sym):
    sym = raw_sym.strip().upper()
    if not sym.endswith(".NS") and not sym.endswith(".BO"):
        sym += ".NS"
    return sym

# --- 2. CACHED DATA & INDEX ENGINE ---
@st.cache_data(ttl=3600)
def fetch_stock_data(ticker):
    try:
        df = yf.Ticker(ticker).history(period="15y", auto_adjust=True)
        if not df.empty and "Close" in df.columns:
            df = df[["Open", "High", "Low", "Close"]]
            df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
            return df
    except Exception:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_benchmark_nifty500():
    try:
        df = yf.Ticker("^CRSLDX").history(period="15y", auto_adjust=True)
        if df.empty:
            df = yf.Ticker("^NSEI").history(period="15y", auto_adjust=True)
        df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
        return df["Close"]
    except Exception:
        return pd.Series(dtype=float)

def compute_equal_weight_index(tickers, base_val=1000.0):
    all_data = {t: fetch_stock_data(t) for t in tickers}
    valid = [t for t in tickers if not all_data[t].empty]
    if not valid:
        return pd.DataFrame(), {}
    
    close_df = pd.DataFrame({t: all_data[t]["Close"] for t in valid}).sort_index().ffill()
    open_df  = pd.DataFrame({t: all_data[t]["Open"]  for t in valid}).sort_index().fillna(close_df)
    high_df  = pd.DataFrame({t: all_data[t]["High"]  for t in valid}).sort_index().fillna(close_df)
    low_df   = pd.DataFrame({t: all_data[t]["Low"]   for t in valid}).sort_index().fillna(close_df)
    
    quarter_labels = close_df.index.to_period("Q")
    unique_q = quarter_labels.unique()
    
    records = []
    current_val = float(base_val)
    
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
            records.append({
                "Date": d,
                "Open": round(q_o.loc[d], 2),
                "High": round(q_h.loc[d], 2),
                "Low": round(q_l.loc[d], 2),
                "Close": round(q_c.loc[d], 2),
            })
        current_val = q_c.iloc[-1]
        
    index_df = pd.DataFrame(records).set_index("Date")
    return index_df, all_data

# --- 3. QUANTITATIVE METRICS FUNCTIONS ---
def calc_kaufman_efficiency(series):
    if len(series) < 2:
        return 0.0
    net_change = abs(series.iloc[-1] - series.iloc[0])
    daily_changes = abs(series.diff()).sum()
    if daily_changes == 0 or pd.isna(daily_changes):
        return 0.0
    return float(net_change / daily_changes)

def calc_r_squared(series):
    if len(series) < 5:
        return 0.0
    y = np.log(np.maximum(series.values, 1e-4))
    x = np.arange(len(y))
    if np.std(y) == 0:
        return 0.0
    corr = np.corrcoef(x, y)[0, 1]
    if np.isnan(corr):
        return 0.0
    return float(corr ** 2)

def calc_sharpe(series, rf=0.068):
    if len(series) < 5:
        return 0.0
    daily_ret = series.pct_change().dropna()
    if len(daily_ret) == 0 or daily_ret.std() == 0:
        return 0.0
    ann_ret = (series.iloc[-1] / series.iloc[0]) ** (252 / len(series)) - 1
    ann_vol = daily_ret.std() * np.sqrt(252)
    if ann_vol == 0:
        return 0.0
    return float((ann_ret - rf) / ann_vol)

# --- 4. TOP-LEVEL DASHBOARD NAVIGATION TABS ---
main_tab1, main_tab2, main_tab3, main_tab4 = st.tabs([
    "🕯️ Single Sector Candlesticks & Zoom",
    "📈 Multi-Sector Comparison vs Nifty 500",
    "🧠 Sector Momentum & Trend Leaderboard",
    "🔍 Stock Attribution & Driver Deep-Dive"
])

# ==============================================================================
# TAB 1: SINGLE SECTOR CANDLESTICKS & ZOOM (100% PRESERVED)
# ==============================================================================
with main_tab1:
    st.sidebar.header("⚙️ Single Sector Controls")
    sector_options = list(st.session_state.sectors.keys())
    selected_sector = st.sidebar.selectbox("Choose Sector Index", sector_options, index=0)

    with st.sidebar.expander("✨ Create New Custom Sector"):
        new_sec_name = st.text_input("New Sector Name (e.g. Defense)").strip()
        new_sec_tickers_raw = st.text_area("Stocks (comma-separated, e.g. HAL, BEL)").strip()
        if st.button("Create Sector"):
            if new_sec_name and new_sec_tickers_raw:
                parsed_tickers = [format_nse_ticker(t) for t in new_sec_tickers_raw.replace("\n", ",").split(",") if t.strip()]
                if parsed_tickers:
                    st.session_state.sectors[new_sec_name] = parsed_tickers
                    st.success(f"Created '{new_sec_name}'!")
                    st.rerun()

    current_constituents = st.session_state.sectors[selected_sector]
    selected_stocks = st.sidebar.multiselect("Constituents (Toggle Stocks)", options=current_constituents, default=current_constituents)

    with st.sidebar.expander(f"➕ Add Stock to '{selected_sector}'"):
        new_stock_input = st.text_input("Enter NSE Ticker (e.g. INDUSINDBK)").strip()
        if st.button("Add to Current Sector"):
            if new_stock_input:
                fmt = format_nse_ticker(new_stock_input)
                if fmt not in current_constituents:
                    st.session_state.sectors[selected_sector].append(fmt)
                    st.rerun()

    base_val = st.sidebar.number_input("Starting Base Value", 100.0, 50000.0, 1000.0, 100.0)

    if not selected_stocks:
        st.warning("Please select at least one stock.")
    else:
        index_df, all_data = compute_equal_weight_index(selected_stocks, base_val)
        if index_df.empty:
            st.error("No market data returned.")
        else:
            s_val = index_df["Close"].iloc[0]
            e_val = index_df["Close"].iloc[-1]
            tot_ret = ((e_val - s_val) / s_val) * 100
            pk = index_df["Close"].cummax()
            dd = (index_df["Close"] - pk) / pk
            m_dd = dd.min() * 100

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Current Value", f"{e_val:,.2f}")
            c1.metric("Total 15Y Return", f"{tot_ret:+,.1f}%")
            c3.metric("Max 15Y Drawdown", f"{m_dd:.1f}%")
            c4.metric("Active Stocks", f"{len(selected_stocks)}")

            t_custom, t_macro, t_breakdown = st.tabs([
                "⏱️ Custom Window (Weeks / Range)",
                "🌐 Full 15-Year Macro (Monthly)",
                "⚖️ Constituent Stock Breakdown"
            ])

            with t_custom:
                col1, col2 = st.columns([2, 1])
                with col1:
                    num_weeks = st.slider("Lookback Window (Weeks):", 1, 260, 12)
                with col2:
                    c_type = st.radio("Granularity:", ["Daily Candlesticks", "Weekly Candlesticks"])

                cutoff = index_df.index.max() - pd.Timedelta(weeks=num_weeks)
                win_df = index_df[index_df.index >= cutoff]
                if "Weekly" in c_type:
                    c_data = win_df.resample("W-FRI").agg({"Open":"first","High":"max","Low":"min","Close":"last"}).dropna()
                else:
                    c_data = win_df

                w_ret = ((win_df["Close"].iloc[-1] - win_df["Close"].iloc[0]) / win_df["Close"].iloc[0]) * 100
                st.caption(f"Showing last **{num_weeks} weeks** ({str(cutoff.date())} to {str(index_df.index.max().date())}) | Return: **{w_ret:+,.2f}%**")

                fig = go.Figure(data=[go.Candlestick(
                    x=c_data.index, open=c_data["Open"], high=c_data["High"],
                    low=c_data["Low"], close=c_data["Close"],
                    increasing_line_color="#26a69a", decreasing_line_color="#ef5350"
                )])
                fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=550)
                st.plotly_chart(fig, use_container_width=True)

            with t_macro:
                m_data = index_df.resample("ME").agg({"Open":"first","High":"max","Low":"min","Close":"last"}).dropna()
                fig_m = go.Figure(data=[go.Candlestick(
                    x=m_data.index, open=m_data["Open"], high=m_data["High"],
                    low=m_data["Low"], close=m_data["Close"],
                    increasing_line_color="#26a69a", decreasing_line_color="#ef5350"
                )])
                fig_m.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=550)
                st.plotly_chart(fig_m, use_container_width=True)

            with t_breakdown:
                rows = []
                for t in selected_stocks:
                    if t in all_data and not all_data[t].empty:
                        rows.append({
                            "Ticker": t,
                            "CMP (Rs)": round(all_data[t]["Close"].iloc[-1], 2),
                            "15Y Return (%)": round(((all_data[t]["Close"].iloc[-1] - all_data[t]["Close"].iloc[0]) / all_data[t]["Close"].iloc[0]) * 100, 1),
                            "Weight": f"{round(100/len(selected_stocks), 2)}%"
                        })
                st.dataframe(pd.DataFrame(rows), use_container_width=True)

# ==============================================================================
# TAB 2: MULTI-SECTOR COMPARISON VS NIFTY 500
# ==============================================================================
with main_tab2:
    st.subheader("📈 Multi-Sector Comparison Against Nifty 500")
    st.caption("Compare multiple custom sectors on a single normalized chart (Base = 100) with the Nifty 500 benchmark in the background.")

    col_m1, col_m2 = st.columns([3, 1])
    with col_m1:
        comp_sectors = st.multiselect(
            "Select Sectors to Compare:",
            options=list(st.session_state.sectors.keys()),
            default=[
                "1. Banking (PSU & Private)",
                "2. Information Technology",
                "3. Automobile (OEMs & EVs)",
                "5. Pharmaceuticals & Formulations",
                "27. Nifty Jewellery & Watches Equal-Weight"
            ]
        )
    with col_m2:
        lookback_choice = st.selectbox("Lookback Period:", ["3 Months", "6 Months", "1 Year", "3 Years", "5 Years", "15 Years"], index=2)

    days_map = {"3 Months": 90, "6 Months": 180, "1 Year": 365, "3 Years": 1095, "5 Years": 1825, "15 Years": 5500}
    days = days_map[lookback_choice]

    if comp_sectors:
        with st.spinner("Calculating sector curves & benchmark..."):
            nifty500 = fetch_benchmark_nifty500()
            fig_multi = go.Figure()

            # Plot Nifty 500 Reference Line in Background
            if not nifty500.empty:
                cutoff_bench = nifty500.index.max() - pd.Timedelta(days=days)
                b_slice = nifty500[nifty500.index >= cutoff_bench]
                if not b_slice.empty:
                    norm_bench = (b_slice / b_slice.iloc[0]) * 100.0
                    fig_multi.add_trace(go.Scatter(
                        x=norm_bench.index, y=norm_bench,
                        mode="lines", name="NIFTY 500 (^CRSLDX)",
                        line=dict(color="#ffffff", width=2.5, dash="dash"),
                        opacity=0.7
                    ))

            # Plot Each Selected Sector
            for sec in comp_sectors:
                stk_list = st.session_state.sectors[sec]
                s_idx, _ = compute_equal_weight_index(stk_list)
                if not s_idx.empty:
                    s_cut = s_idx.index.max() - pd.Timedelta(days=days)
                    s_slice = s_idx.loc[s_idx.index >= s_cut, "Close"]
                    if not s_slice.empty:
                        norm_sec = (s_slice / s_slice.iloc[0]) * 100.0
                        fig_multi.add_trace(go.Scatter(
                            x=norm_sec.index, y=norm_sec,
                            mode="lines", name=sec, line=dict(width=2)
                        ))

            fig_multi.update_layout(
                title=f"Sector Relative Performance vs Nifty 500 ({lookback_choice} Lookback, Base = 100)",
                yaxis_title="Normalized Performance (Base = 100)",
                template="plotly_dark",
                height=600,
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="#1e222d")
            )
            st.plotly_chart(fig_multi, use_container_width=True)

# ==============================================================================
# TAB 3: SECTOR MOMENTUM & TREND LEADERBOARD (INSIGHTS)
# ==============================================================================
with main_tab3:
    st.subheader("🧠 Sector Momentum, Smoothness & Trend Leaderboard")
    st.caption("Identify institutional momentum and smooth trends using Kaufman Efficiency (KER), R-Squared, Sharpe, and Breadth.")

    col_l1, col_l2 = st.columns(2)
    with col_l1:
        primary_window = st.selectbox("Primary Lookback Period:", ["1 Month", "3 Months", "6 Months", "1 Year"], index=1)
    with col_l2:
        sort_metric = st.selectbox(
            "Sort Sectors By:",
            ["Composite Momentum Score", "Total Return (%)", "Kaufman Efficiency Ratio (Smoothness)", "R-Squared (Trend Fit)", "Sharpe Ratio", "Breadth (% Gainers)"],
            index=0
        )

    win_days = {"1 Month": 30, "3 Months": 90, "6 Months": 180, "1 Year": 365}[primary_window]

    if st.button("🚀 Calculate Sector Momentum Scorecard"):
        with st.spinner("Analyzing all 27 sectors..."):
            leaderboard_data = []

            for sec_name, tickers in st.session_state.sectors.items():
                s_idx, s_all = compute_equal_weight_index(tickers[:15]) # sample top 15 for speed
                if not s_idx.empty:
                    cut = s_idx.index.max() - pd.Timedelta(days=win_days)
                    p_slice = s_idx.loc[s_idx.index >= cut, "Close"]

                    if len(p_slice) >= 5:
                        ret = ((p_slice.iloc[-1] - p_slice.iloc[0]) / p_slice.iloc[0]) * 100
                        ker = calc_kaufman_efficiency(p_slice)
                        r2 = calc_r_squared(p_slice)
                        shp = calc_sharpe(p_slice)

                        # Breadth Calculation: Gainers vs Losers
                        gainers = 0
                        valid_count = 0
                        for t in tickers:
                            if t in s_all and not s_all[t].empty:
                                st_slice = s_all[t]["Close"][s_all[t].index >= cut]
                                if len(st_slice) >= 2:
                                    valid_count += 1
                                    if st_slice.iloc[-1] >= st_slice.iloc[0]:
                                        gainers += 1
                        breadth_pct = (gainers / valid_count * 100) if valid_count > 0 else 0.0

                        leaderboard_data.append({
                            "Sector": sec_name,
                            "Return (%)": round(ret, 2),
                            "Kaufman Ratio (KER)": round(ker, 3),
                            "R-Squared (Trend)": round(r2, 3),
                            "Sharpe Ratio": round(shp, 2),
                            "Breadth (Gainers/Total)": f"{gainers}/{valid_count} ({round(breadth_pct, 1)}%)",
                            "_ret_raw": ret,
                            "_ker_raw": ker,
                            "_r2_raw": r2,
                            "_shp_raw": shp,
                            "_breadth_raw": breadth_pct
                        })

            if leaderboard_data:
                df_lead = pd.DataFrame(leaderboard_data)
                
                # Derive Composite Momentum Score (0 - 100)
                ret_p = df_lead["_ret_raw"].rank(pct=True)
                ker_p = df_lead["_ker_raw"].rank(pct=True)
                r2_p  = df_lead["_r2_raw"].rank(pct=True)
                
                # Directional penalty if return is negative
                upward_multiplier = np.where(df_lead["_ret_raw"] > 0, 1.0, 0.3)
                df_lead["Composite Momentum Score"] = np.round((0.40 * ret_p + 0.30 * r2_p + 0.30 * ker_p) * upward_multiplier * 100, 1)

                # Sorting
                sort_col_map = {
                    "Composite Momentum Score": "Composite Momentum Score",
                    "Total Return (%)": "_ret_raw",
                    "Kaufman Efficiency Ratio (Smoothness)": "_ker_raw",
                    "R-Squared (Trend Fit)": "_r2_raw",
                    "Sharpe Ratio": "_shp_raw",
                    "Breadth (% Gainers)": "_breadth_raw"
                }
                df_lead = df_lead.sort_values(by=sort_col_map[sort_metric], ascending=False)
                display_cols = ["Sector", "Composite Momentum Score", "Return (%)", "Kaufman Ratio (KER)", "R-Squared (Trend)", "Sharpe Ratio", "Breadth (Gainers/Total)"]
                
                st.dataframe(df_lead[display_cols], use_container_width=True)
                
                top_sec = df_lead.iloc[0]["Sector"]
                st.success(f"🏆 Top Momentum Leader: **{top_sec}** with a Momentum Score of **{df_lead.iloc[0]['Composite Momentum Score']}/100** and Return of **{df_lead.iloc[0]['Return (%)']}%**")

# ==============================================================================
# TAB 4: STOCK ATTRIBUTION & DRIVER DEEP-DIVE
# ==============================================================================
with main_tab4:
    st.subheader("🔍 Sector Stock Attribution & Driver Deep-Dive")
    st.caption("Inspect individual constituents to see which stocks are leading the rally and which are dragging down the index.")

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        att_sector = st.selectbox("Select Sector to Drill Down:", list(st.session_state.sectors.keys()), index=0)
    with col_d2:
        att_window = st.selectbox("Attribution Lookback Period:", ["1 Month", "3 Months", "6 Months", "1 Year"], index=1)

    att_days = {"1 Month": 30, "3 Months": 90, "6 Months": 180, "1 Year": 365}[att_window]

    stk_constituents = st.session_state.sectors[att_sector]
    sec_idx, sec_data = compute_equal_weight_index(stk_constituents)

    if not sec_idx.empty:
        att_cut = sec_idx.index.max() - pd.Timedelta(days=att_days)
        idx_slice = sec_idx.loc[sec_idx.index >= att_cut, "Close"]
        sec_tot_ret = ((idx_slice.iloc[-1] - idx_slice.iloc[0]) / idx_slice.iloc[0]) * 100

        st.metric(f"{att_sector} — {att_window} Total Return", f"{sec_tot_ret:+,.2f}%")

        stock_rows = []
        n_const = len(stk_constituents)

        for t in stk_constituents:
            if t in sec_data and not sec_data[t].empty:
                s_series = sec_data[t]["Close"][sec_data[t].index >= att_cut]
                if len(s_series) >= 2:
                    p_ret = ((s_series.iloc[-1] - s_series.iloc[0]) / s_series.iloc[0]) * 100
                    # Equal-Weight Contribution
                    contr = p_ret / n_const
                    vol = s_series.pct_change().std() * np.sqrt(252) * 100
                    stk_ker = calc_kaufman_efficiency(s_series)

                    stock_rows.append({
                        "Ticker": t,
                        "CMP (Rs)": round(s_series.iloc[-1], 2),
                        "Period Return (%)": round(p_ret, 2),
                        "Contribution to Index (%)": round(contr, 2),
                        "Annualized Volatility (%)": round(vol, 1),
                        "Trend Smoothness (KER)": round(stk_ker, 3),
                        "_contr_raw": contr,
                        "_ret_raw": p_ret
                    })

        if stock_rows:
            df_stocks = pd.DataFrame(stock_rows).sort_values(by="_contr_raw", ascending=False)

            # Highlight Top Leaders vs Draggers
            top_col1, top_col2 = st.columns(2)
            with top_col1:
                st.markdown("### 🚀 Top Rally Leaders (Biggest Positive Lift)")
                st.dataframe(df_stocks.head(3)[["Ticker", "Period Return (%)", "Contribution to Index (%)"]], use_container_width=True)

            with top_col2:
                st.markdown("### 🔻 Top Draggers (Biggest Negative Pull)")
                st.dataframe(df_stocks.tail(3)[["Ticker", "Period Return (%)", "Contribution to Index (%)"]], use_container_width=True)

            st.markdown("### 📋 Complete Constituent Breakdown")
            display_stk_cols = ["Ticker", "CMP (Rs)", "Period Return (%)", "Contribution to Index (%)", "Annualized Volatility (%)", "Trend Smoothness (KER)"]
            st.dataframe(df_stocks[display_stk_cols], use_container_width=True)
