from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import asyncio
import requests
from datetime import datetime
import os

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

# Open-source AI integration
class OpenSourceAI:
    def __init__(self):
        self.use_local_model = False
        self.api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        self.headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY', '')}"}
        
    async def get_ai_response(self, message: str, language: str = "english") -> str:
        """Get response from open-source AI model"""
        try:
            # Try Hugging Face API first (free tier)
            if os.getenv('HUGGINGFACE_API_KEY'):
                response = await self._call_huggingface(message, language)
                if response:
                    return response
            
            # Fallback to Ollama local model if available
            try:
                response = await self._call_ollama(message, language)
                if response:
                    return response
            except:
                pass
            
            # Final fallback to enhanced rule-based system
            return get_multilingual_response(message, language)
            
        except Exception as e:
            print(f"AI Error: {e}")
            return get_multilingual_response(message, language)
    
    async def _call_huggingface(self, message: str, language: str) -> str:
        """Call Hugging Face API for AI response"""
        try:
            # Prepare prompt based on language
            language_prompts = {
                "spanish": "Responde en español. ",
                "french": "Réponds en français. ",
                "german": "Antworte auf Deutsch. ",
                "portuguese": "Responde em português. ",
                "italian": "Rispondi in italiano. ",
                "english": "Respond in English. "
            }
            
            prompt = language_prompts.get(language, "Respond in English. ") + message
            
            payload = {"inputs": prompt}
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result and len(result) > 0 and 'generated_text' in result[0]:
                    generated_text = result[0]['generated_text']
                    # Extract only the new response part
                    if prompt in generated_text:
                        response_text = generated_text.replace(prompt, "").strip()
                    else:
                        response_text = generated_text.strip()
                    
                    if response_text and len(response_text) > 10:
                        return response_text
            
            return None
            
        except Exception as e:
            print(f"Hugging Face API Error: {e}")
            return None
    
    async def _call_ollama(self, message: str, language: str) -> str:
        """Call local Ollama model"""
        try:
            # Language-specific system prompts
            system_prompts = {
                "spanish": "Eres un asistente IA útil que responde en español. Sé conciso pero completo.",
                "french": "Tu es un assistant IA utile qui répond en français. Sois concis mais complet.",
                "german": "Du bist ein nützlicher KI-Assistent, der auf Deutsch antwortet. Sei prägnant aber vollständig.",
                "portuguese": "Você é um assistente de IA útil que responde em português. Seja conciso mas completo.",
                "italian": "Sei un assistente IA utile che risponde in italiano. Sii conciso ma completo.",
                "english": "You are a helpful AI assistant that responds in English. Be concise but complete."
            }
            
            system_prompt = system_prompts.get(language, system_prompts["english"])
            
            payload = {
                "model": "llama2",  # or "mistral", "codellama", etc.
                "prompt": f"{system_prompt}\n\nUser: {message}\nAssistant:",
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "max_tokens": 150
                }
            }
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'response' in result:
                    return result['response'].strip()
            
            return None
            
        except Exception as e:
            print(f"Ollama Error: {e}")
            return None

# Initialize AI
ai_model = OpenSourceAI()

