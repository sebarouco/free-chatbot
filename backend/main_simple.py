from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import asyncio
import openai
from datetime import datetime

app = FastAPI(title="AI Chatbot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    timestamp: str

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

# AI Integration (using OpenAI as example)
async def get_ai_response(message: str) -> str:
    try:
        # Note: You'll need to set your OpenAI API key
        # openai.api_key = "your-openai-api-key"
        
        # For demo purposes, return a simple response
        # In production, replace with actual OpenAI API call
        responses = [
            "I'm here to help you with your questions!",
            "That's an interesting question. Let me think about it.",
            "Based on what you're asking, I suggest...",
            "Thank you for your message. How can I assist you further?",
            "I understand your concern. Let me provide some information."
        ]
        
        import random
        return random.choice(responses)
        
        # Production code would be:
        # response = await openai.ChatCompletion.acreate(
        #     model="gpt-3.5-turbo",
        #     messages=[{"role": "user", "content": message}],
        #     max_tokens=150
        # )
        # return response.choices[0].message.content
        
    except Exception as e:
        return f"I apologize, but I'm having trouble processing your request right now. Error: {str(e)}"

# API Endpoints
@app.get("/")
async def root():
    return {"message": "AI Chatbot API is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    ai_response = await get_ai_response(message.message)
    
    return ChatResponse(
        response=ai_response,
        timestamp=datetime.now().isoformat()
    )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Get AI response
            ai_response = await get_ai_response(message_data["message"])
            
            # Send response back
            response = {
                "response": ai_response,
                "timestamp": datetime.now().isoformat()
            }
            await manager.send_personal_message(json.dumps(response), websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
