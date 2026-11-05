import os, asyncio, json
os.environ.update(ADMIN_KEY="k")
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
GOAL = "Install CapCut from the Play Store"
def step(labels, label, say, tester=True, i="dev78t", goal=GOAL):
    main._claude_client = Client([J(label, say)] * 3)
    return run(main.next_step(main.Next(goal=goal, labels=labels), x_app_token="tok", x_install_id=i, x_tester="1" if tester else ""))

# 5 Nov, the Play Store: "tap the search box" again and again (Help on steps 3, 4, 5 and 6), while the box was already
# open with the keyboard up. Before and after the tap the box read the same ("Search apps & games [tap]"). App 0.76 marks
# an open box [typing]; on it, the step is what to type, never another tap. (Screen words rebuilt from the watcher's
# report and the Play Store's search page: the report itself stayed on the phone.)
assert "type_in_open_box" in main.STAGED and "[typing]" in main.NEXT_SYSTEM
OPEN = ["Navigate up [tap]", "Search apps & games [typing]", "Voice search [tap]"]
assert main._plain("Search apps & games [typing]") == "Search apps & games"
r = step(OPEN, "Search apps & games", "Tap the search box at the top, then type CapCut.")
assert r["label"] == "Search apps & games" and r["say"] == "Type “CapCut”.", r          # not cut to "Tap the search box."
r = step(OPEN, None, "Tap the search bar at the top.")
assert r["label"] == "Search apps & games" and r["say"] == "Type “CapCut”.", r          # the name from the goal
r = step(OPEN, None, "Tap the search bar.", goal="Search for a video")
assert r["say"] == "Type what you are looking for.", r
r = step(["Back [tap]", "Message [typing]", "Send [tap]"], None, "Tap the message box.", goal="Send a message on WhatsApp")
assert r["label"] == "Message" and r["say"] == "Type what you want to write.", r                # not a search box
# Already typed: the box shows their words. The next step is the keyboard's search key, not another tap on the box
TYPED = ["Navigate up [tap]", "capcut [typing]", "Clear text [tap]", "capcut [tap]", "capcut template [tap]"]
r = step(TYPED, "capcut", "Tap the search box.")
assert r["label"] is None and r["say"] == "Tap the search key on your keyboard.", r
# Unchanged: a box that is not open yet, an answer that already says what to type, and a tap on a result
CLOSED = ["Search apps & games [tap]", "Games [tap]", "Apps [tap]", "Books [tap]"]
r = step(CLOSED, "Search apps & games", "Tap the search bar at the top.")
assert r["label"] == "Search apps & games" and r["say"] == "Tap the search bar.", r
r = step(OPEN, "Search apps & games", "Type CapCut.")
assert r["say"] == "Type CapCut.", r
r = step(TYPED, "capcut template", "Tap “capcut template”.")
assert r["label"] == "capcut template", r
# Never for money words
r = step(OPEN, None, "Tap the search bar.", goal="Install Airtel Money from the Play Store")
assert "Airtel" not in r["say"], r

# Staged: users' phones get it once 0.78 has been live for 24 hours; test phones at once
main._launch["live"][main.STAGED["type_in_open_box"]] = main.time.time()
r = step(OPEN, None, "Tap the search bar at the top.", tester=False, i="user78t")
assert r["say"] != "Type “CapCut”.", r
main._launch["live"][main.STAGED["type_in_open_box"]] -= 25 * 3600
r = step(OPEN, None, "Tap the search bar at the top.", tester=False, i="user78t")
assert r["say"] == "Type “CapCut”.", r
assert main._launch["seen"]["type_in_open_box"]["fired"] == 1
assert main.SERVER_VERSION >= "0.78" and main.PROMPT_VERSION == "55"
print("an open box gets what to type, not another tap")
