import os
import json
import time
import random
from datetime import datetime, timedelta, timezone
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

# ==============================================================================
# 1. COMPLETE 27-SECTOR MASTER DIRECTORY & DYNAMIC UNIVERSE BUILDER
# ==============================================================================
DEFAULT_SECTORS = {
    "1. Banking (PSU, Private & SFBs)": [
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS",
        "PNB.NS", "UNIONBANK.NS", "BANKBARODA.NS", "CANBK.NS", "FEDERALBNK.NS",
        "AUBANK.NS", "IDFCFIRSTB.NS", "YESBANK.NS", "INDUSINDBK.NS", "BANDHANBNK.NS",
        "RBLBANK.NS", "CUB.NS", "KARURVYSYA.NS", "SOUTHBANK.NS", "J&KBANK.NS",
        "MAHABANK.NS", "CENTRALBK.NS", "PSB.NS", "IOB.NS", "UCOBANK.NS",
        "CSBBANK.NS", "KTKBANK.NS", "EQUITASBNK.NS", "JSFB.NS", "UTKARSHBNK.NS",
        "SURYODAY.NS", "ESAFSFB.NS", "UJJIVANSFB.NS", "BANKINDIA.NS", "INDIANB.NS",
        "DCBBANK.NS"
    ],
    "2. Information Technology & Software": [
        "TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS",
        "LTM.NS", "PERSISTENT.NS", "COFORGE.NS", "MPHASIS.NS", "TATAELXSI.NS",
        "LTTS.NS", "OFSS.NS", "CYIENT.NS", "BSOFT.NS", "KPITTECH.NS",
        "ZENSARTECH.NS", "SONATSOFTW.NS", "MASTEK.NS", "FSL.NS", "SAKSOFT.NS",
        "SASKEN.NS", "NEWGEN.NS", "RSYSTEMS.NS", "HAPPSTMNDS.NS", "E2E.NS",
        "ECLERX.NS", "DATAMATICS.NS", "NUCLEUS.NS", "RAMCOSYS.NS", "INFOBEAN.NS",
        "BBOX.NS", "NINSYS.NS", "AURIONPRO.NS", "FRACTAL.NS", "NETWEB.NS",
        "SILVERTUC.NS", "ESDS.NS", "PROTEAN.NS", "63MOONS.NS", "STYL.NS",
        "TECHNVISN.NS", "XTRANET.NS", "EMUDHRA.NS", "CAPILLARY.NS", "ONEPOINT.NS"
    ],
    "3. Automobile (OEMs, 2W, 4W, CVs & EVs)": [
        "MARUTI.NS", "M&M.NS", "TATAMOTORS.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS",
        "TVSMOTOR.NS", "EICHERMOT.NS", "ASHOKLEY.NS", "HYUNDAI.NS", "FORCEMOT.NS",
        "TMPV.NS", "TMCV.NS", "OLAELEC.NS", "ATHERENERG.NS", "ESCORTS.NS",
        "SMLMAH.NS", "VSTTILLERS.NS", "OLECTRA.NS", "TIINDIA.NS"
    ],
    "4. Auto Components, Ancillaries & Tyres": [
        "MOTHERSON.NS", "BHARATFORG.NS", "BOSCHLTD.NS", "UNOMINDA.NS", "ENDURANCE.NS",
        "SONACOMS.NS", "MRF.NS", "BALKRISIND.NS", "CEATLTD.NS", "APOLLOTYRE.NS",
        "JKTYRE.NS", "EXIDEIND.NS", "AMBER.NS", "SCHAEFFLER.NS", "SKFINDIA.NS",
        "CRAFTSMAN.NS", "SANSERA.NS", "TIMKEN.NS", "GABRIEL.NS", "CIEINDIA.NS",
        "LUMAXIND.NS", "LUMAXTECH.NS", "FIEMIND.NS", "ROLEXRINGS.NS", "GNA.NS",
        "AUTOAXLES.NS", "RACLGEAR.NS", "TALBROAUTO.NS", "PRICOLLTD.NS", "SUBROS.NS",
        "SURYAROSNI.NS", "BALUFORGE.NS", "SHARDAMOTR.NS", "HAPPYFORGE.NS", "MSUMI.NS",
        "SHRIPISTON.NS", "DIVGIITTS.NS", "DHOOTTRANS.NS", "SSWL.NS", "RICOAUTO.NS",
        "RKFORGE.NS", "WHEELS.NS", "MINDACORP.NS", "JTEKTINDIA.NS", "NDRAUTO.NS",
        "BANCOINDIA.NS", "KROSS.NS", "GOODYEAR.NS", "SUPRAJIT.NS", "JBMA.NS",
        "INDNIPPON.NS", "JAMNAAUTO.NS", "ASKAUTOLTD.NS", "NRBBEARING.NS", "MENONBE.NS",
        "TENNIND.NS", "STUDDS.NS", "FMGOETZE.NS", "LGBBROSLTD.NS", "VARROC.NS",
        "RML.NS", "TVSSRICHAK.NS"
    ],
    "5. Pharmaceuticals & Formulations": [
        "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "LUPIN.NS", "TORNTPHARM.NS",
        "AUROPHARMA.NS", "ZYDUSLIFE.NS", "MANKIND.NS", "ALKEM.NS", "GLENMARK.NS",
        "LAURUSLABS.NS", "IPCALAB.NS", "BIOCON.NS", "AJANTPHARM.NS", "GLAXO.NS",
        "PFIZER.NS", "SANOFI.NS", "ABBOTINDIA.NS", "NATCOPHARM.NS", "ERIS.NS",
        "JUBLPHARMA.NS", "STAR.NS", "MARKSANS.NS", "FDC.NS", "UNICHEMLAB.NS",
        "CORONA.NS", "WOCKPHARMA.NS", "CAPLIPOINT.NS", "VENUSREM.NS", "SENORES.NS",
        "ZOTA.NS", "KPL.NS", "INDOCO.NS", "SYNCOMF.NS", "PPLPHARMA.NS",
        "SHILPAMED.NS", "PANACEABIO.NS", "GUJTHEM.NS", "AARTIDRUGS.NS", "AKUMS.NS",
        "INNOVACAP.NS", "APLLTD.NS", "MOREPENLAB.NS", "ORCHPHARMA.NS", "SANOFICONR.NS",
        "WINDLAS.NS", "SAIPARENT.NS", "INDSWFTLAB.NS", "BLISSGVS.NS"
    ],
    "6. Healthcare, Hospitals & Diagnostics": [
        "APOLLOHOSP.NS", "MAXHEALTH.NS", "FORTIS.NS", "MEDANTA.NS", "NH.NS",
        "KIMS.NS", "ASTERDM.NS", "RAINBOW.NS", "LALPATHLAB.NS", "METROPOLIS.NS",
        "VIJAYA.NS", "THYROCARE.NS", "ARTEMISMED.NS", "KOVAI.NS", "YATHARTH.NS",
        "JLHL.NS", "KRSNAA.NS", "SURAKSHA.NS", "DRAGARWQ.NS", "MOLBIO.NS",
        "NEPHROPLUS.NS", "PARKHOSPS.NS", "INDRAMEDCO.NS", "AGARWALEYE.NS", "FISCHER.NS"
    ],
    "7. API, CDMO & Life Sciences": [
        "DIVISLAB.NS", "LAURUSLABS.NS", "SYNGENE.NS", "SOLARA.NS", "SMSPHARMA.NS",
        "GRANULES.NS", "NEULANDLAB.NS", "AARTIPHARM.NS", "SUPRIYA.NS", "SUDEEPPHRM.NS",
        "ANTHEM.NS", "SAILIFE.NS", "ALIVUS.NS", "RPGLIFE.NS", "NGLFINE.NS",
        "GUJTHEM.NS", "VIYASH.NS", "CONCORDBIO.NS", "COHANCE.NS", "RUBICON.NS",
        "BLUEJET.NS", "TATVA.NS", "ONESOURCE.NS", "DCAL.NS", "GLAND.NS"
    ],
    "8. Chemicals & Petrochemicals": [
        "SRF.NS", "DEEPAKNTR.NS", "PIIND.NS", "TATACHEM.NS", "AARTIIND.NS",
        "NAVINFLUOR.NS", "FLUOROCHEM.NS", "ATUL.NS", "FINEORG.NS", "SUMICHEM.NS",
        "VINATIORGA.NS", "ALKYLAMINE.NS", "BALAMINES.NS", "NOCIL.NS", "HSCL.NS",
        "CLEAN.NS", "ANURAS.NS", "AETHER.NS", "ROSSARI.NS", "EPIGRAL.NS",
        "PRIVISCL.NS", "CAMLINFINE.NS", "PCBL.NS", "GUJALKALI.NS", "GRAUWEIL.NS",
        "OAL.NS", "PAUSHAKLTD.NS", "CHEMPLASTS.NS", "HLEGLAS.NS", "LINDEINDIA.NS",
        "ACUTAAS.NS", "STALLION.NS", "ELANTAS.NS", "RAIN.NS", "COSMOFIRST.NS",
        "APCOTEXIND.NS", "LXCHEM.NS", "ACI.NS", "GHCL.NS", "JGCHEM.NS",
        "SHREEPUSHK.NS", "BHARATRAS.NS", "SUDARSCHEM.NS", "STYRENIX.NS", "BHAGCHEM.NS",
        "FCL.NS", "YASHO.NS", "BEPL.NS", "SPLPETRO.NS", "BODALCHEM.NS",
        "INDIAGLYCO.NS", "BHAGERIA.NS", "KIRIINDUS.NS", "SHK.NS", "INDOBORAX.NS",
        "TIRUMALCHM.NS"
    ],
    "9. Agrochemicals & Fertilizers": [
        "UPL.NS", "PIIND.NS", "COROMANDEL.NS", "BAYERCROP.NS", "SUMICHEM.NS",
        "FACT.NS", "RCF.NS", "GNFC.NS", "GSFC.NS", "CHAMBLFERT.NS",
        "DEEPAKFERT.NS", "SHARDACROP.NS", "DHANUKA.NS", "INSECTICID.NS", "BHARATRAS.NS",
        "NACLIND.NS", "NFL.NS", "MBAPL.NS", "PARADEEP.NS", "RALLIS.NS",
        "GSPCROP.NS", "BNAGROCHEM.NS", "ASTEC.NS", "KSCL.NS"
    ],
    "10. Metals, Mining & Steel": [
        "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "JINDALSTEL.NS", "VEDL.NS",
        "SAIL.NS", "NMDC.NS", "COALINDIA.NS", "NATIONALUM.NS", "HINDZINC.NS",
        "HINDCOPPER.NS", "JSL.NS", "APLAPOLLO.NS", "WELCORP.NS", "JINDALSAW.NS",
        "RATNAMANI.NS", "GPIL.NS", "SHYAMMETL.NS", "KSL.NS", "MAHASTEEL.NS",
        "PRAKASH.NS", "MOIL.NS", "KIOCL.NS", "ORISSAMINE.NS", "SAMBHV.NS",
        "RSL.NS", "JAYNECOIND.NS", "RATNAVEER.NS", "VAML.NS", "MIDWESTLTD.NS",
        "GOODLUCK.NS", "MANINDS.NS", "VSSL.NS", "LLOYDSME.NS", "USHAMART.NS",
        "SUNFLAG.NS", "WELSPLSOL.NS", "BIRLACORPN.NS", "STEELCAS.NS", "VENUSPIPES.NS",
        "NSLNISP.NS", "MSPL.NS", "KIRLFER.NS", "ELECTCAST.NS", "MUKANDLTD.NS",
        "SARDAEN.NS", "MAITHANALL.NS", "SANDUMA.NS", "IMFA.NS", "JAIBALAJI.NS",
        "BHARATCOAL.NS", "GALLANTT.NS", "MAHSEAMLES.NS", "ARFIN.NS", "JAINREC.NS",
        "GRAVITA.NS", "DECNGOLD.NS"
    ],
    "11. Cement & Building Materials": [
        "ULTRACEMCO.NS", "AMBUJACEM.NS", "ACC.NS", "SHREECEM.NS", "DALBHARAT.NS",
        "JSWCEMENT.NS", "RAMCOCEM.NS", "JKCEMENT.NS", "JKLAKSHMI.NS", "HEIDELBERG.NS",
        "STARCEMENT.NS", "MANGLMCEM.NS", "BIRLACORPN.NS", "SAGCEM.NS", "KCP.NS",
        "PRSMJOHNSN.NS", "ORIENTCEM.NS", "ASIANPAINT.NS", "BERGEPAINT.NS", "INDIGOPNTS.NS",
        "KANSAINER.NS", "PIDILITIND.NS", "CERA.NS", "SOMANYCERA.NS", "ASIANTILES.NS",
        "GREENPLY.NS", "GREENLAM.NS", "GREENPANEL.NS", "CENTURYPLY.NS", "STYLAMIND.NS",
        "ASTRAL.NS", "FINPIPE.NS", "PRINCEPIPE.NS", "APOLLOPIPE.NS", "SUPREMEIND.NS",
        "CARYSIL.NS", "KAJARIACER.NS", "NITCO.NS", "INTERARCH.NS", "JSWDULUX.NS",
        "SIRCA.NS"
    ],
    "12. Real Estate & Urban Developers": [
        "DLF.NS", "LODHA.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "PRESTIGE.NS",
        "PHOENIXLTD.NS", "BRIGADE.NS", "SOBHA.NS", "SIGNATURE.NS", "ANANTRAJ.NS",
        "MAHLIFE.NS", "SUNTECK.NS", "PURVA.NS", "KOLTEPATIL.NS", "ASHIANA.NS",
        "OMAXE.NS", "MARATHON.NS", "AJMERA.NS", "HUBTOWN.NS", "ARKADE.NS",
        "RUSTOMJEE.NS", "MAXESTATES.NS", "LOTUSDEV.NS", "GANESHHOU.NS", "TARC.NS",
        "ABREL.NS", "EMBDL.NS", "RAYMONDREL.NS", "DBREALTY.NS", "SCILAL.NS",
        "HEMIPROP.NS", "ARVSMART.NS", "SMARTWORKS.NS", "WEWORK.NS", "INDIQUBE.NS",
        "EFCIL.NS", "AWFIS.NS"
    ],
    "13. Infrastructure, EPC & Rail": [
        "LT.NS", "RVNL.NS", "IRCON.NS", "NCC.NS", "NBCC.NS",
        "PNCINFRA.NS", "GRINFRA.NS", "DBL.NS", "KNRCON.NS", "HCC.NS",
        "AFCONS.NS", "ASHOKA.NS", "HGINFRA.NS", "CEIGALL.NS", "PSPPROJECT.NS",
        "AHLUCONT.NS", "JKIL.NS", "PATELENG.NS", "GPTINFRA.NS", "BAJEL.NS",
        "TRANSRAILL.NS", "TITAGARH.NS", "TEXRAIL.NS", "SIMPLEXINF.NS", "MBEL.NS",
        "INDIANHUME.NS", "TEXINFRA.NS", "VIKRAN.NS", "GARUDA.NS", "EMSLIMITED.NS",
        "POWERMECH.NS", "RAMKY.NS", "IRB.NS", "GMRP&UI.NS", "CEMPRO.NS",
        "KMEW.NS", "DREDGECORP.NS"
    ],
    "14. Power Generation & Utilities": [
        "NTPC.NS", "TATAPOWER.NS", "JSWENERGY.NS", "POWERGRID.NS", "ADANIPOWER.NS",
        "ADANIENSOL.NS", "NHPC.NS", "SJVN.NS", "CESC.NS", "TORNTPOWER.NS",
        "NLCINDIA.NS", "RTNPOWER.NS", "JPPOWER.NS", "BGRENERGY.NS", "GIPCL.NS",
        "GMRP&UI.NS", "PTC.NS", "RELINFRA.NS", "RPOWER.NS", "BFUTILITIE.NS",
        "VEDPOWER.NS", "GUJENERGY.NS"
    ],
    "15. Renewable Energy & Green Transition": [
        "ADANIGREEN.NS", "SUZLON.NS", "INOXWIND.NS", "WAAREEENER.NS", "WAAREERTL.NS",
        "PREMIERENE.NS", "IREDA.NS", "NTPCGREEN.NS", "KPIGREEN.NS", "SWSOLAR.NS",
        "BORORENEW.NS", "INOXGREEN.NS", "VIKRAMSOLR.NS", "CLEANMAX.NS", "WEBELSOLAR.NS",
        "SAATVIKGL.NS", "UEL.NS", "SERVOTECH.NS", "ACMESOLAR.NS", "JNPR.NS",
        "EMMVEE.NS", "UTLSOLAR.NS", "RELTD.NS", "ADVAIT.NS", "GKENERGY.NS"
    ],
    "16. Electrical Equipment, Cables & Machinery": [
        "ABB.NS", "SIEMENS.NS", "BHEL.NS", "CGPOWER.NS", "POWERINDIA.NS",
        "GVT&D.NS", "HAVELLS.NS", "POLYCAB.NS", "KEI.NS", "FINCABLES.NS",
        "RRKABEL.NS", "VOLTAMP.NS", "TARIL.NS", "ENRIN.NS", "SCHNEIDER.NS",
        "HPL.NS", "GENUSPOWER.NS", "INDOTECH.NS", "QPOWER.NS", "TDPOWERSYS.NS",
        "SPECTRUM.NS", "DIACABS.NS", "PARACABLES.NS", "VIDYAWIRES.NS", "RAMRAT.NS",
        "PRECWIRE.NS", "HIRECT.NS", "CENTUM.NS", "VINDHYATEL.NS", "UNIVCABLES.NS",
        "DYCL.NS", "LASERPOWER.NS", "KSHINTL.NS", "BBL.NS", "MARINE.NS",
        "SHILCTECH.NS", "MVELECTRO.NS", "APARINDS.NS", "KRN.NS", "AEROFLEX.NS",
        "ELGIEQUIP.NS", "KIRLOSBROS.NS", "KIRLOSENG.NS", "KIRLPNU.NS", "TRITURBINE.NS",
        "ISGEC.NS", "ELECON.NS", "THEJO.NS", "JASH.NS", "OSWALPUMPS.NS", "SHAKTIPUMP.NS"
    ],
    "17. Defense, Aerospace & Heavy Engineering": [
        "HAL.NS", "BEL.NS", "BDL.NS", "MAZDOCK.NS", "COCHINSHIP.NS",
        "GRSE.NS", "BEML.NS", "PARAS.NS", "DATAPATTNS.NS", "MTARTECH.NS",
        "ZENTEC.NS", "IDEAFORGE.NS", "APOLLO.NS", "KRISHNADEF.NS", "SWANDEF.NS",
        "SIKA.NS", "ROSSTECH.NS", "UNIMECH.NS", "DYNAMATECH.NS", "AZAD.NS",
        "ASTRAMICRO.NS", "DCXINDIA.NS", "AVANTEL.NS", "HBLENGINE.NS", "AXISCADES.NS",
        "SOLARINDS.NS", "PREMEXPLN.NS", "GOCLCORP.NS"
    ],
    "18. Oil, Gas & Energy Distribution": [
        "RELIANCE.NS", "ONGC.NS", "IOC.NS", "BPCL.NS", "HINDPETRO.NS",
        "GAIL.NS", "PETRONET.NS", "IGL.NS", "MGL.NS", "ATGL.NS",
        "OIL.NS", "MRPL.NS", "CHENNPETRO.NS", "AEGISLOG.NS", "GULFOILLUB.NS",
        "CASTROLIND.NS", "CONFIPET.NS", "HINDOILEXP.NS", "PRABHA.NS", "DEEPINDS.NS",
        "JINDRILL.NS", "ASIANENE.NS", "VEEDOL.NS", "SOTL.NS", "PANAMAPET.NS",
        "GANDHAR.NS", "VOGL.NS", "ANTELOPUS.NS", "AEGISVOPAK.NS"
    ],
    "19. NBFCs, Housing Finance & Lending": [
        "BAJFINANCE.NS", "BAJAJFINSV.NS", "CHOLAFIN.NS", "SHRIRAMFIN.NS", "MUTHOOTFIN.NS",
        "POONAWALLA.NS", "M&MFIN.NS", "SUNDARMFIN.NS", "LTF.NS", "IIFL.NS",
        "MANAPPURAM.NS", "AADHARHFC.NS", "CANFINHOME.NS", "HOMEFIRST.NS", "APTUS.NS",
        "LICHSGFIN.NS", "HUDCO.NS", "PNBHOUSING.NS", "FIVESTAR.NS", "CREDITACC.NS",
        "FUSION.NS", "ARMANFIN.NS", "SPANDANA.NS", "SBFC.NS", "PAISALO.NS",
        "SATIN.NS", "SGFIN.NS", "AIIL.NS", "REPCOHOME.NS", "FEDFINA.NS",
        "MUTHOOTMF.NS", "IRFC.NS", "PFC.NS", "RECLTD.NS", "IFCI.NS",
        "BAJAJHFL.NS", "CHOLAHLDNG.NS", "MASFIN.NS", "INDOSTAR.NS", "INDIASHLTR.NS",
        "HDBFS.NS", "AYE.NS", "NORTHARC.NS", "SAMMAANCAP.NS", "MUFIN.NS"
    ],
    "20. Capital Markets, Exchanges, Wealth & AMCs": [
        "BSE.NS", "MCX.NS", "CDSL.NS", "CAMS.NS", "KFINTECH.NS",
        "ANGELONE.NS", "360ONE.NS", "NUVAMA.NS", "MOTILALOFS.NS", "ANANDRATHI.NS",
        "GEOJITFSL.NS", "SMCGLOBAL.NS", "SHAREINDIA.NS", "IEX.NS", "HDFCAMC.NS",
        "UTIAMC.NS", "NAM-INDIA.NS", "CRAMC.NS", "SBIFUNDS.NS", "CRISIL.NS",
        "ICRA.NS", "CARERATING.NS", "5PAISA.NS", "MONARCH.NS", "JMFINANCIL.NS",
        "EDELWEISS.NS", "GROWW.NS", "PRUDENT.NS", "ARSSBL.NS", "ALGOQUANT.NS",
        "TATAINVEST.NS", "BAJAJHLDNG.NS", "BFINVEST.NS", "KICL.NS", "NSIL.NS",
        "TSFINV.NS", "ELCIDIN.NS", "PILANIINVS.NS", "BENGALASM.NS", "GCSL.NS"
    ],
    "21. FMCG, Foods, Beverages & Dairy": [
        "HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS",
        "GODREJCP.NS", "MARICO.NS", "TATACONSUM.NS", "VBL.NS", "COLPAL.NS",
        "PATANJALI.NS", "EMAMILTD.NS", "PGHH.NS", "GILLETTE.NS", "JYOTHYLAB.NS",
        "HONASA.NS", "ZYDUSWELL.NS", "BIKAJI.NS", "DODLA.NS", "HATSUN.NS",
        "HERITGFOOD.NS", "PARAGMILK.NS", "LTFOODS.NS", "KRBL.NS", "AVADHSUGAR.NS",
        "BALRAMCHIN.NS", "RENUKA.NS", "BANARISUG.NS", "DALMIASUG.NS", "KWIL.NS",
        "VENKEYS.NS", "GODREJAGRO.NS", "UFBL.NS", "TRIVENI.NS", "AVTNPL.NS",
        "ORKLAINDIA.NS", "DIAMONDYD.NS", "BAJAJCON.NS", "BECTORFOOD.NS", "GRMOVER.NS",
        "RADICO.NS", "UNITDSPR.NS", "UBL.NS", "ABDL.NS", "GMBREW.NS", "TI.NS",
        "GLOBUSSPR.NS", "SDBL.NS", "PICCADIL.NS", "GRANDOAK.NS", "GOPAL.NS",
        "TASTYBITE.NS", "VADILALIND.NS", "MILKYMIST.NS", "SUNDROP.NS", "VINCOFE.NS",
        "CCL.NS", "ADFFOODS.NS", "GAEL.NS", "GOKULAGRO.NS", "AWL.NS", "MANORAMA.NS"
    ],
    "22. Retail, Consumer Brands, Footwear & E-Com": [
        "DMART.NS", "TRENT.NS", "V2RETAIL.NS", "VMM.NS", "STYLEBAAZA.NS",
        "CANTABIL.NS", "SHOPERSTOP.NS", "NYKAA.NS", "SWIGGY.NS", "NAUKRI.NS",
        "CARTRADE.NS", "MEESHO.NS", "FIRSTCRY.NS", "URBANCO.NS", "ZAGGLE.NS",
        "BATAINDIA.NS", "RELAXO.NS", "CAMPUS.NS", "METROBRAND.NS", "REDTAPE.NS",
        "SAFARI.NS", "VIPIND.NS", "CELLO.NS", "STOVEKRAFT.NS", "TTKPRESTIG.NS",
        "HAWKINCOOK.NS", "CROMPTON.NS", "VOLTAS.NS", "BLUESTARCO.NS", "WHIRLPOOL.NS",
        "IFBIND.NS", "LGEINDIA.NS", "DIXON.NS", "EUREKAFORB.NS", "SYMPHONY.NS",
        "ORIENTELEC.NS", "BAJAJELEC.NS", "EVEREADY.NS", "VGUARD.NS", "LENSKART.NS",
        "DEVYANI.NS", "RBA.NS", "WESTLIFE.NS", "JUBLFOOD.NS", "SAPPHIRE.NS",
        "DOMS.NS", "FLAIR.NS", "NAVNETEDUL.NS", "PWL.NS", "SEIL.NS",
        "CRIZAC.NS", "PAYTM.NS", "MOBIKWIK.NS", "PINELABS.NS", "TURTLEMINT.NS",
        "POLICYBZR.NS", "JUSTDIAL.NS", "INDIAMART.NS", "SFL.NS", "NILKAMAL.NS"
    ],
    "23. Hotels, Hospitality & Travel Services": [
        "INDHOTEL.NS", "EIHOTEL.NS", "THELEELA.NS", "CHALET.NS", "LEMONTREE.NS",
        "PARKHOTELS.NS", "SAMHI.NS", "JUNIPER.NS", "EIHAHOTELS.NS", "ITDC.NS",
        "TAJGVK.NS", "VENTIVE.NS", "BRIGHOTEL.NS", "WONDERLA.NS", "CORDELIA.NS",
        "TRAVELFOOD.NS", "YATRA.NS", "IXIGO.NS", "TBOTEK.NS", "INDIGO.NS",
        "EASEMYTRIP.NS", "ORIENTHOT.NS", "MHRIL.NS", "THOMASCOOK.NS", "RATEGAIN.NS",
        "IRCTC.NS", "BLS.NS"
    ],
    "24. Logistics, Shipping & Marine Infrastructure": [
        "ADANIPORTS.NS", "CONCOR.NS", "DELHIVERY.NS", "BLUEDART.NS", "INDIGO.NS",
        "SCI.NS", "GESHIP.NS", "TCI.NS", "TCIEXP.NS", "VRLLOG.NS",
        "MAHLOG.NS", "ALLCARGO.NS", "JSWINFRA.NS", "GPPL.NS", "GMRAIRPORT.NS",
        "SHADOWFAX.NS", "SHIPROCKET.NS", "LEAPIND.NS", "SEAMECLTD.NS", "TVSSCS.NS",
        "KMEW.NS", "DREDGECORP.NS", "GATEWAY.NS", "SHREEJISPG.NS", "DOLPHIN.NS",
        "BLACKBUCK.NS", "SINDHUTRAD.NS", "HORIZONIND.NS"
    ],
    "25. Textiles, Apparel, Innerwear & Accessories": [
        "PAGEIND.NS", "RAYMOND.NS", "RAYMONDLSL.NS", "ABFRL.NS", "ARVINDFASN.NS",
        "ARVIND.NS", "KPRMILL.NS", "TRIDENT.NS", "WELSPUNLIV.NS", "VTL.NS",
        "NITINSPIN.NS", "KITEX.NS", "GOKEX.NS", "SPAL.NS", "KKCL.NS",
        "LUXIND.NS", "DOLLAR.NS", "SIYSIL.NS", "SANGAMIND.NS", "FILATEX.NS",
        "INDORAMA.NS", "JINDWORLD.NS", "SPORTKING.NS", "AYMSYNTEX.NS", "MANYAVAR.NS",
        "PERNIASPOP.NS", "BOMDYEING.NS", "ALOKINDS.NS", "GARFIBRES.NS", "RUBYMILLS.NS",
        "SANATHAN.NS", "KUSUMGAR.NS", "SBC.NS"
    ],
    "26. Telecom, Digital Infrastructure & Media": [
        "BHARTIARTL.NS", "BHARTIHEXA.NS", "IDEA.NS", "INDUSTOWER.NS", "TATACOMM.NS",
        "TEJASNET.NS", "HFCL.NS", "ROUTE.NS", "TANLA.NS", "STLTECH.NS",
        "OPTIEMUS.NS", "VINDHYATEL.NS", "TTML.NS", "HATHWAY.NS", "STLNETWORK.NS",
        "EXICOM.NS", "SUNTV.NS", "ZEEL.NS", "PVRINOX.NS", "SAREGAMA.NS",
        "TIPSMUSIC.NS", "NETWORK18.NS", "DBCORP.NS", "NAZARA.NS", "IMAGICAA.NS",
        "AMAGI.NS", "BCG.NS"
    ],
    "27. Nifty Jewellery & Watches Equal-Weight": [
        "TITAN.NS", "KALYANKJIL.NS", "LALITHAA.NS", "SKYGOLD.NS", "PCJEWELLER.NS",
        "THANGAMAYL.NS", "BLUESTONE.NS", "PNGJL.NS", "TIMEX.NS", "ETHOSLTD.NS",
        "SENCO.NS", "DPABHUSHAN.NS", "TBZ.NS", "GOLDIAM.NS", "KDDL.NS"
    ]
}


