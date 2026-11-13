import os, asyncio, json, time
os.environ.update(ADMIN_KEY="k")
import main
# 0.96: these checks are for the fast AI at these moments; with "careful" on, test_v96_careful checks the stronger one
main._launch["paused"]["careful"] = "Paused in this test"
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
def A(text): return json.dumps({"kind": "answer", "text": text, "goal": "", "plan": [], "needs_apps": False})
main.settings.ANTHROPIC_API_KEY = main.settings.ANTHROPIC_API_KEY or "test"

# The owner (10 Nov), "task prediction": "...to determine whether to use a model that thinks harder or not depending on
# the complexity of the task". Until now only follow-ups went to the stronger AI; a first question always went to the
# fast one, however hard. Now a first question that is hard (something is wrong, several things at once, a choice, or
# long) goes to the stronger AI; an easy one stays with the fast one. Only the finished question is ever looked at.
EASY = ["How do I turn on Wi-Fi?", "Open WhatsApp", "How do I take a screenshot", "What is a PDF?", "Send a photo on WhatsApp",
        "How do I make the words bigger", "why"]
HARD = {"Why does my phone keep saying storage is full when I deleted my photos?": "something is wrong",
        "My WhatsApp is not working, messages are not sending": "something is wrong",
        "I can't hear people when they call me": "something is wrong",
        "How do I scan my certificates and then send them to my email as one file": "several things at once",
        "What is the difference between Drive and Photos?": "a choice",
        "Which is better for my child, YouTube or YouTube Kids": "a choice",
        "I bought a new phone and I want to move all my contacts and my WhatsApp chats and my photos from the old phone to this new one without losing anything": "long"}
for q in EASY:
    assert main._hard(q) == "", (q, main._hard(q))
for q, why in HARD.items():
    assert main._hard(q) == why, (q, main._hard(q))
assert main._hard("") == "" and main._hard("?? !!") == ""

def model(q, tester=True, hist=()):
    main._claude_client = Client([A("ok")] * 2); main._TALLY.set(None)
    run(main._answer(q, "en", [], list(hist), tester=tester))
    return main._claude_client.messages.calls[0]["model"]

h0, f0, s0 = main.STATS["chat_hard_first"], main.STATS["chat_fast"], main.STATS["chat_strong"]
assert model("How do I turn on Wi-Fi?") != main.STRONG_MODEL                      # easy: the fast one
assert model("My WhatsApp is not working, messages are not sending") == main.STRONG_MODEL   # hard: the stronger one
assert main.STATS["chat_hard_first"] == h0 + 1
assert main.STATS["chat_fast"] == f0 + 1 and main.STATS["chat_strong"] == s0 + 1  # each model's use is counted
# A follow-up: the stronger one, as before (and counted)
assert model("And the colour?", hist=["User: How do I set up WhatsApp?", "Helper: Open WhatsApp."]) == main.STRONG_MODEL
assert main.STATS["chat_strong"] == s0 + 2 and main.STATS["chat_hard_first"] == h0 + 1

# Users' phones: only after the rule's quiet hours (staged)
main._launch["live"][main.STAGED["hard_first"]] = time.time()
assert model("My WhatsApp is not working, messages are not sending", tester=False) != main.STRONG_MODEL      # not yet
main._launch["live"][main.STAGED["hard_first"]] = time.time() - 25 * 3600
assert model("My WhatsApp is not working, messages are not sending", tester=False) == main.STRONG_MODEL
# The day's limit holds for these too
main._strong_chat_day[main._today()] = main.STRONG_CHATS_PER_DAY
assert model("My WhatsApp is not working, messages are not sending") != main.STRONG_MODEL
main._strong_chat_day[main._today()] = 0
assert main.STAGED["hard_first"] == "0.86" and main.SERVER_VERSION >= "0.86"
import inspect
assert "x_tester" in inspect.signature(main.ask).parameters                       # test phones get it at once
print("a hard first question goes to the stronger AI, an easy one to the fast one; each use is counted")
