import streamlit as st
from datetime import datetime
from analysis import get_stock_data, generate_suggestion, get_sentiment, find_options_contracts, get_company_news, calculate_news_sentiment, get_advanced_data, calculate_analyst_sentiment, run_backtest

st.set_page_config(page_title="Stock Market Agent", layout="wide")
st.title("📈 Stock Market Agent")

# --- Initialization & State ---
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None

def set_selected_ticker(ticker):
    """Sets the ticker in session state."""
    st.session_state.selected_ticker = ticker

# --- Sidebar Navigation & Input ---
with st.sidebar:
    st.title("Navigation")
    page = st.radio("Go to", ["Live Analysis", "Backtesting"])
    st.markdown("---")

    if page == "Live Analysis":
        st.header("Analyze New Ticker")
        new_ticker = st.text_input("Stock Ticker Symbol", "AAPL").upper()
        max_option_cost = st.number_input("Max Option Cost ($)", min_value=1, value=20, step=5)
        st.button("Analyze Stock", type="primary", on_click=set_selected_ticker, args=(new_ticker,))

if page == "Live Analysis":
    # --- Main Layout ---
    col1, col2 = st.columns([1, 3]) # Left column for watchlist, Right for analysis

    # --- Watchlist Column ---
    with col1:
        st.header("Watchlist")
        
        # Add Ticker UI
        new_wl_ticker = st.text_input("Add Ticker", placeholder="MSFT").upper()
        if st.button("Add"):
            if new_wl_ticker:
                with open("watchlist.txt", "a") as f:
                    f.write(f"\n{new_wl_ticker}")
                st.rerun()

        with open("watchlist.txt") as f:
            watchlist = [line.strip() for line in f if line.strip()]

        if watchlist:
            with st.container(height=600):
                for ticker_symbol in watchlist:
                    if st.button(ticker_symbol, key=ticker_symbol, use_container_width=True):
                        set_selected_ticker(ticker_symbol)

    # --- Analysis Column ---
    with col2:
        if st.session_state.selected_ticker:
            ticker = st.session_state.selected_ticker
            st.header(f"Analysis for {ticker}")
            
            with st.spinner(f"Analyzing {ticker}..."):
                stock_data = get_stock_data(ticker)
                
                if stock_data is not None:
                    sentiment, sentiment_error = get_sentiment(ticker)
                    
                    sentiment_for_suggestion = sentiment
                    sentiment_display = f"{sentiment:.2f}"

                    if sentiment_error:
                        st.warning(sentiment_error)
                        sentiment_for_suggestion = None # Use None to signal sentiment-agnostic analysis
                        sentiment_display = "N/A"

                    # Get Company News & Calculate Sentiment
                    news = get_company_news(ticker)
                    news_score = calculate_news_sentiment(news)

                    # Get Advanced Data (Financials, Recommendations, etc.)
                    adv_data = get_advanced_data(ticker)
                    analyst_score = calculate_analyst_sentiment(adv_data.get('recommendations'))
                    
                    # Generate Suggestion with all sentiment sources
                    suggestion = generate_suggestion(stock_data, sentiment=sentiment_for_suggestion, news_sentiment=news_score, analyst_sentiment=analyst_score)
                    
                    # Display Metrics
                    m_col1, m_col2, m_col3 = st.columns(3)
                    m_col1.metric("Suggestion", suggestion, delta=None if suggestion == "Hold" else suggestion)
                    m_col2.metric("Current Price", f"${stock_data['Close'].iloc[-1]:.2f}")
                    
                    combined_display = f"AV: {sentiment_display} | News: {news_score:.2f} | Analyst: {f'{analyst_score:.2f}' if analyst_score is not None else 'N/A'}"
                    m_col3.metric("Sentiment Scores", combined_display)

                    # Chart
                    st.subheader("Price History (1 Year)")
                    st.line_chart(stock_data['Close'])

                    # Option Contract
                    if suggestion in ["Call", "Put"]:
                        st.subheader(f"Top 5 Suggested {suggestion} Options")
                        contracts, expiration = find_options_contracts(ticker, suggestion, max_cost=max_option_cost, underlying_price=stock_data['Close'].iloc[-1])
                        
                        if contracts is not None and not contracts.empty:
                            st.dataframe(contracts[['contractSymbol', 'strike', 'lastPrice', 'Breakeven', 'PoP', 'Risk Level', 'Reasoning', 'volume', 'openInterest', 'impliedVolatility']].astype(str), hide_index=True)
                            st.caption(f"Expiration: {expiration}")
                        else:
                            st.warning(f"No suitable {suggestion} contract found under ${max_option_cost}.")

                    # --- Advanced Data Display ---
                    st.markdown("---")
                    st.subheader("Fundamental & Institutional Data")
                    
                    # 1. Key Metrics
                    if adv_data.get('metrics') and 'metric' in adv_data['metrics']:
                        metrics = adv_data['metrics']['metric']
                        mc1, mc2, mc3, mc4 = st.columns(4)
                        mc1.metric("P/E Ratio", f"{metrics.get('peTTM', 'N/A')}")
                        mc2.metric("EPS (TTM)", f"{metrics.get('epsTTM', 'N/A')}")
                        mc3.metric("52W High", f"{metrics.get('52WeekHigh', 'N/A')}")
                        mc4.metric("52W Low", f"{metrics.get('52WeekLow', 'N/A')}")
                    
                    # 2. Analyst Recommendations
                    if adv_data.get('recommendations'):
                        rec = adv_data['recommendations'][0]
                        st.write(f"**Analyst Consensus ({rec.get('period', 'Latest')}):** Buy: {rec.get('buy')} | Hold: {rec.get('hold')} | Sell: {rec.get('sell')}")
                    
                    # 3. Government & Institutional
                    col_gov1, col_gov2 = st.columns(2)
                    with col_gov1:
                        st.write("**Senate Lobbying (Last 1 Year)**")
                        lobbying = adv_data.get('lobbying')
                        if lobbying and 'data' in lobbying and lobbying['data']:
                            for item in lobbying['data'][:3]:
                                st.text(f"{item.get('name')}: {item.get('description')}")
                        else:
                            st.caption("No recent lobbying data found.")

                    with col_gov2:
                        st.write("**USA Spending (Gov Contracts)**")
                        spending = adv_data.get('usa_spending')
                        if spending and 'data' in spending and spending['data']:
                            for item in spending['data'][:3]:
                                amount = item.get('amount')
                                amount_str = f"${amount:,.2f}" if amount is not None else "N/A"
                                st.text(f"{item.get('agencyName')} - {amount_str}")
                        else:
                            st.caption("No recent government spending data found.")

                    # 4. Filings & Financials (Expanders)
                    with st.expander("Recent SEC Filings"):
                        filings = adv_data.get('filings')
                        if filings:
                            for f in filings[:5]:
                                st.markdown(f"[{f.get('form')}]({f.get('filingUrl')}) - {f.get('filedDate')}")
                        else:
                            st.write("No filings found.")

                    # Company News
                    st.subheader("Recent Company News")
                    if news:
                        for item in news[:5]:
                            st.markdown(f"**[{item['headline']}]({item['url']})**")
                            st.caption(f"{datetime.fromtimestamp(item['datetime']).strftime('%Y-%m-%d %H:%M')} - {item['source']}")
                            st.write(item['summary'])
                    else:
                        st.info("No recent news found.")
                else:
                    st.error(f"Could not fetch data for {ticker}. Please check the symbol.")
        else:
            st.info("Select a ticker from the watchlist or enter one in the sidebar to see the analysis.")

