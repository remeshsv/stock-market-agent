import os

def test_alpha_vantage_key_exists():
    """Verify that the Alpha Vantage API key is set in the environment."""
    assert os.getenv('ALPHA_VANTAGE_API_KEY'), "Alpha Vantage key not found"

def test_finnhub_key_exists():
    """Verify that the Finnhub API key is set in the environment."""
    assert os.getenv('FINNHUB_API_KEY'), "Finnhub key not found"