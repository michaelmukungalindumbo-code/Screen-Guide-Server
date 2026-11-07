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

# #40, 6 Nov (Infinix, Android 14): "Scan a document with the Drive app". The app list had a Search box at the top, but
# Drive was not shown, and the guide said "Swipe up to see all your apps" (twice). The person pressed Help: "why didn't
# you just tell me to search". When an app is not on the screen and the Search box is, the step is: tap Search, type it.
HOME = (["Messages [tap]"] + ["… [tap]"] * 4 + ["Phone [tap]", "… [tap]", "Photos [tap]", "… [tap]", "Play Store [tap]"]
        + ["… [tap]"] * 2 + ["ScreenGuide [tap]", "Settings [tap]", "Sheets [tap]"] + ["… [tap]"] * 2
        + ["Weather [tap]", "WhatsApp [tap]", "… [tap]", "YouTube [tap]", "Search [tap]"])
GOAL = "Scan a document with the Drive app"
SWIPE = "Drive is not on this screen yet. Swipe up to see all your apps, then we will find Drive. You can do it!"
def step(labels, say, goal=GOAL, lang="en", tester="1", i="dev83", label=None):
    main._claude_client = Client([J(label, say)] * 3)
    return run(main.next_step(main.Next(goal=goal, labels=labels, lang=lang), x_app_token="tok", x_install_id=i, x_tester=tester))

r = step(HOME, SWIPE)
assert r["label"] == "Search", r
assert r["say"] == "Tap “Search”, then type Drive.", r
assert "swipe" not in r["say"].lower(), r
# the app's name from the goal when the AI's words do not name it
r = step(HOME, "Swipe up to see all your apps.", goal="Open Drive and scan a document", i="dev83b")
assert r["label"] == "Search" and r["say"] == "Tap “Search”, then type Drive.", r
r = step(HOME, "Swipe up to see all your apps.", goal="Scan a document", i="dev83c")
assert r["label"] == "Search" and r["say"] == "Tap “Search”, then type the app’s name.", r

# No Search box on the screen (#40 step 2, a voice box over the home screen): the swipe stays
r = step(["… [text]"] * 3 + ["… [tap]"], "Tap the Home button, then swipe up to see all your apps and find Drive.", i="dev83d")
assert r["label"] is None and "swipe up" in r["say"].lower(), r
# A search inside an app ("Search in Drive") is not the phone's app search
r = step(["Search in Drive [tap]", "Home [tap]", "Files [tap]"], SWIPE, i="dev83e")
assert r["label"] is None, r
# A scroll inside an app, not the app list, is left alone
r = step(HOME, "Scroll down to find Drive in the list.", i="dev83f")
assert r["label"] != "Search" or "type" not in r["say"], r
# Never typing a money app's name
r = step(HOME, "Airtel Money is not on this screen yet. Swipe up to see all your apps.", goal="Open Airtel Money", i="dev83g")
assert "type" not in r["say"].lower(), r
# Nyanja and Bemba: no checked words yet, so unchanged
r = step(HOME, SWIPE, lang="ny", i="dev83h")
assert r["label"] is None, r

# From the other fixer run (#39, the same screen): the AI named nothing and only said it in words
r = step(HOME, "Drive is not on this screen. Swipe up to see all your apps.", i="dev83i")
assert r["label"] == "Search" and r["say"] == "Tap “Search”, then type Drive.", r
# A home screen whose box is called "Search apps"
r = step(["Phone [tap]", "Messages [tap]", "Camera [tap]", "Search apps [tap]"], "Swipe up to see all your apps, then find Drive.", i="dev83j")
assert r["label"] == "Search apps" and r["say"] == "Tap “Search apps”, then type Drive.", r
# The same list with no Search box: the swipe stays
r = step(HOME[:-1], SWIPE, i="dev83k")
assert r["label"] is None and "swipe up" in r["say"].lower(), r
# A swipe that has nothing to do with finding an app is left alone
r = step(HOME, "Swipe up to see more settings.", goal="Turn on Bluetooth", i="dev83l")
assert r["label"] is None and "swipe up" in r["say"].lower(), r
# Never searching for a mobile money app
r = step(HOME, "MTN MoMo is not on this screen. Swipe up to see all your apps.", goal="Send money with MTN MoMo", i="dev83m")
assert r["label"] != "Search" and "type" not in r["say"].lower(), r

# Staged: users' phones get it only after 24 quiet hours
main._launch["live"].pop(main.STAGED["search_for_app"], None)
r = step(HOME, SWIPE, tester="0", i="user83")
assert r["label"] is None and "swipe up" in r["say"].lower(), r
assert main.STATS["search_for_app"] >= 3
assert main.SERVER_VERSION >= "0.83"
print("an app not on the screen: tap Search and type its name, when the Search box is there")
