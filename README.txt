Build: pip install -r requirements.txt
Start: uvicorn main:app --host 0.0.0.0 --port $PORT
Set GEMINI_API_KEY and APP_TOKEN in the host environment settings. Never commit a real key.

AI fixer (optional): set GITHUB_TOKEN to a fine-grained GitHub token with only "Issues: read and write" on the
Screen-Guide repository. Each new kind of app crash then opens one issue there, labelled "ai-fix", and the AI on GitHub
proposes a fix on its own branch. At most AI_FIX_PER_DAY (default 3) a day. Leave GITHUB_TOKEN unset to turn it off.

Watcher (tester phones only): when a guide goes wrong after someone asks for Help (Help repeated itself, still stuck,
or gave up), the server opens an "ai-fix" issue with a cleaned note of the screen (known button names only). Uses the
same GITHUB_TOKEN. At most AI_WATCH_PER_DAY (default 2) a day.
