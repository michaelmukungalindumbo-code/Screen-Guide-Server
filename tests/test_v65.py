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
H = dict(x_app_token="tok", x_install_id="dev65", x_tester="1")
PIC = "/9j/" + "A" * 400
def step(outs, labels, image=PIC, h=H, goal="How do I scan a document on my phone"):
    main._claude_client = Client(outs)
    r = run(main.next_step(main.Next(goal=goal, labels=labels, image=image), **h))
    return r, main._claude_client.messages.calls
run(main.event(main.Event(event="start", guide="ai"), **H))
SCANNER = ["… [text]"]

# 3 Nov (and 2 Nov): "tap the big round button" in Google's scanner, nothing pointed at. Now its place in the picture.
SHUTTER = "Hold the camera still over the paper, then tap the big round button at the bottom to take the photo."
r, calls = step([J(None, SHUTTER), J(None, SHUTTER, x=0.5, y=0.88)], SCANNER)
assert len(calls) == 2 and (r["x"], r["y"]) == (0.5, 0.88) and r["label"] is None, r
assert "Nothing in <screen_words> is the thing to tap" in calls[1]["messages"][0]["content"][-1]["text"]
# Not asked again: a wait, a step already pointed at, the person's own choice, a gallery, a blocked (black) picture
assert len(step([J(None, "Hold the camera still. It takes the photo by itself.")], SCANNER)[1]) == 1
assert len(step([J(None, SHUTTER, x=0.5, y=0.9)], SCANNER)[1]) == 1
assert len(step([J(None, "Tap the photo you want to send.")], SCANNER)[1]) == 1
assert len(step([J(None, "Tap the photo.")], ["Recents [text]", "Select more [tap]", "… [tap]"])[1]) == 1
UPLOAD = ["Cancel [tap]", "Upload [tap]", "PDF [switch]"]
r, calls = step([J(None, "The screen is black right now."), J(None, "Tap the button at the top right to save it.")], UPLOAD)
assert len(calls) == 2 and r["x"] is None, r           # asked again without the picture, never asked where on a black one

# The reviewer never describes a screen from a black picture (3 Nov: it called the Upload screen "a camera preview")
assert "Never describe a screen from a black picture (not as a camera view either)" in main.REVIEW_SYSTEM

# Slow answers as the phone saw them (3 Nov: 20 seconds, network and a waking server included; the watcher missed it)
H = dict(H, x_install_id="dev65s")
run(main.event(main.Event(event="start", guide="ai"), **H))
step([J("Upload", "Tap “Upload”.")], UPLOAD, image="", h=H)
assert run(main.watch_slow(main.WatchSlow(step=1, ms=20200), **H)) == {"watch": 1}
s = main._sessions["dev65s"]
assert [(p["kind"], p["step"], p["secs"]) for p in s["problems"]] == [("slow", 1, 20)] and s["steps"][0]["phone_secs"] == 20
assert main._rule_card(s["problems"][0])["what"].startswith("The answer to step 1 took 20 seconds. On a weak network people give up. ")
assert "The phone waited 20 seconds" in main._rule_card(s["problems"][0])["what"]   # v0.68: and where the time went
assert run(main.watch_slow(main.WatchSlow(step=1, ms=25000), **H)) == {"watch": 1}          # once per step
assert run(main.watch_slow(main.WatchSlow(step=2, ms=8000), **H)) == {"watch": 1}           # 8 s is not slow
assert run(main.watch_slow(main.WatchSlow(step=99, ms=20000), **H)) == {"watch": 1}         # no such step
assert run(main.watch_slow(main.WatchSlow(step=1, ms=20000), **dict(H, x_tester=""))) == {"watch": 0}
assert main.SERVER_VERSION >= "0.65" and main.PROMPT_VERSION >= "52"
# A second try that fails never breaks the step: the first answer stays (both kinds of second try)
r, calls = step([J(None, SHUTTER), RuntimeError("down"), RuntimeError("down"), RuntimeError("down")], SCANNER)
assert r["say"].startswith("Hold the camera still") and r["x"] is None, r
r, calls = step([J(None, "The screen is black right now."), RuntimeError("down"), RuntimeError("down"), RuntimeError("down")], UPLOAD)
assert r["label"] == "Upload" and "black" not in r["say"].lower(), r
print("pointing, slow and reviewer ok")
