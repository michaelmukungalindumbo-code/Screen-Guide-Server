import os, asyncio, json
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
H = dict(x_app_token="tok", x_install_id="dev60")
WAIT = "Your scan is uploading. Wait a moment, then tell me what you see."
def step(labels, history, say=WAIT):
    main._claude_client = Client([json.dumps({"label": None, "say": say, "done": False, "x": None, "y": None, "look_for": None})])
    return run(main.next_step(main.Next(goal="Scan a document with the Drive app", labels=labels, history=history), **H))
# Screen from the issue (step 5): Drive's file list is back after the Upload screen, the AI still said "uploading".
DRIVE = ["Scan Document [tap]", "Create new [switch]", "Home [tap]", "Starred [tap]", "Files [text]", "My Drive [text]", "Computers [tap]", "… [tap]"]
told = ["Wait a moment. The phone is uploading your scan. When it finishes, tell me what you see."]
r = step(DRIVE, told)
assert r["done"] is True and r["label"] is None, r
# The Upload screen itself (Upload button on screen): not finished, keep the AI's answer.
UPLOAD = ["Cancel [tap]", "Upload [tap]", "PDF [switch]", "JPEG [switch]", "My Drive [text]"]
assert step(UPLOAD, told)["done"] is False
# Drive's list at the start (nothing about uploading told yet): the guide goes on as before.
assert step(DRIVE, ["Tap “Scan Document” to scan your paper."])["done"] is False
print("ok")
