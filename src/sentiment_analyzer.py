import logging
import re
from typing import Dict, List
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# Download VADER lexicon if not already present
try:
    nltk.data.find("vader_lexicon")
except LookupError:
    nltk.download("vader_lexicon")

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    def __init__(self) -> None:
        """Initialize the SentimentAnalyzer with VADER."""
        self.analyzer = SentimentIntensityAnalyzer()
        logger.info("Initialized SentimentAnalyzer with VADER")

    def preprocess_text(self, text: str) -> str:
        """Clean text for sentiment analysis."""
        # Remove URLs, special characters, and extra whitespace
        text = re.sub(r"http\S+|www\S+|https\S+", "", text, flags=re.MULTILINE)
        text = re.sub(r"[^A-Za-z0-9\s]", "", text)
        text = " ".join(text.split())
        return text.lower()

    def analyze_sentiment(
        self, news_data: Dict[str, Dict[str, str]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Analyze sentiment of news data.

        Args:
            news_data: {title: {"description": str, "source": str, "published_at": str}}

        Returns:
            {title: {"neg": float, "neu": float, "pos": float, "compound": float}}
        """
        sentiment_scores = {}
        try:
            for title, info in news_data.items():
                text = f"{title} {info['description']}"  # Combine title and description
                cleaned_text = self.preprocess_text(text)
                scores = self.analyzer.polarity_scores(cleaned_text)
                sentiment_scores[title] = {
                    "neg": scores["neg"],
                    "neu": scores["neu"],
                    "pos": scores["pos"],
                    "compound": scores["compound"],
                }
                logger.debug(f"Sentiment for '{title}': {scores}")
            logger.info("Sentiment analysis completed for all news items")
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
        return sentiment_scores

    def classify_sentiment(self, compound_score: float) -> str:
        """Classify sentiment based on compound score."""
        if compound_score > 0.05:
            return "positive"
        elif compound_score < -0.05:
            return "negative"
        else:
            return "neutral"

    def aggregate_sentiment_by_asset(
        self, news_data: Dict[str, Dict[str, str]], assets: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """
        Aggregate sentiment scores by asset.

        Args:
            news_data: News data from DataIngestion
            assets: List of assets to analyze

        Returns:
            {asset: {"avg_compound": float, "count": int}}
        """
        sentiment_scores = self.analyze_sentiment(news_data)
        asset_sentiments: Dict[str, List[float]] = {asset: [] for asset in assets}

        try:
            for title, scores in sentiment_scores.items():
                # Check which asset(s) the news relates to
                for asset in assets:
                    if (
                        asset.lower() in title.lower()
                        or asset.lower() in news_data[title]["description"].lower()
                    ):
                        asset_sentiments[asset].append(scores["compound"])

            aggregated = {}
            for asset, compounds in asset_sentiments.items():
                if compounds:
                    aggregated[asset] = {
                        "avg_compound": sum(compounds) / len(compounds),
                        "count": len(compounds),
                    }
                else:
                    aggregated[asset] = {"avg_compound": 0.0, "count": 0}
                logger.info(f"Aggregated sentiment for {asset}: {aggregated[asset]}")
            return aggregated
        except Exception as e:
            logger.error(f"Error aggregating sentiment: {str(e)}")
            return {asset: {"avg_compound": 0.0, "count": 0} for asset in assets}
