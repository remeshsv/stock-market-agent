import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta
import requests
import src.config as config
import streamlit as st
import numpy as np
import math

from datetime import datetime, timedelta

from src.finnhub_client import get_finnhub_client

@st.cache_data
def get_company_news(ticker):
    """
    Fetches company news from Finnhub.
    """
    client = get_finnhub_client()
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    news = client.company_news(ticker, _from=yesterday, to=today)
    return news

def calculate_news_sentiment(news_items):
    """
    Calculates a simple sentiment score from a list of news items.
    Returns a score between -1 and 1.
    """
    if not news_items:
        return 0.0
    
    # Basic sentiment dictionary
    positive_words = {'up', 'rise', 'jump', 'gain', 'bull', 'growth', 'high', 'profit', 'buy', 'outperform', 'positive', 'surge', 'soar'}
    negative_words = {'down', 'fall', 'drop', 'loss', 'bear', 'decline', 'low', 'risk', 'sell', 'underperform', 'negative', 'plunge', 'tumble'}
    
    total_score = 0
    count = 0
    
    for item in news_items:
        # Combine headline and summary
        text = (item.get('headline', '') + ' ' + item.get('summary', '')).lower()
        if not text.strip():
            continue
        
        # Simple presence check
        score = sum(1 for word in positive_words if word in text) - sum(1 for word in negative_words if word in text)
        
        # Normalize individual article score to -1, 0, or 1
        if score > 0:
            total_score += 1
        elif score < 0:
            total_score -= 1
        count += 1
        
    return total_score / count if count > 0 else 0.0

@st.cache_data
def get_advanced_data(ticker):
    """
    Fetches advanced data from Finnhub: Financials, Filings, Metrics, Recommendations, Lobbying, Spending.
    Returns a dictionary with keys corresponding to the data points.
    """
    client = get_finnhub_client()
    data = {}
    
    # Helper to safely call API
    def safe_api_call(call_lambda):
        try:
            return call_lambda()
        except Exception as e:
            print(f"Finnhub API error for {ticker}: {e}")
            return None

    # Dates for lobbying/spending (last 1 year)
    today = datetime.now().strftime('%Y-%m-%d')
    last_year = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

    data['financials'] = safe_api_call(lambda: client.financials_reported(symbol=ticker, freq='quarterly'))
    data['filings'] = safe_api_call(lambda: client.filings(symbol=ticker))
    data['metrics'] = safe_api_call(lambda: client.company_basic_financials(ticker, 'all'))
    data['recommendations'] = safe_api_call(lambda: client.recommendation_trends(ticker))
    data['lobbying'] = safe_api_call(lambda: client.stock_lobbying(ticker, _from=last_year, to=today))
    data['usa_spending'] = safe_api_call(lambda: client.stock_usa_spending(ticker, _from=last_year, to=today))
    
    return data

def calculate_analyst_sentiment(recommendations):
    """
    Converts analyst recommendation trends into a sentiment score (-1 to 1).
    """
    if not recommendations:
        return None
    
    # Use the most recent period. Finnhub usually returns the newest first.
    # Structure is usually a list of dicts.
    if isinstance(recommendations, list) and len(recommendations) > 0:
        latest = recommendations[0]
    else:
        return None
    
    buy = latest.get('buy', 0)
    strong_buy = latest.get('strongBuy', 0)
    hold = latest.get('hold', 0)
    sell = latest.get('sell', 0)
    strong_sell = latest.get('strongSell', 0)
    
    total = buy + strong_buy + hold + sell + strong_sell
    if total == 0:
        return 0.0
    
    # Weighted score: Strong Buy=1, Buy=0.5, Hold=0, Sell=-0.5, Strong Sell=-1
    score = (strong_buy * 1.0 + buy * 0.5 + hold * 0.0 + sell * -0.5 + strong_sell * -1.0) / total
    return score

