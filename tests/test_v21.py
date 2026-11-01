import os, asyncio, json
os.environ.update(ADMIN_KEY="k")
import main
from fastapi import HTTPException
run = asyncio.run

# 1. structured outputs are requested, and a refusal of the schema falls back without breaking
class E400(Exception):
    status_code = 400
class Msgs:
    def __init__(self, fail): self.fail = fail; self.calls = []
    async def create(self, **kw):
        self.calls.append(kw)
        if self.fail and "format" in kw.get("extra_body", {}).get("output_config", {}): raise E400("output_config.format not supported")
        class U: input_tokens = 10; output_tokens = 5
        class B: type = "text"; text = json.dumps({"kind": "answer", "text": "hi", "goal": "", "plan": [], "needs_apps": False})
        class M: content = [B()]; usage = U()
        return M()
class Client:
    def __init__(self, fail): self.messages = Msgs(fail)
main._claude_client = Client(False)
out = run(main._complete("sys", "q", None, "ask", main.ASK_SCHEMA))
kw = main._claude_client.messages.calls[0]
assert kw["extra_body"]["output_config"]["format"]["schema"]["required"] == ["kind", "text", "goal", "plan", "needs_apps"]
assert json.loads(out)["text"] == "hi"
main._claude_client = Client(True)
out = run(main._complete("sys", "q", None, "ask", main.ASK_SCHEMA))
assert json.loads(out)["text"] == "hi" and main._feats("claude-haiku-5-5")["schema"] is False and len(main._claude_client.messages.calls) == 2
run(main._complete("sys", "q", None, "ask", main.ASK_SCHEMA))
assert "format" not in main._claude_client.messages.calls[-1]["extra_body"].get("output_config", {}), "after a refusal, stop asking for the schema"
assert main._claude_client.messages.calls[-1]["extra_body"]["thinking"] == {"type": "disabled"}, "other settings stay on"
main._feat.clear()
for s in (main.ASK_SCHEMA, main.NEXT_SCHEMA):   # only features the docs list as supported
    t = json.dumps(s)
    assert s["additionalProperties"] is False and not any(w in t for w in ("maxItems", "minLength", "maximum", "minimum"))
print("structured outputs ok")

# 2. risky buttons are never ringed, and no picture point either
async def fake(system, question, images=None, kind="step", schema=None, **kw):
    fake.schema = schema
    return json.dumps(fake.reply)
main._complete = fake
cases = [("Send money [tap]", "Send money", True), ("Pay [tap]", "Pay", None), ("Enter PIN [tap]", "Enter PIN", None),
         ("Factory reset [tap]", "Factory reset", None), ("Settings [tap]", "Settings", "Settings"), ("Payments history [tap]", "Payments history", "Payments history")]
for lab, ai, want in cases:
    fake.reply = {"label": ai, "say": "Tap it.", "done": False, "x": 0.5, "y": 0.5}
    r = run(main.next_step(main.Next(goal="g", labels=[lab], image="AAAA"), x_app_token="tok", x_install_id="r" + ai))
    if want is True: want = None
    assert r["label"] == want, (ai, r)
    if want is None: assert r["x"] is None and "yourself" in r["say"], r
assert fake.schema is main.NEXT_SCHEMA
print("risky guard ok")

# 3. wording adapts to the person
fake.reply = {"label": None, "say": "x", "done": False, "x": None, "y": None}
async def cap(system, question, images=None, kind="step", schema=None, **kw):
    cap.q = question; return json.dumps(fake.reply)
main._complete = cap
run(main.next_step(main.Next(goal="g", labels=["A [tap]"], level="new"), x_app_token="tok", x_install_id="lv1"))
assert "new to smartphones" in cap.q
run(main.next_step(main.Next(goal="g", labels=["A [tap]"], level="confident"), x_app_token="tok", x_install_id="lv2"))
assert "very short" in cap.q
run(main.next_step(main.Next(goal="g", labels=["A [tap]"]), x_app_token="tok", x_install_id="lv3"))
assert "new to smartphones" not in cap.q and "very short" not in cap.q
print("adaptive ok")

# 4. size limit
class Req:
    def __init__(self, n): self.headers = {"content-length": str(n)}
async def nxt(req): return "passed"
assert run(main._size_limit(Req(3_000_000), nxt)).status_code == 413
assert run(main._size_limit(Req(1000), nxt)) == "passed"
print("size limit ok")
