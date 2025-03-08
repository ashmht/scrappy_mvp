import logging
import pandas as pd
import numpy as np  # Use numpy.nan instead of NaN

logger = logging.getLogger(__name__)


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI manually using pandas and numpy."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)  # Avoid division by zero
    rsi = 100 - (100 / (1 + rs))
    return rsi


class TradingSignalDetector:
    def __init__(self, market_data: dict[str, dict]) -> None:
        self.market_data = market_data

    def detect_opportunities(self) -> dict[str, str]:
        logger.info("Detecting trading opportunities with manual RSI")
        opportunities = {}
        for asset, data in self.market_data.items():
            if "daily_history" in data and len(data["daily_history"]) >= 14:
                df = pd.DataFrame(data["daily_history"], columns=["Close"])
                rsi_series = calculate_rsi(df["Close"], period=14)
                rsi = rsi_series.iloc[-1]
                if pd.notna(rsi):
                    if rsi > 70:
                        opportunities[asset] = "Momentum (Overbought)"
                    elif rsi < 30:
                        opportunities[asset] = "Momentum (Oversold)"
                    else:
                        opportunities[asset] = "No signal"
                else:
                    opportunities[asset] = "No signal (insufficient data)"
            else:
                opportunities[asset] = "No signal (insufficient history)"
        return opportunities
