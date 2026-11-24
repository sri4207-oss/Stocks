```python
"""Personal AI NSE Stock Analysis & 52-Week High/Low Momentum Dashboard.

Run locally with:
    pip install streamlit pandas numpy requests yfinance plotly google-genai
    streamlit run nse_ai_stock_app.py
"""

from __future__ import annotations

import io
import os
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import streamlit as st
import yfinance as yf

NSE_EQUITY_CSV_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
NSE_HOME_URL = "https://www.nseindia.com"

st.set_page_config(
    page_title="NSE AI Stock Screener & 52W High Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_nse_equity_list() -> pd.DataFrame:
    """Download the official NSE EQUITY_L.csv listed-equities directory."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/csv,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/market-data/securities-available-for-trading",
    }
    session = requests.Session()
    try:
        session.get(NSE_HOME_URL, headers=headers, timeout=10)
    except requests.RequestException:
        pass

    resp = session.get(NSE_EQUITY_CSV_URL, headers=headers, timeout=20)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    df.columns = [c.strip() for c in df.columns]
    for col in ("SYMBOL", "NAME OF COMPANY", "SERIES", "ISIN NUMBER"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    return df


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Wilder-style RSI."""
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _extract_ticker_df(raw: pd.DataFrame, yf_symbol: str, single: bool) -> pd.DataFrame | None:
    if raw is None or raw.empty:
        return None
    if single:
        df = raw.copy()
    else:
        if yf_symbol not in raw.columns.get_level_values(0):
            return None
        df = raw[yf_symbol].copy()
    df = df.dropna(subset=["Close"])
    if df.empty or len(df) < 30:
        return None
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def run_52w_momentum_scan(
    symbols_df: pd.DataFrame,
    batch_size: int = 50,
) -> pd.DataFrame:
    """Fetch 1-year OHLCV via yfinance and compute 52W high/low + momentum metrics."""
    symbols = symbols_df["SYMBOL"].tolist()
    name_map = dict(zip(symbols_df["SYMBOL"], symbols_df.get("NAME OF COMPANY", symbols)))
    isin_map = dict(zip(symbols_df["SYMBOL"], symbols_df.get("ISIN NUMBER", [""] * len(symbols))))

    records: list[dict[str, Any]] = []
    progress = st.progress(0.0, text="Downloading 1-year NSE price history...")
    total = len(symbols)

    for start in range(0, total, batch_size):
        chunk = symbols[start : start + batch_size]
        yf_tickers = [f"{s}.NS" for s in chunk]
        try:
            raw = yf.download(
                tickers=" ".join(yf_tickers),
                period="1y",
                interval="1d",
                group_by="ticker",
                auto_adjust=True,
                threads=True,
                progress=False,
            )
        except Exception:
            raw = pd.DataFrame()

        single = len(yf_tickers) == 1
        for sym, yf_sym in zip(chunk, yf_tickers):
            df = _extract_ticker_df(raw, yf_sym, single=single)
            if df is None:
                continue

            close = df["Close"].astype(float)
            high = df["High"].astype(float) if "High" in df else close
            low = df["Low"].astype(float) if "Low" in df else close
            vol = df["Volume"].astype(float) if "Volume" in df else pd.Series(0.0, index=df.index)

            curr_close = float(close.iloc[-1])
            w52_high = float(high.max())
            w52_low = float(low.min())
            if w52_high <= 0 or w52_low <= 0:
                continue

            dist_high_pct = ((curr_close - w52_high) / w52_high) * 100.0
            dist_low_pct = ((curr_close - w52_low) / w52_low) * 100.0
            if w52_high > w52_low:
                range_pos_pct = ((curr_close - w52_low) / (w52_high - w52_low)) * 100.0
            else:
                range_pos_pct = 100.0

            def _ret(days: int) -> float:
                if len(close) > days:
                    prev = float(close.iloc[-(days + 1)])
                    return ((curr_close - prev) / prev) * 100.0 if prev > 0 else np.nan
                return np.nan

            ret_1w = _ret(5)
            ret_1m = _ret(21)
            ret_3m = _ret(63)
            ret_6m = _ret(126)
            ret_1y = ((curr_close - float(close.iloc[0])) / float(close.iloc[0])) * 100.0

            sma20 = float(close.rolling(20).mean().iloc[-1]) if len(close) >= 20 else np.nan
            sma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else np.nan
            sma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else np.nan

            rsi_series = compute_rsi(close, 14)
            rsi_14 = float(rsi_series.iloc[-1]) if not rsi_series.dropna().empty else np.nan

            avg_vol_20 = float(vol.tail(20).mean()) if len(vol) >= 20 else float(vol.mean())
            curr_vol = float(vol.iloc[-1])
            vol_ratio = (curr_vol / avg_vol_20) if avg_vol_20 > 0 else np.nan

            daily_ret = close.pct_change().dropna()
            ann_vol = float(daily_ret.std() * np.sqrt(252) * 100.0) if len(daily_ret) > 10 else np.nan

            # Composite score favoring stocks near 52W High with strong trend & momentum
            proximity_score = max(0.0, 100.0 + dist_high_pct * 3.0)  # 100 at 52W high
            mom_parts = [x for x in (ret_1m, ret_3m, ret_6m) if pd.notna(x)]
            mom_avg = float(np.mean(mom_parts)) if mom_parts else 0.0
            trend_bonus = 0.0
            if pd.notna(sma50) and curr_close > sma50:
                trend_bonus += 10.0
            if pd.notna(sma200) and curr_close > sma200:
                trend_bonus += 10.0
            composite_score = round(0.50 * proximity_score + 0.35 * mom_avg + trend_bonus, 2)

            records.append(
                {
                    "Symbol": sym,
                    "Company": name_map.get(sym, sym),
                    "ISIN": isin_map.get(sym, ""),
                    "Price (₹)": round(curr_close, 2),
                    "52W High (₹)": round(w52_high, 2),
                    "52W Low (₹)": round(w52_low, 2),
                    "Dist 52W High (%)": round(dist_high_pct, 2),
                    "Dist 52W Low (%)": round(dist_low_pct, 2),
                    "52W Range Pos (%)": round(range_pos_pct, 1),
                    "1W (%)": round(ret_1w, 2) if pd.notna(ret_1w) else np.nan,
                    "1M (%)": round(ret_1m, 2) if pd.notna(ret_1m) else np.nan,
                    "3M (%)": round(ret_3m, 2) if pd.notna(ret_3m) else np.nan,
                    "6M (%)": round(ret_6m, 2) if pd.notna(ret_6m) else np.nan,
                    "1Y (%)": round(ret_1y, 2),
                    "RSI (14)": round(rsi_14, 1) if pd.notna(rsi_14) else np.nan,
                    "SMA 50": round(sma50, 2) if pd.notna(sma50) else np.nan,
                    "SMA 200": round(sma200, 2) if pd.notna(sma200) else np.nan,
                    "Vol Ratio": round(vol_ratio, 2) if pd.notna(vol_ratio) else np.nan,
                    "Volatility (%)": round(ann_vol, 1) if pd.notna(ann_vol) else np.nan,
                    "AI Momentum Score": composite_score,
                }
            )

        done = min(start + batch_size, total)
        progress.progress(done / total, text=f"Scanned {done}/{total} NSE equities...")

    progress.empty()
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)


@st.cache_data(ttl=900, show_spinner=False)
def fetch_stock_detail(symbol: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fetch 1-year OHLCV history and fundamental info for a single NSE symbol."""
    ticker = yf.Ticker(f"{symbol}.NS")
    hist = ticker.history(period="1y", interval="1d", auto_adjust=True)
    try:
        info = ticker.info or {}
    except Exception:
        info = {}
    return hist, info


def format_inr_crores(value: Any) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    try:
        cr = float(value) / 1e7
        if cr >= 100000:
            return f"₹{cr / 100000:,.2f} Lakh Cr"
        return f"₹{cr:,.0f} Cr"
    except (TypeError, ValueError):
        return "N/A"


def build_rule_based_ai_summary(row: pd.Series, info: dict[str, Any]) -> str:
    """Deterministic technical & fundamental analysis when no Gemini API key is set."""
    sym = row["Symbol"]
    dist_high = row["Dist 52W High (%)"]
    range_pos = row["52W Range Pos (%)"]
    rsi = row["RSI (14)"]
    vol_ratio = row["Vol Ratio"]
    price = row["Price (₹)"]
    sma50 = row["SMA 50"]
    sma200 = row["SMA 200"]

    signals = []
    if dist_high >= -2.0:
        signals.append(f"**52-Week Breakout Zone**: Trading within {abs(dist_high):.2f}% of its 52-week high (₹{row['52W High (₹)']:,.2f}).")
    elif dist_high >= -5.0:
        signals.append(f"**Approaching 52-Week High**: {abs(dist_high):.2f}% below 52W high; strong relative strength ({range_pos:.1f}% of 52W range).")
    else:
        signals.append(f"**Consolidation / Pullback**: {abs(dist_high):.2f}% below 52W high ({range_pos:.1f}% of 52W range).")

    if pd.notna(sma50) and pd.notna(sma200):
        if price > sma50 > sma200:
            signals.append("**Trend Alignment**: Bullish Stage-2 structure (Price > SMA 50 > SMA 200).")
        elif price > sma200:
            signals.append("**Trend Alignment**: Above 200-day SMA, long-term uptrend intact.")
        else:
            signals.append("**Trend Caution**: Trading below 200-day SMA; watch for trend reversal.")

    if pd.notna(rsi):
        if rsi > 70:
            signals.append(f"**Momentum / RSI ({rsi:.1f})**: Overbought territory — strong momentum, but watch for short-term pullbacks.")
        elif rsi >= 55:
            signals.append(f"**Momentum / RSI ({rsi:.1f})**: Healthy bullish momentum without extreme overbought reading.")
        elif rsi < 35:
            signals.append(f"**Momentum / RSI ({rsi:.1f})**: Oversold zone — potential mean-reversion watch.")
        else:
            signals.append(f"**Momentum / RSI ({rsi:.1f})**: Neutral momentum.")

    if pd.notna(vol_ratio) and vol_ratio >= 1.5:
        signals.append(f"**Volume Confirmation**: Today's volume is {vol_ratio:.2f}x the 20-day average.")

    pe = info.get("trailingPE")
    roe = info.get("returnOnEquity")
    val_notes = []
    if pe is not None:
        val_notes.append(f"Trailing P/E: {pe:.1f}x")
    if roe is not None:
        val_notes.append(f"ROE: {roe * 100:.1f}%")
    if val_notes:
        signals.append("**Fundamentals**: " + " | ".join(val_notes) + ".")

    return "\n\n".join(f"- {s}" for s in signals)


def generate_gemini_analysis(
    api_key: str,
    row: pd.Series,
    info: dict[str, Any],
) -> str:
    """Call Gemini API for personalized stock analysis using retrieved metrics."""
    from google import genai

    client = genai.Client(api_key=api_key)
    prompt = f"""You are a concise Indian equity research assistant. Analyze {row['Company']} ({row['Symbol']}.NS) using ONLY the verified metrics below. Do not invent numbers.

Technical & 52-Week Metrics:
- Current Price: ₹{row['Price (₹)']}
- 52-Week High: ₹{row['52W High (₹)']} ({row['Dist 52W High (%)']}% from high)
- 52-Week Low: ₹{row['52W Low (₹)']} (+{row['Dist 52W Low (%)']}% from low)
- 52W Range Position: {row['52W Range Pos (%)']}%
- Returns: 1W {row['1W (%)']}%, 1M {row['1M (%)']}%, 3M {row['3M (%)']}%, 6M {row['6M (%)']}%, 1Y {row['1Y (%)']}%
- RSI (14): {row['RSI (14)']} | SMA 50: ₹{row['SMA 50']} | SMA 200: ₹{row['SMA 200']}
- Volume Ratio (vs 20D avg): {row['Vol Ratio']}x | Annualized Volatility: {row['Volatility (%)']}%

Fundamentals:
- Sector / Industry: {info.get('sector', 'N/A')} / {info.get('industry', 'N/A')}
- Market Cap: {format_inr_crores(info.get('marketCap'))}
- Trailing P/E: {info.get('trailingPE', 'N/A')} | Forward P/E: {info.get('forwardPE', 'N/A')} | P/B: {info.get('priceToBook', 'N/A')}
- ROE: {round(info['returnOnEquity'] * 100, 2) if info.get('returnOnEquity') else 'N/A'}%
- Debt/Equity: {info.get('debtToEquity', 'N/A')} | Dividend Yield: {round(info['dividendYield'] * 100, 2) if info.get('dividendYield') else 'N/A'}%

Provide:
1. **52-Week High Breakout & Trend Verdict** (2 sentences)
2. **Bullish Catalysts** (2 bullets)
3. **Key Risks / Watchouts** (2 bullets)
4. **Key Levels to Watch** (Support & Breakout/Resistance based on the numbers above)
Add a brief note that this is for informational research only, not SEBI-registered investment advice."""

    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return resp.text or "No response returned by Gemini."


def plot_stock_chart(symbol: str, hist: pd.DataFrame) -> go.Figure:
    """Create interactive 1-year candlestick + SMA + 52W High/Low + RSI chart."""
    df = hist.copy()
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["SMA200"] = df["Close"].rolling(200).mean()
    df["RSI14"] = compute_rsi(df["Close"], 14)

    w52_high = float(df["High"].max())
    w52_low = float(df["Low"].min())

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.60, 0.20, 0.20],
        subplot_titles=(f"{symbol}.NS — 1-Year Price & 52W High/Low", "Volume", "RSI (14)"),
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="OHLC",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA20"], name="SMA 20", line=dict(width=1.2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"], name="SMA 50", line=dict(width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA200"], name="SMA 200", line=dict(width=1.5)), row=1, col=1)

    fig.add_hline(
        y=w52_high,
        line_dash="dash",
        line_color="green",
        annotation_text=f"52W High: ₹{w52_high:,.2f}",
        row=1,
        col=1,
    )
    fig.add_hline(
        y=w52_low,
        line_dash="dash",
        line_color="red",
        annotation_text=f"52W Low: ₹{w52_low:,.2f}",
        row=1,
        col=1,
    )

    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color="rgba(49, 134, 255, 0.5)"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI14"], name="RSI (14)", line=dict(color="orange")), row=3, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="green", row=3, col=1)

    fig.update_layout(
        height=720,
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def main() -> None:
    st.title("📈 Personal AI NSE Stock Screener & 52-Week High Tracker")
    st.caption(
        "Official NSE Equity Universe (EQUITY_L.csv) • 1-Year Market Data via yfinance • "
        "52-Week High Proximity Ranking & AI Research"
    )

    # Sidebar Controls
    with st.sidebar:
        st.header("⚙️ Screener Controls")
        scan_limit = st.selectbox(
            "Stocks to Scan (from NSE EQUITY_L.csv)",
            options=[50, 100, 200, 500, 0],
            index=1,
            format_func=lambda x: "All NSE EQ Stocks (~2,000+)" if x == 0 else f"First {x} NSE EQ Stocks",
        )
        custom_tickers_raw = st.text_input(
            "Custom Watchlist Symbols (comma-separated, optional)",
            value="RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, SBIN, LT, BHARTIARTL, ITC, TATAMOTORS",
            help="These symbols are always included in the scan.",
        )
        sort_mode = st.selectbox(
            "Ranking Mode",
            options=[
                "Approaching 52W High (Closest First)",
                "AI Momentum + 52W High Score",
                "1M Return (%)",
                "3M Return (%)",
                "1Y Return (%)",
                "Near 52W Low (Value Watch)",
            ],
            index=0,
        )
        max_dist_high = st.slider(
            "Filter: Max % Below 52-Week High",
            min_value=1.0,
            max_value=50.0,
            value=15.0,
            step=0.5,
            help="Show stocks within this % of their 52-week high (0% = at 52W high).",
        )
        min_rsi, max_rsi = st.slider("Filter: RSI (14) Range", 0, 100, (30, 85))
        only_above_sma200 = st.checkbox("Only stocks above 200-day SMA", value=False)

        st.divider()
        st.header("🤖 AI Analyst Settings")
        gemini_api_key = st.text_input(
            "Gemini API Key (optional)",
            value=os.environ.get("GEMINI_API_KEY", ""),
            type="password",
            help="Leave blank to use built-in technical & fundamental signal engine.",
        )

        run_scan_btn = st.button("🔄 Run / Refresh NSE Scan", type="primary", use_container_width=True)

    # Load NSE Universe
    try:
        with st.spinner("Loading official NSE EQUITY_L.csv..."):
            nse_df = fetch_nse_equity_list()
    except Exception as exc:
        st.error(f"Could not download NSE EQUITY_L.csv: {exc}")
        st.stop()

    eq_df = nse_df[nse_df["SERIES"] == "EQ"].copy() if "SERIES" in nse_df.columns else nse_df.copy()

    # Build scan universe combining custom watchlist + first N NSE EQ stocks
    custom_syms = [s.strip().upper().replace(".NS", "") for s in custom_tickers_raw.split(",") if s.strip()]
    custom_df = eq_df[eq_df["SYMBOL"].isin(custom_syms)]

    if scan_limit == 0:
        target_df = eq_df
    else:
        base_df = eq_df.head(scan_limit)
        target_df = pd.concat([custom_df, base_df]).drop_duplicates(subset=["SYMBOL"])

    st.info(
        f"Loaded **{len(eq_df):,}** `EQ`-series stocks from NSE `EQUITY_L.csv`. "
        f"Ready to scan **{len(target_df):,}** symbols (as of {datetime.now().strftime('%d %b %Y, %I:%M %p')})."
    )

    if "scan_results" not in st.session_state or run_scan_btn:
        st.session_state["scan_results"] = run_52w_momentum_scan(target_df)

    results_df = st.session_state.get("scan_results", pd.DataFrame())
    if results_df.empty:
        st.warning("No stock data returned. Click 'Run / Refresh NSE Scan' or check your internet connection.")
        st.stop()

    # Apply Filters
    filtered = results_df.copy()
    filtered = filtered[filtered["Dist 52W High (%)"] >= -max_dist_high]
    filtered = filtered[
        filtered["RSI (14)"].isna() | ((filtered["RSI (14)"] >= min_rsi) & (filtered["RSI (14)"] <= max_rsi))
    ]
    if only_above_sma200:
        filtered = filtered[filtered["SMA 200"].notna() & (filtered["Price (₹)"] > filtered["SMA 200"])]

    # Sort according to selected Ranking Mode
    if sort_mode == "Approaching 52W 
