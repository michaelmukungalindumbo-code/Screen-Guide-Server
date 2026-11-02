import os, asyncio, json, time
os.environ.update(ADMIN_KEY="k", GITHUB_TOKEN="ghp_test", AI_WATCH_PER_DAY="5")
import main
run = asyncio.run
class Msgs:
    def __init__(self, out): self.out = list(out)
    async def create(self, **kw):
        class U: input_tokens = 900; output_tokens = 40
        class B: type = "text"; text = self.out.pop(0)
        class M: content = [B()]; usage = U(); stop_reason = "end_turn"
        return M()
class Client:
    def __init__(self, out): self.messages = Msgs(out)
issues = []
async def fake_github(method, path, payload):
    if method == "GET":
        return [dict(i) for i in reversed(issues)]
    if path.endswith("/issues"):
        issues.append({"number": 500 + len(issues), "title": payload["title"], "body": payload["body"], "state": "open",
                       "created_at": "2026-11-01T10:00:00Z"}); return {"number": issues[-1]["number"]}
    return {}
main._github = fake_github
def h(i): return dict(x_app_token="tok", x_install_id=i, x_tester="1")
UPLOAD = ["Cancel [tap]", "Upload [tap]", "PDF [switch]"]
def guide(i):
    run(main.event(main.Event(event="start", guide="ai"), **h(i)))
    main._claude_client = Client([json.dumps({"label": None, "say": "Tap the button to save it.", "done": False, "x": None, "y": None, "look_for": None})])
    run(main.next_step(main.Next(goal="Scan a document with the Drive app", labels=UPLOAD), **h(i)))
    main._claude_client = Client([json.dumps({"problems": []})])
    return run(main.watch_review(**h(i)))["problems"]

# The same problem while its issue is still open: not sent again (issue #6 on 2 Nov)
ps = guide("r1")
assert run(main.watch_send(main.WatchSend(ids=[ps[0]["id"]]), **h("r1"))) == {"sent": 1, "skipped": 0}
ps = guide("r2")
assert run(main.watch_send(main.WatchSend(ids=[ps[0]["id"]], report=True), **h("r2"))) == {"sent": 0, "skipped": 1, "done": [ps[0]["id"]], "wait": []}
# The issue was closed as fixed, and the problem came back: it is sent again, saying so
issues[0]["state"] = "closed"
ps = guide("r3")
assert run(main.watch_send(main.WatchSend(ids=[ps[0]["id"]]), **h("r3"))) == {"sent": 1, "skipped": 0}
assert "**This came back:** the same problem was reported in #500, which was closed as fixed." in issues[-1]["body"], issues[-1]["body"]
assert "came back" not in issues[0]["body"]
assert main.SERVER_VERSION >= "0.63"
print("came back ok")
