import yfinance as yf
import feedparser
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class DataIngestion:
    def __init__(self, assets: List[str]) -> None:
        self.assets = assets
        self.scheduler = BackgroundScheduler()
        self.market_data: Dict[str, Dict[str, Any]] = {}
        self.news_data: Dict[str, Dict[str, str]] = {}
        self.last_market_fetch: Dict[str, datetime] = {}
        logger.info(f"Initialized DataIngestion with assets: {self.assets}")

    def fetch_market_data(self) -> None:
        try:
            for asset in self.assets:
                ticker = yf.Ticker(asset)
                now = datetime.now()
                last_fetch = self.last_market_fetch.get(asset, now - timedelta(days=1))

                intraday = ticker.history(period="1d", interval="5m")
                daily = ticker.history(period="14d", interval="1d")

                if not intraday.empty and not daily.empty:
                    latest_intraday = intraday.iloc[-1]
                    self.market_data[asset] = {
                        "price": latest_intraday["Close"],
                        "volume": int(latest_intraday["Volume"]),
                        "timestamp": now.isoformat(),
                        "intraday_history": intraday["Close"].tolist(),
                        "daily_history": daily["Close"].tolist(),
                    }
                    self.last_market_fetch[asset] = now
                    logger.info(
                        f"Fetched market data for {asset}: price={latest_intraday['Close']}"
                    )
                else:
                    logger.warning(f"No market data for {asset}")
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")

    def fetch_news_data(self) -> None:
        """Fetch latest news for assets from Yahoo Finance RSS."""
        try:
            self.news_data.clear()
            for asset in self.assets:
                url_asset = asset.replace("-USD", "")  # e.g., BTC-USD -> BTCUSD
                url = f"https://finance.yahoo.com/rss/headline?s={url_asset}"
                logger.debug(f"Fetching news from RSS: {url}")
                feed = feedparser.parse(url)
                entries = feed.entries[:5]  # Top 5 news items
                for entry in entries:
                    title = entry.title
                    self.news_data[title] = {
                        "description": entry.summary,
                        "source": "Yahoo Finance",
                        "published_at": (
                            entry.published
                            if "published" in entry
                            else datetime.now().isoformat()
                        ),
                    }
                logger.info(
                    f"Fetched {len(entries)} news items for {asset} from Yahoo Finance RSS"
                )
        except Exception as e:
            logger.error(f"Error fetching news data: {str(e)}")

    def start_scheduler(self) -> None:
        try:
            self.scheduler.add_job(self.fetch_market_data, "interval", minutes=5)
            self.scheduler.add_job(self.fetch_news_data, "interval", minutes=5)
            self.scheduler.start()
            logger.info("Scheduler started for data ingestion every 5 minutes")
        except Exception as e:
            logger.error(f"Error starting scheduler: {str(e)}")

    def get_market_data(self) -> Dict[str, Dict[str, Any]]:
        return self.market_data

    def get_news_data(self) -> Dict[str, Dict[str, str]]:
        return self.news_data

    def stop_scheduler(self) -> None:
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
