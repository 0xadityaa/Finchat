# Finchat - RAG app for real-time stock analysis and visualization

## 📖 Overview
A RAG (Retrieval Augmented Generation) based chat application capable of providing realtime stock quotes, market insights, stock news, historical earnings as well as creating a meaningful visualization of that data on the fly.


<img width="1280" alt="Screenshot 2025-01-31 at 12 20 10 PM" src="https://github.com/user-attachments/assets/5f7f96cc-b962-4e69-b5ff-ba025b54582c" />
<img width="1280" alt="image" src="https://github.com/user-attachments/assets/7e8a7c89-8b3f-41d4-8c2a-6fa0d48572b3" />


#### Stack

  [Streamlit](https://streamlit.io/)
| [Langchain](https://www.langchain.com/)
| [LangGraph](https://langchain-ai.github.io/langgraph/)
| [FastAPI](https://fastapi.tiangolo.com/)
| [FinnHub](https://finnhub.io/)


#### App Architecture
![image](https://github.com/user-attachments/assets/c3df2abd-2885-4aab-8de3-6f0130829604)


Three core components work together:
1. **`client.py`** - Streamlit frontend with chat interface
2. **`server.py`** - FastAPI backend handling AI processing
3. **`llm.py`** - LangGraph workflow with financial data tools

## ✨ Features

- Real-time stock data analysis
- Company recommendation trends visualization
- Earnings history and news summaries
- Conversational AI with financial expertise

## 🛠️ Local Setup

### Prerequisites
- Python 3.12
- Conda package manager
- API keys for [Finnhub](https://finnhub.io) and [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service)

### Installation
```bash
# Create conda environment
conda create -y -p ./conda python=3.12
conda activate ./.conda

# Install dependencies
pip install -r requirements.txt

# Create .env file
touch .env
```

### Environment Variables (`.env`)
```ini
OPENAI_API_DEPLOYMENT=your-deployment-name
OPENAI_API_MODEL=your-model-name
AZURE_OPENAI_ENDPOINT=your-azure-endpoint
OPENAI_API_VERSION=2023-05-15
OPENAI_API_KEY=your-openai-key
FINNHUB_API_KEY=your-finnhub-key
```

## 🚀 Usage

1. **Start Server** (in separate terminal)
```bash
uvicorn server:app --reload
```

2. **Start Client** 
```bash
streamlit run client.py
```

3. **Sample Queries**:
```text
Q. "Show me recommendation trends for apple"
Q. "What's the current price of tesla?"
Q. "Summarize recent news for microsoft"
Q. "Display earnings history for google"
```

## 🧩 Component Interaction

1. **Client (Streamlit Frontend)**
- Handles user interface and chat history
- Sends prompts to server via POST requests
- Visualizes responses using Streamlit charts
- Maintains session-based chat history

2. **Server (FastAPI Backend)**
- Receives POST requests with user prompts
- Maintains conversation state using LangGraph
- Coordinates with financial data tools
- Returns AI-generated responses in JSON format

3. **LLM Workflow (LangGraph)**
- Processes natural language queries using Azure OpenAI
- Routes to appropriate financial tools:
  - `getStockData`: Company profiles
  - `getStockRecommendation`: Analyst trends
  - `getCompanyNews`: Recent news summaries
  - `getStockPrice`: Real-time quotes
  - `getCompanyEarnings`: Historical performance

## 📄 License

MIT License - Use responsibly with proper API key management. Always verify financial insights with professional advisors.
