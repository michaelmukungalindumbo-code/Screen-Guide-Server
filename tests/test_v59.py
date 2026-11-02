import os, sys, asyncio, json, time
os.environ.update(ADMIN_KEY="k", GITHUB_TOKEN="ghp_test", AI_WATCH_PER_DAY="3", AI_CHANGE_PER_DAY="5")
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
issues = []
async def fake_github(method, path, payload):
    if method == "GET":
        return list(reversed(issues))
    if path.endswith("/issues"):
        issues.append({"path": path, "number": 300 + len(issues), "title": payload["title"], "body": payload["body"],
                       "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}); return {"number": issues[-1]["number"]}
    return {}
main._github = fake_github
H = dict(x_app_token="tok", x_install_id="dev59", x_tester="1")
def step(label, say, labels, note="", stuck=False, tapped=False, image=""):
    main._claude_client = Client([json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None}), json.dumps({"label": None, "say": "Tap the button at the top to save your scan.", "done": False, "x": None, "y": None, "look_for": None}), json.dumps({"label": None, "say": "Tap the button at the top to save your scan.", "done": False, "x": None, "y": None, "look_for": None})])  # since server 0.61 a black-screen answer is asked again without the picture; this pretend AI then answers without naming the button
    return run(main.next_step(main.Next(goal="How do I scan a document", labels=labels, note=note, stuck=stuck, tapped=tapped, image=image), **H))
def kinds(): return [(p["kind"], p["step"]) for p in main._sessions["dev59"]["problems"]]

# The test recorded on 2 Nov: Drive's list, Google's scanner (no words ScreenGuide can read), Help, the Upload screen
# (the picture came back black, the words did not), back to Drive's list after the upload, then Stop.
DRIVE = ["My Drive [tap]", "Computers [tap]", "Scan Document [tap]", "Create new [tap]", "… [tap]"]
UPLOAD = ["Cancel [tap]", "Upload [tap]", "PDF [switch]", "JPEG [switch]", "My Drive [text]"]
SCAN = "Tap “Scan Document” to scan your paper."
assert run(main.watch_test_start(main.WatchTest(pkg="zm.screenguide", app="ScreenGuide", repo="michaelmukungalindumbo-code/Screen-Guide"), **H))["ok"]
step("Scan Document", SCAN, DRIVE)                                                                          # 1
step(None, "Hold the camera still over the paper, then tap the big round button in the bottom middle to take the photo.", [], image="iVBOR")   # 2 (2 Nov wording)
step(None, "The page is still being checked, so wait a moment. When the scan looks clear, tap Next.", [], note="Help", stuck=True, image="iVBOR")  # 3
step(None, "The screen is black with only ScreenGuide's bar at the top. Wait a moment, then tap the Stop button.", UPLOAD, image="iVBOR")  # 4
step("Scan Document", SCAN, DRIVE)                                                                          # 5: sent back to the start
run(main.event(main.Event(event="stop", guide="ai"), **H))
assert kinds() == [("no_point", 2), ("help", 2), ("no_point", 3), ("no_point", 4), ("repeat", 5), ("stopped", 5)], kinds()

# 1. The phone says which step pictures it has; the server asks only for those that help (problem steps and the step before)
r = run(main.watch_review(main.WatchReview(have=[1, 2, 3, 4, 5, 77]), **H))
assert r == {"problems": [], "want": [1, 2, 3, 4, 5]}, r
assert main._sessions["dev59"]["review"] is None
# 2. With them, the AI review looks at the pictures. It tried to turn the repeated step into another problem, and to call
#    the Next button missing: the rule's facts stay, and what it saw in the pictures is added.
REV = json.dumps({"problems": [
    {"step": 5, "kind": "repeat", "title": "Unclear next step after upload", "what": "The scan was already uploaded (the picture shows Uploading 1 item), and the guide sent them back to Scan Document.", "fix": "After Upload, notice the new file and finish."},
    {"step": 3, "kind": "no_point", "title": "Next was on screen", "what": "The picture shows a blue Next button at the bottom right, but ScreenGuide could not read the scanner's words.", "fix": "Point at Next from the picture (x, y)."},
    {"step": 4, "kind": "no_point", "title": "Upload screen was not black", "what": "The words show Upload and Cancel; only the picture was black.", "fix": "Trust the words when the picture is black."},
    {"step": 2, "kind": "review", "title": "Shutter not pointed at", "what": "The round shutter button was on screen.", "fix": "Point at it, or say the scanner takes the picture by itself."},
    {"step": 3, "kind": "review", "title": "Capture not noticed", "what": "The page was already captured.", "fix": "Notice the Next screen."},
    {"step": 1, "kind": "review", "title": "Third extra", "what": "x", "fix": "y"},
    {"step": 1, "kind": "review", "title": "Fourth extra", "what": "x", "fix": "y"},
    {"step": 5, "kind": "idea", "title": "Say Done at the end", "what": "x", "fix": "y"}]})