def format_nse_ticker(raw_sym):
    sym = raw_sym.strip().upper()
    if not sym:
        return ""
    if not sym.endswith(".NS") and not sym.endswith(".BO") and not sym.startswith("^"):
        sym += ".NS"
    return sym


if "sectors" not in st.session_state:
    st.session_state.sectors = {
        k: list(dict.fromkeys(format_nse_ticker(t) for t in v if t.strip()))
        for k, v in DEFAULT_SECTORS.items()
    }


def build_universe_mappings(sectors_dict):
    """
    Builds the deduplicated UNIQUE_TICKERS list, maps each ticker to its sector(s),
    and identifies multi-sector duplicate tickers.
    """
    ticker_to_sectors = {}
    total_allocations = 0
    for sec_name, t_list in sectors_dict.items():
        for raw_t in dict.fromkeys(t_list):
            t = format_nse_ticker(raw_t)
            if not t:
                continue
            total_allocations += 1
            ticker_to_sectors.setdefault(t, []).append(sec_name)

    unique_tickers = sorted(ticker_to_sectors.keys())
    duplicate_tickers = {
        t: secs for t, secs in sorted(ticker_to_sectors.items()) if len(secs) > 1
    }
    return unique_tickers, ticker_to_sectors, duplicate_tickers, total_allocations


