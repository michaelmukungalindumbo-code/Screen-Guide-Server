import os, asyncio, json, time
os.environ.update(ADMIN_KEY="k")
import main
from fastapi import HTTPException
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
def J(label, say, done=False, x=None): return json.dumps({"label": label, "say": say, "done": done, "x": x, "y": x, "look_for": None})
main.settings.ANTHROPIC_API_KEY = main.settings.ANTHROPIC_API_KEY or "test"

# The owner's phone (11 Nov, twice): "Scan a document with Drive". On Drive's camera and scan pages ScreenGuide finds no
# words at all (the app does not share them), and the guide stopped dead: "I cannot read the words in this app. Turn on
# Screen pictures…". "This issue keeps appearing." A screen that cannot be read is no longer the end: the helper says so,
# and says what people usually tap on that screen when the goal and the way there make it clear. It never points.
GOAL = "Scan a document with the Drive app"
PATH = ["Home screen", "Drive"]   # only common names are kept: "Drive"
def step(out, labels=(), tester=True, i="dev87", goal=GOAL, image=""):
    main._claude_client = Client(out)
    r = run(main.next_step(main.Next(goal=goal, labels=list(labels), history=["Tap “Scan” to start scanning."], path=PATH, image=image),
                           x_app_token="tok", x_install_id=i, x_tester="1" if tester else ""))
    return r, main._claude_client.messages.calls

b0 = main.STATS["blind_steps"]
r, calls = step([J(None, "I can’t see this screen. Hold the phone over the paper; then tap “Next” at the bottom right.")])
assert r["label"] is None and r["x"] is None and r["done"] is False and r["need_picture"] is False, r
assert r["say"].startswith("I can’t see this screen."), r
assert main.STATS["blind_steps"] == b0 + 1
sent = calls[0]["messages"][0]["content"]; sent = sent if isinstance(sent, str) else " ".join(p.get("text", "") for p in sent if isinstance(p, dict))
assert "ScreenGuide cannot read this screen" in sent and "<path>Drive</path>" in sent and GOAL in sent
assert "<screen_words>" not in sent                                   # nothing made up to look like a screen

# Whatever the AI answers, nothing is ever pointed at and the task is never called done on a screen nobody can see
r, _ = step([J("Next", "Tap “Next”.", done=True, x=0.5)])
assert r["label"] is None and r["x"] is None and r["y"] is None and r["done"] is False, r
# An answer that cannot be read: plain true words, not an error
r, _ = step(["not json"] * 6)
assert r["say"] == main.BLIND_PLAIN and r["label"] is None, r
# Money: never guessed at
r, calls = step([J(None, "Type your PIN.")], goal="Send money with mobile money")
assert r["say"] == main.BLIND_PLAIN and len(calls) == 0, (r, len(calls))

# A screen with words, or with a picture, goes the usual way
r, calls = step([J("Next", "Tap “Next”.")], labels=["Discard scan [tap]", "Next [tap]"])
assert r["label"] == "Next", r
# Users' phones: staged. Before its quiet hours, as before (nothing to work with)
main._launch["live"][main.STAGED["blind_step"]] = time.time()
try:
    step([J(None, "x")], tester=False, i="user87"); raise AssertionError("should have refused")
except HTTPException as e:
    assert e.status_code == 400
main._launch["live"][main.STAGED["blind_step"]] = time.time() - 25 * 3600
r, _ = step([J(None, "I can’t see this screen. Do this step yourself.")], tester=False, i="user87b")
assert r["label"] is None and r["say"].startswith("I can’t see"), r
assert main.STAGED["blind_step"] == "0.87" and main.SERVER_VERSION >= "0.87"
print("a screen that cannot be read is not the end: said so, with what people usually tap there; never pointed at, never money")
