import os, asyncio, json
os.environ.update(ADMIN_KEY="k")
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
def J(label, say, done=False): return json.dumps({"label": label, "say": say, "done": done, "x": None, "y": None, "look_for": None})
H = dict(x_app_token="tok", x_install_id="dev66", x_tester="1")
GOAL = "Upload a video in the YouTube app"
def step(outs, labels, h=H, **kw):
    main._claude_client = Client(outs)
    r = run(main.next_step(main.Next(goal=GOAL, labels=labels, **kw), **h))
    return r, main._claude_client.messages.calls
run(main.event(main.Event(event="start", guide="ai"), **H))

# 3 Nov, YouTube: after "Upload Short" the channel page shows the upload under way, and the guide pointed at + (Create),
# which starts a new upload. The person's part is done.
CHANNEL = ["Analytics [tap]", "Edit channel [tap]", "Shorts [selected]", "Posts [tap]", "Latest [tap]", "Private [tap]",
           "Unlisted [tap]", "Sending file · 8% [text]", "Home [tap]", "Shorts [tap]", "Create [tap]", "Subscriptions [tap]", "You [tap]"]
r, _ = step([J("Create", "Good job, you are almost there! Tap the big button at the bottom called Upload Short.")], CHANNEL)
assert r["done"] is True and r["label"] is None and r["say"].startswith("Done!"), r
r, _ = step([J("Create", "Tap the big button.")], [l.replace("Sending file · 8%", "Preparing 100%") for l in CHANNEL])
assert r["done"] is True, r
r, _ = step([J("Create", "Tap “Create” to make a Short.")], [l for l in CHANNEL if "Sending" not in l])
assert r["done"] is False and r["label"] == "Create"                  # nothing under way yet: the guide goes on

# 3 Nov: "Tap Next" on Add details, which has "Upload Short" and no Next
DETAILS = ["Add details [text]", "Caption your Short [text]", "Visibility [text]", "Unlisted [text]", "Select audience [tap]",
           "Show more [tap]", "Upload Short [tap]"]
r, calls = step([J("Next", "Tap “Next” to go on with your video."), J("Upload Short", "Tap “Upload Short” to share your video.")], DETAILS)
assert r["label"] == "Upload Short" and len(calls) == 2, r
assert "“Next” is not on this screen" in calls[1]["messages"][0]["content"]
r, calls = step([J("Next", "Tap “Next”."), J("Next", "Tap “Next”.")], DETAILS)     # still wrong: kept, the watcher sees it
assert r["label"] is None and len(calls) == 2
r, calls = step([J("Next", "Tap “Next”."), RuntimeError("down"), RuntimeError("down"), RuntimeError("down")], DETAILS)
assert r["say"].startswith("Tap") and len(calls) >= 2                  # a failed second try never breaks the step
r, calls = step([J("Upload Short", "Tap “Upload Short”.")], DETAILS)
assert len(calls) == 1 and r["label"] == "Upload Short"                # right the first time: asked once

# 3 Nov: Help on YouTube's gallery, with no words typed, gave the same sentence back again and again
GALLERY = ["Upload from gallery [text]", "Videos [tap]", "Settings [tap]", "Select more media [tap]", "0:13 [text]", "0:09 [text]",
           "Video [selected]", "Short [tap]", "Live [tap]"]
SAME = "Tap the video you want, or tap + if it is not here."
r, _ = step([J(None, SAME)], GALLERY, stuck=True, history=[SAME])
assert r["say"] != SAME and "0:" in r["say"], r                        # explained: the small pictures, how long each one is

# The watcher: the same problem more than once is said (Michael stops halfway to see what keeps coming back), and the
# pop-up after a Stop says how far the guide got
H2 = dict(H, x_install_id="dev66b")
run(main.event(main.Event(event="start", guide="ai"), **H2))
step([J(None, "Tap the button to go on.")] * 2, ["… [text]"], h=H2)
step([J(None, "Tap the button to go on, please.")] * 2, ["… [text]", "… [tap]"], h=H2)
run(main.event(main.Event(event="stop", guide="quit_ai"), **H2))
main._claude_client = Client([json.dumps({"problems": []})])
r = run(main.watch_review(**H2))
assert [p["title"] for p in r["problems"]] == ["Could not point on step 1", "Could not point on step 2"], r
assert r["problems"][0]["what"].endswith("This happened 2 times in this guide (steps 1 and 2).") and r["stopped"] == 2, r
assert main.SERVER_VERSION >= "0.66"
print("youtube upload ok")
