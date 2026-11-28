import os, asyncio, json, time
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run

# The owner's Infinix phone, 28 Nov, "How do I upload content on YouTube?". After "Tap Upload to send your video." he
# tapped Upload; YouTube opened his channel ("Preparing 10%"), and the guide said "Tap “Create” to start a new video."
# with the ring on Create: the whole task again. Once the upload (or post, or send) button was tapped, "start a new ..."
# means the task is finished: it ends, saying so. Staged: no_restart.


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


def ans(say, label=None, done=False):
    return json.dumps({"label": label, "say": say, "done": done, "x": None, "y": None, "look_for": None})


GOAL = "How do I upload content on YouTube"
TOLD = ["Tap “Create” to start uploading your video.", "Tap your video.", "Tap “Next” to keep going with your video.",
        "Tap “Upload” to send your video."]
# YouTube's bottom bar while the channel page loads
LOADING = ["Navigate up [tap]", "Home [tap]", "Shorts [tap]", "Create [tap]", "You [tap]"]
NEW = "Tap “Create” to start a new video."


def step(outs, labels=LOADING, goal=GOAL, tester="1", install="v112", told=TOLD):
    main._claude_client = Client(outs)
    b = main.Next(goal=goal, labels=list(labels), lang="en", history=list(told))
    return run(main.next_step(b, x_app_token="tok", x_install_id=install, x_tester=tester))


# 1. The replay: after Upload, "start a new video" ends the guide
r = step([ans(NEW, label="Create")])
assert r["done"] is True and r["label"] is None and r["say"] == main._DONE_SAY["en"], r
for say in ("Tap “Create” to make another video.", "Tap “Create” to upload a new Short."):
    r = step([ans(say, label="Create")], install="v112b" + say[18:24])
    assert r["done"] is True, (say, r)
# 2. Not before the upload button was tapped: "Create" is how the task starts
r = step([ans("Tap “Create” to start a new video.", label="Create")], told=TOLD[:1], install="v112c")
assert r["done"] is False and r["label"] == "Create", r
r = step([ans("Tap “Create” to start uploading your video.", label="Create")], told=["Tap “YouTube”."], install="v112d")
assert r["done"] is False and r["label"] == "Create", r
# ...and not for a goal that is not making something
r = step([ans(NEW, label="Create")], goal="Watch a video on YouTube", install="v112e")
assert r["done"] is False, r
# 3. Staged: before 24 quiet hours, other phones get the answer as it was
main._launch["live"][main.STAGED["no_restart"]] = time.time()
r = step([ans(NEW, label="Create")], tester="", install="v112f")
assert r["done"] is False and r["label"] == "Create", r
assert main.STAGED["no_restart"] == "1.12" and main.SERVER_VERSION >= "1.12"
print("after the upload button, \"start a new ...\" ends the guide ok")
