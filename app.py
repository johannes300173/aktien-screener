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
# SIDEBAR – FORM (alles wird erst beim Start gesetzt!)
# --------------------------------------------------
with st.sidebar.form("screener_form"):

    st.header("👤 Modus")
    mode = st.radio(
        "Benutzermodus",
        ["🟢 Anfänger", "🔵 Pro"]
    )

    st.divider()

    st.header("🌍 Indizes")
    indices = st.multiselect(
        "Welche Märkte?",
        ["DAX", "Dow Jones", "S&P 500", "Nikkei"],
        default=["DAX", "Dow Jones"]
    )

    st.divider()

    if mode == "🟢 Anfänger":
        st.header("🧭 Strategie")
        strategy = st.selectbox(
            "Anlagestrategie",
            ["⚖️ Ausgewogen", "🚀 Wachstum", "🛡️ Dividende", "🎯 Turnaround"]
        )
    else:
        st.header("🔍 Filter")
        min_perf = st.slider("3W Performance (%)", -10, 20, 2)
        min_div = st.slider("Dividende (%)", 0.0, 10.0, 1.5)
        max_pe = st.slider("Max. KGV", 5, 40, 18)
        min_dist = st.slider("Abstand vom 52W-Hoch (%)", 0, 60, 15)

        use_div = st.checkbox("Dividenden-Filter aktiv", True)
        use_dist = st.checkbox("52W-Abstand aktiv", True)

        st.subheader("⚖️ Score-Gewichtung")
        w_perf = st.slider("Momentum", 0.0, 1.0, 0.4)
        w_dist = st.slider("Turnaround", 0.0, 1.0, 0.2)
        w_div = st.slider("Dividende", 0.0, 1.0, 0.2)
        w_pe = st.slider("Bewertung (KGV)", 0.0, 1.0, 0.2)

    submitted = st.form_submit_button("🚀 Screener starten")

# --------------------------------------------------
# Warten bis Start gedrückt wurde
# --------------------------------------------------
if not submitted:
    st.info("⬅️ Bitte Parameter einstellen und den Screener starten.")
    st.stop()

# --------------------------------------------------
# Presets für Anfänger-Modus (NACH dem Button!)
# --------------------------------------------------
if mode == "🟢 Anfänger":

    if strategy == "⚖️ Ausgewogen":
        min_perf, min_div, max_pe, min_dist = 0, 1.5, 18, 15
        w_perf, w_dist, w_div, w_pe = 0.4, 0.2, 0.2, 0.2
        use_div, use_dist = True, True

    elif strategy == "🚀 Wachstum":
        min_perf, min_div, max_pe, min_dist = 5, 0.0, 30, 5
        w_perf, w_dist, w_div, w_pe = 0.7, 0.1, 0.0, 0.2
        use_div, use_dist = False, False

    elif strategy == "🛡️ Dividende":
        min_perf, min_div, max_pe, min_dist = -2, 3.0, 15, 20
        w_perf, w_dist, w_div, w_pe = 0.2, 0.1, 0.5, 0.2
        use_div, use_dist = True, True

    elif strategy == "🎯 Turnaround":
        min_perf, min_div, max_pe, min_dist = -5, 0.5, 20, 35
        w_perf, w_dist, w_div, w_pe = 0.2, 0.6, 0.1, 0.1
        use_div, use_dist = False, True

# --------------------------------------------------
# Ticker Map
# --------------------------------------------------
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
# Zeitraum
# --------------------------------------------------
end = datetime.today()
start = end - timedelta(days=120)

# --------------------------------------------------
# Screener Logik
# --------------------------------------------------
results = []

with st.spinner("📡 Lade Marktdaten..."):
    for ticker, name in ticker_map.items():
        try:
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

            if pe is None:
                continue
            if use_div and (div is None or div * 100 < min_div):
                continue
            if perf_3w < min_perf:
                continue
            if use_dist and dist_52w > -min_dist:
                continue
            if pe > max_pe:
                continue

            score = (
                perf_3w * w_perf +
                abs(dist_52w) * w_dist +
                (div * 100 if div else 0) * w_div +
                (max_pe - pe) * w_pe
            )

            results.append({
                "Ticker": ticker,
                "Name": name,
                "Kurs": round(price_now, 2),
                "3W Perf (%)": round(perf_3w, 2),
                "Abstand 52W (%)": round(dist_52w, 2),
                "Dividende (%)": round((div or 0) * 100, 2),
                "KGV": round(pe, 2),
                "Score": round(score, 2)
            })

        except Exception as e:
            st.write(f"⚠️ Fehler bei {ticker}: {e}")

# --------------------------------------------------
# Ergebnis
# --------------------------------------------------
if len(results) == 0:
    st.warning("⚠️ Keine Aktien gefunden – Filter bitte lockern.")
else:
    df = pd.DataFrame(results).sort_values("Score", ascending=False)
    st.subheader("🏆 Ergebnisse")
    st.dataframe(df, use_container_width=True)

    st.download_button(
        "⬇️ Ergebnis als CSV",
        df.to_csv(index=False),
        "aktien_screener.csv"
    )
