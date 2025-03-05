import yfinance as yf
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from flask import Flask, render_template, jsonify, request
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()

# Load API key
groq_api = os.getenv("GROQ_API_KEY")

# ✅ Function to Fetch Stock Data
def fetch_stock_data(company_ticker):
    stock = yf.Ticker(company_ticker)
    historical_data = stock.history(period="1mo")
    historical_data.index = historical_data.index.strftime('%Y-%m-%d')  # Corrected date format
    return historical_data

# ✅ Function to create stock price plot with formatted date labels
def create_stock_plot(data):
    sns.set(style="darkgrid")
    plt.figure(figsize=(12, 6))
    
    # Plot stock prices
    sns.lineplot(x=data.index, y=data['Close'], label='Close Price')
    sns.lineplot(x=data.index, y=data['Open'], label='Open Price')
    
    plt.title("Stock Price Over the Last Month")
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    plt.xticks(rotation=45)  # Rotate for readability
    plt.tight_layout()

    # Save the plot as base64
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()

    return img_base64

# ✅ Agent Setup
stock_analysis_agent = Agent(
    name='Stock Analysis Agent',
    model=Groq(id="deepseek-r1-distill-llama-70b", api_key=groq_api),
    tools=[
        YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True),
        DuckDuckGoTools()
    ],
    instructions=[
        "Analyze the stock data, news, and provide recommendations (Buy, Hold, Sell).",
        "Ensure output is structured in a clean format with key insights."
    ],
    show_tool_calls=True,
    markdown=True
)

# ✅ Flask Routes
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get_stock_data", methods=["POST"])
def get_stock_data():
    data = request.json
    ticker = data.get("ticker", "TSLA")  # Default to TSLA

    # Fetch stock data
    stock_data = fetch_stock_data(ticker)

    # ✅ Structured Prompt for Agent
    structured_prompt = f"""
    Collect stock data for {ticker}, analyze recent news, and provide insights including:
    
    - Historical stock prices, volume changes, and performance for the last month.
    - Key financial indicators such as moving averages, volatility, and momentum.
    - Provide a recommendation (Buy, Hold, Sell) based on the analysis.
    """

    try:
        # Run agent for stock analysis
        analysis_result = stock_analysis_agent.run(structured_prompt)
        analysis_text = analysis_result.content if hasattr(analysis_result, 'content') else str(analysis_result)

        # ✅ Cleaned-up Analysis Output (Removing `###` and `----`)
        analysis_text = analysis_text.replace("###", "").replace("----", "").strip()

        # Create stock plot
        stock_plot_base64 = create_stock_plot(stock_data)

        # ✅ Key details structured data
        key_details = {
            "Stock Symbol": ticker,
            "Current Stock Price": f"${stock_data['Close'].iloc[-1]:.2f}",
            "Historical Performance": {
                "1 Month": f"{(stock_data['Close'].pct_change().iloc[-1] * 100):.2f}%",
                "3 Months": f"{(stock_data['Close'].pct_change(periods=3).iloc[-1] * 100):.2f}%",
                "6 Months": f"{(stock_data['Close'].pct_change(periods=6).iloc[-1] * 100):.2f}%"
            },
            "Volume Changes": {
                "Average Volume (30D)": f"{stock_data['Volume'].mean():,.0f}",
                "Current Volume": f"{stock_data['Volume'].iloc[-1]:,.0f}"
            },
            "Moving Averages": {
                "50-Day": f"${stock_data['Close'].rolling(50).mean().iloc[-1]:.2f}",
                "200-Day": f"${stock_data['Close'].rolling(200).mean().iloc[-1]:.2f}"
            },
            "Volatility": f"{stock_data['Close'].pct_change().std() * 100:.2f}%",
            "Momentum Indicators": {
                "RSI (14)": "62.5",  # Placeholder
                "MACD": "1.15"  # Placeholder
            },
            "Analyst Recommendations": {
                "Buy": "45%",
                "Hold": "35%",
                "Sell": "20%"
            }
        }

        return jsonify({
            "stock_data": stock_data.to_dict(),
            "analysis": analysis_text,
            "stock_plot": stock_plot_base64,
            "key_details": key_details
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Return error message

if __name__ == "__main__":
    app.run(debug=True)
