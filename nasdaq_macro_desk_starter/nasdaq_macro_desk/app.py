import os
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="NASDAQ Macro Desk",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

BG = "#0b1220"
CARD = "#111b2e"
MUTED = "#93a4bd"
GREEN = "#2dd4a7"
RED = "#ff647c"
AMBER = "#f5bd4f"

st.markdown(
    f"""
    <style>
      .stApp {{ background: {BG}; color: #e8eef8; }}
      [data-testid="stSidebar"] {{ background: #0e1728; }}
      h1,h2,h3 {{ letter-spacing: -0.03em; }}
      .eyebrow {{ color: {MUTED}; text-transform: uppercase; letter-spacing: .14em;
                  font-size: .72rem; font-weight: 700; }}
      .metric-card {{ background: {CARD}; border: 1px solid #26344b; border-radius: 14px;
                      padding: 16px 18px; min-height: 115px; }}
      .metric-label {{ color: {MUTED}; font-size: .82rem; }}
      .metric-value {{ color: #f5f7fb; font-size: 1.7rem; font-weight: 750; margin-top: 6px; }}
      .metric-note {{ color: {MUTED}; font-size: .76rem; margin-top: 4px; }}
      .pill {{ display:inline-block; padding: 5px 10px; border-radius: 999px;
               font-size: .78rem; font-weight: 800; letter-spacing: .04em; }}
      .bull {{ color: {GREEN}; background: rgba(45,212,167,.12); border: 1px solid rgba(45,212,167,.35); }}
      .bear {{ color: {RED}; background: rgba(255,100,124,.12); border: 1px solid rgba(255,100,124,.35); }}
      .neutral {{ color: {AMBER}; background: rgba(245,189,79,.12); border: 1px solid rgba(245,189,79,.35); }}
      .small-muted {{ color: {MUTED}; font-size: .82rem; }}
      div[data-testid="stExpander"] {{ border: 1px solid #26344b; border-radius: 12px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("NASDAQ MACRO DESK")
st.markdown(
    '<div class="eyebrow">Macro research • Nasdaq-100 futures • NQ1! workflow</div>',
    unsafe_allow_html=True,
)
st.caption("Dashboard personale per contestualizzare la macroeconomia e preparare la sessione. Non è un sistema di esecuzione ordini.")

with st.sidebar:
    st.header("Impostazioni")
    refresh = st.button("↻ Aggiorna dati adesso", use_container_width=True)
    st.caption("I dati di mercato provengono da Yahoo Finance e possono essere ritardati o incompleti.")
    st.divider()
    st.subheader("Fonti")
    st.markdown("- Federal Reserve (RSS)\n- BLS (RSS, se disponibile)\n- Yahoo Finance\n- FRED, se configuri una API key gratuita")
    st.caption("Ultimo caricamento: " + datetime.now().astimezone().strftime("%d/%m/%Y %H:%M %Z"))

if refresh:
    st.cache_data.clear()

@st.cache_data(ttl=900, show_spinner=False)
def get_history(symbol, period="3mo", interval="1d"):
    try:
        df = yf.download(symbol, period=period, interval=interval, auto_adjust=True, progress=False)
        if df is None or df.empty:
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=1800, show_spinner=False)
def get_rss(url, limit=8):
    try:
        parsed = feedparser.parse(url)
        items = []
        for entry in parsed.entries[:limit]:
            title = getattr(entry, "title", "Senza titolo")
            link = getattr(entry, "link", "")
            summary = getattr(entry, "summary", "")
            published = getattr(entry, "published", "")
            items.append({"title": title, "link": link, "summary": summary, "published": published})
        return items
    except Exception:
        return []

@st.cache_data(ttl=3600, show_spinner=False)
def get_fred_series(series_id, api_key):
    if not api_key:
        return pd.DataFrame()
    import requests
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 10,
    }
    try:
        response = requests.get(url, params=params, timeout=12)
        response.raise_for_status()
        observations = response.json().get("observations", [])
        rows = [{"date": x["date"], "value": float(x["value"])} for x in observations if x["value"] != "."]
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

def last_close(df):
    if df.empty or "Close" not in df:
        return None
    s = df["Close"].dropna()
    return float(s.iloc[-1]) if len(s) else None

def pct_change(df, periods=1):
    if df.empty or "Close" not in df:
        return None
    s = df["Close"].dropna()
    if len(s) <= periods:
        return None
    return float((s.iloc[-1] / s.iloc[-1-periods] - 1) * 100)

def fmt_num(value, digits=2, suffix=""):
    return "N/D" if value is None or pd.isna(value) else f"{value:,.{digits}f}{suffix}"

def metric_card(label, value, note=""):
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True,
    )

# Main market data
symbols = {
    "Nasdaq futures": "NQ=F",
    "S&P 500 futures": "ES=F",
    "Volatilità (VIX)": "^VIX",
    "Treasury USA 10Y": "^TNX",
    "Dollaro (DXY)": "DX-Y.NYB",
    "Oro": "GC=F",
    "Petrolio WTI": "CL=F",
}
market = {name: get_history(ticker, "3mo", "1d") for name, ticker in symbols.items()}
nq = market["Nasdaq futures"]
nq_last = last_close(nq)
nq_day = pct_change(nq, 1)
nq_week = pct_change(nq, 5)
vix_last = last_close(market["Volatilità (VIX)"])
y10_last = last_close(market["Treasury USA 10Y"])
dxy_day = pct_change(market["Dollaro (DXY)"], 1)
es_day = pct_change(market["S&P 500 futures"], 1)

# A deliberately transparent heuristic, not a predictive model.
score = 0
reasons = []
if nq_day is not None:
    if nq_day > 0.35:
        score += 2; reasons.append(("Prezzo NQ", "Momentum giornaliero positivo", "bull"))
    elif nq_day < -0.35:
        score -= 2; reasons.append(("Prezzo NQ", "Momentum giornaliero negativo", "bear"))
    else:
        reasons.append(("Prezzo NQ", "Movimento giornaliero contenuto", "neutral"))
if vix_last is not None:
    if vix_last < 18:
        score += 1; reasons.append(("Volatilità", "VIX sotto 18: regime relativamente più tranquillo", "bull"))
    elif vix_last >= 25:
        score -= 2; reasons.append(("Volatilità", "VIX elevato: risk-off / volatilità potenzialmente alta", "bear"))
    elif vix_last >= 20:
        score -= 1; reasons.append(("Volatilità", "VIX sopra 20: cautela sul rischio", "bear"))
if y10_last is not None and len(market["Treasury USA 10Y"]) >= 6:
    yield_df = market["Treasury USA 10Y"]["Close"].dropna()
    yield_move = float(yield_df.iloc[-1] - yield_df.iloc[-6])
    if yield_move > 0.12:
        score -= 1; reasons.append(("Treasury 10Y", "Rendimenti in aumento nella settimana: possibile pressione sulle valutazioni growth", "bear"))
    elif yield_move < -0.12:
        score += 1; reasons.append(("Treasury 10Y", "Rendimenti in calo nella settimana: potenziale sollievo per le valutazioni growth", "bull"))
    else:
        reasons.append(("Treasury 10Y", "Variazione settimanale limitata", "neutral"))
if dxy_day is not None:
    if dxy_day > 0.35:
        score -= 1; reasons.append(("Dollaro", "Dollaro in rafforzamento: possibile vento contrario per il risk appetite", "bear"))
    elif dxy_day < -0.35:
        score += 1; reasons.append(("Dollaro", "Dollaro in indebolimento: possibile supporto marginale al risk appetite", "bull"))
if es_day is not None:
    if es_day > 0.35:
        score += 1; reasons.append(("Conferma intermarket", "S&P futures positivi: conferma parziale del tono risk-on", "bull"))
    elif es_day < -0.35:
        score -= 1; reasons.append(("Conferma intermarket", "S&P futures negativi: conferma parziale del tono risk-off", "bear"))

if score >= 2:
    signal, signal_class, stance = "BULLISH", "bull", "Bias rialzista condizionato"
elif score <= -2:
    signal, signal_class, stance = "BEARISH", "bear", "Bias ribassista condizionato"
else:
    signal, signal_class, stance = "NEUTRAL", "neutral", "Nessun vantaggio direzionale netto"

st.markdown("## Market snapshot")
c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("NQ futures · ultimo close", fmt_num(nq_last), f"Giorno: {fmt_num(nq_day, 2, '%')} · Settimana: {fmt_num(nq_week, 2, '%')}")
with c2:
    metric_card("VIX", fmt_num(vix_last), "Indice di volatilità implicita")
with c3:
    metric_card("Treasury USA 10Y", fmt_num(y10_last), "Quotazione indicativa Yahoo Finance")
with c4:
    metric_card("DXY · variazione giornaliera", fmt_num(dxy_day, 2, "%"), "Può non essere disponibile in ogni sessione")

st.markdown("## Signal brief")
badge_text = f'<span class="pill {signal_class}">{signal}</span>'
st.markdown(badge_text, unsafe_allow_html=True)
st.markdown(f"### {stance}")
st.write(
    f"Score euristico: **{score:+d}**. È una lettura trasparente di alcuni indicatori di mercato, "
    "non una previsione certa e non un segnale di ingresso. Non incorpora automaticamente tutte le notizie, "
    "le aspettative già prezzate, i livelli tecnici o la liquidità intraday."
)
if signal == "NEUTRAL":
    st.info("Lettura: attendere conferme. Un bias neutrale non significa che il mercato non si muoverà, ma che questi input non danno una direzione sufficientemente concorde.")
elif signal == "BULLISH":
    st.success("Lettura: il quadro osservato è relativamente favorevole al rischio. Verifica che rendimenti, calendario macro e price action non contraddicano il bias.")
else:
    st.warning("Lettura: il quadro osservato è relativamente difensivo. Controlla possibili rimbalzi, sorprese macro e se il movimento è già ampiamente prezzato.")

with st.expander("Perché è uscito questo bias? — componenti del punteggio", expanded=True):
    if reasons:
        for name, desc, kind in reasons:
            icon = "＋" if kind == "bull" else ("−" if kind == "bear" else "•")
            st.markdown(f"**{icon} {name}:** {desc}")
    else:
        st.write("Dati insufficienti per comporre il punteggio. Controlla la connessione o riprova più tardi.")

st.markdown("## Prezzo e contesto")
if not nq.empty:
    chart_df = nq.tail(60)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=chart_df.index, open=chart_df["Open"], high=chart_df["High"],
        low=chart_df["Low"], close=chart_df["Close"], name="NQ futures"
    ))
    fig.update_layout(
        template="plotly_dark", height=430, margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor=BG, plot_bgcolor=BG, xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1.02, x=0),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Prezzi NQ non disponibili in questo momento. Yahoo Finance può essere temporaneamente irraggiungibile.")

st.markdown("## Deep macro analysis")
st.write(
    "Questa sezione presenta un quadro intermarket osservabile. La causalità non è automatica: "
    "la reazione del Nasdaq dipende dalla sorpresa rispetto al consenso, dal posizionamento e dal regime macro."
)
macro_cols = st.columns(3)
macro_cards = [
    ("Inflazione e Fed", "Dati d'inflazione più caldi del previsto possono spingere in alto i tassi attesi e i rendimenti, penalizzando le valutazioni growth. Un dato più freddo può aiutare, ma solo se non segnala un deterioramento brusco della crescita."),
    ("Treasury e duration", "Il Nasdaq è sensibile al tasso di sconto applicato agli utili futuri. Osserva direzione e velocità dei rendimenti, non solo il livello. Un calo dei rendimenti causato da paura recessiva può non essere bullish per le azioni."),
    ("Crescita e utili", "PMI, ISM, consumi e lavoro aiutano a valutare la tenuta della domanda. Il mercato reagisce alla differenza tra dato effettivo e attese, non al dato isolato."),
    ("Dollaro e condizioni finanziarie", "Un dollaro forte può accompagnare condizioni finanziarie più restrittive. È un indizio di contesto, non una regola di trading autonoma."),
    ("Volatilità e risk appetite", "Un VIX in aumento segnala maggiore domanda di protezione, ma va letto insieme a prezzo, breadth, rendimenti e catalizzatori della giornata."),
    ("Event risk", "Prima di CPI, PCE, NFP e Fed, riduci la fiducia in un bias basato sui dati precedenti. La volatilità può aumentare e gli spread/slippage possono peggiorare."),
]
for i, (title, body) in enumerate(macro_cards):
    with macro_cols[i % 3]:
        st.markdown(f'<div class="metric-card"><b>{title}</b><p class="small-muted">{body}</p></div>', unsafe_allow_html=True)

st.markdown("## News desk")
rss_sources = [
    ("Federal Reserve", "https://www.federalreserve.gov/feeds/press_all.xml"),
    ("BLS — comunicati", "https://www.bls.gov/feed/bls_latest.rss"),
]
news_items = []
for source_name, url in rss_sources:
    for item in get_rss(url, 8):
        item["source"] = source_name
        news_items.append(item)

if news_items:
    def sort_key(item):
        try:
            dt = parsedate_to_datetime(item["published"])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return datetime(1970, 1, 1, tzinfo=timezone.utc)
    news_items.sort(key=sort_key, reverse=True)
    for item in news_items[:12]:
        title = item["title"]
        link = item["link"]
        summary = item["summary"]
        source = item["source"]
        with st.expander(f"{source} · {title}"):
            if link:
                st.markdown(f"[Apri la fonte originale]({link})")
            if summary:
                clean = pd.Series([summary]).str.replace(r"<[^>]+>", " ", regex=True).iloc[0]
                st.write(clean[:900])
            st.caption("Impatto sul Nasdaq: da valutare rispetto al consenso, alle aspettative già prezzate e alla reazione dei Treasury.")
else:
    st.info("Feed RSS non disponibili al momento. Apri le fonti ufficiali dalla sezione Fonti o riprova più tardi.")

st.markdown("## FRED — indicatori macro ufficiali (opzionale)")
fred_key = st.secrets.get("FRED_API_KEY", os.getenv("FRED_API_KEY", ""))
if not fred_key:
    st.info("Per aggiungere dati macro storici ufficiali, configura gratuitamente una API key FRED come FRED_API_KEY. La dashboard funziona anche senza.")
else:
    fred_series = [
        ("CPIAUCSL", "CPI USA (indice prezzi al consumo)"),
        ("PCEPI", "PCE Price Index"),
        ("UNRATE", "Tasso di disoccupazione"),
        ("DGS10", "Treasury 10Y (%)"),
        ("FEDFUNDS", "Federal Funds Rate (%)"),
    ]
    cols = st.columns(2)
    for i, (series_id, label) in enumerate(fred_series):
        data = get_fred_series(series_id, fred_key)
        with cols[i % 2]:
            st.markdown(f"**{label}** · `{series_id}`")
            if not data.empty:
                data["date"] = pd.to_datetime(data["date"])
                data = data.sort_values("date")
                st.line_chart(data.set_index("date")["value"], height=150)
                st.caption(f"Ultima osservazione: {data.iloc[-1]['date'].date()} · {data.iloc[-1]['value']}")
            else:
                st.caption("Dato non disponibile.")

st.markdown("## Checklist prima di operare")
checklist = [
    "Ho verificato il calendario macro ufficiale e gli orari in fuso italiano.",
    "Ho controllato il consenso e il dato effettivo, non solo il titolo della notizia.",
    "Ho confrontato la reazione di NQ con Treasury 2Y/10Y, DXY e VIX.",
    "Ho definito un livello di invalidazione dello scenario e il rischio massimo del trade.",
    "Non sto usando il bias macro come sostituto di un piano di ingresso, stop e dimensionamento.",
]
for item in checklist:
    st.checkbox(item, key="check_" + str(checklist.index(item)))

st.divider()
st.caption(
    "Nota: progetto educativo e informativo. Il punteggio è una regola euristica dimostrativa, non un modello validato. "
    "I dati gratuiti possono essere ritardati, mancanti o soggetti a termini d'uso. Verifica sempre le informazioni sulle fonti originali."
)
