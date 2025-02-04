from fastapi import FastAPI
from pydantic import BaseModel
from llm import graph
from langchain_core.messages import HumanMessage, ToolMessage

app = FastAPI()

# Define the request body model using Pydantic
class PromptReq(BaseModel):
    prompt: str

@app.get("/")
async def get():
    return {"message": "Hello, World!"}

@app.post("/")
async def chat(request: PromptReq):
    config = {"configurable": {"thread_id": "abc123"}}
    messages = {"messages": [HumanMessage(request.prompt)]}
    graph.update_state(config, {"language": "English"})

    output = graph.invoke(messages, config)
    
    # Find the ToolMessage in the messages list
    tool_message = None
    for msg in output["messages"]:
        if isinstance(msg, ToolMessage):
            # Check if this is a news API call by looking at the tool name
            if msg.name == "getCompanyNews":
                # Skip adding tool_data for news queries since it's already formatted in the LLM response
                tool_message = None
            else:
                tool_message = msg.content
            break

    # Return just the message for news queries, both message and tool data for others
    return {
        "message": output["messages"][-1].content,
        "tool_data": tool_message
    }