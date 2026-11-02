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
def J(label, say, x=None, y=None): return json.dumps({"label": label, "say": say, "done": False, "x": x, "y": y, "look_for": None})
H = dict(x_app_token="tok", x_install_id="dev64", x_tester="1")
PIC = "/9j/" + "A" * 400
def step(outs, labels, image=PIC, goal="How do I scan a document on my phone"):
    main._claude_client = Client(outs)
    r = run(main.next_step(main.Next(goal=goal, labels=labels, image=image), **H))
    return r, main._claude_client.messages.calls
run(main.event(main.Event(event="start", guide="ai"), **H))

# 3 Nov: Drive's Upload screen, and the AI said "The screen looks black" even when asked again without the picture.
UPLOAD = ["Cancel [tap]", "Upload [tap]", "PDF [switch]", "JPEG [switch]", "My Drive [text]", "Location [text]", "Delete file name [tap]"]
BLACK = "The screen looks black. Wait a moment, then tap the screen once to wake it up."
r, calls = step([J(None, BLACK), J(None, BLACK)], UPLOAD)
assert len(calls) == 2 and r["label"] == "Upload" and r["say"] == "Tap “Upload”." and "black" not in r["say"].lower(), r
# No main button on the screen: at least never "the screen is black"
r, calls = step([J(None, BLACK), J(None, BLACK)], ["Cancel [tap]", "Settings [tap]", "Album [text]"])
assert r["label"] is None and "black" not in r["say"].lower(), r

# 1-3 Nov: Google's scanner hides its words; the AI saw "Next" in the picture and named it, but nothing could be pointed at.
SCANNER = ["… [text]", "Enhance [tap]"]
r, calls = step([J("Next", "Tap “Next” to keep your scan."), J(None, "Tap “Next” to keep your scan.", x=0.79, y=0.95)], SCANNER)
assert len(calls) == 2 and r["x"] == 0.79 and r["y"] == 0.95 and r["label"] is None, r
assert "“Next” is not in <screen_words>" in calls[1]["messages"][0]["content"][-1]["text"]
assert "a button whose word the app hides from the list" in calls[0]["system"]
# It cannot see it either: the step stays as it was (one more try only)
r, calls = step([J("Next", "Tap “Next” to keep your scan."), J("Next", "Tap “Next”.")], SCANNER)
assert len(calls) == 2 and r["x"] is None, r
# A word that is on the screen, or no picture: asked once, as before
r, calls = step([J("Enhance", "Tap “Enhance”.")], SCANNER)
assert len(calls) == 1 and r["label"] == "Enhance"
r, calls = step([J("Next", "Tap “Next”.")], SCANNER, image="")
assert len(calls) == 1

# The watcher: a wait or "hold still" needs nothing pointed at (3 Nov: "Do not tap anything yet" was "Could not point")
H2 = dict(H, x_install_id="dev64b")
def wstep(say):
    main._claude_client = Client([J(None, say)] * 3)
    run(main.next_step(main.Next(goal="Scan a document", labels=SCANNER), **H2))
run(main.event(main.Event(event="start", guide="ai"), **H2))
wstep("Wait a moment. Your scan is uploading to Drive. Do not tap anything yet.")
wstep("Hold the camera still over the paper. The Scan button appears when it sees the page.")
wstep("Don’t press anything: the page is still being checked.")
assert [p["kind"] for p in main._sessions["dev64b"]["problems"]] == [], main._sessions["dev64b"]["problems"]
wstep("Tap “Next” to keep your scan.")
assert [(p["kind"], p["step"]) for p in main._sessions["dev64b"]["problems"]] == [("no_point", 4)]
assert main.SERVER_VERSION >= "0.64" and main.PROMPT_VERSION >= "51"
print("pointing and black screen ok")
