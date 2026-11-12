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

# The owner's phone (13 Nov, Infinix, 0.120). He asked about an app's "Failed to load app" error, with a picture, then
# "Show me". The guide's goal was "Fix a web app error by checking internet and reopening the app": it went to Settings,
# Wi-Fi, and said "Tap the switch next to Wi-Fi to turn it on." on step after step (his phone was online on mobile data,
# and Wi-Fi went on and off), then "Tap the Navigate up arrow", then the Wi-Fi switch again. Stopped at step 10, never
# back in the app. The watcher: "Same instruction three times" (twice), "Back instruction before goal done".
GOAL = "Fix a web app error by checking internet and reopening the app"
WIFI_ON = ["Navigate up [tap]", "Wi-Fi [switch on]", "Network Assistant [tap]", "More Settings [tap]", "Wi-Fi Networks [text]", "Add Network [tap]"]
WIFI_OFF = [l.replace("[switch on]", "[switch off]") for l in WIFI_ON]
HIST = ["Tap “Settings” to check your internet first.", "Tap “Wi-Fi” to check your internet connection."]
TURN_ON = "Tap the switch next to Wi-Fi to turn it on."
def step(labels, out, goal=GOAL, hist=HIST, i="dev95", tester=True):
    main._claude_client = Client(out)
    r = run(main.next_step(main.Next(goal=goal, labels=labels, history=hist, path=["Settings", "Wi-Fi"]),
                           x_app_token="tok", x_install_id=i, x_tester="1" if tester else ""))
    return r, main._claude_client.messages.calls

# The prompts: switch states, and the phone is online during a guide
S = main.NEXT_SYSTEM
assert "[switch on] and [switch off] mean its row has an on/off switch, and whether it is on or off now" in S
assert "Never ask them to turn on a [switch on] or to turn off a [switch off]" in S
assert "The phone is online while a guide runs" in S and "Never ask them to turn Wi-Fi or mobile data on or off" in S
C = main.SYSTEM
assert "the phone's internet is working, because this chat needs it" in C
assert "never make checking or turning on Wi-Fi or mobile data a step" in C
assert C.index("tap Retry, or reload the page, in that same app") < C.index("close that app fully and open it again")
assert "the goal names that app" in C

# The new tags are read like the old ones
assert main._plain("Wi-Fi [switch on]") == "Wi-Fi" and main._plain("Bluetooth [switch off]") == "Bluetooth" and main._plain("Wi-Fi [switch]") == "Wi-Fi"
assert main._match_label("Wi-Fi", WIFI_ON) == "Wi-Fi" and main._match_label("Wi-Fi [switch on]", WIFI_ON) == "Wi-Fi"
assert main._switch_tag("Wi-Fi", WIFI_ON) == "on" and main._switch_tag("Wi-Fi", WIFI_OFF) == "off"
assert main._switch_tag("Wi-Fi", ["Wi-Fi [switch]"]) is None and main._switch_tag("Add Network", WIFI_ON) is None
# Which way the step or the goal wants it
assert main._already_switched("Wi-Fi", TURN_ON, GOAL, WIFI_ON) == ("Wi-Fi", "on")
assert main._already_switched("Wi-Fi", TURN_ON, GOAL, WIFI_OFF) is None                     # off: turning it on is right
assert main._already_switched("Wi-Fi", "Tap the switch.", "Turn on Wi-Fi", WIFI_ON) == ("Wi-Fi", "on")
assert main._already_switched("Wi-Fi", "Tap the switch.", "Turn Wi-Fi off", WIFI_OFF) == ("Wi-Fi", "off")
assert main._already_switched("Wi-Fi", "Tap the switch to turn Wi-Fi off.", "Turn off Wi-Fi", WIFI_ON) is None
assert main._already_switched(None, TURN_ON, GOAL, WIFI_ON) == ("Wi-Fi", "on")              # named only in the words
assert main._already_switched("Wi-Fi", "Tap “Wi-Fi” to see the networks.", "Turn on Wi-Fi", WIFI_ON) is None   # not about the switch
assert main._already_switched("Wi-Fi", TURN_ON, GOAL, [l.replace(" [switch on]", " [switch]") for l in WIFI_ON]) is None   # an older app: as before
assert main._only_switch("Turn on Wi-Fi", "Wi-Fi") and main._only_switch("Turn Wi-Fi on", "Wi-Fi") and main._only_switch("Switch on the Wi-Fi", "Wi-Fi")
assert not main._only_switch(GOAL, "Wi-Fi") and not main._only_switch("Turn on Wi-Fi and connect to my router", "Wi-Fi")

# His screen: Wi-Fi already on. The AI is asked once more, told so, and its next step is taken
n0 = main.STATS["switch_state_asked"]
r, calls = step(WIFI_ON, [J("Wi-Fi", TURN_ON), J("Navigate up", "Wi-Fi is on. Tap “Navigate up” to go back.")])
assert r["label"] == "Navigate up" and "turn it on" not in r["say"], r
assert len(calls) == 2 and "“Wi-Fi” is already on. Never ask them to tap its switch." in json.dumps(calls[1]["messages"], ensure_ascii=False)
assert "already on" not in json.dumps(calls[0]["messages"], ensure_ascii=False)
assert main.STATS["switch_state_asked"] == n0 + 1 and main.STATS["switch_state_fixed"] >= 1
# It says the same again: the step only says it is so, never a ring on the switch
r, calls = step(WIFI_ON, [J("Wi-Fi", TURN_ON), J("Wi-Fi", "Tap the switch to turn Wi-Fi on.")], i="dev95b")
assert r["label"] is None and r["say"] == "“Wi-Fi” is already on." and r["done"] is False, r
# When that was the whole goal, the guide ends
r, calls = step(WIFI_ON, [J("Wi-Fi", "Tap the switch."), J("Wi-Fi", "Tap the switch.")], goal="Turn on Wi-Fi", hist=["Tap “Wi-Fi”."], i="dev95c")
assert r["done"] is True and r["label"] is None, r
# Wi-Fi off and the goal is to turn it on: as before, one AI answer, the switch rung
r, calls = step(WIFI_OFF, [J("Wi-Fi", "Tap the switch.")], goal="Turn on Wi-Fi", hist=["Tap “Wi-Fi”."], i="dev95d")
assert r["label"] == "Wi-Fi" and len(calls) == 1, r
# Users' phones: staged
main._launch["live"][main.STAGED["switch_state"]] = time.time()
r, calls = step(WIFI_ON, [J("Wi-Fi", TURN_ON)], i="user95", tester=False)
assert r["label"] == "Wi-Fi" and len(calls) == 1, r                                   # not yet
main._launch["live"][main.STAGED["switch_state"]] = time.time() - 25 * 3600
r, calls = step(WIFI_ON, [J("Wi-Fi", TURN_ON), J("Navigate up", "Tap “Navigate up”.")], i="user95b", tester=False)
assert r["label"] == "Navigate up", r
assert main.STAGED["switch_state"] == "0.95" and main.SERVER_VERSION >= "0.95" and main.PROMPT_VERSION >= "66"
print("a switch already on is never turned on again; an error in an app is fixed in that app, never in Wi-Fi settings")
