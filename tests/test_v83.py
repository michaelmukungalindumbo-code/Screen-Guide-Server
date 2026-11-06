import os, asyncio, json
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run
class Msgs:
    def __init__(self, out): self.out = list(out); self.calls = []
    async def create(self, **kw):
        self.calls.append(kw)
        class U: input_tokens = 2300; output_tokens = 200
        class B: type = "text"; text = self.out.pop(0)
        class M: content = [B()]; usage = U(); stop_reason = "end_turn"
        return M()
class Client:
    def __init__(self, out): self.messages = Msgs(out)
def J(label, say): return json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})
main.settings.ANTHROPIC_API_KEY = main.settings.ANTHROPIC_API_KEY or "test"

# #39, 6 Nov: Infinix, Android 14. The list of all apps was open (scrolled to M) with a Search box at the top; Drive was
# above, out of sight. The guide said "Swipe up to see all your apps" with nothing pointed at, and the person asked
# "why didn't you just tell me to search". An app that is not on a screen with a Search box: point at Search.
DRAWER = ["Messages [tap]", "… [tap]", "… [tap]", "… [tap]", "… [tap]", "Phone [tap]", "… [tap]", "Photos [tap]", "… [tap]",
          "Play Store [tap]", "… [tap]", "… [tap]", "ScreenGuide [tap]", "Settings [tap]", "Sheets [tap]", "… [tap]", "… [tap]",
          "Weather [tap]", "WhatsApp [tap]", "… [tap]", "YouTube [tap]", "Search [tap]"]
SWIPE = "Drive is not on this screen yet. Swipe up to see all your apps, then we will find Drive. You can do it!"
def step(labels, label, say, goal="Scan a document with the Drive app", tester="1", lang="en", i="dev83"):
    main._claude_client = Client([J(label, say)] * 4)
    return run(main.next_step(main.Next(goal=goal, labels=labels, lang=lang), x_app_token="tok", x_install_id=i, x_tester=tester))

r = step(DRAWER, "Drive", SWIPE)
assert r["label"] == "Search", r
assert r["say"] == "Drive is not on this screen. Tap “Search”, then type Drive.", r
assert main.STATS["search_for_app"] >= 1
# The AI named nothing, only said it in words
r = step(DRAWER, None, "Drive is not on this screen. Swipe up to see all your apps.")
assert r["label"] == "Search" and "Drive" in r["say"], r
# A home screen whose search box is called "Search apps"
HOME = ["Phone [tap]", "Messages [tap]", "Camera [tap]", "Search apps [tap]"]
r = step(HOME, "Drive", "Swipe up to see all your apps, then find Drive.")
assert r["label"] == "Search apps", r
# No search box: the swipe stays
r = step(DRAWER[:-1], "Drive", SWIPE)
assert r["label"] is None and "Swipe up" in r["say"], r
# Not about finding an app (a swipe inside an app): unchanged
r = step(DRAWER, None, "Swipe up to see more settings.", goal="Turn on Bluetooth")
assert r["label"] is None and "Swipe up" in r["say"], r
# Never searches for a banking or mobile money app
r = step(DRAWER, "MTN MoMo", "MTN MoMo is not on this screen. Swipe up to see all your apps.", goal="Send money with MTN MoMo")
assert r["label"] != "Search", r
# Staged: users' phones get it only after the quiet hours
main._launch["live"].pop(main.STAGED["search_for_app"], None)
r = step(DRAWER, "Drive", SWIPE, tester="", i="user83")
assert r["label"] is None and "Swipe up" in r["say"], r
assert main.SERVER_VERSION >= "0.83"
print("an app not on a screen with a Search box: the ring goes to Search, and the step says what to type")
