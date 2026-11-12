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

# The owner's phone (12 Nov, 0.116): "Open my Safe folder" in Files. He tapped "Safe folder", which opened its lock screen
# (a PIN pad that shares no words: only "Navigate up"). The guide said "Tap Navigate up to go back to your folders", then
# "Tap Safe folder" again, round and round. A tap on the very thing the goal names that opens a near-empty screen means
# they got there: it is a locked or private screen. Done, and they enter their PIN themselves; never "go back".
GOAL = "Open the Safe folder in the Files app"
HIST = ["Tap “Files” to open it.", "Tap “Safe folder” to open it."]
LOCK = ["Navigate up [tap]"]
def step(labels, hist, out, goal=GOAL, i="dev92", tester=True):
    main._claude_client = Client(out)
    r = run(main.next_step(main.Next(goal=goal, labels=labels, history=hist, path=["Files"]), x_app_token="tok", x_install_id=i, x_tester="1" if tester else ""))
    return r, main._claude_client.messages.calls

n0 = main.STATS["locked_arrival"]
r, calls = step(LOCK, HIST, [J("Navigate up", "Tap “Navigate up” to go back to your folders.")])
assert r["done"] is True and r["label"] is None, r
assert r["say"].startswith("You are in “Safe folder”.") and "PIN" in r["say"] and "yourself" in r["say"], r["say"]
assert len(calls) == 0 and main.STATS["locked_arrival"] == n0 + 1                 # no AI needed, no cost
# The same near-empty screen after a tap on something else: the AI as usual
r, calls = step(LOCK, ["Tap “Files” to open it.", "Tap “Documents”."], [J("Navigate up", "Tap “Navigate up”.")])
assert r["label"] == "Navigate up" and len(calls) == 1, r
# A screen with real words after the tap: as usual
r, calls = step(["Navigate up [tap]", "Photos [tap]", "Videos [tap]", "Add files [tap]"], HIST, [J("Add files", "Tap “Add files”.")])
assert r["label"] == "Add files", r
# Only when the goal names it: "Tap Settings" opening a near-empty page is not the goal
r, calls = step(LOCK, ["Tap “Settings”."], [J("Navigate up", "Tap “Navigate up”.")], goal="Turn on Wi-Fi")
assert r["done"] is False, r
assert main._arrived_locked("Open the Safe Folder app", "Tap “Safe folder” to open it.", ["Navigate up [tap]", "Use fingerprint [tap]"]) == "Safe folder"
assert main._arrived_locked("Open WhatsApp", "Tap “WhatsApp”.", []) == "WhatsApp"
assert main._arrived_locked("Open WhatsApp", "Tap “WhatsApp”.", ["Chats [tap]", "Updates [tap]", "Calls [tap]", "Search [tap]"]) == ""
# Users' phones: staged
main._launch["live"][main.STAGED["locked_arrival"]] = time.time()
r, calls = step(LOCK, HIST, [J("Navigate up", "Tap “Navigate up”.")], i="user92", tester=False)
assert r["done"] is False, r                                                     # not yet
main._launch["live"][main.STAGED["locked_arrival"]] = time.time() - 25 * 3600
r, calls = step(LOCK, HIST, [J("Navigate up", "x")], i="user92b", tester=False)
assert r["done"] is True, r
assert main.STAGED["locked_arrival"] == "0.92" and main.SERVER_VERSION >= "0.92"
print("a tap on what the goal names that opens a locked, near-empty screen: arrived; they enter their PIN themselves")
