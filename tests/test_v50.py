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
def step(label, say, labels, note="", stuck=False, history=(), lang="en", goal="Upload a video in the YouTube app"):
    main._claude_client = Client([json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})])
    r = run(main.next_step(main.Next(goal=goal, labels=labels, lang=lang, note=note, stuck=stuck, history=list(history)),
                           x_app_token="tok", x_install_id="v50"))
    return r, main._claude_client.messages.calls[0]

# The screen from the phone recording (1 Nov): YouTube's gallery, two videos and the "+"
YT = ["Upload from gallery [text]", "Videos [tap]", "Settings [tap]", "Select more media [tap]", "0:09 [text]", "0:14 [text]"]
SAME = "Tap the video you want, or tap + if it is not here."

# Before: "I don't understand" got the same sentence back. Now: a plain explanation, still no ring (they choose).
r, call = step(None, SAME, YT, note="I don't understand", stuck=True, history=[SAME])
assert r["label"] is None, r
assert r["say"] == "Your videos are the small pictures on this screen. Each one shows how long it is, like 0:09. Tap the one you want. If yours is not here, tap +.", r
assert "<user_note>I don't understand</user_note>" in call["messages"][0]["content"] and "asked for help" in call["messages"][0]["content"]
assert "never repeat the words in <already_told>" in call["system"]

# The AI's own explanation is kept when it is a real explanation and safe (not just one short order)
good = "The small squares near the top are your videos. Tap the one you want to share."
r, _ = step(None, good, YT, note="I don't understand", stuck=True, history=[SAME])
assert r["label"] is None and r["say"] == good, r

# ...but never one that sends them to the album menu: the plain explanation instead
r, _ = step("Videos", "Your videos are in a list. Tap Videos at the top to see them.", YT, note="I can't find it", stuck=True, history=[SAME])
assert r["label"] is None and r["say"].startswith("Your videos are the small pictures"), r

# One video: still ringed, and the explanation is not cut down to one short order
ONE = ["Upload from gallery [text]", "Videos [tap]", "Select more media [tap]", "0:14 [text]"]
r, _ = step("0:14", "Your video is the small picture that shows 0:14. Tap it.", ONE, note="I don't understand", stuck=True,
            history=["Tap your video, or tap + if it is not here."])
assert r["label"] == "0:14" and r["say"] == "Your video is the small picture that shows 0:14. Tap it.", r

# No video shows yet, only the "+": ring the + and say why
PLUS = ["Upload from gallery [text]", "Videos [tap]", "Select more media [tap]"]
r, _ = step(None, "Tap + to choose your video.", PLUS, note="I don't understand", stuck=True, history=["Tap + to choose your video."])
assert r["label"] == "Select more media" and r["say"] == "This app cannot see your videos yet. Tap + to choose one from your phone.", r

# Nothing changes when they did not ask for help
r, _ = step(None, "Tap the video that shows 0:14.", YT)
assert r["label"] is None and r["say"] == SAME, r
# Nyanja: no checked wording for the explanation yet, so the usual sentence (or the AI's own explanation)
r, _ = step(None, "Tap the video you want.", YT, note="I don't understand", stuck=True, lang="ny")
assert r["say"] == "Dinani vidiyo imene mukufuna, kapena dinani + ngati palibe.", r
assert main.SERVER_VERSION >= "0.50"
print("help explains instead of repeating ok")
