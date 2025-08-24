from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from stocks.models import Portfolio, Stock, StockPrice
from stocks.services import AlphaVantageService


class Command(BaseCommand):
    help = 'Update current stock prices for all portfolio positions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbols',
            nargs='+',
            help='Specific symbols to update (default: all portfolio symbols)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if prices are recent',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting stock price update...'))
        
        # Get symbols to update
        if options['symbols']:
            symbols = [s.upper() for s in options['symbols']]
        else:
            # Get all symbols from current portfolio
            symbols = list(Portfolio.objects.values_list('stock__symbol', flat=True).distinct())
        
        if not symbols:
            self.stdout.write(self.style.WARNING('No symbols found to update.'))
            return
        
        self.stdout.write(f'Updating prices for {len(symbols)} symbols: {", ".join(symbols)}')
        
        alpha_service = AlphaVantageService()
        updated_count = 0
        error_count = 0
        
        for symbol in symbols:
            try:
                self.stdout.write(f'Updating {symbol}...', ending=' ')
                
                # Get current price from API
                current_price_data = alpha_service.get_current_price(symbol)
                
                if current_price_data and 'price' in current_price_data:
                    current_price = Decimal(str(current_price_data['price']))
                    
                    # Create or update stock record
                    stock, _ = Stock.objects.get_or_create(
                        symbol=symbol,
                        defaults={'company_name': ''}
                    )
                    
                    # Update or create price record for today
                    today = timezone.now().date()
                    price_obj, created = StockPrice.objects.update_or_create(
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
                    
                    action = 'Created' if created else 'Updated'
                    self.stdout.write(
                        self.style.SUCCESS(f'{action} - ${current_price}')
                    )
                    updated_count += 1
                    
                else:
                    self.stdout.write(self.style.ERROR('No price data available'))
                    error_count += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
                error_count += 1
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'Price update completed!'))
        self.stdout.write(f'✅ Successfully updated: {updated_count} symbols')
        if error_count > 0:
            self.stdout.write(f'❌ Errors: {error_count} symbols')
        self.stdout.write('='*50)
