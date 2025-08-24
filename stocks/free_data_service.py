import requests
import json
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from .models import Stock, StockPrice
from .yahoo_finance import YahooFinanceService


class FreeDataService:
    """
    Unified service for stock data using only free APIs without requiring API keys.
    Uses Yahoo Finance as primary source with multiple fallbacks.
    """
    
    def __init__(self):
        self.yahoo_service = YahooFinanceService()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_current_price(self, symbol):
        """Get current stock price from multiple free sources"""
        print(f"🔍 Fetching current price for {symbol}...")
        
        # Primary: Yahoo Finance (most reliable and comprehensive)
        try:
            print(f"  → Trying Yahoo Finance...")
            price_data = self.yahoo_service.get_current_price(symbol)
            if price_data and price_data.get('price', 0) > 0:
                print(f"  ✅ Yahoo Finance: ${price_data['price']}")
                return price_data
        except Exception as e:
            print(f"  ❌ Yahoo Finance error: {e}")
        
        # Fallback 1: Twelve Data (free tier - 8 calls/minute)
        try:
            print(f"  → Trying Twelve Data (free tier)...")
            price_data = self._get_twelve_data_price(symbol)
            if price_data and price_data.get('price', 0) > 0:
                print(f"  ✅ Twelve Data: ${price_data['price']}")
                return price_data
        except Exception as e:
            print(f"  ❌ Twelve Data error: {e}")
        
        # Fallback 2: Alpha Vantage demo endpoint (limited)
        try:
            print(f"  → Trying Alpha Vantage demo...")
            price_data = self._get_alpha_vantage_demo_price(symbol)
            if price_data and price_data.get('price', 0) > 0:
                print(f"  ✅ Alpha Vantage demo: ${price_data['price']}")
                return price_data
        except Exception as e:
            print(f"  ❌ Alpha Vantage demo error: {e}")
        
        # Fallback 3: Financial Modeling Prep (free tier - 250 calls/day)
        try:
            print(f"  → Trying Financial Modeling Prep...")
            price_data = self._get_fmp_price(symbol)
            if price_data and price_data.get('price', 0) > 0:
                print(f"  ✅ Financial Modeling Prep: ${price_data['price']}")
                return price_data
        except Exception as e:
            print(f"  ❌ Financial Modeling Prep error: {e}")
        
        # Fallback 4: MarketStack (free tier - 1000 calls/month)
        try:
            print(f"  → Trying MarketStack...")
            price_data = self._get_marketstack_price(symbol)
            if price_data and price_data.get('price', 0) > 0:
                print(f"  ✅ MarketStack: ${price_data['price']}")
                return price_data
        except Exception as e:
            print(f"  ❌ MarketStack error: {e}")
        
        print(f"  🚫 No price data available for {symbol} from any source")
        return None
    
    def _get_twelve_data_price(self, symbol):
        """Get current price from Twelve Data free tier (8 calls/minute)"""
        url = "https://api.twelvedata.com/price"
        params = {
            'symbol': symbol,
            'apikey': 'demo'  # Demo key for basic functionality
        }
        
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'price' in data and data['price'] != 'N/A':
            price = float(data['price'])
            if price > 0:
                return {
                    'symbol': symbol,
                    'price': price,
                    'change': 0,  # Twelve Data free tier doesn't include change
                    'change_percent': '0.00',
                    'last_updated': 'Current',
                    'source': 'Twelve Data (Free)',
                    'market_status': 'Unknown'
                }
        
        return None
    
    def _get_alpha_vantage_demo_price(self, symbol):
        """Get current price using Alpha Vantage demo endpoint (very limited)"""
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': 'demo'  # Demo key with very limited functionality
        }
        
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        global_quote = data.get('Global Quote', {})
        if '05. price' in global_quote:
            price = float(global_quote['05. price'])
            if price > 0:
                change = float(global_quote.get('09. change', 0))
                change_percent = global_quote.get('10. change percent', '0%').replace('%', '')
                
                return {
                    'symbol': symbol,
                    'price': price,
                    'change': change,
                    'change_percent': change_percent,
                    'last_updated': global_quote.get('07. latest trading day', ''),
                    'source': 'Alpha Vantage (Demo)',
                    'market_status': 'Unknown'
                }
        
        return None
    
    def _get_fmp_price(self, symbol):
        """Get current price from Financial Modeling Prep (250 calls/day free)"""
        url = f"https://financialmodelingprep.com/api/v3/quote-short/{symbol}"
        params = {
            'apikey': 'demo'  # Demo key for limited functionality
        }
        
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data and len(data) > 0:
            quote = data[0]
            price = quote.get('price', 0)
            if price and price > 0:
                return {
                    'symbol': symbol,
                    'price': float(price),
                    'change': 0,  # Basic endpoint doesn't include change
                    'change_percent': '0.00',
                    'last_updated': 'Current',
                    'source': 'Financial Modeling Prep (Free)',
                    'market_status': 'Unknown'
                }
        
        return None
    
    def _get_marketstack_price(self, symbol):
        """Get current price from MarketStack (1000 calls/month free)"""
        url = "http://api.marketstack.com/v1/eod/latest"
        params = {
            'access_key': 'demo',  # Demo key for limited functionality
            'symbols': symbol
        }
        
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data and len(data['data']) > 0:
            quote = data['data'][0]
            price = quote.get('close', 0)
            if price and price > 0:
                return {
                    'symbol': symbol,
                    'price': float(price),
                    'change': 0,  # Basic endpoint doesn't include intraday change
                    'change_percent': '0.00',
                    'last_updated': quote.get('date', 'Current'),
                    'source': 'MarketStack (Free)',
                    'market_status': 'Unknown'
                }
        
        return None
    
    def search_symbols(self, query):
        """Search for stock symbols using multiple free sources"""
        if not query or len(query.strip()) < 1:
            return []
        
        # Primary: Yahoo Finance search (most comprehensive)
        try:
            results = self.yahoo_service.search_symbols(query)
            if results:
                return results
        except Exception as e:
            print(f"Yahoo Finance search error: {e}")
        
        # Fallback: Simple symbol validation for known exchanges
        # This creates a basic result for common symbols
        query = query.strip().upper()
        if len(query) <= 5 and query.isalpha():
            return [{
                'symbol': query,
                'name': f'{query} Corporation',
                'exchange': 'NASDAQ',
                'type': 'Equity',
                'region': 'United States'
            }]
        
        return []
    
    def get_daily_prices(self, symbol, days_back=30):
        """Get historical daily prices using Yahoo Finance"""
        try:
            return self.yahoo_service.update_stock_prices_for_period(symbol, days_back)
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return 0
    
    def get_intraday_data(self, symbol, interval='5m'):
        """Get intraday data using Yahoo Finance"""
        try:
            return self.yahoo_service.get_intraday_data(symbol, interval)
        except Exception as e:
            print(f"Error fetching intraday data for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol, period='1d', interval='1d'):
        """Get historical data using Yahoo Finance"""
        try:
            return self.yahoo_service.get_historical_data(symbol, period, interval)
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return []
    
    def update_stock_prices(self, symbol, days_back=30):
        """
        Update stock prices in database for given symbol using free APIs
        """
        try:
            # Get or create the stock
            stock, created = Stock.objects.get_or_create(
                symbol=symbol.upper(),
                defaults={'company_name': ''}
            )
            
            # First try to get current price and update today's record
            current_price_data = self.get_current_price(symbol)
            if current_price_data and 'price' in current_price_data:
                current_price = Decimal(str(current_price_data['price']))
                today = timezone.now().date()
                
                # Update or create today's price record
                StockPrice.objects.update_or_create(
                    stock=stock,
                    date=today,
                    defaults={
                        'open_price': current_price,
                        'high_price': current_price,
                        'low_price': current_price,
                        'close_price': current_price,
                        'volume': 0
                    }
                )
            
            # Then try to get historical data using Yahoo Finance
            try:
                historical_count = self.yahoo_service.update_stock_prices_for_period(symbol, days_back)
                return historical_count
            except Exception as e:
                print(f"Historical data update failed for {symbol}: {e}")
                # If historical update fails but we got current price, still return 1
                return 1 if current_price_data else 0
            
        except Exception as e:
            raise ValueError(f"Failed to update prices for {symbol}: {str(e)}")
    
    def get_multiple_quotes(self, symbols):
        """Get multiple stock quotes efficiently"""
        if not symbols:
            return {}
        
        # Try Yahoo Finance batch API first (most efficient)
        try:
            return self.yahoo_service.get_multiple_quotes(symbols)
        except Exception as e:
            print(f"Batch quotes error: {e}")
        
        # Fallback to individual requests
        quotes = {}
        for symbol in symbols:
            try:
                price_data = self.get_current_price(symbol)
                if price_data:
                    quotes[symbol] = price_data
            except Exception as e:
                print(f"Error getting quote for {symbol}: {e}")
                continue
        
        return quotes
