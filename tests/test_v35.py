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
def step(label, say, labels, goal="Upload a video in the YouTube app", lang="en"):
    main._claude_client = Client([json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})])
    return run(main.next_step(main.Next(goal=goal, labels=labels, lang=lang), x_app_token="tok", x_install_id="v35"))
# the exact screen from the recording
YT = ["Video [selected]", "Short [tap]", "Live [tap]", "Post [tap]", "Close [tap]", "Videos [tap]", "Settings [tap]", "Select more media [tap]", "0:14 [text]"]
r = step("Videos", 'Tap "Videos" to choose the video you want to upload.', YT)
assert r["label"] == "0:14" and r["say"] == "Tap your video, or tap + if it is not here.", r
r = step("0:14", "Tap the video you want to upload, the one that shows 0:14.", YT)
assert r["label"] == "0:14" and r["say"] == "Tap your video, or tap + if it is not here.", r
# the "+" tile: no video shows yet -> ring the +
r = step(None, "Choose what you want, then tap it.", ["Video [selected]", "Short [tap]", "Videos [tap]", "Select more media [tap]", "Upload from gallery [text]"])
assert r["label"] == "Select more media" and r["say"] == "Tap + to choose your video.", r
# the AI already points at the + or at Next: left alone
r = step("Select more media", "Tap the plus.", YT)
assert r["label"] == "Select more media" and r["say"] == "Tap the plus.", r
r = step("Next", "Tap Next.", YT + ["Next [tap]"])
assert r["label"] == "Next" and r["say"] == "Tap Next.", r
# one video, no + : plain wording
r = step("0:14", "Tap it.", ["Video [selected]", "Videos [tap]", "0:14 [text]", "Upload from gallery [text]"])
assert r["label"] == "0:14" and r["say"] == "Tap your video.", r
many = YT + ["1:02 [text]", "0:37 [text]"]
r = step("0:14", "Tap the video that shows 0:14.", many)
assert r["label"] is None and r["say"] == "Tap the video you want, or tap + if it is not here.", r
r = step("All albums", "Tap All albums.", many, lang="ny")
assert r["label"] is None and r["say"] == "Dinani vidiyo imene mukufuna, kapena dinani + ngati palibe.", r
r = step("Photos", "Tap Photos.", ["Recents [tap]", "Photos [tap]", "IMG 1 [tap]"], goal="Send a photo on WhatsApp")
assert r["label"] is None and r["say"] == "Tap the photo you want.", r
# a normal screen is untouched, and the Video tab tag is understood
r = step("Create", "Tap Create.", ["Home [tap]", "Shorts [tap]", "Create [tap]", "Videos [tap]"])
assert r["label"] == "Create" and r["say"] == "Tap Create.", r
assert main._plain("Video [selected]") == "Video"
r = step("Video", "Tap Video.", YT)
assert r["label"] == "Video"   # the AI is told not to; the server only cleans the tag
sysp = main.NEXT_SYSTEM
assert "[selected] means" in sysp and "Never point at an album menu" in sysp and main.SERVER_VERSION >= "0.35"
assert main.STATS["gallery_fixed"] >= 3
print("gallery ok")