UNIQUE_TICKERS, TICKER_TO_SECTORS, DUPLICATE_TICKERS, TOTAL_SECTOR_ALLOCATIONS = (
    build_universe_mappings(st.session_state.sectors)
)

st.title("🏛️ Quantitative Equal-Weighted Sector & Momentum Terminal")
st.caption(
    f"Live Universe: {len(UNIQUE_TICKERS)} Unique Stocks ({TOTAL_SECTOR_ALLOCATIONS} Sector Allocations, "
    f"{len(DUPLICATE_TICKERS)} Multi-Sector Overlap Tickers) Across {len(st.session_state.sectors)} Sectors | "
    "Parquet Local Cache | 1W/2W/4W/3M/6M/1Y Momentum, Rank History, RS & MA Breadth"
)


# ==============================================================================
# 2. RATE-LIMIT AWARE PRICE FETCHER (YAHOO + .BO FALLBACK + BROKER API STUB)
# ==============================================================================
DATA_PROVIDER = "yahoo"  # Change to "broker" after filling in fetch_prices_broker_stub()
MAX_REFRESH_PER_RUN = 150


def _is_rate_limit(exc):
    name = type(exc).__name__
    msg = str(exc).lower()
    return (
        "ratelimit" in name.lower()
        or "too many requests" in msg
        or "429" in msg
        or "rate limit" in msg
    )


