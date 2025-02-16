from market_analyzer import MarketAnalyzer
import json

def print_analysis_results(title, data):
    print("\n" + "="*50)
    print(f"{title}")
    print("="*50)
    if isinstance(data, dict):
        print(json.dumps(data, indent=2))
    else:
        print(data)

def main():
    # Initialize analyzer
    analyzer = MarketAnalyzer()
    
    # List of stocks to analyze
    stocks = ['RELIANCE', 'TCS', 'HDFCBANK']
    
    for stock in stocks:
        print(f"\n\n📊 Analyzing {stock}...")
        
        # Get technical analysis
        tech_analysis = analyzer.get_technical_analysis(stock)
        print_analysis_results("Technical Analysis", tech_analysis)
        
        # Get fundamental analysis
        fundamental = analyzer.get_fundamental_analysis(stock)
        print_analysis_results("Fundamental Analysis", fundamental)
        
        # Get news sentiment
        sentiment = analyzer.get_news_sentiment(stock)
        print_analysis_results("News Sentiment", sentiment)
        
        # Get sector analysis
        sector = analyzer.get_sector_analysis(stock)
        print_analysis_results("Sector Analysis", sector)
        
        print("\n📈 Charts generated:")
        if isinstance(tech_analysis, dict):
            print(f"Technical Chart: {tech_analysis.get('chart_path')}")
        if isinstance(sector, dict):
            print(f"Sector Comparison: {sector.get('chart_path')}")
        
        print("\n" + "-"*70)

if __name__ == "__main__":
    print("🚀 Starting Market Analysis...")
    main()
    print("\n✅ Analysis Complete!") 