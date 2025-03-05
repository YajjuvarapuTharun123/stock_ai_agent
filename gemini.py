import yfinance as yf
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from flask import Flask, render_template, jsonify, request
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools  # Import YFinanceTools
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
    historical_data.index = historical_data.index.astype(str)  # Convert timestamps to string
    return historical_data

# Function to create stock price plot with vertical date labels
def create_stock_plot(data):
    # Set up seaborn style
    sns.set(style="darkgrid")
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    sns.lineplot(x=data.index, y=data['Close'], label='Close Price')
    sns.lineplot(x=data.index, y=data['Open'], label='Open Price')
    plt.title("Stock Price Over the Last Month")
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    
    # Rotate the x-axis labels for better readability
    plt.xticks(rotation=90)
    
    # Save the plot to a BytesIO object (in-memory file)
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    
    # Encode image as base64
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
    
    # Close the plot to avoid display in a non-interactive environment
    plt.close()
    
    return img_base64

# ✅ Agent Setup
stock_analysis_agent = Agent(
    name='Stock Analysis Agent',
    model=Groq(id="deepseek-r1-distill-llama-70b", api_key=groq_api),
    tools=[
        YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True),  # Add YFinanceTools here
        DuckDuckGoTools()
    ],
    instructions=["Analyze the stock data, news, and provide recommendations (Buy, Hold, Sell).",
                   "Ensure output is structured in tabular format with all key details."],
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
    ticker = data.get("ticker", "TSLA")  # Default to TSLA if no ticker is provided

    # Fetch stock data
    stock_data = fetch_stock_data(ticker)

    # ✅ Structured Prompt for Agent
    structured_prompt = f"""
    Collect stock data for {ticker}, analyze recent news, and provide insights including:
    - Historical stock prices, volume changes, and performance for the last month.
    - Analyze key financial indicators such as moving averages, volatility, and momentum.
    - Provide a recommendation (Buy, Hold, Sell) based on the analysis.
    """

    try:
        # Run agent for stock analysis
        analysis_result = stock_analysis_agent.run(structured_prompt)
        analysis_text = analysis_result.content if hasattr(analysis_result, 'content') else str(analysis_result)

        # Create stock plot
        stock_plot_base64 = create_stock_plot(stock_data)

        # Prepare structured data for table (key details)
        key_details = {
            "Stock Symbol": ticker,
            "Current Stock Price": f"${stock_data['Close'].iloc[-1]:.2f}",
            "Historical Performance": {
                "1 Month": f"+{(stock_data['Close'].pct_change().iloc[-1] * 100):.2f}%",
                "3 Months": f"+{(stock_data['Close'].pct_change(periods=3).iloc[-1] * 100):.2f}%",
                "6 Months": f"+{(stock_data['Close'].pct_change(periods=6).iloc[-1] * 100):.2f}%"
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
                "RSI (14)": "62.5",  # Placeholder for actual calculation
                "MACD": "1.15"  # Placeholder for actual calculation
            },
            "Analyst Recommendations": {
                "Buy": "45%",
                "Hold": "35%",
                "Sell": "20%"
            }
        }

        # ✅ Return structured response
        return jsonify({
            "stock_data": stock_data.to_dict(),
            "analysis": analysis_text.strip(),
            "stock_plot": stock_plot_base64,  # Return the base64 image here
            "key_details": key_details
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Return error message

if __name__ == "__main__":
    app.run(debug=True)
