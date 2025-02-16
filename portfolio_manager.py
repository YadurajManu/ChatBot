import pandas as pd
import yfinance as yf
from pathlib import Path
import json
from datetime import datetime
import plotly.graph_objects as go

class PortfolioManager:
    def __init__(self):
        self.portfolio_dir = Path("portfolios")
        self.portfolio_dir.mkdir(exist_ok=True)
        
    def create_portfolio(self, user_id, portfolio_name="default"):
        """Create a new portfolio for a user"""
        portfolio_file = self.portfolio_dir / f"{user_id}_{portfolio_name}.json"
        if not portfolio_file.exists():
            portfolio = {
                "stocks": {},
                "mutual_funds": {},
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
            with open(portfolio_file, 'w') as f:
                json.dump(portfolio, f, indent=4)
            return "Portfolio created successfully!"
        return "Portfolio already exists!"
    
    def add_stock(self, user_id, symbol, quantity, buy_price, portfolio_name="default"):
        """Add a stock to the portfolio"""
        portfolio_file = self.portfolio_dir / f"{user_id}_{portfolio_name}.json"
        if not portfolio_file.exists():
            return "Portfolio not found!"
            
        try:
            # Verify stock exists
            stock = yf.Ticker(f"{symbol}.NS")
            current_price = stock.info.get('currentPrice', 0)
            
            with open(portfolio_file, 'r') as f:
                portfolio = json.load(f)
            
            if symbol in portfolio["stocks"]:
                # Update existing holding
                old_quantity = portfolio["stocks"][symbol]["quantity"]
                old_value = old_quantity * portfolio["stocks"][symbol]["buy_price"]
                new_value = quantity * buy_price
                avg_price = (old_value + new_value) / (old_quantity + quantity)
                
                portfolio["stocks"][symbol] = {
                    "quantity": old_quantity + quantity,
                    "buy_price": avg_price,
                    "current_price": current_price,
                    "last_updated": datetime.now().isoformat()
                }
            else:
                # Add new holding
                portfolio["stocks"][symbol] = {
                    "quantity": quantity,
                    "buy_price": buy_price,
                    "current_price": current_price,
                    "last_updated": datetime.now().isoformat()
                }
            
            portfolio["last_updated"] = datetime.now().isoformat()
            
            with open(portfolio_file, 'w') as f:
                json.dump(portfolio, f, indent=4)
                
            return f"Added {quantity} shares of {symbol} at ₹{buy_price} per share"
            
        except Exception as e:
            return f"Error adding stock: {str(e)}"
    
    def get_portfolio_summary(self, user_id, portfolio_name="default"):
        """Get portfolio summary with current values"""
        portfolio_file = self.portfolio_dir / f"{user_id}_{portfolio_name}.json"
        if not portfolio_file.exists():
            return "Portfolio not found!"
            
        try:
            with open(portfolio_file, 'r') as f:
                portfolio = json.load(f)
            
            total_investment = 0
            current_value = 0
            summary = []
            
            for symbol, data in portfolio["stocks"].items():
                stock = yf.Ticker(f"{symbol}.NS")
                current_price = stock.info.get('currentPrice', data["current_price"])
                
                investment = data["quantity"] * data["buy_price"]
                current_stock_value = data["quantity"] * current_price
                profit_loss = current_stock_value - investment
                profit_loss_percent = (profit_loss / investment) * 100
                
                total_investment += investment
                current_value += current_stock_value
                
                summary.append({
                    "symbol": symbol,
                    "quantity": data["quantity"],
                    "buy_price": data["buy_price"],
                    "current_price": current_price,
                    "investment": investment,
                    "current_value": current_stock_value,
                    "profit_loss": profit_loss,
                    "profit_loss_percent": profit_loss_percent
                })
            
            total_profit_loss = current_value - total_investment
            total_profit_loss_percent = (total_profit_loss / total_investment) * 100
            
            return {
                "summary": summary,
                "total_investment": total_investment,
                "current_value": current_value,
                "total_profit_loss": total_profit_loss,
                "total_profit_loss_percent": total_profit_loss_percent
            }
            
        except Exception as e:
            return f"Error getting portfolio summary: {str(e)}"
    
    def generate_portfolio_chart(self, user_id, portfolio_name="default"):
        """Generate a pie chart of portfolio allocation"""
        summary = self.get_portfolio_summary(user_id, portfolio_name)
        if isinstance(summary, str):
            return summary
            
        labels = [item["symbol"] for item in summary["summary"]]
        values = [item["current_value"] for item in summary["summary"]]
        
        fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
        fig.update_layout(title="Portfolio Allocation")
        
        chart_path = self.portfolio_dir / f"{user_id}_{portfolio_name}_allocation.html"
        fig.write_html(str(chart_path))
        
        return str(chart_path)
    
    def get_portfolio_metrics(self, user_id, portfolio_name="default"):
        """Calculate portfolio metrics like Beta, Alpha, Sharpe Ratio"""
        # This is a placeholder for more advanced portfolio metrics
        summary = self.get_portfolio_summary(user_id, portfolio_name)
        if isinstance(summary, str):
            return summary
            
        return {
            "diversification_score": len(summary["summary"]),  # Simple score based on number of stocks
            "risk_level": "High" if len(summary["summary"]) < 5 else "Medium" if len(summary["summary"]) < 10 else "Low",
            "suggested_actions": [
                "Consider adding more stocks for better diversification" if len(summary["summary"]) < 5 else
                "Portfolio is well diversified"
            ]
        } 