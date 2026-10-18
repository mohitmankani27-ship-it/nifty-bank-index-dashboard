import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Quantitative Equal-Weight Sector Dashboard",
    layout="wide",
    page_icon="📈"
)

st.title("🏛️ Quantitative Equal-Weighted Sector & Momentum Terminal")
st.caption(
    "27 Full-Basket Sector Indices | Chunked Multi-Threaded OHLC Engine | "
    "1W/2W/4W/3M/6M/1Y Momentum, Rank History, Relative Strength & Moving-Average Breadth"
)

# ==============================================================================
# 1. COMPLETE 27-SECTOR MASTER DIRECTORY (NO SAMPLING)
# ==============================================================================
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
    if not sym:
        return ""
    if not sym.endswith(".NS") and not sym.endswith(".BO") and not sym.startswith("^"):
        sym += ".NS"
    return sym


# ==============================================================================
# 2. CHUNKED, CACHE-SAFE FULL OHLC BATCH DOWNLOADER
# ==============================================================================
def _extract_ohlc_from_yf_chunk(raw_df, chunk_tickers):
    """Normalizes single-ticker or multi-ticker yf.download output into 4 OHLC DataFrames."""
    fields = ("Open", "High", "Low", "Close")
    if raw_df is None or raw_df.empty:
        return {f: pd.DataFrame() for f in fields}

    df = raw_df.copy()
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    df = df[~df.index.duplicated(keep="last")].sort_index()

    out = {}
    if isinstance(df.columns, pd.MultiIndex):
        lvl0 = set(df.columns.get_level_values(0))
        for f in fields:
            if f in lvl0:
                sub = df[f].copy()
                if isinstance(sub, pd.Series):
                    sub = sub.to_frame(name=chunk_tickers[0])
                out[f] = sub
            else:
                out[f] = pd.DataFrame(index=df.index)
    else:
        t0 = chunk_tickers[0]
        for f in fields:
            if f in df.columns:
                out[f] = pd.DataFrame({t0: df[f]}, index=df.index)
            else:
                out[f] = pd.DataFrame(index=df.index)
    return out


@st.cache_data(ttl=3600, show_spinner=False)
def _download_ohlc_cached(sorted_tickers_tuple, period="2y", chunk_size=45):
    """
    Downloads full Open/High/Low/Close in chunks of ~45 tickers to prevent Yahoo throttling.
    Audit for dead/suspended stocks runs BEFORE forward-filling.
    Raises RuntimeError if completely empty so Streamlit NEVER caches a failed fetch.
    """
    tickers = list(sorted_tickers_tuple)
    if not tickers:
        raise ValueError("Ticker list is empty.")

    ohlc_parts = {"Open": [], "High": [], "Low": [], "Close": []}

    for i in range(0, len(tickers), chunk_size):
        chunk = tickers[i:i + chunk_size]
        raw_chunk = yf.download(
            chunk,
            period=period,
            auto_adjust=True,
            group_by="column",
            threads=True,
            progress=False
        )
        extracted = _extract_ohlc_from_yf_chunk(raw_chunk, chunk)
        for f in ("Open", "High", "Low", "Close"):
            if not extracted[f].empty:
                ohlc_parts[f].append(extracted[f])

    if not ohlc_parts["Close"]:
        raise RuntimeError("Yahoo Finance returned empty dataset across all chunks.")

    raw_ohlc = {}
    for f in ("Open", "High", "Low", "Close"):
        if ohlc_parts[f]:
            combined = pd.concat(ohlc_parts[f], axis=1)
            combined = combined.loc[:, ~combined.columns.duplicated()].sort_index()
            raw_ohlc[f] = combined
        else:
            raw_ohlc[f] = pd.DataFrame()

    raw_close = raw_ohlc["Close"].dropna(how="all")
    if raw_close.empty:
        raise RuntimeError("All downloaded Close series are empty.")

    market_last_date = raw_close.index.max()

    # Single-ticker retry for any symbol that was throttled in batch mode
    missing_initial = [
        t for t in tickers
        if t not in raw_close.columns or raw_close[t].dropna().empty
    ]
    if 0 < len(missing_initial) <= 15:
        for t in missing_initial:
            try:
                single_df = yf.Ticker(t).history(period=period, auto_adjust=True)
                if not single_df.empty and "Close" in single_df.columns:
                    single_df.index = pd.to_datetime(single_df.index).tz_localize(None).normalize()
                    single_df = single_df[~single_df.index.duplicated(keep="last")].sort_index()
                    for f in ("Open", "High", "Low", "Close"):
                        if f in single_df.columns:
                            raw_ohlc[f][t] = single_df[f]
            except Exception:
                pass
        raw_close = raw_ohlc["Close"].dropna(how="all")
        market_last_date = raw_close.index.max()

    # Audit failures & stale/suspended tickers BEFORE forward-filling
    failed_missing = []
    failed_stale = []
    last_valid_dates = {}

    for t in tickers:
        if t not in raw_close.columns:
            failed_missing.append(t)
            continue
        valid_s = raw_close[t].dropna()
        if valid_s.empty:
            failed_missing.append(t)
            continue
        last_dt = valid_s.index.max()
        last_valid_dates[t] = last_dt
        if (market_last_date - last_dt).days > 5:
            failed_stale.append(f"{t} (last trade: {str(last_dt.date())})")

    # Forward-fill short single-day holiday gaps (limit=5) ONLY up to each stock's last valid trade date
    # so suspended/delisted stocks are never flat-lined into the future
    cleaned_ohlc = {}
    cleaned_close = raw_ohlc["Close"].copy()
    for t in cleaned_close.columns:
        if t in last_valid_dates:
            last_dt = last_valid_dates[t]
            cleaned_close.loc[:last_dt, t] = cleaned_close.loc[:last_dt, t].ffill(limit=5)
    cleaned_ohlc["Close"] = cleaned_close

    for f in ("Open", "High", "Low"):
        df_f = raw_ohlc[f].copy()
        df_f = df_f.fillna(cleaned_close)
        cleaned_ohlc[f] = df_f

    return {
        "Open": cleaned_ohlc["Open"],
        "High": cleaned_ohlc["High"],
        "Low": cleaned_ohlc["Low"],
        "Close": cleaned_ohlc["Close"],
        "failed_missing": failed_missing,
        "failed_stale": failed_stale,
        "market_last_date": market_last_date
    }


