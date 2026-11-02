import os, sys, types, asyncio, json, time, base64
os.environ.update(ADMIN_KEY="k", GITHUB_TOKEN="ghp_test", AI_WATCH_PER_DAY="3")
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
        return list(reversed(issues))
    if path.endswith("/issues"):
        issues.append({"number": 90 + len(issues), "title": payload["title"], "body": payload["body"],
                       "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}); return {"number": issues[-1]["number"]}
    return {}
main._github = fake_github
J = lambda label, say: json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})
def step(out, labels, **kw):
    main._claude_client = Client([out, json.dumps({"label": None, "say": "Tap the button at the top to save your scan.", "done": False, "x": None, "y": None, "look_for": None})])  # since server 0.61 a black-screen answer is asked again without the picture; this pretend AI then answers without naming the button
    return run(main.next_step(main.Next(goal="Scan a document with the Drive app", labels=labels, **kw), x_app_token="tok", x_install_id="dev55", x_tester="1"))

run(main.event(main.Event(event="start", guide="ai"), x_app_token="tok", x_install_id="dev55", x_tester="1"))
UP = ["Cancel [tap]", "Upload [tap]", "PDF [switch]"]
r1 = step(J("Upload", "Tap “Upload”."), UP)
r2 = step(J(None, "The screen is black. Tap the power button."), UP, image="iVBOR")
assert (r1["watch_step"], r2["watch_step"]) == (1, 2), (r1, r2)      # the phone matches its pictures to these numbers
main._claude_client = Client([J("Upload", "Tap Upload.")])
assert run(main.next_step(main.Next(goal="x", labels=UP), x_app_token="tok", x_install_id="plain55"))["watch_step"] == 0

main._claude_client = Client([json.dumps({"problems": []})])
ps = run(main.watch_review(x_app_token="tok", x_install_id="dev55", x_tester="1"))["problems"]
assert ps and ps[0]["step"] == 2, ps
JPG = base64.b64encode(b"\xff\xd8\xff" + b"picture" * 60).decode()
shots = [{"n": 1, "jpg": JPG}, {"n": 2, "jpg": JPG}, {"n": "3", "jpg": JPG}, {"n": 4, "jpg": "not base64 !!" * 20}, {"n": 5, "jpg": "A" * 500_000}]
out = run(main.watch_send(main.WatchSend(ids=[ps[0]["id"]], shots=shots), x_app_token="tok", x_install_id="dev55", x_tester="1"))
assert out == {"sent": 1, "skipped": 0}, out
b = issues[0]["body"]
assert "**Screen pictures:** 2 of this guide" in b and "never put on GitHub" in b, b
sid = b.split("<!-- shots: ")[1].split(" -->")[0]
assert JPG not in b and len(b) < 20000           # the pictures themselves never go to GitHub
assert [x["n"] for x in main._shots[sid]["shots"]] == [1, 2]

# Only the AI fixer's GitHub run may download them: GitHub is asked which repositories the token can reach
class Resp:
    def __init__(self, code, data): self.status_code = code; self._d = data
    def json(self): return self._d
asked = []
class AsyncClient:
    def __init__(self, **k): pass
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    async def get(self, url, headers=None):
        asked.append((url, headers["Authorization"]))
        tok = headers["Authorization"].split()[-1]
        repos = {"ghs_fixer": "michaelmukungalindumbo-code/Screen-Guide", "ghs_other": "someone/else"}
        return Resp(200, {"repositories": [{"full_name": repos[tok]}]}) if tok in repos else Resp(401, {})
sys.modules["httpx"] = types.SimpleNamespace(AsyncClient=AsyncClient)
def get(auth):
    try:
        return run(main.watch_shots(sid, authorization=auth))
    except main.HTTPException as e:
        return e.status_code
assert get("") == 401 and get("Bearer ghs_other") == 401 and get("Bearer wrong") == 401
got = get("Bearer ghs_fixer")
assert isinstance(got, dict) and [x["n"] for x in got["shots"]] == [1, 2] and got["shots"][0]["jpg"] == JPG
assert asked[-1][0] == "https://api.github.com/installation/repositories"
n = len(asked); get("Bearer ghs_fixer"); assert len(asked) == n       # remembered for a while
try:
    run(main.watch_shots("0123456789abcdef", authorization="Bearer ghs_fixer")); assert False
except main.HTTPException as e:
    assert e.status_code == 404

# Old pictures go after 48 hours
main._shots[sid]["t"] -= 49 * 3600
main._keep_shots("ffff", [])
assert sid not in main._shots
p = run(main.privacy()); assert "kept privately on the server for 48 hours" in str(getattr(p, "body", p))
assert main.SERVER_VERSION >= "0.55"
print("step pictures ok")
