# Scrappy MVP Trading Idea Generator

Welcome to the **Scrappy MVP Trading Idea Generator**, a real-time stock analysis tool designed to identify trading opportunities based on market data, sentiment analysis, and dynamic stock summaries. Built with Python and powered by Streamlit, this application fetches trending stocks (focusing on the biggest losers of the day), analyzes their sentiment, detects trading signals, and sends customizable email alerts to multiple recipients.

## Overview

The Scrappy MVP leverages APIs (e.g., FinancialModelingPrep, Yahoo Finance) to provide:

- Real-time stock prices, volume, and price charts.
- Sentiment analysis of news articles.
- Trading signals (e.g., "Buy - Momentum (Oversold)").
- Dynamic company summaries (description, sector, S&P 500 status).
- Email alerts with HTML formatting for actionable insights.

The app is designed for traders and investors looking to spot undervalued or overbought stocks with high potential, focusing on stocks with significant daily losses, refined by sentiment and volatility metrics.

## Features

- **Dynamic Asset Selection**: Uses `AssetFinder` to fetch the top 10 biggest losers of the day from FMP and selects the top 5 based on sentiment, volatility, and P/E ratio.
- **Interactive Dashboard**: Displays stock data, charts, sentiment, news, and summaries in a user-friendly Streamlit interface.
- **Sentiment Analysis**: Analyzes news sentiment using a custom `SentimentAnalyzer`.
- **Trading Signals**: Detects opportunities (e.g., oversold, overbought) via `TradingSignalDetector`.
- **Email Alerts**: Sends HTML-formatted alerts to multiple recipients with stock details, summaries, and dashboard links, triggered by customizable thresholds.
- **Caching**: Implements `@st.cache_data` to cache API calls (e.g., FMP profiles) for 24 hours, optimizing performance during testing.

## Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/your-username/scrappy-mvp-trading.git
   cd scrappy-mvp-trading
   ```

2. **Install Dependencies**:  
   Ensure you have Python 3.8+ installed. Then run:
   ```bash
   pip install -r requirements.txt
   ```

   The `requirements.txt` should include:
   ```
   streamlit
   yfinance
   pandas
   plotly
   requests
   python-dotenv
   ```

3. **Set Up Environment Variables**:  
   Create a `.env` file in the project root with the following:

   ```bash
   FMP_API_KEY=your_financialmodelingprep_api_key
   EMAIL_SENDER=your.email@gmail.com
   EMAIL_PASSWORD=your_gmail_app_password
   EMAIL_RECIPIENTS=recipient1@example.com,recipient2@example.com
   ```

   - **FMP_API_KEY**: Obtain from [FinancialModelingPrep](https://financialmodelingprep.com) (free tier available with 250 calls/day).
   - **EMAIL_SENDER/EMAIL_PASSWORD**: Use a Gmail account with a 2FA-enabled app password (generate via Google Account > Security > App Passwords).
   - **EMAIL_RECIPIENTS**: Comma-separated list of email addresses to receive alerts.

4. **Run the Application**:
   ```bash
   streamlit run app.py
   ```

   Open your browser at [http://localhost:8501](http://localhost:8501) to view the dashboard.

## Usage

### Launch the Dashboard:
The app automatically fetches the top 5 trending stocks based on the biggest losers of the day. Each stock card shows:
- Current price
- Volume
- Price chart
- Trading signal
- Sentiment
- News items
- Summary

### Receive Alerts:
Email alerts are sent when a stock meets the threshold (e.g., **"Oversold"** with sentiment > 0.5 or **"Overbought"** with sentiment < -0.5).  
The email includes an HTML-formatted summary with the stock’s description, sector, and approximate S&P 500 status.

### Customize:
- Adjust alert thresholds in `alert_manager.py` by modifying the `should_alert` condition.
- Add more assets to the fallback list in `asset_finder.py` or `app.py` if needed.

## Project Structure

```
scrappy-mvp-trading/
│
├── src/
│   ├── __init__.py
│   ├── data_ingestion.py       # Fetches market and news data
│   ├── sentiment_analyzer.py   # Analyzes news sentiment
│   ├── trading_detector.py     # Detects trading signals
│   ├── alert_manager.py        # Sends email alerts
│   ├── asset_finder.py         # Selects top stocks
│   └── dashboard.py            # Renders the Streamlit UI
│
├── app.py                      # Main application entry point
├── .env                        # Environment variables (API keys, email config)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
```

## Development Notes:
- **API Limits**: The free FMP tier has a 250 calls/day limit. Monitor usage in logs and consider a paid plan for heavy use.
- **S&P 500 Status**: Currently approximated by market cap (> $10B). For accuracy, integrate an official S&P 500 list (e.g., via web scraping or a paid API).
- **Caching**: Summaries are cached for 24 hours with `@st.cache_data`. Clear the cache manually with `st.cache_data.clear()` if needed.
- **Testing**: Test email alerts with your Gmail app password and adjust recipients in `.env`.

## Contributing:
Feel free to fork this repository and submit pull requests. Suggestions for improvements (e.g., adding more APIs, enhancing UI) are welcome!

## Acknowledgments:
- Built with assistance from **Grok 3**, created by **xAI**.
- Data sourced from **FinancialModelingPrep**, **Yahoo Finance**, and news feeds.
- **Streamlit** for the interactive dashboard.

Thank you for using Scrappy MVP! Let’s make trading smarter together.
```