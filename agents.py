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

def create_stock_plot(data):
    # Set up seaborn style
    sns.set(style="darkgrid")
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    sns.lineplot(x=data.index, y=data['Close'], label='Close Price')
    plt.title("Stock Price Over the Last Month")
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    
    # Format the x-axis to display every 10th day
    plt.xticks(rotation=45)
    ax = plt.gca()
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=10))  # Show every 10th day
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))  # Format the date
    
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
finance_agents = Agent(
    name='finance Agent',
    model=Groq(id="llama-3.3-70b-versatile", api_key=groq_api),
    tools=[
        YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True),  # Add YFinanceTools here
        DuckDuckGoTools()
    ],
    instructions=['Use tables to represent'],
    show_tool_calls=True,
    markdown=True
)

# ✅ Merged Agent for Stock Data Analysis and Recommendation
analysis_and_recommendation_agent = Agent(
    model=Groq(id="llama-3.3-70b-versatile", api_key=groq_api),
    markdown=True,
    instructions=["Analyze the given stock data.",
                   "Identify trends, volatility, and key indicators such as moving averages.",
                   "Based on the analysis, provide a recommendation (Buy, Hold, Sell).",
                   "Ensure the output is structured in a table format with all key details."]
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

    # ✅ Structured Prompt
    structured_prompt = f"""
    Collect real-time stock data and market insights for {ticker}.

    1. Retrieve historical stock prices, volume changes, and performance over the last month.
    2. Search for recent news articles related to {ticker} that might impact its stock performance.
    3. Analyze key financial indicators such as moving averages, volatility, and momentum.
    4. Based on historical trends and recent news, provide a stock recommendation (Buy, Hold, or Sell).
    5. At last, display the disclaimer: "Please do your own research before making any financial decisions."
    """

    try:
        # Fetch real-time stock data and news using the new agent
        stock_data_with_news = finance_agents.run(structured_prompt)
        stock_news_content = stock_data_with_news.content if hasattr(stock_data_with_news, 'content') else str(stock_data_with_news)

        # Analyze stock data and get recommendation
        analysis_and_recommendation_result = analysis_and_recommendation_agent.run(stock_news_content)
        analysis_and_recommendation_text = analysis_and_recommendation_result.content if hasattr(analysis_and_recommendation_result, 'content') else str(analysis_and_recommendation_result)

        # Create stock plot
        stock_plot_base64 = create_stock_plot(stock_data)

        # ✅ Return formatted JSON response with the base64 image and tables
        return jsonify({
            "stock_data": stock_data.to_dict(),
            "news": stock_news_content.strip(),
            "analysis_and_recommendation": analysis_and_recommendation_text.strip(),
            "stock_plot": stock_plot_base64  # Return the base64 image here
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Return error message

if __name__ == "__main__":
    app.run(debug=True)
