import os, asyncio, json
os.environ.update(ADMIN_KEY="k")
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
def J(label, say): return json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})
def step(labels, label, say, tester=True, goal="Upload a video in the YouTube app", i="dev73"):
    main._claude_client = Client([J(label, say), J(label, say)])
    return run(main.next_step(main.Next(goal=goal, labels=labels), x_app_token="tok", x_install_id=i, x_tester="1" if tester else ""))

# 4 Nov, YouTube's Shorts editor: "Tap “Exit editor” to go back", with the ring on the back arrow, while uploading.
# The rule that keeps an upload going forward skipped "Next", because this editor shows Next as plain words inside a
# tappable box ([text]). It now uses such a Next when no tappable one is there.
ED = ["Edit [tap]", "Exit editor [tap]", "Volume [tap]", "Next [text]", "Add sound [tap]", "Text [tap]", "Effects [tap]",
      "Filters [tap]", "Stickers [tap]"]
assert "forward_from_text" in main.STAGED
r = step(ED, "Exit editor", "Tap “Exit editor” to go back.")
assert r["label"] == "Next" and r["say"] == "Tap “Next”.", r
# A tappable Next still comes first; a goal that makes nothing may still go back
r = step(ED + ["Next [tap]"], "Exit editor", "Tap “Exit editor”.")
assert r["label"] == "Next"
r = step(ED, "Exit editor", "Tap “Exit editor”.", goal="Turn on dark mode")
assert r["label"] == "Exit editor"
# Staged (the Launch Bay): users' phones get it once 0.73 has been live for 24 hours; test phones at once
main._launch["live"][main.STAGED["forward_from_text"]] = main.time.time()
r = step(ED, "Exit editor", "Tap “Exit editor” to go back.", tester=False, i="user73")
assert r["label"] == "Exit editor", r                                  # not yet for users
main._launch["live"][main.STAGED["forward_from_text"]] -= 25 * 3600
r = step(ED, "Exit editor", "Tap “Exit editor” to go back.", tester=False, i="user73")
assert r["label"] == "Next", r
assert main._launch["seen"]["forward_from_text"]["fired"] == 1        # counted for the automatic pause
assert main.SERVER_VERSION >= "0.73"
print("forward from a plain-words Next")
