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
def step(labels, label, say, goal="Upload a video in the YouTube app", tester=True, i="dev90"):
    main._claude_client = Client([J(label, say)] * 3)
    return run(main.next_step(main.Next(goal=goal, labels=labels, history=["Tap “Create”."]),
                              x_app_token="tok", x_install_id=i, x_tester="1" if tester else ""))

# #79 (12 Nov, change request "remove this step"): YouTube's gallery, step 3 of "Upload a video in the YouTube app".
# The guide said "Tap "Video" to choose what kind of upload you want." while Video was already the chosen tab.
SAID = "Tap “Video” to choose what kind of upload you want."
REST = ["Short [tap]", "Live [tap]", "Post [tap]", "Back [tap]", "Upload from gallery [text]", "Videos [tap]",
        "Settings [tap]", "Select more media [tap]", "0:04 [tap]", "0:06 [tap]", "0:13 [tap]", "0:21 [tap]"]
assert "chosen_tab" in main.STAGED
for video in ("Video [selected]", "Video [tap]"):   # marked as chosen by the phone, or not
    r = step([video] + REST, "Video", SAID)
    assert r["label"] != "Video" and r["say"] == "Tap the video you want, or tap + if it is not here.", r

# Another tab is still a step when the goal asks for it
r = step(["Video [selected]"] + REST, "Short", "Tap “Short”.", goal="Upload a Short in the YouTube app")
assert r["label"] == "Short", r
# Not a gallery: the rule does nothing
r = step(["Video [tap]", "Short [tap]", "Live [tap]"], "Video", SAID)
assert r["label"] == "Video", r

# Staged (the Launch Bay): users' phones only after 0.90 has been live for 24 hours
main._launch["live"][main.STAGED["chosen_tab"]] = main.time.time()
r = step(["Video [selected]"] + REST, "Video", SAID, tester=False, i="user90")
assert r["label"] == "Video", r
main._launch["live"][main.STAGED["chosen_tab"]] -= 25 * 3600
r = step(["Video [selected]"] + REST, "Video", SAID, tester=False, i="user90b")
assert r["label"] != "Video", r
assert main._launch["seen"]["chosen_tab"]["fired"] >= 1
assert main.SERVER_VERSION >= "0.90"
print("a tab that is already chosen is never a step on a gallery")
