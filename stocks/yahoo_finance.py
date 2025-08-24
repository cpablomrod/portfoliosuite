import requests
import json
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone


class YahooFinanceService:
    """Service to interact with Yahoo Finance API for real-time stock data"""
    
    BASE_URL = "https://query1.finance.yahoo.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_current_price(self, symbol):
        """Get current stock price from Yahoo Finance"""
        try:
            # Use Yahoo Finance chart API for real-time quotes
            url = f"{self.BASE_URL}/v8/finance/chart/{symbol}"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Parse the response
            chart_result = data.get('chart', {}).get('result', [])
            if not chart_result:
                raise ValueError("No chart data found")
            
            meta = chart_result[0].get('meta', {})
            
            # Extract price information
            current_price = meta.get('regularMarketPrice')
            prev_close = meta.get('previousClose', current_price)
            market_state = meta.get('marketState', 'REGULAR')  # REGULAR, PRE, POST, CLOSED
            
            if current_price is None or current_price <= 0:
                raise ValueError("Invalid price data")
            
            # Calculate change and percentage change
            change = current_price - prev_close if prev_close else 0
            change_pct = (change / prev_close * 100) if prev_close and prev_close > 0 else 0
            
            # Get market time info
            market_time = meta.get('regularMarketTime')
            last_updated = 'Live'
            if market_time:
                try:
                    # Convert timestamp to readable format
                    dt = datetime.fromtimestamp(market_time)
                    last_updated = dt.strftime('%I:%M %p')
                except:
                    pass
            
            # Determine if market is open or closed
            if market_state == 'REGULAR':
                market_status = 'Open'
            elif market_state in ['PRE', 'POST']:
                market_status = f'{market_state.title()}-Market'
            else:
                market_status = 'Closed'
            
            return {
                'symbol': symbol,
                'price': float(current_price),
                'change': float(change),
                'change_percent': f"{change_pct:.2f}",
                'prev_close': float(prev_close) if prev_close else 0,
                'market_state': market_state,
                'market_status': market_status,
                'last_updated': last_updated,
                'source': 'Yahoo Finance',
                'currency': meta.get('currency', 'USD'),
                'exchange': meta.get('exchangeName', 'Unknown')
            }
            
        except Exception as e:
            raise ValueError(f"Yahoo Finance API error for {symbol}: {str(e)}")
    
    def get_multiple_quotes(self, symbols):
        """Get quotes for multiple symbols at once (more efficient)"""
        if not symbols or len(symbols) == 0:
            return {}
        
        # Yahoo Finance supports multiple symbols in one request
        symbols_str = ','.join(symbols)
        url = f"{self.BASE_URL}/v7/finance/quote"
        params = {'symbols': symbols_str}
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            quotes = {}
            quote_response = data.get('quoteResponse', {}).get('result', [])
            
            for quote in quote_response:
                symbol = quote.get('symbol')
                if not symbol:
                    continue
                
                current_price = quote.get('regularMarketPrice')
                prev_close = quote.get('regularMarketPreviousClose', current_price)
                
                if current_price and current_price > 0:
                    change = current_price - prev_close if prev_close else 0
                    change_pct = (change / prev_close * 100) if prev_close and prev_close > 0 else 0
                    
                    # Get market time
                    market_time = quote.get('regularMarketTime')
                    last_updated = 'Live'
                    if market_time:
                        try:
                            dt = datetime.fromtimestamp(market_time)
                            last_updated = dt.strftime('%I:%M %p')
                        except:
                            pass
                    
                    market_state = quote.get('marketState', 'REGULAR')
                    if market_state == 'REGULAR':
                        market_status = 'Open'
                    elif market_state in ['PRE', 'POST']:
                        market_status = f'{market_state.title()}-Market'
                    else:
                        market_status = 'Closed'
                    
                    quotes[symbol] = {
                        'symbol': symbol,
                        'price': float(current_price),
                        'change': float(change),
                        'change_percent': f"{change_pct:.2f}",
                        'prev_close': float(prev_close) if prev_close else 0,
                        'market_state': market_state,
                        'market_status': market_status,
                        'last_updated': last_updated,
                        'source': 'Yahoo Finance',
                        'currency': quote.get('currency', 'USD'),
                        'exchange': quote.get('fullExchangeName', 'Unknown')
                    }
            
            return quotes
            
        except Exception as e:
            print(f"Error fetching multiple quotes: {str(e)}")
            return {}
    
    def get_intraday_data(self, symbol, interval='5m'):
        """Get intraday price data for today (like Google Finance 1D chart)"""
        try:
            # Get today's intraday data
            from datetime import datetime, timedelta
            
            # Calculate today's trading session timestamps
            now = datetime.now()
            # Start from market open (9:30 AM ET) or beginning of today if before market open
            if now.hour < 9 or (now.hour == 9 and now.minute < 30):
                # If before market open, show previous trading day
                start_time = int((now - timedelta(days=1)).replace(hour=9, minute=30, second=0, microsecond=0).timestamp())
            else:
                # Show today's data from market open
                start_time = int(now.replace(hour=9, minute=30, second=0, microsecond=0).timestamp())
            
            end_time = int(now.timestamp())
            
            url = f"{self.BASE_URL}/v8/finance/chart/{symbol}"
            params = {
                'period1': start_time,
                'period2': end_time,
                'interval': interval,  # 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h
                'includePrePost': 'true',
                'events': 'div,splits'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            chart_result = data.get('chart', {}).get('result', [])
            if not chart_result:
                raise ValueError("No intraday data found")
            
            result = chart_result[0]
            timestamps = result.get('timestamp', [])
            indicators = result.get('indicators', {}).get('quote', [{}])[0]
            
            # Extract OHLC data
            opens = indicators.get('open', [])
            highs = indicators.get('high', [])
            lows = indicators.get('low', [])
            closes = indicators.get('close', [])
            volumes = indicators.get('volume', [])
            
            # Prepare data in the format expected by views
            datetime_list = []
            price_list = []
            
            for i, timestamp in enumerate(timestamps):
                if i < len(closes) and closes[i] is not None:
                    dt = datetime.fromtimestamp(timestamp)
                    datetime_list.append(dt)
                    price_list.append(float(closes[i]))
            
            return {
                'timestamps': datetime_list,
                'prices': price_list,
                'count': len(price_list)
            }
            
        except Exception as e:
            print(f"Error fetching intraday data for {symbol}: {str(e)}")
            return None
    
    def get_historical_data(self, symbol, period='1d', interval='1d'):
        """Get historical price data"""
        try:
            # Calculate timestamps for the period
            end_time = int(datetime.now().timestamp())
            
            if period == '1d':
                start_time = end_time - 86400  # 1 day
            elif period == '1w':
                start_time = end_time - (7 * 86400)  # 1 week
            elif period == '1mo':
                start_time = end_time - (30 * 86400)  # 1 month
            elif period == '3mo':
                start_time = end_time - (90 * 86400)  # 3 months
            elif period == '1y':
                start_time = end_time - (365 * 86400)  # 1 year
            else:
                start_time = end_time - 86400  # Default to 1 day
            
            url = f"{self.BASE_URL}/v8/finance/chart/{symbol}"
            params = {
                'period1': start_time,
                'period2': end_time,
                'interval': interval,
                'includePrePost': 'true'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            chart_result = data.get('chart', {}).get('result', [])
            if not chart_result:
                raise ValueError("No historical data found")
            
            result = chart_result[0]
            timestamps = result.get('timestamp', [])
            indicators = result.get('indicators', {}).get('quote', [{}])[0]
            
            # Extract OHLCV data
            opens = indicators.get('open', [])
            highs = indicators.get('high', [])
            lows = indicators.get('low', [])
            closes = indicators.get('close', [])
            volumes = indicators.get('volume', [])
            
            historical_data = []
            for i, timestamp in enumerate(timestamps):
                if i < len(closes) and closes[i] is not None:
                    date = datetime.fromtimestamp(timestamp).date()
                    historical_data.append({
                        'date': date,
                        'open': opens[i] if i < len(opens) and opens[i] else closes[i],
                        'high': highs[i] if i < len(highs) and highs[i] else closes[i],
                        'low': lows[i] if i < len(lows) and lows[i] else closes[i],
                        'close': closes[i],
                        'volume': volumes[i] if i < len(volumes) and volumes[i] else 0
                    })
            
            return historical_data
            
        except Exception as e:
            raise ValueError(f"Error fetching historical data for {symbol}: {str(e)}")
    
    def search_symbols(self, query):
        """Search for stock symbols"""
        if not query or len(query.strip()) < 1:
            return []
        
        try:
            url = f"{self.BASE_URL}/v1/finance/search"
            params = {
                'q': query.strip(),
                'quotesCount': 10,
                'newsCount': 0
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            quotes = data.get('quotes', [])
            results = []
            
            for quote in quotes:
                if quote.get('typeDisp') == 'Equity':  # Only show stocks
                    results.append({
                        'symbol': quote.get('symbol', ''),
                        'name': quote.get('longname') or quote.get('shortname', ''),
                        'exchange': quote.get('exchange', ''),
                        'type': quote.get('typeDisp', 'Equity'),
                        'region': 'United States' if quote.get('exchange', '').endswith('Q') or 'NAS' in quote.get('exchange', '') else 'Other'
                    })
            
            return results[:10]  # Limit to 10 results
            
        except Exception as e:
            print(f"Error searching symbols: {str(e)}")
            return []
    
    def update_stock_prices_for_period(self, symbol, days_back):
        """Update stock prices for a given period using historical data"""
        from .models import Stock, StockPrice
        from django.utils import timezone
        from datetime import timedelta
        
        try:
            # Get or create stock
            stock, _ = Stock.objects.get_or_create(
                symbol=symbol,
                defaults={'company_name': ''}
            )
            
            # Calculate the period
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            # Fetch historical data from Yahoo Finance
            # Map days to appropriate period
            if days_back <= 7:
                period = '1w'
                interval = '1d'
            elif days_back <= 30:
                period = '1mo'
                interval = '1d'
            elif days_back <= 90:
                period = '3mo'
                interval = '1d'
            else:
                period = '1y'
                interval = '1d'
            
            historical_data = self.get_historical_data(symbol, period, interval)
            
            if not historical_data:
                print(f"No historical data returned for {symbol}")
                return 0
            
            updated_count = 0
            
            # Update database with historical prices
            for data_point in historical_data:
                date = data_point['date']
                
                # Only update prices within our target range
                if start_date <= date <= end_date:
                    # Check if price already exists for this date
                    existing_price = StockPrice.objects.filter(
                        stock=stock,
                        date=date
                    ).first()
                    
                    if not existing_price:
                        # Create new price record
                        StockPrice.objects.create(
                            stock=stock,
                            date=date,
                            open_price=data_point['open'],
                            high_price=data_point['high'],
                            low_price=data_point['low'],
                            close_price=data_point['close'],
                            volume=data_point['volume']
                        )
                        updated_count += 1
                        print(f"Added price for {symbol} on {date}: ${data_point['close']}")
            
            print(f"Updated {updated_count} price records for {symbol}")
            return updated_count
            
        except Exception as e:
            print(f"Error updating prices for {symbol}: {str(e)}")
            return 0
