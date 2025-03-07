from fastapi import FastAPI
from pydantic import BaseModel
from llm import create_graph  # Import create_graph instead of graph
from langchain_core.messages import HumanMessage, ToolMessage
import uuid

app = FastAPI()

# Define the request body model using Pydantic
class PromptReq(BaseModel):
    prompt: str

# Store graph instances - create a new instance for each thread
graph_instances = {}

@app.get("/")
async def get():
    return {"message": "Hello, World!"}

@app.post("/reset")
async def reset_state():
    """Reset the graph state completely"""
    global graph_instances
    graph_instances = {}  # Clear all graph instances
    return {"status": "All graph states reset successfully"}

@app.post("/")
async def chat(request: PromptReq):
    # Create a unique thread ID for each request
    thread_id = f"thread-{uuid.uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}
    
    # Create a fresh graph for this request
    graph = create_graph()
    graph_instances[thread_id] = graph
    
    # Reset chart data and message ID for new request
    messages = {"messages": [HumanMessage(request.prompt)]}
    
    # Get response from graph
    output = graph.invoke(messages, config)
    
    # Find the ToolMessage in the messages list
    tool_message = None
    tool_type = None
    message_id = None
    
    for msg in output["messages"]:
        if isinstance(msg, ToolMessage):
            if msg.name == "getStockRecommendation":
                tool_message = msg.content
                tool_type = "chart"
                message_id = f"assistant-{uuid.uuid4()}"  # Generate unique ID
                
                # We don't need to update the graph state since it's ephemeral now
            elif msg.name == "getCompanyNews":
                tool_message = None
                tool_type = "news"
            else:
                tool_message = msg.content
                tool_type = "data"
            break

    # Return response with tool data, type and message ID
    return {
        "message": output["messages"][-1].content,
        "tool_data": tool_message,
        "tool_type": tool_type,
        "message_id": message_id  # Include message ID in response
    }