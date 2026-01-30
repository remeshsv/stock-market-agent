# 📈 Stock Market Agent

A comprehensive stock market analysis tool powered by Python, Streamlit, and AI-driven sentiment analysis. This agent provides real-time technical analysis, news sentiment, fundamental data, and options trading suggestions.

## 🚀 Features

*   **Live Analysis Dashboard**: Interactive Streamlit interface for analyzing stock tickers.
*   **Technical Analysis**: Automatically calculates RSI, SMA (50/200), and generates Buy/Sell/Hold signals.
*   **Sentiment Analysis**:
    *   **Alpha Vantage**: News sentiment scoring.
    *   **Finnhub**: Company news aggregation and custom sentiment scoring.
    *   **Analyst Ratings**: Consensus recommendations from Wall Street analysts.
*   **Options Intelligence**:
    *   Suggests specific Call/Put contracts based on analysis.
    *   Calculates **Probability of Profit (PoP)** using Delta approximation.
    *   Filters for liquidity (Open Interest) and risk levels.
*   **Fundamental Data**: Displays P/E ratios, EPS, SEC filings, Senate lobbying, and Government spending contracts.
*   **Backtesting Engine**: Validate the technical strategy against historical data with equity curves and trade logs.
*   **Watchlist**: Persistent watchlist to track favorite tickers.
*   **CLI Support**: Run quick analyses directly from the terminal.

## 🛠️ Tech Stack

*   **Frontend**: [Streamlit](https://streamlit.io/)
*   **Data Sources**:
    *   [yfinance](https://pypi.org/project/yfinance/) (Market Data & Options)
    *   [Finnhub API](https://finnhub.io/) (News, Fundamentals, Filings)
    *   [Alpha Vantage](https://www.alphavantage.co/) (Sentiment)
*   **Analysis**:
    *   `pandas` & `pandas_ta` (Technical Indicators)
    *   `numpy` & `math` (Black-Scholes Delta Calculation)

## ⚙️ Setup & Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd stock-market-agent
```

### 2. Create a Virtual Environment
It is recommended to use a virtual environment to manage dependencies.
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
*Note: Ensure you have `streamlit`, `yfinance`, `pandas`, `pandas_ta_classic`, `finnhub-python`, `requests`, and `scipy` (or `numpy`) installed.*

### 4. Configuration
Create a `.env` file in the root directory to store your API keys:

```ini
ALPHA_VANTAGE_API_KEY=YOUR_ALPHA_VANTAGE_KEY
FINNHUB_API_KEY=YOUR_FINNHUB_KEY
```

## 🖥️ Usage

### Running the Dashboard
Launch the interactive web interface:
```bash
streamlit run app.py
```
Open your browser to `http://localhost:8501`.

### Running the CLI
Perform a quick analysis from the command line:
```bash
python main.py --stock AAPL
```

## 📂 Project Structure

*   **`app.py`**: Main Streamlit application entry point. Handles UI, navigation, and display logic.
*   **`analysis.py`**: Core logic engine. Contains functions for:
    *   Fetching stock data (`get_stock_data`)
    *   Calculating technical indicators
    *   Generating suggestions (`generate_suggestion`)
    *   Options chain logic (`find_options_contracts`)
    *   Backtesting engine (`run_backtest`)
*   **`main.py`**: Command-line interface wrapper.
*   **`finnhub_client.py`**: Helper for initializing the Finnhub API client.
*   **`watchlist.txt`**: Text file storing the user's watchlist.

## ⚠️ Disclaimer

This tool is for **informational and educational purposes only**. It does not constitute financial advice.
*   The "Probability of Profit" (PoP) is a theoretical approximation based on Delta.
*   Backtesting results do not guarantee future performance.
*   Always do your own due diligence before trading.
```

<!--
[PROMPT_SUGGESTION]Create a requirements.txt file based on the imports in the code.[/PROMPT_SUGGESTION]
[PROMPT_SUGGESTION]Add a section to the README about how the "Probability of Profit" is calculated.[/PROMPT_SUGGESTION]
-->