import streamlit as st
import logging
import pandas as pd
import plotly.express as px
import requests
import os
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()
logger = logging.getLogger(__name__)


# Function to load CSS from a file
def load_css(file_path: str) -> str:
    with open(file_path, "r") as file:
        return f"<style>{file.read()}</style>"


# Load CSS from the external file
LIGHT_MODE_CSS = load_css("src/styles.css")

# FMP API key
FMP_API_KEY = os.getenv("FMP_API_KEY")
if not FMP_API_KEY:
    logger.error("FMP_API_KEY not found in .env file")
    st.error("FMP API key is missing. Please add it to your .env file.")
    FMP_API_KEY = "demo"  # FMP demo key for testing (limited)


# Cached function to fetch company profile from FMP
@st.cache_data(ttl=86400)  # Cache for 24 hours (86,400 seconds)
def fetch_company_profile(ticker: str) -> Dict[str, Any]:
    """Fetch company profile data from FMP API with caching."""
    try:
        url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={FMP_API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data or not isinstance(data, list) or len(data) == 0:
            logger.warning(f"No profile data for {ticker}")
            return {
                "description": f"No data available for {ticker}",
                "sector": "Unknown",
                "sp500": "Unknown",
            }

        profile = data[0]
        description = profile.get("description", "No description available")
        sector = profile.get("sector", "Unknown")
        industry = profile.get("industry", "")
        full_sector = f"{sector} ({industry})" if industry else sector
        market_cap = profile.get("mktCap", 0)
        sp500_status = "Yes" if market_cap > 10_000_000_000 else "No"  # Rough heuristic

        return {
            "description": description,
            "sector": full_sector,
            "sp500": sp500_status,
        }
    except Exception as e:
        logger.error(f"Error fetching profile for {ticker}: {str(e)}")
        return {
            "description": f"Error fetching data for {ticker}",
            "sector": "Unknown",
            "sp500": "Unknown",
        }


def run_dashboard(ingestion: Any, sentiment: Any, detector: Any, alerts: Any) -> None:
    """Launch a visually appealing Streamlit dashboard with dynamic stock summaries."""
    # Inject CSS
    st.markdown(LIGHT_MODE_CSS, unsafe_allow_html=True)

    # Header
    st.title("Scrappy Trading Ideas")
    st.subheader("Real-Time Market Insights")
    st.write(
        "Get the latest prices, trading signals, and news—updated every 5 minutes."
    )

    # Fetch data
    market_data = ingestion.get_market_data()
    news_data = ingestion.get_news_data()
    sentiment_scores = sentiment.analyze_sentiment(news_data)
    asset_sentiments = sentiment.aggregate_sentiment_by_asset(
        news_data, ingestion.assets
    )
    opportunities = detector.detect_opportunities()

    # Asset Cards
    for asset in ingestion.assets:
        with st.container():
            st.markdown(f"### 📈 {asset}", unsafe_allow_html=True)
            col1, col2 = st.columns([2, 1])

            # Left Column: Price, Chart
            with col1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                if asset in market_data:
                    price = market_data[asset]["price"]
                    volume = market_data[asset]["volume"]
                    st.markdown(
                        f"**💰 Current Price**: ${price:.2f}", unsafe_allow_html=True
                    )
                    st.markdown(f"**📊 Volume**: {volume:,}", unsafe_allow_html=True)

                    # Price Chart using Plotly
                    daily_history = market_data[asset]["daily_history"]
                    if daily_history:
                        df = pd.DataFrame({"Price": daily_history})
                        dates = pd.date_range(
                            start=pd.Timestamp.now()
                            - pd.Timedelta(days=len(daily_history) - 1),
                            periods=len(daily_history),
                            freq="D",
                        )
                        df["Date"] = dates
                        min_price = min(daily_history) * 0.95  # 5% buffer below
                        max_price = max(daily_history) * 1.05  # 5% buffer above
                        fig = px.line(df, x="Date", y="Price", height=150)
                        fig.update_traces(line_color="#00cc96")
                        fig.update_layout(
                            margin=dict(l=0, r=0, t=0, b=0),
                            yaxis=dict(range=[min_price, max_price], title=""),
                            xaxis=dict(title="", tickformat="%b %d"),
                            showlegend=False,
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning(f"No market data for {asset}")
                st.markdown("</div>", unsafe_allow_html=True)

            # Right Column: Signal and Sentiment
            with col2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                signal = opportunities.get(asset, "No signal")
                if "Overbought" in signal:
                    st.markdown(
                        f"**📉 Signal**: :red[Sell - {signal}]", unsafe_allow_html=True
                    )
                elif "Oversold" in signal:
                    st.markdown(
                        f"**📈 Signal**: :green[Buy - {signal}]", unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"**⚖️ Signal**: :gray[{signal}]", unsafe_allow_html=True
                    )

                sentiment_info = asset_sentiments.get(
                    asset, {"avg_compound": 0.0, "count": 0}
                )
                avg_compound = sentiment_info["avg_compound"]
                news_count = sentiment_info["count"]
                sentiment_label = sentiment.classify_sentiment(avg_compound)
                color = (
                    ":green"
                    if sentiment_label == "positive"
                    else ":red"
                    if sentiment_label == "negative"
                    else ":gray"
                )
                st.markdown(
                    f"**😊 Mood**: {color}[{sentiment_label.capitalize()} ({avg_compound:.2f})]",
                    unsafe_allow_html=True,
                )
                st.markdown(f"**📰 News Items**: {news_count}", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # News Section
            with st.expander("📰 Latest News"):
                if news_count > 0:
                    for title, info in news_data.items():
                        if (
                            asset.lower() in title.lower()
                            or asset.lower() in info["description"].lower()
                        ):
                            score = sentiment_scores.get(title, {}).get("compound", 0.0)
                            sentiment_color = (
                                ":green"
                                if score > 0.05
                                else ":red"
                                if score < -0.05
                                else ":gray"
                            )
                            st.markdown(
                                f"- {sentiment_color}[{title}] (Score: {score:.2f})",
                                unsafe_allow_html=True,
                            )
                else:
                    st.info("No recent news available.")

            # Stock Summary Section (Dynamic from FMP)
            profile = fetch_company_profile(asset)
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f"**📋 Summary**: {profile['description']}")
            st.markdown(f"**🏭 Sector**: {profile['sector']}")
            st.markdown(
                f"**S&P 500**: {profile['sp500']} (Note: Approximate; verify manually)",
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

    # Sidebar
    st.sidebar.markdown("### About Scrappy")
    st.sidebar.write(
        "Real-time insights from Yahoo Finance and news feeds to spot trading opportunities. Green = Go, Red = Caution!"
    )
    st.sidebar.markdown("**Assets Monitored**: " + ", ".join(ingestion.assets))

    logger.info("Dashboard launched")