def _download_chunk_with_backoff(chunk, start_str, end_str, max_attempts=5):
    """
    Downloads a multi-ticker chunk with threads=False and exponential backoff
    (5s, 10s, 20s, 40s, 80s + random jitter) on HTTP 429 / silent throttling.
    """
    delay = 5.0
    for attempt in range(max_attempts):
        try:
            raw = yf.download(
                chunk,
                start=start_str,
                end=end_str,
                auto_adjust=True,
                group_by="column",
                threads=False,
                progress=False
            )
            if raw is not None and not raw.empty:
                return raw, "ok"
            # An empty result on a multi-ticker chunk often means silent throttling
        except Exception as e:
            if not _is_rate_limit(e):
                return None, f"error: {type(e).__name__}"
        if attempt < max_attempts - 1:
            time.sleep(delay + random.uniform(0.0, 2.0))
            delay = min(delay * 2.0, 120.0)
    return None, "rate_limit"


def _download_single_ticker_with_backoff(sym, start_str, end_str, max_attempts=3):
    """
    Downloads a single ticker (used for .NS retry and .BO rescue fallback).
    Only backs off if a rate-limit error is raised so genuinely non-existent .NS
    symbols fail over to .BO immediately without stalling.
    """
    delay = 5.0
    for attempt in range(max_attempts):
        try:
            df = yf.Ticker(sym).history(start=start_str, end=end_str, auto_adjust=True)
            if df is not None and not df.empty and "Close" in df.columns and not df["Close"].dropna().empty:
                return df, "ok"
            return pd.DataFrame(), "empty"
        except Exception as e:
            if not _is_rate_limit(e):
                return pd.DataFrame(), f"error: {type(e).__name__}"
            if attempt < max_attempts - 1:
                time.sleep(delay + random.uniform(0.0, 2.0))
                delay = min(delay * 2.0, 60.0)
    return pd.DataFrame(), "rate_limit"


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


def fetch_prices_broker_stub(tickers, start, end, broker="kite"):
    """
    OPTIONAL PAID BROKER API STUB (Zerodha Kite Connect / Upstox / DhanHQ).
    -----------------------------------------------------------------------
    WHAT YOU MUST FILL IN TO ACTIVATE:
    1. Set DATA_PROVIDER = "broker" above.
    2. Provide your API_KEY and daily ACCESS_TOKEN below (or in st.secrets).
    3. Provide an INSTRUMENT_MAP mapping NSE symbols (e.g. "HDFCBANK.NS") to your
       broker's numeric instrument_token / security_id.
    4. Ensure you pass `continuous=False` (or the broker's split/bonus corporate-action
       adjusted flag) so historical candles are adjusted for splits and bonuses.
    """
    API_KEY = os.environ.get("BROKER_API_KEY", "YOUR_API_KEY_HERE")
    ACCESS_TOKEN = os.environ.get("BROKER_ACCESS_TOKEN", "YOUR_DAILY_ACCESS_TOKEN_HERE")
    RATE_LIMIT_CALLS_PER_SEC = 3  # Kite Connect allows 3 historical requests/sec

    raise NotImplementedError(
        f"Broker provider '{broker}' selected (API_KEY={API_KEY[:4]}***), "
        f"but instrument token mapping and live session are not configured yet. "
        f"Fill in API_KEY, ACCESS_TOKEN, and INSTRUMENT_MAP in fetch_prices_broker_stub() "
        f"with rate limit {RATE_LIMIT_CALLS_PER_SEC} req/s, or keep DATA_PROVIDER = 'yahoo'."
    )


