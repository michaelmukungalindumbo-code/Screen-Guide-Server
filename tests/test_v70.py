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
def step(i, label, say, labels, tapped=False, stuck=False, note=""):
    main._claude_client = Client([J(label, say)])
    return run(main.next_step(main.Next(goal="Upload a video in the YouTube app", labels=labels, tapped=tapped, stuck=stuck, note=note),
                              x_app_token="tok", x_install_id=i, x_tester="1"))
def kinds(i): return [p["kind"] for p in main._sessions[i]["problems"]]
def start(i): run(main.event(main.Event(event="start", guide="ai"), x_app_token="tok", x_install_id=i, x_tester="1"))

# #22, 4 Nov: in the photo picker the person scrolled through their videos. Each scroll made the phone check again, and
# each time the answer was "Tap Done" with the ring on Done, which was right. The watcher called it going round in circles.
DONE = "Tap “Done” to finish choosing your video."
def picker(k): return ["… [tap]", "Photos [text]", "… [tap]", "… [text]", "… [text]", "… [tap]", "Done [tap]"] + ["… [tap]"] * k
start("s1")
for k in (7, 9, 15):                                                  # the list grew as they scrolled: 7, 9, then 15 items
    step("s1", "Done", DONE, picker(k))
assert "loop" not in kinds("s1"), kinds("s1")

# Still going round in circles:
start("s2")                                                           # the same screen each time
for _ in range(3):
    step("s2", "Done", DONE, picker(7))
assert "loop" in kinds("s2"), kinds("s2")
start("s3")                                                           # they tapped Done, and got "Tap Done" back
step("s3", "Done", DONE, picker(7)); step("s3", "Done", DONE, picker(9), tapped=True); step("s3", "Done", DONE, picker(15))
assert "loop" in kinds("s3"), kinds("s3")
start("s4")                                                           # nothing pointed at
for k in (7, 9, 15):
    step("s4", None, "Choose your video, then tap the button to go on.", picker(k))
assert "loop" in kinds("s4"), kinds("s4")
start("s5")                                                           # they pressed Help in between
step("s5", "Done", DONE, picker(7)); step("s5", "Done", DONE, picker(9), stuck=True); step("s5", "Done", DONE, picker(15))
assert "loop" in kinds("s5"), kinds("s5")
assert main.SERVER_VERSION >= "0.70"
print("scrolling is not going round in circles")
