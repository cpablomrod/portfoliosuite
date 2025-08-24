# Portfolio Suite

A Django-based web application to track your stock portfolio and run historical simulations. **No API keys required!**

## ✨ Features

- **Portfolio Management**: Track your stock purchases and sales across multiple portfolios
- **Current Positions**: View your current stock holdings with real-time gains/losses
- **Free Stock Data**: Fetches stock prices from Yahoo Finance and multiple free APIs
- **Historical Simulations**: Run "what-if" scenarios for past investment periods
- **Interactive Charts**: Portfolio performance and individual stock charts
- **PDF Reports**: Generate detailed portfolio reports
- **Multiple Portfolios**: Switch between different investment portfolios
- **Responsive Design**: Works perfectly on desktop and mobile devices

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/cpablomrod/portfoliosuite.git
cd portfoliosuite
```

### 2. Set Up Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Database

```bash
python manage.py migrate
```

### 5. Run the Application

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

## 🔄 Data Sources

Portfolio Suite uses multiple **free** data sources with automatic fallbacks:

1. **Yahoo Finance** (Primary) - Real-time and historical data
2. **Twelve Data** (Demo) - Backup financial data API
3. **Alpha Vantage** (Demo mode) - No API key required
4. **Financial Modeling Prep** (Demo) - Free tier access
5. **MarketStack** (Demo) - Additional data source

**No API keys needed!** The app works out of the box.

## 🗄️ Database Models

- **Stock**: Basic stock information (symbol, company name)
- **StockPrice**: Historical daily prices (OHLCV data)
- **Portfolio**: Your transactions (buys/sells with dates and prices)

## 📁 File Structure

```
portfoliosuite/
├── stocks/                    # Main Django app
│   ├── models.py             # Database models
│   ├── views.py              # View logic and API endpoints
│   ├── forms.py              # Django forms
│   ├── services.py           # Stock data and analytics services
│   ├── free_data_service.py  # Free API integrations
│   ├── yahoo_finance.py      # Yahoo Finance integration
│   ├── templates/stocks/     # HTML templates
│   ├── management/commands/  # Django management commands
│   └── migrations/           # Database migrations
├── portfolio_tracker/        # Django project settings
├── requirements.txt          # Python dependencies
├── db.sqlite3               # SQLite database (excluded from git)
├── .env                     # Environment variables (excluded from git)
└── manage.py                # Django management script
```

## 🔧 Admin Interface

Access the Django admin at `http://localhost:8000/admin/` to:
- View and edit transactions directly
- Manage stock data and price history
- Monitor system performance

Create a superuser account:
```bash
python manage.py createsuperuser
```

## 🐛 Troubleshooting

**No Price Data:**
- Stock prices are only available for trading days
- The app tries multiple data sources automatically
- Check internet connection for API access

**Simulation Errors:**
- Ensure simulation period covers trading days
- Verify stock symbols are valid (e.g., AAPL, MSFT, GOOGL)
- Check that start date is before end date

**Performance Issues:**
- Large portfolios may take longer to update prices
- The app caches prices to improve performance
- Consider running price updates during off-hours

## 🚀 Key Technologies

- **Backend**: Django 5.2.5, Python 3.8+
- **Database**: SQLite (easily upgradable to PostgreSQL)
- **Data Sources**: Yahoo Finance API, Multiple free financial APIs
- **Charts**: Chart.js for interactive visualizations
- **Reports**: ReportLab for PDF generation
- **Frontend**: Bootstrap 5, responsive design

## 🎯 Extending the App

Easy customization options:
- **Add more data sources**: Implement new API integrations in `free_data_service.py`
- **Custom analytics**: Extend `services.py` with new portfolio metrics
- **Advanced charts**: Add new chart types in the dashboard templates
- **User authentication**: Add Django's built-in user system for multi-user support
- **Real-time updates**: Implement WebSocket connections for live price feeds
- **Mobile app**: Create API endpoints for mobile app integration
- **Cloud deployment**: Deploy to Heroku, AWS, or other cloud platforms

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
