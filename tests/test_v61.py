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
def J(label, say): return json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})
H = dict(x_app_token="tok", x_install_id="dev61", x_tester="1")
PIC = "/9j/" + "A" * 400
def step(outs, labels, image=PIC, h=H):
    main._claude_client = Client(outs)
    r = run(main.next_step(main.Next(goal="Scan a document with the Drive app", labels=labels, image=image,
                                     history=["Hold the camera still over the paper, then tap the big round button."]), **h))
    return r, main._claude_client.messages.calls

# Issue #6 (1 Nov) and the 2 Nov test: Drive's Upload screen had Cancel and Upload, the screen picture came back black,
# and the guide said "The screen is black right now" instead of pointing at Upload.
UPLOAD = ["Cancel [tap]", "Upload [tap]", "PDF [switch]", "JPEG [switch]", "My Drive [text]", "Location [text]", "Delete file name [tap]"]
BLACK = "The screen is black right now. Wait a moment, then tell me what you see, or open Drive again from your apps."
run(main.event(main.Event(event="start", guide="ai"), **H))
r, calls = step([J(None, BLACK), J("Upload", "Tap “Upload” to save your scan.")], UPLOAD)
assert r["label"] == "Upload" and "black" not in r["say"].lower(), r
assert len(calls) == 2
first, second = calls[0]["messages"][0]["content"], calls[1]["messages"][0]["content"]
assert isinstance(first, list) and first[0]["type"] == "image"                 # asked with the picture first
assert isinstance(second, str) and "came back black only because this app blocks pictures" in second   # then words only
assert "picture of the user's screen is attached" not in calls[1]["system"]
assert [p["kind"] for p in main._sessions["dev61"]["problems"]] == []          # pointed at Upload: nothing to report
assert main._sessions["dev61"]["steps"][-1]["picture"] is True          # the phone did send one

# The other way the AI said it on 2 Nov
r, calls = step([J(None, "The screen is black with only ScreenGuide's bar at the top. Wait a moment, then tap the Stop button."),
                 J("Upload", "Tap “Upload”.")], UPLOAD)
assert r["label"] == "Upload" and len(calls) == 2, r

# Not changed: a screen with almost no words really may be blank (Google's scanner: no words at all), and a black
# button is not a black screen
SCANNER = ["… [text]"]
r, calls = step([J(None, BLACK)], SCANNER)
assert len(calls) == 1 and "black" in r["say"].lower()
r, calls = step([J("Upload", "Tap the black “Upload” button.")], UPLOAD)
assert len(calls) == 1 and r["label"] == "Upload"
# Without a picture nothing is asked twice
r, calls = step([J(None, BLACK)], UPLOAD, image="")
assert len(calls) == 1
assert main.SERVER_VERSION >= "0.61" and main.STATS["black_picture_ignored"] == 2
print("black picture ok")
