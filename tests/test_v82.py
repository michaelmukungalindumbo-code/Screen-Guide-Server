import os, asyncio, json
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run
class Msgs:
    def __init__(self, out): self.out = list(out); self.calls = []
    async def create(self, **kw):
        self.calls.append(kw)
        class U: input_tokens = 2300; output_tokens = 200
        class B: type = "text"; text = self.out.pop(0)
        class M: content = [B()]; usage = U(); stop_reason = "end_turn"
        return M()
class Client:
    def __init__(self, out): self.messages = Msgs(out)
def A(text, goal="", plan=None, kind="answer"): return json.dumps({"kind": kind, "text": text, "goal": goal, "plan": plan or [], "needs_apps": False})
def J(label, say): return json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})

# 6 Nov, 05:23: WhatsApp, then "the background display in the chat" got ScreenGuide's own setting; the correction went
# back to setting up WhatsApp; "wallpaper" got the phone's. The owner chose three fixes.

# 1. Follow-ups are answered by the stronger AI (the earlier conversation matters); first questions by the fast one
main.settings.ANTHROPIC_API_KEY = main.settings.ANTHROPIC_API_KEY or "test"
main._claude_client = Client([A("WhatsApp is set up from its first screen.")])
run(main._answer("How do I set up WhatsApp on a new phone?", "en", [], []))
first = main._claude_client.messages.calls[0]["model"]
assert first != main.STRONG_MODEL, first
HIST = ["User: How do I set up WhatsApp on a new phone?", "Helper: Open WhatsApp, agree, and type your number."]
main._claude_client = Client([A("In WhatsApp, open Settings, then Chats, then Default chat theme.")])
run(main._answer("How do I change the background display in the chat", "en", [], HIST))
assert main._claude_client.messages.calls[0]["model"] == main.STRONG_MODEL
assert main.STATS["strong_chats"] >= 1
main._strong_chat_day[main._today()] = main.STRONG_CHATS_PER_DAY            # the day's limit: the fast one again
main._claude_client = Client([A("In WhatsApp, open Settings.")])
main._TALLY.set(None)
run(main._answer("And the colour?", "en", [], HIST))
assert main._claude_client.messages.calls[0]["model"] != main.STRONG_MODEL

# 2. The chat is told what "the chat" means, and what to do after a correction
assert 'only when the person names ScreenGuide or says "this app" or "here"' in main.SYSTEM
assert "never ScreenGuide's" in main.SYSTEM and "When the person corrects you" in main.SYSTEM
assert "Never go back to an older topic they did not ask about again" in main.SYSTEM

# 3. Never pointing at a change to the person's account that their goal did not ask for
ACC = ["Back [tap]", "Login and security [text]", "Two-step verification [tap]", "Username [tap]", "Change phone number [tap]",
       "Log out [tap]"]
def step(goal, label, say, i="dev82"):
    main._claude_client = Client([J(label, say)] * 3)
    return run(main.next_step(main.Next(goal=goal, labels=ACC), x_app_token="tok", x_install_id=i, x_tester="1"))
r = step("Set up WhatsApp with your phone number", "Change phone number", "Tap “Change phone number” to set up your number.")
assert r["label"] is None and "did not ask for that" in r["say"], r
r = step("Change my WhatsApp number", "Change phone number", "Tap “Change phone number”.")
assert r["label"] == "Change phone number", r
r = step("Log out of WhatsApp", "Log out", "Tap “Log out”.")
assert r["label"] == "Log out", r
# 4. The stronger AI (Sonnet 5.5) refuses thinking "disabled" and names "between_tools" (6 Nov, the first real-AI check).
# Dropping the setting left it thinking before every answer; the server now uses the setting the service named.
class Err(Exception):
    def __init__(self, msg): super().__init__(msg); self.status_code = 400
SONNET_SAYS = ("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'To turn thinking "
               "off on this model, send \"thinking\": {\"type\": \"between_tools\"} instead of {\"type\": \"disabled\"}.'}}")
class Refuses(Msgs):
    async def create(self, **kw):
        if kw.get("extra_body", {}).get("thinking") == {"type": "disabled"}:
            self.calls.append(kw); raise Err(SONNET_SAYS)
        return await super().create(**kw)
main._feat.clear()
main._strong_chat_day.clear()   # part 1 used up the day's limit
main._claude_client = Client([])
main._claude_client.messages = Refuses([A("In WhatsApp, open Settings.")] * 3)
main._TALLY.set(None)
run(main._answer("And the colour?", "en", [], HIST))
calls = main._claude_client.messages.calls
assert calls[0]["model"] == main.STRONG_MODEL and calls[0]["extra_body"]["thinking"] == {"type": "disabled"}
assert calls[1]["extra_body"]["thinking"] == {"type": "between_tools"}, calls[1].get("extra_body")
assert calls[1]["extra_body"]["output_config"]["effort"] == "low"
run(main._answer("And the colour?", "en", [], HIST))   # remembered: no refused call the second time
assert len(calls) == 3 and calls[2]["extra_body"]["thinking"] == {"type": "between_tools"}
assert main._feats("claude-haiku-5-5")["thinking"] is True   # the fast AI keeps "disabled"
assert main.SERVER_VERSION >= "0.82" and main.PROMPT_VERSION >= "59"
print("follow-ups by the stronger AI; 'the chat' is the app talked about; no account change nobody asked for")