# Language detection and multilingual support
def detect_language(message: str) -> str:
    """Simple language detection based on common words and characters"""
    message_lower = message.lower().strip()
    
    # Spanish keywords
    spanish_keywords = ['hola', 'gracias', 'por favor', 'adiós', 'buenos días', 'buenas tardes', 'ayuda', 'cómo', 'qué', 'dónde', 'cuándo', 'por qué', 'puedes', 'necesito', 'quiero', 'tengo', 'español', 'españa', 'méxico', 'argentina']
    
    # French keywords
    french_keywords = ['bonjour', 'merci', 's\'il vous plaît', 'au revoir', 'aide', 'comment', 'quoi', 'où', 'quand', 'pourquoi', 'pouvez', 'besoin', 'veux', 'ai', 'français', 'france', 'paris']
    
    # German keywords
    german_keywords = ['hallo', 'danke', 'bitte', 'auf wiedersehen', 'hilfe', 'wie', 'was', 'wo', 'wann', 'warum', 'können', 'brauche', 'will', 'habe', 'deutsch', 'deutschland', 'berlin']
    
    # Portuguese keywords
    portuguese_keywords = ['olá', 'obrigado', 'por favor', 'tchau', 'ajuda', 'como', 'o que', 'onde', 'quando', 'por que', 'pode', 'preciso', 'quero', 'tenho', 'português', 'brasil', 'portugal']
    
    # Italian keywords
    italian_keywords = ['ciao', 'grazie', 'per favore', 'arrivederci', 'aiuto', 'come', 'cosa', 'dove', 'quando', 'perché', 'può', 'bisogno', 'voglio', 'ho', 'italiano', 'italia', 'roma']
    
    # Check for language-specific characters and patterns
    if any(char in message for char in ['ñ', 'á', 'é', 'í', 'ó', 'ú', 'ü']):
        return 'spanish'
    elif any(char in message for char in ['ç', 'à', 'â', 'ê', 'î', 'ô', 'û', 'è', 'é', 'ë', 'ï', 'ù']):
        return 'french'
    elif any(char in message for char in ['ä', 'ö', 'ü', 'ß']):
        return 'german'
    elif 'ã' in message or 'õ' in message or 'ç' in message:
        return 'portuguese'
    elif any(char in message for char in ['à', 'è', 'é', 'ì', 'ò', 'ù']):
        return 'italian'
    
    # Check for keywords
    if any(keyword in message_lower for keyword in spanish_keywords):
        return 'spanish'
    elif any(keyword in message_lower for keyword in french_keywords):
        return 'french'
    elif any(keyword in message_lower for keyword in german_keywords):
        return 'german'
    elif any(keyword in message_lower for keyword in portuguese_keywords):
        return 'portuguese'
    elif any(keyword in message_lower for keyword in italian_keywords):
        return 'italian'
    
    return 'english'

