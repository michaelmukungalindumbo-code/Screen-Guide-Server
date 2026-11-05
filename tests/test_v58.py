import os, sys, types, asyncio, json, time
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
        return list(reversed(issues))
    if path.endswith("/issues"):
        issues.append({"path": path, "number": 200 + len(issues), "title": payload["title"], "body": payload["body"],
                       "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}); return {"number": issues[-1]["number"]}
    return {}
main._github = fake_github
H = dict(x_app_token="tok", x_install_id="dev58", x_tester="1")
def step(label, say, labels, note="", stuck=False, tapped=False, h=H):
    main._claude_client = Client([json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})])
    return run(main.next_step(main.Next(goal="Scan a document with the Drive app", labels=labels, note=note, stuck=stuck, tapped=tapped), **h))
def kinds(i="dev58"): return [p["kind"] for p in main._sessions[i]["problems"]]

# The recording from 2 Nov: Drive's list, "Tap Scan Document". The person tapped it, scanned, the file was saved
# ("1 upload complete"), and the guide said "Tap Scan Document" again. Before, the watcher noticed nothing.
DRIVE = ["My Drive [tap]", "Computers [tap]", "Scan Document [tap]", "Create new [tap]", "… [tap]"]
SCAN = "Tap “Scan Document” to start scanning your paper."
run(main.event(main.Event(event="start", guide="ai"), **H))
step("Scan Document", SCAN, DRIVE)
r = step("Scan Document", SCAN, DRIVE + ["1 upload complete [text]"], tapped=True)
assert kinds() == ["repeat"] and r["watch"] == 1, kinds()
card = main._rule_card(main._sessions["dev58"]["problems"][0])
assert card["title"] == "Step 2 repeated step 1" and "“Tap “Scan Document” to start scanning your paper.” again" in card["what"], card
main.PAUSED_RULES = {"loop_breaker"}                             # 0.78: the loop breaker steps in here (just below)
step("Scan Document", SCAN, DRIVE, tapped=True)
assert kinds() == ["repeat", "loop"], kinds()                    # three in a row is the old "loop"; no second "repeat"
main.PAUSED_RULES = set()
# 0.78, the loop breaker: tapped twice and nothing changed, so it is not said a third time; the watcher says why
HL = dict(H, x_install_id="dev58l")
run(main.event(main.Event(event="start", guide="ai"), **HL))
step("Scan Document", SCAN, DRIVE, h=HL)
step("Scan Document", SCAN, DRIVE + ["1 upload complete [text]"], tapped=True, h=HL)
r = step("Scan Document", SCAN, DRIVE, tapped=True, h=HL)
assert kinds("dev58l") == ["repeat", "circles"] and r["say"] == main._NOT_SURE, (kinds("dev58l"), r)

# It also counts when the instruction comes back after other steps (the scanner's own screens in between)
H2 = dict(H, x_install_id="dev58b")
run(main.event(main.Event(event="start", guide="ai"), **H2))
step("Scan Document", SCAN, DRIVE, h=H2)
step("Done", "Tap “Done” to save the scan.", ["Done [tap]", "Retake [tap]"], tapped=True, h=H2)
step("Scan Document", SCAN, DRIVE, h=H2)
assert kinds("dev58b") == ["repeat"] and main._sessions["dev58b"]["problems"][0]["n0"] == 1

# Not a problem: the same words twice when nothing was tapped (the screen just moved), after Help, or after scrolling
H3 = dict(H, x_install_id="dev58c")
run(main.event(main.Event(event="start", guide="ai"), **H3))
step("Scan Document", SCAN, DRIVE, h=H3)
step("Scan Document", SCAN, DRIVE, h=H3)
step("Done", "Tap “Done” to save the scan.", ["Done [tap]"], h=H3)
step("Scan Document", SCAN, DRIVE, note="They scrolled the list.", h=H3)
step("Scan Document", SCAN, DRIVE, note="Where is it?", stuck=True, h=H3)
assert "repeat" not in kinds("dev58c"), kinds("dev58c")