main._claude_client = Client([REV])
PIC = "A" * 300
r = run(main.watch_review(main.WatchReview(have=[1, 2, 3, 4, 5], shots=[{"n": n, "jpg": PIC} for n in (1, 2, 3, 4, 5)] + [{"n": 6, "jpg": "bad!"}]), **H))
call = main._claude_client.messages.calls[0]
content = call["messages"][0]["content"]
assert [c["type"] for c in content] == ["image"] * 5 + ["text"], [c["type"] for c in content]
assert "<pictures>step 1, step 2, step 3, step 4, step 5</pictures>" in content[-1]["text"]
assert "Trust them over the screen words" in call["system"] and "Never turn it into a different problem" in call["system"]
assert main._shots == {} or all(v["t"] < 0 for v in main._shots.values())     # used for the review only, not kept
ps = r["problems"]
titles = [p["title"] for p in ps]
assert titles == ["Could not point on step 2", "Needed Help on step 2", "Could not point on step 3", "Could not point on step 4",
                  "Step 5 repeated step 1", "Stopped at step 5", "Shutter not pointed at", "Capture not noticed", "Third extra",
                  "Say Done at the end"], titles                # every rule problem (the old limit of 6 hid Stop), 3 extras, 1 idea
rep = ps[4]
assert rep["what"].startswith("Step 5 said “Tap “Scan Document” to scan your paper.” again") and "the guide sent them back to Scan Document." in rep["what"], rep
assert ps[2]["what"].startswith("ScreenGuide told them to tap something on step 3") and "blue Next button" in ps[2]["what"]
assert r["limits"] == {"problems": 3, "changes": 5} and r["saved"]["sig"]
assert run(main.watch_review(**H))["problems"] == ps           # asked again: same list, no second AI call

# 3. Allow with tick boxes: only the chosen ones. The phone hears which are done and which wait for tomorrow (3 a day)
pick = [ps[i]["id"] for i in (2, 3, 4, 5, 9)]
out = run(main.watch_send(main.WatchSend(ids=pick, report=True), **H))
assert out == {"sent": 4, "skipped": 1, "done": pick[:3] + [pick[4]], "wait": [pick[3]]}, out
assert [i["title"] for i in issues] == ["App problem: Could not point on step 3 (ScreenGuide)", "App problem: Could not point on step 4 (ScreenGuide)",
                                       "App problem: Step 5 repeated step 1 (ScreenGuide)", "Idea: Say Done at the end"], [i["title"] for i in issues]
out = run(main.watch_send(main.WatchSend(ids=pick, report=True), **H))
assert out["done"] == pick[:3] + [pick[4]] and out["wait"] == [pick[3]], out     # sent before: done; today's limit: waits
assert run(main.watch_send(main.WatchSend(ids=pick), **H)).keys() == {"sent", "skipped"}   # old phones: the same reply as before

# A phone that does not send pictures (v0.62 and older) gets the review at once, as before
H2 = dict(H, x_install_id="dev59b")
run(main.event(main.Event(event="start", guide="ai"), **H2))
main._claude_client = Client([json.dumps({"label": "Scan Document", "say": SCAN, "done": False, "x": None, "y": None, "look_for": None})])
run(main.next_step(main.Next(goal="Scan", labels=DRIVE, note="Where?", stuck=True), **H2))
main._claude_client = Client([json.dumps({"problems": []})])
r = run(main.watch_review(**H2))
assert [p["title"] for p in r["problems"]] == ["Needed Help on step 1"] and "want" not in r
# No AI today (limit or budget): no pictures are asked for, the rules' own words are shown
H3 = dict(H, x_install_id="dev59c")
run(main.event(main.Event(event="start", guide="ai"), **H3))
main._claude_client = Client([json.dumps({"label": "Scan Document", "say": SCAN, "done": False, "x": None, "y": None, "look_for": None})])
run(main.next_step(main.Next(goal="Scan", labels=DRIVE, note="Where?", stuck=True), **H3))
main._review_day["dev59c" + main._today()] = 40
r = run(main.watch_review(main.WatchReview(have=[1]), **H3))
assert [p["title"] for p in r["problems"]] == ["Needed Help on step 1"] and "want" not in r, r
assert main.SERVER_VERSION >= "0.59" and int(main.PROMPT_VERSION) >= 48
print("v59 ok")
