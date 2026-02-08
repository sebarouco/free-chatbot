import asyncio
from datetime import datetime
import os
import json
import random
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import warnings
warnings.filterwarnings("ignore")
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiohttp
import re

app = FastAPI(title="Free Chatbot with Web Search", version="9.0.0", description="Advanced Chatbot with DistilGPT2 and Real-time Web Search")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:9000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    intent: str
    confidence: float
    language: str
    model_used: str

class DistilGPT2Assistant:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Initialize DistilGPT2
        print("Loading DistilGPT2 model...")
        try:
            self.gpt2_model = GPT2LMHeadModel.from_pretrained('distilgpt2')
            self.gpt2_tokenizer = GPT2Tokenizer.from_pretrained('distilgpt2')
            self.gpt2_model.to(self.device)
            print("DistilGPT2 loaded successfully!")
        except Exception as e:
            print(f"Error loading DistilGPT2: {e}")
            self.gpt2_model = None
            self.gpt2_tokenizer = None
        
        self.conversation_history = []
        
        # Language patterns for detection
        self.language_patterns = {
            'spanish': ['hola', 'adiós', 'gracias', 'por favor', '¿cómo', 'qué', 'dónde', 'cuándo'],
            'french': ['bonjour', 'au revoir', 'merci', 's\'il vous plaît', 'comment', 'où', 'quand'],
            'german': ['hallo', 'auf wiedersehen', 'danke', 'bitte', 'wie', 'wo', 'wann'],
            'portuguese': ['olá', 'tchau', 'obrigado', 'por favor', 'como', 'onde', 'quando'],
            'italian': ['ciao', 'arrivederci', 'grazie', 'per favore', 'come', 'dove', 'quando']
        }
        
        # Wikipedia language codes
        self.wikipedia_languages = {
            'spanish': 'es',
            'french': 'fr', 
            'german': 'de',
            'portuguese': 'pt',
            'italian': 'it',
            'english': 'en'
        }
    
    def detect_language(self, message: str) -> str:
        message_lower = message.lower()
        for lang, patterns in self.language_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                return lang
        return 'english'
    
    def classify_intent_fallback(self, message: str) -> tuple:
        message_lower = message.lower().strip()
        
        greeting_patterns = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'hola', 'bonjour', 'hallo', 'olá', 'ciao']
        if any(pattern in message_lower for pattern in greeting_patterns):
            return 'greeting', 0.9
        
        goodbye_patterns = ['goodbye', 'bye', 'see you', 'farewell', 'adiós', 'au revoir', 'auf wiedersehen', 'tchau', 'arrivederci']
        if any(pattern in message_lower for pattern in goodbye_patterns):
            return 'goodbye', 0.9
        
        thanks_patterns = ['thank', 'thanks', 'gracias', 'merci', 'danke', 'obrigado', 'grazie']
        if any(pattern in message_lower for pattern in thanks_patterns):
            return 'thanks', 0.9
        
        if any(word in message_lower for word in ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'can', 'could', 'would', 'should']):
            return 'question', 0.8
        
        return 'statement', 0.6
    
    def clean_query_for_wikipedia(self, query: str, language: str) -> str:
        # Remove common question words and clean for Wikipedia
        question_words = ['what', 'who', 'where', 'when', 'why', 'how', 'qué', 'quién', 'dónde', 'cuándo', 'por qué', 'comment', 'où', 'qui', 'wie', 'was', 'wer']
        
        cleaned_query = query.lower()
        for word in question_words:
            cleaned_query = cleaned_query.replace(word, '').strip()
        
        # Remove special characters and limit length
        cleaned_query = re.sub(r'[^\w\s]', '', cleaned_query)
        cleaned_query = cleaned_query.strip()[:50]
        
        return cleaned_query
    
    async def search_wikipedia(self, query: str, language: str = 'en') -> str:
        try:
            lang_code = self.wikipedia_languages.get(language, 'en')
            cleaned_query = self.clean_query_for_wikipedia(query, language)
            
            url = f"https://{lang_code}.wikipedia.org/api/rest_v1/page/summary/{cleaned_query}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'extract' in data and data['extract']:
                            return data['extract'][:500]
                        elif 'description' in data:
                            return data['description'][:300]
                    return None
        except Exception as e:
            print(f"Wikipedia search error: {e}")
            return None
    
    async def search_duckduckgo(self, query: str) -> str:
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'AbstractText' in data:
                            return data['AbstractText'][:500]
                    return None
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return None
    
    async def search_web(self, query: str, language: str = 'en') -> str:
        # Try Wikipedia first
        wiki_result = await self.search_wikipedia(query, language)
        if wiki_result:
            return wiki_result
        
        # Fall back to DuckDuckGo
        ddg_result = await self.search_duckduckgo(query)
        if ddg_result:
            return ddg_result
        
        return f"I couldn't find information about '{query}' on the web."
    
    def format_web_response(self, response: str, language: str = 'en') -> str:
        if not response:
            return "I couldn't find relevant information on the web."
        
        greetings = {
            'spanish': 'Según mi búsqueda en la web',
            'french': 'Selon ma recherche sur le web',
            'german': 'Laut meiner Websuche',
            'portuguese': 'Segundo minha busca na web',
            'italian': 'Secondo la mia ricerca sul web'
        }
        
        intro = greetings.get(language, "According to my web search")
        return f"{intro}: {response}"
    
    def generate_response(self, message: str, language: str = 'en') -> str:
        if not self.gpt2_model or not self.gpt2_tokenizer:
            return "I'm having trouble with my AI model right now. Please try again later."
        
        try:
            # Add context about multilingual capabilities
            context_prompt = f"You are a multilingual AI assistant. Respond in {language} if the message is in {language}. Be helpful and conversational."
            
            inputs = self.gpt2_tokenizer.encode(message, return_tensors='pt')
            inputs = inputs.to(self.device)
            
            with torch.no_grad():
                outputs = self.gpt2_model.generate(
                    inputs,
                    max_length=150,
                    num_return_sequences=1,
                    temperature=0.7,
                    pad_token_id=self.gpt2_tokenizer.eos_token_id,
                    do_sample=True
                )
            
            response = self.gpt2_tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response[:500]
        
        except Exception as e:
            print(f"Generation error: {e}")
            return "I'm having trouble generating a response right now."
    
    async def get_response(self, message: str) -> tuple:
        language = self.detect_language(message)
        intent, confidence = self.classify_intent_fallback(message)
        
        # Use web search for questions or low confidence
        if intent == 'question' or confidence < 0.7:
            web_response = await self.search_web(message, language)
            if web_response and not web_response.startswith("I couldn't find"):
                formatted_response = self.format_web_response(web_response, language)
                return formatted_response, intent, 0.9, language, "Web Search + Free AI"
        
        # Use DistilGPT2 for other cases
        ai_response = self.generate_response(message, language)
        return ai_response, intent, confidence, language, "Free AI"
    
    def add_to_history(self, message: str, response: str):
        self.conversation_history.append({
            'message': message,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 10 conversations
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

# Initialize assistant
distilgpt2_assistant = DistilGPT2Assistant()

async def get_ai_response(message: str) -> tuple:
    try:
        response, intent, confidence, language, model_used = await distilgpt2_assistant.get_response(message)
        distilgpt2_assistant.add_to_history(message, response)
        return response, intent, confidence, language, model_used
    except Exception as e:
        print(f"Error in get_ai_response: {e}")
        return "I'm having trouble processing your request right now. Please try again.", "error", 0.0, "english", "Fallback"

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Free Chatbot with Web Search is running", "version": "9.0.0", "features": ["DistilGPT2", "Web Search", "6 Languages"]}

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    response, intent, confidence, language, model_used = await get_ai_response(message.message)
    
    return ChatResponse(
        response=response,
        timestamp=datetime.now().isoformat(),
        intent=intent,
        confidence=confidence,
        language=language,
        model_used=model_used
    )

@app.get("/models")
async def get_models():
    return {
        "gpt2_loaded": distilgpt2_assistant.gpt2_model is not None,
        "web_search_enabled": True,
        "supported_languages": ["english", "spanish", "french", "german", "portuguese", "italian"]
    }

@app.get("/intents")
async def get_intents():
    """Get available capabilities"""
    return {
        "capabilities": ["greeting", "goodbye", "thanks", "question", "statement", "web_search"],
        "technology": "Free AI + Web Search",
        "features": ["Real-time Information", "Multilingual Web Search", "Wikipedia Integration", "DuckDuckGo Search"]
    }

@app.get("/conversation/history")
async def get_conversation_history():
    """Get conversation history"""
    return {"history": distilgpt2_assistant.conversation_history}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection established")
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                message = message_data.get("message", "")
                
                if message:
                    # Show typing indicator
                    await websocket.send_json({"typing": True})
                    
                    # Get response
                    response, intent, confidence, language, model_used = await get_ai_response(message)
                    
                    # Send response
                    await websocket.send_json({
                        "response": response,
                        "intent": intent,
                        "confidence": confidence,
                        "language": language,
                        "model_used": model_used
                    })
                    
                    # Add to history
                    distilgpt2_assistant.add_to_history(message, response)
                    
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON format"})
            except Exception as e:
                print(f"WebSocket error: {e}")
                await websocket.send_json({"error": str(e)})
                
    except WebSocketDisconnect:
        print("WebSocket connection closed")
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
