import os, asyncio, json, time
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
        issues.append({"number": 80 + len(issues), "title": payload["title"], "body": payload["body"],
                       "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}); return {"number": issues[-1]["number"]}
    return {}
main._github = fake_github
J = lambda label, say: json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})
def ev(phone, e, guide="ai"):
    run(main.event(main.Event(event=e, guide=guide), x_app_token="tok", x_install_id=phone, x_tester="1"))
def step(phone, out, labels, stuck=False, note="", history=(), image=""):
    main._claude_client = Client([out])
    return run(main.next_step(main.Next(goal="Scan a document with the Drive app", labels=labels, stuck=stuck, note=note,
                                        history=list(history), image=image, device="Infinix phone, Android 14"),
                              x_app_token="tok", x_install_id=phone, x_tester="1"))

# The guide from the 1 Nov recording (Google Drive, Infinix phone)
DRIVE = ["Search in Drive [tap]", "Scan document [tap]", "Create new [switch]", "Home [tap]", "Files [text]", "Chisomo CV.pdf [tap]"]
UPLOAD = ["Cancel [tap]", "Upload [tap]", "Scanned_20261101-1841.pdf [text]", "PDF [switch]", "JPEG [switch]", "My Drive [text]"]
ev("dev54", "start")
step("dev54", J("Scan document", "Tap “Scan Document” to start scanning your paper."), DRIVE)
# Help pressed while "Tap Scan Document" was shown: the problem belongs to step 1, not to the answer that followed
r = step("dev54", J("Create new", "Tap “Create new” to open the menu."), DRIVE, stuck=True, history=["Tap “Scan Document” to start scanning your paper."])
s = main._sessions["dev54"]
assert [(p["kind"], p["step"]) for p in s["problems"]] == [("not_working", 1)], s["problems"]
assert s["steps"][0]["help_after"] == "pressed Help" and s["steps"][1]["stuck"]
# The upload screen: the picture came back black, the AI said so, though the screen had words
step("dev54", J(None, "The screen is black, so the phone may be dark. Tap the power button once to wake the screen."), UPLOAD, image="iVBOR")
ev("dev54", "stop")
assert [(p["kind"], p["step"]) for p in s["problems"]] == [("not_working", 1), ("no_point", 3), ("stopped", 3)], s["problems"]

# Step numbers stay in titles (they were "step #"); long numbers still go
REV = json.dumps({"problems": [{"step": 3, "kind": "no_point", "title": "Said black screen on step 3",
                                "what": "Step 3 showed Upload and Cancel, but it said the screen was black. Call 0977 123 456.", "fix": "Trust the words."}]})
main._claude_client = Client([REV])
ps = run(main.watch_review(x_app_token="tok", x_install_id="dev54", x_tester="1"))["problems"]
titles = [p["title"] for p in ps]
assert titles == ["Step 1 did not work", "Said black screen on step 3", "Stopped at step 3"], titles
assert "0977" not in json.dumps(ps) and "#" in ps[1]["what"]
out = run(main.watch_send(main.WatchSend(ids=[ps[1]["id"]]), x_app_token="tok", x_install_id="dev54", x_tester="1"))
assert out == {"sent": 1, "skipped": 0}, out
t, b = issues[0]["title"], issues[0]["body"]
assert t.startswith("Guide problem: Said black screen on step 3"), t
# Every step's screen is in the issue, Help is shown where it was pressed, and the picture is mentioned
assert "1. said: Tap “Scan Document” to start scanning your paper." in b and "**then the person pressed Help: “pressed Help”**" in b, b
assert "(answer after Help)" in b and "with a screen picture" in b
assert "screen: Cancel [tap], Upload [tap], … [text], PDF [switch], JPEG [switch], My Drive [text]" in b, b
assert "screen: Search in Drive [tap], Scan document [tap], Create new [switch], Home [tap], Files [text], … [tap]" in b, b
assert "not the app's \"Step N of 5\"" in b
assert "Chisomo" not in b and "1841" not in b and "dev54" not in b, b          # still nothing personal

# Words seen on the screens of 3 different phones are button names, even if no list has them yet
for ph in ("w1", "w2"):
    main._learn_words(ph, ["Kuyamba [tap]"])
assert main._clean_label("Kuyamba [tap]") == "… [tap]"
main._learn_words("w3", ["Kuyamba [tap]"])
assert main._clean_label("Kuyamba [tap]") == "Kuyamba [tap]"
main._learn_words("w4", ["0977123456 [text]"]); main._learn_words("w5", ["0977123456 [text]"]); main._learn_words("w6", ["0977123456 [text]"])
assert main._clean_label("0977123456 [text]") == "… [text]"                 # numbers never become "known"

assert main._clean_text("Step 12: tap “Upload” in 0:09", ours=True) == "Step 12: tap “Upload” in 0:09"
assert main._clean_text("Call 0977 123 456 now", ours=True) == "Call # now"
assert "Never guess what happened on the phone between steps" in main.REVIEW_SYSTEM
assert main.SERVER_VERSION >= "0.54"
print("watcher evidence ok")
