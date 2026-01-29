import argparse
from analysis import get_stock_data, generate_suggestion, get_sentiment

def main():
    """
    Main function to run the CLI.
    """
    parser = argparse.ArgumentParser(description="Get a stock option suggestion.")
    parser.add_argument("--stock", type=str, required=True, help="Stock ticker symbol (e.g., AAPL)")
    args = parser.parse_args()

    ticker = args.stock.upper()
    print(f"Analyzing {ticker}...")
    stock_data = get_stock_data(ticker)

    if stock_data is not None:
        sentiment = get_sentiment(ticker)
        suggestion = generate_suggestion(stock_data, sentiment)
        print(f"Sentiment for {ticker}: {sentiment:.2f}")
        print(f"Suggestion for {ticker}: {suggestion}")

        if suggestion in ["Call", "Put"]:
            print("Finding a suitable contract...")
            from analysis import find_options_contracts
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

if __name__ == "__main__":
    main()
