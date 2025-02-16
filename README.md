# FinWise: AI-Powered Financial Assistant 🤖💰

FinWise is a sophisticated financial assistant that combines artificial intelligence with real-time market data to provide comprehensive financial insights, portfolio management, and market analysis.

![FinWise Interface](screenshots/finwise.png)

## 🌟 Features

### 1. Real-Time Market Analysis
- **Live Stock Tracking**: Real-time stock prices from multiple sources
- **Technical Analysis**: Advanced indicators including SMA, RSI, MACD, Bollinger Bands
- **Market Sentiment**: AI-powered analysis of market trends and mood
- **News Integration**: Live financial news with sentiment analysis

### 2. Portfolio Management
- **Portfolio Tracking**: Create and manage investment portfolios
- **Performance Analytics**: Track returns, profits, and losses
- **Diversification Analysis**: Get insights on portfolio balance
- **Visual Reports**: Interactive charts and performance graphs

### 3. Financial Tools
- **SIP Calculator**: Calculate systematic investment returns
- **EMI Calculator**: Loan EMI calculations
- **Returns Calculator**: Investment return projections
- **Risk Assessment**: Portfolio risk analysis tools

### 4. AI-Powered Features
- **Smart Advisor**: Context-aware financial advice
- **Market Predictions**: AI-driven market trend analysis
- **News Sentiment**: Automated news sentiment analysis
- **Learning Resources**: Personalized educational content

### 5. Interactive UI Features
- **Multi-Mode Interface**: 
  - Advisor Mode
  - Analysis Mode
  - Portfolio Mode
  - Learning Mode
- **Dark/Light Theme**
- **Voice Commands**
- **Quick Actions**
- **Responsive Design**

## 🛠️ Technology Stack

- **Backend**:
  - Python 3.8+
  - Flask
  - Google Gemini AI
  - yfinance
  - pandas
  - numpy
  - plotly

- **Frontend**:
  - HTML5/CSS3
  - JavaScript/jQuery
  - Bootstrap 5
  - Font Awesome
  - Plotly.js

- **AI/ML**:
  - Google Generative AI
  - TextBlob
  - NLTK
  - Transformers
  - Torch

- **Data Sources**:
  - Yahoo Finance
  - NSE India
  - News API
  - MoneyControl

## 📦 Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/finwise.git
   cd finwise
   ```

2. **Set Up Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Setup**
   Create a `.env` file with the following:
   ```
   GOOGLE_API_KEY=your_google_api_key
   NEWSAPI_KEY=your_newsapi_key
   ```

5. **Run the Application**
   ```bash
   python app.py
   ```

## 🚀 Usage

### Market Analysis
```
price SYMBOL          # Get real-time stock price
analysis SYMBOL       # Get technical analysis
sentiment SYMBOL      # Get market sentiment
market mood          # Check overall market mood
```

### Portfolio Management
```
create portfolio              # Create new portfolio
add stock SYMBOL QTY PRICE   # Add stock to portfolio
show portfolio               # View portfolio summary
remove stock SYMBOL          # Remove stock from portfolio
```

### Financial Calculations
```
calculate sip AMOUNT YEARS RETURN    # Calculate SIP returns
calculate emi AMOUNT RATE YEARS      # Calculate loan EMI
calculate returns AMOUNT YEARS RATE  # Calculate investment returns
```

### Learning Resources
```
learn stocks         # Learn about stocks
learn mutual_funds   # Learn about mutual funds
learn technical      # Learn technical analysis
```

## 🎨 Themes and UI

- **Theme Switching**: Toggle between light and dark modes
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Interactive Charts**: Dynamic, interactive financial visualizations
- **Command Guide**: Built-in command reference
- **Context Menu**: Right-click actions for messages
- **Toast Notifications**: User-friendly notifications

## 🔒 Security Features

- API key protection
- Secure data storage
- Error handling
- Input validation
- Rate limiting
- Session management

## 📊 Data Sources

- Real-time stock data from Yahoo Finance
- NSE India market data
- News from NewsAPI and MoneyControl
- Technical indicators calculation
- Market sentiment analysis

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

Yaduraj Singh *Initial work* - [YourGithub](https://github.com/YadurajManu)

## 🙏 Acknowledgments

- Google Generative AI for powering the AI features
- Yahoo Finance for market data
- NewsAPI for financial news
- Open source community for various tools and libraries

## 📞 Support

For support, email yadurajsingham@gmail.com or open an issue in the repository.

---

Made with ❤️ by Yaduraj # ChatBot
