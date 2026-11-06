import os, asyncio, json
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run
class Msgs:
    def __init__(self, out): self.out = list(out); self.calls = []
    async def create(self, **kw):
        self.calls.append(kw)
        class U: input_tokens = 900; output_tokens = 80
        class B: type = "text"; text = self.out.pop(0)
        class M: content = [B()]; usage = U(); stop_reason = "end_turn"
        return M()
class Client:
    def __init__(self, out): self.messages = Msgs(out)
def A(text, goal, plan): return json.dumps({"kind": "guide", "text": text, "goal": goal, "plan": plan, "needs_apps": False})
HIST = ["User: How do I change the background display in screen guide",
        "Helper: You can change the chat background in ScreenGuide from its menu. Tap Show me and I will point to each step."]

# 6 Nov: "How do I logout", right after a question about ScreenGuide. The answer said "Tap Show me and I will point to the
# steps inside ScreenGuide", but its steps opened WhatsApp. When the words and the steps are about different apps, the AI
# is asked once more; the second answer is the one shown.
WRONG = A("Logging out depends on which app you mean. Tell me the app name, or tap Show me and I will point to the steps inside ScreenGuide.",
          "Log out of WhatsApp", ["Open the WhatsApp app", "Tap the three dots at the top", "Tap Settings", "Tap Account", "Tap Log out"])
RIGHT = A("To sign out of ScreenGuide, tap Show me and I will point to each step.", "Sign out of ScreenGuide",
          ["Tap the three dots at the top", "Tap Your account", "Tap Sign out"])
main._claude_client = Client([WRONG, RIGHT])
r = run(main._answer("How do I logout", "en", [], HIST))
calls = main._claude_client.messages.calls
assert len(calls) == 2 and "same app" in str(calls[1]["messages"][0]["content"]), len(calls)
assert r["goal"] == "Sign out of ScreenGuide" and r["plan"][1] == "Tap Your account", r
assert "<conversation>" in str(calls[0]["messages"][0]["content"]) and "screen guide" in str(calls[0]["messages"][0]["content"])

# Not asked again: a WhatsApp guide whose words name ScreenGuide only as the helper, and a ScreenGuide guide
OK = A("Tap Show me and ScreenGuide will point to each step in WhatsApp.", "Log out of WhatsApp",
       ["Open the WhatsApp app", "Tap the three dots at the top", "Tap Settings"])
main._claude_client = Client([OK])
run(main._answer("How do I log out of WhatsApp", "en", [], []))
assert len(main._claude_client.messages.calls) == 1
main._claude_client = Client([RIGHT])
run(main._answer("How do I sign out", "en", [], HIST))
assert len(main._claude_client.messages.calls) == 1
assert main._mixed_apps("Steps inside ScreenGuide.", "", ["Open the WhatsApp app"])
assert main._mixed_apps("", "Change the colours in ScreenGuide", ["Open YouTube"])
assert not main._mixed_apps("Steps inside ScreenGuide.", "", ["Tap the three dots at the top"])
assert not main._mixed_apps("Steps inside ScreenGuide.", "", [])

# The chat knows a short follow-up continues the conversation, and ScreenGuide's whole menu (it did not know Sign out)
assert "A short follow-up that names no app" in main.SYSTEM and "Ask which app only when <conversation> does not say" in main.SYSTEM
assert '"Your account" (Sign in with Google, Sign out, Delete my account)' in main.SYSTEM
assert "Your photo from the gallery" in main.SYSTEM
assert main.SERVER_VERSION >= "0.81" and main.PROMPT_VERSION >= "58"
print("a follow-up stays on the topic; words and steps are about the same app")
