import requests
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from .models import Stock, StockPrice
from .yahoo_finance import YahooFinanceService
from .free_data_service import FreeDataService


class StockDataService:
    """Service to interact with free stock data APIs (no API key required)"""
    
    def __init__(self):
        self.free_service = FreeDataService()
    
    def get_current_price(self, symbol):
        """Get current stock price using free APIs (no API key required)"""
        return self.free_service.get_current_price(symbol)
    
    def search_symbols(self, keywords):
        """Search for stock symbols using free APIs"""
        return self.free_service.search_symbols(keywords)
    
    def update_stock_prices(self, symbol, days_back=30):
        """Update stock prices in database using free APIs"""
        return self.free_service.update_stock_prices(symbol, days_back)
    
    def get_multiple_quotes(self, symbols):
        """Get multiple stock quotes efficiently using free APIs"""
        return self.free_service.get_multiple_quotes(symbols)
    
    def get_daily_prices(self, symbol, days_back=30):
        """Get historical daily prices using free APIs"""
        return self.free_service.get_daily_prices(symbol, days_back)
    
    def get_intraday_data(self, symbol, interval='5m'):
        """Get intraday data using free APIs"""
        return self.free_service.get_intraday_data(symbol, interval)
    
    def get_historical_data(self, symbol, period='1d', interval='1d'):
        """Get historical data using free APIs"""
        return self.free_service.get_historical_data(symbol, period, interval)


