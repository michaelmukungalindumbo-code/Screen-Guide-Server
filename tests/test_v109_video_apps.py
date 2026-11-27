import os, asyncio, json, time
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run

# The owner's Infinix phone, 27 Nov: "How do I upload content on YouTube?" On the phone's picker of photos and videos
# (opened with YouTube's "+"), the guide said "Tap the photo you want." He asked in Help: "it's YouTube, why have you asked
# me to tap photo?" and was told "Your photos are the small pictures on this screen. Tap the one you want." The goal did not
# say "video", and the picker did not name its videos, so the gallery rule chose photos. On YouTube (and TikTok, Reels,
# Shorts) an upload is a video. Staged: video_app_goal.


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
# Android's photo picker, as YouTube's "+" opens it (its items named only as photos)
PICKER = ["Photos [selected]", "Collections [tap]", "Photo taken on Nov 26, 2026 4:23 PM [tap]",
          "Photo taken on Nov 26, 2026 1:20 PM [tap]", "Photo taken on Nov 25, 2026 9:02 AM [tap]", "Preview [tap]", "Done [tap]"]
TOLD = ["Tap “YouTube”.", "Tap “Create” to start your upload.", "Tap the video you want, or tap + if it is not here."]


def step(outs, labels=PICKER, goal=GOAL, tester="1", install="v109", stuck=False, note=""):
    main._claude_client = Client(outs)
    b = main.Next(goal=goal, labels=list(labels), lang="en", history=list(TOLD), stuck=stuck, note=note)
    return run(main.next_step(b, x_app_token="tok", x_install_id=install, x_tester=tester))


# 1. The replay: a YouTube upload is a video, never "Tap the photo you want."
r = step([ans("Tap the photo you want.")])
assert r["say"] == "Tap the video you want.", r
# Help ("why have you asked me to tap photo?"): the explanation is about videos too
r = step([ans("Tap the photo you want.")], install="v109b", stuck=True, note="it's YouTube, why have you asked me to tap photo?")
assert "video" in r["say"].lower() and "photo" not in r["say"].lower(), r
# TikTok, Reels and Shorts are videos too
for g in ("Post on TikTok", "Make a Facebook reel", "Upload a YouTube Short"):
    r = step([ans("Tap the photo you want.")], goal=g, install="v109c" + g[:4])
    assert r["say"] == "Tap the video you want.", (g, r)

# 2. A goal that says photo stays photo (a YouTube profile picture, a photo on WhatsApp), as before
r = step([ans("Tap the photo you want.")], goal="Change my YouTube profile picture", install="v109d")
assert r["say"] == "Tap the photo you want.", r
r = step([ans("Tap the photo you want.")], goal="Send a picture on WhatsApp", install="v109e")
assert r["say"] == "Tap the photo you want.", r
# ...and a goal that names no app or kind still goes by what the picker shows
r = step([ans("Tap the photo you want.")], goal="Upload my file", install="v109f")
assert r["say"] == "Tap the photo you want.", r

# 3. Staged: before 24 quiet hours, other phones get the answer as it was
main._launch["live"][main.STAGED["video_app_goal"]] = time.time()
r = step([ans("Tap the photo you want.")], tester="", install="v109g")
assert r["say"] == "Tap the photo you want.", r
assert main.STAGED["video_app_goal"] == "1.09" and main.SERVER_VERSION >= "1.09"
print("YouTube, TikTok, Reels, Shorts: the gallery asks for a video, never a photo ok")