def fetch_all_ohlc(tickers, period="2y"):
    """Safe wrapper around _download_ohlc_cached that clears cache on transient failures."""
    sorted_unique = tuple(sorted(set(t.strip().upper() for t in tickers if t and t.strip())))
    if not sorted_unique:
        return None
    try:
        res = _download_ohlc_cached(sorted_unique, period=period)
        if res is None or res["Close"].empty:
            _download_ohlc_cached.clear()
            return None
        return res
    except Exception as exc:
        _download_ohlc_cached.clear()
        st.error(f"Market data download encountered an issue: {exc}. Cache was NOT poisoned; click Rerun to retry.")
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_benchmark_series(period="15y"):
    """
    Fetches official benchmark and returns (Series, Accurate_Label) so Nifty 50 fallback
    is never mislabeled as Nifty 500.
    """
    for sym, label in [
        ("^CRSLDX", "NIFTY 500 (^CRSLDX)"),
        ("^NSEI", "NIFTY 50 (^NSEI — Broad Market Fallback)")
    ]:
        try:
            df = yf.Ticker(sym).history(period=period, auto_adjust=True)
            if not df.empty and "Close" in df.columns and len(df) >= 10:
                s = df["Close"].copy()
                s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
                s = s[~s.index.duplicated(keep="last")].sort_index()
                return s, label
        except Exception:
            pass
    raise RuntimeError("Benchmark download failed.")


# ==============================================================================
# 3. UNIFIED QUARTERLY EQUAL-WEIGHT OHLC ENGINE (REWIRED TO BATCH LOADER)
# ==============================================================================
def compute_equal_weight_index(tickers, ohlc_bundle, base_val=1000.0, exclude_stale=True):
    """
    Computes genuine quarterly-rebalanced Open, High, Low, Close candlesticks
    using 100% of active constituents from the unified ohlc_bundle.
    """
    if ohlc_bundle is None or ohlc_bundle["Close"].empty:
        return pd.DataFrame(), []

    stale_set = set(s.split(" ")[0] for s in ohlc_bundle.get("failed_stale", [])) if exclude_stale else set()
    missing_set = set(ohlc_bundle.get("failed_missing", []))

    close_all = ohlc_bundle["Close"]
    open_all = ohlc_bundle["Open"]
    high_all = ohlc_bundle["High"]
    low_all = ohlc_bundle["Low"]

    valid_tickers = [
        t for t in tickers
        if t in close_all.columns
        and t not in missing_set
        and t not in stale_set
        and not close_all[t].dropna().empty
    ]
    if not valid_tickers:
        valid_tickers = [
            t for t in tickers
            if t in close_all.columns and not close_all[t].dropna().empty
        ]
    if not valid_tickers:
        return pd.DataFrame(), []

    c_df = close_all[valid_tickers].dropna(how="all")
    o_df = open_all[valid_tickers].reindex(c_df.index).fillna(c_df)
    h_df = high_all[valid_tickers].reindex(c_df.index).fillna(c_df)
    l_df = low_all[valid_tickers].reindex(c_df.index).fillna(c_df)

    quarter_labels = c_df.index.to_period("Q")
    unique_q = quarter_labels.unique()

    records = []
    current_val = float(base_val)

    for q in unique_q:
        q_mask = (quarter_labels == q)
        dates = c_df.index[q_mask]
        if len(dates) == 0:
            continue

        first_prices = c_df.loc[dates[0]].dropna()
        active = first_prices.index
        if len(active) == 0:
            continue

        q_c_sub = c_df.loc[dates, active].ffill()
        q_o_sub = o_df.loc[dates, active].fillna(q_c_sub)
        q_h_sub = h_df.loc[dates, active].fillna(q_c_sub)
        q_l_sub = l_df.loc[dates, active].fillna(q_c_sub)

        pts_per_stock = current_val / len(active)
        notional_shares = pts_per_stock / first_prices

        idx_o = q_o_sub.multiply(notional_shares, axis=1).sum(axis=1)
        idx_h = q_h_sub.multiply(notional_shares, axis=1).sum(axis=1)
        idx_l = q_l_sub.multiply(notional_shares, axis=1).sum(axis=1)
        idx_c = q_c_sub.multiply(notional_shares, axis=1).sum(axis=1)

        for d in dates:
            o_v = float(idx_o.loc[d])
            c_v = float(idx_c.loc[d])
            h_v = max(float(idx_h.loc[d]), o_v, c_v)
            l_v = min(float(idx_l.loc[d]), o_v, c_v)
            records.append({
                "Date": d,
                "Open": round(o_v, 2),
                "High": round(h_v, 2),
                "Low": round(l_v, 2),
                "Close": round(c_v, 2),
                "Active_Stocks": len(active)
            })
        current_val = float(idx_c.iloc[-1])

    index_df = pd.DataFrame(records).set_index("Date")
    index_df = index_df[~index_df.index.duplicated(keep="last")]
    return index_df, valid_tickers


# ==============================================================================
# 4. QUANTITATIVE TREND, MOMENTUM & BREADTH FORMULAS
# ==============================================================================
WINDOW_DAYS_MAP = {
    "1 Week (5D)": 7,
    "2 Weeks (10D)": 14,
    "4 Weeks (1M)": 30,
    "3 Months (63D)": 91,
    "6 Months (126D)": 182,
    "1 Year (252D)": 365
}


def slice_by_window(series, window_label):
    if series is None or series.empty:
        return pd.Series(dtype=float)
    s = series.dropna()
    if s.empty:
        return s
    days = WINDOW_DAYS_MAP.get(window_label, 91)
    cutoff = s.index.max() - pd.Timedelta(days=days)
    sliced = s[s.index >= cutoff]
    if len(sliced) < 2 and len(s) >= 2:
        return s.tail(2)
    return sliced