@st.cache_data
def get_stock_data(ticker):
    """
    Fetches historical stock data and calculates technical indicators.
    """
    # Fetch daily data for the last year
    data = yf.download(ticker, period="1y", interval="1d")
    data.columns = data.columns.get_level_values(0)
    if data.empty:
        print(f"No data found for {ticker}, please check the ticker symbol.")
        return None

    # Calculate technical indicators
    # RSI
    data.ta.rsi(append=True)
    # Simple Moving Averages (50 and 200 days)
    data.ta.sma(length=50, append=True)
    data.ta.sma(length=200, append=True)

    return data

def generate_suggestion(data, sentiment=None, news_sentiment=None, analyst_sentiment=None):
    """
    Generates a 'call', 'put', or 'hold' suggestion based on technical indicators and sentiment.
    If sentiment, news_sentiment, or analyst_sentiment is provided, it incorporates them into the decision.
    """
    latest_data = data.iloc[-1]

    # Bullish Signal
    is_bullish = latest_data['SMA_50'] > latest_data['SMA_200'] and latest_data['RSI_14'] < 70 and latest_data['Close'] > latest_data['SMA_50']
    
    # Bearish Signal
    is_bearish = latest_data['SMA_50'] < latest_data['SMA_200'] and latest_data['RSI_14'] > 30 and latest_data['Close'] < latest_data['SMA_50']

    # Determine effective sentiment (average of available sources)
    sources = [s for s in [sentiment, news_sentiment, analyst_sentiment] if s is not None]
    if sources:
        effective_sentiment = sum(sources) / len(sources)
    else:
        effective_sentiment = None

    if effective_sentiment is not None:
        if is_bullish and effective_sentiment > 0.15:
            return "Call"
        if is_bearish and effective_sentiment < -0.15:
            return "Put"
    else: # Sentiment-agnostic logic
        if is_bullish:
            return "Call"
        if is_bearish:
            return "Put"

    return "Hold"


@st.cache_data
def get_sentiment(ticker):
    """
    Fetches sentiment data for a given ticker from Alpha Vantage.
    Returns a tuple of (sentiment_score, error_message).
    """
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={config.ALPHA_VANTAGE_API_KEY}"
    try:
        r = requests.get(url)
        r.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        data = r.json()

        # Check for API error messages
        if "Information" in data:
            info_message = data['Information']
            if "rate limit" in info_message.lower():
                return 0.0, "Alpha Vantage API Error: Rate limit exceeded."
            else:
                return 0.0, "Alpha Vantage API Error: Please check your API key and try again."
        if "Error Message" in data:
            return 0.0, f"Alpha Vantage API Error: {data['Error Message']}"

        if "feed" in data and data["feed"]:
            sentiment_score = 0
            count = 0
            for item in data['feed']:
                sentiment_score += float(item.get('overall_sentiment_score', 0.0))
                count += 1
            if count > 0:
                return sentiment_score / count, None # Success
            else:
                return 0.0, "No sentiment data found in the API response."

    except requests.exceptions.RequestException as e:
        return 0.0, f"Network error fetching sentiment data: {e}"
    except ValueError: # Catches JSON decoding errors
        return 0.0, "Error parsing sentiment data from Alpha Vantage."

    return 0.0, "Failed to fetch sentiment data for an unknown reason."


@st.cache_data
def get_option_chain(ticker):
    """
    Fetches the option chain for a given ticker.
    """
    stock = yf.Ticker(ticker)
    return stock.option_chain

def calculate_delta(S, K, T, r, sigma, option_type):
    """
    Calculates the Delta of an option using Black-Scholes formula.
    """
    if T <= 0 or sigma <= 0:
        return 0.0
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    
    # Calculate CDF using error function (removes scipy dependency)
    cdf = 0.5 * (1 + math.erf(d1 / math.sqrt(2)))

    if option_type == "Call":
        return cdf
    elif option_type == "Put":
        return cdf - 1
    return 0.0

