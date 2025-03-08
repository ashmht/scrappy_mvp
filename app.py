import os
from dotenv import load_dotenv
import logging
from src.data_ingestion import DataIngestion
from src.sentiment_analyzer import SentimentAnalyzer
from src.trading_detector import TradingSignalDetector
from src.alert_manager import AlertManager
from src.dashboard import run_dashboard
from src.asset_finder import AssetFinder
from typing import List, Dict

load_dotenv()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting Scrappy MVP Trading Idea Generator")

    # Step 1: Initialize AssetFinder to get the list of biggest losers
    asset_finder = AssetFinder(target_assets=5, max_candidates=10)
    candidate_assets = asset_finder.stock_candidates

    # Step 2: Fetch initial market data and news for all candidates
    ingestion = DataIngestion(assets=candidate_assets)
    ingestion.fetch_market_data()
    ingestion.fetch_news_data()

    # Step 3: Perform sentiment analysis on the candidates
    sentiment = SentimentAnalyzer()
    sentiment_scores = sentiment.analyze_sentiment(ingestion.get_news_data())
    asset_sentiments = sentiment.aggregate_sentiment_by_asset(
        ingestion.get_news_data(), candidate_assets
    )

    # Step 4: Find top 5 interesting assets based on sentiment, volatility, and P/E
    ASSETS: List[str] = asset_finder.find_interesting_assets(asset_sentiments)
    if not ASSETS:
        logger.warning("No interesting assets found, falling back to default list")
        ASSETS = [
            "DZSI",
            "BBWI",
            "ETSY",
            "SENS",
            "NGVC",
            "INOD",
            "NGS",
            "OB",
            "TBBK",
            "HESM",
        ][:5]

    # Step 5: Reinitialize DataIngestion with selected assets for detailed analysis
    ingestion = DataIngestion(assets=ASSETS)
    detector = TradingSignalDetector(market_data=ingestion.get_market_data())
    EMAIL_CONFIG: Dict[str, str] = {
        "sender": os.getenv("EMAIL_SENDER", ""),
        "password": os.getenv("EMAIL_PASSWORD", ""),
    }
    alerts = AlertManager(email_config=EMAIL_CONFIG)

    # Step 6: Fetch detailed data and run the full pipeline
    ingestion.fetch_market_data()
    ingestion.fetch_news_data()
    sentiment_scores = sentiment.analyze_sentiment(ingestion.get_news_data())
    asset_sentiments = sentiment.aggregate_sentiment_by_asset(
        ingestion.get_news_data(), ASSETS
    )
    opportunities = detector.detect_opportunities()
    alerts.process_alerts(opportunities, asset_sentiments)
    logger.info("Alerts processed successfully")
    ingestion.start_scheduler()

    logger.info(f"Sentiment Scores: {sentiment_scores}")
    logger.info(f"Asset Sentiments: {asset_sentiments}")
    logger.info(f"Trading Opportunities: {opportunities}")
    run_dashboard(ingestion, sentiment, detector, alerts)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Program terminated by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