def calc_period_return(series, window_label):
    sliced = slice_by_window(series, window_label)
    if len(sliced) < 2 or sliced.iloc[0] == 0:
        return np.nan
    return float(((sliced.iloc[-1] - sliced.iloc[0]) / sliced.iloc[0]) * 100.0)


def calc_kaufman_efficiency(series):
    s = series.dropna()
    if len(s) < 2:
        return 0.0
    net_change = abs(s.iloc[-1] - s.iloc[0])
    daily_changes = abs(s.diff()).sum()
    if daily_changes == 0 or pd.isna(daily_changes):
        return 0.0
    return float(net_change / daily_changes)


def calc_r_squared(series):
    s = series.dropna()
    if len(s) < 4:
        return 0.0
    y = np.log(np.maximum(s.values, 1e-4))
    x = np.arange(len(y))
    if np.std(y) == 0:
        return 0.0
    corr = np.corrcoef(x, y)[0, 1]
    if np.isnan(corr):
        return 0.0
    return float(corr ** 2)


def calc_sharpe(series, rf=0.068):
    s = series.dropna()
    if len(s) < 4:
        return 0.0
    daily_ret = s.pct_change().dropna()
    if len(daily_ret) == 0 or daily_ret.std() == 0:
        return 0.0
    ann_ret = (s.iloc[-1] / s.iloc[0]) ** (252.0 / max(len(s), 1)) - 1.0
    ann_vol = daily_ret.std() * np.sqrt(252.0)
    if ann_vol == 0 or pd.isna(ann_vol):
        return 0.0
    return float((ann_ret - rf) / ann_vol)


def calc_ma_breadth(close_df, tickers):
    """Computes % of active constituents trading above their 20-DMA, 50-DMA, and 200-DMA."""
    above_20, above_50, above_200 = 0, 0, 0
    total_20, total_50, total_200 = 0, 0, 0

    for t in tickers:
        if t not in close_df.columns:
            continue
        s = close_df[t].dropna()
        if len(s) >= 20:
            total_20 += 1
            if s.iloc[-1] > s.iloc[-20:].mean():
                above_20 += 1
        if len(s) >= 50:
            total_50 += 1
            if s.iloc[-1] > s.iloc[-50:].mean():
                above_50 += 1
        if len(s) >= 200:
            total_200 += 1
            if s.iloc[-1] > s.iloc[-200:].mean():
                above_200 += 1

    pct_20 = round((above_20 / total_20) * 100.0, 1) if total_20 > 0 else 0.0
    pct_50 = round((above_50 / total_50) * 100.0, 1) if total_50 > 0 else 0.0
    pct_200 = round((above_200 / total_200) * 100.0, 1) if total_200 > 0 else 0.0
    return pct_20, pct_50, pct_200


def compute_composite_scores(df_metrics, ret_col, r2_col, ker_col):
    """Derives 0-100 Composite Momentum Score from cross-sectional percentiles."""
    ret_p = df_metrics[ret_col].rank(pct=True)
    r2_p = df_metrics[r2_col].rank(pct=True)
    ker_p = df_metrics[ker_col].rank(pct=True)
    upward_mult = np.where(df_metrics[ret_col] > 0, 1.0, 0.30)
    return np.round((0.45 * ret_p + 0.30 * r2_p + 0.25 * ker_p) * upward_mult * 100.0, 1)


# ==============================================================================
# 5. SINGLE-CALL MASTER UNIVERSE LOADER FOR MULTI-SECTOR TABS
# ==============================================================================
def load_master_universe(sectors_dict, period="2y"):
    """Collects all unique tickers across all sectors and downloads once in chunks."""
    all_tickers = []
    for t_list in sectors_dict.values():
        all_tickers.extend(t_list)
    return fetch_all_ohlc(all_tickers, period=period)


# ==============================================================================
# 6. SIDEBAR: GLOBAL SECTOR & CONSTITUENT CONTROLS
# ==============================================================================
st.sidebar.header("⚙️ Index & Universe Controls")
sector_options = list(st.session_state.sectors.keys())
selected_sector = st.sidebar.selectbox("Choose Sector Index (Tab 1)", sector_options, index=0)

with st.sidebar.expander("✨ Create New Custom Sector"):
    new_sec_name = st.text_input("New Sector Name (e.g. Defense)").strip()
    new_sec_tickers_raw = st.text_area("Stocks (comma-separated, e.g. HAL, BEL)").strip()
    if st.button("Create Sector"):
        if new_sec_name and new_sec_tickers_raw:
            parsed_tickers = [
                format_nse_ticker(t)
                for t in new_sec_tickers_raw.replace("\n", ",").split(",")
                if t.strip()
            ]
            if parsed_tickers:
                st.session_state.sectors[new_sec_name] = parsed_tickers
                st.success(f"Created '{new_sec_name}' with {len(parsed_tickers)} stocks!")
                st.rerun()

current_constituents = st.session_state.sectors[selected_sector]
selected_stocks = st.sidebar.multiselect(
    "Constituents (Toggle Stocks)",
    options=current_constituents,
    default=current_constituents
)

with st.sidebar.expander(f"➕ Add Stock to '{selected_sector}'"):
    new_stock_input = st.text_input("Enter NSE Ticker (e.g. INDUSINDBK)").strip()
    if st.button("Add to Current Sector"):
        if new_stock_input:
            fmt = format_nse_ticker(new_stock_input)
            if fmt and fmt not in current_constituents:
                st.session_state.sectors[selected_sector].append(fmt)
                st.rerun()

base_val = st.sidebar.number_input("Starting Base Value", 100.0, 50000.0, 1000.0, 100.0)

if st.sidebar.button("🔄 Clear Data Cache & Refresh"):
    st.cache_data.clear()
    st.rerun()


# ==============================================================================
# 7. TOP-LEVEL DASHBOARD NAVIGATION TABS
# ==============================================================================
main_tab1, main_tab2, main_tab3, main_tab4 = st.tabs([
    "🕯️ Single Sector Candlesticks & RS",
    "📈 Multi-Sector Comparison vs Benchmark",
    "🧠 Sector Momentum, Breadth & Rank History",
    "🔍 Stock Attribution & Driver Deep-Dive"
])

