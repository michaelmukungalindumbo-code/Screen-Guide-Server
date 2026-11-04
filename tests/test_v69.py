import os, asyncio, json, time as _time
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run

# A pretend clock: each AI answer takes 8 seconds, without the test waiting for them
class Clock:
    now = _time.time()
    def time(self): return Clock.now
    def __getattr__(self, k): return getattr(_time, k)
main.time = Clock()

class Msgs:
    def __init__(self, out): self.out = list(out); self.calls = []
    async def create(self, **kw):
        self.calls.append(kw); Clock.now += 8
        class U: input_tokens = 900; output_tokens = 40
        class B: type = "text"; text = self.out.pop(0)
        class M: content = [B()]; usage = U(); stop_reason = "end_turn"
        return M()
class Client:
    def __init__(self, out): self.messages = Msgs(out)
def J(label, say, done=False): return json.dumps({"label": label, "say": say, "done": done, "x": None, "y": None, "look_for": None})
def step(outs, labels, h, goal="Turn on mobile data", **kw):
    main._claude_client = Client(outs)
    r = run(main.next_step(main.Next(goal=goal, labels=labels, **kw), **h))
    return r, main._claude_client.messages.calls

# #20, 3 Nov: "Turn on mobile data" from the home screen. Step 1 took 16 s on the server and 41 s on the phone, and nobody
# could tell where the time went. The answer was a swipe ("Swipe down from the top ... to open the quick settings panel"):
# when the AI also named a button, the server asked it a second time ("... is not on this screen"), which doubles the
# wait and makes no sense for a swipe.
HOME = ["… [text]", "… [tap]", "Messages [tap]", "… [tap]", "… [tap]", "WhatsApp [tap]", "Camera [tap]", "Phone [tap]",
        "07:31 [tap]", "… [tap]", "… [tap]", "… [tap]"]
SWIPE = "Swipe down from the top of the screen to open the quick settings panel."
H = dict(x_app_token="tok", x_install_id="dev68", x_tester="1")
run(main.event(main.Event(event="start", guide="ai"), **H))
for named in ("Quick settings", "Mobile data", "Settings"):
    r, calls = step([J(named, SWIPE), J(named, SWIPE)], HOME, H)
    assert len(calls) == 1, (named, len(calls))                     # a swipe is not a missing button: asked once
    assert r["say"] == SWIPE and r["label"] is None, r
r, calls = step([J("Mobile Data", "Scroll down, then tap “Mobile Data”."), J("Mobile Data", "x")], HOME, H)
assert len(calls) == 1                                               # off screen until they scroll: also asked once
# Still asked again for a real missing button (3 Nov, YouTube: "Tap Next" where there is only "Upload Short")
DETAILS = ["Add details [text]", "Caption your Short [text]", "Visibility [text]", "Unlisted [text]", "Select audience [tap]",
           "Show more [tap]", "Upload Short [tap]"]
r, calls = step([J("Next", "Tap “Next” to go on."), J("Upload Short", "Tap “Upload Short”.")], DETAILS, H, goal="Upload a video in the YouTube app")
assert len(calls) == 2 and r["label"] == "Upload Short", r

# Where the time went, for every step: how many times the AI was asked and why, and how long the server had been up.
H2 = dict(H, x_install_id="dev68b")
run(main.event(main.Event(event="start", guide="ai"), **H2))
main.STARTED = Clock.now - 20                                        # the server had just woken up
r, calls = step([J("Next", "Tap “Next” to go on."), J("Next", "Tap “Next”.")], DETAILS, H2, goal="Upload a video in the YouTube app")
st = main._sessions["dev68b"]["steps"][0]
assert st["secs"] == 16 and st["ai_calls"] == 2 and st["again"] == ["the button it named was not on the screen"], st
assert 15 <= st["up"] <= 25, st
slow = [p for p in main._sessions["dev68b"]["problems"] if p["kind"] == "slow"]
assert len(slow) == 1 and slow[0]["secs"] == 16, slow
card = main._rule_card(slow[0])
assert "asked the AI 2 times" in card["what"] and "not on the screen" in card["what"], card
# Then the phone says it waited 41 s: the same problem, now with the phone's time and where the rest went
run(main.watch_slow(main.WatchSlow(step=1, ms=41200), **H2))
slow = [p for p in main._sessions["dev68b"]["problems"] if p["kind"] == "slow"]
assert len(slow) == 1 and slow[0]["secs"] == 41, slow
card = main._rule_card(slow[0])
assert card["what"].startswith("The answer to step 1 took 41 seconds"), card
assert "server's own part was 16 seconds" in card["what"] and "waking up" in card["what"], card
title, body = main._watch_issue(main._sessions["dev68b"], card)
assert "16.0s (the phone waited 41s; the AI was asked 2 times)" in body, body[:1500]

# A server that has been up for an hour: the rest was the network. One slow AI answer: the AI itself was slow.
H3 = dict(H, x_install_id="dev68c")
run(main.event(main.Event(event="start", guide="ai"), **H3))
main.STARTED = Clock.now - 3600
class SlowMsgs(Msgs):
    async def create(self, **kw):
        Clock.now += 5; return await super().create(**kw)
main._claude_client = Client([J("Upload Short", "Tap “Upload Short”.")]); main._claude_client.messages = SlowMsgs([J("Upload Short", "Tap “Upload Short”.")])
run(main.next_step(main.Next(goal="Upload a video in the YouTube app", labels=DETAILS), **H3))
run(main.watch_slow(main.WatchSlow(step=1, ms=30000), **H3))
card = main._rule_card([p for p in main._sessions["dev68c"]["problems"] if p["kind"] == "slow"][0])
assert "the network" in card["what"] and "waking" not in card["what"], card
assert "The AI took 13 seconds for its one answer" in card["what"], card
# Quick steps get no timing words at all
H4 = dict(H, x_install_id="dev68d")
run(main.event(main.Event(event="start", guide="ai"), **H4))
step([J("Upload Short", "Tap “Upload Short”.")], DETAILS, H4, goal="Upload a video in the YouTube app")
assert not main._sessions["dev68d"]["problems"]
assert main.SERVER_VERSION >= "0.69"
print("slow steps explained, no second try for swipes")
