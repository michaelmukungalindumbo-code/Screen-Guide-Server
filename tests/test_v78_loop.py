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
def J(label, say): return json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})
GOAL = "Install CapCut from the Play Store"
OPEN = ["Navigate up [tap]", "Search apps & games [tap]", "Voice search [tap]"]
HIST = {}
def step(i, label, say, stuck=False, tapped=False, labels=OPEN, tester=True, goal=GOAL):
    main._claude_client = Client([J(label, say)] * 4)
    h = HIST.setdefault((i, goal), [])                        # what the phone already told, as the phone sends it
    r = run(main.next_step(main.Next(goal=goal, labels=labels, stuck=stuck, tapped=tapped, history=h[-6:]),
                           x_app_token="tok", x_install_id=i, x_tester="1" if tester else ""))
    if h[-1:] != [r["say"]]:
        h.append(r["say"])
    calls = main._claude_client.messages.calls
    return r, [c["model"] for c in calls], [str(c["messages"][0]["content"]) for c in calls]

# The loop breaker (5 Nov, the owner chose it). Every bad test had the same shape: the same instruction again and again,
# and Help (YouTube's editor, WhatsApp Business, the Play Store's search box). ScreenGuide notices, tries another way with
# the stronger AI told what did not work, and if that fails too it says it is not sure, instead of going round again.
assert "loop_breaker" in main.STAGED
NOT_SURE = main._NOT_SURE
assert "not sure" in NOT_SURE and not main._POINT_ACTION.search(NOT_SURE)   # never read as "could not point"

# 1. Help twice in a row on the same step (the Play Store, steps 3 to 6)
step("L1", "Search apps & games", "Tap the search bar.")
r, m, t = step("L1", "Search apps & games", "Tap the search box at the top.", stuck=True)        # the first Help: as before
assert "<going_round>" not in t[0], t
r, m, t = step("L1", "Voice search", "Tap “Voice search”, then say CapCut.", stuck=True)        # the second Help in a row
assert "<going_round>" in t[0] and "Help was pressed twice" in t[0] and "Tap the search box" in t[0], t
assert m[0] == main.STRONG_MODEL, m                                                               # the stronger AI
assert r["label"] == "Voice search", r                                                            # another way: taken
r, m, t = step("L1", "Search apps & games", "Tap the search box.", stuck=True)                   # Help yet again
assert r["label"] is None and r["say"] == NOT_SURE and m == [], (r, m)                            # honest; no AI asked
assert "circles" in [p["kind"] for p in main._sessions["L1"]["problems"]]                        # the watcher knows
card = main._rule_card(next(p for p in main._sessions["L1"]["problems"] if p["kind"] == "circles"))
assert card["title"].startswith("Going round in circles"), card

# 2. The stronger AI gives the same instruction anyway: honest at once
step("L2", "Search apps & games", "Tap the search bar.")
step("L2", "Search apps & games", "Tap the search box.", stuck=True)
r, m, t = step("L2", "Search apps & games", "Tap the search box.", stuck=True)
assert "<going_round>" in t[0] and r["label"] is None and r["say"] == NOT_SURE, r

# 3. The same instruction twice on the same screen, tapped each time, and nothing changed: not a third time
INSTALL = ["CapCut [text]", "Install [tap]", "About this app [tap]", "Ratings and reviews [tap]"]
step("L3", "Install", "Tap “Install”.", labels=INSTALL)
r, m, t = step("L3", "Install", "Tap “Install”.", tapped=True, labels=INSTALL)
assert "<going_round>" not in t[0]
r, m, t = step("L3", "Install", "Tap “Install”.", tapped=True, labels=INSTALL)
assert "<going_round>" in t[0] and "did not change the screen" in t[0], t
assert r["say"] == NOT_SURE, r                                                                    # repeated anyway

# Not going round: re-checks while they scroll (the same "Tap Done", the screen changing, nothing tapped), a new goal,
# and a new screen between two Helps
P = [["Done [tap]"] + ["0:%02d [tap]" % (10 + 4 * k + j) for j in range(4)] for k in range(4)]
for p in P:
    r, m, t = step("R1", "Done", "Tap “Done”.", labels=p)
    assert "<going_round>" not in t[0] and r["label"] == "Done", r
step("R2", "Search apps & games", "Tap the search bar.", stuck=True)
r, m, t = step("R2", "Settings", "Tap “Settings”.", stuck=True, goal="Turn on Wi-Fi", labels=["Settings [tap]", "Wi-Fi [tap]"])
assert "<going_round>" not in t[0], t
step("R3", "Search apps & games", "Tap the search bar.", stuck=True)
step("R3", "Install", "Tap “Install”.", labels=INSTALL)
r, m, t = step("R3", "Install", "Tap “Install”.", stuck=True, labels=INSTALL)
assert "<going_round>" not in t[0], t

# A new guide, even for the same goal, starts with a clean slate
run(main.event(main.Event(event="start", guide="ai"), x_app_token="tok", x_install_id="L1", x_tester="1"))
HIST.pop(("L1", GOAL), None)
step("L1", "Search apps & games", "Tap the search bar.", stuck=True)
r, m, t = step("L1", "Voice search", "Tap “Voice search”.", stuck=True)
assert "<going_round>" in t[0] and r["label"] == "Voice search", r                       # another way first, not "not sure"

# Kept in memory only, as fingerprints of the words, never the words themselves
for v in main._loops.values():
    assert isinstance(v["goal"], int) and all(isinstance(x["label"], int) and isinstance(x["say"], int)
                                              and all(isinstance(w, int) for w in x["sig"]) for x in v["last"]), v

# Staged: users' phones get it once 0.78 has been live for 24 hours; test phones at once
main._launch["live"][main.STAGED["loop_breaker"]] = main.time.time()
step("U1", "Search apps & games", "Tap the search bar.", tester=False)
step("U1", "Search apps & games", "Tap the search box.", stuck=True, tester=False)
r, m, t = step("U1", "Search apps & games", "Tap the search box.", stuck=True, tester=False)
assert "<going_round>" not in t[0], t                                                            # not yet for users
main._launch["live"][main.STAGED["loop_breaker"]] -= 25 * 3600
r, m, t = step("U1", "Search apps & games", "Tap the search box.", stuck=True, tester=False)
assert "<going_round>" in t[0] and r["say"] == NOT_SURE, r
assert main._launch["seen"]["loop_breaker"]["fired"] >= 1
print("going round in circles is noticed: another way, then honest")