# A phone that is not a developer's: nothing is kept
step("Scan Document", SCAN, DRIVE, h=dict(H, x_install_id="user58", x_tester=""))
step("Scan Document", SCAN, DRIVE, tapped=True, h=dict(H, x_install_id="user58", x_tester=""))
assert "user58" not in main._sessions

# "Test an app" with a guide inside it: Stop while the guide is still guiding counts; Stop after only screens does not
assert run(main.watch_test_start(main.WatchTest(pkg="zm.screenguide", app="ScreenGuide", repo="michaelmukungalindumbo-code/Screen-Guide"), **H))["ok"]
run(main.watch_screen(main.WatchScreen(labels=["Ask anything [text]", "Speak [tap]"]), **H))
step("Scan Document", SCAN, DRIVE)
run(main.event(main.Event(event="stop", guide="ai"), **H))
s = main._sessions["dev58"]
assert kinds() == ["stopped"] and s["problems"][0]["step"] == 2, s["problems"]
H4 = dict(H, x_install_id="dev58d")
run(main.watch_test_start(main.WatchTest(pkg="zm.screenguide", app="ScreenGuide", repo="michaelmukungalindumbo-code/Screen-Guide"), **H4))
run(main.watch_screen(main.WatchScreen(labels=["Ask anything [text]"], found=[{"kind": "dead_tap", "detail": "Speak"}]), **H4))
run(main.event(main.Event(event="stop", guide="test"), **H4))
assert kinds("dev58d") == ["dead_tap"]

# Past results: the review comes with a signed copy, and Allow still works days later, after the server restarted
main._claude_client = Client([json.dumps({"problems": []})])
r = run(main.watch_review(**H))
assert r["title"] == "Test of ScreenGuide: Scan a document with the Drive app" and r["problems"][0]["title"] == "Stopped at step 2", r
saved = r["saved"]
assert set(saved) == {"data", "sig"} and "dev58" not in saved["data"]
main._sessions.clear()
out = run(main.watch_send(main.WatchSend(ids=[r["problems"][0]["id"]], saved=saved), **H))
assert out == {"sent": 1, "skipped": 0}, out
assert issues[-1]["title"] == "App problem: Stopped at step 2 (ScreenGuide)" and issues[-1]["path"].startswith("/repos/michaelmukungalindumbo-code/Screen-Guide/")
assert run(main.watch_send(main.WatchSend(ids=[r["problems"][0]["id"]], saved=saved), **H)) == {"sent": 0, "skipped": 1}   # never twice
# Only what this server made, only from the phone it was made for, and not when too old
bad = dict(saved, data=saved["data"].replace("ScreenGuide", "Other"))
assert "older than" in run(main.watch_send(main.WatchSend(ids=["x"], saved=bad), **H))["error"]
assert "older than" in run(main.watch_send(main.WatchSend(ids=["x"], saved=saved), **dict(H, x_install_id="someone")))["error"]
d = json.loads(saved["data"]); d["at"] -= 31 * 86400
old = {"data": json.dumps(d, ensure_ascii=False, separators=(",", ":"))}
old["sig"] = main.hmac.new(main._seal_key(), old["data"].encode(), main.hashlib.sha256).hexdigest()
assert "older than" in run(main.watch_send(main.WatchSend(ids=["x"], saved=old), **H))["error"]
assert run(main.watch_send(main.WatchSend(ids=["x"], saved=saved), **dict(H, x_tester=""))) == {"sent": 0, "skipped": 0}
# A guide that went well: nothing to show, nothing to keep
H5 = dict(H, x_install_id="dev58e")
run(main.event(main.Event(event="start", guide="ai"), **H5))
step("Scan Document", SCAN, DRIVE, h=H5)
main._claude_client = Client([json.dumps({"problems": []})])
assert run(main.watch_review(**H5)) == {"problems": []}
assert main.SERVER_VERSION >= "0.58"
print("v58 ok")
