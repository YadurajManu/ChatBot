import os
import time
import json
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
from pathlib import Path
import random
from portfolio_manager import PortfolioManager

# Load environment variables
load_dotenv()

# Configure Google Gemini API
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

class MarketData:
    """Class to handle market data operations"""
    
    @staticmethod
    def get_stock_info(symbol):
        """Get real-time stock information"""
        try:
            # Add .NS for NSE stocks
            if not symbol.endswith('.NS'):
                symbol = f"{symbol}.NS"
            stock = yf.Ticker(symbol)
            info = stock.info
            current_price = info.get('currentPrice', 'N/A')
            day_high = info.get('dayHigh', 'N/A')
            day_low = info.get('dayLow', 'N/A')
            volume = info.get('volume', 'N/A')
            pe_ratio = info.get('trailingPE', 'N/A')
            market_cap = info.get('marketCap', 'N/A')
            dividend_yield = info.get('dividendYield', 'N/A')
            if dividend_yield != 'N/A':
                dividend_yield = round(dividend_yield * 100, 2)
            
            return {
                'price': current_price,
                'day_high': day_high,
                'day_low': day_low,
                'volume': volume,
                'name': info.get('longName', symbol),
                'pe_ratio': pe_ratio,
                'market_cap': market_cap,
                'dividend_yield': dividend_yield
            }
        except Exception as e:
            return f"Error fetching stock data: {str(e)}"

    @staticmethod
    def get_mutual_fund_info(scheme_code):
        """Get mutual fund information from AMFI"""
        try:
            url = f"https://api.mfapi.in/mf/{scheme_code}"
            response = requests.get(url)
            data = response.json()
            return data
        except Exception as e:
            return f"Error fetching mutual fund data: {str(e)}"

    @staticmethod
    def get_market_mood():
        """Get overall market mood based on Nifty"""
        try:
            nifty = yf.Ticker("^NSEI")
            info = nifty.info
            current = info.get('regularMarketPrice', 0)
            previous = info.get('regularMarketPreviousClose', 0)
            change = ((current - previous) / previous) * 100
            
            if change > 1.5:
                return "🚀 Market is super bullish today! Time to ride the wave!"
            elif change > 0.5:
                return "📈 Market is showing positive vibes!"
            elif change > -0.5:
                return "😐 Market is taking a coffee break, staying neutral."
            elif change > -1.5:
                return "📉 Market is feeling a bit under the weather."
            else:
                return "🐻 Bears are having a party today! Stay cautious!"
        except:
            return "🤔 Market seems to be playing hide and seek with us!"

class FinancialCalculator:
    """Class for financial calculations"""
    
    @staticmethod
    def calculate_sip_returns(monthly_investment, years, expected_return):
        """Calculate SIP returns"""
        monthly_rate = expected_return / (12 * 100)
        months = years * 12
        future_value = monthly_investment * ((pow(1 + monthly_rate, months) - 1) / monthly_rate) * (1 + monthly_rate)
        total_investment = monthly_investment * months
        returns = future_value - total_investment
        
        # Calculate XIRR
        xirr = ((pow((future_value/total_investment), (1/years))) - 1) * 100
        
        return {
            'future_value': round(future_value, 2),
            'total_investment': round(total_investment, 2),
            'returns': round(returns, 2),
            'xirr': round(xirr, 2)
        }

    @staticmethod
    def calculate_lumpsum_returns(principal, years, expected_return):
        """Calculate lumpsum investment returns"""
        future_value = principal * pow(1 + expected_return/100, years)
        returns = future_value - principal
        
        return {
            'future_value': round(future_value, 2),
            'total_investment': principal,
            'returns': round(returns, 2)
        }
        
    @staticmethod
    def calculate_emi(principal, rate, years):
        """Calculate EMI for loans"""
        monthly_rate = rate / (12 * 100)
        months = years * 12
        emi = (principal * monthly_rate * pow(1 + monthly_rate, months)) / (pow(1 + monthly_rate, months) - 1)
        total_payment = emi * months
        total_interest = total_payment - principal
        
        return {
            'emi': round(emi, 2),
            'total_payment': round(total_payment, 2),
            'total_interest': round(total_interest, 2)
        }

