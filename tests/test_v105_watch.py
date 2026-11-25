import os, asyncio, json
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run

# The owner's phone, 25 Nov, his second "How do I back up my photos?": Google Photos showed "Backup complete" and the guide
# ended with "Your photos are backed up." (server 1.02). The watcher's AI review then reported "Says backup is done before any
# backup ... no backup setting visible": it never saw "Backup complete", because the watcher hides screen words it does not
# know (so that no personal words reach a report), and nothing told it why the guide ended. Now those words are known, the
# step says why the guide ended, and the person is told plainly that backup is on.


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


PHOTOS = ["Backup complete [tap]", "Create [tap]", "Notifications [tap]", "Account and settings [tap]",
          "Photo taken on Nov 20, 2026 9:48:12 AM [tap]", "Photos [selected]", "Collections [tap]"]

# 1. The words that show the backup's state are kept in reports; personal words are still hidden
for w in ("Backup complete", "Backup is off", "Account and settings", "Photos settings", "Turn on backup"):
    assert main._clean_word(w) == w, w
assert main._clean_word("Mum") == "…"

# 2. The guide ends on "Backup complete": the step says why, and the person hears that backup is on
main._sessions.clear()
main._claude_client = Client([json.dumps({"label": "Account and settings", "say": "Tap your profile picture.", "done": False,
                                          "x": None, "y": None, "look_for": None})])
r = run(main.next_step(main.Next(goal="How do I back up my photos?", labels=PHOTOS, lang="en", history=["Tap “Photos”."]),
                       x_app_token="tok", x_install_id="v105", x_tester="1"))
assert r["done"] is True and r["say"] == "Backup is on. Your photos are backed up." == main._BACKED_UP_SAY, r
st = main._sessions["v105"]["steps"][-1]
assert st["ended_by"] == "the screen said the backup is complete", st
assert "Backup complete [tap]" in st["screen"], st["screen"]
title, body = main._watch_issue(main._sessions["v105"], {"title": "t", "step": 1, "what": "w", "fix": "f"})[:2]
assert "ended because the screen said the backup is complete" in body, body[:900]
assert main.SERVER_VERSION >= "1.05"
print("the watcher sees why a backup guide ended, and the person hears that backup is on ok")
