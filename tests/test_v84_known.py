import os, asyncio, json, time
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run
class Msgs:
    def __init__(self, out): self.out = list(out); self.calls = []
    async def create(self, **kw):
        self.calls.append(kw)
        class U: input_tokens = 900; output_tokens = 40
        class B: type = "text"; text = self.out.pop(0)   # the AI asked when it should not be: no answer left, the test fails
        class M: content = [B()]; usage = U(); stop_reason = "end_turn"
        return M()
class Client:
    def __init__(self, out): self.messages = Msgs(out)
def J(label, say, done=False): return json.dumps({"label": label, "say": say, "done": done, "x": None, "y": None, "look_for": None})
main.settings.ANTHROPIC_API_KEY = main.settings.ANTHROPIC_API_KEY or "test"

# v0.84, the owner's list (7 Nov): "reuse answers that worked" and "app maps". The screens of his "Turn on Hotspot" test
# (Infinix): Settings, then Hotspot & Connections. Personal words are "…".
GOAL = "Turn on Hotspot"
SETTINGS = ["… [tap]", "My Phone [tap]", "SIM & Network Settings [tap]", "Wi-Fi [tap]", "Bluetooth [tap]",
            "Hotspot & Connections [tap]", "Personalization [tap]"]
HOTSPOT = ["Navigate up [tap]", "Airplane mode [switch]", "Tethering [text]", "Personal Hotspot [tap]", "USB tethering [switch]",
           "Bluetooth tethering [switch]", "VPN [tap]", "Private DNS [tap]"]
TAP_HC = J("Hotspot & Connections", "Tap “Hotspot & Connections”.")
TAP_PH = J("Personal Hotspot", "Tap “Personal Hotspot”.")
def step(labels, out, i="dev84", tester=True, followed=False, stuck=False, path=None, note="", goal=GOAL):
    main._claude_client = Client(out)
    r = run(main.next_step(main.Next(goal=goal, labels=labels, followed=followed, stuck=stuck, path=path or [], note=note),
                           x_app_token="tok", x_install_id=i, x_tester="1" if tester else ""))
    return r, main._claude_client.messages.calls

# 1. A test phone: the AI answers; the person taps it (the next step says followed); then the same screen and goal again
#    gets the same answer at once, with no AI
r, calls = step(SETTINGS, [TAP_HC])
assert r["label"] == "Hotspot & Connections" and len(calls) == 1
r, calls = step(HOTSPOT, [TAP_PH], followed=True)          # they tapped it: learned
assert len(calls) == 1 and main.STATS["known_learned"] >= 1
r, calls = step(SETTINGS, [])                              # a new guide on the same screen: no AI at all
assert r["label"] == "Hotspot & Connections" and r["say"] == "Tap “Hotspot & Connections”." and calls == [], (r, calls)
assert main.STATS["known_used"] >= 1

# 2. Not when they asked for help, or wrote to it, or with a picture: the AI is asked
r, calls = step(SETTINGS, [J("Wi-Fi", "Tap “Wi-Fi”.")], stuck=True)
assert len(calls) == 1
r, calls = step(SETTINGS, [TAP_HC], note="I can't find it")
assert len(calls) == 1

# 3. Help right after it counts against it: once the bad outweigh the good, the AI is asked again
main._known["k"].clear(); main._known["s"].clear(); main._known_pending.clear()
step(SETTINGS, [TAP_HC], i="dev84b"); step(HOTSPOT, [TAP_PH], i="dev84b", followed=True)
r, calls = step(SETTINGS, [], i="dev84b"); assert calls == []
step(HOTSPOT, [J("Personal Hotspot", "Tap “Personal Hotspot”.")], i="dev84b", stuck=True)   # Help right after it
r, calls = step(SETTINGS, [TAP_HC], i="dev84b"); assert len(calls) == 1, "one good, one bad: asked again"

# 4. Its button must be on this screen
main._known["k"].clear(); main._known_pending.clear()
step(SETTINGS, [TAP_HC], i="dev84c"); step(HOTSPOT, [TAP_PH], i="dev84c", followed=True)
r, calls = step([l for l in SETTINGS if not l.startswith("Hotspot")], [J(None, "Scroll down to find Hotspot & Connections.")], i="dev84c")
assert len(calls) == 1

