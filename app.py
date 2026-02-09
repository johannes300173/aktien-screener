import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from tickers import DAX, DOW_JONES, SP500, NIKKEI

st.set_page_config(page_title="Aktienscreener", layout="wide")
st.title("📈 Aktienscreener – Value & Momentum")

st.sidebar.header("🔍 Filter")

min_perf = st.sidebar.slider("3-Wochen-Performance (%)", 0, 20, 5)
min_div = st.sidebar.slider("Dividendenrendite (%)", 0.0, 10.0, 5.0)
max_pe = st.sidebar.slider("Max. KGV", 1, 30, 14)
min_dist = st.sidebar.slider("Abstand vom 52W-Hoch (%)", 0, 60, 30)

indices = st.sidebar.multiselect(
    "Indizes",
    ["DAX", "Dow Jones", "S&P 500", "Nikkei"],
    default=["DAX", "Dow Jones"]
)

st.sidebar.header("⚖️ Score-Gewichtung")

w_perf = st.sidebar.slider("Momentum", 0.0, 1.0, 0.4)
w_dist = st.sidebar.slider("Turnaround", 0.0, 1.0, 0.3)
w_div = st.sidebar.slider("Dividende", 0.0, 1.0, 0.2)
w_pe = st.sidebar.slider("Bewertung (KGV)", 0.0, 1.0, 0.1)

ticker_map = {}
if "DAX" in indices:
    ticker_map.update(DAX)
if "Dow Jones" in indices:
    ticker_map.update(DOW_JONES)
if "S&P 500" in indices:
    ticker_map.update(SP500)
if "Nikkei" in indices:
    ticker_map.update(NIKKEI)

end = datetime.today()
start = end - timedelta(days=120)

if st.button("🚀 Screener starten"):

    results = []

    with st.spinner("Daten werden geladen..."):
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

                if (
                    pe is None or div is None or
                    perf_3w < min_perf or
                    dist_52w > -min_dist or
                    pe > max_pe or
                    div * 100 < min_div
                ):
                    continue

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
                    "3W Performance (%)": round(perf_3w, 2),
                    "Abstand 52W Hoch (%)": round(dist_52w, 2),
                    "Dividende (%)": round(div * 100, 2),
                    "KGV": round(pe, 2),
                    "Score": round(score, 2)
                })

            except Exception as e:
                st.write(f"⚠️ Fehler bei {ticker}: {e}")

    if len(results) == 0:
        st.warning("⚠️ Keine Aktien gefunden. Bitte Filter lockern.")
    else:
        df = pd.DataFrame(results).sort_values("Score", ascending=False)

        st.subheader("🏆 Ranking")
        st.dataframe(df, use_container_width=True)

        st.download_button(
            "⬇️ Ergebnis als CSV",
            df.to_csv(index=False),
            "aktien_screener.csv"
        )
