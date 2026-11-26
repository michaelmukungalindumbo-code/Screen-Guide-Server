import os, asyncio, json, time
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run

# Issue #103, the owner's phone, 26 Nov: "How do I make a quiz with Google Forms?" The chat said Google Forms is not on the
# phone and to install it from the Play Store (server 1.03's rule). But Google Forms has no Android app: it is a website.
# On the Play Store results the card said "Tap Install to put Google Forms on your phone." with the ring on the Install of
# the first result, a Sponsored app by another company ("Forms App", Aurora Innovation Labs). The owner: "It said Google
# forms, but it pointed at something else, not by Google". Also: on the Play Store's home, with no box open, the card said
# "Keep typing. Type the rest of the words: ay Store." and he pressed Help.


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


def ans(say, label=None):
    return json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})


def step(outs, labels, goal, history=("Tap “Search”.",), tester="1", install="v107"):
    main._claude_client = Client(outs)
    b = main.Next(goal=goal, labels=list(labels), lang="en", history=list(history))
    r = run(main.next_step(b, x_app_token="tok", x_install_id=install, x_tester=tester))
    return r, main._claude_client.messages.calls


# 1. The chat knows Google Forms is a website (Chrome), never an app to install
assert "Google Forms has no Android app" in main.SYSTEM and "forms.google.com" in main.SYSTEM
assert "only an app you are sure is on the Play Store" in main.SYSTEM

# 2. Play Store results whose first Install belongs to a Sponsored app: never ring that Install
RESULTS = ["Navigate up [tap]", "google forms [text]", "Rating [tap]", "Android Auto [tap]", "Sponsored [text]",
           "Forms App - Make Online Forms [tap]", "Aurora Innovation Labs [text]", "Install [tap]",
           "Forms App - Manage your forms [tap]", "Google Docs [tap]", "Google LLC [text]", "Installed [text]"]
r, _ = step([ans("Tap “Install” to put Google Forms on your phone.", label="Install")], RESULTS,
            "Install Google Forms from the Play Store")
assert r["label"] is None and r["say"] == "“Google Forms” is not in this list. Never tap Install on an app marked Sponsored.", r
# The app they want is further down: its name gets the ring (its own page has its own Install)
WA = ["Navigate up [tap]", "whatsapp [text]", "Sponsored [text]", "Super Kwacha - Online Loans [tap]", "Kwacha Ltd [text]",
      "Install [tap]", "WhatsApp Messenger [tap]", "WhatsApp LLC [text]", "Install [tap]"]
r, _ = step([ans("Tap “Install”.", label="Install")], WA, "Install WhatsApp from the Play Store", install="v107b")
assert r["label"] == "WhatsApp Messenger" and r["say"] == "Tap “WhatsApp Messenger” to open its page. Check who made it before you install it.", r
# On the app's own page (its Install comes before any Sponsored row), Install is rung as before
PAGE = ["Navigate up [tap]", "WhatsApp Messenger [text]", "WhatsApp LLC [tap]", "Install [tap]", "About this app [tap]",
        "Sponsored [text]", "Super Kwacha - Online Loans [tap]"]
r, _ = step([ans("Tap “Install”.", label="Install")], PAGE, "Install WhatsApp from the Play Store", install="v107c")
assert r["label"] == "Install", r

# 3. "Keep typing" with no box open: asked again
HOME = ["Games [tap]", "Apps [tap]", "Search [tap]", "You [tap]", "Sponsored [text]", "MoMo [tap]", "My Airtel [tap]"]
r, calls = step([ans("Keep typing. Type the rest of the words: ay Store. Then look for Google Forms in the list."),
                 ans("Tap “Search”.", label="Search")], HOME, "Install Google Forms from the Play Store",
                history=("Type Play Store.", "Tap “Search” of the store."), install="v107d")
assert len(calls) == 2 and "No text box is open" in json.dumps(calls[1]["messages"]), len(calls)
assert r["label"] == "Search", r

# 4. Staged
for rule in ("store_ads", "no_box_typing"):
    main._launch["live"][main.STAGED[rule]] = time.time()
r, _ = step([ans("Tap “Install”.", label="Install")], WA, "Install WhatsApp from the Play Store", tester="", install="v107e")
assert r["label"] == "Install", r
assert main.STAGED["store_ads"] == "1.07" and main.SERVER_VERSION >= "1.07"
print("Play Store: never the Install of a Sponsored app; Google Forms is a website; no 'keep typing' without a box ok")
