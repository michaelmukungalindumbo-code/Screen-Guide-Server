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

# The owner (7 Nov): "What happens when you are using YouTube, and then an ad pops up?" The AI is told never to point at
# ads, but nothing made sure. On an ad that covers the screen, only its own "Skip ad" or "Close ad" is ever rung.
GOAL = "Watch a video about farming on YouTube"
AD = ["Ad · 0:15 [text]", "Visit advertiser [tap]", "Skip in 5 [text]", "Learn more [tap]", "Install [tap]"]
SKIP = ["Ad · 0:09 [text]", "Visit advertiser [tap]", "Skip ad [tap]", "Install [tap]"]
def step(labels, out, i="dev84o", tester=True):
    main._claude_client = Client(out)
    return run(main.next_step(main.Next(goal=GOAL, labels=labels), x_app_token="tok", x_install_id=i, x_tester="1" if tester else ""))

r = step(AD, [J("Install", "Tap “Install” to get the app.")])
assert r["label"] is None and r["say"].startswith("This is an ad. Wait a few seconds"), r
r = step(AD, [J("Visit advertiser", "Tap “Visit advertiser”.")])
assert r["label"] is None, r
r = step(SKIP, [J("Install", "Tap “Install”.")])
assert r["label"] == "Skip ad" and r["say"] == "This is an ad. Tap “Skip ad” to go on.", r
r = step(SKIP, [J("Skip ad", "Tap “Skip ad” to go back to your video.")])
assert r["label"] == "Skip ad", r                                      # already right: kept
assert main.STATS["ad_button_blocked"] >= 3

# A "Sponsored" post in a feed is not an ad covering the screen: the step goes on as usual
FEED = ["Sponsored [text]", "Like [tap]", "Comment [tap]", "Share [tap]", "Home [tap]", "Search [tap]"]
r = step(FEED, [J("Search", "Tap “Search”.")])
assert r["label"] == "Search", r

# Users' phones: after the rule's quiet hours (staged)
main._launch["live"][main.STAGED["ad_buttons"]] = time.time()
r = step(AD, [J("Install", "Tap “Install”.")], i="user84o", tester=False)
assert r["label"] == "Install", r                                      # not yet
main._launch["live"][main.STAGED["ad_buttons"]] = time.time() - 25 * 3600
r = step(AD, [J("Install", "Tap “Install”.")], i="user84o2", tester=False)
assert r["label"] is None and r["say"].startswith("This is an ad."), r
assert main.STAGED["ad_buttons"] == "0.84"
print("on an ad that covers the screen, only its own Skip ad or Close ad is ever rung")
