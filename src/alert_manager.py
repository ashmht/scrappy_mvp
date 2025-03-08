import smtplib
import logging
from email.mime.text import MIMEText
from typing import Dict, List, Any
import os
from dotenv import load_dotenv
import requests

load_dotenv()
logger = logging.getLogger(__name__)

# FMP API key for fetching summaries
FMP_API_KEY = os.getenv("FMP_API_KEY", "demo")


def fetch_company_profile(ticker: str) -> Dict[str, Any]:
    """Fetch company profile data from FMP API."""
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
        sp500_status = "Yes" if market_cap > 10_000_000_000 else "No"

        return {
            "description": description,
            "sector": full_sector,
            "sp500": sp500_status,
        }
    except requests.RequestException as e:
        logger.error(f"Error fetching profile for {ticker}: {str(e)}")
        return {
            "description": f"Error fetching data for {ticker}",
            "sector": "Unknown",
            "sp500": "Unknown",
        }


class AlertManager:
    def __init__(self, email_config: Dict[str, str]) -> None:
        """
        Initialize the AlertManager with email configuration.

        Args:
            email_config: Dict containing 'sender' and 'password' for email.
        """
        self.email_config = email_config
        self.sender = email_config.get("sender", "")
        self.password = email_config.get("password", "")

        # Load recipients from .env (comma-separated list)
        recipients_str = os.getenv("EMAIL_RECIPIENTS", "your_email@example.com")
        self.recipients = [
            email.strip() for email in recipients_str.split(",") if email.strip()
        ]

        if not self.sender or not self.password:
            logger.warning(
                "Email sender or password not provided. Alerts will not be sent."
            )
        if not self.recipients:
            logger.warning("No email recipients provided. Alerts will not be sent.")
        logger.info(f"AlertManager initialized with recipients: {self.recipients}")

    def send_email(self, subject: str, body: str) -> None:
        """Send an HTML email alert to the recipients."""
        if not self.sender or not self.password:
            logger.error("Cannot send email: Sender or password missing.")
            return
        if not self.recipients:
            logger.error("Cannot send email: No recipients specified.")
            return

        # Create HTML email body
        msg = MIMEText(body, "html")
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)

        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(self.sender, self.password)
                server.sendmail(self.sender, self.recipients, msg.as_string())
            logger.info(f"Email sent: {subject} to {self.recipients}")
        except smtplib.SMTPException as e:
            logger.error(f"Failed to send email: {str(e)}")

    def process_alerts(
        self,
        opportunities: Dict[str, str],
        asset_sentiments: Dict[str, Dict[str, float]],
    ) -> None:
        """
        Process trading opportunities and send HTML email alerts based on thresholds.

        Args:
            opportunities: Dict mapping assets to trading signals.
            asset_sentiments: Dict mapping assets to sentiment data.
        """
        logger.info("Processing alerts")
        for asset, signal in opportunities.items():
            sentiment_info = asset_sentiments.get(
                asset, {"avg_compound": 0.0, "count": 0}
            )
            avg_compound = sentiment_info["avg_compound"]
            news_count = sentiment_info["count"]

            # Define alert thresholds
            should_alert = ("Oversold" in signal and avg_compound > 0.5) or (
                "Overbought" in signal and avg_compound < -0.5
            )

            if not should_alert:
                logger.debug(
                    f"No alert for {asset}: Signal={signal}, Sentiment={avg_compound}"
                )
                continue

            # Fetch stock summary
            profile = fetch_company_profile(asset)

            # Determine sentiment color for HTML
            sentiment_label = (
                "Positive"
                if avg_compound > 0
                else "Negative"
                if avg_compound < 0
                else "Neutral"
            )
            sentiment_color = (
                "green" if avg_compound > 0 else "red" if avg_compound < 0 else "gray"
            )
            action_color = "green" if "Oversold" in signal else "red"

            # Load the HTML template from file
            with open("src/email_template.html", "r") as file:
                template = file.read()

            # Construct HTML email content by replacing placeholders
            body = template.format(
                action="Buy" if "Oversold" in signal else "Sell",
                action_color=action_color,
                asset=asset,
                signal=signal,
                sentiment_color=sentiment_color,
                avg_compound=avg_compound,
                sentiment_label=sentiment_label,
                news_count=news_count,
                description=profile["description"],
                sector=profile["sector"],
                sp500=profile["sp500"],
            )

            # Send the email
            subject = f"Trading Alert: {'Buy' if 'Oversold' in signal else 'Sell'} Opportunity for {asset}"
            self.send_email(subject, body)
