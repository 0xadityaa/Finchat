from fastapi import FastAPI
from pydantic import BaseModel
from llm import graph
from langchain_core.messages import HumanMessage

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
    return {"message": output["messages"][-1].content}