elif page == "Backtesting":
    st.header("Strategy Backtesting")
    st.markdown("Validate the technical analysis strategy on historical data.")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        bt_ticker = st.text_input("Ticker", "AAPL", key="bt_ticker").upper()
        bt_period = st.selectbox("Period", ["1y", "2y", "5y", "10y"], index=1)
    with col_b2:
        initial_capital = st.number_input("Initial Capital", value=10000, step=1000)
        
    if st.button("Run Backtest"):
        with st.spinner(f"Backtesting {bt_ticker} over {bt_period}..."):
            trades, equity = run_backtest(bt_ticker, bt_period, initial_capital)
            
            if trades is not None and not trades.empty:
                # Summary Metrics
                final_equity = equity['Equity'].iloc[-1]
                total_return = (final_equity - initial_capital) / initial_capital
                win_rate = len(trades[trades['PnL'] > 0]) / len(trades) if len(trades) > 0 else 0
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Return", f"{total_return:.2%}", delta=f"${final_equity - initial_capital:,.2f}")
                m2.metric("Final Equity", f"${final_equity:,.2f}")
                m3.metric("Win Rate", f"{win_rate:.1%}")
                
                # Equity Curve
                st.subheader("Equity Curve")
                st.line_chart(equity)
                
                # Trade Log
                st.subheader("Trade Log")
                st.dataframe(trades, use_container_width=True)
            else:
                st.warning("No trades generated or insufficient data.")