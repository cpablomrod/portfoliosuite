# Stock Portfolio Tracker

A Django-based web application to track your stock portfolio and run historical simulations.

## Features

- **Portfolio Management**: Track your stock purchases and sales
- **Current Positions**: View your current stock holdings with gains/losses
- **Price Updates**: Fetch real-time stock prices from Alpha Vantage API  
- **Historical Simulations**: Run "what-if" scenarios for past time periods
- **Single-Screen Dashboard**: All functionality on one compact screen
- **Responsive Design**: Works on laptop screens without scrolling

## Setup Instructions

### 1. Alpha Vantage API Key

You'll need a free API key from Alpha Vantage to fetch stock data:

1. Go to [https://www.alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key)
2. Sign up for a free account
3. Get your API key (free tier allows 25 requests per day, 5 requests per minute)

### 2. Environment Configuration

Edit the `.env` file in the project root and add your API key:

```
ALPHA_VANTAGE_API_KEY=your_actual_api_key_here
DEBUG=True
SECRET_KEY=your-secret-key-here
```

### 3. Install Dependencies

The virtual environment and dependencies are already set up. To activate the environment:

```bash
source venv/bin/activate
```

### 4. Run the Application

```bash
python manage.py runserver
```

Open your browser and go to `http://localhost:8000`

## How to Use

### Adding Stock Transactions

1. Use the "Add Transaction" form in the middle column
2. Enter the stock symbol (e.g., AAPL, GOOGL)
3. Choose BUY or SELL
4. Enter quantity and price per share
5. Set the transaction date
6. Add optional notes
7. Click "Add Transaction"

### Updating Stock Prices

1. Click the "Update Prices" button in the left column
2. The app will fetch the latest prices for all stocks in your portfolio
3. Current prices and gains/losses will be displayed

### Running Historical Simulations

1. Use the "Historical Simulation" form in the right column
2. Enter stock symbols separated by commas (e.g., "AAPL, GOOGL, MSFT")
3. Set start and end dates for the simulation period
4. Enter the total investment amount (will be split equally among stocks)
5. Click "Run Simulation"
6. View results showing how your investment would have performed

### Understanding the Dashboard

**Left Column - Portfolio Overview:**
- Portfolio summary with total invested and number of stocks
- Current positions with real-time gains/losses
- Update prices button

**Middle Column - Transactions:**
- Form to add new transactions
- Recent transaction history

**Right Column - Simulations:**
- Historical simulation form
- Simulation results with individual stock performance

## Database Models

- **Stock**: Basic stock information (symbol, company name)
- **StockPrice**: Historical daily prices (OHLCV data)
- **Portfolio**: Your transactions (buys/sells with dates and prices)

## API Rate Limits

- Alpha Vantage free tier: 25 requests/day, 5 requests/minute
- The app automatically handles rate limiting
- Price updates fetch the most recent data available

## File Structure

```
stock_portfolio_tracker/
├── stocks/                 # Main Django app
│   ├── models.py          # Database models
│   ├── views.py           # View logic
│   ├── forms.py           # Django forms
│   ├── services.py        # API and analytics services
│   ├── templates/         # HTML templates
│   └── admin.py           # Django admin config
├── portfolio_tracker/     # Django project settings
├── db.sqlite3            # SQLite database
├── .env                  # Environment variables
└── manage.py             # Django management script
```

## Admin Interface

Access the Django admin at `http://localhost:8000/admin/` to:
- View and edit transactions directly
- Manage stock data
- View price history

Create a superuser account:
```bash
python manage.py createsuperuser
```

## Troubleshooting

**API Key Issues:**
- Make sure your API key is correctly set in the `.env` file
- Check that you haven't exceeded the rate limit (25 requests/day)

**No Price Data:**
- Stock prices are only available for trading days
- Some symbols might not be available in Alpha Vantage
- Try updating prices for individual stocks

**Simulation Errors:**
- Ensure you have price data for the simulation period
- Check that stock symbols are valid
- Make sure dates are not weekends or holidays

## Extending the App

You can easily extend this app by:
- Adding more stock data providers
- Implementing portfolio charts and visualizations  
- Adding alerts for price targets
- Creating more sophisticated analytics
- Integrating with brokerage APIs
- Adding user authentication for multiple portfolios
