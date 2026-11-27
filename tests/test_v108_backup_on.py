import os, asyncio, json, time
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run

# #109, #110 (the owner's Infinix phone, 27 Nov, "Turn on backup in the Photos app"). Google Photos' account menu shares no
# words, so the AI looked at a picture: "Backup already shows complete. To check it, tap “Photos settings”." It went on
# round the menus to check (Help twice), and on the Backup page ("Backup is on", its switch on) the guide ended with
# "✔ Tap the back arrow to go back." When the backup is on, the guide ends saying so; and a finished guide never sends the
# person back.


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


def ans(say, done=False, x=None, y=None, label=None):
    return json.dumps({"label": label, "say": say, "done": done, "x": x, "y": y, "look_for": None})


IMG = "A" * 2000
GOAL = "Turn on backup in the Photos app"
TOLD = ["Tap “Photos”.", "Tap your profile picture at the top of the screen.",
        "Tap your round profile picture. It is a small circle with your photo or letter."]
# The report's step 6: Google Photos' Backup page ("…" are words the report leaves out)
BACKUP_PAGE = ["… [text]", "… [text]", "Backup is on [switch on]", "… [text]", "… [tap]", "… [tap]", "Navigate up [tap]",
               "Backup settings [text]"]
SAID = "Backup already shows complete. To check it, tap “Photos settings”."


def step(outs, labels=(), goal=GOAL, tester="1", install="v108", image="", lang="en", told=TOLD):
    main._claude_client = Client(outs)
    b = main.Next(goal=goal, labels=list(labels), lang=lang, history=list(told), image=image)
    r = run(main.next_step(b, x_app_token="tok", x_install_id=install, x_tester=tester))
    return r, main._claude_client.messages.calls


# 1. The report's step 3: no words, a picture; the AI read "Backup complete" in it. The guide ends: backup is on.
r, calls = step([ans(SAID, x=0.5, y=0.96)], image=IMG)
assert r["done"] is True and r["say"] == main._BACKED_UP_SAY and r["label"] is None, r
assert r["say"] == "Backup is on. Your photos are backed up."
# 2. The report's step 6: the Backup page, its switch on; the AI said done with "Tap Navigate up to go back"
r, calls = step([ans("Tap “Navigate up” to go back.", done=True, label="Navigate up")], BACKUP_PAGE, install="v108b")
assert r["done"] is True and r["say"] == main._BACKED_UP_SAY and r["label"] is None, r
# ...and the same page when the AI has not said done yet
r, calls = step([ans("Tap “Navigate up”.", label="Navigate up")], BACKUP_PAGE, install="v108c")
assert r["done"] is True and r["say"] == main._BACKED_UP_SAY, r

# 3. Not when backup is off, or not complete, or the goal is to turn it off
r, calls = step([ans("Tap the switch to turn Backup on.", label="Backup is off")],
                [l.replace("Backup is on [switch on]", "Backup is off [switch off]") for l in BACKUP_PAGE], install="v108d")
assert r["done"] is False and r["label"] == "Backup is off", r
for say in ("Backup is not complete yet. Tap “Photos settings”.", "Backup is off. Tap “Photos settings”.",
            "Backing up 3 photos. Wait a moment."):
    r, calls = step([ans(say, x=0.5, y=0.9)], image=IMG, install="v108e" + str(len(say)))
    assert r["done"] is False, (say, r)
r, calls = step([ans("Tap the switch to turn Backup off.", label="Backup is on")], BACKUP_PAGE, goal="Turn off backup in Photos",
                install="v108f")
assert r["done"] is False and r["label"] == "Backup is on", r
# Another goal on the same screen: as before
r, calls = step([ans("Tap “Navigate up”.", label="Navigate up")], BACKUP_PAGE, goal="Change my profile picture", install="v108g")
assert r["done"] is False, r

# 4. Any goal: a finished guide never says "go back" (it says it is done)
SETTINGS = ["Dark theme [switch on]", "Navigate up [tap]", "Display [text]"]
r, calls = step([ans("Dark theme is on. Tap “Navigate up” to go back.", done=True, label="Navigate up")], SETTINGS,
                goal="Turn on dark mode", install="v108h", told=["Tap “Display”."])
assert r["done"] is True and r["label"] is None and r["say"] == main._DONE_SAY["en"], r
r, calls = step([ans("Dark theme is on. Well done!", done=True)], SETTINGS, goal="Turn on dark mode", install="v108i",
                told=["Tap “Display”."])
assert r["say"] == "Dark theme is on. Well done!", r   # a done sentence that sends nobody back stays
r, calls = step([ans("Tap “Navigate up” to go back.", label="Navigate up")], SETTINGS, goal="Turn on dark mode",
                install="v108j", told=["Tap “Display”."])
assert r["done"] is False and r["label"] == "Navigate up", r   # not done: going back can be the way

# 5. Staged: before 24 quiet hours, other phones get the answer as it was.
for rule in ("backup_on", "done_not_back"):
    main._launch["live"][main.STAGED[rule]] = time.time()
r, calls = step([ans("Tap “Navigate up” to go back.", done=True, label="Navigate up")], BACKUP_PAGE, tester="", install="v108k")
assert r["done"] is True and r["say"] != main._BACKED_UP_SAY, r
assert main.STAGED["backup_on"] == "1.08" and main.STAGED["done_not_back"] == "1.08" and main.SERVER_VERSION >= "1.08"
print("backup on: ends saying the backup is on (switch on, or read in a picture); a finished guide never says go back ok")
