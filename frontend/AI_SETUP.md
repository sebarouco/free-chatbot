# Open-Source AI Setup Guide

This chatbot now supports multiple open-source AI models for better responses. Choose one of the options below:

## Option 1: Hugging Face API (Recommended - Free)

### Setup:
1. Create a free account at [Hugging Face](https://huggingface.co/)
2. Go to Settings → Access Tokens
3. Create a new token (read permissions are sufficient)
4. Set environment variable:
   ```bash
   # Windows
   set HUGGINGFACE_API_KEY=your_token_here
   
   # macOS/Linux
   export HUGGINGFACE_API_KEY=your_token_here
   ```

### Features:
- ✅ Free tier available
- ✅ Multiple models (DialoGPT, GPT-2, etc.)
- ✅ No local installation required
- ✅ Multilingual support

## Option 2: Ollama (Local Models)

### Setup:
1. Download and install [Ollama](https://ollama.ai/)
2. Install a model (choose one):
   ```bash
   ollama pull llama2          # General purpose
   ollama pull mistral         # Fast and efficient
   ollama pull codellama       # Code-focused
   ollama pull neural-chat     # Conversational
   ```
3. Start Ollama service:
   ```bash
   ollama serve
   ```

### Features:
- ✅ Completely free and local
- ✅ No internet required after setup
- ✅ Privacy-focused
- ✅ Multiple model options

## Option 3: Local Transformers (Advanced)

### Setup:
1. Install additional dependencies:
   ```bash
   pip install torch transformers accelerate
   ```
2. The system will automatically use local models if available

### Features:
- ✅ Maximum privacy
- ✅ Customizable models
- ✅ No API costs
- ⚠️ Requires powerful hardware

## Current Configuration

The chatbot is configured with this priority order:
1. **Hugging Face API** (if API key is set)
2. **Ollama** (if running locally)
3. **Rule-based responses** (fallback)

## Testing the AI

After setup, restart the backend server:

```bash
cd backend
python main.py
```

Test with these examples:
- "What is artificial intelligence?"
- "¿Cómo funciona el aprendizaje automático?"
- "Qu'est-ce que le machine learning?"
- "Was ist künstliche Intelligenz?"

## Model Information

### Currently Using:
- **Primary**: Microsoft DialoGPT-medium (Hugging Face)
- **Fallback**: Llama2 (Ollama)
- **Final**: Enhanced rule-based system

### Model Capabilities:
- 🌍 Multilingual conversations
- 🧠 Contextual understanding
- 💬 Natural dialogue flow
- 🔧 Technical assistance
- 📚 Educational support

## Troubleshooting

### Hugging Face Issues:
- Check your API key is correctly set
- Verify internet connection
- Some models may have rate limits

### Ollama Issues:
- Ensure Ollama is running: `ollama serve`
- Check model is installed: `ollama list`
- Verify port 11434 is available

### Performance Tips:
- Use smaller models for faster responses
- Consider GPU acceleration for local models
- Monitor API usage for Hugging Face

## Next Steps

1. Choose your preferred AI option
2. Complete the setup
3. Restart the servers
4. Test with various questions
5. Enjoy improved AI responses!
