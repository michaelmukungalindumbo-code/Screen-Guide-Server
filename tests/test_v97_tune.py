import os, asyncio, json, time
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run
class Msgs:
    def __init__(self, out): self.out = list(out); self.calls = []
    async def create(self, **kw):
        self.calls.append(kw)
        class U: input_tokens = 900; output_tokens = 60
        class B: type = "text"; text = self.out.pop(0)
        class M: content = [B()]; usage = U(); stop_reason = "end_turn"
        return M()
class Client:
    def __init__(self, out): self.messages = Msgs(out)
def J(label, say, done=False): return json.dumps({"label": label, "say": say, "done": done, "x": None, "y": None, "look_for": None})
main.settings.ANTHROPIC_API_KEY = main.settings.ANTHROPIC_API_KEY or "test"
APPS = ["Chrome", "Drive", "Settings", "WhatsApp", "AI Studio"]
def step(labels, hist, out, goal, path=(), i="dev97", tester=True):
    main._claude_client = Client(out)
    r = run(main.next_step(main.Next(goal=goal, labels=labels, history=hist, path=list(path), apps=APPS),
                           x_app_token="tok", x_install_id=i, x_tester="1" if tester else ""))
    return r, main._claude_client.messages.calls

# The owner (19 Nov): "use whatever I have been sending you to go through the code again and tune ScreenGuide".

# 1. The owner's phone (13 Nov, Infinix), step 4 of his "Show me" guide: "Tap the Navigate up arrow to go back." with the
# ring on "Wi-Fi". The words named one button and the AI's label another: the ring follows the words.
WIFI = ["Navigate up [tap]", "Wi-Fi [switch on]", "Network Assistant [tap]", "More Settings [tap]", "Add Network [tap]"]
GOAL = "Tap Retry in AI Studio"
r, calls = step(WIFI, ["Tap “Settings”.", "Tap “Wi-Fi”."], [J("Wi-Fi", "Tap the Navigate up arrow to go back.")], GOAL, ["Settings", "Wi-Fi"])
assert r["label"] == "Navigate up" and r["say"] == "Tap the Navigate up arrow to go back.", r
assert main.STATS["label_follows_words"] >= 1
# Words and label agree, or the words name no button on the screen: as before
r, calls = step(WIFI, ["Tap “Settings”."], [J("Navigate up", "Tap “Navigate up” to go back.")], GOAL, ["Settings", "Wi-Fi"], i="dev97a")
assert r["label"] == "Navigate up", r
r, calls = step(WIFI, ["Tap “Settings”."], [J("Wi-Fi", "Tap the switch next to Wi-Fi.")], "Turn off Wi-Fi", ["Settings", "Wi-Fi"], i="dev97b")
assert r["label"] == "Wi-Fi", r
# A choice ("or") keeps its own rules
assert main._label_from_say("Tap “Add Network”, or tap Navigate up.", WIFI) == "Add Network"
r, calls = step(WIFI, ["Tap “Settings”."], [J("Navigate up", "Tap “Add Network”, or tap Navigate up to go back.")], GOAL, ["Settings", "Wi-Fi"], i="dev97c")
assert r["label"] == "Navigate up", r

# 2. An option that is already chosen (#79 was a tab; Settings lists have them too): asked again, told so
TIMEOUT = ["Navigate up [tap]", "Screen timeout [text]", "15 seconds [tap]", "30 seconds [selected]", "1 minute [tap]", "2 minutes [tap]"]
assert main._already_chosen("30 seconds", "Tap “30 seconds”.", TIMEOUT) == "30 seconds"
assert main._already_chosen("2 minutes", "Tap “2 minutes”.", TIMEOUT) == ""
assert main._already_chosen("30 seconds", "“30 seconds” is already on.", TIMEOUT) == ""                 # not a tap
assert main._already_chosen("Video", "Tap “Video”.", ["Video [selected]", "Short [tap]", "Live [tap]", "0:14 [tap]", "0:32 [tap]", "Recents [tap]"]) == ""   # a gallery: chosen_tab
n0 = main.STATS["already_chosen_asked"]
r, calls = step(TIMEOUT, ["Tap “Display”.", "Tap “Screen timeout”."], [J("30 seconds", "Tap “30 seconds”."), J("2 minutes", "Tap “2 minutes”.")],
                "Make the screen stay on for 2 minutes", ["Settings", "Display", "Screen timeout"], i="dev97d")
