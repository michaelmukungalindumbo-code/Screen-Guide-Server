import os, asyncio
os.environ.update(ADMIN_KEY="owner-secret", GOOGLE_CLIENT_ID="web-123.apps.googleusercontent.com")
os.environ.pop("DATABASE_URL", None)
import main
run = asyncio.run

# 6 Nov: the owner asked for a choice of chat background colours (app 0.78: Customize ScreenGuide, Chat background).
# 1. The choice is kept in the account with the other settings, so it comes back on a new phone
async def fake_google(tok):
    return {"michael": {"sub": "111", "email": "m@example.com", "name": "Michael"}}.get(tok)
main._verify_google = fake_google
main.UPSTASH_URL = ""; main._store = main._Store("")
H = dict(x_app_token="tok")
sess = run(main.auth_google(main.GoogleIn(id_token="michael"), x_install_id="phone1", **H))["session"]
run(main.me_save(main.MeIn(profile={"chat_bg": "green", "theme": "dark", "secret": "x"}, learned=[]), x_install_id="phone1", x_session=sess, **H))
back = run(main.auth_google(main.GoogleIn(id_token="michael"), x_install_id="phone2", **H))["profile"]
assert back.get("chat_bg") == "green" and back.get("theme") == "dark" and "secret" not in back, back

# 2. "Change my ScreenGuide chat background": the chat knows where ScreenGuide's own settings are. (Until 0.80 it answered
# in words only; the owner then chose Show me inside ScreenGuide too: tests/test_v80.py.)
assert "Customize ScreenGuide" in main.SYSTEM and "Chat background" in main.SYSTEM
assert main.SERVER_VERSION >= "0.79" and main.PROMPT_VERSION >= "56"
print("the chat background is kept, and the chat knows where it is")
