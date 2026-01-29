import yfinance as yf
import pandas_ta_classic as ta
import requests
import config

from datetime import datetime, timedelta

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

def generate_suggestion(data, sentiment=0.0):
    """
    Generates a 'call', 'put', or 'hold' suggestion based on technical indicators and sentiment.
    """
    latest_data = data.iloc[-1]

    # Bullish Signal (Suggest Call)
    if latest_data['SMA_50'] > latest_data['SMA_200'] and latest_data['RSI_14'] < 70 and latest_data['Close'] > latest_data['SMA_50'] and sentiment > 0.15:
        return "Call"

    # Bearish Signal (Suggest Put)
    if latest_data['SMA_50'] < latest_data['SMA_200'] and latest_data['RSI_14'] > 30 and latest_data['Close'] < latest_data['SMA_50'] and sentiment < -0.15:
        return "Put"

    return "Hold"


def get_sentiment(ticker):
    """
    Fetches sentiment data for a given ticker from Alpha Vantage.
    """
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={config.ALPHA_VANTAGE_API_KEY}"
    try:
        r = requests.get(url)
        r.raise_for_status()  # Raise an exception for bad status codes
        data = r.json()
        if "feed" in data:
            # crude sentiment score calculation
            sentiment_score = 0
            for item in data['feed']:
                sentiment_score += float(item.get('overall_sentiment_score', 0.0))
            if data['feed']:
                return sentiment_score / len(data['feed'])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sentiment data: {e}")
    except ValueError:
        print("Error parsing sentiment data JSON.")

    return 0.0 # Neutral sentiment if API fails or no data


def get_option_chain(ticker):
    """
    Fetches the option chain for a given ticker.
    """
    stock = yf.Ticker(ticker)
    return stock.option_chain

def find_options_contracts(ticker, suggestion):

    """

    Finds a suitable options contract based on the suggestion and risk management rules.

    Returns the contract and its expiration date.

    """

    stock = yf.Ticker(ticker)

    expirations = stock.options



    if not expirations:

        return None, None



    max_cost = 20



    # Find a suitable expiration date

    today = datetime.now()

    future_expirations = [exp for exp in expirations if datetime.strptime(exp, '%Y-%m-%d') > today]

    

    if not future_expirations:

        return None, None



    # Find the first expiration at least 30 days out

    target_expiration = None

    for exp_str in future_expirations:

        exp_date = datetime.strptime(exp_str, '%Y-%m-%d')

        if exp_date > today + timedelta(days=28):

            target_expiration = exp_str

            break



    if not target_expiration:

        return None, None



    if suggestion == "Call":

        options = stock.option_chain(target_expiration).calls

        # Find the first out-of-the-money call that fits our budget

        otm_calls = options[(options['inTheMoney'] == False) & (options['lastPrice'] * 100 <= max_cost)]

        if not otm_calls.empty:

            return otm_calls.iloc[0], target_expiration

    elif suggestion == "Put":

        options = stock.option_chain(target_expiration).puts

        # Find the first out-of-the-money put that fits our budget

        otm_puts = options[(options['inTheMoney'] == False) & (options['lastPrice'] * 100 <= max_cost)]

        if not otm_puts.empty:

            return otm_puts.iloc[0], target_expiration



    return None, None





if __name__ == '__main__':

    # Example usage:

    ticker = "AAPL"

    stock_data = get_stock_data(ticker)

    if stock_data is not None:

        sentiment = get_sentiment(ticker)
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

