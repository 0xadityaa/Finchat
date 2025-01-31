import os 
from dotenv import load_dotenv 
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph, END
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
import requests, finnhub, datetime, timedelta, json
from langgraph.prebuilt import ToolNode, tools_condition
import pandas as pd

# Load environment variables from .env file 
load_dotenv() 

# Define the system prompt for finance GPT
SYSTEM_PROMPT = """
You are Finance GPT, an AI-powered financial assistant designed to help users manage personal finances. 
Your role is to provide insights on budgeting, savings, investments, debt management, and financial literacy.

# Tone & Personality:
- Friendly, professional, and approachable.
- Clear and concise, avoiding unnecessary jargon.
- Encouraging but realistic—no guaranteed financial predictions.

# Capabilities:
- Explain budgeting techniques (e.g., 50/30/20 rule).
- Provide debt management strategies (e.g., snowball vs. avalanche method).
- Offer general investment insights without giving direct financial advice.
- Guide users on savings plans and emergency funds.
- Analyze and categorize transactions if user data is provided.
- Educate users on personal finance concepts and common pitfalls.

# Limitations:
- You are NOT a licensed financial advisor—always encourage users to seek professional advice.
- Avoid speculative predictions or tax/legal compliance guidance.
- Do not store or process sensitive financial data beyond a session.

# User Engagement Rules:
- Ask clarifying questions before giving financial guidance.
- Adapt responses to user expertise level (beginner, intermediate, advanced).
- Provide actionable steps with examples.
- Encourage healthy financial habits (e.g., building emergency funds, reducing bad debt).

# RESPONSE FORMATTING:
- Always return response in proper Markdown Syntax.
- Use bullet points for lists and headings for sections.
- Use Bold, Italics, and Hyperlinks for emphasis and references.
"""

# Creating a Finnhub client to access stock data
finnhub_client = finnhub.Client(os.getenv("FINNHUB_API_KEY"))

# Creating a Weather Tool
# @tool
# def getWeather(city: str):
#     """Call the weather API to get the weather of the city""""  
#     url = f"http://api.weatherapi.com/v1/current.json?key=6f1d93acbcc0475eb09163014252901&q={city}&aqi=no"
#     try:
#         response = requests.get(url)
#         response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
#         return response.json()
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching weather data: {e}")
#         return None

# Creating a Company Profile Tool
@tool
def getStockData(symbol: str):
    """Call the stock API to get the latest company profile data of the symbol for requested company and convert it to a stacked bar chart, returning pandas dataframe"""
    try:
        response = finnhub_client.company_profile2(symbol=symbol)
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error fetching company profile data: {e}")
        return None

# Creating a Stock Recommendation Tool
@tool
def getStockRecommendation(symbol: str):
    """Call the stock API to get the stock recommendation of the symbol for requested company"""
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
    """Call the stock API to get the stock price of the symbol for requested company"""
    try:
        response = finnhub_client.quote(symbol=symbol)
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error fetching company quote data: {e}")
        return None

# Creating a Company Earnings History Tool
@tool
def getCompanyEarnings(symbol: str):
    """Call the stock API to get the earnings history of the symbol for requested company"""
    try:
        response = finnhub_client.company_earnings(symbol=symbol)
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error fetching company earnings data: {e}")
        return None

# Creating a Company News Tools
@tool
def getCompanyNews(symbol: str):
    """Fetch company news from the API and summarize it."""
    
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
    max_tokens=400
).bind_tools(tools)

class CustomState(TypedDict):
    messages: Annotated[list, add_messages]
    language: str

# Define a new graph
workflow = StateGraph(CustomState)

# Action taken by the home node
def invoke_llm(state: CustomState):
    prompt_template = ChatPromptTemplate([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("messages")
    ])
    prompt = prompt_template.invoke(state)
    response = llm.invoke(prompt)
    return {"messages": response}
    # response = llm.invoke(state["messages"])
    # return {"messages": response}

# Define a graph with a single node
workflow.add_edge(START, "home")
workflow.add_node("home", invoke_llm)
tool_node = ToolNode(tools)
workflow.add_node("tools", tool_node)
workflow.add_conditional_edges("home", tools_condition, ["tools", END])
workflow.add_edge("tools", "home")

# Compile the workflow, specifying a checkpointer
# that persists checkpoints to memory
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)