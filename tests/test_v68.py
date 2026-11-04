import os, sys, types, asyncio, json, time
os.environ.update(ADMIN_KEY="k", GITHUB_TOKEN="ghp_test", AI_WATCH_PER_DAY="5")
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
async def fake_github(method, path, payload):
    return [] if method == "GET" else {}
main._github = fake_github
H = dict(x_app_token="tok", x_install_id="dev68", x_tester="1")
def step(label, say, labels, note="", stuck=False, tapped=False):
    main._claude_client = Client([json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})])
    return run(main.next_step(main.Next(goal="Upload a video in the YouTube app", labels=labels, note=note, stuck=stuck, tapped=tapped), **H))
def kinds(): return [p["kind"] for p in main._sessions["dev68"]["problems"]]

# 4 Nov: YouTube's gallery, then the photo picker (+, Done), then the gallery again with a NEW video in the list (0:21).
# The person must now tap it, so saying "Tap the video you want" again is right, not a repeat.
SAY = "Tap the video you want, or tap + if it is not here."
GAL = ["Video [selected]", "Short [tap]", "Live [tap]", "Post [tap]", "Close [tap]", "Upload from gallery [text]", "Videos [tap]",
       "Settings [tap]", "Select more media [tap]", "0:13 [tap]", "0:09 [tap]", "0:14 [tap]"]
run(main.event(main.Event(event="start", guide="ai"), **H))
step(None, SAY, GAL)
step("Done", "Tap Done to finish choosing your video.", ["… [tap]", "Photos [text]", "Done [tap]"], tapped=True)
step(None, SAY, GAL[:9] + ["0:13 [tap]", "0:21 [tap]", "0:09 [tap]", "0:14 [tap]"])
assert "repeat" not in kinds(), kinds()

# Still a problem: the very same screen comes back after another step
step("Done", "Tap Done to finish choosing your video.", ["Done [tap]"], tapped=True)
step(None, SAY, GAL)
assert "repeat" in kinds(), kinds()
print("ok", kinds())
