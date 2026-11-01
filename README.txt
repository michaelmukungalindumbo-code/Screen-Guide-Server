Build: pip install -r requirements.txt
Start: uvicorn main:app --host 0.0.0.0 --port $PORT
Set GEMINI_API_KEY and APP_TOKEN in the host environment settings. Never commit a real key.

AI fixer (optional): set GITHUB_TOKEN to a fine-grained GitHub token with only "Issues: read and write" on the
Screen-Guide repository. Each new kind of app crash then opens one issue there, labelled "ai-fix", and the AI on GitHub
proposes a fix on its own branch. At most AI_FIX_PER_DAY (default 3) a day. Leave GITHUB_TOKEN unset to turn it off.

Watcher (developer phones only: TEST builds, or "Show what ScreenGuide sees" on): every guide is checked for
problems (Help, a step that did not work, nothing to point at, slow, going round in circles, stopped) and reviewed by
the AI at the end. The phone flashes red when a problem is seen and shows them in a pop-up after the guide. Only
"Allow" sends them to the AI fixer as "ai-fix" issues (cleaned: known button names only). Uses the same GITHUB_TOKEN.
At most AI_WATCH_PER_DAY (default 3) a day.