def fetch_prices(tickers, start, end, provider=DATA_PROVIDER, chunk_size=45, progress_cb=None):
    """
    Single price-fetching gateway for the entire application.
    - Downloads each unique ticker once in chunks of ~45 with _download_chunk_with_backoff().
    - Retries any failed .NS ticker with the .BO (BSE) suffix before giving up,
      storing rescued prices under the original .NS key and logging the rescue.
    - Returns {"Open", "High", "Low", "Close", "rescued_bo", "had_rate_limit"}.
    """
    unique_list = sorted(set(format_nse_ticker(t) for t in tickers if t and t.strip()))
    if not unique_list:
        return None

    if provider == "broker":
        return fetch_prices_broker_stub(unique_list, start, end)

    start_str = pd.Timestamp(start).strftime("%Y-%m-%d")
    end_str = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    ohlc_parts = {"Open": [], "High": [], "Low": [], "Close": []}
    total_chunks = max(1, (len(unique_list) + chunk_size - 1) // chunk_size)
    had_rate_limit = False

    for idx_chunk, i in enumerate(range(0, len(unique_list), chunk_size)):
        chunk = unique_list[i:i + chunk_size]
        if progress_cb is not None:
            progress_cb(
                idx_chunk / total_chunks,
                f"Downloading chunk {idx_chunk + 1}/{total_chunks} ({len(chunk)} tickers)..."
            )

        raw_chunk, status = _download_chunk_with_backoff(chunk, start_str, end_str)
        if status == "rate_limit":
            had_rate_limit = True

        if raw_chunk is not None and not raw_chunk.empty:
            extracted = _extract_ohlc_from_yf_chunk(raw_chunk, chunk)
            for f in ("Open", "High", "Low", "Close"):
                if not extracted[f].empty:
                    ohlc_parts[f].append(extracted[f])

        # Polite pause between chunks to avoid Yahoo Finance rate limiting
        if idx_chunk < total_chunks - 1:
            time.sleep(0.4 + random.uniform(0.0, 0.25))

    if not ohlc_parts["Close"]:
        return {
            "Open": pd.DataFrame(),
            "High": pd.DataFrame(),
            "Low": pd.DataFrame(),
            "Close": pd.DataFrame(),
            "rescued_bo": {},
            "had_rate_limit": had_rate_limit
        }

    raw_ohlc = {}
    for f in ("Open", "High", "Low", "Close"):
        if ohlc_parts[f]:
            comb = pd.concat(ohlc_parts[f], axis=1)
            comb = comb.loc[:, ~comb.columns.duplicated()].sort_index()
            raw_ohlc[f] = comb
        else:
            raw_ohlc[f] = pd.DataFrame()

    master_index = raw_ohlc["Close"].index
    for f in ("Open", "High", "Low", "Close"):
        raw_ohlc[f] = raw_ohlc[f].reindex(index=master_index, columns=unique_list)

    # Identify tickers that returned completely empty in batch mode
    empty_tickers = [
        t for t in unique_list
        if raw_ohlc["Close"][t].dropna().empty
    ]

    rescued_bo = {}
    if empty_tickers:
        if progress_cb is not None:
            progress_cb(0.92, f"Retrying {len(empty_tickers)} missing tickers (including .BO fallback)...")

        for t in empty_tickers:
            # Step A: Single-ticker retry on original .NS symbol
            fetched_df, st_status = _download_single_ticker_with_backoff(t, start_str, end_str)
            if st_status == "rate_limit":
                had_rate_limit = True

            # Step B: If .NS still has no data, retry with .BO (BSE) suffix
            if fetched_df.empty and t.endswith(".NS"):
                bo_sym = t[:-3] + ".BO"
                bo_df, bo_status = _download_single_ticker_with_backoff(bo_sym, start_str, end_str)
                if bo_status == "rate_limit":
                    had_rate_limit = True
                if not bo_df.empty:
                    fetched_df = bo_df
                    rescued_bo[t] = bo_sym

            if not fetched_df.empty:
                fetched_df.index = pd.to_datetime(fetched_df.index).tz_localize(None).normalize()
                fetched_df = fetched_df[~fetched_df.index.duplicated(keep="last")].sort_index()
                union_idx = raw_ohlc["Close"].index.union(fetched_df.index).sort_values()
                for f in ("Open", "High", "Low", "Close"):
                    raw_ohlc[f] = raw_ohlc[f].reindex(index=union_idx)
                    if f in fetched_df.columns:
                        raw_ohlc[f].loc[fetched_df.index, t] = fetched_df[f]

    if progress_cb is not None:
        progress_cb(1.0, "Download complete.")

    return {
        "Open": raw_ohlc["Open"],
        "High": raw_ohlc["High"],
        "Low": raw_ohlc["Low"],
        "Close": raw_ohlc["Close"],
        "rescued_bo": rescued_bo,
        "had_rate_limit": had_rate_limit
    }


# ==============================================================================
# 3. PERSISTENT LOCAL PARQUET CACHE (./data_cache) & PENDING-REFRESH QUEUE
# ==============================================================================
CACHE_DIR = "./data_cache"
META_FILE = os.path.join(CACHE_DIR, "metadata.json")
FIELDS = ("Open", "High", "Low", "Close")


def _ist_now():
    return datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)


def _latest_expected_nse_trading_date():
    """
    Returns the most recent completed weekday trading date in IST.
    Waits until 16:00 IST (4:00 PM IST) on weekdays so incomplete intraday candles
    are never fetched into the EOD cache.
    """
    now_ist = _ist_now()
    candidate = now_ist.date()
    if now_ist.weekday() < 5 and now_ist.hour < 16:
        candidate -= timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate -= timedelta(days=1)
    return candidate


