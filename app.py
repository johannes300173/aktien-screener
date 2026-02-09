import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from tickers import DAX, DOW_JONES, SP500, NIKKEI

# --------------------------------------------------
# App Setup
# --------------------------------------------------
st.set_page_config(page_title="Aktienscreener", layout="wide")
st.title("📈 Aktienscreener – Value, Momentum & Turnaround")

# --------------------------------------------------
# Sidebar – Modus
# --------------------------------------------------
st.sidebar.header("👤 Modus")

mode = st.sidebar.radio(
    "Benutzermodus",
    ["🟢 Anfänger", "🔵 Pro"],
    help="Anfänger = einfache Presets | Pro = volle Kontrolle"
)

# --------------------------------------------------
# Sidebar – Indizes
# --------------------------------------------------
st.sidebar.header("🌍 Indizes")

indices = st.sidebar.multiselect(
    "Welche Märkte?",
    ["DAX", "Dow Jones", "S&P 500", "Nikkei"],
    default=["DAX", "Dow Jones"]
)

ticker_map = {}
if "DAX" in indices:
    ticker_map.update(DAX)
if "Dow Jones" in indices:
    ticker_map.update(DOW_JONES)
if "S&P 500" in indices:
    ticker_map.update(SP500)
if "Nikkei" in indices:
    ticker_map.update(NIKKEI)

# --------------------------------------------------
# Anfänger-Modus
# --------------------------------------------------
if mode == "🟢 Anfänger":

    st.sidebar.header("🧭 Strategie")

    strategy = st.sidebar.selectbox(
        "Anlagestrategie",
        ["⚖️ Ausgewogen", "🚀 Wachstum", "🛡️ Dividende", "🎯 Turnaround"]
    )

    if strategy == "⚖️ Ausgewogen":
        min_perf, min_div, max_pe, min_dist = 0, 1.5, 18, 15
        w_perf, w_dist, w_div, w_pe = 0.4, 0.2, 0.2, 0.2

    elif strategy == "🚀 Wachstum":
        min_perf, min_div, max_pe, min_dist = 5, 0.0, 30, 5
        w_perf, w_dist, w_div, w_pe = 0.7, 0.1, 0.0, 0.2

    elif strategy == "🛡️ Dividende":
        min_perf, min_div, max_pe, min_dist = -2, 3.0, 15, 20
        w_perf, w_dist, w_div, w_pe = 0.2, 0.1, 0.5, 0.2

    elif strategy == "🎯 Turnaround":
        min_perf, min_div, max_pe, min_dist = -5, 0.5, 20, 35
        w_perf, w_dist, w_div, w_pe = 0.2, 0.6, 0.1, 0.1

    use_div = True
    use_dist = True

# --------------------------------------------------
# Pro-Modus
# --------------------------------------------------
else:
    st.sidebar.header("🔍 Filter")

    min_perf = st.sidebar.slider("3W Performance (%)", -10, 20, 2)
    min_div = st.sidebar.slider("Dividende (%)", 0.0, 10.0, 1.5)
    max_pe = st.sidebar.slider("Max. KGV", 5, 40, 18)
    min_dist = st.sidebar.slider("Abstand vom 52W-Hoch (%)", 0, 60, 15)

    use_div = st.sidebar.checkbox("Dividenden-Filter aktiv", True)
    use_dist = st.sidebar.checkbox("52W-Abstand aktiv", True)

    st.sidebar.header("⚖️ Score-Gewichtung")
    w_perf = st.sidebar.slider("Momentum", 0.0, 1.0, 0.4)
    w_dist = st.sidebar.slider("Turnaround", 0.0, 1.0, 0.2)
    w_div = st.sidebar.slider("Dividende", 0.0, 1.0, 0.2)
    w_pe = st.sidebar.slider("Bewertung (KGV)", 0.0, 1.0, 0.2)

# --------------------------------------------------
# Zeitraum
# --------------------------------------------------
end = datetime.today()
start = end - timedelta(days=120)

# --------------------------------------------------
# Screener
# --------------------------------------------------
if st.button("🚀 Screener starten"):

    results = []

    total = after_perf = after_dist = after_pe = after_div = 0

    with st.spinner("📡 Lade Marktdaten..."):
        for ticker, name in ticker_map.items():
            try:
                total += 1

                stock = yf.Ticker(ticker)
                hist = stock.history(start=start, end=end)

                if len(hist) < 30:
                    continue

                price_now = hist["Close"].iloc[-1]
                price_3w = hist["Close"].iloc[-15]

                perf_3w = ((price_now / price_3w) - 1) * 100
                high_52w = hist["High"].max()
                dist_52w = ((price_now / high_52w) - 1) * 100

                info = stock.info
                pe = info.get("trailingPE")
                div = info.get("dividendYield")

                if pe is None or div is None:
                    continue

                if perf_3w < min_perf:
                    continue
                after_perf += 1

                if use_dist and dist_52w > -min_dist:
                    continue
                after_dist += 1

                if pe > max_pe:
                    continue
                after_pe += 1

                if use_div and div * 100 < min_div:
                    continue
                after_div += 1

                score = (
                    perf_3w * w_perf +
                    abs(dist_52w) * w_dist +
                    (div * 100) * w_div +
                    (max_pe - pe) * w_pe
                )

results.append({
    "Ticker": ticker,
    "Name": name,
    "Kurs": round(price_now, 2),
    "3W Perf (%)": round(perf_3w, 2),
    "Abstand 52W (%)": round(dist_52w, 2),
    "Dividende (%)": round(div * 100, 2),
    "KGV": round(pe, 2),
    "Score": round(score, 2),

    "Score Momentum": round(perf_3w * w_perf, 2),
    "Score Turnaround": round(abs(dist_52w) * w_dist, 2),
    "Score Dividende": round((div * 100) * w_div, 2),
    "Score Bewertung": round((max_pe - pe) * w_pe, 2),
})
