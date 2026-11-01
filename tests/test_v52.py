import os, asyncio, json, time
os.environ.update(ADMIN_KEY="k", GITHUB_TOKEN="ghp_test", AI_WATCH_PER_DAY="3")
import main
run = asyncio.run
class Msgs:
    def __init__(self, out): self.out = list(out); self.calls = 0
    async def create(self, **kw):
        self.calls += 1
        o = self.out.pop(0)
        if isinstance(o, Exception): raise o
        class U: input_tokens = 900; output_tokens = 40
        class B: type = "text"; text = o
        class M: content = [B()]; usage = U(); stop_reason = "end_turn"
        return M()
class Client:
    def __init__(self, out): self.messages = Msgs(out)
issues, posts = [], []
async def fake_github(method, path, payload):
    if method == "GET":
        return list(reversed(issues))
    posts.append(path)
    if path.endswith("/issues"):
        n = 60 + len(issues); issues.append({"number": n, "title": payload["title"], "body": payload["body"],
                                             "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}); return {"number": n}
    return {}
main._github = fake_github
J = lambda label, say: json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})

def call(coro):
    return run(coro)
def ev(phone, e, guide="ai", tester=True):
    call(main.event(main.Event(event=e, guide=guide), x_app_token="tok", x_install_id=phone, x_tester="1" if tester else ""))
def step(phone, outs, labels, note="", stuck=False, history=(), tester=True, goal="Turn on Wi-Fi for Mary"):
    main._claude_client = Client(outs if isinstance(outs, list) else [outs])
    return call(main.next_step(main.Next(goal=goal, labels=labels, note=note, stuck=stuck, history=list(history), device="TECNO phone, Android 13"),
                               x_app_token="tok", x_install_id=phone, x_tester="1" if tester else ""))
def review(phone, outs=(), tester=True):
    main._claude_client = Client(list(outs))
    return call(main.watch_review(x_app_token="tok", x_install_id=phone, x_tester="1" if tester else ""))["problems"]
def send(phone, ids):
    return call(main.watch_send(main.WatchSend(ids=ids), x_app_token="tok", x_install_id=phone, x_tester="1"))

WIFI = ["Wi-Fi [tap]", "Bluetooth [switch]", "Mum [tap]", "0977123456 [text]", "Mobile data [tap]"]

# A normal phone (not a developer phone): nothing is watched
ev("n1", "start", tester=False)
r = step("n1", J("Wi-Fi", "Tap Wi-Fi."), WIFI, note="I don't understand", stuck=True, history=["Tap Wi-Fi."], tester=False)
assert r["watch"] == 0 and review("n1", tester=False) == [] and "n1" not in main._sessions

# A developer phone: every step is watched, and the count goes up when a problem is seen (the phone flashes red)
ev("devphone1", "start")
assert step("devphone1", J("Wi-Fi", "Tap Wi-Fi."), WIFI)["watch"] == 0
assert step("devphone1", J("Wi-Fi", "Tap Wi-Fi."), WIFI, note="I don't understand", stuck=True, history=["Tap Wi-Fi."])["watch"] == 1   # Help repeated
assert step("devphone1", J(None, "Tap the switch."), WIFI, history=["Tap Wi-Fi."])["watch"] == 2     # told to tap, nothing to point at
ev("devphone1", "done")
kinds = [(p["kind"], p["step"]) for p in main._sessions["devphone1"]["problems"]]
assert kinds == [("help_repeated", 2), ("no_point", 3)], kinds

# After the guide: the AI review explains them and adds what the rules missed (cleaned: no names)
REV = json.dumps({"problems": [
    {"step": 2, "kind": "help_repeated", "title": "Help said the same thing", "what": "They said they did not understand and heard the same words.", "fix": "Explain where Wi-Fi is on the screen."},
    {"step": 1, "kind": "review", "title": "Goal names a person", "what": "The goal mentions Mary, which does not matter here.", "fix": "Ignore names in the goal."}]})
