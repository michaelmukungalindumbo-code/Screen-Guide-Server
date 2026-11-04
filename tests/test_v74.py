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
def H(i): return dict(x_app_token="tok", x_install_id=i, x_tester="1")
def step(i, labels, label, say, goal="Upload a video in the YouTube app", stuck=False, note=""):
    main._claude_client = Client([J(label, say), J(label, say)])
    return run(main.next_step(main.Next(goal=goal, labels=labels, stuck=stuck, note=note), **H(i)))
def kinds(i): return [p["kind"] for p in main._sessions[i]["problems"]]
def start(i): run(main.event(main.Event(event="start", guide="ai"), **H(i)))

# 4 Nov: "Tap Exit editor" in the middle of a YouTube upload looked like a normal step to every watcher rule.
# Now a step that leaves what the person is making is "Sent backwards", when no way forward could replace it.
EDITOR = ["Exit editor [tap]", "Volume [tap]", "Add sound [tap]", "Text [tap]", "Effects [tap]"]
start("w1")
r = step("w1", EDITOR, "Exit editor", "Tap “Exit editor” to go back.")
assert r["label"] == "Exit editor" and kinds("w1") == ["backwards"], (r, kinds("w1"))
card = main._rule_card(main._sessions["w1"]["problems"][0])
assert card["title"] == "Sent backwards on step 1" and "“Exit …”" in card["what"], card   # unknown words stay hidden
# Not when a way forward replaced it (the 0.73 rule), when they asked for it in Help, or when nothing is being made
start("w2"); step("w2", EDITOR + ["Next [text]"], "Exit editor", "Tap “Exit editor”."); assert kinds("w2") == [], kinds("w2")
start("w3"); step("w3", EDITOR, "Exit editor", "Tap “Exit editor”.", stuck=True, note="I picked the wrong video")
assert "backwards" not in kinds("w3"), kinds("w3")
start("w4"); step("w4", ["Back [tap]", "Display [tap]"], "Back", "Tap “Back”.", goal="Turn on dark mode"); assert kinds("w4") == []

# The AI review checks every step against the goal (prompt version 54)
assert "Check every step against the goal" in main.REVIEW_SYSTEM and main.PROMPT_VERSION == "54"

# A guide the server forgot (it restarted): the phone is told, instead of seeing nothing at all
assert run(main.watch_review(**H("never-seen"))) == {"problems": [], "lost": True}
assert run(main.watch_review(x_app_token="tok", x_install_id="never-seen", x_tester="")) == {"problems": [], "lost": False}
assert main.SERVER_VERSION >= "0.74"
print("backwards noticed, review checks the goal, lost guides said")
