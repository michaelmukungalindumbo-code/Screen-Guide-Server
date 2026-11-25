import os, asyncio, json, time
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run

# The owner's Infinix phone, 25 Nov: "How do I back up my photos?", then Show me (plan: Open the Photos app | Tap your
# profile picture at the top | Tap Photos settings | Tap Backup | Turn on Backup). As soon as Google Photos opened, the card
# said "Tap the photo you want.", again and again, Help included. Google Photos' main screen is a grid of the person's
# photos, so the rule for choosing one of your own photos (to send or upload) replaced "Tap your profile picture": the word
# "picture" counted as choosing a photo. Then "Backup complete" and "1,310 photos backed up" were on the screen, and the
# guide still did not end. Backing up is not choosing a photo; and when the screen says the backup is done, it is done.


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


def ans(say, label=None, done=False):
    return json.dumps({"label": label, "say": say, "done": done, "x": None, "y": None, "look_for": None})


PLAN = ["Open the Photos app", "Tap your profile picture at the top", "Tap Photos settings", "Tap Backup", "Turn on Backup"]
# Google Photos' main screen (button names as Google Photos gives them; the photos are named by when they were taken)
PHOTOS = ["Backup complete [tap]", "Create [tap]", "Notifications [tap]", "Account and settings [tap]", "Best of October [text]",
          "Photo taken on Nov 20, 2026 9:48:12 AM [tap]", "Photo taken on Nov 19, 2026 4:02:51 PM [tap]",
          "Photo taken on Nov 18, 2026 11:20:05 AM [tap]", "Photos [selected]", "Collections [tap]", "Ask Photos [tap]"]
BACKED = ["1,310 photos backed up [text]", "Stay in the loop about backup [text]", "Turn on notifications [tap]",
          "Photo taken on Nov 20, 2026 9:48:12 AM [tap]", "Photos [selected]", "Collections [tap]"]


def step(outs, labels, goal="How do I back up my photos?", tester="1", install="v102", history=("Tap “Photos”.",)):
    main._claude_client = Client(outs)
    b = main.Next(goal=goal, labels=list(labels), lang="en", history=list(history), plan=PLAN)
    return run(main.next_step(b, x_app_token="tok", x_install_id=install, x_tester=tester))


# 1. Step 2 of the recording (Photos had just opened; its "Backup complete" button was not showing yet): the AI's own
#    step stands, not "Tap the photo you want."
OPENED = PHOTOS[1:]
r = step([ans("Tap your profile picture at the top.")], OPENED)
assert r["say"] != "Tap the photo you want." and "profile picture" in r["say"] and not r["done"], r
r = step([ans("Tap your profile picture.", label="Account and settings")], OPENED, install="v102b")
assert r["label"] == "Account and settings" and r["say"] != "Tap the photo you want.", r

# 2. Choosing a photo to send or upload still gets the choosing sentence, as before
r = step([ans("Tap the photo you want to send.")], OPENED, goal="Send a photo on WhatsApp", install="v102c")
assert r["say"] == "Tap the photo you want.", r

# 3. "Backup complete" or "1,310 photos backed up" on the screen: a backup goal is done
r = step([ans("Tap the photo you want.")], BACKED, install="v102d")
assert r["done"] is True and r["say"] == main._BACKED_UP_SAY and r["label"] is None, r
r = step([ans("Tap your profile picture.", label="Account and settings")], PHOTOS, install="v102e")
assert r["done"] is True and r["say"] == "Your photos are backed up.", r
# ...but not for another goal on the same screen, and never when the screen says the backup is off
r = step([ans("Tap the photo you want to send.")], BACKED, goal="Send a photo on WhatsApp", install="v102f")
assert r["done"] is False, r
r = step([ans("Tap “Backup is off”.", label="Backup is off")], ["Backup is off [tap]"] + PHOTOS[1:], install="v102g")
assert r["done"] is False, r

# 4. Staged: test phones at once, everyone else after 24 quiet hours (until then, as before)
for rule in ("backup_goal",):
    main._launch["live"][main.STAGED[rule]] = time.time()
r = step([ans("Tap your profile picture at the top.")], PHOTOS, tester="", install="v102h")
assert r["say"] == "Tap the photo you want." and not r["done"], r
assert main.STAGED["backup_goal"] == main.SERVER_VERSION == "1.02"
print("backing up photos: not choosing a photo; done when the screen says the backup is complete ok")
