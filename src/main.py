import argparse
from src.analysis import get_stock_data, generate_suggestion, get_sentiment, get_company_news, calculate_news_sentiment, get_advanced_data, calculate_analyst_sentiment

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
        sentiment, _ = get_sentiment(ticker)
        
        news = get_company_news(ticker)
        news_score = calculate_news_sentiment(news)
        
        adv_data = get_advanced_data(ticker)
        analyst_score = calculate_analyst_sentiment(adv_data.get('recommendations'))
        
        suggestion = generate_suggestion(stock_data, sentiment=sentiment, news_sentiment=news_score, analyst_sentiment=analyst_score)
        print(f"Alpha Vantage Sentiment: {sentiment:.2f}")
        print(f"News Sentiment: {news_score:.2f}")
        print(f"Analyst Sentiment: {analyst_score:.2f}" if analyst_score is not None else "Analyst Sentiment: N/A")
        print(f"Suggestion for {ticker}: {suggestion}")

        if suggestion in ["Call", "Put"]:
            print("Finding a suitable contract...")
            from src.analysis import find_options_contracts
            contracts, expiration_date = find_options_contracts(ticker, suggestion, underlying_price=stock_data['Close'].iloc[-1])
            
            if contracts is not None and not contracts.empty:
                print(f"\n--- Top 5 Suggested {suggestion} Options (Exp: {expiration_date}) ---")
                for _, contract in contracts.iterrows():
                    print(f"Symbol: {contract['contractSymbol']}")
                    print(f"Strike: {contract['strike']} | Price: {contract['lastPrice']} | Breakeven: {contract['Breakeven']:.2f}")
                    print(f"PoP: {contract['PoP']}")
                    print(f"Risk: {contract['Risk Level']}")
                    print(f"Reasoning: {contract['Reasoning']}")
                    print(f"Vol/OI: {contract['volume']}/{contract['openInterest']}")
                    print("---------------------------------")
            else:
                print("Could not find a suitable options contract.")

if __name__ == "__main__":
    main()
