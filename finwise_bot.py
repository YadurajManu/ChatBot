import os
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
from market_analyzer import MarketAnalyzer
from financial_advisor_bot import FinancialAdvisor
import json
import pandas as pd
import torch

class FinWiseBot:
    def __init__(self):
        load_dotenv()
        self.market_analyzer = MarketAnalyzer()
        self.financial_advisor = FinancialAdvisor()
        
        # Initialize AI models with better error handling
        self.models = self._initialize_models()
        
        # Enhanced conversation context
        self.conversation_context = {
            'history': [],
            'max_history': 5,
            'system_prompts': {
                'advisor': self._get_advisor_prompt(),
                'analysis': self._get_analysis_prompt(),
                'portfolio': self._get_portfolio_prompt(),
                'learning': self._get_learning_prompt()
            },
            'user_preferences': {
                'language': 'en',
                'detail_level': 'detailed',
                'risk_profile': 'moderate'
            }
        }
        
        # Initialize modes and commands
        self.modes = {
            'advisor': '🤝 Financial Advisor Mode',
            'analysis': '📊 Market Analysis Mode',
            'portfolio': '💼 Portfolio Management Mode',
            'learning': '📚 Learning Mode'
        }
        
        self.commands = {
            'price': 'Get real-time stock price',
            'analysis': 'Get technical analysis',
            'sentiment': 'Get market sentiment',
            'portfolio': 'View/manage portfolio',
            'calculate': 'Financial calculations',
            'learn': 'Learn about topics',
            'help': 'Show available commands',
            'mode': 'Change interaction mode',
            'preferences': 'Set user preferences'
        }
        
        self.current_mode = 'advisor'
    
    def _initialize_models(self):
        """Initialize all AI models with better error handling"""
        models = {}
        
        # Initialize Gemini
        try:
            genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
            models['gemini'] = {
                'model': genai.GenerativeModel('gemini-pro'),
                'status': 'active',
                'priority': 1
            }
        except Exception as e:
            print(f"Gemini initialization error: {str(e)}")
            models['gemini'] = {'status': 'error', 'error': str(e)}

        # Initialize PaLM
        try:
            import google.generativeai as palm
            palm.configure(api_key=os.getenv('GOOGLE_API_KEY'))
            models['palm'] = {
                'model': palm,
                'status': 'active',
                'priority': 2
            }
        except Exception as e:
            print(f"PaLM initialization error: {str(e)}")
            models['palm'] = {'status': 'error', 'error': str(e)}

        # Initialize HuggingFace
        try:
            from transformers import pipeline
            models['huggingface'] = {
                'model': pipeline('text-generation', 
                                model='facebook/opt-350m',
                                device='cuda' if torch.cuda.is_available() else 'cpu'),
                'status': 'active',
                'priority': 3
            }
        except Exception as e:
            print(f"HuggingFace initialization error: {str(e)}")
            models['huggingface'] = {'status': 'error', 'error': str(e)}

        return models

    def _enhance_prompt(self, base_prompt, mode, query):
        """Enhance the prompt with context and specifics"""
        # Add market context
        market_mood = self.market_analyzer.get_market_mood()
        
        # Add user preferences
        prefs = self.conversation_context['user_preferences']
        
        # Add recent conversation context
        recent_context = "\n".join([
            f"User: {q}\nAssistant: {a}" 
            for q, a in self.conversation_context['history'][-2:]
        ])
        
        enhanced_prompt = f"""
{base_prompt}

Current Market Context:
{market_mood}

User Preferences:
- Detail Level: {prefs['detail_level']}
- Risk Profile: {prefs['risk_profile']}

Recent Conversation:
{recent_context}

Current Query: {query}

Remember to:
1. Be precise and data-driven
2. Use simple language but maintain professionalism
3. Include relevant market context
4. Consider user preferences
5. Provide actionable insights
6. Include appropriate disclaimers
"""
        return enhanced_prompt

    def _get_advisor_prompt(self):
        return """You are FinWise (फाइनवाइज़), a professional AI-powered financial guide specializing in Indian markets.

Key Responsibilities:
1. Provide accurate, research-based financial guidance
2. Explain complex concepts in simple terms
3. Focus on Indian market context
4. Maintain professional yet approachable tone
5. Always include relevant disclaimers

Expertise Areas:
- Indian Stock Markets (NSE/BSE)
- Mutual Funds and SIPs
- Tax Planning (Indian context)
- Risk Management
- Portfolio Diversification
- Retirement Planning

Guidelines:
1. Always start with a clear introduction
2. Use data and facts to support advice
3. Include practical examples
4. Highlight risks and considerations
5. Provide actionable next steps
6. End with appropriate disclaimers

Remember: You are a guide, not a registered financial advisor."""

    def _get_analysis_prompt(self):
        return """You are a technical analysis expert focusing on Indian markets.

Key Responsibilities:
1. Analyze market trends and patterns
2. Interpret technical indicators
3. Provide data-driven insights
4. Explain analysis in clear terms

Focus Areas:
- Technical Analysis
- Market Trends
- Volume Analysis
- Price Action
- Chart Patterns
- Risk Assessment

Guidelines:
1. Start with key findings
2. Support with technical data
3. Explain indicators used
4. Provide clear insights
5. Include risk warnings"""

    def _get_portfolio_prompt(self):
        return """You are a portfolio management specialist for Indian investors.

Key Responsibilities:
1. Portfolio optimization
2. Risk assessment
3. Diversification strategies
4. Performance tracking

Focus Areas:
- Asset Allocation
- Risk Management
- Rebalancing Strategies
- Performance Analysis
- Tax Efficiency

Guidelines:
1. Focus on portfolio health
2. Suggest improvements
3. Consider risk tolerance
4. Include market context
5. Explain recommendations"""

    def _get_learning_prompt(self):
        return """You are a financial education specialist focusing on Indian markets.

Key Responsibilities:
1. Explain financial concepts
2. Provide structured learning
3. Use relevant examples
4. Break down complex topics

Focus Areas:
- Basic Financial Concepts
- Investment Fundamentals
- Market Mechanics
- Risk Management
- Technical Analysis

Guidelines:
1. Start with basics
2. Use simple language
3. Provide examples
4. Include practice exercises
5. Suggest next steps"""

    def _get_enhanced_response(self, query, mode='advisor'):
        """Get enhanced response using multiple AI models with better handling"""
        try:
            # Get and enhance the system prompt
            base_prompt = self.conversation_context['system_prompts'][mode]
            enhanced_prompt = f"""
{base_prompt}

Guidelines for Response Format:
1. Use clear, professional language
2. Structure the response with proper sections and headings
3. Format numbers with proper commas and decimals
4. Include relevant market data when available
5. Always end with a clear disclaimer

Current Mode: {mode}
User Query: {query}

Please provide a professional response following this structure:
1. Brief introduction/summary
2. Detailed explanation with data points
3. Key takeaways or action items
4. Professional disclaimer
"""
            
            # Try models in order of priority
            for model_name, model_info in sorted(
                self.models.items(), 
                key=lambda x: x[1].get('priority', 999) if x[1].get('status') == 'active' else 999
            ):
                if model_info.get('status') != 'active':
                    continue
                    
                try:
                    response = None
                    if model_name == 'gemini':
                        response = model_info['model'].generate_content(enhanced_prompt)
                        if response and response.text:
                            return self._format_response(response.text, mode)
                    
                    elif model_name == 'palm':
                        response = model_info['model'].generate_text(
                            prompt=enhanced_prompt,
                            temperature=0.7,
                            max_output_tokens=1024
                        )
                        if response and response.result:
                            return self._format_response(response.result, mode)
                    
                    elif model_name == 'huggingface':
                        response = model_info['model'](
                            enhanced_prompt,
                            max_length=500,
                            num_return_sequences=1
                        )
                        if response:
                            return self._format_response(response[0]['generated_text'], mode)
                
                except Exception as e:
                    print(f"{model_name} error: {str(e)}")
                    continue

            # If all models fail, use a fallback response
            return self._get_fallback_response(query, mode)

        except Exception as e:
            return f"""
Error Processing Request

We apologize, but we encountered an error while processing your request. 

Suggested Actions:
1. Please try your request again
2. If asking about market data, try using specific commands like:
   • price [SYMBOL]
   • analysis [SYMBOL]
   • market mood
3. Contact support if the issue persists

Technical Details:
{str(e)}

Note: For immediate market information, please visit the NSE website or use your trading platform.
"""

    def _format_response(self, response, mode):
        """Enhanced response formatting with professional styling"""
        # Clean up any random asterisks or unnecessary formatting
        response = response.replace('**', '')
        response = response.replace(':**', ':')
        response = response.replace(':**', ':')
        
        # Add mode-specific prefixes
        mode_headers = {
            'advisor': '💼 Financial Advisory',
            'analysis': '📊 Market Analysis',
            'portfolio': '📈 Portfolio Management',
            'learning': '📚 Investment Education'
        }
        
        response = f"{mode_headers.get(mode, '')}\n\n{response}"
        
        # Format numbers and percentages
        import re
        # Format numbers with commas
        number_pattern = r'(?<!\d)(\d{4,})(?!\d)'
        response = re.sub(number_pattern, lambda m: "{:,}".format(int(m.group(1))), response)
        
        # Format percentages to 2 decimal places
        percentage_pattern = r'(\d+\.?\d*)%'
        response = re.sub(percentage_pattern, lambda m: f"{float(m.group(1)):.2f}%", response)
        
        # Format currency amounts
        currency_pattern = r'₹\s*(\d+\.?\d*)'
        response = re.sub(currency_pattern, lambda m: f"₹{float(m.group(1)):,.2f}", response)
        
        # Add section formatting
        response = response.replace('Summary:', '\n📋 Summary:')
        response = response.replace('Key Points:', '\n🎯 Key Points:')
        response = response.replace('Action Items:', '\n✅ Action Items:')
        response = response.replace('Note:', '\n📝 Note:')
        
        # Ensure proper disclaimer
        if 'disclaimer' not in response.lower():
            response += """

⚠️ Important Disclaimer:
This information is provided for educational purposes only and should not be construed as financial advice. Always conduct your own research and consult with a SEBI-registered financial advisor before making investment decisions. Market investments are subject to risk, and past performance is not indicative of future results."""
        
        return response

    def _get_fallback_response(self, query, mode):
        """Generate a professional fallback response when AI models fail"""
        if 'price' in query.lower():
            # Use market analyzer directly
            symbol = query.split()[-1].upper()
            price_data = self.market_analyzer.verify_price(symbol)
            return self.format_price_data(symbol, price_data)
        
        elif 'analysis' in query.lower():
            # Use technical analysis directly
            symbol = query.split()[-1].upper()
            analysis = self.market_analyzer.get_technical_analysis(symbol)
            return self.format_technical_analysis(symbol, analysis)
        
        else:
            return f"""
We apologize for the inconvenience. Our AI response system is currently unavailable.

Alternative Options:
1. Use Direct Market Commands:
   • price [SYMBOL] - Get current stock prices
   • analysis [SYMBOL] - View technical analysis
   • market mood - Check market sentiment

2. Access Basic Functions:
   • View your portfolio: 'show portfolio'
   • Calculate investments: 'calculate sip'
   • Learn about topics: 'learn stocks'

3. Market Resources:
   • NSE: www.nseindia.com
   • BSE: www.bseindia.com
   • Market News: www.moneycontrol.com

Please try your request again in a few moments. If you need immediate assistance, consider using one of the direct commands listed above.

Note: For real-time market data and critical trading decisions, please use your authorized trading platform."""

    def show_help(self):
        help_text = """
🤖 FinWise Bot Commands:

1. Price Commands:
   - 'price SYMBOL' - Get real-time price
   - 'analysis SYMBOL' - Get technical analysis
   - 'sentiment SYMBOL' - Get market sentiment

2. Portfolio Commands:
   - 'create portfolio' - Create new portfolio
   - 'add stock SYMBOL QUANTITY PRICE' - Add stock
   - 'show portfolio' - View portfolio
   
3. Calculator Commands:
   - 'calculate sip AMOUNT YEARS RETURN' - SIP calculator
   - 'calculate emi AMOUNT RATE YEARS' - EMI calculator
   
4. Mode Commands:
   - 'mode advisor' - Switch to advisor mode
   - 'mode analysis' - Switch to analysis mode
   - 'mode portfolio' - Switch to portfolio mode
   - 'mode learning' - Switch to learning mode

5. Learning Commands:
   - 'learn stocks' - Learn about stocks
   - 'learn mutual_funds' - Learn about mutual funds
   - 'learn technical' - Learn technical analysis
   
6. Market Commands:
   - 'market mood' - Get market sentiment
   - 'top gainers' - Show top gaining stocks
   - 'top losers' - Show top losing stocks

Type 'quit' to exit
"""
        return help_text
    
    def process_command(self, user_input):
        """Process user commands with enhanced AI responses"""
        input_lower = user_input.lower().strip()
        
        # First check for special commands
        special_response = self.financial_advisor.process_special_commands(user_input)
        if special_response:
            return special_response
            
        # Check for mode change
        if input_lower.startswith('mode '):
            requested_mode = input_lower.split()[1]
            if requested_mode in self.modes:
                self.current_mode = requested_mode
                return f"Switched to {self.modes[requested_mode]}"
        
        # Get AI response based on current mode
        response = self._get_enhanced_response(user_input, self.current_mode)
        
        # Update conversation history
        self.conversation_context['history'].append((user_input, response))
        if len(self.conversation_context['history']) > self.conversation_context['max_history']:
            self.conversation_context['history'].pop(0)
        
        return response
    
    def format_price_data(self, symbol, data):
        """Format price data with enhanced styling and structure"""
        try:
            if isinstance(data, dict) and 'error' in data:
                return f"""
❌ Price Data Error for {symbol}
{'='*50}
{data['error']}

Please:
• Verify the stock symbol
• Try again in a few moments
• Check if markets are open
"""

            output = f"""
📊 Price Analysis: {symbol}
{'='*50}

💰 Current Trading Status
{'─'*50}"""
            
            if isinstance(data['average_price'], (int, float)):
                price_change = data.get('price_change', 0)
                change_color = "🟢" if price_change >= 0 else "🔴"
                change_arrow = "↗️" if price_change >= 0 else "↘️"
                
                output += f"""
Current Price    : ₹{data['average_price']:,.2f} {change_arrow}
Market Status    : {data['market_status']}
Data Reliability : {data['reliability']}

📈 Today's Range
{'─'*50}
High            : ₹{data['price_range']['max']:,.2f}
Low             : ₹{data['price_range']['min']:,.2f}
"""

            if data['sources']:
                output += f"""
📡 Source Analysis
{'─'*50}"""
                
                for source, info in data['sources'].items():
                    output += f"\n{source.upper()}:"
                    for key, value in info.items():
                        if isinstance(value, (int, float)):
                            if 'price' in key.lower():
                                output += f"\n  • {key}: ₹{value:,.2f}"
                            elif 'volume' in key.lower():
                                output += f"\n  • {key}: {value:,.0f}"
                            else:
                                output += f"\n  • {key}: {value:,.2f}"
                        else:
                            output += f"\n  • {key}: {value}"

            output += f"""

⏰ Last Updated
{'─'*50}
{data['timestamp']}

ℹ️ Note: Prices may be delayed by 15 minutes for NSE/BSE data.
"""
            return output

        except Exception as e:
            return f"""
❌ Error Formatting Price Data

We encountered an error while formatting the price data for {symbol}.
Error details: {str(e)}

Please try:
1. Refreshing the price data
2. Verifying the stock symbol
3. Checking your internet connection
"""

    def format_technical_analysis(self, symbol, data):
        """Format technical analysis with enhanced styling and structure"""
        try:
            output = f"""
📈 Technical Analysis Report: {symbol}
{'='*50}

🎯 Signal Summary
{'─'*50}"""
            
            # Add trend indicators with colors and arrows
            trend_indicators = {
                'Bullish': ('🟢', '↗️'),
                'Bearish': ('🔴', '↘️'),
                'Neutral': ('⚪', '↔️')
            }
            
            for signal, value in data['signals'].items():
                color, arrow = trend_indicators.get(value, ('⚪', '↔️'))
                output += f"\n{signal.title():<12}: {color} {value} {arrow}"

            output += f"""

📊 Key Technical Indicators
{'─'*50}
RSI (14)        : {data['indicators']['rsi']:.2f}
MACD            : {data['indicators']['macd']:.2f}
Signal Line     : {data['indicators']['signal']:.2f}

💰 Price Levels
{'─'*50}
Current Price   : ₹{data['current_price']:,.2f}
Bollinger Bands : 
  • Upper Band  : ₹{data['indicators']['bollinger_upper']:,.2f}
  • Lower Band  : ₹{data['indicators']['bollinger_lower']:,.2f}

📈 Volume Analysis
{'─'*50}
Current Volume  : {data['indicators']['volume']:,.0f}
20-Day Avg Vol  : {data['indicators']['volume_ma']:,.0f}
Volume Trend    : {data['signals']['volume']}

🔍 Technical Charts
{'─'*50}
Detailed charts available at: {data['chart_path']}

⚠️ Important Note:
• Technical analysis is one of many tools for market analysis
• Past performance does not guarantee future results
• Consider multiple indicators and time frames
• Always use stop-loss orders for risk management
"""
            return output

        except Exception as e:
            return f"""
❌ Error in Technical Analysis

We encountered an error while analyzing {symbol}.
Error details: {str(e)}

Please try:
1. Refreshing the analysis
2. Checking data availability
3. Verifying the stock symbol
"""

    def format_portfolio_summary(self, data):
        """Format portfolio summary with enhanced styling and structure"""
        if isinstance(data, str):
            return f"""
📊 Portfolio Status
{'='*50}
{data}
"""
        
        try:
            output = """
💼 Portfolio Summary Report
{'='*50}

📈 Holdings Overview
"""
            # Add holdings table
            output += """
┌─────────────┬──────────┬────────────────┬────────────────┬───────────┐
│   Symbol    │ Quantity │ Invested Value │ Current Value  │   P/L %   │
├─────────────┼──────────┼────────────────┼────────────────┼───────────┤"""

            for stock in data["summary"]:
                profit_loss_color = "🟢" if stock['profit_loss'] > 0 else "🔴"
                trend_arrow = "↗️" if stock['profit_loss'] > 0 else "↘️"
                
                output += f"""
│ {stock['symbol']:<10} │ {stock['quantity']:>8.2f} │ ₹{stock['investment']:>12,.2f} │ ₹{stock['current_value']:>12,.2f} │ {profit_loss_color}{stock['profit_loss_percent']:>6.2f}% {trend_arrow} │"""

            output += """
└─────────────┴──────────┴────────────────┴────────────────┴───────────┘"""

            # Add portfolio metrics
            total_pl_color = "🟢" if data['total_profit_loss'] > 0 else "🔴"
            total_pl_arrow = "↗️" if data['total_profit_loss'] > 0 else "↘️"
            
            output += f"""

💰 Portfolio Valuation
{'─'*50}
Total Investment      : ₹{data['total_investment']:,.2f}
Current Value        : ₹{data['current_value']:,.2f}
Overall Profit/Loss  : {total_pl_color} ₹{abs(data['total_profit_loss']):,.2f} ({data['total_profit_loss_percent']:.2f}%) {total_pl_arrow}

📊 Portfolio Metrics
{'─'*50}"""

            if 'metrics' in data:
                output += f"""
Diversification Score: {data['metrics']['diversification_score']}/10
Risk Level          : {data['metrics']['risk_level']}
"""
                if data['metrics'].get('suggested_actions'):
                    output += "\n🎯 Suggested Actions:"
                    for action in data['metrics']['suggested_actions']:
                        output += f"\n• {action}"

            # Add chart information if available
            if 'chart_path' in data:
                output += f"""

📈 Portfolio Visualization
{'─'*50}
Chart available at: {data['chart_path']}"""

            # Add disclaimer
            output += """

⚠️ Important Notes:
• Past performance is not indicative of future results
• Market values are subject to change
• Consider consulting a financial advisor for personalized advice
"""
            return output

        except Exception as e:
            return f"""
❌ Error Formatting Portfolio Summary

We encountered an error while formatting your portfolio summary.
Error details: {str(e)}

Please try:
1. Refreshing your portfolio data
2. Checking individual stock details
3. Contacting support if the issue persists
"""

    def get_learning_content(self, topic):
        """Get educational content based on topic"""
        topics = {
            'stocks': """
📚 Introduction to Stocks

What are Stocks?
- Stocks represent ownership in a company
- When you buy a stock, you become a shareholder

Key Concepts:
1. Share Price: Market value of one share
2. Market Cap: Total value of the company
3. Dividends: Profits distributed to shareholders
4. Trading: Buying and selling shares

How to Start:
1. Open a demat account
2. Choose a reliable broker
3. Start with blue-chip companies
4. Diversify your investments

Risk Management:
- Never invest all money in one stock
- Research before investing
- Keep track of company news
- Set stop-loss orders

⚠️ Disclaimer: This is educational content. Consult a SEBI registered advisor for personalized advice.
""",
            'mutual_funds': """
📚 Understanding Mutual Funds

What are Mutual Funds?
- Professional managed investment pools
- Money collected from many investors
- Invested in stocks, bonds, etc.

Types of Mutual Funds:
1. Equity Funds
2. Debt Funds
3. Hybrid Funds
4. Index Funds

Key Concepts:
- NAV (Net Asset Value)
- Expense Ratio
- Exit Load
- Fund Management

How to Invest:
1. Choose fund type based on goals
2. Start SIP for regular investing
3. Track performance regularly
4. Stay invested for long term

⚠️ Disclaimer: This is educational content. Consult a SEBI registered advisor for personalized advice.
""",
            'technical': """
📚 Technical Analysis Basics

What is Technical Analysis?
- Study of price movements
- Uses charts and patterns
- Helps predict future trends

Key Indicators:
1. Moving Averages (SMA, EMA)
2. RSI (Relative Strength Index)
3. MACD (Moving Average Convergence Divergence)
4. Bollinger Bands

Chart Patterns:
- Head and Shoulders
- Double Top/Bottom
- Triangle Patterns
- Support and Resistance

Volume Analysis:
- Volume confirms trends
- High volume = strong movement
- Low volume = weak movement

⚠️ Disclaimer: This is educational content. Past performance doesn't guarantee future results.
"""
        }
        
        return topics.get(topic, "Topic not found in learning database")

    def format_market_analysis(self, symbol, data):
        """Format comprehensive market analysis with enhanced styling"""
        try:
            output = f"""
📊 Comprehensive Market Analysis: {symbol}
{'='*50}

💹 Real-Time Technical Indicators
{'─'*50}"""
            
            # Add Moving Average signals
            output += "\n📈 Moving Averages:"
            for sma, info in data['sma_signals'].items():
                trend_arrow = "↗️" if info['signal'] == 'Bullish' else "↘️"
                output += f"\n• {sma}: ₹{info['value']:,.2f} ({info['signal']}) {trend_arrow}"
            
            # Add RSI
            rsi_color = "🔴" if data['rsi']['signal'] == 'Overbought' else "🟢" if data['rsi']['signal'] == 'Oversold' else "⚪"
            output += f"""

📊 Momentum Indicators
{'─'*50}
• RSI (14): {rsi_color} {data['rsi']['value']:.2f} ({data['rsi']['signal']})
• MACD: {'🟢' if data['macd']['trend'] == 'Bullish' else '🔴'} {data['macd']['macd']:.2f}
  - Signal: {data['macd']['signal']:.2f}
  - Histogram: {data['macd']['histogram']:.2f}
  - Trend: {data['macd']['trend']}"""

            # Add Bollinger Bands
            output += f"""

📈 Price Bands & Levels
{'─'*50}
• Bollinger Bands:
  - Upper: ₹{data['bollinger_bands']['upper']:,.2f}
  - Middle: ₹{data['bollinger_bands']['middle']:,.2f}
  - Lower: ₹{data['bollinger_bands']['lower']:,.2f}
  - Status: {data['bollinger_bands']['position']}

• Support Levels:"""
            for level in data['support_resistance']['support_levels']:
                output += f"\n  - ₹{level:,.2f}"
            
            output += "\n• Resistance Levels:"
            for level in data['support_resistance']['resistance_levels']:
                output += f"\n  - ₹{level:,.2f}"

            # Add Volume Analysis
            volume_color = "🟢" if data['volume']['trend'] == 'High' else "🔴"
            output += f"""

📊 Volume Analysis
{'─'*50}
• Current Volume: {data['volume']['current']:,.0f}
• Average Volume: {data['volume']['average']:,.0f}
• Volume Trend: {volume_color} {data['volume']['trend']}"""

            # Add chart information
            output += f"""

📈 Technical Charts
{'─'*50}
Advanced technical charts have been generated and saved.
View the interactive charts for detailed analysis.

⚠️ Important Notes:
• Technical indicators should not be used in isolation
• Consider multiple timeframes for better analysis
• Always use proper risk management
• Past performance does not guarantee future results
"""
            return output

        except Exception as e:
            return f"""
❌ Error Formatting Market Analysis

We encountered an error while formatting the analysis for {symbol}.
Error details: {str(e)}

Please try:
1. Refreshing the analysis
2. Checking data availability
3. Verifying the stock symbol
"""

    def format_sentiment_analysis(self, symbol, data):
        """Format sentiment analysis with enhanced styling"""
        try:
            output = f"""
🎯 Market Sentiment Analysis: {symbol}
{'='*50}

📰 News Sentiment
{'─'*50}
Overall Sentiment: {data['news']['overall_sentiment']}
Sentiment Score: {data['news']['sentiment_score']:.2f}
Articles Analyzed: {data['news']['total_articles']}

Recent News Headlines:"""
            
            for item in data['news']['news_items']:
                sentiment_color = "🟢" if item['sentiment'] > 0 else "🔴" if item['sentiment'] < 0 else "⚪"
                output += f"\n• {sentiment_color} {item['title']}"

            # Add Technical Sentiment
            output += f"""

📊 Technical Sentiment
{'─'*50}"""
            for signal, value in data['technical']['signals'].items():
                trend_color = "🟢" if value in ['Bullish', 'High'] else "🔴" if value in ['Bearish', 'Low'] else "⚪"
                output += f"\n• {signal}: {trend_color} {value}"

            # Add Sector Analysis
            output += f"""

🏢 Sector Analysis
{'─'*50}
Sector: {data['sector']['sector']}

Peer Comparison:"""
            
            for peer, performance in data['sector']['peer_performance'].items():
                perf_color = "🟢" if performance > 0 else "🔴"
                output += f"\n• {peer}: {perf_color} {performance:.2f}%"

            # Add Institutional Holdings
            if isinstance(data['institutional']['summary'], dict):
                output += f"""

🏛️ Institutional Holdings
{'─'*50}
Total Shares: {data['institutional']['summary']['total_shares']:,.0f}
Total Value: ₹{data['institutional']['summary']['total_value']:,.2f}

Top Holders:"""
                
                for holder in data['institutional']['summary']['top_holders']:
                    output += f"\n• {holder['Holder']}: {holder['Shares']:,.0f} shares"

            output += """

⚠️ Important Notes:
• Sentiment analysis is one of many tools for market analysis
• News sentiment can change rapidly
• Consider multiple data points for decision making
• Always conduct thorough research before investing
"""
            return output

        except Exception as e:
            return f"""
❌ Error Formatting Sentiment Analysis

We encountered an error while formatting the sentiment analysis for {symbol}.
Error details: {str(e)}

Please try:
1. Refreshing the analysis
2. Checking data availability
3. Verifying the stock symbol
"""

    def format_live_news(self, data, show_summaries=True):
        """Format live news with enhanced styling and summaries"""
        try:
            if 'error' in data:
                return f"""
❌ News Fetch Error
{'='*50}
{data['error']}

Please try:
1. Checking your internet connection
2. Verifying API keys
3. Trying again in a few moments
"""

            output = f"""
📰 Live Market News
{'='*50}

📊 Sentiment Overview
{'─'*50}
Overall Market Sentiment: {self._get_sentiment_emoji(data['market_sentiment'])} {data['market_sentiment']}

Sentiment Distribution:
• Positive News: 🟢 {data['sentiment_distribution']['positive']} articles
• Negative News: 🔴 {data['sentiment_distribution']['negative']} articles
• Neutral News:  ⚪ {data['sentiment_distribution']['neutral']} articles

📈 Latest Updates
{'─'*50}"""

            # Group news by source
            news_by_source = {}
            for item in data['news_items']:
                source = item['source']
                if source not in news_by_source:
                    news_by_source[source] = []
                news_by_source[source].append(item)

            # Display news grouped by source
            for source, items in news_by_source.items():
                output += f"\n\n📱 {source}"
                for item in items:
                    sentiment_emoji = self._get_sentiment_emoji(item['sentiment'])
                    published = datetime.fromisoformat(item['published_at'].replace('Z', '+00:00'))
                    time_ago = self._get_time_ago(published)
                    
                    output += f"\n\n{sentiment_emoji} {item['title']}"
                    if show_summaries and item['summary']:
                        output += f"\n   📝 {item['summary']}"
                    output += f"\n   🔗 {item['url']}"
                    output += f"\n   ⏰ {time_ago}"

            output += f"""

📊 News Statistics
{'─'*50}
• Total Articles: {data['total_articles']}
• Category: {data['category'].title()}
• Last Updated: {datetime.fromisoformat(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}

⚠️ Disclaimer:
• News sentiment is analyzed automatically and may not be 100% accurate
• Always verify news from multiple sources
• Trading decisions should not be based solely on news sentiment
"""
            return output

        except Exception as e:
            return f"""
❌ Error Formatting News

We encountered an error while formatting the news feed.
Error details: {str(e)}

Please try:
1. Refreshing the news feed
2. Checking your internet connection
3. Verifying the news sources are accessible
"""

    def _get_sentiment_emoji(self, sentiment):
        """Get appropriate emoji for sentiment"""
        return {
            'Positive': '🟢',
            'Negative': '🔴',
            'Neutral': '⚪',
            'Unknown': '❓'
        }.get(sentiment, '❓')

    def _get_time_ago(self, timestamp):
        """Convert timestamp to relative time"""
        now = datetime.now(timestamp.tzinfo)
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours} hours ago"
        minutes = (diff.seconds % 3600) // 60
        if minutes > 0:
            return f"{minutes} minutes ago"
        return "Just now"

def main():
    bot = FinWiseBot()
    
    print("🤖 Welcome to FinWise - Your Comprehensive Financial Assistant!")
    print("\nAvailable Modes:")
    for mode, description in bot.modes.items():
        print(f"- {description}")
    print("\nType 'help' for available commands")
    
    while True:
        try:
            user_input = input(f"\n[{bot.modes[bot.current_mode]}] Your query: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n👋 Thank you for using FinWise! Have a prosperous day!")
                break
            
            if not user_input:
                continue
            
            response = bot.process_command(user_input)
            print(f"\n{response}")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye! Have a great day!")
            break
        except Exception as e:
            print(f"❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 