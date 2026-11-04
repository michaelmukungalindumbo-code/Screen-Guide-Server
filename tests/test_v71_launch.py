import os, asyncio, json, time
os.environ.update(ADMIN_KEY="k", GITHUB_TOKEN="ghp_test")
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
def J(label, say): return json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})
SET = ["Settings [text]", "Search [tap]", "Network & internet [tap]", "Apps [tap]"]
def step(phone, tester=False, stuck=False):
    main._claude_client = Client([J("Apps", "Tap “Apps”.")])
    return run(main.next_step(main.Next(goal="Uninstall an app", labels=SET, stuck=stuck, device="Tecno phone, Android 10"),
                              x_app_token="tok", x_install_id=phone, x_tester="1" if tester else ""))
issues = []
async def fake_github(method, path, payload):
    issues.append((method, path, payload)); return {"number": 99}
main._github = fake_github
main.GITHUB_TOKEN = "ghp_test"

# The Launch Bay: a staged rule is on at once for test phones, and for everyone after 24 quiet hours
main.STAGED["test_rule"] = main.SERVER_VERSION
step("u0")                                                            # the first step: this version is now live
assert abs(main._launch["live"][main.SERVER_VERSION] - time.time()) < 60
assert main._staged("test_rule", True) and not main._staged("test_rule", False)
main._launch["live"][main.SERVER_VERSION] -= 25 * 3600
assert main._staged("test_rule", False)
try:
    main._staged("not_listed", True); assert False, "a staged rule must be listed in STAGED"
except KeyError:
    pass

# Paused at once, without an update: on Render (PAUSED_RULES), or from the report page; then resumed
main.PAUSED_RULES = {"test_rule"}
assert not main._staged("test_rule", True) and not main._staged("test_rule", False)
main.PAUSED_RULES = set()
run(main.admin_pause(key="k", rule="test_rule", on="1"))
assert not main._staged("test_rule", False) and main._launch["paused"]["test_rule"] == "Paused by the owner"
run(main.admin_pause(key="k", rule="test_rule", on="0"))
assert main._staged("test_rule", False)
run(main.admin_pause(key="k", rule="all", on="1")); assert not main._staged("test_rule", True)
run(main.admin_pause(key="k", rule="all", on="0")); assert main._staged("test_rule", True)
try:
    run(main.admin_pause(key="k", rule="nothing", on="1")); assert False
except main.HTTPException as e:
    assert e.status_code == 404
try:
    run(main.admin_pause(key="wrong", rule="test_rule", on="1")); assert False
except main.HTTPException:
    pass

# Help right after a rule changed the answer counts against it (through a real step: the rule marks itself)
orig = main._gallery_fix
def marked(*a, **k):
    main._fired("test_rule"); return orig(*a, **k)
main._gallery_fix = marked
step("u1"); step("u1", stuck=True)
seen = main._launch["seen"]["test_rule"]
assert seen["fired"] == 2 and seen["help_after"] == 1, seen
assert main._counts[main._today()]["rules"]["test_rule"] == {"fired": 2, "help_after": 1}
step("dev", tester=True); step("dev", tester=True, stuck=True)        # test phones never count
assert main._launch["seen"]["test_rule"]["fired"] == 2
main._gallery_fix = orig

# It pauses itself when Help right after it is far above normal, and says so on GitHub
main._launch["users"] = {"steps": 200, "help": 10}                   # 5% of all steps
main._launch["seen"]["test_rule"] = {"fired": 19, "help_after": 9}
run(main._maybe_pause("test_rule"))
assert "test_rule" not in main._launch["paused"]                      # not before 20 times
main._launch["seen"]["test_rule"] = {"fired": 20, "help_after": 4}   # 20%: under 30%
run(main._maybe_pause("test_rule"))
assert "test_rule" not in main._launch["paused"] and not issues
main._launch["seen"]["test_rule"] = {"fired": 20, "help_after": 10}  # 50%, ten times normal
run(main._maybe_pause("test_rule"))
assert main._launch["paused"]["test_rule"].startswith("Paused itself: people pressed Help right after it 10 times in 20 (50%)")
assert not main._staged("test_rule", False) and len(issues) == 1
assert issues[0][2]["title"] == "Launch Bay: rule “test_rule” paused itself" and "@claude" in issues[0][2]["body"], issues
assert "labels" not in issues[0][2]                                   # the fixer starts only when Michael asks
run(main._maybe_pause("test_rule")); assert len(issues) == 1          # once

# Kept across a restart (Upstash here), so the 24-hour clock does not start again
store = {}
async def fake_upstash(cmd):
    if cmd[0] == "GET":
        return store.get(cmd[1])
    store[cmd[1]] = cmd[2]; return "OK"
main._upstash = fake_upstash
main.UPSTASH_URL, main.UPSTASH_TOKEN = "https://example.upstash.io", "t"
run(main._launch_save())
live_before = main._launch["live"][main.SERVER_VERSION]
main._launch.update(live={}, paused={}, seen={}, users={"steps": 0, "help": 0}); main._launch_state["loaded"] = False
run(main._launch_load())
assert main._launch["live"][main.SERVER_VERSION] == live_before and "test_rule" in main._launch["paused"]

# The report page shows it, with Pause and Resume
page = main.launch_report_html("k")
assert "test_rule" in page and "Paused itself" in page and "/admin/pause?key=k&rule=test_rule&on=0" in page, page
assert main.STAGED.pop("test_rule")
assert "No staged rules right now" in main.launch_report_html("k")
print("launch bay ok")
