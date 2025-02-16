import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
from textblob import TextBlob
import pandas_ta as ta
import json
from pathlib import Path
import time
import os
from plotly.subplots import make_subplots

class MarketAnalyzer:
    def __init__(self):
        self.analysis_dir = Path("market_analysis")
        self.analysis_dir.mkdir(exist_ok=True)
        self.cache_dir = self.analysis_dir / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize technical indicators
        self.indicators = {
            'SMA': [20, 50, 200],  # Simple Moving Averages
            'RSI': 14,             # Relative Strength Index period
            'MACD': [12, 26, 9],   # MACD parameters
            'BB': [20, 2],         # Bollinger Bands parameters
        }

    def get_nse_price(self, symbol):
        """Get price from NSE website"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return {
                    'price': data['priceInfo']['lastPrice'],
                    'change': data['priceInfo']['change'],
                    'change_percent': data['priceInfo']['pChange'],
                    'volume': data['preOpenMarket']['totalTradedVolume'],
                    'timestamp': data['metadata']['lastUpdateTime']
                }
        except:
            return None
            
    def get_money_control_price(self, symbol):
        """Get price from MoneyControl"""
        try:
            url = f"https://www.moneycontrol.com/india/stockpricequote/{symbol}"
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                price_div = soup.find('div', {'class': 'inprice1'})
                if price_div:
                    return float(price_div.text.strip().replace(',', ''))
        except:
            return None
    
    def verify_price(self, symbol):
        """Verify stock price from multiple sources"""
        try:
            # Clean up the symbol and ensure proper format for NSE
            symbol = symbol.upper().strip().replace('.NS', '').replace('&', '%26')
            nse_symbol = f"{symbol}.NS"
            
            sources = {}
            max_retries = 3
            retry_delay = 1
            
            # Get Yahoo Finance price with retries
            for attempt in range(max_retries):
                try:
                    yf_stock = yf.Ticker(nse_symbol)
                    # Get today's data
                    today_data = yf_stock.history(period='1d')
                    if not today_data.empty:
                        sources['yahoo'] = {
                            'price': float(today_data['Close'].iloc[-1]),
                            'open': float(today_data['Open'].iloc[-1]),
                            'high': float(today_data['High'].iloc[-1]),
                            'low': float(today_data['Low'].iloc[-1]),
                            'volume': int(today_data['Volume'].iloc[-1]),
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        break
                except Exception as e:
                    if attempt == max_retries - 1:  # Last attempt
                        print(f"Yahoo Finance error for {symbol} after {max_retries} attempts: {str(e)}")
                    else:
                        time.sleep(retry_delay)
            
            # Try alternative Yahoo Finance method if first method failed
            if 'yahoo' not in sources:
                try:
                    info = yf_stock.info
                    if info and 'regularMarketPrice' in info and info['regularMarketPrice'] is not None:
                        sources['yahoo'] = {
                            'price': float(info['regularMarketPrice']),
                            'open': float(info.get('regularMarketOpen', info['regularMarketPrice'])),
                            'high': float(info.get('regularMarketDayHigh', info['regularMarketPrice'])),
                            'low': float(info.get('regularMarketDayLow', info['regularMarketPrice'])),
                            'volume': int(info.get('regularMarketVolume', 0)),
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                except Exception as e:
                    print(f"Yahoo Finance info error for {symbol}: {str(e)}")
            
            # Try NSE direct API
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Connection': 'keep-alive',
                }
                
                # First get the cookie
                session = requests.Session()
                session.get("https://www.nseindia.com", headers=headers, timeout=5)
                
                # Then get the stock data
                url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
                response = session.get(url, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    sources['nse'] = {
                        'price': float(data['priceInfo']['lastPrice']),
                        'open': float(data['priceInfo']['open']),
                        'high': float(data['priceInfo']['intraDayHighLow']['max']),
                        'low': float(data['priceInfo']['intraDayHighLow']['min']),
                        'volume': int(data['preOpenMarket']['totalTradedVolume']),
                        'timestamp': data['metadata']['lastUpdateTime']
                    }
            except Exception as e:
                print(f"NSE API error for {symbol}: {str(e)}")
            
            # If no data available from any source
            if not sources:
                return {
                    'error': f"Could not fetch data for {symbol}. Please verify the stock symbol.",
                    'sources': {},
                    'average_price': 'N/A',
                    'variance': 'N/A',
                    'reliability': 'N/A',
                    'market_status': 'Unknown',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'price_range': {
                        'min': 'N/A',
                        'max': 'N/A'
                    }
                }
                
            # Calculate average price and variance
            prices = []
            for source_data in sources.values():
                if isinstance(source_data, dict) and 'price' in source_data:
                    if isinstance(source_data['price'], (int, float)) and source_data['price'] > 0:
                        prices.append(source_data['price'])
            
            if prices:
                avg_price = np.mean(prices)
                variance = np.std(prices) if len(prices) > 1 else 0
                price_reliability = "High" if variance < 1 else "Medium" if variance < 5 else "Low"
                
                # Get market status based on Indian market hours (9:15 AM to 3:30 PM IST)
                now = datetime.now()
                market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
                market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
                market_status = "Open" if market_open <= now <= market_close and now.weekday() < 5 else "Closed"
                
                return {
                    'sources': sources,
                    'average_price': avg_price,
                    'variance': variance,
                    'reliability': price_reliability,
                    'market_status': market_status,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'price_range': {
                        'min': min(prices),
                        'max': max(prices)
                    }
                }
            
            return {
                'error': 'No valid price data available',
                'sources': sources,
                'average_price': 'N/A',
                'variance': 'N/A',
                'reliability': 'N/A',
                'market_status': 'Unknown',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'price_range': {
                    'min': 'N/A',
                    'max': 'N/A'
                }
            }
                
        except Exception as e:
            return {
                'error': f"Error verifying price: {str(e)}",
                'sources': {},
                'average_price': 'N/A',
                'variance': 'N/A',
                'reliability': 'N/A',
                'market_status': 'Unknown',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'price_range': {
                    'min': 'N/A',
                    'max': 'N/A'
                }
            }

    def get_technical_analysis(self, symbol, period='1y'):
        """Get technical analysis for a stock"""
        try:
            # Verify current price first
            price_data = self.verify_price(symbol)
            
            # Get historical data
            stock = yf.Ticker(f"{symbol}.NS")
            hist = stock.history(period=period)
            
            # Calculate technical indicators using pandas_ta
            hist.ta.sma(length=20, append=True)
            hist.ta.sma(length=50, append=True)
            hist.ta.rsi(length=14, append=True)
            hist.ta.macd(append=True)
            
            # Add Bollinger Bands
            hist.ta.bbands(length=20, append=True)
            
            # Add Volume Analysis
            hist['Volume_MA'] = hist['Volume'].rolling(window=20).mean()
            volume_trend = "High" if hist['Volume'].iloc[-1] > hist['Volume_MA'].iloc[-1] else "Low"
            
            # Generate signals
            signals = {
                'trend': 'Bullish' if hist['SMA_20'].iloc[-1] > hist['SMA_50'].iloc[-1] else 'Bearish',
                'rsi': 'Overbought' if hist['RSI_14'].iloc[-1] > 70 else 'Oversold' if hist['RSI_14'].iloc[-1] < 30 else 'Neutral',
                'macd': 'Buy' if hist['MACD_12_26_9'].iloc[-1] > hist['MACDs_12_26_9'].iloc[-1] else 'Sell',
                'volume': volume_trend
            }
            
            # Create visualization
            fig = go.Figure()
            
            # Candlestick chart
            fig.add_trace(go.Candlestick(
                x=hist.index,
                open=hist['Open'],
                high=hist['High'],
                low=hist['Low'],
                close=hist['Close'],
                name='Price'
            ))
            
            # Add SMAs
            fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_20'], name='SMA 20', line=dict(color='blue')))
            fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_50'], name='SMA 50', line=dict(color='red')))
            
            # Add Bollinger Bands
            fig.add_trace(go.Scatter(x=hist.index, y=hist['BBU_20_2.0'], name='BB Upper',
                                   line=dict(color='gray', dash='dash')))
            fig.add_trace(go.Scatter(x=hist.index, y=hist['BBL_20_2.0'], name='BB Lower',
                                   line=dict(color='gray', dash='dash')))
            
            # Add volume bars
            fig.add_trace(go.Bar(x=hist.index, y=hist['Volume'], name='Volume',
                               yaxis='y2', marker_color='rgba(0,0,0,0.2)'))
            
            # Update layout
            fig.update_layout(
                title=f'{symbol} Technical Analysis',
                yaxis_title='Price',
                yaxis2=dict(
                    title='Volume',
                    overlaying='y',
                    side='right'
                ),
                xaxis_title='Date',
                height=800
            )
            
            # Save chart
            chart_path = self.analysis_dir / f"{symbol}_technical.html"
            fig.write_html(str(chart_path))
            
            return {
                'price_verification': price_data,
                'signals': signals,
                'current_price': hist['Close'].iloc[-1],
                'chart_path': str(chart_path),
                'indicators': {
                    'rsi': hist['RSI_14'].iloc[-1],
                    'macd': hist['MACD_12_26_9'].iloc[-1],
                    'signal': hist['MACDs_12_26_9'].iloc[-1],
                    'bollinger_upper': hist['BBU_20_2.0'].iloc[-1],
                    'bollinger_lower': hist['BBL_20_2.0'].iloc[-1],
                    'volume': hist['Volume'].iloc[-1],
                    'volume_ma': hist['Volume_MA'].iloc[-1]
                },
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return f"Error in technical analysis: {str(e)}"
    
    def get_news_sentiment(self, symbol):
        """Get news sentiment analysis"""
        try:
            # Get news from multiple sources
            news_sources = [
                f"https://newsapi.org/v2/everything?q={symbol}+stock+market&language=en",
                # Add more news sources
            ]
            
            news_items = []
            sentiments = []
            
            for source in news_sources:
                # This is a placeholder - you'll need actual API keys
                response = requests.get(source)
                if response.status_code == 200:
                    articles = response.json().get('articles', [])
                    for article in articles:
                        # Analyze sentiment
                        blob = TextBlob(article['title'] + " " + article['description'])
                        sentiment = blob.sentiment.polarity
                        sentiments.append(sentiment)
                        
                        news_items.append({
                            'title': article['title'],
                            'sentiment': sentiment,
                            'url': article['url'],
                            'date': article['publishedAt']
                        })
            
            # Calculate overall sentiment
            avg_sentiment = np.mean(sentiments) if sentiments else 0
            sentiment_label = 'Positive' if avg_sentiment > 0.1 else 'Negative' if avg_sentiment < -0.1 else 'Neutral'
            
            return {
                'overall_sentiment': sentiment_label,
                'sentiment_score': avg_sentiment,
                'news_items': news_items[:5],  # Return top 5 news items
                'total_articles': len(news_items)
            }
            
        except Exception as e:
            return f"Error in sentiment analysis: {str(e)}"
    
    def get_fundamental_analysis(self, symbol):
        """Get fundamental analysis of a stock"""
        try:
            stock = yf.Ticker(f"{symbol}.NS")
            info = stock.info
            
            # Calculate key ratios
            pe_ratio = info.get('trailingPE', 'N/A')
            pb_ratio = info.get('priceToBook', 'N/A')
            debt_to_equity = info.get('debtToEquity', 'N/A')
            profit_margins = info.get('profitMargins', 'N/A')
            
            # Get financial statements
            balance_sheet = stock.balance_sheet
            income_stmt = stock.income_stmt
            cash_flow = stock.cashflow
            
            # Calculate growth rates
            if not income_stmt.empty:
                revenue_growth = ((income_stmt.iloc[0]['Total Revenue'] - 
                                 income_stmt.iloc[1]['Total Revenue']) / 
                                income_stmt.iloc[1]['Total Revenue'] * 100)
            else:
                revenue_growth = 'N/A'
            
            analysis = {
                'key_ratios': {
                    'pe_ratio': pe_ratio,
                    'pb_ratio': pb_ratio,
                    'debt_to_equity': debt_to_equity,
                    'profit_margins': profit_margins
                },
                'growth': {
                    'revenue_growth': revenue_growth
                },
                'recommendation': {
                    'rating': info.get('recommendationKey', 'N/A'),
                    'target_price': info.get('targetMeanPrice', 'N/A')
                }
            }
            
            return analysis
            
        except Exception as e:
            return f"Error in fundamental analysis: {str(e)}"
    
    def get_sector_analysis(self, symbol):
        """Get sector performance and comparison"""
        try:
            stock = yf.Ticker(f"{symbol}.NS")
            sector = stock.info.get('sector', '')
            
            # Get sector peers
            peers = stock.info.get('recommendedSymbols', [])
            peer_performance = {}
            
            for peer in peers:
                peer_stock = yf.Ticker(f"{peer}.NS")
                hist = peer_stock.history(period='1y')
                if not hist.empty:
                    yearly_return = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / 
                                   hist['Close'].iloc[0] * 100)
                    peer_performance[peer] = yearly_return
            
            # Create sector comparison chart
            fig = go.Figure([go.Bar(x=list(peer_performance.keys()), 
                                  y=list(peer_performance.values()))])
            fig.update_layout(title=f"{sector} - Peer Comparison")
            
            chart_path = self.analysis_dir / f"{symbol}_sector_comparison.html"
            fig.write_html(str(chart_path))
            
            return {
                'sector': sector,
                'peer_performance': peer_performance,
                'chart_path': str(chart_path)
            }
            
        except Exception as e:
            return f"Error in sector analysis: {str(e)}"
    
    def generate_comprehensive_report(self, symbol):
        """Generate a comprehensive analysis report"""
        technical = self.get_technical_analysis(symbol)
        fundamental = self.get_fundamental_analysis(symbol)
        sentiment = self.get_news_sentiment(symbol)
        sector = self.get_sector_analysis(symbol)
        
        report = {
            'symbol': symbol,
            'analysis_date': datetime.now().isoformat(),
            'technical_analysis': technical,
            'fundamental_analysis': fundamental,
            'sentiment_analysis': sentiment,
            'sector_analysis': sector
        }
        
        # Save report
        report_path = self.analysis_dir / f"{symbol}_comprehensive_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=4)
        
        return report

    def get_market_mood(self):
        """Get overall market mood based on Nifty and key indicators"""
        try:
            # Get Nifty data
            nifty = yf.Ticker("^NSEI")
            nifty_data = nifty.history(period='2d')
            
            if nifty_data.empty:
                return "Unable to determine market mood at the moment."
            
            # Calculate daily change
            current_price = nifty_data['Close'].iloc[-1]
            previous_price = nifty_data['Close'].iloc[-2]
            change_percent = ((current_price - previous_price) / previous_price) * 100
            
            # Get volume trend
            current_volume = nifty_data['Volume'].iloc[-1]
            avg_volume = nifty_data['Volume'].mean()
            volume_trend = "High" if current_volume > avg_volume else "Low"
            
            # Get market breadth (can add more indicators here)
            market_status = "Open" if 9 <= datetime.now().hour < 15 or (datetime.now().hour == 15 and datetime.now().minute <= 30) else "Closed"
            
            # Determine mood based on price change
            mood = ""
            if change_percent > 1.5:
                mood = "🚀 Market is strongly bullish! Showing significant upward momentum."
            elif change_percent > 0.5:
                mood = "📈 Market is mildly bullish. Showing positive sentiment."
            elif change_percent > -0.5:
                mood = "↔️ Market is neutral. Moving sideways with no clear direction."
            elif change_percent > -1.5:
                mood = "📉 Market is mildly bearish. Showing some weakness."
            else:
                mood = "🔻 Market is strongly bearish! Showing significant downward pressure."
            
            # Format detailed response
            response = f"""
