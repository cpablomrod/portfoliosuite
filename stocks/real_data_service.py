import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_GET
import json

def get_real_historical_data(symbol, period='1Y'):
    """
    Fetch real historical stock data using Yahoo Finance
    """
    try:
        # Create ticker object
        ticker = yf.Ticker(symbol)
        
        # Map our period format to yfinance format
        period_mapping = {
            '1D': '1d',
            '1W': '5d', 
            '1M': '1mo',
            '6M': '6mo',
            '1Y': '1y',
            '5Y': '5y',
            '10Y': '10y',
            '20Y': '20y',
            'MAX': 'max'
        }
        
        yf_period = period_mapping.get(period, '1y')
        
        # Get historical data
        hist = ticker.history(period=yf_period)
        
        if hist.empty:
            return None, None
            
        # Process the data based on period
        labels = []
        prices = []
        processed_data = None
        
        if period == '1D':
            # For 1 day, use hourly intervals if available
            processed_data = hist
        elif period == '1W':
            # For 1 week, show daily data
            processed_data = hist
        elif period == '1M':
            # For 1 month, show every few days
            processed_data = hist.tail(15)  # Last 15 data points
        elif period == '6M':
            # For 6 months, show weekly data
            processed_data = hist.resample('W').last().dropna()
        elif period == '1Y':
            # For 1 year, show monthly data
            processed_data = hist.resample('M').last().dropna()
        elif period == '5Y':
            # For 5 years, show quarterly data
            processed_data = hist.resample('Q').last().dropna()
        elif period == '10Y':
            # For 10 years, show quarterly data
            processed_data = hist.resample('Q').last().dropna()
        elif period == '20Y':
            # For 20 years, show yearly data
            processed_data = hist.resample('Y').last().dropna()
        elif period == 'MAX':
            # For max, show yearly data
            processed_data = hist.resample('Y').last().dropna()
        
        if processed_data is not None and not processed_data.empty:
            # Get baseline price (first price in the period)
            baseline_price = processed_data.iloc[0]['Close']
            
            for timestamp in processed_data.index:
                # Format labels based on period
                if period == '1D':
                    labels.append(timestamp.strftime('%I:%M %p'))
                elif period == '1W':
                    labels.append(timestamp.strftime('%a, %b %d'))
                elif period == '1M':
                    labels.append(timestamp.strftime('%b %d'))
                elif period == '6M':
                    labels.append(timestamp.strftime('%b %d'))
                elif period == '1Y':
                    labels.append(timestamp.strftime('%b %y'))
                elif period == '5Y':
                    labels.append(timestamp.strftime('%b %y'))
                elif period == '10Y':
                    labels.append(timestamp.strftime('%b %y'))
                elif period == '20Y':
                    labels.append(timestamp.strftime('%Y'))
                elif period == 'MAX':
                    labels.append(timestamp.strftime('%Y'))
                
                # Get actual price for this data point
                current_price = processed_data.loc[timestamp, 'Close']
                # Calculate percentage change from baseline
                percentage_change = ((current_price - baseline_price) / baseline_price) * 100
                # Store both percentage and actual price
                prices.append({
                    'percentage': round(float(percentage_change), 2),
                    'actual_price': round(float(current_price), 2)
                })
        
        return labels, prices
        
    except Exception as e:
        print(f"Error fetching data for {symbol}: {str(e)}")
        return None, None

@require_GET
def real_historical_chart_data(request):
    """
    API endpoint to serve real historical stock data
    """
    period = request.GET.get('period', '1Y')
    symbols = request.GET.get('symbols', 'AAPL,MSFT,GOOGL').split(',')
    
    try:
        datasets = []
        all_labels = None
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        for i, symbol in enumerate(symbols):
            symbol = symbol.strip().upper()
            labels, prices = get_real_historical_data(symbol, period)
            
            if labels and prices:
                # Use the first successful symbol's labels for all
                if all_labels is None:
                    all_labels = labels
                
                # Extract percentage data for chart display
                percentage_data = [p['percentage'] if isinstance(p, dict) else p for p in prices]
                
                dataset = {
                    'label': symbol,
                    'data': percentage_data,
                    'actualPrices': prices,  # Include full price data for tooltips
                    'borderColor': colors[i % len(colors)],
                    'backgroundColor': 'rgba(0,0,0,0)',
                    'borderWidth': 2,
                    'fill': False,
                    'tension': 0.1,
                    'pointRadius': 2,
                    'pointHoverRadius': 6,
                    'pointBackgroundColor': colors[i % len(colors)],
                    'pointBorderColor': '#ffffff',
                    'pointBorderWidth': 1
                }
                datasets.append(dataset)
        
        if not datasets:
            # Fallback to simulated data if no real data available
            return JsonResponse({
                'error': 'No real data available',
                'labels': [],
                'datasets': []
            })
        
        return JsonResponse({
            'labels': all_labels or [],
            'datasets': datasets,
            'source': 'Yahoo Finance',
            'period': period
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'labels': [],
            'datasets': []
        }, status=500)
