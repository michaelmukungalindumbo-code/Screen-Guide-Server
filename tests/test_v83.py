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
def step(labels, label, say, i="dev83", tester=True, tapped=True):
    main._claude_client = Client([J(label, say)] * 3)
    return run(main.next_step(main.Next(goal=GOAL, labels=labels, tapped=tapped), x_app_token="tok", x_install_id=i,
                              x_tester="1" if tester else ""))

# 6 Nov, issue 41: YouTube's gallery said "Tap the video you want, or tap + if it is not here." The person tapped the
# "+", went through Android's photo picker, tapped Done, and came back to the same gallery, where they got the very same
# sentence again (and again after a second round, when their new video was there). Once they have been through the
# "+", it is not offered again on that gallery; a video that was not there before is the one to ring.
HOME = ["Home [selected]", "Shorts [tap]", "Create [tap]", "You [tap]"]
TOP = ["Video [selected]", "Short [tap]", "Live [tap]", "Post [tap]", "Close [tap]", "Upload from gallery [text]",
       "Videos [tap]", "Settings [tap]", "Select more media [tap]"]
GAL = TOP + ["0:06 [tap]", "0:13 [tap]", "0:21 [tap]", "0:09 [tap]", "0:14 [tap]"]
GAL_NEW = TOP + ["0:04 [tap]", "0:06 [tap]", "0:13 [tap]", "0:21 [tap]", "0:09 [tap]", "0:14 [tap]"]
PICKER = ["… [tap]", "Photos [text]", "… [tap]", "… [text]", "… [text]", "… [tap]", "Done [tap]", "… [tap]", "… [tap]",
          "… [tap]", "… [tap]", "… [text]", "… [tap]", "Photo taken on …, 5:56 AM [tap]"]
WANT = "Tap the video you want, or tap + if it is not here."
main._loops.clear()
r = step(HOME, "Create", "Tap “Create”.")
r = step(GAL, None, WANT)
assert r["say"] == WANT, r                                                  # first time: the "+" is offered
r = step(GAL, None, WANT)
assert r["say"] == WANT, r                                                  # same gallery, never left: unchanged
r = step(PICKER, "Done", "Tap the video you want to upload, or tap Done after you pick it.")
assert r["label"] == "Done", r
r = step(GAL, None, WANT)                                                   # the issue's step 5
assert r["say"] == "Tap the video you want." and r["label"] is None, r      # back from the "+": not offered again
r = step(PICKER, "Done", "Tap “Done” to finish picking your video.")
r = step(GAL_NEW, None, WANT)                                               # the issue's step 8: a new video, 0:04
assert r["label"] == "0:04" and r["say"] == "Tap your video.", r
r = step(GAL_NEW, None, WANT)
assert r["label"] == "0:04" and r["say"] == "Tap your video.", r

# Leaving the gallery another way (Close, then Create again) is not a trip through the "+": it is still offered
main._loops.clear()
step(HOME, "Create", "Tap “Create”.", i="dev83b")
step(GAL, None, WANT, i="dev83b")
step(HOME, "Create", "Tap “Create”.", i="dev83b")
r = step(GAL, None, WANT, i="dev83b")
assert r["say"] == WANT, r

# Staged (the Launch Bay): users' phones get it once 0.83 has been live for 24 hours; test phones at once
assert main.STAGED["after_plus"] == "0.83"
def round_trip(i, tester):
    main._loops.pop(i, None)
    step(GAL, None, WANT, i=i, tester=tester)
    step(PICKER, "Done", "Tap “Done”.", i=i, tester=tester)
    return step(GAL, None, WANT, i=i, tester=tester)
main._launch["live"][main.STAGED["after_plus"]] = main.time.time()
assert round_trip("user83", False)["say"] == WANT                          # not yet for users
main._launch["live"][main.STAGED["after_plus"]] -= 25 * 3600
assert round_trip("user83", False)["say"] == "Tap the video you want."
assert main._launch["seen"]["after_plus"]["fired"] >= 1
assert main.STATS["gallery_after_plus"] >= 1
assert main.SERVER_VERSION >= "0.83"
print("back from the + on a gallery: the + is not offered again, and a new video gets the ring")