# Multilingual response templates
def get_multilingual_response(message: str, language: str) -> str:
    """Get response in the detected language"""
    
    if language == 'spanish':
        message_lower = message.lower().strip()
        
        # Spanish greetings
        if any(greeting in message_lower for greeting in ['hola', 'buenos días', 'buenas tardes', 'buenas noches']):
            greetings = [
                "¡Hola! ¿Cómo puedo ayudarte hoy?",
                "¡Hola! ¿En qué puedo asistirte?",
                "¡Saludos! Estoy aquí para ayudar. ¿Qué tienes en mente?",
                "¡Hola! No dudes en preguntarme lo que necesites."
            ]
            import random
            return random.choice(greetings)
        
        # Spanish help requests
        elif any(help_word in message_lower for help_word in ['ayuda', 'ayúdame', 'asistencia', 'qué puedes hacer']):
            return """Puedo ayudarte con diversas tareas incluyendo:
• Responder preguntas sobre diferentes temas
• Proporcionar explicaciones y definiciones
• Ayudar con la resolución de problemas
• Ofrecer sugerencias y recomendaciones
• Asistir con aprendizaje e investigación
• Proporcionar información y consejos generales

¿En qué área específica te gustaría recibir ayuda?"""
        
        # Spanish questions
        elif message_lower.endswith('?') or any(q_word in message_lower for q_word in ['qué', 'cómo', 'por qué', 'cuándo', 'dónde', 'quién', 'cuál']):
            return f"¡Esa es una excelente pregunta! Basado en tu consulta sobre '{message[:50]}...', estaré encantado de ayudarte. En un entorno de producción, proporcionaría una respuesta detallada y precisa. Por ahora, estoy demostrando el sistema de respuestas. ¿Podrías decirme más sobre qué información específica estás buscando?"
        
        # Spanish technology
        elif any(tech_word in message_lower for tech_word in ['código', 'programación', 'software', 'aplicación', 'página web', 'desarrollo']):
            return """¡Definitivamente puedo ayudar con temas de tecnología y programación! Puedo asistirte con:
• Explicaciones de código y depuración
• Diseño y optimización de algoritmos
• Mejores prácticas en desarrollo de software
• Recomendaciones de stack tecnológico
• Consejos de arquitectura de sistemas
• Conceptos y tutoriales de programación

¿Qué desafío específico de programación o tema estás trabajando?"""
        
        # Spanish thanks
        elif any(thank_word in message_lower for thank_word in ['gracias', 'agradecido', 'te agradezco']):
            thanks_responses = [
                "¡De nada! Me alegra haber podido ayudar. ¿Hay algo más en lo que pueda asistirte?",
                "¡Es un placer! No dudes en pedir más ayuda si la necesitas.",
                "¡Con gusto! Estoy aquí siempre que necesites asistencia.",
                "¡Feliz de ayudar! No dudes en preguntarme cualquier otra cosa."
            ]
            import random
            return random.choice(thanks_responses)
        
        # Spanish goodbye
        elif any(bye_word in message_lower for bye_word in ['adiós', 'chao', 'hasta luego', 'nos vemos']):
            bye_responses = [
                "¡Adiós! ¡Que tengas un excelente día, y no dudes en volver cuando quieras!",
                "¡Hasta luego! Fue un placer conversar contigo.",
                "¡Nos vemos! Estaré aquí siempre que necesites asistencia en el futuro.",
                "¡Cuídate! No dudes en regresar si necesitas ayuda."
            ]
            import random
            return random.choice(bye_responses)
        
        else:
            return f"Entiendo que estás preguntando sobre '{message[:30]}...'. ¡Este es un tema interesante! En un entorno de producción con integración de IA, te proporcionaría una respuesta detallada y precisa basada en conocimiento actual. Por ahora, estoy demostrando el flujo de conversación. ¿Qué aspecto específico de este tema te interesa más?"
    
    elif language == 'french':
        message_lower = message.lower().strip()
        
        # French greetings
        if any(greeting in message_lower for greeting in ['bonjour', 'salut', 'bonsoir']):
            greetings = [
                "Bonjour ! Comment puis-je vous aider aujourd'hui ?",
                "Salut ! En quoi puis-je vous aider ?",
                "Bonjour ! Je suis là pour aider. Qu'est-ce qui vous préoccupe ?",
                "Bonjour ! N'hésitez pas à me poser des questions."
            ]
            import random
            return random.choice(greetings)
        
        # French help requests
        elif any(help_word in message_lower for help_word in ['aide', "aide-moi", 'assistance', 'que peux-tu faire']):
            return """Je peux vous aider avec diverses tâches notamment :
• Répondre à des questions sur différents sujets
• Fournir des explications et des définitions
• Aider à la résolution de problèmes
• Offrir des suggestions et recommandations
• Assister avec l'apprentissage et la recherche
• Fournir des informations et conseils généraux

Dans quel domaine spécifique aimeriez-vous de l'aide ?"""
        
        # French thanks
        elif any(thank_word in message_lower for thank_word in ['merci', 'remercié', 'je vous remercie']):
            thanks_responses = [
                "De rien ! Je suis content d'avoir pu aider. Y a-t-il autre chose que je puisse faire pour vous ?",
                "Avec plaisir ! N'hésitez pas à demander plus d'aide si nécessaire.",
                "Je vous en prie ! Je suis là quand vous avez besoin d'assistance.",
                "Heureux d'aider ! N'hésitez pas à me poser d'autres questions."
            ]
            import random
            return random.choice(thanks_responses)
        
        else:
            return f"Je comprends que vous demandez à propos de '{message[:30]}...'. C'est un sujet intéressant ! Dans un environnement de production avec intégration IA, je vous fournirais une réponse détaillée et précise basée sur les connaissances actuelles. Pour l'instant, je démontre le flux de conversation. Quel aspect spécifique de ce sujet vous intéresse le plus ?"
    
    elif language == 'german':
        message_lower = message.lower().strip()
        
        # German greetings
        if any(greeting in message_lower for greeting in ['hallo', 'guten tag', 'guten morgen', 'guten abend']):
            greetings = [
                "Hallo! Wie kann ich Ihnen heute helfen?",
                "Hallo! Wobei kann ich Ihnen behilflich sein?",
                "Grüße! Ich bin hier, um zu helfen. Was beschäftigt Sie?",
                "Hallo! Fühlen Sie sich frei, mir alles zu fragen."
            ]
            import random
            return random.choice(greetings)
        
        # German help requests
        elif any(help_word in message_lower for help_word in ['hilfe', 'hilf mir', 'unterstützung', 'was kannst du tun']):
            return """Ich kann Ihnen mit verschiedenen Aufgaben helfen, einschließlich:
• Beantwortung von Fragen zu verschiedenen Themen
• Bereitstellung von Erklärungen und Definitionen
• Hilfe bei der Problemlösung
• Anbieten von Vorschlägen und Empfehlungen
• Unterstützung beim Lernen und Forschen
• Bereitstellung allgemeiner Informationen und Ratschläge

In welchem spezifischen Bereich möchten Sie Hilfe?"""
        
        # German thanks
        elif any(thank_word in message_lower for thank_word in ['danke', 'vielen dank', 'ich danke dir']):
            thanks_responses = [
                "Gern geschehen! Ich freue mich, dass ich helfen konnte. Gibt es noch etwas, wobei ich Ihnen behilflich sein kann?",
                "Mit Vergnügen! Zögern Sie nicht, um mehr Hilfe zu bitten, wenn Sie sie benötigen.",
                "Bitte! Ich bin immer da, wenn Sie Unterstützung benötigen.",
                "Freut mich zu helfen! Fühlen Sie sich frei, mir andere Fragen zu stellen."
            ]
            import random
            return random.choice(thanks_responses)
        
        else:
            return f"Ich verstehe, Sie fragen nach '{message[:30]}...'. Das ist ein interessantes Thema! In einer Produktionsumgebung mit KI-Integration würde ich Ihnen eine detaillierte, genaue Antwort basierend auf aktuellem Wissen geben. Derzeit demonstriere ich den Konversationsablauf. Welcher spezifische Aspekt dieses Themas interessiert Sie am meisten?"
    
    elif language == 'portuguese':
        message_lower = message.lower().strip()
        
        # Portuguese greetings
        if any(greeting in message_lower for greeting in ['olá', 'oi', 'bom dia', 'boa tarde', 'boa noite']):
            greetings = [
                "Olá! Como posso ajudá-lo hoje?",
                "Oi! Em que posso ajudar?",
                "Saudações! Estou aqui para ajudar. O que você tem em mente?",
                "Olá! Sinta-se à vontade para me perguntar qualquer coisa."
            ]
            import random
            return random.choice(greetings)
        
        # Portuguese help requests
        elif any(help_word in message_lower for help_word in ['ajuda', 'ajude-me', 'assistência', 'o que você pode fazer']):
            return """Posso ajudá-lo com várias tarefas incluindo:
• Responder perguntas sobre diferentes tópicos
• Fornecer explicações e definições
• Ajudar na resolução de problemas
• Oferecer sugestões e recomendações
• Assistir com aprendizado e pesquisa
• Fornecer informações e conselhos gerais

Em que área específica você gostaria de ajuda?"""
        
        # Portuguese thanks
        elif any(thank_word in message_lower for thank_word in ['obrigado', 'agradecido', 'eu agradeço']):
            thanks_responses = [
                "De nada! Fico feliz em ter podido ajudar. Há mais alguma coisa em que possa ajudar?",
                "Com prazer! Não hesite em pedir mais ajuda se precisar.",
                "Por nada! Estou aqui sempre que você precisar de assistência.",
                "Feliz em ajudar! Sinta-se à vontade para me perguntar qualquer outra coisa."
            ]
            import random
            return random.choice(thanks_responses)
        
        else:
            return f"Entendo que você está perguntando sobre '{message[:30]}...'. Este é um tópico interessante! Em um ambiente de produção com integração de IA, eu forneceria uma resposta detalhada e precisa baseada em conhecimento atual. Por enquanto, estou demonstrando o fluxo de conversação. Que aspecto específico deste tópico mais lhe interessa?"
    
    elif language == 'italian':
        message_lower = message.lower().strip()
        
        # Italian greetings
        if any(greeting in message_lower for greeting in ['ciao', 'buongiorno', 'buonasera']):
            greetings = [
                "Ciao! Come posso aiutarti oggi?",
                "Ciao! In cosa posso aiutarti?",
                "Saluti! Sono qui per aiutare. Cosa hai in mente?",
                "Ciao! Sentiti libero di chiedermi qualsiasi cosa."
            ]
            import random
            return random.choice(greetings)
        
        # Italian help requests
        elif any(help_word in message_lower for help_word in ['aiuto', 'aiutami', 'assistenza', 'cosa puoi fare']):
            return """Posso aiutarti con varie attività tra cui:
• Rispondere a domande su diversi argomenti
• Fornire spiegazioni e definizioni
• Aiutare nella risoluzione dei problemi
• Offrire suggerimenti e raccomandazioni
• Assistere con apprendimento e ricerca
• Fornire informazioni e consigli generali

In quale area specifica vorresti aiuto?"""
        
        # Italian thanks
        elif any(thank_word in message_lower for thank_word in ['grazie', 'ringraziato', 'ti ringrazio']):
            thanks_responses = [
                "Prego! Sono felice di aver potuto aiutare. C'è altro che posso fare per te?",
                "Con piacere! Non esitare a chiedere più aiuto se necessario.",
                "Prego! Sono qui ogni volta che hai bisogno di assistenza.",
                "Felice di aiutare! Sentiti libero di chiedermi qualsiasi altra cosa."
            ]
            import random
            return random.choice(thanks_responses)
        
        else:
            return f"Capisco che stai chiedendo di '{message[:30]}...'. Questo è un argomento interessante! In un ambiente di produzione con integrazione IA, ti fornirei una risposta dettagliata e accurata basata sulla conoscenza attuale. Per ora, sto dimostrando il flusso di conversazione. Quale aspetto specifico di questo argomento ti interessa di più?"
    
    # Default to English
    else:
        return get_english_response(message)

