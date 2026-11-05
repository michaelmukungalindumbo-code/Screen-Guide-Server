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
GOAL = "Open the WhatsApp Business app"
def step(labels, label, say, tester=True, i="dev78a", goal=GOAL):
    main._claude_client = Client([J(label, say)] * 3)
    return run(main.next_step(main.Next(goal=goal, labels=labels), x_app_token="tok", x_install_id=i, x_tester="1" if tester else ""))

# 5 Nov: on a phone without WhatsApp Business, the AI's "WhatsApp Business" was matched to "WhatsApp" on the screen (the
# shorter name fitted its start), and the ring sent the person into plain WhatsApp. A longer name of that kind is
# another app: WhatsApp Business, YouTube Kids, YouTube Music, YouTube Studio.
assert "longer_app_name" in main.STAGED
DRAWER = ["VidMate [tap]", "Weather [tap]", "WhatsApp [tap]", "XTheme [tap]", "YouTube [tap]"]
r = step(DRAWER, "WhatsApp Business", "Tap WhatsApp Business to open it.")
assert r["label"] is None, r                                                    # no ring on plain WhatsApp
r = step(DRAWER, None, "Tap WhatsApp Business.")
assert r["label"] is None, r                                                    # nor from the words
# Under its icon WhatsApp Business is "WA Business": that is the one
r = step(DRAWER + ["WA Business [tap]"], "WhatsApp Business", "Tap WhatsApp Business.")
assert r["label"] == "WA Business", r
r = step(["YouTube [tap]", "Gmail [tap]"], "YouTube Kids", "Tap YouTube Kids.", goal="Watch cartoons on YouTube Kids")
assert r["label"] is None, r
# Unchanged: a name the AI shortened or lengthened a little, the plain app itself, and Go or Lite (the same job)
r = step(DRAWER, "WhatsApp", "Tap WhatsApp.", goal="Send a photo on WhatsApp")
assert r["label"] == "WhatsApp", r
r = step(["Settings [tap]", "Facebook [tap]"], "Facebook Lite", "Tap Facebook Lite.", goal="Post on Facebook")
assert r["label"] == "Facebook", r
r = step(["Network & internet [tap]", "Apps [tap]"], "Network", "Tap Network & internet.", goal="Turn on Wi-Fi")
assert r["label"] == "Network & internet", r

# Staged
main._launch["live"][main.STAGED["longer_app_name"]] = main.time.time()
r = step(DRAWER, "WhatsApp Business", "Tap WhatsApp Business.", tester=False, i="user78a")
assert r["label"] == "WhatsApp", r                                              # not yet for users
main._launch["live"][main.STAGED["longer_app_name"]] -= 25 * 3600
r = step(DRAWER, "WhatsApp Business", "Tap WhatsApp Business.", tester=False, i="user78a")
assert r["label"] is None, r
assert main._launch["seen"]["longer_app_name"]["fired"] == 1
print("a longer app name is another app")
