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
GOAL = "Upload a video in the YouTube app"
def step(labels, label, say, tester=True, i="dev77"):
    main._claude_client = Client([J(label, say), J(label, say)])
    return run(main.next_step(main.Next(goal=GOAL, labels=labels, history=["Tap “Done” to finish picking."]),
                              x_app_token="tok", x_install_id=i, x_tester="1" if tester else ""))

# 4 Nov, 15:39: the person added their video with YouTube's "+" (Select more media) and tapped Done in the picker.
# Back on YouTube's gallery the AI said "Tap your video, or tap Select more media if it is not here", but put the ring on
# the "+", which sends them straight back to the picker. The "+" was only the second choice: the ring follows the first.
TOP = ["Video [selected]", "Short [tap]", "Live [tap]", "Post [tap]", "Close [tap]", "Upload from gallery [text]",
       "Videos [tap]", "Settings [tap]", "Select more media [tap]"]
GAL = TOP + ["0:06 [tap]", "0:13 [tap]", "0:21 [tap]", "0:09 [tap]", "0:14 [tap]"]
SAID = "Tap your video, or tap Select more media if it is not here."
assert "video_before_plus" in main.STAGED
r = step(GAL, "Select more media", SAID)
assert r["label"] is None and r["say"] == "Tap the video you want, or tap + if it is not here.", r   # several: they choose
r = step(TOP + ["0:06 [tap]"], "Select more media", SAID)
assert r["label"] == "0:06" and r["say"] == "Tap your video, or tap + if it is not here.", r         # one: ring it
r = step(TOP, "Select more media", SAID)
assert r["label"] == "Select more media" and r["say"] == "Tap + to choose your video.", r            # none: the + it is

# When the "+" is what the AI means first, it stays (their video is not there, or they asked for more)
r = step(GAL, "Select more media", "Tap “Select more media” to add more videos.")
assert r["label"] == "Select more media", r
r = step(GAL, "Select more media", "Tap Select more media, or tap your video if you can see it.")
assert r["label"] == "Select more media", r
main._claude_client = Client([J("Select more media", SAID)] * 3)        # they said in Help why: the AI's choice stands
r = run(main.next_step(main.Next(goal=GOAL, labels=GAL, stuck=True, note="my video is not there"),
                       x_app_token="tok", x_install_id="dev77h", x_tester="1"))
assert r["label"] == "Select more media", r

# Staged (the Launch Bay): users' phones get it once 0.77 has been live for 24 hours; test phones at once
main._launch["live"][main.STAGED["video_before_plus"]] = main.time.time()
r = step(GAL, "Select more media", SAID, tester=False, i="user77")
assert r["label"] == "Select more media", r                            # not yet for users
main._launch["live"][main.STAGED["video_before_plus"]] -= 25 * 3600
r = step(GAL, "Select more media", SAID, tester=False, i="user77")
assert r["label"] is None, r
assert main._launch["seen"]["video_before_plus"]["fired"] == 1        # counted for the automatic pause
assert main.SERVER_VERSION >= "0.77"
print("the ring follows the video, not the + named as a second choice")
