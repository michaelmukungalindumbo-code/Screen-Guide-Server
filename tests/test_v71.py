import os, asyncio, json
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run
class Msgs:
    def __init__(self, out): self.out = list(out)
    async def create(self, **kw):
        class U: input_tokens = 900; output_tokens = 40
        class B: type = "text"; text = self.out.pop(0)
        class M: content = [B()]; usage = U(); stop_reason = "end_turn"
        return M()
class Client:
    def __init__(self, out): self.messages = Msgs(out)
def J(label, say): return json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})
def step(phone, labels, tester=False, stuck=False, label="Videos", say="Tap “Videos”."):
    main._claude_client = Client([J(label, say)])
    return run(main.next_step(main.Next(goal="Upload a video in the YouTube app", labels=labels, stuck=stuck,
                                        device="Infinix phone, Android 14"),
                              x_app_token="tok", x_install_id=phone, x_tester="1" if tester else ""))
def ev(phone, e, tester=False):
    run(main.event(main.Event(event=e, guide="ai"), x_app_token="tok", x_install_id=phone, x_tester="1" if tester else ""))
TODAY = main._today()

# The Mother Ship's Performance deck: counts from users' phones, kept across restarts. Test phones are left out.
# YouTube's gallery from the 4 Nov test, with a personal word ("Mum") and video lengths on it
GAL = ["Video [selected]", "Short [tap]", "Live [tap]", "Post [tap]", "Close [tap]", "Upload from gallery [text]", "Videos [tap]",
       "Settings [tap]", "Select more media [tap]", "Mum [text]", "0:13 [tap]", "0:21 [tap]"]
ev("u1", "start"); ev("dev", "start", tester=True)
step("u1", GAL); step("u1", GAL, stuck=True); step("u2", GAL, stuck=True); step("u2", GAL, stuck=True)
step("dev", GAL, tester=True, stuck=True)                                   # the developer's test phone: not counted
ev("u1", "done"); ev("u2", "stop")
d = main._counts[TODAY]
assert d["steps"] == 4 and d["help"] == 3 and d["guides"] == {"start": 1, "done": 1, "stop": 1}, d
assert d["kinds"]["Infinix phone, Android 14"] == {"steps": 4, "help": 3}, d["kinds"]
assert d["versions"][main.SERVER_VERSION]["help"] == 3
(sc,) = d["screens"].values()
assert sc["steps"] == 4 and sc["help"] == 3 and len(sc["phones"]) == 2, sc        # 2 phones pressed Help here
assert sc["words"] == "Video, Short, Live, Post, Close, Upload from gallery, Videos, Settings, Select more media", sc["words"]
assert "Mum" not in json.dumps(main._counts) and "0:13" not in json.dumps(main._counts)   # never anyone's own words or numbers
assert "u1" not in json.dumps(main._counts) and "dev" not in json.dumps(main._counts)      # phones only as short codes
main._count_step("u3", GAL, "Tecno phone, Android 10", False, 12.4)                       # a slow answer
assert main._counts[TODAY]["slow"] == 1

# Saved without a database or Upstash: kept in memory, and added up with what comes later
assert main.counts_kind() == "memory"
run(main.counts_flush(force=True))
assert main._counts == {} and main._counts_mem[TODAY]["steps"] == 5
step("u1", GAL, stuck=True)
run(main.counts_flush(force=True))
saved = main._counts_mem[TODAY]
assert saved["steps"] == 6 and saved["help"] == 4, saved
(s2,) = saved["screens"].values()
assert len(s2["phones"]) == 2                                                               # the same 2 phones, not 3

# Upstash: saved there with a 90-day expiry, read back together with what is not saved yet
store = {}
async def fake_upstash(cmd):
    if cmd[0] == "GET":
        return store.get(cmd[1])
    assert cmd[0] == "SET" and cmd[3:] == ["EX", 90 * 86400], cmd
    store[cmd[1]] = cmd[2]; return "OK"
main._upstash = fake_upstash
main.UPSTASH_URL, main.UPSTASH_TOKEN = "https://example.upstash.io", "t"
assert main.counts_kind() == "Upstash"
step("u4", GAL, stuck=True)
run(main.counts_flush(force=True))
assert json.loads(store["sg:counts:" + TODAY])["help"] == 1
step("u4", GAL)
days = run(main.counts_days(7))
assert days[0][0] == TODAY and days[0][1]["steps"] == 2 and len(days) == 7, days[0]
# Upstash down: nothing is lost, it is saved on the next try
async def down(cmd): raise RuntimeError("Upstash is down")
main._upstash = down
run(main.counts_flush(force=True))
assert main._counts[TODAY]["steps"] == 1 and "down" in main._counts_state["error"]
main._upstash = fake_upstash
run(main.counts_flush(force=True))
assert main._counts == {} and json.loads(store["sg:counts:" + TODAY])["steps"] == 2 and main._counts_state["error"] == ""
# Not saved more than every 10 minutes unless forced
step("u4", GAL); run(main.counts_flush())
assert main._counts[TODAY]["steps"] == 1

# The existing database (DATABASE_URL), when it is set, is used first
main.DATABASE_URL = "sqlite:"; main._store = main._Store("sqlite:")
assert main.counts_kind() == "database"
run(main.counts_flush(force=True))
assert main._store.kv_get("counts", TODAY)["steps"] == 1

# The owner report shows it, without anyone's own words
step("u5", GAL, stuck=True)
page = run(main.users_report_html(7))
assert "Real users (test phones left out)" in page and "Saved in the database" in page, page[:300]
assert "Select more media" in page and "Mum" not in page
pp = run(main.privacy())
assert "Test phones are not counted" in str(getattr(pp, "body", pp) if not isinstance(getattr(pp, "body", None), bytes) else pp.body.decode())
assert main.SERVER_VERSION >= "0.71"
print("real-user counts kept")

# 4 Nov: the owner stays on the free plan and accepts the wait while the server wakes up. A slow answer on a test phone
# is then not reported when the server had just started and its own part was quick; any other slow answer still is.
main.DATABASE_URL = ""; main.UPSTASH_URL = ""
H = dict(x_app_token="tok", x_install_id="dev71w", x_tester="1")
run(main.event(main.Event(event="start", guide="ai"), **H))
main.STARTED = main.time.time() - 20                                   # the server started 20 seconds ago
main._claude_client = Client([J("Videos", "Tap “Videos”.")])
run(main.next_step(main.Next(goal="Upload a video in the YouTube app", labels=GAL), **H))
assert run(main.watch_slow(main.WatchSlow(step=1, ms=35000), **H)) == {"watch": 0}
assert not main._sessions["dev71w"]["problems"]
main.STARTED = main.time.time() - 3600                                 # awake for an hour: the wait was the network
main._claude_client = Client([J("Videos", "Tap “Videos”.")])
run(main.next_step(main.Next(goal="Upload a video in the YouTube app", labels=GAL), **H))
assert run(main.watch_slow(main.WatchSlow(step=2, ms=35000), **H)) == {"watch": 1}
print("waking up is not reported")
