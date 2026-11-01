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
ans = lambda t, g: json.dumps({"kind": "guide", "text": t, "goal": g, "plan": ["Open Drive", "Tap Scan"], "needs_apps": True})
APPS = ["Camera", "Drive", "Airtel Money", "Zanaco Bank", "Google Pay", "WhatsApp", "Drive", "x" * 60]
# 1. The app list goes into the prompt, cleaned: no money apps, no repeats, 40 characters at most
assert main._apps(APPS) == ["Camera", "Drive", "WhatsApp", "x" * 40], main._apps(APPS)
main._cache.clear()
main._claude_client = c = Client([ans("Use Drive.", "Scan a document with Drive"), ans("Use Drive again.", "Scan a document with Drive"),
                                  ans("Generic.", "Scan a document with Drive"), ans("Generic 2.", "x")])
r = run(main.ask(main.Ask(question="How do I scan a document?", apps=APPS, device="Samsung tablet, Android 14"), x_app_token="tok", x_install_id="v42a"))
m = json.dumps(c.messages.calls[0]["messages"], ensure_ascii=False); sysp = c.messages.calls[0]["system"]
assert "<installed_apps>Camera, Drive, WhatsApp, " in m and "Airtel" not in m and "Zanaco" not in m and "Google Pay" not in m, m
assert "Install <name> from the Play Store" in sysp and "who makes it" in sysp and "free data" in sysp
assert r["goal"] == "Scan a document with Drive", r
# 2. Answers chosen from one phone's apps are not saved for others, nor served from the shared store
r2 = run(main.ask(main.Ask(question="How do I scan a document?", apps=["Camera"], device="Samsung tablet, Android 14"), x_app_token="tok", x_install_id="v42b"))
assert r2["answer"] == "Use Drive again." and len(c.messages.calls) == 2 and not main._cache, "asked anew, nothing saved"
g1 = run(main.ask(main.Ask(question="How do I scan a document?", device="Samsung tablet, Android 14"), x_app_token="tok", x_install_id="v42c"))
g2 = run(main.ask(main.Ask(question="How do I scan a document?", device="Samsung tablet, Android 14"), x_app_token="tok", x_install_id="v42d"))
assert g1["answer"] == g2["answer"] == "Generic." and len(c.messages.calls) == 3, "without apps, saved answers still work"
r3 = run(main.ask(main.Ask(question="How do I scan a document?", apps=["Camera"], device="Samsung tablet, Android 14"), x_app_token="tok", x_install_id="v42e"))
assert r3["answer"] == "Generic 2." and len(c.messages.calls) == 4, "with apps, the shared saved answer is not used"
# 3. The step prompt knows how to install a named app; the privacy page says when app names are sent
main._claude_client = c = Client([json.dumps({"label": "Search apps & games", "say": "Tap Search apps & games.", "done": False, "x": None, "y": None, "look_for": None})])
r = run(main.next_step(main.Next(goal="Install Adobe Scan from the Play Store", labels=["Search apps & games [tap]", "Games [tap]", "Apps [selected]"]),
                       x_app_token="tok", x_install_id="v42"))
assert "type that name, then tap that app's Install" in c.messages.calls[0]["system"] and r["label"] == "Search apps & games", r
p = run(main.privacy()); b = getattr(p, "body", p); page = b.decode() if isinstance(b, bytes) else str(b)
assert "When you ask how to do something" in page
assert main.SERVER_VERSION >= "0.42"
print("installed apps, recommendations and saved answers ok")