# 5. A personal word is never kept ("Mum" is no common button name): nothing learned, the AI asked every time
main._known["k"].clear(); main._known_pending.clear()
CHATS = ["Chats [selected]", "Mum [tap]", "… [tap]", "New chat [tap]"]
step(CHATS, [J("Mum", "Tap “Mum”.")], i="dev84d", goal="Send a photo to Mum on WhatsApp")
step(["Message [typing]", "Attach [tap]"], [J("Attach", "Tap “Attach”.")], i="dev84d", goal="Send a photo to Mum on WhatsApp", followed=True)
assert not main._known["k"], main._known["k"]
doc = json.dumps(main._known)
assert "Mum" not in doc and "dev84" not in doc        # no personal words, no phone ids
# ... and a name inside the AI's words is replaced by the plain instruction
assert main._known_say("Tap “Personal Hotspot” to share with John.", "Personal Hotspot", "en") == "Tap “Personal Hotspot”."
assert main._known_say("Tap “Personal Hotspot”. Then tap the switch.", "Personal Hotspot", "en") in (
    "Tap “Personal Hotspot”. Then tap the switch.", "Tap “Personal Hotspot”.")

# 6. Users' phones: only once 2 different phones followed it, and only after the rule's quiet hours (staged)
main._known["k"].clear(); main._known["s"].clear(); main._known_pending.clear()
main._launch["live"][main.STAGED["known_screens"]] = time.time() - 25 * 3600
step(SETTINGS, [TAP_HC], i="user1", tester=False); step(HOTSPOT, [TAP_PH], i="user1", tester=False, followed=True)
r, calls = step(SETTINGS, [TAP_HC], i="user2", tester=False)
assert len(calls) == 1, "one phone is not enough for users"
step(HOTSPOT, [TAP_PH], i="user2", tester=False, followed=True)
r, calls = step(SETTINGS, [], i="user3", tester=False)
assert calls == [] and r["label"] == "Hotspot & Connections"
main._launch["live"][main.STAGED["known_screens"]] = time.time()     # just went live: not yet for users
r, calls = step(SETTINGS, [TAP_HC], i="user4", tester=False)
assert len(calls) == 1

# 7. App maps: what people tapped on this screen goes to the AI as a hint (<often>), for another goal too
main._launch["live"][main.STAGED["known_screens"]] = time.time() - 25 * 3600
r, calls = step(SETTINGS, [J("Bluetooth", "Tap “Bluetooth”.")], i="user5", tester=False, goal="Turn on Bluetooth")
asked = str(calls[0]["messages"][0]["content"])
assert "<often>“Hotspot & Connections” (2)</often>" in asked, asked[-400:]

# 8. Breadcrumbs: where they have been, in common button names only
r, calls = step(HOTSPOT, [TAP_PH], i="dev84e", path=["Home screen", "Settings", "Settings", "Hotspot & Connections", "Mum"])
asked = str(calls[0]["messages"][0]["content"])
assert "<path>Settings › Hotspot & Connections</path>" in asked   # ">" is made safe inside a tag and "Mum" not in asked.split("<path>")[1].split("</path>")[0], asked[-300:]
assert main._trail(["Mum", "…"]) == []

# 9. Kept across restarts (the free server sleeps): saved, then read back
main._known_state["dirty"] = True
run(main._known_save(force=True))
saved = json.loads(json.dumps(main._known))
main._known["k"].clear(); main._known["s"].clear(); main._known_state["loaded"] = False
run(main._known_load())
assert main._known == saved and main._known["k"]

assert main.STAGED["known_screens"] == "0.84" and main.SERVER_VERSION >= "0.84" and main.PROMPT_VERSION >= "60"
assert "<path> is where the person has been" in main.NEXT_SYSTEM and "<often> is what other people tapped" in main.NEXT_SYSTEM
print("an answer people followed comes again without the AI; what they tapped is a hint; where they have been goes with it")
