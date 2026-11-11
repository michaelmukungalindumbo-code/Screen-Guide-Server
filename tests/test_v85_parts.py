import os, asyncio, json
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run
class Msgs:
    def __init__(self, out): self.out = list(out); self.calls = []
    async def create(self, **kw):
        self.calls.append(kw)
        class U: input_tokens = 900; output_tokens = 40
        class B: type = "text"; text = self.out.pop(0)
        class M: content = [B()]; usage = U(); stop_reason = "end_turn"
        return M()
class Client:
    def __init__(self, out): self.messages = Msgs(out)
main.settings.ANTHROPIC_API_KEY = main.settings.ANTHROPIC_API_KEY or "test"
ANS = json.dumps({"kind": "guide", "text": "Open Files. Tap Show me and I will point to each step.", "goal": "Open Safe folder in the Files app",
                  "plan": ["Open Files", "Tap Safe folder"], "needs_apps": False})

# 11 Nov, the real-AI check (the first run with credit): "How do I open the Safe Folder app?" was answered "Safe Folder is
# not in your list of apps... check Settings for it", with a plan to search for it. The AI was never told what the phone
# app already knows (v0.91): some things people call apps are parts of an app. Now the question's own words say so.
def sent(q, apps=("Chrome", "Files", "Settings")):
    main._claude_client = Client([ANS, ANS])
    main._TALLY.set(None)
    run(main._answer(q, "en", [], [], apps=list(apps)))
    m = main._claude_client.messages.calls[0]["messages"][0]["content"]
    return m if isinstance(m, str) else " ".join(p.get("text", "") for p in m if isinstance(p, dict))

p = sent("How do I open the Safe Folder app?")
assert "<part_of_an_app>Safe folder is not an app. It is a part of the Files app" in p, p[-600:]
assert p.index("<part_of_an_app>") < p.index("<user_message>")
p = sent("where is app twin")
assert "App twin is not an app. It is a part of the Settings app" in p
assert "<part_of_an_app>" not in sent("How do I open WhatsApp?")
assert "<part_of_an_app>" not in sent("Is it safe to keep photos in a folder?")      # the two words apart: not the Safe folder
assert main._part_of("SAFE  FOLDER please") == ("Safe folder", "Files")
assert main._part_of("") is None
assert "part_of_an_app" in main.SYSTEM
assert int(main.PROMPT_VERSION) >= 61
print("a part of an app that people call an app: the helper is told which app it is in")