Market Mood Analysis:
{mood}

📊 Nifty50 Details:
Current Level: {current_price:,.2f}
Change: {change_percent:.2f}%
Volume Trend: {volume_trend}
Market Status: {market_status}

💡 Key Insights:
• Volume is {volume_trend.lower()} compared to average
• Market is currently {market_status.lower()}
• Trend indicates {'buying' if change_percent > 0 else 'selling'} pressure

Note: This is a technical overview. Please consider fundamental factors as well.
"""
            return response

        except Exception as e:
            return f"""
🔍 Market Mood Analysis:
Currently unable to fetch real-time market mood. 

Possible reasons:
• Market hours: Trading session might be closed
• Data delay: Real-time data feed might be delayed
• Technical issue: Temporary connection problem

Please try:
• Checking NSE website directly
• Waiting a few minutes and trying again
• Using specific stock queries instead

Error details: {str(e)}
"""

    def get_real_time_indicators(self, symbol):
        """Get comprehensive real-time market indicators"""
        try:
            stock = yf.Ticker(f"{symbol}.NS")
            hist = stock.history(period='1y')
            
            if hist.empty:
                return "No data available for the symbol"

            # Calculate all technical indicators
            indicators = {}
            
            # Moving Averages
            for period in self.indicators['SMA']:
                hist[f'SMA_{period}'] = hist['Close'].rolling(window=period).mean()
            
            # RSI
            hist['RSI'] = ta.rsi(hist['Close'], length=self.indicators['RSI'])
            
            # MACD
            macd = ta.macd(hist['Close'], 
                          fast=self.indicators['MACD'][0],
                          slow=self.indicators['MACD'][1],
                          signal=self.indicators['MACD'][2])
            hist = pd.concat([hist, macd], axis=1)
            
            # Bollinger Bands
            bb = ta.bbands(hist['Close'], 
                          length=self.indicators['BB'][0],
                          std=self.indicators['BB'][1])
            hist = pd.concat([hist, bb], axis=1)

            # Support and Resistance Levels
            support, resistance = self._calculate_support_resistance(hist)
            
            # Volume Analysis
            volume_sma = hist['Volume'].rolling(window=20).mean()
            volume_trend = "High" if hist['Volume'].iloc[-1] > volume_sma.iloc[-1] else "Low"

            # Get current values
            current_price = hist['Close'].iloc[-1]
            current_data = {
                'price': current_price,
                'sma_signals': {
                    f'SMA_{period}': {
                        'value': hist[f'SMA_{period}'].iloc[-1],
                        'signal': 'Bullish' if current_price > hist[f'SMA_{period}'].iloc[-1] else 'Bearish'
                    } for period in self.indicators['SMA']
                },
                'rsi': {
                    'value': hist['RSI'].iloc[-1],
                    'signal': 'Overbought' if hist['RSI'].iloc[-1] > 70 else 'Oversold' if hist['RSI'].iloc[-1] < 30 else 'Neutral'
                },
                'macd': {
                    'macd': hist['MACD_12_26_9'].iloc[-1],
                    'signal': hist['MACDs_12_26_9'].iloc[-1],
                    'histogram': hist['MACDh_12_26_9'].iloc[-1],
                    'trend': 'Bullish' if hist['MACD_12_26_9'].iloc[-1] > hist['MACDs_12_26_9'].iloc[-1] else 'Bearish'
                },
                'bollinger_bands': {
                    'upper': hist['BBU_20_2.0'].iloc[-1],
                    'middle': hist['BBM_20_2.0'].iloc[-1],
                    'lower': hist['BBL_20_2.0'].iloc[-1],
                    'position': self._get_bb_position(current_price, hist)
                },
                'support_resistance': {
                    'support_levels': support,
                    'resistance_levels': resistance
                },
                'volume': {
                    'current': hist['Volume'].iloc[-1],
                    'average': volume_sma.iloc[-1],
                    'trend': volume_trend
                }
            }

            # Generate visualization
            self._generate_advanced_charts(hist, symbol, current_data)

            return current_data

        except Exception as e:
            return f"Error calculating real-time indicators: {str(e)}"

    def _calculate_support_resistance(self, data, window=20):
        """Calculate support and resistance levels using pivot points"""
        pivots = []
        supports = []
        resistances = []
        
        for i in range(window, len(data)-window):
            max_val = data['High'].iloc[i-window:i+window].max()
            min_val = data['Low'].iloc[i-window:i+window].min()
            
            if data['High'].iloc[i] == max_val:
                resistances.append(max_val)
            if data['Low'].iloc[i] == min_val:
                supports.append(min_val)
        
        # Get most recent levels
        supports = sorted(list(set([round(s, 2) for s in supports])))[-3:]
        resistances = sorted(list(set([round(r, 2) for r in resistances])))[-3:]
        
        return supports, resistances

    def _get_bb_position(self, price, data):
        """Get position relative to Bollinger Bands"""
        upper = data['BBU_20_2.0'].iloc[-1]
        lower = data['BBL_20_2.0'].iloc[-1]
        
        if price > upper:
            return "Above Upper Band (Overbought)"
        elif price < lower:
            return "Below Lower Band (Oversold)"
        else:
            return "Within Bands (Neutral)"

    def _generate_advanced_charts(self, data, symbol, indicators):
        """Generate advanced technical analysis charts"""
        # Create main figure with subplots
        fig = make_subplots(rows=3, cols=1, 
                           shared_xaxes=True,
                           vertical_spacing=0.05,
                           row_heights=[0.5, 0.25, 0.25])

        # Candlestick chart
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='Price'
        ), row=1, col=1)

        # Add Moving Averages
        colors = ['blue', 'orange', 'purple']
        for period, color in zip(self.indicators['SMA'], colors):
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data[f'SMA_{period}'],
                name=f'SMA {period}',
                line=dict(color=color)
            ), row=1, col=1)

        # Add Bollinger Bands
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['BBU_20_2.0'],
            name='BB Upper',
            line=dict(color='gray', dash='dash')
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['BBL_20_2.0'],
            name='BB Lower',
            line=dict(color='gray', dash='dash'),
            fill='tonexty'
        ), row=1, col=1)

        # Add Volume
        fig.add_trace(go.Bar(
            x=data.index,
            y=data['Volume'],
            name='Volume',
            marker_color='rgba(0,0,0,0.2)'
        ), row=2, col=1)

        # Add RSI
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['RSI'],
            name='RSI'
        ), row=3, col=1)

        # Add RSI levels
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

        # Update layout
        fig.update_layout(
            title=f'{symbol} Technical Analysis',
            yaxis_title='Price',
            yaxis2_title='Volume',
            yaxis3_title='RSI',
            height=1000,
            showlegend=True
        )

        # Save chart
        chart_path = self.analysis_dir / f"{symbol}_advanced_technical.html"
        fig.write_html(str(chart_path))

    def get_market_sentiment(self, symbol):
        """Get comprehensive market sentiment analysis"""
        try:
            # Get news sentiment
            news_sentiment = self.get_news_sentiment(symbol)
            
            # Get technical sentiment
            technical = self.get_technical_analysis(symbol)
            
            # Get sector performance
            sector = self.get_sector_analysis(symbol)
            
            # Get institutional holdings
            stock = yf.Ticker(f"{symbol}.NS")
            inst_holders = stock.institutional_holders
            
            sentiment_data = {
                'news': news_sentiment,
                'technical': technical,
                'sector': sector,
                'institutional': {
                    'holders': inst_holders.to_dict() if isinstance(inst_holders, pd.DataFrame) else None,
                    'summary': self._analyze_institutional_holdings(inst_holders)
                }
            }
            
            return sentiment_data

        except Exception as e:
            return f"Error analyzing market sentiment: {str(e)}"

    def _analyze_institutional_holdings(self, holders):
        """Analyze institutional holdings patterns"""
        if not isinstance(holders, pd.DataFrame) or holders.empty:
            return "No institutional holdings data available"
            
        total_shares = holders['Shares'].sum()
        total_value = holders['Value'].sum()
        
        return {
            'total_shares': total_shares,
            'total_value': total_value,
            'top_holders': holders.nlargest(3, 'Shares').to_dict('records')
        }

    def get_live_news(self, symbol=None, category='market'):
        """Get live news from multiple sources with summaries"""
        try:
            news_items = []
            
            # Get news from NewsAPI
            newsapi_key = os.getenv('NEWSAPI_KEY')
            if newsapi_key:
                base_url = "https://newsapi.org/v2/everything"
                
                # Build query based on input
                if symbol:
                    query = f"{symbol} stock market india"
                else:
                    query = "indian stock market nse bse"
                    
                if category == 'market':
                    query += " market analysis"
                elif category == 'economy':
                    query += " indian economy"
                elif category == 'global':
                    query += " global markets"
                
                params = {
                    'q': query,
                    'apiKey': newsapi_key,
                    'language': 'en',
                    'sortBy': 'publishedAt',
                    'pageSize': 10
                }
                
                response = requests.get(base_url, params=params)
                if response.status_code == 200:
                    articles = response.json().get('articles', [])
                    for article in articles:
                        # Generate summary using TextBlob
                        blob = TextBlob(article['description'] or '')
                        summary = ' '.join([str(sent) for sent in blob.sentences[:2]])
                        
                        # Calculate sentiment
                        sentiment = blob.sentiment.polarity
                        sentiment_label = 'Positive' if sentiment > 0.1 else 'Negative' if sentiment < -0.1 else 'Neutral'
                        
                        news_items.append({
                            'title': article['title'],
                            'summary': summary,
                            'url': article['url'],
                            'source': article['source']['name'],
                            'published_at': article['publishedAt'],
                            'sentiment': sentiment_label,
                            'sentiment_score': sentiment
                        })
            
            # Get news from MoneyControl (Web Scraping)
            try:
                mc_url = "https://www.moneycontrol.com/news/business/markets/"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(mc_url, headers=headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    articles = soup.find_all('li', class_='clearfix')
                    
                    for article in articles[:5]:  # Get top 5 articles
                        title_elem = article.find('h2')
                        if title_elem:
                            title = title_elem.text.strip()
                            link = title_elem.find('a')['href'] if title_elem.find('a') else ''
                            desc_elem = article.find('p')
                            description = desc_elem.text.strip() if desc_elem else ''
                            
                            # Generate summary and sentiment
                            blob = TextBlob(description)
                            summary = ' '.join([str(sent) for sent in blob.sentences[:2]])
                            sentiment = blob.sentiment.polarity
                            sentiment_label = 'Positive' if sentiment > 0.1 else 'Negative' if sentiment < -0.1 else 'Neutral'
                            
                            news_items.append({
                                'title': title,
                                'summary': summary,
                                'url': link,
                                'source': 'MoneyControl',
                                'published_at': datetime.now().isoformat(),
                                'sentiment': sentiment_label,
                                'sentiment_score': sentiment
                            })
            except Exception as e:
                print(f"Error fetching MoneyControl news: {str(e)}")
            
            # Sort news by date
            news_items.sort(key=lambda x: x['published_at'], reverse=True)
            
            # Calculate overall market sentiment
            sentiments = [item['sentiment_score'] for item in news_items]
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
            market_sentiment = 'Positive' if avg_sentiment > 0.1 else 'Negative' if avg_sentiment < -0.1 else 'Neutral'
            
            # Group news by sentiment
            positive_news = [item for item in news_items if item['sentiment'] == 'Positive']
            negative_news = [item for item in news_items if item['sentiment'] == 'Negative']
            neutral_news = [item for item in news_items if item['sentiment'] == 'Neutral']
            
            return {
                'news_items': news_items,
                'market_sentiment': market_sentiment,
                'sentiment_distribution': {
                    'positive': len(positive_news),
                    'negative': len(negative_news),
                    'neutral': len(neutral_news)
                },
                'total_articles': len(news_items),
                'timestamp': datetime.now().isoformat(),
                'category': category
            }
            
        except Exception as e:
            return {
                'error': f"Error fetching live news: {str(e)}",
                'news_items': [],
                'market_sentiment': 'Unknown',
                'sentiment_distribution': {},
                'total_articles': 0,
                'timestamp': datetime.now().isoformat(),
                'category': category
            } 