ps = review("devphone1", [REV])
assert [p["title"] for p in ps] == ["Help said the same thing", "Could not point on step 3", "Goal names a person"], ps
assert all(p["id"] and p["what"] and p["fix"] for p in ps)
assert "Mary" not in json.dumps(ps)
assert review("devphone1") == ps            # asked again: the same answer, no second AI call

# Don't allow: nothing is sent. Allow: each chosen problem becomes one ai-fix issue
assert issues == []
out = send("devphone1", [ps[0]["id"], ps[2]["id"]])
assert out == {"sent": 2, "skipped": 0}, out
assert [p for p in posts if p.endswith("/labels")] == ["/repos/michaelmukungalindumbo-code/Screen-Guide/issues/60/labels",
                                                       "/repos/michaelmukungalindumbo-code/Screen-Guide/issues/61/labels"]
b = issues[0]["body"]
assert issues[0]["title"].startswith("Guide problem: Help said the same thing"), issues[0]["title"]
assert "tapped **Allow**" in b and "**→** 2." in b and "Explain where Wi-Fi is" in b and '"… [tap]"' in b and "<!-- watch-id: " in b
assert "Mum" not in b and "0977" not in b and "Mary" not in b and "devphone" not in b, b       # nothing personal reaches GitHub
assert send("devphone1", [ps[0]["id"]]) == {"sent": 0, "skipped": 0}      # already sent

# The same problem from another phone: not sent twice (GitHub is the memory)
ev("d2", "start")
step("d2", J("Wi-Fi", "Tap Wi-Fi."), WIFI)
step("d2", J("Wi-Fi", "Tap Wi-Fi."), WIFI, note="I don't understand", stuck=True, history=["Tap Wi-Fi."])
ps2 = review("d2", [json.dumps({"problems": []})])
assert [p["title"] for p in ps2] == ["Help repeated itself"], ps2   # the rule's own words when the AI adds nothing
assert send("d2", [ps2[0]["id"]]) == {"sent": 0, "skipped": 1}

# Stopped, left idle, going round in circles, slow, and an unreadable AI answer
SET = ["Settings [text]", "Search [tap]", "Network & internet [tap]", "Apps [tap]"]
ev("d3", "start")
for _ in range(3):
    step("d3", J("Apps", "Tap Apps."), SET, goal="Uninstall an app")
step("d3", ["oops", "oops", "oops"], SET, goal="Uninstall an app")
ev("d3", "stop", guide="ai")
kinds = [p["kind"] for p in main._sessions["d3"]["problems"]]
assert kinds == ["loop", "ai_empty", "stopped"], kinds
ev("d4", "start"); step("d4", J("Apps", "Tap Apps."), SET); ev("d4", "stop", guide="idle_ai")
assert [p["kind"] for p in main._sessions["d4"]["problems"]] == ["idle"]
main._watch_start("d5", "ai")
assert main._watch_step("d5", True, "Open YouTube", SET, [], "", False, "Apps", "Tap Apps.", None, None, False, False, False, 12.4, False, "en", "", "") == 1
assert main._sessions["d5"]["problems"][0]["kind"] == "slow"

# The AI review fails: the rules' own words are still shown
ps3 = review("d3", [RuntimeError("down"), RuntimeError("down"), RuntimeError("down")])
assert [p["title"] for p in ps3][:2] == ["Same instruction three times", "No usable answer on step 4"], ps3

# The daily limit (3): one more goes, then the rest wait for tomorrow
out = send("d3", [p["id"] for p in ps3])
assert out == {"sent": 1, "skipped": 2}, out

# Cleaning keeps app and button names, removes people
assert main._clean_text("Send a photo to Mary on WhatsApp") == "Send a photo to … on WhatsApp"
assert main._clean_text('Tap "Mum", then tap “Upload from gallery”.') == "Tap “…”, then tap “Upload from gallery”."
assert main._clean_label("0:09 [text]") == "0:09 [text]" and main._clean_label("Chisomo Phiri [tap]") == "… [tap]"
p = run(main.privacy()); assert "only if you tap Allow" in str(getattr(p, "body", p))
assert main.SERVER_VERSION >= "0.52"
print("watcher: every guide, review, Allow ok")
