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
def step(reply, labels, note=""):
    main._claude_client = Client([json.dumps(reply)])
    r = run(main.next_step(main.Next(goal="Check storage space", labels=labels, note=note), x_app_token="tok", x_install_id="v34"))
    return r, main._claude_client.messages.calls[0]
SETTINGS = ["Search [tap]", "My Phone [tap]", "Wi-Fi [tap]", "Bluetooth [tap]"]

# 1. the exact reply seen on the phone: two actions and a place -> one action, no place
r, c = step({"label": "Search", "say": "Tap the Search box at the top, then type the word storage.", "done": False, "x": None, "y": None, "look_for": None}, SETTINGS)
assert r["label"] == "Search" and r["say"] == "Tap the Search box.", r
assert main._one_action("Tap “Storage”.", True) == "Tap “Storage”."
assert main._one_action("Tap Settings in the top right corner.", True) == "Tap Settings."
assert main._one_action("Look at the top of the page, then tap Back.", False) == "Look at the top of the page, then tap Back.", "only when pointing"
print("one action ok")

# 2. look_for: the item is further down the list -> the phone rings it when it shows
r, c = step({"label": None, "say": "Scroll down to find Storage.", "done": False, "x": None, "y": None, "look_for": "Storage"}, SETTINGS)
assert r["label"] is None and r["look_for"] == "Storage" and r["say"] == "Scroll down to find Storage.", r
assert main.STATS["look_for"] >= 1
# already on screen -> becomes the label
r, _ = step({"label": None, "say": "Tap Wi-Fi.", "done": False, "x": None, "y": None, "look_for": "Wi-Fi"}, SETTINGS)
assert r["label"] == "Wi-Fi" and r["look_for"] is None, r
# risky names are never looked for
r, _ = step({"label": None, "say": "Scroll down.", "done": False, "x": None, "y": None, "look_for": "Reset phone"}, SETTINGS)
assert r["look_for"] is None, r
# older replies without the field still work
r, _ = step({"label": "Bluetooth", "say": "Tap Bluetooth.", "done": False, "x": None, "y": None}, SETTINGS)
assert r["label"] == "Bluetooth" and r["look_for"] is None
print("look_for ok")

# 3. the prompt knows about scrolling, typing and search pages; the phone's note reaches the AI inside tags
r, c = step({"label": None, "say": "Keep typing.", "done": False, "x": None, "y": None, "look_for": None},
            ["stor [text]", "Credential Storage [tap]"], note="They typed “stor” in the search box.")
assert "<user_note>They typed" in c["messages"][0]["content"]
sysp = c["system"]
for want in ("look_for", "Typing is hard", "search page", "Never say they have reached a page", "scrolled the list"):
    assert want in sysp, want
assert "look_for" in main.NEXT_SCHEMA["required"] and main.SERVER_VERSION >= "0.34"
print("prompt ok")
