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
def step(label, say, labels, goal="Upload a video to YouTube"):
    main._claude_client = Client([json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})])
    return run(main.next_step(main.Next(goal=goal, labels=labels), x_app_token="tok", x_install_id="v38"))
# the exact screen from the recording: YouTube's gallery, the AI said to close it
YT = ["Close [tap]", "Upload from gallery [text]", "Videos [tap]", "Settings [tap]", "Select more media [tap]", "0:14 [text]",
      "Video [selected]", "Short [tap]", "Live [tap]", "Post [tap]"]
r = step("Close", "Tap “Close” to close this pop-up.", YT)
assert r["label"] == "0:14" and r["say"] == "Tap your video, or tap + if it is not here.", r
r = step(None, "Go back and try again.", YT)
assert r["label"] == "0:14", r
r = step("Navigate up", "Tap the back arrow.", YT + ["Navigate up [tap]"])
assert r["label"] == "0:14", r
# away from a picker, closing a real pop-up is still allowed
r = step("Not now", "Tap “Not now”.", ["Rate this app [text]", "Not now [tap]", "Rate [tap]"], goal="Upload a video to YouTube")
assert r["label"] == "Not now", r
assert "never close it" in main.NEXT_SYSTEM
print("never close the picker ok")