def _write_df_safely(df, field_name):
    """Writes a DataFrame atomically to ./data_cache/{field_name}.parquet (with pickle fallback)."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    pq_path = os.path.join(CACHE_DIR, f"{field_name}.parquet")
    tmp_pq = pq_path + ".tmp"
    try:
        df.to_parquet(tmp_pq)
        os.replace(tmp_pq, pq_path)
        return "parquet"
    except Exception:
        if os.path.exists(tmp_pq):
            try:
                os.remove(tmp_pq)
            except OSError:
                pass
        pkl_path = os.path.join(CACHE_DIR, f"{field_name}.pkl")
        tmp_pkl = pkl_path + ".tmp"
        df.to_pickle(tmp_pkl)
        os.replace(tmp_pkl, pkl_path)
        return "pickle"


def _read_df_safely(field_name):
    pq_path = os.path.join(CACHE_DIR, f"{field_name}.parquet")
    pkl_path = os.path.join(CACHE_DIR, f"{field_name}.pkl")
    if os.path.exists(pq_path):
        df = pd.read_parquet(pq_path)
    elif os.path.exists(pkl_path):
        df = pd.read_pickle(pkl_path)
    else:
        return None
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    return df[~df.index.duplicated(keep="last")].sort_index()


def load_disk_cache():
    """Loads OHLC Parquet files and metadata.json from ./data_cache if present and valid."""
    if not os.path.exists(META_FILE):
        return None, None
    try:
        with open(META_FILE, "r", encoding="utf-8") as f:
            meta = json.load(f)
        ohlc = {}
        for field in FIELDS:
            df = _read_df_safely(field)
            if df is None or df.empty:
                return None, None
            ohlc[field] = df
        meta.setdefault("pending_refresh", [])
        meta.setdefault("rescued_bo", {})
        return ohlc, meta
    except Exception:
        return None, None


def save_disk_cache(
    ohlc_dict,
    rescued_bo_map,
    pending_refresh_list=None,
    stamp_last_checked=True,
    prev_meta=None
):
    """
    Atomically persists Open, High, Low, Close DataFrames and metadata.json to ./data_cache.
    - Saves meta["pending_refresh"].
    - Only stamps last_checked when stamp_last_checked=True (never on rate-limited or failed updates).
    """
    if ohlc_dict is None or ohlc_dict["Close"].dropna(how="all").empty:
        return None
    os.makedirs(CACHE_DIR, exist_ok=True)
    storage_fmt = "parquet"
    for field in FIELDS:
        storage_fmt = _write_df_safely(ohlc_dict[field], field)

    valid_close = ohlc_dict["Close"].dropna(how="all")
    last_trade_dt = str(valid_close.index.max().date())
    first_trade_dt = str(valid_close.index.min().date())
    now_ist = _ist_now()
    now_str = now_ist.strftime("%Y-%m-%d %H:%M:%S IST")

    pending_clean = sorted(set(pending_refresh_list or []))
    prev_checked = (prev_meta or {}).get("last_checked", None)
    last_checked_val = str(now_ist.date()) if stamp_last_checked else prev_checked

    meta = {
        "last_updated": now_str,
        "last_checked": last_checked_val,
        "last_trading_date": last_trade_dt,
        "first_trading_date": first_trade_dt,
        "storage_format": storage_fmt,
        "ticker_count": int(ohlc_dict["Close"].shape[1]),
        "rescued_bo": rescued_bo_map or {},
        "pending_refresh": pending_clean
    }
    tmp_meta = META_FILE + ".tmp"
    with open(tmp_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    os.replace(tmp_meta, META_FILE)
    return meta


def sync_local_cache(unique_tickers, mode="auto"):
    """
    Manages the ./data_cache lifecycle:
    - Uses expected_latest (4:00 PM IST EOD cutoff) as the end date so pressing "Update data now"
      before 4:00 PM IST never saves a half-finished intraday candle.
    - Protects "Full rebuild" with a 90% coverage check so a rate-limited partial rebuild
      never overwrites an existing complete cache.
    - Handles pending_refresh tickers first at the start of every update (capped at MAX_REFRESH_PER_RUN = 150).
    - Only appends incremental rows for a split-flagged ticker if its 15Y refresh succeeded.
    - Never stamps last_checked if a fetch failed, returned empty, or hit a rate limit.
    """
    expected_latest = _latest_expected_nse_trading_date()
    start_15y = expected_latest - timedelta(days=365 * 15 + 10)

    cached_ohlc, meta = load_disk_cache()

    # 1. FULL 15-YEAR REBUILD (or initial first-time build)
    if cached_ohlc is None or meta is None or mode == "rebuild":
        prog = st.sidebar.progress(0.0, text="Building 15-year local Parquet cache (chunks of 45)...")
        fresh = fetch_prices(
            unique_tickers,
            start=start_15y,
            end=expected_latest,
            progress_cb=lambda p, msg: prog.progress(min(max(p, 0.0), 1.0), text=msg)
        )
        prog.empty()
        if fresh is None or fresh["Close"].dropna(how="all").empty:
            if cached_ohlc is not None:
                st.sidebar.error("Full rebuild failed; kept existing valid local cache intact.")
                return cached_ohlc, meta
            st.error("Initial market data download failed. Please check internet connection and retry.")
            return None, None

        if cached_ohlc is not None and mode == "rebuild":
            got = int(fresh["Close"].notna().any().sum())
            if got < 0.9 * len(unique_tickers):
                st.sidebar.error(
                    f"Rebuild only got {got}/{len(unique_tickers)} tickers (likely rate-limited). "
                    "Kept your existing cache."
                )
                return cached_ohlc, meta

        new_meta = save_disk_cache(
            fresh,
            fresh.get("rescued_bo", {}),
            pending_refresh_list=[],
            stamp_last_checked=not fresh.get("had_rate_limit", False),
            prev_meta=meta
        )
        return fresh, new_meta

    rescued_bo = dict(meta.get("rescued_bo", {}))
    pending_refresh = list(dict.fromkeys(meta.get("pending_refresh", [])))
    updated_any = False
    had_rate_limit_any = False

    # 2. CHECK FOR NEWLY ADDED SIDEBAR TICKERS NOT YET IN DISK CACHE
    cached_cols = set(cached_ohlc["Close"].columns)
    new_tickers = [t for t in unique_tickers if t not in cached_cols]
    if new_tickers:
        prog_new = st.sidebar.progress(0.0, text=f"Fetching 15Y history for {len(new_tickers)} newly added ticker(s)...")
        new_bundle = fetch_prices(
            new_tickers,
            start=start_15y,
            end=expected_latest,
            progress_cb=lambda p, msg: prog_new.progress(min(max(p, 0.0), 1.0), text=msg)
        )
        prog_new.empty()
        if new_bundle is not None:
            if new_bundle.get("had_rate_limit"):
                had_rate_limit_any = True
            if not new_bundle["Close"].dropna(how="all").empty:
                union_idx = cached_ohlc["Close"].index.union(new_bundle["Close"].index).sort_values()
                for field in FIELDS:
                    cached_ohlc[field] = cached_ohlc[field].reindex(index=union_idx)
                    for t in new_tickers:
                        if t in new_bundle[field].columns:
                            cached_ohlc[field][t] = new_bundle[field][t]
                rescued_bo.update(new_bundle.get("rescued_bo", {}))
                updated_any = True

    # 3. DETERMINE IF UPDATE / PENDING-REFRESH RETRY SHOULD RUN
    last_cached_dt = pd.Timestamp(meta["last_trading_date"]).date()
    last_checked_str = meta.get("last_checked")
    already_checked_for_cycle = (last_checked_str == str(_ist_now().date())) and (last_cached_dt >= expected_latest)

    needs_update = (
        (mode == "incremental")
        or (last_cached_dt < expected_latest and not already_checked_for_cycle)
        or (len(pending_refresh) > 0 and not already_checked_for_cycle)
    )

    inc_got_data = False
    if needs_update:
        inc_start = last_cached_dt - timedelta(days=5)
        prog_inc = st.sidebar.progress(
            0.0,
            text=f"Incremental update: fetching {inc_start} → {expected_latest}..."
        )
        inc_bundle = fetch_prices(
            unique_tickers,
            start=inc_start,
            end=expected_latest,
            progress_cb=lambda p, msg: prog_inc.progress(min(max(p, 0.0), 1.0), text=msg)
        )
        prog_inc.empty()

        if inc_bundle is not None:
            if inc_bundle.get("had_rate_limit"):
                had_rate_limit_any = True

            if not inc_bundle["Close"].dropna(how="all").empty:
                inc_got_data = True
                # Detect newly split/bonus-adjusted tickers on the overlap seam (>1.5% difference)
                overlap_dates = cached_ohlc["Close"].index.intersection(inc_bundle["Close"].index)
                newly_flagged = []
                if len(overlap_dates) > 0:
                    check_dt = overlap_dates[-1]
                    old_row = cached_ohlc["Close"].loc[check_dt]
                    new_row = inc_bundle["Close"].loc[check_dt]
                    common_t = old_row.dropna().index.intersection(new_row.dropna().index)
                    for t in common_t:
                        if old_row[t] > 0 and abs(new_row[t] - old_row[t]) / old_row[t] > 0.015:
                            newly_flagged.append(t)

                # Queue order: existing pending_refresh FIRST, then newly_flagged
                combined_refresh_queue = list(dict.fromkeys(pending_refresh + newly_flagged))
                flagged_set = set(combined_refresh_queue)

                to_refresh_now = combined_refresh_queue[:MAX_REFRESH_PER_RUN]
                overflow_pending = combined_refresh_queue[MAX_REFRESH_PER_RUN:]

                refreshed_ok = set()
                failed_refresh = list(overflow_pending)

                if to_refresh_now:
                    prog_ref = st.sidebar.progress(
                        0.0,
                        text=f"Refreshing full 15Y history for {len(to_refresh_now)} split/pending ticker(s)..."
                    )
                    adj_bundle = fetch_prices(
                        to_refresh_now,
                        start=start_15y,
                        end=expected_latest,
                        progress_cb=lambda p, msg: prog_ref.progress(min(max(p, 0.0), 1.0), text=msg)
                    )
                    prog_ref.empty()

                    if adj_bundle is not None:
                        if adj_bundle.get("had_rate_limit"):
                            had_rate_limit_any = True
                        rescued_bo.update(adj_bundle.get("rescued_bo", {}))
                        union_idx = cached_ohlc["Close"].index.union(adj_bundle["Close"].index).sort_values()
                        for field in FIELDS:
                            cached_ohlc[field] = cached_ohlc[field].reindex(index=union_idx)

                        for t in to_refresh_now:
                            if (
                                t in adj_bundle["Close"].columns
                                and not adj_bundle["Close"][t].dropna().empty
                            ):
                                for field in FIELDS:
                                    cached_ohlc[field][t] = adj_bundle[field][t]
                                refreshed_ok.add(t)
                            else:
                                failed_refresh.append(t)
                    else:
                        failed_refresh.extend(to_refresh_now)

                # Only append incremental rows for a flagged ticker if its full-history refresh succeeded!
                skip_append_tickers = flagged_set - refreshed_ok
                allowed_inc_tickers = [
                    t for t in inc_bundle["Close"].columns if t not in skip_append_tickers
                ]

                if allowed_inc_tickers:
                    union_idx = cached_ohlc["Close"].index.union(inc_bundle["Close"].index).sort_values()
                    for field in FIELDS:
                        cached_ohlc[field] = cached_ohlc[field].reindex(index=union_idx)
                        inc_sub = inc_bundle[field][allowed_inc_tickers]
                        comb_sub = pd.concat(
                            [cached_ohlc[field][allowed_inc_tickers], inc_sub], axis=0
                        )
                        comb_sub = comb_sub[~comb_sub.index.duplicated(keep="last")].reindex(index=union_idx)
                        cached_ohlc[field][allowed_inc_tickers] = comb_sub

                rescued_bo.update(inc_bundle.get("rescued_bo", {}))
                pending_refresh = list(dict.fromkeys(failed_refresh))
                updated_any = True

    if updated_any or needs_update:
        # Only stamp last_checked if incremental fetch succeeded with data, no rate-limit occurred, and pending_refresh is empty
        should_stamp_checked = (
            inc_got_data
            and (not had_rate_limit_any)
            and (len(pending_refresh) == 0)
        )
        meta = save_disk_cache(
            cached_ohlc,
            rescued_bo,
            pending_refresh_list=pending_refresh,
            stamp_last_checked=should_stamp_checked,
            prev_meta=meta
        ) or meta

    if meta and len(meta.get("pending_refresh", [])) > 0:
        n_pend = len(meta["pending_refresh"])
        st.sidebar.warning(
            f"{n_pend} tickers are waiting for a history refresh; they will be retried on the next update."
        )

    return cached_ohlc, meta


# ==============================================================================
# 4. DATA HEALTH AUDIT, CORPORATE ACTION (>40% MOVE) CHECK & CLEANING
# ==============================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def prepare_cleaned_universe_and_health(
    _raw_ohlc,
    unique_tickers_tuple,
    ticker_to_sectors_json,
    rescued_bo_json,
    pending_refresh_json,
    cache_timestamp
):
    """
    Runs on the raw cached OHLC frames BEFORE forward-filling:
    1. Flags any single-day move > 40% as a possible unadjusted split/bonus anomaly.
    2. Classifies every unique ticker as OK, Rescued (.BO), Pending Split Refresh,
       Stale (>5D), Too Short (<60D), or Missing.
    3. Forward-fills short holiday gaps (limit=5) ONLY up to each stock's last valid date.
    """
    ticker_to_sectors = json.loads(ticker_to_sectors_json)
    rescued_bo = json.loads(rescued_bo_json)
    pending_set = set(json.loads(pending_refresh_json))

    raw_close = _raw_ohlc["Close"].dropna(how="all")
    market_last_date = raw_close.index.max()

    failed_missing = []
    failed_stale = []
    last_valid_dates = {}
    health_rows = []
    corp_action_anomalies = []

    for t in unique_tickers_tuple:
        sectors_str = ", ".join(ticker_to_sectors.get(t, []))
        src_sym = rescued_bo.get(t, t)

        if t not in raw_close.columns or raw_close[t].dropna().empty:
            failed_missing.append(t)
            health_rows.append({
                "Ticker": t,
                "Source Symbol": "None (.NS & .BO failed)",
                "Sector(s)": sectors_str,
                "Status": "Missing",
                "First Valid Date": "—",
                "Last Valid Date": "—",
                "Trading Days": 0,
                "Max 1D Move (%)": np.nan,
                "Corporate Action Check": "—",
                "Included in Index": "No (Excluded)"
            })
            continue

        valid_s = raw_close[t].dropna()
        first_dt = valid_s.index.min()
        last_dt = valid_s.index.max()
        last_valid_dates[t] = last_dt
        n_days = len(valid_s)
        lag_days = (market_last_date - last_dt).days

        pct_s = valid_s.pct_change().dropna()
        max_abs_move = float(pct_s.abs().max() * 100.0) if not pct_s.empty else 0.0
        extreme_moves = pct_s[pct_s.abs() > 0.40]

        if not extreme_moves.empty:
            worst_dt = extreme_moves.abs().idxmax()
            worst_val = float(extreme_moves.loc[worst_dt] * 100.0)
            ca_flag = f"⚠️ {worst_val:+.1f}% on {str(worst_dt.date())}"
            corp_action_anomalies.append({
                "Ticker": t,
                "Sector(s)": sectors_str,
                "Anomaly Date": str(worst_dt.date()),
                "1-Day Move (%)": round(worst_val, 2),
                "Events >40%": len(extreme_moves)
            })
        else:
            ca_flag = "Clean"

        if lag_days > 5:
            status = "Pending Refresh" if t in pending_set else "Stale (>5D)"
            included = "No (Excluded)"
            failed_stale.append(f"{t} (last trade: {str(last_dt.date())})")
        elif t in pending_set:
            status = "Pending Split Refresh"
            included = "Yes (Pre-Split Cached)"
        elif n_days < 60:
            status = "Too Short (<60D)" if t not in rescued_bo else "Rescued (.BO) / <60D"
            included = "Yes"
        elif t in rescued_bo:
            status = "Rescued (.BO)"
            included = "Yes"
        else:
            status = "OK"
            included = "Yes"

        health_rows.append({
            "Ticker": t,
            "Source Symbol": src_sym,
            "Sector(s)": sectors_str,
            "Status": status,
            "First Valid Date": str(first_dt.date()),
            "Last Valid Date": str(last_dt.date()),
            "Trading Days": n_days,
            "Max 1D Move (%)": round(max_abs_move, 2),
            "Corporate Action Check": ca_flag,
            "Included in Index": included
        })

    cleaned_close = _raw_ohlc["Close"].copy()
    for t, last_dt in last_valid_dates.items():
        if t in cleaned_close.columns:
            cleaned_close.loc[:last_dt, t] = cleaned_close.loc[:last_dt, t].ffill(limit=5)

    cleaned_ohlc = {"Close": cleaned_close}
    for f in ("Open", "High", "Low"):
        df_f = _raw_ohlc[f].copy()
        cleaned_ohlc[f] = df_f.fillna(cleaned_close)

    cleaned_ohlc["failed_missing"] = failed_missing
    cleaned_ohlc["failed_stale"] = failed_stale
    cleaned_ohlc["market_last_date"] = market_last_date
    cleaned_ohlc["health_df"] = pd.DataFrame(health_rows)
    cleaned_ohlc["anomalies_df"] = pd.DataFrame(corp_action_anomalies)
    return cleaned_ohlc


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_benchmark_series(period="15y"):
    """Fetches official benchmark and returns (Series, Accurate_Label)."""
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
    return pd.Series(dtype=float), "Benchmark Unavailable"


# ==============================================================================
# 5. UNIFIED QUARTERLY EQUAL-WEIGHT OHLC ENGINE (PRECOMPUTED & CACHED ONCE)
# ==============================================================================
def compute_equal_weight_index(tickers, ohlc_bundle, base_val=1000.0, exclude_stale=True):
    """
    Computes genuine quarterly-rebalanced Open, High, Low, Close candlesticks.
    Rebalances notional shares against the previous quarter's final closing prices
    so Day 1 of each new quarter preserves 100% of its overnight & intraday return.
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
        t for t in dict.fromkeys(tickers)
        if t in close_all.columns
        and t not in missing_set
        and t not in stale_set
        and not close_all[t].dropna().empty
    ]
    if not valid_tickers:
        valid_tickers = [
            t for t in dict.fromkeys(tickers)
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
    prev_q_last_close = None

    for q in unique_q:
        q_mask = (quarter_labels == q)
        dates = c_df.index[q_mask]
        if len(dates) == 0:
            continue

        q_c_window = c_df.loc[dates].ffill().bfill(limit=2)
        if prev_q_last_close is not None:
            ref_prices = prev_q_last_close.reindex(valid_tickers).fillna(q_c_window.iloc[0]).dropna()
        else:
            ref_prices = q_c_window.iloc[0].dropna()

        active = [t for t in ref_prices.index if not c_df.loc[dates, t].dropna().empty]
        if len(active) == 0:
            continue

        ref_prices = ref_prices.loc[active]
        q_c_sub = c_df.loc[dates, active].ffill().bfill(limit=2)
        q_o_sub = o_df.loc[dates, active].fillna(q_c_sub)
        q_h_sub = h_df.loc[dates, active].fillna(q_c_sub)
        q_l_sub = l_df.loc[dates, active].fillna(q_c_sub)

        pts_per_stock = current_val / len(active)
        notional_shares = pts_per_stock / ref_prices

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
        prev_q_last_close = q_c_sub.iloc[-1]

    index_df = pd.DataFrame(records).set_index("Date")
    index_df = index_df[~index_df.index.duplicated(keep="last")]
    return index_df, valid_tickers


@st.cache_data(ttl=3600, show_spinner=False)
def precompute_all_sector_indices(_ohlc_bundle, sectors_json, cache_timestamp, base_val=1000.0):
    """
    Precomputes all sector OHLC indices ONCE after loading, keyed by the cache's
    last-updated timestamp (`cache_timestamp`), and reuses them across all four tabs.
    """
    sectors_dict = json.loads(sectors_json)
    sector_indices = {}
    sector_valid_lists = {}
    for sec_name, tickers in sectors_dict.items():
        idx_df, valid_list = compute_equal_weight_index(tickers, _ohlc_bundle, base_val=base_val)
        sector_indices[sec_name] = idx_df
        sector_valid_lists[sec_name] = valid_list
    return sector_indices, sector_valid_lists


# ==============================================================================
# 6. QUANTITATIVE TREND, MOMENTUM & BREADTH FORMULAS (UNCHANGED RESULTS)
# ==============================================================================
WINDOW_DAYS_MAP = {
    "1 Week (5D)": 7,
    "2 Weeks (10D)": 14,
    "4 Weeks (1M)": 30,
    "3 Months (63D)": 91,
    "6 Months (126D)": 182,
    "1 Year (252D)": 365
}


def _resample_month_end(df):
    try:
        return df.resample("ME")
    except ValueError:
        return df.resample("M")


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
    ret_p = df_metrics[ret_col].rank(pct=True)
    r2_p = df_metrics[r2_col].rank(pct=True)
    ker_p = df_metrics[ker_col].rank(pct=True)
    upward_mult = np.where(df_metrics[ret_col] > 0, 1.0, 0.30)
    return np.round((0.45 * ret_p + 0.30 * r2_p + 0.25 * ker_p) * upward_mult * 100.0, 1)


def show_data_health(bundle, tickers=None, key_suffix="global"):
    """Displays missing/stale summary, >40% corporate action flags, and full CSV download."""
    if not bundle:
        return
    miss = bundle.get("failed_missing", [])
    stale = bundle.get("failed_stale", [])
    health_df = bundle.get("health_df", pd.DataFrame())
    anomalies_df = bundle.get("anomalies_df", pd.DataFrame())

    if tickers is not None:
        s = set(tickers)
        miss = [t for t in miss if t in s]
        stale = [x for x in stale if x.split(" ")[0] in s]
        if not health_df.empty:
            health_df = health_df[health_df["Ticker"].isin(s)]
        if not anomalies_df.empty:
            anomalies_df = anomalies_df[anomalies_df["Ticker"].isin(s)]

    rescued_cnt = int((health_df["Status"].str.contains("Rescued", na=False)).sum()) if not health_df.empty else 0
    anom_cnt = len(anomalies_df)

    if miss or stale or rescued_cnt > 0 or anom_cnt > 0:
        with st.expander(
            f"🩺 Data Health & Corporate Action Audit — "
            f"{len(miss)} Missing | {len(stale)} Stale (>5D) | "
            f"{rescued_cnt} Rescued (.BO) | {anom_cnt} Moves >40%"
        ):
            if miss:
                st.write("**Missing (No .NS or .BO data):**", ", ".join(miss))
            if stale:
                st.write("**Stale / Suspended (>5 Days Behind Market — Excluded from Index):**", ", ".join(stale))
            if not anomalies_df.empty:
                st.markdown("**⚠️ Single-Day Moves > 40% (Potential Unadjusted Split/Bonus or Outlier):**")
                st.dataframe(anomalies_df, use_container_width=True, hide_index=True)
            if not health_df.empty:
                st.markdown("**Complete Ticker-Level Health Table:**")
                st.dataframe(health_df, use_container_width=True, hide_index=True)
                csv_bytes = health_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Data Health Table (CSV)",
                    data=csv_bytes,
                    file_name=f"nse_data_health_{key_suffix}.csv",
                    mime="text/csv",
                    key=f"dl_health_{key_suffix}"
                )