class FinancialAdvisor:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
        self.conversation_history = []
        self.max_retries = 3
        self.retry_delay = 1
        self.market_data = MarketData()
        self.calculator = FinancialCalculator()
        self.portfolio_manager = PortfolioManager()
        
        # Create necessary directories
        self.advice_dir = Path("saved_advice")
        self.charts_dir = Path("charts")
        for directory in [self.advice_dir, self.charts_dir]:
            directory.mkdir(exist_ok=True)
            
        # Fun money quotes for random display
        self.money_quotes = [
            "Remember: Money is like a good joke - it's all about the timing! 😄",
            "Investing is like cooking - follow the recipe but don't forget to taste! 🍳",
            "Your portfolio is like a garden - it needs both flowers and vegetables! 🌺🥕",
            "Markets are like Mumbai traffic - sometimes you just have to be patient! 🚦",
            "SIP is like morning chai - best when regular! ☕",
            "Diversification is like having backup snacks - always a good idea! 🍫",
            "Your financial goals are like GPS - they show you the way! 🗺️",
            "Risk management is like carrying an umbrella - better safe than sorry! ☔"
        ]

    def get_random_quote(self):
        """Get a random money quote"""
        return random.choice(self.money_quotes)

    def format_response(self, text):
        """Format the response for better readability"""
        text = text.replace("Disclaimer:", "⚠️ Disclaimer:")
        text = text.replace("Note:", "📝 Note:")
        text = text.replace("Warning:", "⚠️ Warning:")
        text = text.replace("Tip:", "💡 Tip:")
        text = text.replace("Action Items:", "✅ Action Items:")
        text = text.replace("Risk Level:", "🎯 Risk Level:")
        text = text.replace("Tax Implications:", "💰 Tax Implications:")
        text = text.replace("Pro Tip:", "🎯 Pro Tip:")
        return text

    def save_advice(self, question, advice):
        """Save important financial advice to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.advice_dir / f"financial_advice_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write(f"Question: {question}\n\n")
            f.write(f"Advice:\n{advice}\n")
            f.write(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            f.write(f"\n\nFun Quote: {self.get_random_quote()}")
        
        return filename

    def process_special_commands(self, query, user_id="default"):
        """Process special commands for real-time data and calculations"""
        query_lower = query.lower()
        
        # Portfolio Commands
        if query_lower.startswith("create portfolio"):
            return self.portfolio_manager.create_portfolio(user_id)
            
        if query_lower.startswith("add stock"):
            # Format: add stock SYMBOL QUANTITY PRICE
            parts = query.split()
            if len(parts) >= 5:
                symbol = parts[2].upper()
                quantity = float(parts[3])
                price = float(parts[4])
                return self.portfolio_manager.add_stock(user_id, symbol, quantity, price)
            return "Please use format: add stock SYMBOL QUANTITY PRICE"
            
        if query_lower.startswith("show portfolio"):
            summary = self.portfolio_manager.get_portfolio_summary(user_id)
            if isinstance(summary, str):
                return summary
                
            # Format the summary nicely
            response = "📊 Your Portfolio Summary:\n\n"
            for stock in summary["summary"]:
                response += f"""
{stock['symbol']}:
Quantity: {stock['quantity']}
Current Value: ₹{stock['current_value']:,.2f}
Profit/Loss: ₹{stock['profit_loss']:,.2f} ({stock['profit_loss_percent']:.2f}%)
------------------------"""
            
            response += f"""
\n📈 Overall Portfolio:
Total Investment: ₹{summary['total_investment']:,.2f}
Current Value: ₹{summary['current_value']:,.2f}
Total Profit/Loss: ₹{summary['total_profit_loss']:,.2f} ({summary['total_profit_loss_percent']:.2f}%)
"""
            
            # Generate and add chart
            chart_path = self.portfolio_manager.generate_portfolio_chart(user_id)
            if not isinstance(chart_path, str) or "error" in chart_path.lower():
                response += "\n❌ Could not generate portfolio chart."
            else:
                response += f"\n📊 Portfolio allocation chart saved to: {chart_path}"
            
            # Add portfolio metrics
            metrics = self.portfolio_manager.get_portfolio_metrics(user_id)
            if not isinstance(metrics, str):
                response += f"""