# ==============================================================================
# TAB 1: SINGLE SECTOR CANDLESTICKS, CUSTOM WEEKS & RELATIVE STRENGTH LINE
# ==============================================================================
with main_tab1:
    if not selected_stocks:
        st.warning("Please select at least one stock in the sidebar.")
    else:
        with st.spinner(f"Loading 15-year OHLC data for {selected_sector} ({len(selected_stocks)} stocks)..."):
            sec_ohlc_15y = fetch_all_ohlc(selected_stocks, period="15y")
            index_df, valid_15y = compute_equal_weight_index(selected_stocks, sec_ohlc_15y, base_val=base_val)

        if index_df.empty:
            st.error("No valid market data returned for the selected constituents.")
        else:
            missing_15y = [t for t in selected_stocks if t in sec_ohlc_15y["failed_missing"]]
            stale_15y = [s for s in sec_ohlc_15y["failed_stale"] if s.split(" ")[0] in selected_stocks]
            if missing_15y or stale_15y:
                with st.expander("⚠️ Constituent Data Health Audit (Missing / Suspended Tickers Excluded)"):
                    if missing_15y:
                        st.write("**Missing / No Yahoo Data:**", ", ".join(missing_15y))
                    if stale_15y:
                        st.write("**Stale / Suspended (>5 Days Behind Market):**", ", ".join(stale_15y))

            s_val = index_df["Close"].iloc[0]
            e_val = index_df["Close"].iloc[-1]
            tot_ret = ((e_val - s_val) / s_val) * 100.0
            pk = index_df["Close"].cummax()
            dd = (index_df["Close"] - pk) / pk
            m_dd = dd.min() * 100.0

            pct_20, pct_50, pct_200 = calc_ma_breadth(sec_ohlc_15y["Close"], valid_15y)

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Current Index Value", f"{e_val:,.2f}")
            c2.metric("Total 15Y Return", f"{tot_ret:+,.1f}%")
            c3.metric("Max 15Y Drawdown", f"{m_dd:.1f}%")
            c4.metric("Active Constituents", f"{len(valid_15y)} / {len(selected_stocks)}")
            c5.metric("Breadth > 50 DMA", f"{pct_50:.1f}%", f"{pct_200:.1f}% > 200 DMA")

            t_custom, t_macro, t_breakdown = st.tabs([
                "⏱️ Custom Window (Weeks / Range + RS Line)",
                "🌐 Full 15-Year Macro (Monthly)",
                "⚖️ Constituent Stock Breakdown"
            ])

            with t_custom:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    num_weeks = st.slider("Lookback Window (in Weeks):", 1, 260, 12)
                with col2:
                    c_type = st.radio("Candle Granularity:", ["Daily Candlesticks", "Weekly Candlesticks"])
                with col3:
                    show_rs = st.checkbox("Show Relative Strength (RS) Line vs Benchmark", value=True)

                cutoff = index_df.index.max() - pd.Timedelta(weeks=num_weeks)
                win_df = index_df[index_df.index >= cutoff]
                if "Weekly" in c_type:
                    c_data = win_df.resample("W-FRI").agg({
                        "Open": "first", "High": "max", "Low": "min", "Close": "last"
                    }).dropna()
                else:
                    c_data = win_df

                w_ret = ((win_df["Close"].iloc[-1] - win_df["Close"].iloc[0]) / win_df["Close"].iloc[0]) * 100.0
                st.caption(
                    f"Showing last **{num_weeks} weeks** ({str(cutoff.date())} to {str(index_df.index.max().date())}) | "
                    f"Period Return: **{w_ret:+,.2f}%** | Breadth > 20 DMA: **{pct_20:.1f}%**"
                )

                if show_rs:
                    try:
                        bench_s, bench_label = fetch_benchmark_series(period="15y")
                        common_idx = c_data.index.intersection(bench_s.index)
                    except Exception:
                        common_idx = pd.Index([])
                        bench_label = "Benchmark"

                    if len(common_idx) >= 2:
                        fig = make_subplots(
                            rows=2, cols=1, shared_xaxes=True,
                            vertical_spacing=0.06, row_heights=[0.72, 0.28],
                            subplot_titles=(
                                f"{selected_sector} — Candlesticks (Last {num_weeks} Weeks)",
                                f"Relative Strength (RS) Line vs {bench_label} (Base = 100)"
                            )
                        )
                        fig.add_trace(
                            go.Candlestick(
                                x=c_data.index, open=c_data["Open"], high=c_data["High"],
                                low=c_data["Low"], close=c_data["Close"],
                                increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
                                name=selected_sector
                            ),
                            row=1, col=1
                        )
                        rs_raw = c_data.loc[common_idx, "Close"] / bench_s.loc[common_idx]
                        rs_norm = (rs_raw / rs_raw.iloc[0]) * 100.0
                        rs_ma = rs_norm.rolling(min(20, max(3, len(rs_norm) // 3))).mean()

                        fig.add_trace(
                            go.Scatter(
                                x=common_idx, y=rs_norm, mode="lines",
                                name="RS Line (Sector / Benchmark)",
                                line=dict(color="#2962FF", width=2.2)
                            ),
                            row=2, col=1
                        )
                        fig.add_trace(
                            go.Scatter(
                                x=common_idx, y=rs_ma, mode="lines",
                                name="RS Moving Average",
                                line=dict(color="#FF6D00", width=1.6, dash="dot")
                            ),
                            row=2, col=1
                        )
                        fig.update_layout(
                            template="plotly_dark", xaxis_rangeslider_visible=False,
                            height=680, margin=dict(l=10, r=10, t=40, b=10)
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        fig = go.Figure(data=[go.Candlestick(
                            x=c_data.index, open=c_data["Open"], high=c_data["High"],
                            low=c_data["Low"], close=c_data["Close"],
                            increasing_line_color="#26a69a", decreasing_line_color="#ef5350"
                        )])
                        fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=550)
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    fig = go.Figure(data=[go.Candlestick(
                        x=c_data.index, open=c_data["Open"], high=c_data["High"],
                        low=c_data["Low"], close=c_data["Close"],
                        increasing_line_color="#26a69a", decreasing_line_color="#ef5350"
                    )])
                    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=550)
                    st.plotly_chart(fig, use_container_width=True)

            with t_macro:
                m_data = index_df.resample("ME").agg({
                    "Open": "first", "High": "max", "Low": "min", "Close": "last"
                }).dropna()
                fig_m = go.Figure(data=[go.Candlestick(
                    x=m_data.index, open=m_data["Open"], high=m_data["High"],
                    low=m_data["Low"], close=m_data["Close"],
                    increasing_line_color="#26a69a", decreasing_line_color="#ef5350"
                )])
                fig_m.update_layout(
                    title=f"{selected_sector} — 15-Year Monthly Candlesticks ({len(m_data)} Months)",
                    template="plotly_dark", xaxis_rangeslider_visible=False, height=550
                )
                st.plotly_chart(fig_m, use_container_width=True)

            with t_breakdown:
                rows = []
                close_15y = sec_ohlc_15y["Close"]
                for t in valid_15y:
                    s_t = close_15y[t].dropna()
                    if not s_t.empty:
                        ma50 = s_t.iloc[-50:].mean() if len(s_t) >= 50 else np.nan
                        ma200 = s_t.iloc[-200:].mean() if len(s_t) >= 200 else np.nan
                        rows.append({
                            "Ticker": t,
                            "CMP (Rs)": round(float(s_t.iloc[-1]), 2),
                            "1W (%)": round(calc_period_return(s_t, "1 Week (5D)"), 2),
                            "4W (%)": round(calc_period_return(s_t, "4 Weeks (1M)"), 2),
                            "3M (%)": round(calc_period_return(s_t, "3 Months (63D)"), 2),
                            "1Y (%)": round(calc_period_return(s_t, "1 Year (252D)"), 2),
                            "15Y Return (%)": round(((s_t.iloc[-1] - s_t.iloc[0]) / s_t.iloc[0]) * 100.0, 1),
                            "vs 50 DMA (%)": round(((s_t.iloc[-1] - ma50) / ma50) * 100.0, 1) if pd.notna(ma50) else np.nan,
                            "vs 200 DMA (%)": round(((s_t.iloc[-1] - ma200) / ma200) * 100.0, 1) if pd.notna(ma200) else np.nan,
                            "Equal Weight": f"{round(100.0 / len(valid_15y), 2)}%"
                        })
                st.dataframe(pd.DataFrame(rows), use_container_width=True)


# ==============================================================================
# TAB 2: MULTI-SECTOR COMPARISON & RELATIVE STRENGTH VS BENCHMARK
# ==============================================================================
with main_tab2:
    st.subheader("📈 Multi-Sector Relative Performance & RS Ratio vs Benchmark")
    st.caption(
        "Uses 100% of constituents per sector from a single chunked batch download. "
        "Switch between Normalized Price Performance and Relative Strength (Sector / Benchmark)."
    )

    col_m1, col_m2, col_m3 = st.columns([3, 1, 1])
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
        lookback_choice = st.selectbox(
            "Lookback Window:",
            list(WINDOW_DAYS_MAP.keys()) + ["2 Years (504D)"],
            index=5
        )
    with col_m3:
        chart_mode = st.radio(
            "Chart Mode:",
            ["Normalized Return (Base=100)", "Relative Strength (RS vs Benchmark)"]
        )

    days = WINDOW_DAYS_MAP.get(lookback_choice, 730)

    if comp_sectors:
        with st.spinner("Loading unified multi-sector batch dataset (chunked, 100% constituents)..."):
            master_2y = load_master_universe(st.session_state.sectors, period="2y")
            try:
                bench_series, bench_true_label = fetch_benchmark_series(period="5y")
            except Exception:
                bench_series, bench_true_label = pd.Series(dtype=float), "Benchmark Unavailable"

        if master_2y is not None:
            fig_multi = go.Figure()

            if not bench_series.empty:
                cutoff_bench = bench_series.index.max() - pd.Timedelta(days=days)
                b_slice = bench_series[bench_series.index >= cutoff_bench]
                if not b_slice.empty:
                    if "Relative Strength" in chart_mode:
                        fig_multi.add_trace(go.Scatter(
                            x=b_slice.index,
                            y=pd.Series(100.0, index=b_slice.index),
                            mode="lines",
                            name=f"★ {bench_true_label} Baseline (100)",
                            line=dict(color="#FF6D00", width=3.2, dash="dash")
                        ))
                    else:
                        norm_bench = (b_slice / b_slice.iloc[0]) * 100.0
                        fig_multi.add_trace(go.Scatter(
                            x=norm_bench.index,
                            y=norm_bench,
                            mode="lines",
                            name=f"★ {bench_true_label}",
                            line=dict(color="#FF6D00", width=3.5, dash="dash")
                        ))

            vibrant_colors = [
                "#2962FF", "#00C853", "#AA00FF", "#00B8D4", "#D50000",
                "#FFD600", "#FF1744", "#304FFE", "#00BFA5", "#C51162"
            ]

            for idx_color, sec in enumerate(comp_sectors):
                stk_list = st.session_state.sectors[sec]
                sec_ohlc_df, valid_list = compute_equal_weight_index(stk_list, master_2y)
                if not sec_ohlc_df.empty:
                    s_curve = sec_ohlc_df["Close"]
                    s_cut = s_curve.index.max() - pd.Timedelta(days=days)
                    s_slice = s_curve[s_curve.index >= s_cut]
                    if len(s_slice) >= 2:
                        color_choice = vibrant_colors[idx_color % len(vibrant_colors)]
                        if "Relative Strength" in chart_mode and not bench_series.empty:
                            c_dates = s_slice.index.intersection(bench_series.index)
                            if len(c_dates) >= 2:
                                rs_line = (s_slice.loc[c_dates] / bench_series.loc[c_dates])
                                rs_norm = (rs_line / rs_line.iloc[0]) * 100.0
                                fig_multi.add_trace(go.Scatter(
                                    x=rs_norm.index, y=rs_norm,
                                    mode="lines",
                                    name=f"{sec} RS ({len(valid_list)} stocks)",
                                    line=dict(width=2.5, color=color_choice)
                                ))
                        else:
                            norm_sec = (s_slice / s_slice.iloc[0]) * 100.0
                            fig_multi.add_trace(go.Scatter(
                                x=norm_sec.index, y=norm_sec,
                                mode="lines",
                                name=f"{sec} ({len(valid_list)} stocks)",
                                line=dict(width=2.5, color=color_choice)
                            ))

            fig_multi.update_layout(
                title=f"{chart_mode} — {lookback_choice} ({bench_true_label})",
                yaxis_title="Indexed Value (Base = 100)",
                height=620,
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0,
                    bgcolor="rgba(255, 255, 255, 0.92)", bordercolor="#888888", borderwidth=1,
                    font=dict(color="#111111", size=12)
                ),
                margin=dict(l=10, r=10, t=80, b=10)
            )
            st.plotly_chart(fig_multi, use_container_width=True)


# ==============================================================================
# TAB 3: SECTOR MOMENTUM LEADERBOARD, DUAL WINDOWS, MA BREADTH & RANK HISTORY
# ==============================================================================
with main_tab3:
    st.subheader("🧠 Full-Basket Sector Momentum, Breadth & Weekly Rank History")
    st.caption(
        "Evaluates 100% of active constituents across all 27 sectors from a single cached batch call. "
        "Includes 1W/2W/4W/3M/6M/1Y returns, dual-window rank delta, moving-average breadth, and weekly rank trajectory."
    )

    col_l1, col_l2, col_l3 = st.columns(3)
    window_options = list(WINDOW_DAYS_MAP.keys())
    with col_l1:
        primary_window = st.selectbox("Primary Ranking Window:", window_options, index=3)
    with col_l2:
        comparison_window = st.selectbox("Comparison Baseline Window:", window_options, index=2)
    with col_l3:
        sort_metric = st.selectbox(
            "Sort Sectors By:",
            [
                "Primary Momentum Score",
                "Primary Return (%)",
                "1W (%)",
                "2W (%)",
                "4W (%)",
                "3M (%)",
                "6M (%)",
                "1Y (%)",
                "Kaufman Efficiency Ratio (Smoothness)",
                "R-Squared (Trend Fit)",
                "Sharpe Ratio",
                "Breadth (% Gainers)",
                "% > 50 DMA",
                "% > 200 DMA"
            ],
            index=0
        )

    with st.spinner("Computing full-basket momentum, breadth & rank history across all 27 sectors..."):
        master_2y = load_master_universe(st.session_state.sectors, period="2y")

    if master_2y is not None:
        leaderboard_rows = []
        sector_curves = {}

        for sec_name, tickers in st.session_state.sectors.items():
            sec_ohlc_df, valid_list = compute_equal_weight_index(tickers, master_2y)
            if sec_ohlc_df.empty:
                continue

            s_curve = sec_ohlc_df["Close"]
            sector_curves[sec_name] = s_curve

            p_slice = slice_by_window(s_curve, primary_window)
            c_slice = slice_by_window(s_curve, comparison_window)
            if len(p_slice) < 2 or len(c_slice) < 2:
                continue

            prim_ret = ((p_slice.iloc[-1] - p_slice.iloc[0]) / p_slice.iloc[0]) * 100.0
            comp_ret = ((c_slice.iloc[-1] - c_slice.iloc[0]) / c_slice.iloc[0]) * 100.0

            ker = calc_kaufman_efficiency(p_slice)
            r2 = calc_r_squared(p_slice)
            shp = calc_sharpe(p_slice)

            c_ker = calc_kaufman_efficiency(c_slice)
            c_r2 = calc_r_squared(c_slice)

            r_1w = calc_period_return(s_curve, "1 Week (5D)")
            r_2w = calc_period_return(s_curve, "2 Weeks (10D)")
            r_4w = calc_period_return(s_curve, "4 Weeks (1M)")
            r_3m = calc_period_return(s_curve, "3 Months (63D)")
            r_6m = calc_period_return(s_curve, "6 Months (126D)")
            r_1y = calc_period_return(s_curve, "1 Year (252D)")

            cut_dt = p_slice.index[0]
            gainers = 0
            counted = 0
            close_mat = master_2y["Close"]
            for t in valid_list:
                stk_s = close_mat[t].dropna()
                stk_s = stk_s[stk_s.index >= cut_dt]
                if len(stk_s) >= 2:
                    counted += 1
                    if stk_s.iloc[-1] >= stk_s.iloc[0]:
                        gainers += 1
            breadth_pct = round((gainers / counted) * 100.0, 1) if counted > 0 else 0.0

            pct_20, pct_50, pct_200 = calc_ma_breadth(close_mat, valid_list)

            leaderboard_rows.append({
                "Sector": sec_name,
                "Active Stocks": len(valid_list),
                "Primary Return (%)": round(prim_ret, 2),
                "Comparison Return (%)": round(comp_ret, 2),
                "1W (%)": round(r_1w, 2) if pd.notna(r_1w) else np.nan,
                "2W (%)": round(r_2w, 2) if pd.notna(r_2w) else np.nan,
                "4W (%)": round(r_4w, 2) if pd.notna(r_4w) else np.nan,
                "3M (%)": round(r_3m, 2) if pd.notna(r_3m) else np.nan,
                "6M (%)": round(r_6m, 2) if pd.notna(r_6m) else np.nan,
                "1Y (%)": round(r_1y, 2) if pd.notna(r_1y) else np.nan,
                "Kaufman Ratio (KER)": round(ker, 3),
                "R-Squared (Trend)": round(r2, 3),
                "Sharpe Ratio": round(shp, 2),
                "Breadth (Gainers)": f"{gainers}/{counted} ({breadth_pct}%)",
                "% > 20 DMA": pct_20,
                "% > 50 DMA": pct_50,
                "% > 200 DMA": pct_200,
                "_prim_ret": prim_ret,
                "_comp_ret": comp_ret,
                "_ker": ker,
                "_r2": r2,
                "_c_ker": c_ker,
                "_c_r2": c_r2,
                "_shp": shp,
                "_breadth": breadth_pct
            })

        if leaderboard_rows:
            df_lead = pd.DataFrame(leaderboard_rows)
            df_lead["Primary Momentum Score"] = compute_composite_scores(df_lead, "_prim_ret", "_r2", "_ker")
            df_lead["Baseline Momentum Score"] = compute_composite_scores(df_lead, "_comp_ret", "_c_r2", "_c_ker")

            df_lead["Primary Rank"] = df_lead["Primary Momentum Score"].rank(ascending=False, method="min").astype(int)
            df_lead["Baseline Rank"] = df_lead["Baseline Momentum Score"].rank(ascending=False, method="min").astype(int)
            df_lead["Rank Change"] = df_lead["Baseline Rank"] - df_lead["Primary Rank"]

            sort_col_map = {
                "Primary Momentum Score": "Primary Momentum Score",
                "Primary Return (%)": "_prim_ret",
                "1W (%)": "1W (%)",
                "2W (%)": "2W (%)",
                "4W (%)": "4W (%)",
                "3M (%)": "3M (%)",
                "6M (%)": "6M (%)",
                "1Y (%)": "1Y (%)",
                "Kaufman Efficiency Ratio (Smoothness)": "_ker",
                "R-Squared (Trend Fit)": "_r2",
                "Sharpe Ratio": "_shp",
                "Breadth (% Gainers)": "_breadth",
                "% > 50 DMA": "% > 50 DMA",
                "% > 200 DMA": "% > 200 DMA"
            }
            df_lead = df_lead.sort_values(by=sort_col_map[sort_metric], ascending=False)

            display_cols = [
                "Primary Rank", "Rank Change", "Sector", "Active Stocks",
                "Primary Momentum Score", "Baseline Momentum Score",
                "Primary Return (%)", "Comparison Return (%)",
                "1W (%)", "2W (%)", "4W (%)", "3M (%)", "6M (%)", "1Y (%)",
                "Breadth (Gainers)", "% > 20 DMA", "% > 50 DMA", "% > 200 DMA",
                "Kaufman Ratio (KER)", "R-Squared (Trend)", "Sharpe Ratio"
            ]
            st.dataframe(df_lead[display_cols], use_container_width=True, hide_index=True)

            top_row = df_lead.iloc[0]
            st.success(
                f"🏆 Top Ranked Sector ({primary_window}): **{top_row['Sector']}** | "
                f"Momentum Score: **{top_row['Primary Momentum Score']}/100** | "
                f"Return: **{top_row['Primary Return (%)']}%** | "
                f"Breadth > 50 DMA: **{top_row['% > 50 DMA']}%**"
            )

            # --- WEEKLY SECTOR RANK HISTORY (BUMP CHART) ---
            st.markdown("### 📊 Weekly Sector Momentum Rank History (Last 16 Weeks)")
            st.caption("Tracks how each sector's 4-Week Momentum Rank evolved week-by-week (Rank 1 at the top = strongest sector).")

            curves_df = pd.DataFrame(sector_curves).sort_index().ffill()
            weekly_closes = curves_df.resample("W-FRI").last().dropna(how="all")

            if len(weekly_closes) >= 6:
                rolling_4w_ret = weekly_closes.pct_change(4).dropna(how="all") * 100.0
                recent_weeks = rolling_4w_ret.tail(16)
                weekly_ranks = recent_weeks.rank(axis=1, ascending=False, method="min")

                default_rank_secs = list(df_lead["Sector"].head(6))
                rank_sectors_sel = st.multiselect(
                    "Select Sectors to Trace on Rank History Chart:",
                    options=list(st.session_state.sectors.keys()),
                    default=default_rank_secs
                )

                if rank_sectors_sel:
                    fig_rank = go.Figure()
                    palette = [
                        "#2962FF", "#00C853", "#AA00FF", "#FF6D00",
                        "#00B8D4", "#D50000", "#FFD600", "#C51162"
                    ]
                    for idx_c, s_name in enumerate(rank_sectors_sel):
                        if s_name in weekly_ranks.columns:
                            fig_rank.add_trace(go.Scatter(
                                x=weekly_ranks.index,
                                y=weekly_ranks[s_name],
                                mode="lines+markers",
                                name=s_name,
                                line=dict(width=2.5, color=palette[idx_c % len(palette)]),
                                marker=dict(size=7)
                            ))
                    fig_rank.update_layout(
                        yaxis=dict(title="Sector Rank (1 = Top Leader)", autorange="reversed", dtick=2),
                        xaxis_title="Week Ending (Friday)",
                        height=500,
                        legend=dict(
                            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0,
                            bgcolor="rgba(255, 255, 255, 0.92)", bordercolor="#888888", borderwidth=1,
                            font=dict(color="#111111", size=11)
                        ),
                        margin=dict(l=10, r=10, t=60, b=10)
                    )
                    st.plotly_chart(fig_rank, use_container_width=True)


# ==============================================================================
# TAB 4: STOCK ATTRIBUTION, MULTI-WINDOW RETURNS & MOVING-AVERAGE DEEP-DIVE
# ==============================================================================
with main_tab4:
    st.subheader("🔍 Sector Stock Attribution, Multi-Horizon Returns & Trend Deep-Dive")
    st.caption(
        "Inspect every constituent in a sector across 1W/2W/4W/3M/6M/1Y windows, "
        "standard deviation, individual momentum score, distance from 50/200 DMA, and index lift/drag."
    )

    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        att_sector = st.selectbox("Select Sector to Drill Down:", list(st.session_state.sectors.keys()), index=0)
    with col_d2:
        att_window = st.selectbox("Attribution Window:", list(WINDOW_DAYS_MAP.keys()), index=3)
    with col_d3:
        stk_sort_by = st.selectbox(
            "Sort Constituents By:",
            [
                "Contribution to Index (%)",
                "Stock Momentum Score",
                "Window Return (%)",
                "1W (%)",
                "4W (%)",
                "3M (%)",
                "1Y (%)",
                "Trend Smoothness (KER)",
                "Annualized Volatility (%)"
            ],
            index=0
        )

    stk_constituents = st.session_state.sectors[att_sector]
    with st.spinner("Retrieving full constituent prices from unified cache..."):
        master_2y = load_master_universe(st.session_state.sectors, period="2y")
        sec_ohlc_df, valid_stocks = compute_equal_weight_index(stk_constituents, master_2y)

    if not sec_ohlc_df.empty and valid_stocks:
        idx_slice = slice_by_window(sec_ohlc_df["Close"], att_window)
        sec_tot_ret = ((idx_slice.iloc[-1] - idx_slice.iloc[0]) / idx_slice.iloc[0]) * 100.0 if len(idx_slice) >= 2 else 0.0

        close_mat = master_2y["Close"]
        pct_20, pct_50, pct_200 = calc_ma_breadth(close_mat, valid_stocks)

        stock_rows = []
        n_const = len(valid_stocks)

        for t in valid_stocks:
            full_s = close_mat[t].dropna()
            s_slice = slice_by_window(full_s, att_window)
            if len(s_slice) >= 2:
                p_ret = ((s_slice.iloc[-1] - s_slice.iloc[0]) / s_slice.iloc[0]) * 100.0
                contr = p_ret / n_const
                vol = s_slice.pct_change().dropna().std() * np.sqrt(252.0) * 100.0 if len(s_slice) >= 3 else 0.0
                stk_ker = calc_kaufman_efficiency(s_slice)
                stk_r2 = calc_r_squared(s_slice)

                ma50 = full_s.iloc[-50:].mean() if len(full_s) >= 50 else np.nan
                ma200 = full_s.iloc[-200:].mean() if len(full_s) >= 200 else np.nan

                stock_rows.append({
                    "Ticker": t,
                    "CMP (Rs)": round(float(full_s.iloc[-1]), 2),
                    "Window Return (%)": round(p_ret, 2),
                    "Contribution to Index (%)": round(contr, 2),
                    "1W (%)": round(calc_period_return(full_s, "1 Week (5D)"), 2),
                    "2W (%)": round(calc_period_return(full_s, "2 Weeks (10D)"), 2),
                    "4W (%)": round(calc_period_return(full_s, "4 Weeks (1M)"), 2),
                    "3M (%)": round(calc_period_return(full_s, "3 Months (63D)"), 2),
                    "6M (%)": round(calc_period_return(full_s, "6 Months (126D)"), 2),
                    "1Y (%)": round(calc_period_return(full_s, "1 Year (252D)"), 2),
                    "Annualized Volatility (%)": round(float(vol), 1) if pd.notna(vol) else 0.0,
                    "Trend Smoothness (KER)": round(stk_ker, 3),
                    "R-Squared": round(stk_r2, 3),
                    "vs 50 DMA (%)": round(((full_s.iloc[-1] - ma50) / ma50) * 100.0, 1) if pd.notna(ma50) else np.nan,
                    "vs 200 DMA (%)": round(((full_s.iloc[-1] - ma200) / ma200) * 100.0, 1) if pd.notna(ma200) else np.nan,
                    "_ret_raw": p_ret,
                    "_ker_raw": stk_ker,
                    "_r2_raw": stk_r2,
                    "_contr_raw": contr
                })

        if stock_rows:
            df_stocks = pd.DataFrame(stock_rows)
            df_stocks["Stock Momentum Score"] = compute_composite_scores(
                df_stocks, "_ret_raw", "_r2_raw", "_ker_raw"
            )

            gainers_cnt = int((df_stocks["_ret_raw"] >= 0).sum())
            losers_cnt = len(df_stocks) - gainers_cnt

            m_c1, m_c2, m_c3, m_c4 = st.columns(4)
            m_c1.metric(f"{att_window} Sector Return", f"{sec_tot_ret:+,.2f}%")
            m_c2.metric("Winning vs Losing Stocks", f"{gainers_cnt} W / {losers_cnt} L", f"{round(gainers_cnt/len(df_stocks)*100, 1)}% Win Rate")
            m_c3.metric("Stocks > 50 DMA", f"{pct_50:.1f}%", f"{pct_20:.1f}% > 20 DMA")
            m_c4.metric("Stocks > 200 DMA", f"{pct_200:.1f}%")

            by_contr = df_stocks.sort_values(by="_contr_raw", ascending=False)
            top_col1, top_col2 = st.columns(2)
            with top_col1:
                st.markdown("### 🚀 Top 3 Rally Leaders (Biggest Positive Lift)")
                st.dataframe(
                    by_contr.head(3)[["Ticker", "Window Return (%)", "Contribution to Index (%)", "Stock Momentum Score"]],
                    use_container_width=True, hide_index=True
                )
            with top_col2:
                st.markdown("### 🔻 Top 3 Index Draggers (Biggest Negative Pull)")
                st.dataframe(
                    by_contr.tail(3).sort_values(by="_contr_raw", ascending=True)[
                        ["Ticker", "Window Return (%)", "Contribution to Index (%)", "Stock Momentum Score"]
                    ],
                    use_container_width=True, hide_index=True
                )

            stk_sort_map = {
                "Contribution to Index (%)": "_contr_raw",
                "Stock Momentum Score": "Stock Momentum Score",
                "Window Return (%)": "_ret_raw",
                "1W (%)": "1W (%)",
                "4W (%)": "4W (%)",
                "3M (%)": "3M (%)",
                "1Y (%)": "1Y (%)",
                "Trend Smoothness (KER)": "_ker_raw",
                "Annualized Volatility (%)": "Annualized Volatility (%)"
            }
            df_stocks = df_stocks.sort_values(by=stk_sort_map[stk_sort_by], ascending=False)

            st.markdown("### 📋 Complete Constituent Multi-Horizon Breakdown")
            display_stk_cols = [
                "Ticker", "CMP (Rs)", "Stock Momentum Score",
                "Window Return (%)", "Contribution to Index (%)",
                "1W (%)", "2W (%)", "4W (%)", "3M (%)", "6M (%)", "1Y (%)",
                "vs 50 DMA (%)", "vs 200 DMA (%)",
                "Trend Smoothness (KER)", "R-Squared", "Annualized Volatility (%)"
            ]
            st.dataframe(df_stocks[display_stk_cols], use_container_width=True, hide_index=True)
