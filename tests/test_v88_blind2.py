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
def J(say): return json.dumps({"label": None, "say": say, "done": False, "x": None, "y": None, "look_for": None})
main.settings.ANTHROPIC_API_KEY = main.settings.ANTHROPIC_API_KEY or "test"

# The owner's phone (11 Nov, 0.113, the first test of the words-only step): on Drive's page AFTER the photo (Enhance,
# Filters, Next) the helper said "tap the round shutter button at the bottom to take a photo": the camera page's
# instruction, on the page after it. It cannot see which page this is, so the phone now says how many unseen screens
# have come in a row, and the helper is told that a second one is the page AFTER the one it last spoke about.
def sent(blind, hist):
    main._claude_client = Client([J("I can’t see this screen. Tap “Next” at the bottom right.")])
    r = run(main.next_step(main.Next(goal="Scan a document with the Drive app", labels=[], history=hist, path=["Drive"], blind=blind),
                           x_app_token="tok", x_install_id="dev88", x_tester="1"))
    m = main._claude_client.messages.calls[0]["messages"][0]["content"]
    return r, (m if isinstance(m, str) else " ".join(p.get("text", "") for p in m if isinstance(p, dict)))

r, p = sent(1, ["Tap “Scan” to start scanning."])
assert "<unseen_screens_in_a_row>1</unseen_screens_in_a_row>" in p
assert "the screen that usually comes AFTER" not in p
r, p = sent(2, ["Tap “Scan” to start scanning.", "I can’t see this screen. Tap the round button at the bottom to take the photo."])
assert "<unseen_screens_in_a_row>2</unseen_screens_in_a_row>" in p
assert "the screen that usually comes AFTER" in p and "Never repeat the instruction you gave for the screen before" in p
assert r["label"] is None and "Next" in r["say"], r
r, p = sent(0, [])                                                   # an older app that does not count: as 0.87
assert "<unseen_screens_in_a_row>" not in p and "ScreenGuide cannot read this screen" in p
r, p = sent(99, [])
assert "<unseen_screens_in_a_row>9</unseen_screens_in_a_row>" in p      # a number from outside is kept small
assert main.SERVER_VERSION >= "0.88"
print("unseen screens in a row: the second is the page after the one last spoken about, never the same instruction again")
