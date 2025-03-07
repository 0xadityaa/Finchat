# Finchat

## 📖 Overview
A RAG (Retrieval Augmented Generation) based chat application capable of providing realtime stock quotes, market insights, stock news, historical earnings as well as creating a meaningful visualization of that data on the fly.

https://github.com/user-attachments/assets/75e18bb6-9b46-45e6-83d7-ce55e469b51a

## 📚 Stack

  **Frontend:** [Streamlit](https://streamlit.io/), [Pandas](https://pandas.pydata.org/)
  
  **Backend:** [FastAPI](https://fastapi.tiangolo.com/), [Docker](https://www.docker.com/), [FinnHub](https://finnhub.io/)
  
  **AI/LLM:** [LangChain](https://www.langchain.com/), [LangGraph](https://langchain-ai.github.io/langgraph/), [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service)

## 🏛️ App Architecture
![Architecture Diagram](https://github.com/user-attachments/assets/c47f911b-3622-4c4a-97e6-678dc466a623)


Three core components work together:
1. **`client.py`** - Streamlit frontend with chat interface
2. **`server.py`** - FastAPI backend handling AI processing
3. **`llm.py`** - LangGraph workflow with financial data tools

## ✨ Features

- Real-time stock data analysis
- Company recommendation trends visualization
- Earnings history and news summaries
- Conversational AI with financial expertise
- Dockerized application for easy deployment

## 🛠️ Local Setup

### Prerequisites
- Docker and Docker Compose
- API keys for [Finnhub](https://finnhub.io) and [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service)

### Installation
1. Clone the repository
2. Create a `.env` file in the root directory with the following content:

```ini
OPENAI_API_DEPLOYMENT=your-deployment-name
OPENAI_API_MODEL=your-model-name
AZURE_OPENAI_ENDPOINT=your-azure-endpoint
OPENAI_API_VERSION=2023-05-15
OPENAI_API_KEY=your-openai-key
FINNHUB_API_KEY=your-finnhub-key
```

3. Build and run the Docker containers:

```bash
docker-compose up --build
```

## 🚀 Usage

After running the Docker containers:

1. Access the Streamlit frontend at `http://localhost:8502`
2. The FastAPI backend will be available at `http://localhost:8000`

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

## 🐳 Docker Configuration

The application is containerized using Docker for easy deployment and consistency across environments.

1. **Dockerfile**: Defines the environment for both the server and client.
2. **docker-compose.yml**: Orchestrates the multi-container setup:
   - `server`: Runs the FastAPI backend
   - `client`: Runs the Streamlit frontend

To modify ports or environment variables, adjust the `docker-compose.yml` file.

## 📄 License
MIT License - Use responsibly with proper API key management. Always verify financial insights with professional advisors.
