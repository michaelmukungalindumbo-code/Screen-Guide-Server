import os, asyncio, json, time
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
def J(label, say, done=False): return json.dumps({"label": label, "say": say, "done": done, "x": None, "y": None, "look_for": None})
main.settings.ANTHROPIC_API_KEY = main.settings.ANTHROPIC_API_KEY or "test"

# #41 step 10 (the owner's YouTube upload test, 7 Nov): on YouTube's editor, whose way on has no words, the guide said
# "Tap “Done” to finish picking your video." with nothing pointed at, even after asking the AI again. Never tell people to
# tap what is not on the screen: say so, and look at a picture of the screen next (if they allowed screen pictures).
GOAL = "Upload a video in the YouTube app"
EDITOR = ["… [tap]", "… [tap]", "… [tap]", "Filters [tap]", "… [tap]", "… [tap]", "… [tap]", "… [text]", "… [text]",
          "Filters [text]", "… [text]", "… [text]", "More [text]"]
DONE = J("Done", "Tap “Done” to finish picking your video.")
def step(labels, out, i="dev84m", tester=True):
    main._claude_client = Client(out)
    r = run(main.next_step(main.Next(goal=GOAL, labels=labels), x_app_token="tok", x_install_id=i, x_tester="1" if tester else ""))
    return r, main._claude_client.messages.calls

r, calls = step(EDITOR, [DONE, DONE])
assert len(calls) == 2, len(calls)                                    # asked again, as before
assert r["label"] is None and "Tap “Done”" not in r["say"], r
assert r["say"].startswith("I can’t see “Done” on this screen."), r["say"]
assert r["need_picture"] is True                                      # the phone looks at a picture next, if allowed
assert main.STATS["missing_button_picture"] >= 1

# The second answer found a real button: it is used, as before
r, calls = step(EDITOR, [DONE, J("Filters", "Tap “Filters”.")])
assert r["label"] == "Filters" and r["need_picture"] is False, r

# Users' phones: only after the rule's quiet hours (staged)
main._launch["live"][main.STAGED["missing_button_picture"]] = time.time()
r, calls = step(EDITOR, [DONE, DONE], i="user84m", tester=False)
assert r["say"] == "Tap “Done” to finish picking your video.", r    # not yet
main._launch["live"][main.STAGED["missing_button_picture"]] = time.time() - 25 * 3600
r, calls = step(EDITOR, [DONE, DONE], i="user84m2", tester=False)
assert r["say"].startswith("I can’t see “Done”") and r["need_picture"] is True, r
assert main.STAGED["missing_button_picture"] == "0.84"
print("a button that is not on the screen is never the instruction: said so, and a picture looked at next")
