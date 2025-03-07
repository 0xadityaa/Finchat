import os 
from dotenv import load_dotenv 
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph, END
from typing import Annotated, Optional, Dict, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
import requests, finnhub, datetime, json
from langgraph.prebuilt import ToolNode, tools_condition
import pandas as pd

# Load environment variables from .env file 
load_dotenv() 

SYSTEM_PROMPT = """
You are Finance GPT, an AI-powered financial assistant designed to help users manage personal finances. 
Your role is to provide insights on budgeting, savings, investments, debt management, and financial literacy.

# Available Tools:
- getStockData: Get company profile and general information
- getStockRecommendation: Get analyst recommendations and trends
- getCompanyNews: Get recent news articles from last 7 days
- getStockPrice: Get real-time stock price and trading data
- getCompanyEarnings: Get quarterly earnings history and estimates

# Tone & Personality:
- Friendly, professional, and approachable
- Clear and concise, avoiding unnecessary jargon
- Encouraging but realistic, no guaranteed financial predictions

# Capabilities:
- Access real-time stock market data and analysis
- Explain budgeting techniques (e.g., 50/30/20 rule)
- Provide debt management strategies (e.g., snowball vs. avalanche)
- Guide users on savings plans and emergency funds
- Analyze market trends and company performance
- Educate users on personal finance concepts

# Limitations:
- NOT a licensed financial advisor—encourage seeking professional advice
- Avoid speculative predictions or tax/legal compliance guidance
- Do not store sensitive financial data beyond a session

# User Engagement Rules:
- Ask clarifying questions before giving financial guidance
- Adapt responses to user expertise level
- Provide actionable steps with examples
- Use available tools appropriately for market data requests
- Encourage healthy financial habits

# RESPONSE FORMATTING:
- Always return response in proper Markdown Syntax
- Use bullet points for lists and headings for sections
- Use Bold, Italics, and Hyperlinks for emphasis
- Include tool-generated data in formatted responses
- Only use recommendations tool if the user prompt SPECIFICALLY asks for it
"""

# Creating a Finnhub client to access stock data
finnhub_client = finnhub.Client(os.getenv("FINNHUB_API_KEY"))

# Creating a Company Profile Tool
@tool
def getStockData(symbol: str):
    """Get general company information and profile data from Finnhub API.

    Args:
        symbol (str): Stock symbol/ticker of the company (e.g. 'AAPL' for Apple Inc.)

    Returns:
        dict: Company profile data containing:
            - country: Company's country of registration
            - currency: Company's reporting currency
            - exchange: Listed exchange
            - ipo: IPO date
            - marketCapitalization: Market capitalization value
            - name: Company name
            - phone: Company phone number
            - shareOutstanding: Number of outstanding shares
            - ticker: Stock symbol
            - weburl: Company website URL
            - logo: URL to company logo
            - finnhubIndustry: Industry classification
        
    Returns None if API request fails.
    """
    try:
        response = finnhub_client.company_profile2(symbol=symbol)
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error fetching company profile data: {e}")
        return None

# Creating a Stock Recommendation Tool
@tool
def getStockRecommendation(symbol: str):
    """Get latest analyst recommendation trends for a company from Finnhub API.

    Args:
        symbol (str): Stock symbol/ticker of the company (e.g. 'AAPL' for Apple Inc.)

    Returns:
        list[dict]: List of monthly recommendation trends with each dict containing:
            - buy: Number of buy recommendations
            - hold: Number of hold recommendations
            - period: Time period of recommendations (YYYY-MM-DD)
            - sell: Number of sell recommendations
            - strongBuy: Number of strong buy recommendations
            - strongSell: Number of strong sell recommendations
            - symbol: Stock symbol

    Returns None if API request fails.
    """
    try:
        response = finnhub_client.recommendation_trends(symbol=symbol)
        print(response)
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error fetching company recommendation data: {e}")
        return None
    
# Creating a Stock Pice Tool
@tool
def getStockPrice(symbol: str):
    """Get real-time stock price data from Finnhub API.

    Args:
        symbol (str): Stock symbol/ticker of the company (e.g. 'AAPL' for Apple Inc.)

    Returns:
        dict: Real-time stock price data containing:
            - c: Current price
            - d: Change
            - dp: Percent change
            - h: High price of the day
            - l: Low price of the day
            - o: Open price of the day
            - pc: Previous close price
            - t: Timestamp

    Returns None if API request fails.
    """
    try:
        response = finnhub_client.quote(symbol=symbol)
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error fetching company quote data: {e}")
        return None

