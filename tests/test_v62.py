import os, asyncio, json, time
os.environ.update(ADMIN_KEY="k", GITHUB_TOKEN="ghp_test")
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
def J(label, say): return json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})
def h(i, tester="1"): return dict(x_app_token="tok", x_install_id=i, x_tester=tester)
def step(i, label, say, labels):
    main._claude_client = Client([J(label, say)] * 2)
    return run(main.next_step(main.Next(goal="Scan a document with the Drive app", labels=labels), **h(i)))
def ev(i, e, guide): run(main.event(main.Event(event=e, guide=guide), **h(i)))
def kinds(i): return [(p["kind"], p["step"]) for p in main._sessions[i]["problems"]]
DRIVE = ["My Drive [tap]", "Scan Document [tap]", "Create new [tap]"]
SHUTTER = "Hold the camera still over the paper, then tap the big round button in the bottom middle to take the photo."

# 1. "Why did you stop?" -> "Just testing": not a problem (2 Nov: a Stop on purpose came back as "Stopped at step 1")
ev("q1", "start", "ai"); step("q1", "Scan Document", "Tap “Scan Document”.", DRIVE)
ev("q1", "stop", "quit_ai")
assert kinds("q1") == [] and main._sessions["q1"]["end"] == "stop"
main._claude_client = Client([json.dumps({"problems": []})])
assert run(main.watch_review(**h("q1"))) == {"problems": []}           # nothing to show: no pop-up
# "I was stuck" (or no answer): still a problem, as before
ev("q2", "start", "ai"); step("q2", "Scan Document", "Tap “Scan Document”.", DRIVE)
ev("q2", "stop", "ai")
assert kinds("q2") == [("stopped", 1)]
# The same in "Test an app"
assert run(main.watch_test_start(main.WatchTest(pkg="zm.screenguide", app="ScreenGuide", repo="michaelmukungalindumbo-code/Screen-Guide"), **h("q3")))["ok"]
step("q3", "Scan Document", "Tap “Scan Document”.", DRIVE)
ev("q3", "stop", "quit_ai")
assert kinds("q3") == []

# 2. The screen changed while the step stayed (2 Nov: the photo was taken, the guide kept saying to take it for 15 s)
ev("c1", "start", "ai")
step("c1", "Scan Document", "Tap “Scan Document”.", DRIVE)
step("c1", None, SHUTTER, ["… [text]"])
r = run(main.watch_stale(main.WatchStale(step=2, secs=14), **h("c1")))
assert r == {"watch": 1, "pic": 151}, r
assert run(main.watch_stale(main.WatchStale(step=2, secs=20), **h("c1"))) == {"watch": 1, "pic": 0}    # once per step
assert run(main.watch_stale(main.WatchStale(step=9, secs=5), **h("c1")))["pic"] == 0                   # no such step
assert run(main.watch_stale(main.WatchStale(step=2, secs=5), **h("c1", tester="")))["pic"] == 0         # not a developer phone
card = main._rule_card(main._sessions["c1"]["problems"][0])
assert card["title"] == "Screen changed, step 2 stayed" and "About 14 seconds" in card["what"] and "media/step151.jpg" in card["what"], card
# The review asks for that picture too, and is told what it shows
r = run(main.watch_review(main.WatchReview(have=[1, 2, 151]), **h("c1")))
assert r["want"] == [1, 2, 151], r
main._claude_client = Client([json.dumps({"problems": [{"step": 2, "kind": "stale", "title": "x", "what": "The picture shows the photo was taken and Next is showing.", "fix": "Look again when the screen changes."}]})])
PIC = "A" * 300
r = run(main.watch_review(main.WatchReview(have=[1, 2, 151], shots=[{"n": n, "jpg": PIC} for n in (1, 2, 151)]), **h("c1")))
text = main._claude_client.messages.calls[0]["messages"][0]["content"][-1]["text"]
assert "<pictures>step 1, step 2, picture 151 (the screen after it changed while step 2 was still shown)</pictures>" in text, text
p = r["problems"][0]
assert p["title"] == "Screen changed, step 2 stayed" and "Next is showing" in p["what"] and p["fix"] == "Look again when the screen changes."
# Allow sends picture 151 with the others for the fixer
issues = []
async def fake_github(method, path, payload):
    if method == "GET": return []
    if path.endswith("/issues"):
        issues.append(payload); return {"number": 400 + len(issues)}
    return {}
main._github = fake_github
out = run(main.watch_send(main.WatchSend(ids=[p["id"]], shots=[{"n": n, "jpg": PIC} for n in (1, 2, 151)]), **h("c1")))
assert out == {"sent": 1, "skipped": 0}, out
assert "media/step151.jpg" in issues[0]["body"] and "Screen pictures:** 3" in issues[0]["body"]
assert main.SERVER_VERSION >= "0.62"
print("why stop and screen changed ok")
