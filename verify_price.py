from market_analyzer import MarketAnalyzer
import json
from time import sleep

def print_price_info(symbol, data):
    print(f"\n{'='*60}")
    print(f"Price Verification for {symbol}")
    print(f"{'='*60}")
    
    if isinstance(data, dict):
        # Print average price and reliability
        print(f"\n📊 Summary:")
        print(f"Average Price: ₹{data['average_price']:,.2f}")
        print(f"Price Variance: {data['variance']:.2f}")
        print(f"Reliability: {data['reliability']}")
        print(f"Last Updated: {data['timestamp']}")
        
        # Print individual source prices
        print(f"\n📈 Prices by Source:")
        for source, info in data['sources'].items():
            print(f"\n{source.upper()}:")
            for key, value in info.items():
                if isinstance(value, (int, float)):
                    print(f"  {key}: ₹{value:,.2f}")
                else:
                    print(f"  {key}: {value}")
    else:
        print("Error getting price data")

def main():
    analyzer = MarketAnalyzer()
    
    # List of stocks to verify
    stocks = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'TATAMOTORS']
    
    print("🔍 Starting Price Verification...")
    
    for symbol in stocks:
        print(f"\n\nVerifying {symbol}...")
        price_data = analyzer.verify_price(symbol)
        print_price_info(symbol, price_data)
        
        # Add a small delay between requests
        sleep(2)
    
    print("\n✅ Price verification complete!")

if __name__ == "__main__":
    main() 