# ==============================================================================
# 7. SIDEBAR: CACHE MANAGEMENT, UNIVERSE OVERLAPS & SECTOR CONTROLS
# ==============================================================================
st.sidebar.header("💾 Local Parquet Cache")

col_btn1, col_btn2 = st.sidebar.columns(2)
trigger_incremental = col_btn1.button("🔄 Update data now", use_container_width=True)
trigger_rebuild = col_btn2.button("🧱 Full rebuild", use_container_width=True)

sync_mode = "rebuild" if trigger_rebuild else ("incremental" if trigger_incremental else "auto")
if trigger_rebuild or trigger_incremental:
    st.cache_data.clear()

raw_disk_ohlc, cache_meta = sync_local_cache(UNIQUE_TICKERS, mode=sync_mode)

if raw_disk_ohlc is None or cache_meta is None:
    st.stop()

st.sidebar.caption(
    f"**Last updated:** {cache_meta.get('last_updated', 'Unknown')}  \n"
    f"**Last checked:** {cache_meta.get('last_checked') or 'Pending retry'}  \n"
    f"**Latest trading date:** {cache_meta.get('last_trading_date', 'Unknown')}  \n"
    f"**Cached unique tickers:** {cache_meta.get('ticker_count', 0)} ({cache_meta.get('storage_format', 'parquet')})"
)

