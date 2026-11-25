import os, asyncio, json, time
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run

# The owner's phone, 25 Nov ("How do I back up my photos?", step 4): "Tap "Navigate up" to go back." with the ring on the back
# arrow. Issue #97 (an idea he allowed): words like "Navigate up" are unclear to a first-time user. Taught guides say "Tap the
# back arrow." since app 0.130; the Smart guide's words now do too. The ring stays on the button. English only.


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


VIEWER = ["Navigate up [tap]", "Nov 20 [text]", "Favourite [tap]", "More options [tap]", "Share [tap]", "Edit [tap]", "Delete [tap]"]


def step(label, say, tester="1", install="v104", lang="en", labels=VIEWER):
    main._claude_client = Client([json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})])
    b = main.Next(goal="Back up my photos", labels=list(labels), lang=lang, history=["Tap “Photos”."])
    return run(main.next_step(b, x_app_token="tok", x_install_id=install, x_tester=tester))


# The pure rule
assert main._plain_icons("Tap \"Navigate up\" to go back.", "Navigate up") == "Tap the back arrow to go back."
assert main._plain_icons("Tap “Navigate up” to go back.", "Navigate up") == "Tap the back arrow to go back."
assert main._plain_icons("Tap the Navigate up arrow to go back.", "Navigate up") == "Tap the back arrow to go back."
assert main._plain_icons("Tap “More options”.", "More options") == "Tap the three dots."
assert main._plain_icons("Tap “Share”.", "Share") == "Tap “Share”."            # ordinary names stay

# Through next_step: the words change, the ring stays on the button
r = step("Navigate up", "Tap \"Navigate up\" to go back.")
assert r["say"] == "Tap the back arrow to go back." and r["label"] == "Navigate up", r
# Nyanja: no new words; Bemba likewise
r = step("Navigate up", "Dinani “Navigate up”.", lang="ny", install="v104b")
assert r["say"] == "Dinani “Navigate up”.", r
# Staged: other phones after 24 quiet hours
main._launch["live"][main.STAGED["plain_icons"]] = time.time()
r = step("Navigate up", "Tap \"Navigate up\" to go back.", tester="", install="v104c")
assert r["say"] == "Tap \"Navigate up\" to go back.", r
assert main.STAGED["plain_icons"] == "1.04" and main.SERVER_VERSION >= "1.04"
print("plain words for icons in the Smart guide: the back arrow, the three dots ok")
