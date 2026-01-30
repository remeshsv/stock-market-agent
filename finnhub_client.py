import finnhub
import config

def get_finnhub_client():
    """
    Initializes and returns a Finnhub client.
    """
    return finnhub.Client(api_key=config.FINNHUB_API_KEY)