def get_english_response(message: str) -> str:
    """Original English response system"""
    message_lower = message.lower().strip()
    
    # Greeting patterns
    if any(greeting in message_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
        greetings = [
            "Hello! How can I assist you today?",
            "Hi there! What can I help you with?",
            "Greetings! I'm here to help. What's on your mind?",
            "Hello! Feel free to ask me anything."
        ]
        import random
        return random.choice(greetings)
    
    # Help and assistance patterns
    elif any(help_word in message_lower for help_word in ['help', 'assist', 'support', 'what can you do']):
        return """I can help you with various tasks including:
• Answering questions on different topics
• Providing explanations and definitions
• Helping with problem-solving
• Offering suggestions and recommendations
• Assisting with learning and research
• Providing general information and advice

What specific area would you like help with?"""
    
    # Question patterns
    elif message_lower.endswith('?') or any(q_word in message_lower for q_word in ['what', 'how', 'why', 'when', 'where', 'who', 'which']):
        return f"That's a great question! Based on your query about '{message[:50]}...', I'd be happy to help. In a production environment, I would provide a detailed, accurate answer. For now, I'm demonstrating the response system. Could you tell me more about what specific information you're looking for?"
    
    # Technology and programming patterns
    elif any(tech_word in message_lower for tech_word in ['code', 'programming', 'software', 'app', 'website', 'development']):
        return """I can definitely help with technology and programming topics! I can assist with:
• Code explanations and debugging
• Algorithm design and optimization
• Best practices in software development
• Technology stack recommendations
• System architecture advice
• Programming concepts and tutorials

What specific programming challenge or topic are you working on?"""
    
    # Business and professional patterns
    elif any(biz_word in message_lower for biz_word in ['business', 'company', 'work', 'career', 'professional', 'job']):
        return """I'm here to help with business and professional topics! I can provide guidance on:
• Business strategy and planning
• Career development and job searching
• Professional communication
• Project management
• Leadership and teamwork
• Industry trends and insights

What business or professional area would you like to explore?"""
    
    # Learning and education patterns
    elif any(learn_word in message_lower for learn_word in ['learn', 'study', 'education', 'course', 'tutorial', 'explain']):
        return """I love helping people learn! I can assist with:
• Explaining complex concepts in simple terms
• Study strategies and techniques
• Learning resources and recommendations
• Subject-specific guidance
• Skill development advice
• Educational planning

What subject or skill would you like to learn more about?"""
    
    # Personal advice patterns
    elif any(advice_word in message_lower for advice_word in ['advice', 'suggest', 'recommend', 'opinion', 'think']):
        return """I'd be happy to offer some thoughtful advice! While I can provide general guidance and suggestions, remember that personal situations are unique. I can help with:
• General life advice and tips
• Decision-making frameworks
• Problem-solving approaches
• Goal-setting strategies
• Productivity and time management
• Personal development ideas

What specific area would you like advice on?"""
    
    # Thank you patterns
    elif any(thank_word in message_lower for thank_word in ['thank', 'thanks', 'appreciate', 'grateful']):
        thanks_responses = [
            "You're very welcome! I'm glad I could help. Is there anything else I can assist you with?",
            "My pleasure! Don't hesitate to ask if you need more help.",
            "You're welcome! I'm here whenever you need assistance.",
            "Happy to help! Feel free to ask me anything else."
        ]
        import random
        return random.choice(thanks_responses)
    
    # Goodbye patterns
    elif any(bye_word in message_lower for bye_word in ['bye', 'goodbye', 'see you', 'farewell', 'exit']):
        bye_responses = [
            "Goodbye! Have a wonderful day, and feel free to come back anytime!",
            "See you later! It was great chatting with you.",
            "Farewell! I'm here whenever you need assistance in the future.",
            "Take care! Don't hesitate to return if you need help."
        ]
        import random
        return random.choice(bye_responses)
    
    # Default intelligent responses
    else:
        # Analyze message length and complexity for more contextual responses
        if len(message.split()) < 3:
            return "Could you tell me a bit more about that? I'd love to help but need a little more information to give you the best response."
        elif len(message.split()) > 20:
            return "That's quite detailed! Let me process what you've shared. In a full implementation, I would provide a comprehensive response addressing all the points you've mentioned. For now, could you help me understand what specific aspect is most important to you?"
        else:
            return f"I understand you're asking about '{message[:30]}...'. This is an interesting topic! In a production environment with AI integration, I would provide you with a detailed, accurate response based on current knowledge. For now, I'm demonstrating the conversation flow. What specific aspect of this topic interests you most?"

# AI Integration with open-source models
async def get_ai_response(message: str) -> str:
    try:
        # Detect language first
        detected_language = detect_language(message)
        
        # Get response from open-source AI model
        ai_response = await ai_model.get_ai_response(message, detected_language)
        
        return ai_response
        
    except Exception as e:
        return f"I apologize, but I encountered an issue while processing your request. Please try again or rephrase your question. Error: {str(e)}"

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
    uvicorn.run(app, host="0.0.0.0", port=8002)
