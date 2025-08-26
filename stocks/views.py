from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from .models import Portfolio, Stock, StockPrice
from .forms import AddTransactionForm, SimulationForm
from .services import StockDataService, PortfolioAnalytics


@login_required
def dashboard(request):
    """Main dashboard view"""
    # Get current portfolio name from session or use default
    current_portfolio = request.session.get('current_portfolio', 'My Investment Portfolio')
    
    # Get portfolio summary for current portfolio (filtered by user)
    summary = PortfolioAnalytics.get_portfolio_summary(current_portfolio, request.user)
    
    # Get current positions for current portfolio (filtered by user)
    positions = PortfolioAnalytics.get_stock_positions(current_portfolio, request.user)
    
    # Get recent transactions (filtered by user)
    recent_transactions = Portfolio.objects.filter(user=request.user).select_related('stock').order_by('-created_at')[:10]
    
    # Get current prices for positions - ALWAYS refresh prices on page load
    data_service = StockDataService()
    
    for position in positions:
        symbol = position['symbol']
        try:
            # Always try to fetch current price from APIs
            print(f"\n🔄 Fetching current price for {symbol}...")  # Debug log
            current_price_data = data_service.get_current_price(symbol)
            
            if current_price_data and 'price' in current_price_data:
                current_price = Decimal(str(current_price_data['price']))
                source = current_price_data.get('source', 'Unknown')
                
                print(f"✅ Got price for {symbol}: ${current_price} from {source}")  # Debug log
                
                # Create or update stock price record
                stock, _ = Stock.objects.get_or_create(
                    symbol=symbol,
                    defaults={'company_name': ''}
                )
                
                StockPrice.objects.update_or_create(
                    stock=stock,
                    date=timezone.now().date(),
                    defaults={
                        'open_price': current_price,
                        'high_price': current_price,
                        'low_price': current_price,
                        'close_price': current_price,
                        'volume': 0
                    }
                )
                
                position['current_price'] = current_price
                position['current_value'] = position['quantity'] * current_price
                position['gain_loss'] = position['current_value'] - position['total_cost']
                position['gain_loss_pct'] = (position['gain_loss'] / position['total_cost'] * 100) if position['total_cost'] > 0 else Decimal('0')
                position['price_source'] = source
            else:
                print(f"❌ No current price data for {symbol}, using fallback")  # Debug log
                
                # Fallback to latest stored price if API call returns no data
                latest_price = StockPrice.objects.filter(
                    stock__symbol=symbol
                ).order_by('-date').first()
                
                if latest_price:
                    print(f"📦 Using stored price for {symbol}: ${latest_price.close_price} from {latest_price.date}")
                    position['current_price'] = latest_price.close_price
                    position['current_value'] = position['quantity'] * latest_price.close_price
                    position['gain_loss'] = position['current_value'] - position['total_cost']
                    position['gain_loss_pct'] = (position['gain_loss'] / position['total_cost'] * 100) if position['total_cost'] > 0 else Decimal('0')
                    position['price_source'] = f'Cached ({latest_price.date})'
                else:
                    print(f"❌ No price data available for {symbol}")
                    position['current_price'] = None
                    position['current_value'] = None
                    position['gain_loss'] = None
                    position['gain_loss_pct'] = None
                    position['price_source'] = 'No data'
                    
        except Exception as e:
            print(f"💥 Error fetching price for {symbol}: {str(e)}")  # Debug log
            
            # Fallback to latest stored price if API call fails
            latest_price = StockPrice.objects.filter(
                stock__symbol=symbol
            ).order_by('-date').first()
            
            if latest_price:
                position['current_price'] = latest_price.close_price
                position['current_value'] = position['quantity'] * latest_price.close_price
                position['gain_loss'] = position['current_value'] - position['total_cost']
                position['gain_loss_pct'] = (position['gain_loss'] / position['total_cost'] * 100) if position['total_cost'] > 0 else Decimal('0')
                position['price_source'] = f'Cached ({latest_price.date})'
            else:
                position['current_price'] = None
                position['current_value'] = None
                position['gain_loss'] = None
                position['gain_loss_pct'] = None
                position['price_source'] = 'Error'
    
    # Price updates are fetched silently without notifications
    
    # Get detailed holdings for the table (filtered by user)
    detailed_holdings = PortfolioAnalytics.get_detailed_holdings(current_portfolio, request.user)
    
    # Get upcoming earnings (filtered by user)
    upcoming_earnings = PortfolioAnalytics.get_upcoming_earnings(current_portfolio, request.user)
    
    # Get upcoming dividends (filtered by user)
    upcoming_dividends = PortfolioAnalytics.get_upcoming_dividends(current_portfolio, request.user)
    
    # Get all available portfolio names (filtered by user)
    available_portfolios = Portfolio.objects.filter(user=request.user).values_list('portfolio_name', flat=True).distinct().order_by('portfolio_name')
    
    # Forms
    transaction_form = AddTransactionForm()
    
    context = {
        'summary': summary,
        'positions': positions,
        'recent_transactions': recent_transactions,
        'detailed_holdings': detailed_holdings,
        'upcoming_earnings': upcoming_earnings,
        'upcoming_dividends': upcoming_dividends,
        'transaction_form': transaction_form,
        'current_portfolio': current_portfolio,
        'available_portfolios': available_portfolios,
    }
    
    return render(request, 'stocks/dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def add_transaction(request):
    """Add a new transaction"""
    try:
        # Debug: Log the incoming data
        print(f"DEBUG: Transaction data received: {request.POST}")
        print(f"DEBUG: User: {request.user}")
        print(f"DEBUG: Session portfolio: {request.session.get('current_portfolio')}")
        
        form = AddTransactionForm(request.POST)
        if form.is_valid():
            # Get current portfolio name from session
            current_portfolio = request.session.get('current_portfolio', 'My Investment Portfolio')
            print(f"DEBUG: Portfolio name: {current_portfolio}")
            print(f"DEBUG: Form cleaned data: {form.cleaned_data}")
            
            transaction = form.save(portfolio_name=current_portfolio, user=request.user)
            print(f"DEBUG: Transaction created successfully: {transaction}")
            messages.success(request, f'Transaction added: {transaction.transaction_type} {transaction.quantity} {transaction.stock.symbol}')
        else:
            print(f"DEBUG: Form validation failed: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    except Exception as e:
        # Catch any unexpected errors
        import traceback
        error_msg = str(e)
        traceback_msg = traceback.format_exc()
        print(f"ERROR in add_transaction: {error_msg}")
        print(f"TRACEBACK: {traceback_msg}")
        messages.error(request, f'Error adding transaction: {error_msg}')
    
    return redirect('dashboard')


@login_required
@require_http_methods(["POST"])
def update_prices(request):
    """Update stock prices using free APIs (no API key required)"""
    symbols = request.POST.getlist('symbols')
    if not symbols:
        # Get all symbols from current user's positions
        symbols = Portfolio.objects.filter(user=request.user).values_list('stock__symbol', flat=True).distinct()
    
    data_service = StockDataService()
    updated_count = 0
    
    for symbol in symbols:
        try:
            count = data_service.update_stock_prices(symbol, days_back=7)
            updated_count += count
        except Exception as e:
            messages.error(request, f'Error updating {symbol}: {str(e)}')
    
    if updated_count > 0:
        messages.success(request, f'Updated {updated_count} price records')
    else:
        messages.info(request, 'No new prices to update')
    
    return redirect('dashboard')


@login_required
@require_http_methods(["POST"])
def run_simulation(request):
    """Run a historical simulation"""
    form = SimulationForm(request.POST)
    if form.is_valid():
        symbols = form.cleaned_data['symbols']
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        initial_investment = form.cleaned_data['initial_investment']
        
        try:
            results = _run_historical_simulation(symbols, start_date, end_date, initial_investment)
            
            # Store results in session for display
            request.session['simulation_results'] = {
                'symbols': symbols,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'initial_investment': str(initial_investment),
                'results': results
            }
            
            messages.success(request, f'Simulation completed for {len(symbols)} stocks')
            
        except Exception as e:
            messages.error(request, f'Simulation error: {str(e)}')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{field}: {error}')
    
    return redirect('dashboard')


def _run_historical_simulation(symbols, start_date, end_date, initial_investment):
    """Run historical simulation logic"""
    data_service = StockDataService()
    investment_per_stock = initial_investment / len(symbols)
    
    results = []
    total_final_value = Decimal('0')
    
    for symbol in symbols:
        try:
            # Update prices for this symbol
            data_service.update_stock_prices(symbol, days_back=(end_date - start_date).days + 30)
            
            # Get start and end prices
            start_price_obj = StockPrice.objects.filter(
                stock__symbol=symbol,
                date__gte=start_date
            ).order_by('date').first()
            
            end_price_obj = StockPrice.objects.filter(
                stock__symbol=symbol,
                date__lte=end_date
            ).order_by('-date').first()
            
            if not start_price_obj or not end_price_obj:
                results.append({
                    'symbol': symbol,
                    'error': 'Insufficient price data for simulation period'
                })
                continue
            
            start_price = start_price_obj.close_price
            end_price = end_price_obj.close_price
            
            # Calculate shares and final value
            shares = investment_per_stock / start_price
            final_value = shares * end_price
            gain_loss = final_value - investment_per_stock
            gain_loss_pct = (gain_loss / investment_per_stock) * 100
            
            total_final_value += final_value
            
            results.append({
                'symbol': symbol,
                'start_price': float(start_price),
                'end_price': float(end_price),
                'shares': float(shares),
                'investment': float(investment_per_stock),
                'final_value': float(final_value),
                'gain_loss': float(gain_loss),
                'gain_loss_pct': float(gain_loss_pct),
                'start_date': start_price_obj.date.isoformat(),
                'end_date': end_price_obj.date.isoformat()
            })
            
        except Exception as e:
            results.append({
                'symbol': symbol,
                'error': str(e)
            })
    
    # Calculate overall results
    total_gain_loss = total_final_value - initial_investment
    total_gain_loss_pct = (total_gain_loss / initial_investment) * 100 if initial_investment > 0 else Decimal('0')
    
    return {
        'stocks': results,
        'total_investment': float(initial_investment),
        'total_final_value': float(total_final_value),
        'total_gain_loss': float(total_gain_loss),
        'total_gain_loss_pct': float(total_gain_loss_pct)
    }


@login_required
def chart_data(request):
    """Provide chart data for portfolio performance"""
    period = request.GET.get('period', '1D')
    chart_type = request.GET.get('chart_type', 'portfolio')
    symbol = request.GET.get('symbol', None)  # Get the symbol parameter
    
    try:
        # Get current portfolio name from session
        current_portfolio = request.session.get('current_portfolio', 'My Investment Portfolio')
        
        # Get all stocks in current portfolio (filtered by user)
        positions = PortfolioAnalytics.get_stock_positions(current_portfolio, request.user)
        
        if not positions:
            # Return sample data if no portfolio exists
            return JsonResponse(_get_sample_chart_data(period, chart_type, symbol))
        
        # For 1D period, use intraday data from Yahoo Finance
        if period == '1D':
            if chart_type == 'historical':
                chart_data = _calculate_intraday_stock_prices(positions)
            else:
                chart_data = _calculate_intraday_portfolio_performance(positions)
            return JsonResponse(chart_data)
        
        # For other periods, use daily data
        # Calculate date range based on period
        end_date = timezone.now().date()
        
        if period == '1W':
            start_date = end_date - timedelta(weeks=1)
        elif period == '1M':
            start_date = end_date - timedelta(days=30)
        elif period == '6M':
            start_date = end_date - timedelta(days=180)
        elif period == '1Y':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=7)
        
        # Get chart data based on type
        if chart_type == 'single' and symbol:
            # Get data for a single stock
            chart_data = _calculate_single_stock_price(symbol, start_date, end_date, period)
        elif chart_type == 'historical':
            chart_data = _calculate_historical_stock_prices(positions, start_date, end_date, period)
        else:
            chart_data = _calculate_portfolio_performance(positions, start_date, end_date, period)
        
        return JsonResponse(chart_data)
        
    except Exception as e:
        # Return sample data on error
        return JsonResponse(_get_sample_chart_data(period, chart_type, symbol))


def _calculate_portfolio_performance(positions, start_date, end_date, period):
    """Calculate weighted portfolio performance over time"""
    # Get all unique dates with price data for any stock in the portfolio
    all_dates = set()
    stock_prices = {}
    
    for position in positions:
        symbol = position['symbol']
        prices = StockPrice.objects.filter(
            stock__symbol=symbol,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        stock_prices[symbol] = {p.date: p.close_price for p in prices}
        all_dates.update(stock_prices[symbol].keys())
    
    if not all_dates:
        return _get_sample_chart_data(period)
    
    # Sort dates
    sorted_dates = sorted(all_dates)
    
    # Calculate total portfolio value for each date
    portfolio_values = []
    labels = []
    
    total_investment = sum(position['total_cost'] for position in positions)
    
    for date in sorted_dates:
        daily_value = Decimal('0')
        
        for position in positions:
            symbol = position['symbol']
            if date in stock_prices[symbol]:
                price = stock_prices[symbol][date]
                daily_value += position['quantity'] * price
        
        if daily_value > 0:
            portfolio_values.append(float(daily_value))
            
            # Format label based on period
            if period == '1D':
                labels.append(date.strftime('%H:%M'))
            elif period in ['1W', '1M']:
                labels.append(date.strftime('%m/%d'))
            else:
                labels.append(date.strftime('%b %Y'))
    
    # If we have fewer than 2 data points, return sample data
    if len(portfolio_values) < 2:
        return _get_sample_chart_data(period)
    
    return {
        'labels': labels,
        'values': portfolio_values
    }


def _calculate_historical_stock_prices(positions, start_date, end_date, period):
    """Calculate historical stock prices for each stock in the portfolio"""
    # Get all unique dates with price data for any stock in the portfolio
    all_dates = set()
    stock_prices = {}
    
    # Colors for different stocks
    colors = [
        '#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', 
        '#00f2fe', '#43e97b', '#38f9d7', '#ffecd2', '#fcb69f',
        '#a8edea', '#fed6e3', '#ffeaa7', '#fab1a0', '#74b9ff'
    ]
    
    datasets = []
    
    for i, position in enumerate(positions):
        symbol = position['symbol']
        prices = StockPrice.objects.filter(
            stock__symbol=symbol,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        if prices:
            stock_dates = []
            stock_price_values = []
            
            for price in prices:
                stock_dates.append(price.date)
                stock_price_values.append(float(price.close_price))
                all_dates.add(price.date)
            
            if stock_price_values:
                datasets.append({
                    'label': symbol,
                    'data': stock_price_values,
                    'borderColor': colors[i % len(colors)],
                    'backgroundColor': colors[i % len(colors)] + '20',
                    'borderWidth': 2,
                    'fill': False,
                    'tension': 0.4,
                    'pointRadius': 0,
                    'pointHoverRadius': 4
                })
                
                # Store data for alignment with dates
                stock_prices[symbol] = {
                    'dates': stock_dates,
                    'values': stock_price_values
                }
    
    if not all_dates or not datasets:
        return _get_sample_chart_data(period, 'historical')
    
    # Sort dates
    sorted_dates = sorted(all_dates)
    
    # Align all datasets to the same date range
    aligned_datasets = []
    for dataset in datasets:
        symbol = dataset['label']
        aligned_data = []
        
        for date in sorted_dates:
            # Find the price for this date or the last available price
            price_value = None
            if symbol in stock_prices:
                for j, stock_date in enumerate(stock_prices[symbol]['dates']):
                    if stock_date <= date:
                        price_value = stock_prices[symbol]['values'][j]
                    else:
                        break
            
            if price_value is not None:
                aligned_data.append(price_value)
            else:
                aligned_data.append(None)  # No data available
        
        if aligned_data:
            aligned_datasets.append({
                'label': dataset['label'],
                'data': aligned_data,
                'borderColor': dataset['borderColor'],
                'backgroundColor': dataset['backgroundColor'],
                'borderWidth': dataset['borderWidth'],
                'fill': dataset['fill'],
                'tension': dataset['tension'],
                'pointRadius': dataset['pointRadius'],
                'pointHoverRadius': dataset['pointHoverRadius'],
                'spanGaps': True  # Connect points even if there are null values
            })
    
    # Format labels based on period
    labels = []
    for date in sorted_dates:
        if period == '1D':
            labels.append(date.strftime('%H:%M'))
        elif period in ['1W', '1M']:
            labels.append(date.strftime('%m/%d'))
        else:
            labels.append(date.strftime('%b %Y'))
    
    return {
        'labels': labels,
        'datasets': aligned_datasets
    }


def _calculate_single_stock_price(symbol, start_date, end_date, period):
    """Calculate historical price data for a single stock"""
    # Get price data for the specified stock
    prices = StockPrice.objects.filter(
        stock__symbol=symbol,
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')
    
    if not prices:
        return _get_sample_chart_data(period, 'single', symbol)
    
    # Process price data
    dates = []
    price_values = []
    
    for price in prices:
        dates.append(price.date)
        price_values.append(float(price.close_price))
    
    # Format labels based on period
    labels = []
    for date in dates:
        if period == '1D':
            labels.append(date.strftime('%H:%M'))
        elif period in ['1W', '1M']:
            labels.append(date.strftime('%m/%d'))
        else:
            labels.append(date.strftime('%b %Y'))
    
    # If we have fewer than 2 data points, return sample data
    if len(price_values) < 2:
        return _get_sample_chart_data(period, 'single', symbol)
    
    # Create a single dataset
    dataset = {
        'label': symbol,
        'data': price_values,
        'borderColor': '#4facfe',  # Primary color for single stock
        'backgroundColor': 'transparent',
        'borderWidth': 2,
        'fill': False,
        'tension': 0.1,  # Lower tension for a more traditional stock chart look
        'pointRadius': 0,
        'pointHoverRadius': 4
    }
    
    return {
        'labels': labels,
        'datasets': [dataset]
    }


def _calculate_intraday_stock_prices(positions):
    """Calculate intraday stock prices for all stocks in portfolio"""
    try:
        from .yahoo_finance import YahooFinanceService
        yahoo_service = YahooFinanceService()
        
        # Colors for different stocks
        colors = [
            '#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', 
            '#00f2fe', '#43e97b', '#38f9d7', '#ffecd2', '#fcb69f',
            '#a8edea', '#fed6e3', '#ffeaa7', '#fab1a0', '#74b9ff'
        ]
        
        datasets = []
        common_labels = None
        
        for i, position in enumerate(positions):
            symbol = position['symbol']
            try:
                # Get intraday data from Yahoo Finance
                intraday_data = yahoo_service.get_intraday_data(symbol)
                
                if intraday_data and intraday_data.get('timestamps') and intraday_data.get('prices'):
                    timestamps = intraday_data['timestamps']
                    prices = intraday_data['prices']
                    
                    # Format labels (time only)
                    labels = [ts.strftime('%H:%M') for ts in timestamps]
                    
                    # Use the first stock's labels as the common labels
                    if common_labels is None:
                        common_labels = labels
                    
                    datasets.append({
                        'label': symbol,
                        'data': prices,
                        'borderColor': colors[i % len(colors)],
                        'backgroundColor': colors[i % len(colors)] + '20',
                        'borderWidth': 2,
                        'fill': False,
                        'tension': 0.3,
                        'pointRadius': 0,
                        'pointHoverRadius': 4
                    })
                    
            except Exception as e:
                print(f"Error getting intraday data for {symbol}: {e}")
                continue
        
        # If we have datasets, return them
        if datasets and common_labels:
            return {
                'labels': common_labels,
                'datasets': datasets
            }
        
    except ImportError:
        print("Yahoo Finance service not available")
    except Exception as e:
        print(f"Error in intraday stock prices: {e}")
    
    # Fallback to sample data
    return _get_sample_chart_data('1D', 'historical')


def _calculate_intraday_portfolio_performance(positions):
    """Calculate intraday portfolio performance using real-time data"""
    try:
        from .yahoo_finance import YahooFinanceService
        yahoo_service = YahooFinanceService()
        
        # Get intraday data for all stocks
        stock_intraday_data = {}
        common_timestamps = None
        
        for position in positions:
            symbol = position['symbol']
            try:
                intraday_data = yahoo_service.get_intraday_data(symbol)
                if intraday_data and intraday_data.get('timestamps') and intraday_data.get('prices'):
                    stock_intraday_data[symbol] = {
                        'timestamps': intraday_data['timestamps'],
                        'prices': intraday_data['prices'],
                        'quantity': position['quantity']
                    }
                    
                    # Use the first stock's timestamps as reference
                    if common_timestamps is None:
                        common_timestamps = intraday_data['timestamps']
                        
            except Exception as e:
                print(f"Error getting intraday data for {symbol}: {e}")
                continue
        
        # Calculate portfolio values at each timestamp
        if stock_intraday_data and common_timestamps:
            portfolio_values = []
            labels = []
            
            for i, timestamp in enumerate(common_timestamps):
                portfolio_value = 0
                
                # Calculate total portfolio value at this timestamp
                for symbol, data in stock_intraday_data.items():
                    if i < len(data['prices']):
                        stock_value = data['prices'][i] * float(data['quantity'])  # Convert Decimal to float
                        portfolio_value += stock_value
                
                portfolio_values.append(portfolio_value)
                labels.append(timestamp.strftime('%H:%M'))
            
            return {
                'labels': labels,
                'values': portfolio_values
            }
            
    except ImportError:
        print("Yahoo Finance service not available")
    except Exception as e:
        print(f"Error in intraday portfolio performance: {e}")
    
    # Fallback to sample data
    return _get_sample_chart_data('1D', 'portfolio')


def _get_sample_chart_data(period, chart_type='portfolio', symbol=None):
    """Generate sample chart data for display when no real data is available"""
    if chart_type == 'single' and symbol:
        # Generate sample data for a single stock
        import random
        
        # Choose realistic base price based on symbol
        if symbol == 'AAPL':
            base_price = 175.0
        elif symbol == 'MSFT':
            base_price = 320.0
        elif symbol == 'GOOGL':
            base_price = 140.0
        elif symbol == 'AMZN':
            base_price = 130.0
        elif symbol == 'TSLA':
            base_price = 250.0
        elif symbol == 'META':
            base_price = 300.0
        elif symbol == 'NVDA':
            base_price = 450.0
        else:
            # Use a random but realistic price for other symbols
            base_price = random.uniform(50, 400)
        
        # Generate more realistic price data with slight upward bias
        if period == '1D':
            labels = ['9:30', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00']
            # Use realistic volatility for intraday
            volatility = 0.008  # 0.8% typical intraday movement
        elif period == '1W':
            labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
            volatility = 0.015  # 1.5% daily movement
        elif period == '1M':
            labels = [f"Week {i+1}" for i in range(4)]
            volatility = 0.03  # 3% weekly movement
        elif period == '6M':
            labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
            volatility = 0.06  # 6% monthly movement
        elif period == '1Y':
            labels = ['Jan', 'Mar', 'May', 'Jul', 'Sep', 'Nov']
            volatility = 0.08  # 8% bi-monthly movement
        else:
            labels = ['Start', 'End']
            volatility = 0.1  # 10% for generic periods
        
        # Generate prices with a random walk but slight upward bias
        stock_prices = [base_price]
        for _ in range(1, len(labels)):
            change = random.normalvariate(0.002, volatility)  # Slight positive bias
            stock_prices.append(stock_prices[-1] * (1 + change))
        
        dataset = {
            'label': symbol,
            'data': stock_prices,
            'borderColor': '#4facfe',
            'backgroundColor': 'transparent',
            'borderWidth': 2,
            'fill': False,
            'tension': 0.1,  # Lower tension for stock chart look
            'pointRadius': 0,
            'pointHoverRadius': 4
        }
        
        return {
            'labels': labels,
            'datasets': [dataset]
        }
    elif chart_type == 'historical':
        # Generate sample historical stock prices
        import random
        
        # Sample stock data
        stocks = ['AAPL', 'GOOGL', 'MSFT']
        colors = ['#667eea', '#f5576c', '#43e97b']
        datasets = []
        
        if period == '1D':
            labels = ['9:30', '10:00', '11:00', '12:00', '1:00', '2:00', '3:00', '4:00']
        elif period == '1W':
            labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
        elif period == '1M':
            labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
        elif period == '6M':
            labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        elif period == '1Y':
            labels = ['Jan', 'Mar', 'May', 'Jul', 'Sep', 'Nov']
        else:
            labels = ['Start', 'End']
        
        for i, stock in enumerate(stocks):
            base_price = random.uniform(100, 300)  # Random base price
            stock_prices = [base_price]
            
            for j in range(1, len(labels)):
                change = random.uniform(-0.05, 0.05)  # ±5% change
                stock_prices.append(stock_prices[-1] * (1 + change))
            
            datasets.append({
                'label': stock,
                'data': stock_prices,
                'borderColor': colors[i],
                'backgroundColor': colors[i] + '20',
                'borderWidth': 2,
                'fill': False,
                'tension': 0.4,
                'pointRadius': 0,
                'pointHoverRadius': 4
            })
        
        return {
            'labels': labels,
            'datasets': datasets
        }
    else:
        # Original portfolio value sample data
        base_value = 10000
        
        if period == '1D':
            labels = ['9:30', '10:00', '11:00', '12:00', '1:00', '2:00', '3:00', '4:00']
            values = [base_value, base_value * 1.02, base_value * 0.99, base_value * 1.01, 
                     base_value * 1.03, base_value * 0.98, base_value * 1.05, base_value * 1.04]
        elif period == '1W':
            labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
            values = [base_value, base_value * 1.05, base_value * 0.97, base_value * 1.08, base_value * 1.12]
        elif period == '1M':
            labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
            values = [base_value, base_value * 1.15, base_value * 1.08, base_value * 1.25]
        elif period == '6M':
            labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
            values = [base_value, base_value * 1.12, base_value * 0.95, base_value * 1.18, 
                     base_value * 1.22, base_value * 1.35]
        elif period == '1Y':
            labels = ['Jan', 'Mar', 'May', 'Jul', 'Sep', 'Nov']
            values = [base_value, base_value * 1.15, base_value * 0.88, base_value * 1.25, 
                     base_value * 1.45, base_value * 1.62]
        else:
            labels = ['Start', 'End']
            values = [base_value, base_value * 1.1]
        
        return {
            'labels': labels,
            'values': values
        }


@login_required
def performance_since_inception_data(request):
    """Provide performance data for individual stocks since their inception in portfolio"""
    try:
        # Get current portfolio name from session
        current_portfolio = request.session.get('current_portfolio', 'My Investment Portfolio')
        
        # Get current positions (filtered by user)
        positions = PortfolioAnalytics.get_stock_positions(current_portfolio, request.user)
        
        if not positions:
            return JsonResponse({'datasets': [], 'labels': []})
        
        # Calculate performance data for each stock from inception
        chart_data = _calculate_performance_since_inception(positions, current_portfolio)
        
        return JsonResponse(chart_data)
        
    except Exception as e:
        # Return sample data on error
        return JsonResponse(_get_sample_inception_chart_data())


def _calculate_performance_since_inception(positions, portfolio_name):
    """Calculate performance for each stock from its purchase date and portfolio average"""
    from django.db.models import Min
    from .yahoo_finance import YahooFinanceService
    
    # Prepare datasets for Chart.js
    datasets = []
    all_dates = set()
    stock_data = {}
    
    # Colors for different stocks
    colors = [
        '#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', 
        '#00f2fe', '#43e97b', '#38f9d7', '#ffecd2', '#fcb69f',
        '#a8edea', '#fed6e3', '#ffeaa7', '#fab1a0', '#74b9ff'
    ]
    
    # Process each stock
    for i, position in enumerate(positions):
        symbol = position['symbol']
        
        # Get first purchase date for this stock
        first_purchase = Portfolio.objects.filter(
            stock__symbol=symbol,
            portfolio_name=portfolio_name,
            transaction_type='BUY'
        ).aggregate(first_date=Min('transaction_date'))['first_date']
        
        if not first_purchase:
            continue
            
        # Get price data from first purchase date to now
        prices = StockPrice.objects.filter(
            stock__symbol=symbol,
            date__gte=first_purchase
        ).order_by('date')
        
        # If we have limited price data, try to fetch more from Yahoo Finance
        if prices.count() < 5:  # Less than 5 data points
            try:
                yahoo_service = YahooFinanceService()
                # Fetch historical data from first purchase to today
                days_back = (timezone.now().date() - first_purchase).days + 1
                yahoo_service.update_stock_prices_for_period(symbol, days_back)
                
                # Re-fetch prices after update
                prices = StockPrice.objects.filter(
                    stock__symbol=symbol,
                    date__gte=first_purchase
                ).order_by('date')
            except Exception as e:
                print(f"Warning: Could not fetch historical data for {symbol}: {e}")
        
        if not prices:
            continue
            
        # Calculate performance relative to average cost
        avg_cost = position['avg_cost']
        stock_performance = []
        stock_dates = []
        
        for price in prices:
            # Calculate percentage gain/loss from average cost
            performance_pct = ((price.close_price - avg_cost) / avg_cost) * 100
            stock_performance.append(float(performance_pct))
            stock_dates.append(price.date)
            all_dates.add(price.date)
        
        if stock_performance:
            # Store data for portfolio average calculation
            stock_data[symbol] = {
                'dates': stock_dates,
                'performance': stock_performance,
                'weight': float(position['total_cost'])  # Weight by investment amount
            }
    
    if not all_dates:
        return _get_sample_inception_chart_data()
    
    # Sort dates and align all stock data to the same date range
    sorted_dates = sorted(all_dates)
    
    # Now create aligned datasets for each stock
    for i, (symbol, data) in enumerate(stock_data.items()):
        aligned_performance = []
        
        for date in sorted_dates:
            # Find the performance value for this date or the last available
            date_performance = None
            for j, stock_date in enumerate(data['dates']):
                if stock_date <= date:
                    date_performance = data['performance'][j]
                else:
                    break
            
            # If we found performance data, use it; otherwise use 0 (no data yet)
            if date_performance is not None:
                aligned_performance.append(date_performance)
            else:
                aligned_performance.append(0)
        
        # Add aligned dataset
        datasets.append({
            'label': symbol,
            'data': aligned_performance,
            'borderColor': colors[i % len(colors)],
            'backgroundColor': colors[i % len(colors)] + '20',  # Add transparency
            'borderWidth': 2,
            'fill': False,
            'tension': 0.4,
            'pointRadius': 0,
            'pointHoverRadius': 4
        })
    
    # Calculate portfolio average
    portfolio_performance = []
    total_weight = sum(data['weight'] for data in stock_data.values())
    
    for date in sorted_dates:
        weighted_performance = 0
        available_weight = 0
        
        for symbol, data in stock_data.items():
            # Find the performance value for this date or the last available
            date_performance = None
            for i, stock_date in enumerate(data['dates']):
                if stock_date <= date:
                    date_performance = data['performance'][i]
                else:
                    break
            
            if date_performance is not None:
                weighted_performance += date_performance * data['weight']
                available_weight += data['weight']
        
        if available_weight > 0:
            portfolio_avg = weighted_performance / available_weight
            portfolio_performance.append(portfolio_avg)
        else:
            portfolio_performance.append(0)
    
    # Add portfolio average line
    datasets.append({
        'label': 'Portfolio Average',
        'data': portfolio_performance,
        'borderColor': '#00CED1',  # Changed from #2c3e50 to bright cyan for visibility
        'backgroundColor': '#00CED120',
        'borderWidth': 3,
        'fill': False,
        'tension': 0.4,
        'pointRadius': 0,
        'pointHoverRadius': 4,
        'borderDash': [5, 5]  # Dashed line to distinguish it
    })
    
    # Format labels
    labels = [date.strftime('%m/%d/%Y') for date in sorted_dates]
    
    return {
        'labels': labels,
        'datasets': datasets
    }


def _get_sample_inception_chart_data():
    """Generate sample inception chart data"""
    import random
    
    # Generate sample dates over 6 months
    base_date = datetime.now().date() - timedelta(days=180)
    dates = [base_date + timedelta(days=i*7) for i in range(26)]  # Weekly data points
    labels = [date.strftime('%m/%d/%Y') for date in dates]
    
    # Sample stock data
    stocks = ['AAPL', 'GOOGL', 'MSFT']
    colors = ['#667eea', '#f5576c', '#43e97b']
    datasets = []
    
    for i, stock in enumerate(stocks):
        # Generate performance data with some volatility
        performance = [0]  # Start at 0%
        for j in range(1, len(labels)):
            change = random.uniform(-5, 8)  # Random daily change
            performance.append(performance[-1] + change)
        
        datasets.append({
            'label': stock,
            'data': performance,
            'borderColor': colors[i],
            'backgroundColor': colors[i] + '20',
            'borderWidth': 2,
            'fill': False,
            'tension': 0.4,
            'pointRadius': 0,
            'pointHoverRadius': 4
        })
    
    # Portfolio average
    portfolio_avg = [sum(datasets[j]['data'][i] for j in range(len(datasets))) / len(datasets) for i in range(len(labels))]
    datasets.append({
        'label': 'Portfolio Average',
        'data': portfolio_avg,
        'borderColor': '#00CED1',  # Changed from #2c3e50 to bright cyan for visibility
        'backgroundColor': '#00CED120',
        'borderWidth': 3,
        'fill': False,
        'tension': 0.4,
        'pointRadius': 0,
        'pointHoverRadius': 4,
        'borderDash': [5, 5]
    })
    
    return {
        'labels': labels,
        'datasets': datasets
    }


def stock_search(request):
    """API endpoint for stock symbol search"""
    query = request.GET.get('q', '').strip().upper()
    
    if len(query) < 1:
        return JsonResponse({'results': []})
    
    try:
        # Use Yahoo Finance for symbol search (more reliable and free)
        from .yahoo_finance import YahooFinanceService
        yahoo_service = YahooFinanceService()
        search_results = yahoo_service.search_symbols(query)
        
        # Format results for autocomplete
        formatted_results = []
        for result in search_results[:10]:  # Limit to 10 results
            formatted_results.append({
                'symbol': result.get('symbol', ''),
                'name': result.get('name', ''),
                'type': result.get('type', 'Equity'),
                'region': result.get('region', 'United States'),
                'exchange': result.get('exchange', '')
            })
        
        return JsonResponse({'results': formatted_results})
        
    except Exception as e:
        # Final fallback to simple symbol validation
        return JsonResponse({
            'results': [{
                'symbol': query,
                'name': f'{query} Stock',
                'type': 'Equity',
                'region': 'United States',
                'currency': 'USD'
            }] if query else []
        })


def get_stock_price(request):
    """API endpoint to get current stock price"""
    symbol = request.GET.get('symbol', '').strip().upper()
    
    if not symbol:
        return JsonResponse({'error': 'Symbol is required'}, status=400)
    
    try:
        # Use Yahoo Finance for current prices (most reliable and real-time)
        from .yahoo_finance import YahooFinanceService
        yahoo_service = YahooFinanceService()
        price_data = yahoo_service.get_current_price(symbol)
        
        if price_data:
            return JsonResponse({
                'symbol': price_data.get('symbol', symbol),
                'price': price_data.get('price', 0),
                'change': price_data.get('change', 0),
                'change_percent': float(price_data.get('change_percent', 0)),
                'prev_close': price_data.get('prev_close', 0),
                'market_status': price_data.get('market_status', 'Unknown'),
                'last_updated': price_data.get('last_updated', 'Live'),
                'source': price_data.get('source', 'Yahoo Finance'),
                'currency': price_data.get('currency', 'USD'),
                'exchange': price_data.get('exchange', 'Unknown')
            })
    except Exception as yahoo_error:
        print(f"Yahoo Finance error for {symbol}: {yahoo_error}")
        
        
        # Final fallback to reasonable price estimate
        import random
        fallback_price = random.uniform(10, 500)  # Random price between $10-$500
        
        return JsonResponse({
            'symbol': symbol,
            'price': round(fallback_price, 2),
            'change': 0,
            'change_percent': 0,
            'last_updated': 'Estimated',
            'source': 'Fallback',
            'note': 'Price estimated - APIs unavailable'
        })


@login_required
@require_http_methods(["GET"])
def sector_allocation_data(request):
    """Provide sector allocation data for pie chart"""
    try:
        # Get current portfolio name from session
        current_portfolio = request.session.get('current_portfolio', 'My Investment Portfolio')
        
        # Get current positions (filtered by user)
        positions = PortfolioAnalytics.get_stock_positions(current_portfolio, request.user)
        
        if not positions:
            return JsonResponse({'sectors': [], 'labels': [], 'values': []})
        
        # Sector mapping (simplified - in production you'd want to use real sector data from an API)
        SECTOR_MAPPING = {
            # Technology companies
            'AAPL': 'Technology', 'MSFT': 'Technology', 'CRM': 'Technology',
            'ORCL': 'Technology', 'ADBE': 'Technology', 'INTC': 'Technology', 'AMD': 'Technology',
            'NVDA': 'Technology', 'IBM': 'Technology', 'NOW': 'Technology',
            
            # Communication Services (including search engines and social media)
            'GOOGL': 'Communication Services', 'GOOG': 'Communication Services', 'META': 'Communication Services',
            'NFLX': 'Communication Services', 'DIS': 'Communication Services', 'T': 'Communication Services',
            'VZ': 'Communication Services', 'CMCSA': 'Communication Services',
            
            # Consumer Discretionary (including e-commerce and electric vehicles)
            'AMZN': 'Consumer Discretionary', 'TSLA': 'Consumer Discretionary', 'HD': 'Consumer Discretionary',
            'NKE': 'Consumer Discretionary', 'LOW': 'Consumer Discretionary', 'SBUX': 'Consumer Discretionary',
            
            # Healthcare
            'JNJ': 'Healthcare', 'PFE': 'Healthcare', 'UNH': 'Healthcare', 'ABBV': 'Healthcare',
            'TMO': 'Healthcare', 'DHR': 'Healthcare', 'BMY': 'Healthcare', 'MRK': 'Healthcare',
            
            # Financials (including insurance and diversified financials)
            'JPM': 'Financials', 'BAC': 'Financials', 'WFC': 'Financials', 'GS': 'Financials',
            'MS': 'Financials', 'AXP': 'Financials', 'BLK': 'Financials', 'C': 'Financials',
            'BRK-A': 'Financials', 'BRK-B': 'Financials', 'BRK.A': 'Financials', 'BRK.B': 'Financials',
            'V': 'Financials', 'MA': 'Financials', 'PYPL': 'Financials', 'COF': 'Financials',
            
            # Consumer Staples
            'PG': 'Consumer Staples', 'KO': 'Consumer Staples', 'PEP': 'Consumer Staples',
            'WMT': 'Consumer Staples', 'COST': 'Consumer Staples', 'CL': 'Consumer Staples',
            
            # Industrials (including machinery, aerospace, transportation)
            'MMM': 'Industrials', 'BA': 'Industrials', 'CAT': 'Industrials', 'GE': 'Industrials',
            'DE': 'Industrials', 'HON': 'Industrials', 'UPS': 'Industrials', 'RTX': 'Industrials',
            'LMT': 'Industrials', 'NOC': 'Industrials', 'FDX': 'Industrials',
            
            # Energy
            'XOM': 'Energy', 'CVX': 'Energy', 'COP': 'Energy', 'SLB': 'Energy', 'EOG': 'Energy',
            
            # Utilities
            'NEE': 'Utilities', 'DUK': 'Utilities', 'SO': 'Utilities', 'D': 'Utilities',
            
            # Real Estate (including REITs)
            'AMT': 'Real Estate', 'PLD': 'Real Estate', 'O': 'Real Estate', 'SPG': 'Real Estate',
            'EXR': 'Real Estate', 'PSA': 'Real Estate', 'WELL': 'Real Estate', 'EQIX': 'Real Estate',
            
            # Materials
            'LIN': 'Materials', 'APD': 'Materials', 'SHW': 'Materials', 'FCX': 'Materials'
        }
        
        # Calculate sector allocation based on current market values
        sector_values = {}
        total_portfolio_value = 0
        
        # Get current prices for all positions to calculate market values
        for position in positions:
            symbol = position['symbol']
            sector = SECTOR_MAPPING.get(symbol, 'Other')  # Default to 'Other' if not mapped
            
            # Calculate current market value using latest stock price
            try:
                latest_price = StockPrice.objects.filter(
                    stock__symbol=symbol
                ).order_by('-date').first()
                
                if latest_price:
                    # Use current market value (shares * current price)
                    position_value = float(position['quantity']) * float(latest_price.close_price)
                else:
                    # Fallback to total cost if no current price available
                    position_value = float(position.get('total_cost', 0))
            except Exception:
                # Fallback to total cost if there's any error
                position_value = float(position.get('total_cost', 0))
            
            sector_values[sector] = sector_values.get(sector, 0) + position_value
            total_portfolio_value += position_value
        
        # Prepare data for pie chart
        if total_portfolio_value > 0:
            labels = list(sector_values.keys())
            values = [sector_values[sector] for sector in labels]
            percentages = [(value / total_portfolio_value) * 100 for value in values]
            
            # Sort by value (largest first)
            sorted_data = sorted(zip(labels, values, percentages), key=lambda x: x[1], reverse=True)
            labels, values, percentages = zip(*sorted_data) if sorted_data else ([], [], [])
            
            return JsonResponse({
                'labels': list(labels),
                'values': list(values),
                'percentages': [round(p, 1) for p in percentages],
                'total_value': round(total_portfolio_value, 2)
            })
        else:
            return JsonResponse({'labels': [], 'values': [], 'percentages': [], 'total_value': 0})
        
    except Exception as e:
        # Return sample data on error
        return JsonResponse({
            'labels': ['Technology', 'Healthcare', 'Financials', 'Consumer Staples'],
            'values': [5000, 3000, 2000, 1500],
            'percentages': [43.5, 26.1, 17.4, 13.0],
            'total_value': 11500
        })

@login_required
def change_portfolio(request):
    """Change the current portfolio name"""
    if request.method == 'POST':
        new_portfolio_name = request.POST.get('portfolio_name', '').strip()
        
        if not new_portfolio_name:
            messages.error(request, 'Portfolio name cannot be empty')
        else:
            # Update session with new portfolio name
            request.session['current_portfolio'] = new_portfolio_name
            messages.success(request, f'Switched to portfolio: {new_portfolio_name}')
    
    return redirect('dashboard')


@login_required
def generate_portfolio_report(request):
    """Generate PDF report of portfolio transactions"""
    # Get current portfolio name from session
    current_portfolio = request.session.get('current_portfolio', 'My Investment Portfolio')
    
    # Get all transactions for current portfolio (filtered by user)
    transactions = Portfolio.objects.filter(user=request.user, portfolio_name=current_portfolio).select_related('stock').order_by('-transaction_date', '-created_at')
    
    # Get portfolio summary (filtered by user)
    summary = PortfolioAnalytics.get_portfolio_summary(current_portfolio, request.user)
    
    # Get current positions (filtered by user)
    positions = PortfolioAnalytics.get_stock_positions(current_portfolio, request.user)
    
    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        spaceAfter=30,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=15,
        textColor=colors.darkgreen
    )
    
    # Title
    elements.append(Paragraph(f"Portfolio Report: {current_portfolio}", title_style))
    elements.append(Paragraph(f"Generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Portfolio Summary
    elements.append(Paragraph("Portfolio Summary", heading_style))
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Invested', f"${summary['total_invested']:.2f}"],
        ['Total Received', f"${summary['total_received']:.2f}"],
        ['Net Invested', f"${summary['net_invested']:.2f}"],
        ['Number of Companies', str(summary['companies_count'])],
        ['Total Transactions', str(summary['total_transactions'])],
    ]
    
    summary_table = Table(summary_data, colWidths=[200, 150])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Current Positions
    if positions:
        elements.append(Paragraph("Current Positions", heading_style))
        
        positions_data = [['Symbol', 'Shares', 'Avg Cost', 'Total Cost']]
        for position in positions:
            positions_data.append([
                position['symbol'],
                f"{position['quantity']:.0f}",
                f"${position['avg_cost']:.2f}",
                f"${position['total_cost']:.2f}"
            ])
        
        positions_table = Table(positions_data, colWidths=[100, 80, 100, 120])
        positions_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(positions_table)
        elements.append(Spacer(1, 20))
    
    # All Transactions
    elements.append(Paragraph("Transaction History", heading_style))
    
    if transactions:
        transaction_data = [['Date', 'Type', 'Symbol', 'Quantity', 'Price', 'Total', 'Notes']]
        
        for txn in transactions:
            total_value = txn.quantity * txn.price_per_share
            transaction_data.append([
                txn.transaction_date.strftime('%m/%d/%Y'),
                txn.transaction_type,
                txn.stock.symbol,
                f"{txn.quantity:.0f}",
                f"${txn.price_per_share:.2f}",
                f"${total_value:.2f}",
                txn.notes[:30] + '...' if len(txn.notes) > 30 else txn.notes
            ])
        
        transaction_table = Table(transaction_data, colWidths=[70, 40, 60, 60, 70, 80, 120])
        transaction_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(transaction_table)
    else:
        elements.append(Paragraph("No transactions found for this portfolio.", styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    
    # Return PDF response
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"{current_portfolio.replace(' ', '_')}_portfolio_report_{timezone.now().strftime('%Y%m%d')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    buffer.close()
    
    return response