assert r["label"] == "2 minutes" and len(calls) == 2 and main.STATS["already_chosen_asked"] == n0 + 1, r
assert "“30 seconds” is already chosen" in json.dumps(calls[1]["messages"], ensure_ascii=False)
# It says the same again: only said, never rung; done when it was the goal
r, calls = step(TIMEOUT, ["Tap “Screen timeout”."], [J("30 seconds", "Tap “30 seconds”."), J("30 seconds", "Tap “30 seconds”.")],
                "Make the screen stay on for 2 minutes", ["Settings", "Screen timeout"], i="dev97e")
assert r["label"] is None and r["say"] == "“30 seconds” is already chosen." and r["done"] is False, r
r, calls = step(TIMEOUT, ["Tap “Screen timeout”."], [J("30 seconds", "Tap “30 seconds”."), J("30 seconds", "Tap “30 seconds”.")],
                "Set the screen timeout to 30 seconds", ["Settings", "Screen timeout"], i="dev97f")
assert r["done"] is True and r["label"] is None, r

# 3. Careful thinking for the first step in a new app, once: Infinix reports few taps, so the path often stays at the app's
# name, and every routine step there looked like a new app (slower and dearer for nothing)
assert main._path_app(["Home screen", "Drive"], APPS) == "drive" and main._path_app(["Drive", "Create new"], APPS) == ""
assert main._path_app([], APPS) == "" and main._path_app(["Drive"], []) == ""
DRIVE = ["Navigate up [tap]", "Create new [tap]", "My Drive [tap]", "Files [tap]"]
r, calls = step(DRIVE, ["Tap “Drive”."], [J("Create new", "Tap “Create new”.")], "Scan a document with Drive", ["Home screen", "Drive"], i="dev97g")
assert calls[0]["model"] == main.STRONG_MODEL                                      # the first step in Drive: careful
r, calls = step(DRIVE, ["Tap “Drive”.", "Tap “Create new”."], [J("Files", "Tap “Files”.")], "Scan a document with Drive", ["Home screen", "Drive"], i="dev97g")
assert calls[0]["model"] == "claude-haiku-5-5", calls[0]["model"]                 # the next, still in Drive (no tap reported): routine
r, calls = step(["Chats [tap]", "Updates [tap]", "Calls [tap]"], ["Tap “Drive”.", "Tap “Create new”.", "Tap “Files”."], [J("Chats", "Tap “Chats”.")],
                "Scan a document with Drive", ["Drive", "WhatsApp"], i="dev97g")
assert calls[0]["model"] == main.STRONG_MODEL                                      # another app: careful again
assert main._careful_why(["x"], ["Home screen", "Drive"], APPS, {"last": [], "app": "drive"}, False, False) == ""
assert main._careful_why(["x"], ["Home screen", "Drive"], APPS, {"last": [], "app": "whatsapp"}, False, False) == "new app"

# Users' phones: staged
for rule in ("label_follows_words", "already_chosen"):
    assert main.STAGED[rule] == "0.97"
main._launch["live"]["0.97"] = time.time()
r, calls = step(WIFI, ["Tap “Settings”.", "Tap “Wi-Fi”."], [J("Wi-Fi", "Tap the Navigate up arrow to go back.")], GOAL, ["Settings", "Wi-Fi"], i="user97", tester=False)
assert r["label"] == "Wi-Fi", r                                                   # not yet
main._launch["live"]["0.97"] = time.time() - 25 * 3600
r, calls = step(WIFI, ["Tap “Settings”.", "Tap “Wi-Fi”."], [J("Wi-Fi", "Tap the Navigate up arrow to go back.")], GOAL, ["Settings", "Wi-Fi"], i="user97b", tester=False)
assert r["label"] == "Navigate up", r
assert main.SERVER_VERSION >= "0.97"
print("the ring follows the words; a chosen option is never tapped again; careful once per new app")
