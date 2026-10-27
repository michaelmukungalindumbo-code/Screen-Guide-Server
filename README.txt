Build: pip install -r requirements.txt
Start: uvicorn main:app --host 0.0.0.0 --port $PORT
Set GEMINI_API_KEY and APP_TOKEN in the host environment settings. Never commit a real key.