\n📊 Portfolio Metrics:
Diversification Score: {metrics['diversification_score']}
Risk Level: {metrics['risk_level']}
Suggested Actions: {', '.join(metrics['suggested_actions'])}
"""
            
            return response

        # Market Mood
        if "market mood" in query_lower or "market status" in query_lower:
            return self.market_data.get_market_mood()
        
        # Stock price check
        if "stock price" in query_lower or "stock info" in query_lower:
            words = query.split()
            for word in words:
                if word.isalpha() and len(word) >= 2:
                    stock_info = self.market_data.get_stock_info(word.upper())
                    if isinstance(stock_info, dict):
                        market_cap_str = 'N/A'
                        if stock_info['market_cap'] != 'N/A':
                            market_cap_str = f"₹{stock_info['market_cap']:,.0f}"
                        
                        return f"""
📈 Stock Information for {stock_info['name']}:
Current Price: ₹{stock_info['price']}
Day High: ₹{stock_info['day_high']}
Day Low: ₹{stock_info['day_low']}
Volume: {stock_info['volume']}
P/E Ratio: {stock_info['pe_ratio']}
Market Cap: {market_cap_str}
Dividend Yield: {stock_info['dividend_yield']}%

{self.get_random_quote()}
"""
        
        # SIP Calculator
        if "calculate sip" in query_lower:
            try:
                numbers = [float(s) for s in query.split() if s.replace('.','').isdigit()]
                if len(numbers) >= 3:
                    result = self.calculator.calculate_sip_returns(numbers[0], numbers[1], numbers[2])
                    return f"""
💰 SIP Calculator Results:
Monthly Investment: ₹{numbers[0]:,.2f}
Time Period: {numbers[1]} years
Expected Return: {numbers[2]}%

Future Value: ₹{result['future_value']:,.2f}
Total Investment: ₹{result['total_investment']:,.2f}
Expected Returns: ₹{result['returns']:,.2f}
XIRR: {result['xirr']}%

{self.get_random_quote()}
"""
            except Exception as e:
                return f"Error in SIP calculation: {str(e)}"
        
        # EMI Calculator
        if "calculate emi" in query_lower:
            try:
                numbers = [float(s) for s in query.split() if s.replace('.','').isdigit()]
                if len(numbers) >= 3:
                    result = self.calculator.calculate_emi(numbers[0], numbers[1], numbers[2])
                    return f"""
💳 EMI Calculator Results:
Loan Amount: ₹{numbers[0]:,.2f}
Interest Rate: {numbers[1]}%
Loan Term: {numbers[2]} years

Monthly EMI: ₹{result['emi']:,.2f}
Total Payment: ₹{result['total_payment']:,.2f}
Total Interest: ₹{result['total_interest']:,.2f}

{self.get_random_quote()}
"""
            except Exception as e:
                return f"Error in EMI calculation: {str(e)}"
        
        return None

    def get_financial_advice(self, user_query):
        """Get financial advice with Indian context and real-time data"""
        # First check for special commands
        special_response = self.process_special_commands(user_query)
        if special_response:
            return special_response
        
        # System message with Indian context
        context = """You are FinWise (फाइनवाइज़), a friendly AI-powered financial guide (not an advisor) with knowledge about:
        1. Indian Stock Markets (NSE/BSE)
        2. Mutual Funds and SIP investments
        3. Tax-saving instruments (ELSS, PPF, NPS)
        4. Portfolio diversification
        5. Risk management
        6. Indian tax laws and regulations
        7. Retirement planning
        8. Insurance planning
        
        Your personality:
        - Friendly and approachable, like a knowledgeable friend
        - Use simple language and relatable Indian examples
        - Add occasional humor but maintain professionalism
        - Use relevant analogies from daily Indian life
        - Be encouraging but realistic
        
        Important guidelines:
        - Always clarify that you're an AI guide providing general information
        - Encourage users to verify information with registered financial advisors
        - Focus on educational content and basic concepts
        - Use examples from Indian context
        - Explain complex terms in simple language
        - Include relevant disclaimers
        
        Always structure your response with:
        1. A brief introduction/summary
        2. Detailed explanation with examples from Indian context
        3. Educational points and concepts
        4. Things to consider
        5. Next steps to learn more
        6. A clear disclaimer
        
        Make it engaging and conversational while maintaining accuracy and professionalism.
        
        Remember to start each response with: 'As an AI-powered financial guide, here's what I can share about...'"""

        # Add conversation history for context
        history_context = ""
        if self.conversation_history:
            last_exchanges = self.conversation_history[-2:]
            history_context = "\n\nPrevious conversation:\n" + "\n".join(
                [f"Q: {q}\nA: {a}" for q, a in last_exchanges]
            )

        retries = 0
        while retries < self.max_retries:
            try:
                full_prompt = f"{context}{history_context}\n\nUser Question: {user_query}"
                response = self.model.generate_content(full_prompt)
                
                if not response or not response.text:
                    raise Exception("Empty response from AI model")
                
                formatted_response = self.format_response(response.text)
                
                # Add standard disclaimer if not present
                if "disclaimer" not in formatted_response.lower():
                    formatted_response += "\n\n⚠️ Disclaimer: This is general information for educational purposes only. Please consult with SEBI registered financial advisors for personalized investment advice."
                
                self.conversation_history.append((user_query, formatted_response))
                if len(self.conversation_history) > 5:
                    self.conversation_history.pop(0)
                
                # Add a random money quote at the end
                formatted_response += f"\n\n{self.get_random_quote()}"
                
                return formatted_response
                
            except Exception as e:
                retries += 1
                if retries == self.max_retries:
                    return f"""❌ I apologize, but I'm having trouble processing your request right now. 

As an AI financial guide, I can try to help you with:
1. Basic financial concepts
2. Educational information about investments
3. General market information
4. Calculator tools and portfolio tracking

Please try rephrasing your question or use one of our special commands like:
- Get stock price for [SYMBOL]
- Calculate SIP
- Show portfolio
- Market mood

Error details: {str(e)}"""
                time.sleep(self.retry_delay)

