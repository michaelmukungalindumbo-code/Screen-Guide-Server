import os, asyncio, json, time, base64
os.environ.update(ADMIN_KEY="k", GITHUB_TOKEN="ghp_test", AI_WATCH_PER_DAY="3", AI_CHANGE_PER_DAY="5")
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
        issues.append({"number": 100 + len(issues), "title": payload["title"], "body": payload["body"],
                       "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}); return {"number": issues[-1]["number"]}
    return {}
main._github = fake_github
J = lambda label, say: json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})
H = dict(x_app_token="tok", x_install_id="dev56", x_tester="1")
def step(out, labels):
    main._claude_client = Client([out])
    return run(main.next_step(main.Next(goal="Upload a video in the YouTube app", labels=labels), **H))
def change(text, x=-1.0, y=-1.0, labels=(), **h):
    return run(main.watch_change(main.WatchChange(text=text, x=x, y=y, labels=list(labels)), **(h or H)))

run(main.event(main.Event(event="start", guide="ai"), **H))
YT = ["Create [tap]", "Upload a video [tap]", "Chisomo's channel [text]"]
step(J("Create", "Tap “Create”."), YT)
step(J("Upload a video", "Tap “Upload a video”."), YT)

# Not a developer phone, or nothing said: nothing kept
assert change("Make it bigger", x_app_token="tok", x_install_id="n56", x_tester="") == {"ok": False}
assert change("  ") == {"ok": False}
# The developer points at a spot and says what should change
r = change("Make this ring thicker so it is easier to see. Call 0977 123 456", x=0.42, y=0.81, labels=YT)
assert r == {"ok": True, "pic": 101, "count": 1}, r
r = change("Say the step number out loud before each instruction")
assert r == {"ok": True, "pic": 102, "count": 2}, r
s = main._sessions["dev56"]
assert s["changes"][0]["step"] == 2 and s["changes"][0]["x"] == 0.42 and "0977" not in s["changes"][0]["text"]
assert s["changes"][0]["screen"] == ["Create [tap]", "… [tap]", "… [text]"], s["changes"][0]["screen"]

# After the guide: problems, the AI's ideas, and the changes, each with its kind
ev = run(main.event(main.Event(event="done", guide="ai"), **H))
REV = json.dumps({"problems": [{"step": 2, "kind": "idea", "title": "Say Upload, not Upload a video", "what": "Long button names are hard to read.", "fix": "Use the shortest words on the button."},
                               {"step": 1, "kind": "idea", "title": "Two", "what": "w", "fix": "f"}, {"step": 1, "kind": "idea", "title": "Three", "what": "w", "fix": "f"}]})
main._claude_client = Client([REV])
ps = run(main.watch_review(**H))["problems"]
assert [(p["kind"], p["title"][:22]) for p in ps] == [("idea", "Say Upload, not Upload"), ("idea", "Two"), ("change", "Change: Make this ring"),
                                                    ("change", "Change: Say the step n")], ps
assert ps[2]["what"].startswith("You asked: “Make this ring thicker") and "(at the spot you marked)" in ps[2]["what"]
assert run(main.watch_review(**H))["problems"] == ps          # same list again, no second AI call

# Allow: changes and ideas become their own issues, with the picture of that moment
JPG = base64.b64encode(b"\xff\xd8\xff" + b"pic" * 80).decode()
out = run(main.watch_send(main.WatchSend(ids=[p["id"] for p in ps], shots=[{"n": 2, "jpg": JPG}, {"n": 101, "jpg": JPG}]), **H))
assert out == {"sent": 4, "skipped": 0}, out
titles = [i["title"] for i in issues]
assert titles[0] == "Idea: Say Upload, not Upload a video" and titles[2].startswith("Change request: Make this ring thicker"), titles
b = issues[2]["body"]
assert "this is a change request, not a bug" in b and "reply here with a short plan" in b and "@claude" in b
assert "`media/step101.jpg` is the screen when they asked, with a red circle where they pointed" in b and "42% across, 81% down" in b
assert "Create [tap], … [tap], … [text]" in b and "<!-- change-id: " in b and "<!-- shots: " in b
assert "Chisomo" not in b and "0977" not in b and "dev56" not in b, b
assert "they did not point at a spot" in issues[3]["body"] and "media/step102" not in issues[3]["body"]
assert "this is an idea, not a bug" in issues[0]["body"]

# The same change from a new guide is not sent twice; and changes have their own daily limit
run(main.event(main.Event(event="start", guide="ai"), **H))
step(J("Create", "Tap “Create”."), YT)
change("Say the step number out loud before each instruction")
change("Make the Stop button red")
main._claude_client = Client([json.dumps({"problems": []})])
ps2 = run(main.watch_review(**H))["problems"]
assert [p["kind"] for p in ps2] == ["change", "change"], ps2
out = run(main.watch_send(main.WatchSend(ids=[p["id"] for p in ps2]), **H))
assert out == {"sent": 1, "skipped": 1}, out                  # the first was sent before
assert issues[-1]["title"] == "Change request: Make the Stop button red"
assert main.SERVER_VERSION >= "0.56"
print("change requests ok")