# Creating a Company Earnings History Tool
@tool
def getCompanyEarnings(symbol: str):
    """Get quarterly earnings history and analyst estimates for a company from Finnhub API.

    Args:
        symbol (str): Stock symbol/ticker of the company (e.g. 'AAPL' for Apple Inc.)

    Returns:
        list[dict]: List of quarterly earnings reports with each dict containing:
            - actual: Actual earnings per share (EPS)
            - estimate: Estimated EPS by analysts
            - period: Reporting period date (YYYY-MM-DD)
            - quarter: Fiscal quarter (1-4)
            - surprise: Difference between actual and estimated EPS
            - surprisePercent: Percentage difference from estimate
            - symbol: Stock symbol
            - year: Fiscal year
            
    Returns None if API request fails.
    """
    try:
        response = finnhub_client.company_earnings(symbol=symbol)
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error fetching company earnings data: {e}")
        return None

# Creating a Company News Tools
@tool
def getCompanyNews(symbol: str):
    """Get recent news articles and summaries for a company from Finnhub API.

    Args:
        symbol (str): Stock symbol/ticker of the company (e.g. 'AAPL' for Apple Inc.)

    Returns:
        str: JSON-formatted string containing:
            - summaries: Combined text of all news article summaries
            - error: Error message if no news data is available or an error occurred
            
        News data includes articles from the last 7 days with fields:
            - category: News category/type
            - datetime: Unix timestamp of publication
            - headline: Article headline
            - summary: Article summary text
            - url: Link to full article
            - source: News source name
            
    Returns JSON error object if API request fails or no news data available.
    """
    try:
        # Get current date and 7 days ago
        to_date = datetime.date.today()
        from_date = to_date - datetime.timedelta(days=7)

        # Fetch news data
        response = finnhub_client.company_news(symbol=symbol, _from=str(from_date), to=str(to_date))
        
        if not response:
            return json.dumps({"error": "No news data available"}, indent=4)

        # Extract summaries, handling missing keys
        summaries = []
        for item in response:
            if "summary" in item and item["summary"]:
                summaries.append(item["summary"])
        
        if not summaries:
            return json.dumps({"error": "No summaries found in response"}, indent=4)

        # Combine summaries
        combined_summaries = "\n".join(summaries)

        # Convert to JSON object
        result_json = json.dumps({"summaries": combined_summaries}, indent=4, ensure_ascii=False)

        return result_json

    except finnhub.FinnhubAPIException as e:
        print(f"API error: {e}")
        return json.dumps({"error": f"API error: {e}"}, indent=4)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return json.dumps({"error": f"Unexpected error: {e}"}, indent=4)


# Initialize Azure OpenAI LLM 
tools = [getStockData, getStockRecommendation, getCompanyNews, getStockPrice, getCompanyEarnings]
llm = AzureChatOpenAI( 
    deployment_name=os.getenv("OPENAI_API_DEPLOYMENT"),
    model=os.getenv("OPENAI_API_MODEL"),
    temperature=0.8,
    max_tokens=1000
).bind_tools(tools)

class CustomState(TypedDict):
    messages: Annotated[list, add_messages]
    chart_data: Optional[Dict[str, Any]] = None
    message_id: Optional[str] = None

# Define a new graph
workflow = StateGraph(CustomState)

# Action taken by the home node
def invoke_llm(state: CustomState):
    # Get existing messages and state
    messages = state.get("messages", [])
    chart_data = state.get("chart_data", None)
    message_id = state.get("message_id", None)
    
    # Create prompt with system message
    prompt_template = ChatPromptTemplate([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("messages")
    ])
    
    # Create prompt with messages
    prompt = prompt_template.invoke({"messages": messages})
    
    # Get response from LLM
    response = llm.invoke(prompt)
    
    # Return response with state
    return {
        "messages": response,
        "chart_data": chart_data,
        "message_id": message_id
    }

# Define a graph with a single node
workflow.add_edge(START, "home")
workflow.add_node("home", invoke_llm)
tool_node = ToolNode(tools)
workflow.add_node("tools", tool_node)
workflow.add_conditional_edges("home", tools_condition, ["tools", END])
workflow.add_edge("tools", "home")

# Function to create a fresh graph instance
def create_graph():
    """Create a fresh graph instance with a new memory saver"""
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)

# For backwards compatibility
graph = create_graph()