def main():
    advisor = FinancialAdvisor()
    
    print("🤖 Welcome to FinWise (फाइनवाइज़) - Your Smart Indian Financial Advisor!")
    print("\n💫 Special Features:")
    print("1. 📈 Real-time stock prices (e.g., 'Get stock price for RELIANCE')")
    print("2. 💰 SIP Calculator (e.g., 'Calculate SIP for 5000 monthly for 10 years at 12% return')")
    print("3. 💳 EMI Calculator (e.g., 'Calculate EMI for 1000000 loan at 8.5% for 20 years')")
    print("4. 📊 Market Mood (e.g., 'How is the market today?')")
    print("5. 📱 Mutual Fund Analysis")
    print("\n📊 Portfolio Management:")
    print("- 'create portfolio' - Create a new portfolio")
    print("- 'add stock SYMBOL QUANTITY PRICE' - Add a stock to your portfolio")
    print("- 'show portfolio' - View your portfolio summary and analysis")
    
    print("\n🎯 Investment Topics I Can Help With:")
    print("- Stocks and Share Market")
    print("- Mutual Funds and SIPs")
    print("- Tax Saving Investments")
    print("- Retirement Planning")
    print("- Insurance Planning")
    print("- Risk Management")
    
    print("\n⚡ Commands:")
    print("- Type your question for financial advice")
    print("- Type 'save' to save the last advice")
    print("- Type 'history' to see conversation history")
    print("- Type 'quit' to exit")
    
    print(f"\n{advisor.get_random_quote()}")
    
    last_response = None
    
    while True:
        try:
            user_input = input("\n🤔 Your question: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n👋 Thank you for using FinWise! Remember:")
                print("पैसा important है, पर wisdom ज़रूरी है! (Money is important, but wisdom is essential!)")
                print("Have a prosperous day! 🙏")
                break
                
            elif user_input.lower() == 'save' and last_response:
                filename = advisor.save_advice(advisor.conversation_history[-1][0], last_response)
                print(f"✅ Advice saved to: {filename}")
                continue
                
            elif user_input.lower() == 'history':
                print("\n📚 Conversation History:")
                for i, (q, a) in enumerate(advisor.conversation_history, 1):
                    print(f"\n--- Exchange {i} ---")
                    print(f"Q: {q}")
                    print(f"A: {a}")
                continue
                
            elif not user_input:
                print("❌ Please enter a valid question!")
                continue
                
            response = advisor.get_financial_advice(user_input)
            print("\n🤖 FinWise:", response)
            last_response = response
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye! Remember: Investment in knowledge pays the best interest! 📚")
            break
        except Exception as e:
            print(f"❌ Oops! Even financial advisors have their moments: {str(e)}")

if __name__ == "__main__":
    main() 