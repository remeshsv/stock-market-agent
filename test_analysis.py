import sys
import os
import pytest

# Add the parent directory to sys.path to allow importing modules from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import calculate_news_sentiment, calculate_delta

def test_calculate_news_sentiment():
    """Test the sentiment calculation logic with mocked news items."""
    
    # Case 1: Clearly positive news
    # Words like 'surge', 'profit', 'growth' are in the positive_words set
    positive_news = [
        {'headline': 'Stock price surge', 'summary': 'Record profit and growth reported.'}
    ]
    assert calculate_news_sentiment(positive_news) == 1.0

    # Case 2: Clearly negative news
    # Words like 'drop', 'loss', 'decline' are in the negative_words set
    negative_news = [
        {'headline': 'Market drop', 'summary': 'Huge loss and decline in revenue.'}
    ]
    assert calculate_news_sentiment(negative_news) == -1.0

    # Case 3: Mixed news (one positive, one negative)
    mixed_news = [
        {'headline': 'Profit up', 'summary': 'Good growth'}, # Score: +1
        {'headline': 'Loss down', 'summary': 'Bad decline'}  # Score: -1
    ]
    # Average of 1 and -1 is 0
    assert calculate_news_sentiment(mixed_news) == 0.0

    # Case 4: Empty list
    assert calculate_news_sentiment([]) == 0.0

def test_calculate_delta():
    """Test the Black-Scholes Delta calculation."""
    # Parameters: S=100, K=100, T=1 year, r=5%, sigma=20%
    S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
    
    # Call Delta for ATM option should be roughly 0.5 (usually > 0.5 due to positive interest rates)
    call_delta = calculate_delta(S, K, T, r, sigma, "Call")
    assert 0.5 < call_delta < 0.7
    
    # Put Delta should be Call Delta - 1 (Put-Call Parity relationship for Delta)
    put_delta = calculate_delta(S, K, T, r, sigma, "Put")
    assert abs(put_delta - (call_delta - 1)) < 1e-9
    
    # Test invalid inputs (e.g., negative time) return 0.0
    assert calculate_delta(S, K, -1, r, sigma, "Call") == 0.0