import yfinance as yf
import pandas as pd
import logging
import requests
import os
from dotenv import load_dotenv
from typing import List, Dict, Any
import numpy as np

load_dotenv()
logger = logging.getLogger(__name__)


class AssetFinder:
    def __init__(self, target_assets: int = 5, max_candidates: int = 10) -> None:
        """
        Initialize the AssetFinder to discover trending stocks with the biggest losses.

        Args:
            target_assets: Number of assets to select (default 5).
            max_candidates: Maximum number of candidate stocks to fetch (default 10).
        """
        self.target_assets = max(5, min(target_assets, 10))  # Ensure 5–10 assets
        self.max_candidates = max_candidates
        self.fmp_api_key = os.getenv("FMP_API_KEY")
        if not self.fmp_api_key:
            logger.error("FMP_API_KEY not found in .env file")
            raise ValueError("FMP_API_KEY is required")
        self.stock_candidates = self.fetch_biggest_losers()
        logger.info(
            f"Initialized AssetFinder with {len(self.stock_candidates)} stock candidates"
        )

    def fetch_biggest_losers(self) -> List[str]:
        """Fetch stocks with the biggest losses today using FinancialModelingPrep API."""
        try:
            # FMP endpoint for stock market losers
            url = f"https://financialmodelingprep.com/api/v3/stock_market/losers?limit={self.max_candidates}&apikey={self.fmp_api_key}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            tickers = [stock["symbol"] for stock in data[: self.max_candidates]]
            if not tickers:  # Ensure we have some data
                logger.warning("No losers fetched from FMP, using fallback list")
                return [
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
                ]
            logger.info(f"Fetched {len(tickers)} biggest losers: {tickers}")
            return tickers
        except Exception as e:
            logger.error(f"Error fetching biggest losers from FMP: {str(e)}")
            # Updated fallback list to include DZSI and similar micro-cap stocks
            return [
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
            ]

    def calculate_volatility(self, history: pd.DataFrame) -> float:
        """Calculate the volatility (standard deviation of daily returns)."""
        if len(history) < 2:
            return 0.0
        returns = history["Close"].pct_change().dropna()
        return returns.std() * np.sqrt(252)  # Annualized volatility

    def fetch_asset_data(self, ticker: str) -> Dict[str, Any]:
        """Fetch market data for a single stock and calculate metrics."""
        try:
            asset = yf.Ticker(ticker)
            history = asset.history(period="14d", interval="1d")
            if history.empty:
                return None

            # Market Cap and P/E Ratio
            info = asset.info
            market_cap = info.get("marketCap", 0)
            pe_ratio = info.get(
                "forwardPE", float("inf")
            )  # Use forward P/E; default to inf if unavailable
            if market_cap == 0:
                return None

            volatility = self.calculate_volatility(history)

            return {
                "ticker": ticker,
                "market_cap": market_cap,
                "volatility": volatility,
                "pe_ratio": pe_ratio,
            }
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {str(e)}")
            return None

    def find_interesting_assets(
        self, asset_sentiments: Dict[str, Dict[str, float]]
    ) -> List[str]:
        """
        Find interesting stocks from the biggest losers based on sentiment, volatility, and P/E.

        Args:
            asset_sentiments: Sentiment data from SentimentAnalyzer {ticker: {"avg_compound": float, "count": int}}
        """
        asset_data = []

        for ticker in self.stock_candidates:
            data = self.fetch_asset_data(ticker)
            if not data:
                continue

            # Get sentiment score
            sentiment_info = asset_sentiments.get(
                ticker, {"avg_compound": 0.0, "count": 0}
            )
            sentiment_score = abs(
                sentiment_info["avg_compound"]
            )  # Absolute value (both positive/negative are interesting)
            sentiment_weight = (
                sentiment_score if sentiment_info["count"] > 0 else 0.1
            )  # Neutral score if no news

            # P/E ratio score (lower is better for undervaluation; invert for scoring)
            pe_score = (
                1 / data["pe_ratio"]
                if data["pe_ratio"] != float("inf") and data["pe_ratio"] > 0
                else 0.0
            )

            # Calculate combined score (weights: sentiment 40%, volatility 30%, P/E 30%)
            score = sentiment_weight * 0.4 + data["volatility"] * 0.3 + pe_score * 0.3
            data["score"] = score
            data["sentiment"] = sentiment_score
            data["news_count"] = sentiment_info["count"]
            asset_data.append(data)

        # Sort by score and return top assets
        asset_data.sort(key=lambda x: x["score"], reverse=True)
        selected_assets = [data["ticker"] for data in asset_data[: self.target_assets]]

        logger.info(f"Found interesting stocks: {selected_assets}")
        logger.debug(
            f"Asset scores: {[f'{d["ticker"]}: score={d["score"]:.2f}, sentiment={d["sentiment"]:.2f}, volatility={d["volatility"]:.2f}, pe_ratio={d["pe_ratio"]:.2f}' for d in asset_data[: self.target_assets]]}"
        )
        return selected_assets