with st.sidebar.expander(f"🔗 Multi-Sector Stocks ({len(DUPLICATE_TICKERS)} Overlap Tickers)"):
    st.caption("Downloaded once in the master cache, included in each assigned sector index:")
    dup_rows = [
        {"Ticker": t, "# Sectors": len(secs), "Assigned Sectors": " | ".join(secs)}
        for t, secs in DUPLICATE_TICKERS.items()
    ]
    st.dataframe(pd.DataFrame(dup_rows), use_container_width=True, hide_index=True)

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
                st.session_state.sectors[new_sec_name] = list(dict.fromkeys(parsed_tickers))
                st.cache_data.clear()
                st.success(f"Created '{new_sec_name}' with {len(parsed_tickers)} stocks!")
                st.rerun()

current_constituents = st.session_state.sectors[selected_sector]
selected_stocks = st.sidebar.multiselect(
    "Constituents (Toggle Stocks)",
    options=current_constituents,
    default=current_constituents
)

with st.sidebar.expander(f"➕ Add Stock to '{selected_sector}'"):
    new_stock_input = st.text_input("Enter NSE Ticker (e.g. KMEW)").strip()
    if st.button("Add to Current Sector"):
        if new_stock_input:
            fmt = format_nse_ticker(new_stock_input)
            if fmt and fmt not in current_constituents:
                st.session_state.sectors[selected_sector].append(fmt)
                st.cache_data.clear()
                st.rerun()

base_val = st.sidebar.number_input("Starting Base Value", 100.0, 50000.0, 1000.0, 100.0)


# ==============================================================================
# 8. PRECOMPUTE CLEANED UNIVERSE & ALL 27 SECTOR INDICES ONCE
# ==============================================================================
cache_ts_key = (
    f"{cache_meta.get('last_updated', '')}_"
    f"{cache_meta.get('ticker_count', 0)}_"
    f"{len(cache_meta.get('pending_refresh', []))}"
)

master_ohlc = prepare_cleaned_universe_and_health(
    raw_disk_ohlc,
    tuple(UNIQUE_TICKERS),
    json.dumps(TICKER_TO_SECTORS, sort_keys=True),
    json.dumps(cache_meta.get("rescued_bo", {}), sort_keys=True),
    json.dumps(cache_meta.get("pending_refresh", []), sort_keys=True),
    cache_ts_key
)

PRECOMPUTED_INDICES, PRECOMPUTED_VALID_LISTS = precompute_all_sector_indices(
    master_ohlc,
    json.dumps(st.session_state.sectors, sort_keys=True),
    cache_ts_key,
    base_val=float(base_val)
)

show_data_health(master_ohlc, tickers=None, key_suffix="full_universe")


# ==============================================================================
# 9. TOP-LEVEL DASHBOARD NAVIGATION TABS
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
        if set(selected_stocks) == set(current_constituents) and selected_sector in PRECOMPUTED_INDICES:
            index_df = PRECOMPUTED_INDICES[selected_sector]
            valid_15y = PRECOMPUTED_VALID_LISTS[selected_sector]
        else:
            index_df, valid_15y = compute_equal_weight_index(
                selected_stocks, master_ohlc, base_val=float(base_val)
            )

        if index_df.empty:
            st.error("No valid market data returned for the selected constituents.")
        else:
            show_data_health(master_ohlc, selected_stocks, key_suffix="tab1_sector")

            s_val = index_df["Close"].iloc[0]
            e_val = index_df["Close"].iloc[-1]
            tot_ret = ((e_val - s_val) / s_val) * 100.0
            pk = index_df["Close"].cummax()
            dd = (index_df["Close"] - pk) / pk
            m_dd = dd.min() * 100.0

            pct_20, pct_50, pct_200 = calc_ma_breadth(master_ohlc["Close"], valid_15y)

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
                    bench_s, bench_label = fetch_benchmark_series(period="15y")
                    common_idx = c_data.index.intersection(bench_s.index)

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
                m_data = _resample_month_end(index_df).agg({
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
                close_15y = master_ohlc["Close"]
                for t in valid_15y:
                    s_t = close_15y[t].dropna()
                    if not s_t.empty:
                        ma50 = s_t.iloc[-50:].mean() if len(s_t) >= 50 else np.nan
                        ma200 = s_t.iloc[-200:].mean() if len(s_t) >= 200 else np.nan
                        rows.append({
                            "Ticker": t,
                            "Sectors Count": len(TICKER_TO_SECTORS.get(t, [selected_sector])),
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
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ==============================================================================
# TAB 2: MULTI-SECTOR COMPARISON & RELATIVE STRENGTH VS BENCHMARK
# ==============================================================================
with main_tab2:
    st.subheader("📈 Multi-Sector Relative Performance & RS Ratio vs Benchmark")
    st.caption(
        "Reuses precomputed 15-year sector curves from the local Parquet cache. "
        "Switch between Normalized Price Performance and Relative Strength (Sector / Benchmark)."
    )

    col_m1, col_m2, col_m3 = st.columns([3, 1, 1])
    with col_m1:
        comp_sectors = st.multiselect(
            "Select Sectors to Compare:",
            options=list(st.session_state.sectors.keys()),
            default=[
                "1. Banking (PSU, Private & SFBs)",
                "2. Information Technology & Software",
                "3. Automobile (OEMs, 2W, 4W, CVs & EVs)",
                "5. Pharmaceuticals & Formulations",
                "27. Nifty Jewellery & Watches Equal-Weight"
            ]
        )
    with col_m2:
        lookback_choice = st.selectbox(
            "Lookback Window:",
            list(WINDOW_DAYS_MAP.keys()) + ["2 Years (504D)", "5 Years", "15 Years"],
            index=5
        )
    with col_m3:
        chart_mode = st.radio(
            "Chart Mode:",
            ["Normalized Return (Base=100)", "Relative Strength (RS vs Benchmark)"]
        )

    extra_days = {"2 Years (504D)": 730, "5 Years": 1825, "15 Years": 5500}
    days = WINDOW_DAYS_MAP.get(lookback_choice, extra_days.get(lookback_choice, 365))

    if comp_sectors:
        bench_series, bench_true_label = fetch_benchmark_series(period="15y")
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
            sec_ohlc_df = PRECOMPUTED_INDICES.get(sec, pd.DataFrame())
            valid_list = PRECOMPUTED_VALID_LISTS.get(sec, [])
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
    st.subheader("🧠 Full-Universe Sector Momentum, Breadth & Weekly Rank History")
    st.caption(
        "Instantaneous rankings computed from precomputed sector indices and local Parquet cache. "
        "Select primary and comparison baseline windows to track momentum acceleration."
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

    sectors_scope = st.multiselect(
        "Sectors to Include in Leaderboard:",
        options=list(st.session_state.sectors.keys()),
        default=list(st.session_state.sectors.keys())
    )

    if sectors_scope:
        leaderboard_rows = []
        sector_curves = {}
        close_mat = master_ohlc["Close"]

        for sec_name in sectors_scope:
            sec_ohlc_df = PRECOMPUTED_INDICES.get(sec_name, pd.DataFrame())
            valid_list = PRECOMPUTED_VALID_LISTS.get(sec_name, [])
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
            for t in valid_list:
                if t in close_mat.columns:
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

            # Weekly Sector Rank History (Bump Chart)
            st.markdown("### 📊 Weekly Sector Momentum Rank History (Last 16 Weeks)")
            curves_df = pd.DataFrame(sector_curves).sort_index().ffill()
            weekly_closes = curves_df.resample("W-FRI").last().dropna(how="all")

            if len(weekly_closes) >= 6:
                rolling_4w_ret = weekly_closes.pct_change(4).dropna(how="all") * 100.0
                recent_weeks = rolling_4w_ret.tail(16)
                weekly_ranks = recent_weeks.rank(axis=1, ascending=False, method="min")

                default_rank_secs = list(df_lead["Sector"].head(6))
                rank_sectors_sel = st.multiselect(
                    "Select Sectors to Trace on Rank History Chart:",
                    options=list(sector_curves.keys()),
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
# TAB 4: STOCK ATTRIBUTION & DRIVER DEEP-DIVE
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
    sec_ohlc_df = PRECOMPUTED_INDICES.get(att_sector, pd.DataFrame())
    valid_stocks = PRECOMPUTED_VALID_LISTS.get(att_sector, [])

    if not sec_ohlc_df.empty and valid_stocks:
        show_data_health(master_ohlc, stk_constituents, key_suffix="tab4_sector")
        idx_slice = slice_by_window(sec_ohlc_df["Close"], att_window)
        sec_tot_ret = ((idx_slice.iloc[-1] - idx_slice.iloc[0]) / idx_slice.iloc[0]) * 100.0 if len(idx_slice) >= 2 else 0.0

        close_mat = master_ohlc["Close"]
        pct_20, pct_50, pct_200 = calc_ma_breadth(close_mat, valid_stocks)

        stock_rows = []
        n_const = len(valid_stocks)

        for t in valid_stocks:
            if t in close_mat.columns:
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