class PortfolioAnalytics:
    """Service for portfolio analysis and metrics"""
    
    @staticmethod
    def get_portfolio_summary(portfolio_name='My Investment Portfolio'):
        """Get overall portfolio summary for a specific portfolio"""
        from django.db.models import Sum, F, Q
        from .models import Portfolio
        
        # Get all buy transactions for this portfolio
        buy_transactions = Portfolio.objects.filter(transaction_type='BUY', portfolio_name=portfolio_name)
        
        # Get all sell transactions for this portfolio
        sell_transactions = Portfolio.objects.filter(transaction_type='SELL', portfolio_name=portfolio_name)
        
        # Calculate total invested (buys) and total received (sells)
        total_invested = buy_transactions.aggregate(
            total=Sum(F('quantity') * F('price_per_share'))
        )['total'] or Decimal('0.00')
        
        total_received = sell_transactions.aggregate(
            total=Sum(F('quantity') * F('price_per_share'))
        )['total'] or Decimal('0.00')
        
        # Get unique companies in current portfolio (only companies with current positions)
        # We need to count companies that have positive net positions
        current_positions = PortfolioAnalytics.get_stock_positions(portfolio_name)
        companies_count = len(current_positions)
        
        return {
            'total_invested': total_invested,
            'total_received': total_received,
            'net_invested': total_invested - total_received,
            'companies_count': companies_count,
            'total_transactions': Portfolio.objects.filter(portfolio_name=portfolio_name).count()
        }
    
    @staticmethod
    def get_stock_positions(portfolio_name='My Investment Portfolio'):
        """Get current stock positions for a specific portfolio"""
        from django.db.models import Sum, F
        from .models import Portfolio
        
        # Calculate net positions for each stock in this portfolio
        positions = []
        stocks = Portfolio.objects.filter(portfolio_name=portfolio_name).values('stock__symbol', 'stock__company_name').distinct()
        
        for stock_info in stocks:
            symbol = stock_info['stock__symbol']
            company_name = stock_info['stock__company_name']
            
            # Calculate total bought
            bought = Portfolio.objects.filter(
                stock__symbol=symbol,
                transaction_type='BUY',
                portfolio_name=portfolio_name
            ).aggregate(
                total_quantity=Sum('quantity'),
                total_value=Sum(F('quantity') * F('price_per_share'))
            )
            
            # Calculate total sold
            sold = Portfolio.objects.filter(
                stock__symbol=symbol,
                transaction_type='SELL',
                portfolio_name=portfolio_name
            ).aggregate(
                total_quantity=Sum('quantity'),
                total_value=Sum(F('quantity') * F('price_per_share'))
            )
            
            # Calculate net position
            net_quantity = (bought['total_quantity'] or Decimal('0')) - (sold['total_quantity'] or Decimal('0'))
            net_value = (bought['total_value'] or Decimal('0')) - (sold['total_value'] or Decimal('0'))
            
            if net_quantity > 0:  # Only include positions we still hold
                avg_cost = net_value / net_quantity if net_quantity > 0 else Decimal('0')
                
                positions.append({
                    'symbol': symbol,
                    'company_name': company_name,
                    'quantity': net_quantity,
                    'avg_cost': avg_cost,
                    'total_cost': net_value,
                })
        
        return positions
    
    @staticmethod
    def get_detailed_holdings(portfolio_name='My Investment Portfolio'):
        """Get detailed holdings information for the table"""
        from django.db.models import Sum, F, Min
        from django.utils import timezone
        from datetime import timedelta
        from .models import Portfolio, StockPrice
        
        holdings = []
        
        # Get all stocks with transactions for this portfolio
        stocks_with_transactions = Portfolio.objects.filter(
            portfolio_name=portfolio_name
        ).values(
            'stock__symbol', 
            'stock__company_name'
        ).distinct()
        
        # Calculate total portfolio value for weight calculation
        total_portfolio_value = Decimal('0')
        positions = PortfolioAnalytics.get_stock_positions(portfolio_name)
        
        for position in positions:
            # Get current price
            latest_price = StockPrice.objects.filter(
                stock__symbol=position['symbol']
            ).order_by('-date').first()
            
            if latest_price:
                current_value = position['quantity'] * latest_price.close_price
                total_portfolio_value += current_value
        
        for stock_info in stocks_with_transactions:
            symbol = stock_info['stock__symbol']
            company_name = stock_info['stock__company_name']
            
            # Get position data
            position = next((p for p in positions if p['symbol'] == symbol), None)
            if not position or position['quantity'] <= 0:
                continue
            
            # Get first purchase date
            first_purchase = Portfolio.objects.filter(
                stock__symbol=symbol,
                transaction_type='BUY'
            ).order_by('transaction_date').first()
            
            # Get current price
            latest_price = StockPrice.objects.filter(
                stock__symbol=symbol
            ).order_by('-date').first()
            
            # Calculate current price per share and weight
            current_price_per_share = None
            performance_pct = None
            weight_pct = Decimal('0')
            
            if latest_price:
                current_price_per_share = latest_price.close_price
                performance_pct = ((latest_price.close_price - position['avg_cost']) / position['avg_cost']) * 100
                
                # Calculate total value for weight calculation
                total_value_for_weight = position['quantity'] * latest_price.close_price
                if total_portfolio_value > 0:
                    weight_pct = (total_value_for_weight / total_portfolio_value) * 100
            
            # Calculate time owned
            time_owned = "N/A"
            if first_purchase:
                days_owned = (timezone.now().date() - first_purchase.transaction_date).days
                if days_owned < 30:
                    time_owned = f"{days_owned} days"
                elif days_owned < 365:
                    months = days_owned // 30
                    time_owned = f"{months} month{'s' if months != 1 else ''}"
                else:
                    years = days_owned // 365
                    remaining_months = (days_owned % 365) // 30
                    time_owned = f"{years}y {remaining_months}m" if remaining_months > 0 else f"{years} year{'s' if years != 1 else ''}"
            
            holdings.append({
                'symbol': symbol,
                'company_name': company_name or symbol,
                'purchase_date': first_purchase.transaction_date if first_purchase else 'N/A',
                'weight_pct': weight_pct,
                'entry_price': position['avg_cost'],
                'current_value': current_price_per_share,
                'performance_pct': performance_pct,
                'time_owned': time_owned
            })
        
        # Sort by weight (largest positions first)
        holdings.sort(key=lambda x: x['weight_pct'], reverse=True)
        
        return holdings
    
    @staticmethod
    def get_upcoming_earnings(portfolio_name='My Investment Portfolio'):
        """Get upcoming earnings dates for portfolio stocks"""
        from django.utils import timezone
        from datetime import timedelta, datetime
        from .models import Portfolio
        
        # Get current positions for this portfolio
        positions = PortfolioAnalytics.get_stock_positions(portfolio_name)
        
        if not positions:
            return []
        
        earnings = []
        current_date = timezone.now().date()
        current_year = current_date.year
        current_quarter = (current_date.month - 1) // 3 + 1
        
        # Realistic earnings calendar data for major stocks
        EARNINGS_CALENDAR = {
            # Technology companies - mostly report in Q4: Oct-Jan, Q1: Jan-Apr, Q2: Apr-Jul, Q3: Jul-Oct
            'AAPL': {'quarters': [1, 2, 3, 4], 'months': [1, 4, 7, 10], 'days': [26, 25, 25, 26]},
            'MSFT': {'quarters': [1, 2, 3, 4], 'months': [1, 4, 7, 10], 'days': [24, 23, 24, 24]},
            'GOOGL': {'quarters': [1, 2, 3, 4], 'months': [2, 4, 7, 10], 'days': [2, 25, 25, 26]},
            'GOOG': {'quarters': [1, 2, 3, 4], 'months': [2, 4, 7, 10], 'days': [2, 25, 25, 26]},
            'META': {'quarters': [1, 2, 3, 4], 'months': [2, 4, 7, 10], 'days': [1, 26, 27, 25]},
            'TSLA': {'quarters': [1, 2, 3, 4], 'months': [1, 4, 7, 10], 'days': [25, 24, 24, 25]},
            'NVDA': {'quarters': [1, 2, 3, 4], 'months': [2, 5, 8, 11], 'days': [22, 24, 24, 22]},
            'AMZN': {'quarters': [1, 2, 3, 4], 'months': [2, 4, 7, 10], 'days': [2, 27, 26, 26]},
            
            # Financial companies
            'JPM': {'quarters': [1, 2, 3, 4], 'months': [1, 4, 7, 10], 'days': [15, 15, 15, 15]},
            'BAC': {'quarters': [1, 2, 3, 4], 'months': [1, 4, 7, 10], 'days': [17, 17, 17, 17]},
            'BRK-A': {'quarters': [1, 2, 3, 4], 'months': [2, 5, 8, 11], 'days': [25, 4, 5, 4]},
            'BRK-B': {'quarters': [1, 2, 3, 4], 'months': [2, 5, 8, 11], 'days': [25, 4, 5, 4]},
            'BRK.A': {'quarters': [1, 2, 3, 4], 'months': [2, 5, 8, 11], 'days': [25, 4, 5, 4]},
            'BRK.B': {'quarters': [1, 2, 3, 4], 'months': [2, 5, 8, 11], 'days': [25, 4, 5, 4]},
            'V': {'quarters': [1, 2, 3, 4], 'months': [2, 4, 7, 10], 'days': [1, 26, 26, 26]},
            
            # Industrial companies
            'DE': {'quarters': [1, 2, 3, 4], 'months': [2, 5, 8, 11], 'days': [20, 20, 20, 20]},
            'CAT': {'quarters': [1, 2, 3, 4], 'months': [1, 4, 7, 10], 'days': [31, 30, 31, 28]},
            'BA': {'quarters': [1, 2, 3, 4], 'months': [1, 4, 7, 10], 'days': [31, 24, 24, 23]},
            'GE': {'quarters': [1, 2, 3, 4], 'months': [1, 4, 7, 10], 'days': [23, 25, 26, 26]},
            
            # REITs and Real Estate
            'O': {'quarters': [1, 2, 3, 4], 'months': [2, 5, 8, 11], 'days': [15, 15, 15, 15]},
            'AMT': {'quarters': [1, 2, 3, 4], 'months': [2, 4, 7, 10], 'days': [28, 26, 26, 26]},
            
            # Healthcare
            'JNJ': {'quarters': [1, 2, 3, 4], 'months': [1, 4, 7, 10], 'days': [21, 16, 16, 17]},
            'PFE': {'quarters': [1, 2, 3, 4], 'months': [2, 5, 7, 10], 'days': [1, 1, 30, 29]},
        }
        
        for position in positions:
            symbol = position['symbol']
            
            # Get earnings schedule for this symbol
            schedule = EARNINGS_CALENDAR.get(symbol)
            if not schedule:
                # Default quarterly schedule for unknown stocks
                schedule = {'quarters': [1, 2, 3, 4], 'months': [2, 4, 7, 10], 'days': [15, 15, 15, 15]}
            
            # Find next earnings date
            next_earnings_date = None
            for i, quarter in enumerate(schedule['quarters']):
                month = schedule['months'][i]
                day = schedule['days'][i]
                
                # Try current year first
                try:
                    earnings_date = datetime(current_year, month, day).date()
                    if earnings_date >= current_date:
                        next_earnings_date = earnings_date
                        break
                except ValueError:
                    # Handle invalid dates (like Feb 30)
                    earnings_date = datetime(current_year, month, min(day, 28)).date()
                    if earnings_date >= current_date:
                        next_earnings_date = earnings_date
                        break
            
            # If no date found in current year, use first quarter of next year
            if not next_earnings_date:
                try:
                    next_earnings_date = datetime(current_year + 1, schedule['months'][0], schedule['days'][0]).date()
                except ValueError:
                    next_earnings_date = datetime(current_year + 1, schedule['months'][0], 28).date()
            
            # Calculate time until earnings
            days_until = (next_earnings_date - current_date).days
            if days_until <= 7:
                time_until = f"{days_until} day{'s' if days_until != 1 else ''}"
            elif days_until <= 30:
                weeks = days_until // 7
                time_until = f"{weeks} week{'s' if weeks != 1 else ''}"
            else:
                months = days_until // 30
                time_until = f"{months} month{'s' if months != 1 else ''}"
            
            earnings.append({
                'symbol': symbol,
                'company_name': symbol,  # Use symbol as company name for simplicity
                'earnings_date': next_earnings_date.strftime('%m/%d/%Y'),
                'time_until': time_until,
                'days_until': days_until
            })
        
        # Sort by earnings date (soonest first)
        earnings.sort(key=lambda x: x['days_until'])
        
        return earnings  # Return all earnings dates
    
    @staticmethod
    def get_upcoming_dividends(portfolio_name='My Investment Portfolio'):
        """Get upcoming dividend information for portfolio stocks"""
        from django.utils import timezone
        from datetime import timedelta, datetime
        from .models import Portfolio
        
        # Get current positions for this portfolio
        positions = PortfolioAnalytics.get_stock_positions(portfolio_name)
        
        if not positions:
            return []
        
        dividends = []
        current_date = timezone.now().date()
        current_year = current_date.year
        current_month = current_date.month
        
        # Realistic dividend calendar data for major dividend-paying stocks
        DIVIDEND_CALENDAR = {
            # High dividend yield stocks with known dividend schedules
            'O': {
                'type': 'monthly',
                'yield_pct': 5.8,
                'months': list(range(1, 13)),
                'ex_date_day': 15,
                'quarterly_amount': 0.25
            },
            'AAPL': {
                'type': 'quarterly',
                'yield_pct': 0.5,
                'months': [2, 5, 8, 11],  # Feb, May, Aug, Nov
                'ex_date_day': 10,
                'quarterly_amount': 0.24
            },
            'MSFT': {
                'type': 'quarterly',
                'yield_pct': 0.7,
                'months': [2, 5, 8, 11],  # Feb, May, Aug, Nov
                'ex_date_day': 15,
                'quarterly_amount': 0.75
            },
            'JPM': {
                'type': 'quarterly',
                'yield_pct': 2.8,
                'months': [1, 4, 7, 10],  # Jan, Apr, Jul, Oct
                'ex_date_day': 5,
                'quarterly_amount': 1.05
            },
            'BAC': {
                'type': 'quarterly',
                'yield_pct': 2.9,
                'months': [3, 6, 9, 12],  # Mar, Jun, Sep, Dec
                'ex_date_day': 3,
                'quarterly_amount': 0.24
            },
            'BRK-B': {
                'type': 'none',  # Berkshire doesn't pay dividends
                'yield_pct': 0.0,
                'months': [],
                'ex_date_day': 0,
                'quarterly_amount': 0.0
            },
            'BRK.B': {
                'type': 'none',  # Berkshire doesn't pay dividends
                'yield_pct': 0.0,
                'months': [],
                'ex_date_day': 0,
                'quarterly_amount': 0.0
            },
            'BRK-A': {
                'type': 'none',  # Berkshire doesn't pay dividends
                'yield_pct': 0.0,
                'months': [],
                'ex_date_day': 0,
                'quarterly_amount': 0.0
            },
            'BRK.A': {
                'type': 'none',  # Berkshire doesn't pay dividends
                'yield_pct': 0.0,
                'months': [],
                'ex_date_day': 0,
                'quarterly_amount': 0.0
            },
            'V': {
                'type': 'quarterly',
                'yield_pct': 0.7,
                'months': [3, 6, 9, 12],  # Mar, Jun, Sep, Dec
                'ex_date_day': 10,
                'quarterly_amount': 0.52
            },
            'DE': {
                'type': 'quarterly',
                'yield_pct': 1.3,
                'months': [3, 6, 9, 12],  # Mar, Jun, Sep, Dec
                'ex_date_day': 25,
                'quarterly_amount': 1.40
            },
            'CAT': {
                'type': 'quarterly',
                'yield_pct': 2.2,
                'months': [2, 5, 8, 11],  # Feb, May, Aug, Nov
                'ex_date_day': 20,
                'quarterly_amount': 1.30
            },
            'JNJ': {
                'type': 'quarterly',
                'yield_pct': 2.9,
                'months': [3, 6, 9, 12],  # Mar, Jun, Sep, Dec
                'ex_date_day': 8,
                'quarterly_amount': 1.19
            },
            'PFE': {
                'type': 'quarterly',
                'yield_pct': 5.8,
                'months': [2, 5, 8, 11],  # Feb, May, Aug, Nov
                'ex_date_day': 7,
                'quarterly_amount': 0.42
            },
            'AMT': {
                'type': 'quarterly',
                'yield_pct': 3.1,
                'months': [1, 4, 7, 10],  # Jan, Apr, Jul, Oct
                'ex_date_day': 12,
                'quarterly_amount': 1.56
            },
            # Google/Alphabet started paying dividends in 2024
            'GOOGL': {
                'type': 'quarterly',
                'yield_pct': 0.41,
                'months': [3, 6, 9, 12],  # Mar, Jun, Sep, Dec
                'ex_date_day': 10,
                'quarterly_amount': 0.20
            },
            'GOOG': {
                'type': 'quarterly',
                'yield_pct': 0.41,
                'months': [3, 6, 9, 12],  # Mar, Jun, Sep, Dec
                'ex_date_day': 10,
                'quarterly_amount': 0.20
            },
            # Other non-dividend paying stocks
            'TSLA': {'type': 'none', 'yield_pct': 0.0, 'months': [], 'ex_date_day': 0, 'quarterly_amount': 0.0},
            'META': {'type': 'none', 'yield_pct': 0.0, 'months': [], 'ex_date_day': 0, 'quarterly_amount': 0.0},
            'NVDA': {'type': 'quarterly', 'yield_pct': 0.1, 'months': [3, 6, 9, 12], 'ex_date_day': 8, 'quarterly_amount': 0.04},
            'AMZN': {'type': 'none', 'yield_pct': 0.0, 'months': [], 'ex_date_day': 0, 'quarterly_amount': 0.0},
        }
        
        for position in positions:
            symbol = position['symbol']
            quantity = position['quantity']
            
            # Get dividend schedule for this symbol
            div_info = DIVIDEND_CALENDAR.get(symbol)
            if not div_info or div_info['type'] == 'none':
                # Default for stocks without known dividend schedule (assume no dividend)
                continue
            
            # Find next dividend date
            next_dividend_date = None
            dividend_amount = 0.0
            
            if div_info['type'] == 'monthly':
                # For monthly dividends (like O - Realty Income)
                dividend_amount = div_info['quarterly_amount'] / 3  # Monthly = quarterly/3
                # Find next month's ex-dividend date
                for month_offset in range(12):  # Look ahead 12 months
                    test_month = current_month + month_offset
                    test_year = current_year
                    if test_month > 12:
                        test_month -= 12
                        test_year += 1
                    
                    try:
                        test_date = datetime(test_year, test_month, div_info['ex_date_day']).date()
                        if test_date >= current_date:
                            next_dividend_date = test_date
                            break
                    except ValueError:
                        # Handle invalid dates
                        continue
            
            elif div_info['type'] == 'quarterly':
                dividend_amount = div_info['quarterly_amount']
                # Find next quarterly dividend date
                for month in div_info['months']:
                    # Check current year first
                    try:
                        test_date = datetime(current_year, month, div_info['ex_date_day']).date()
                        if test_date >= current_date:
                            next_dividend_date = test_date
                            break
                    except ValueError:
                        continue
                
                # If no date found in current year, check next year
                if not next_dividend_date:
                    try:
                        next_dividend_date = datetime(current_year + 1, div_info['months'][0], div_info['ex_date_day']).date()
                    except ValueError:
                        continue
            
            if next_dividend_date and dividend_amount > 0:
                expected_amount = quantity * Decimal(str(dividend_amount))
                
                # Calculate days until ex-dividend date
                days_until = (next_dividend_date - current_date).days
                
                dividends.append({
                    'symbol': symbol,
                    'yield_pct': Decimal(str(div_info['yield_pct'])),
                    'expected_amount': expected_amount,
                    'dividend_per_share': Decimal(str(dividend_amount)),
                    'ex_date': next_dividend_date.strftime('%m/%d/%Y'),
                    'days_until': days_until,
                    'frequency': div_info['type']
                })
        
        # Sort by ex-dividend date (soonest first)
        dividends.sort(key=lambda x: x['days_until'])
        
        return dividends  # Return all upcoming dividends
