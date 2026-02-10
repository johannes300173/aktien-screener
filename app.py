import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime, timedelta
from tickers import DAX, DOW_JONES, SP500, NIKKEI

# --------------------------------------------------
# App Setup
# --------------------------------------------------
st.set_page_config(page_title="Aktienscreener (Hybrid)", layout="wide")
st.title("📊 Aktienscreener – Hybrid-Version")
st.caption("Phase 1: Performance | Phase 2: Fundamentaldaten (Top 20)")

# --------------------------------------------------
# Sidebar – Filter
# --------------------------------------------------
with st.sidebar:
    with st.form("filter_form"):

        st.subheader("Bewertung (Phase 2)")
        kgv_min = st.number_input("KGV von", 0.0, 100.0, 0.0, 0.5)
        kgv_max = st.number_input("KGV bis", 0.0, 100.0, 30.0, 0.5)

        div_min = st.number_input("Dividende von (%)", 0.0, 20.0, 0.0, 0.1)
        div_max = st.number_input("Dividende bis (%)", 0.0, 20.0, 10.0, 0.1)

        st.subheader("Performance (Phase 1)")
        lookback_days = st.number_input("Zeitraum (Börsentage)", 5, 250, 20)
        min_performance = st.number_input("Mindest-Performance (%)", value=0.0)

        st.subheader("Indizes")
        indices = st.multiselect(
            "Auswahl",
            ["DAX", "Dow Jones", "S&P 500", "Nikkei"],
            default=["DAX", "Dow Jones"]
        )

        submitted = st.form_submit_button("🚀 Screener starten")

if not submitted:
    st.info("⬅️ Filter setzen und Screener starten")
    st.stop()

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
start = end - timedelta(days=400)

# --------------------------------------------------
# PHASE 1 – Performance Scan
# --------------------------------------------------
candidates = []

with st.spinner("🔍 Phase 1: Performance-Scan"):
    for ticker, name in ticker_map.items():
        try:
            hist = yf.Ticker(ticker).history(start=start, end=end)

            if len(hist) < lookback_days + 1:
                continue

            price_now = hist["Close"].iloc[-1]
            price_then = hist["Close"].iloc[-lookback_days]

            perf = ((price_now / price_then) - 1) * 100

            if perf < min_performance:
                continue

            high_52w = hist["High"].max()
            high_date = hist["High"].idxmax().date()

            candidates.append({
                "Ticker": ticker,
                "Aktie": name,
                "Kurs": round(price_now, 2),
                "Performance (%)": round(perf, 2),
                "52W Hoch": round(high_52w, 2),
                "Datum 52W Hoch": high_date
            })

        except Exception:
            continue

# Top 20 nach Performance
df_phase1 = pd.DataFrame(candidates)
df_phase1 = df_phase1.sort_values("Performance (%)", ascending=False).head(20)

# --------------------------------------------------
# PHASE 2 – Fundamentaldaten NUR für Top 20
# --------------------------------------------------
results = []

with st.spinner("📊 Phase 2: Fundamentaldaten (Top 20)"):
    for _, row in df_phase1.iterrows():
        try:
            stock = yf.Ticker(row["Ticker"])
            fast = stock.fast_info

            pe = fast.get("pe_ratio")
            div = fast.get("dividend_yield")
            div_percent = (div or 0) * 100

            if pe is None or pe < kgv_min or pe > kgv_max:
                continue
            if div_percent < div_min or div_percent > div_max:
                continue

            row["KGV"] = round(pe, 2)
            row["Dividende (%)"] = round(div_percent, 2)

            results.append(row)

            time.sleep(0.4)  # sehr wenige Requests → stabil

        except Exception:
            continue

# --------------------------------------------------
# Ergebnis
# --------------------------------------------------
if not results:
    st.warning("⚠️ Keine Aktien nach Fundamentaldaten übrig.")
else:
    df_final = pd.DataFrame(results)

    st.subheader("🏆 Top 20 Aktien (Hybrid-Screener)")
    st.dataframe(
        df_final[
            [
                "Aktie",
                "Ticker",
                "Kurs",
                "Dividende (%)",
                "KGV",
                "Performance (%)",
                "52W Hoch",
                "Datum 52W Hoch"
            ]
        ],
        use_container_width=True
    )

    st.download_button(
        "⬇️ Ergebnis als CSV",
        df_final.to_csv(index=False),
        "hybrid_aktienscreener.csv"
    )
