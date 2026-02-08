# Hugging Face API Setup for @yalega8245

## Step 1: Get Your API Key

1. Go to: https://huggingface.co/settings/tokens
2. Click "New token"
3. Give it a name (e.g., "chatbot-api")
4. Select "read" permissions (sufficient for our use)
5. Click "Generate token"
6. Copy the token (it starts with "hf_...")

## Step 2: Set Environment Variable

### Windows (Command Prompt):
```cmd
set HUGGINGFACE_API_KEY=hf_your_token_here
```

### Windows (PowerShell):
```powershell
$env:HUGGINGFACE_API_KEY="hf_your_token_here"
```

### Windows (.venv activated):
```powershell
$env:HUGGINGFACE_API_KEY="hf_your_token_here"
```

## Step 3: Restart the Backend

Since you have the virtual environment activated:

```bash
cd backend
python main.py
```

## Step 4: Test the AI

Once the backend is running, try these test messages:
- "What is artificial intelligence?"
- "Explain machine learning"
- "¿Cómo funciona la IA?"

## What You'll Get:

✅ Real AI responses from Microsoft DialoGPT-medium
✅ Multilingual support maintained
✅ Free tier usage (generous limits)
✅ Much better conversation quality

## Troubleshooting:

If you get "API key not found":
- Double-check the environment variable is set
- Restart your terminal/backend server
- Verify the token starts with "hf_"

The AI will automatically fall back to rule-based responses if the API is unavailable, so the chatbot will always work!
