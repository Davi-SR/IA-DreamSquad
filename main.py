from fastapi import FastAPI
from pydantic import BaseModel
from agent import run_agent  # vem do agent.py

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

app = FastAPI()

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(body: ChatRequest):
    user_message = body.message
    resposta_do_agente = await run_agent(user_message)
    return ChatResponse(response=resposta_do_agente)