@st.cache_data
def find_options_contracts(ticker, suggestion, max_cost=20, underlying_price=None):
    """
    Finds a suitable options contract based on the suggestion and risk management rules.
    Prioritizes liquidity (Open Interest) and proximity to current price (Delta proxy).
    Returns the contract and its expiration date.
    """
    stock = yf.Ticker(ticker)

    # Get underlying price if not provided
    if underlying_price is None:
        try:
            history = stock.history(period="1d")
            if not history.empty:
                underlying_price = history['Close'].iloc[-1]
            else:
                return None, None
        except Exception:
            return None, None

    expirations = stock.options
    if not expirations:
        return None, None

    # Find a suitable expiration date (Sweet spot: 3 weeks to ~7 weeks)
    today = datetime.now()
    target_expiration = None
    valid_expirations = []
    
    for exp_str in expirations:
        exp_date = datetime.strptime(exp_str, '%Y-%m-%d')
        days_out = (exp_date - today).days
        
        # Minimum 21 days (3 weeks)
        if days_out >= 21:
            valid_expirations.append(exp_str)
            # Prefer expiration within 50 days to capture the move without paying too much time premium
            if days_out <= 50:
                target_expiration = exp_str
                break
    
    # Fallback: If no "sweet spot" expiration found, take the first one > 21 days
    if not target_expiration and valid_expirations:
        target_expiration = valid_expirations[0]

    if not target_expiration:
        return None, None

    if suggestion == "Call":
        options = stock.option_chain(target_expiration).calls
    elif suggestion == "Put":
        options = stock.option_chain(target_expiration).puts
    else:
        return None, None

    # Filter: Out of the Money AND Within Budget
    candidates = options[(options['inTheMoney'] == False) & (options['lastPrice'] * 100 <= max_cost)].copy()

    if candidates.empty:
        return None, None

    # Calculate Delta for filtering
    exp_date = datetime.strptime(target_expiration, '%Y-%m-%d')
    T = (exp_date - datetime.now()).days / 365.0
    r = 0.045 # Assumption: 4.5% risk-free rate

    def get_delta(row):
        return calculate_delta(underlying_price, row['strike'], T, r, row['impliedVolatility'], suggestion)

    candidates['delta'] = candidates.apply(get_delta, axis=1)

    # Filter out low probability trades (e.g. < 15%) to avoid "lottery tickets"
    candidates = candidates[candidates['delta'].abs() >= 0.15]

    if candidates.empty:
        return None, None

    # --- Calculated Selection Logic ---
    
    # 1. Calculate Distance from Price (Moneyness)
    # We want to avoid deep OTM options if possible, as they have low probability of profit.
    candidates['dist_pct'] = abs(candidates['strike'] - underlying_price) / underlying_price
    
    # 2. Filter for "Reasonable" OTM (e.g., within 15% of current price)
    # If we have candidates within 15%, use them. Otherwise, use whatever is available (deep OTM).
    reasonable_candidates = candidates[candidates['dist_pct'] <= 0.15]
    
    if not reasonable_candidates.empty:
        selection_pool = reasonable_candidates
    else:
        selection_pool = candidates
        
    # 3. Sort by Liquidity (Open Interest)
    # High OI implies tighter spreads and better exit liquidity.
    selection_pool = selection_pool.sort_values(by='openInterest', ascending=False)

    # 4. Select Top 5
    top_contracts = selection_pool.head(5).copy()

    # 5. Add Risk Level & Reasoning
    def analyze_contract(row):
        dist = row['dist_pct']
        if dist < 0.05:
            risk = "Low Risk"
        elif dist < 0.15:
            risk = "Medium Risk"
        else:
            risk = "High Risk"
        
        reasoning = f"High Liquidity (OI: {row['openInterest']}). {risk} play ({dist:.1%} OTM)."
        
        if suggestion == "Call":
            breakeven = row['strike'] + row['lastPrice']
        else:
            breakeven = row['strike'] - row['lastPrice']

        # Calculate Delta / PoP
        delta = row['delta']
        pop = f"{abs(delta):.0%}" # Probability of Profit ~ Delta (approx)

        return pd.Series([risk, reasoning, breakeven, pop], index=['Risk Level', 'Reasoning', 'Breakeven', 'PoP'])

    top_contracts[['Risk Level', 'Reasoning', 'Breakeven', 'PoP']] = top_contracts.apply(analyze_contract, axis=1)

    return top_contracts, target_expiration

