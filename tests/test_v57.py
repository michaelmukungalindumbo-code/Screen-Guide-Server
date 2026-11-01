import os, sys, types, asyncio, json, time
os.environ.update(ADMIN_KEY="k", GITHUB_TOKEN="ghp_test", AI_WATCH_PER_DAY="3", AI_FIX_REPOS="me/zexam-app, bad repo name")
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
issues, gets = [], []
async def fake_github(method, path, payload):
    if method == "GET":
        gets.append(path); return list(reversed(issues))
    if path.endswith("/issues"):
        issues.append({"path": path, "number": 120 + len(issues), "title": payload["title"], "body": payload["body"],
                       "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}); return {"number": issues[-1]["number"]}
    return {}
main._github = fake_github
H = dict(x_app_token="tok", x_install_id="dev57", x_tester="1")
def start(**kw):
    return run(main.watch_test_start(main.WatchTest(**kw), **H))
def screen(labels, found=(), new=True):
    return run(main.watch_screen(main.WatchScreen(labels=list(labels), found=list(found), new=new), **H))

assert main.AI_FIX_REPOS == {"me/zexam-app"}
assert run(main.watch_test_start(main.WatchTest(pkg="zm.screenguide", repo="me/x"), x_app_token="tok", x_install_id="n57", x_tester=""))["ok"] is False
assert start(pkg="zm.screenguide", app="ScreenGuide", repo="not a repo")["ok"] is False
assert start(pkg="zm.zexam", app="Zexam", repo="someone/else") == {"ok": True, "repo_ok": False}
r = start(pkg="zm.screenguide", app="ScreenGuide", repo="michaelmukungalindumbo-code/Screen-Guide", goal="Turn on the torch", device="Infinix phone, Android 14")
assert r == {"ok": True, "repo_ok": True}, r

# Screens of the app under test, with what the phone spotted on them
HOME = ["Ask anything [text]", "Speak [tap]", "Mum's chat [tap]", "Settings [tap]"]
r = screen(HOME, [{"kind": "error_text", "detail": "Something went wrong. Call 0977 123 456"}])
assert r == {"watch": 1, "watch_step": 1}, r
r = screen(HOME, [{"kind": "dead_tap", "detail": "Speak"}], new=False)
assert r == {"watch": 2, "watch_step": 0}, r                     # same screen: no new step, no new picture
r = screen(["Settings [text]", "About [tap]"], [{"kind": "unlabeled", "detail": "3"}, {"kind": "small_target", "detail": "2"},
                                                 {"kind": "crash", "detail": "ScreenGuide keeps stopping"}, {"kind": "not a kind"}])
assert r == {"watch": 5, "watch_step": 2}, r
s = main._sessions["dev57"]
assert s["kind"] == "test" and [p["kind"] for p in s["problems"]] == ["error_text", "dead_tap", "unlabeled", "small_target", "crash"]
assert "0977" not in s["problems"][0]["detail"] and s["steps"][0]["screen"][2] == "… [tap]"

# With a goal, ScreenGuide's guide runs inside the test: its "start" does not end the test, its steps join it
run(main.event(main.Event(event="start", guide="ai"), **H))
assert main._sessions["dev57"] is s and s["kind"] == "test"
main._claude_client = Client([json.dumps({"label": "Settings", "say": "Tap “Settings”.", "done": False, "x": None, "y": None, "look_for": None})])
r = run(main.next_step(main.Next(goal="Turn on the torch", labels=HOME), **H))
assert r["watch_step"] == 3 and len(s["steps"]) == 3
run(main.event(main.Event(event="stop", guide="ai"), **H))
assert "stopped" not in [p["kind"] for p in s["problems"]]       # stopping a test is not a problem

# After the test: problems explained, and they go to the app's own repository
main._claude_client = Client([json.dumps({"problems": []})])
ps = run(main.watch_review(**H))["problems"]
titles = [p["title"] for p in ps]
assert titles[:5] == ["Error message on screen 1", "A tap did nothing on screen 1", "Buttons with no name on screen 2",
                      "Small buttons on screen 2", "The app crashed on screen 2"], titles
assert ps[2]["what"].startswith("3 buttons have no text") and "“Speak” was tapped 3 times" in ps[1]["what"]
out = run(main.watch_send(main.WatchSend(ids=[ps[0]["id"], ps[4]["id"]]), **H))
assert out == {"sent": 2, "skipped": 0}, out
assert gets[-1].startswith("/repos/michaelmukungalindumbo-code/Screen-Guide/issues?")
i = issues[0]
assert i["path"] == "/repos/michaelmukungalindumbo-code/Screen-Guide/issues" and i["title"] == "App problem: Error message on screen 1 (ScreenGuide)", i
b = i["body"]
assert "Noticed while testing **ScreenGuide** (`zm.screenguide`)" in b and "with the goal “Turn on the torch”" in b
assert "**→** 1. spotted: error_text, dead_tap" in b and "screen: Ask anything [text], Speak [tap], … [tap], Settings [tap]" in b, b
assert "Phone: Infinix phone, Android 14" in b and "its code is this repository" in b and "Mum" not in b and "0977" not in b and "dev57" not in b

# A test of an app whose repository is not allowed yet: nothing is sent, and the developer is told what to do
start(pkg="zm.zexam", app="Zexam", repo="someone/else")
screen(["Download [tap]"], [{"kind": "dead_tap", "detail": "Download"}])
main._claude_client = Client([json.dumps({"problems": []})])
ps = run(main.watch_review(**H))["problems"]
out = run(main.watch_send(main.WatchSend(ids=[ps[0]["id"]]), **H))
assert out["sent"] == 0 and "AI_FIX_REPOS" in out["error"], out
# An allowed extra repository works, and its fixer may download pictures
start(pkg="zm.zexam", app="Zexam", repo="me/zexam-app")
screen(["Download [tap]"], [{"kind": "dead_tap", "detail": "Download"}])
main._claude_client = Client([json.dumps({"problems": []})])
ps = run(main.watch_review(**H))["problems"]
assert run(main.watch_send(main.WatchSend(ids=[ps[0]["id"]]), **H)) == {"sent": 1, "skipped": 0}
assert issues[-1]["path"] == "/repos/me/zexam-app/issues"
class Resp:
    def __init__(self, code, data): self.status_code = code; self._d = data
    def json(self): return self._d
class AsyncClient:
    def __init__(self, **k): pass
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    async def get(self, url, headers=None):
        return Resp(200, {"repositories": [{"full_name": "me/zexam-app"}]})
sys.modules["httpx"] = types.SimpleNamespace(AsyncClient=AsyncClient)
assert run(main._is_fixer("Bearer ghs_zexam")) is True
assert main.SERVER_VERSION >= "0.57"
print("test an app ok")
