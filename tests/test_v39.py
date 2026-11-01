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
def step(label, say, labels, goal, lang="en", done=False):
    main._claude_client = Client([json.dumps({"label": label, "say": say, "done": done, "x": None, "y": None, "look_for": None})])
    return run(main.next_step(main.Next(goal=goal, labels=labels, lang=lang), x_app_token="tok", x_install_id="v39"))
# 1. the mobile data recording: a remark with a ring on the switch -> no ring, and the check is done
SIM = ["Navigate up [tap]", "MTN [text]", "Mobile Data [text]", "SIM 1,Mobile Data is enabled. [switch]", "SIM 2,Mobile Data is disabled. [switch]",
       "Call [text]", "Data Usage [tap]", "Network Optimization [tap]"]
r = step("SIM 1,Mobile Data is enabled.", "Good, Mobile Data is on for SIM 1", SIM, "Check the network and mobile data")
assert r["label"] is None and r["done"] is True, r
r = step("Mobile Data", "Tap “Mobile Data” to check if your mobile data is on.", SIM, "Check the network and mobile data")
assert r["label"] == "Mobile Data" and r["done"] is False, r
r = step("Data Usage", "This is where you see your data.", SIM, "Turn on mobile data")   # not a check goal: no ring, not done
assert r["label"] is None and r["done"] is False, r
# 2. the YouTube editor recording: "Exit editor" while "Next" is on screen -> Next; a remark before the instruction is dropped
ED = ["Edit [tap]", "Exit editor [tap]", "Volume [tap]", "Next [tap]", "Add sound [tap]", "Text [tap]", "Effects [tap]", "Filters [tap]", "Stickers [tap]"]
r = step("Exit editor", "You are in the video editor. Tap the back arrow to leave it.", ED, "Upload a video to YouTube")
assert r["label"] == "Next" and r["say"] == "Tap “Next”.", r
r = step("Exit editor", "Tap Exit editor.", ED, "Upload a video to YouTube", lang="bem")
assert r["label"] == "Next" and r["say"] == "Kandeni “Next”.", r
r = step("Next", "You are in the video editor. Tap Next.", ED, "Upload a video to YouTube")
assert r["label"] == "Next" and r["say"] == "Tap Next.", r
# 3. going back is still right when they are in the wrong place, or when the goal makes nothing
r = step("Navigate up", "Tap the back arrow.", ["Navigate up [tap]", "Wi-Fi [tap]", "Bluetooth [tap]"], "Upload a video to YouTube")
assert r["label"] == "Navigate up", r
r = step("Close", "Tap Close.", ["Rate this app [text]", "Close [tap]", "Rate [tap]"], "Turn on Wi-Fi")
assert r["label"] == "Close", r
# 4. Chinyanja and Icibemba steps keep their ring (the remark check is English only)
r = step("Settings", "Pitani ku Settings.", ["Settings [tap]", "Phone [tap]"], "Check storage", lang="ny")
assert r["label"] == "Settings" and r["done"] is False, r
assert "Keep moving forward" in main.NEXT_SYSTEM and main.SERVER_VERSION >= "0.39"
print("remarks, check goals and moving forward ok")