def run_backtest(ticker, period="1y", initial_capital=10000):
    """
    Runs a backtest of the technical strategy on historical data.
    """
    # Fetch data
    data = yf.download(ticker, period=period, interval="1d")
    if data.empty:
        return None, "No data found"
    
    # Handle MultiIndex columns if present
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
        
    # Calculate Indicators
    data.ta.rsi(append=True)
    data.ta.sma(length=50, append=True)
    data.ta.sma(length=200, append=True)
    data = data.dropna()
    
    if data.empty:
        return None, "Not enough data for indicators"

    # Backtest Loop
    balance = initial_capital
    position = 0 # 0: None, 1: Long, -1: Short
    entry_price = 0
    shares = 0
    
    trades = []
    equity_curve = []
    
    for index, row in data.iterrows():
        # Strategy Logic (Same as generate_suggestion but purely technical)
        is_bullish = row['SMA_50'] > row['SMA_200'] and row['RSI_14'] < 70 and row['Close'] > row['SMA_50']
        is_bearish = row['SMA_50'] < row['SMA_200'] and row['RSI_14'] > 30 and row['Close'] < row['SMA_50']
        
        # Exit Logic
        if position == 1 and not is_bullish: # Exit Long
            balance += shares * row['Close']
            trades.append({'Date': index, 'Type': 'Sell', 'Price': row['Close'], 'PnL': (row['Close'] - entry_price) * shares})
            position = 0
            shares = 0
        elif position == -1 and not is_bearish: # Exit Short
            # Short covering: Profit = (Entry - Exit) * Shares
            cost = shares * row['Close']
            pnl = (entry_price - row['Close']) * shares
            balance += (shares * entry_price) + pnl # Return margin + profit
            trades.append({'Date': index, 'Type': 'Cover', 'Price': row['Close'], 'PnL': pnl})
            position = 0
            shares = 0
            
        # Entry Logic
        if position == 0:
            if is_bullish:
                shares = balance / row['Close']
                balance -= shares * row['Close']
                entry_price = row['Close']
                position = 1
                trades.append({'Date': index, 'Type': 'Buy', 'Price': row['Close'], 'PnL': 0})
            elif is_bearish:
                # Simulate Short: Assume we can sell 100% equity worth
                shares = balance / row['Close']
                # balance stays as collateral, we track entry
                balance -= shares * row['Close'] # Deduct collateral
                entry_price = row['Close']
                position = -1
                trades.append({'Date': index, 'Type': 'Short', 'Price': row['Close'], 'PnL': 0})
        
        # Mark to Market Equity
        current_equity = balance
        if position == 1:
            current_equity += shares * row['Close']
        elif position == -1:
            current_equity += (shares * entry_price) + ((entry_price - row['Close']) * shares)
            
        equity_curve.append({'Date': index, 'Equity': current_equity})

    return pd.DataFrame(trades), pd.DataFrame(equity_curve).set_index('Date')





if __name__ == '__main__':
    # Example usage:
    ticker = "AAPL"
    stock_data = get_stock_data(ticker)
    if stock_data is not None:
        sentiment, error = get_sentiment(ticker)
        if error:
            print(error)
        else:
            suggestion = generate_suggestion(stock_data, sentiment)
            print(f"Sentiment for {ticker}: {sentiment:.2f}")
            print(f"Suggestion for {ticker}: {suggestion}")

            if suggestion in ["Call", "Put"]:
                contract, expiration_date = find_options_contracts(ticker, suggestion)
                if contract is not None:
                    print("\n--- Suggested Option Contract ---")
                    print(f"Symbol: {contract['contractSymbol']}")
                    print(f"Type: {suggestion}")
                    print(f"Expiration: {expiration_date}")
                    print(f"Strike Price: {contract['strike']}")
                    print(f"Last Price: {contract['lastPrice']}")
                    print(f"Implied Volatility: {contract['impliedVolatility']:.2%}")
                    print("---------------------------------")
                else:
                    print("Could not find a suitable options contract.")

        # Print the last 5 rows of the dataframe with the new indicators
        print(f"\nData for {ticker}:")
        print(stock_data.tail())
