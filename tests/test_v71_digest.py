import os, asyncio, json, time as _time, calendar
os.environ.update(ADMIN_KEY="k", GITHUB_TOKEN="ghp_test")
import main
run = asyncio.run

# A pretend clock: Monday 9 Nov 2026, 08:00 in Zambia
class Clock:
    now = calendar.timegm((2026, 11, 9, 6, 0, 0))
    def time(self): return Clock.now
    def __getattr__(self, k): return getattr(_time, k)
main.time = Clock()
issues = []
async def fake_github(method, path, payload):
    if method == "GET":
        return [{"body": i[2]["body"]} for i in issues]
    issues.append((method, path, payload)); return {"number": 100 + len(issues)}
main._github = fake_github
main.GITHUB_TOKEN = "ghp_test"

# Two weeks of users' counts: the last week had more Help, mostly on YouTube's gallery
GAL = "Video, Short, Live, Post, Close, Upload from gallery, Videos, Settings, Select more media"
def day(n, steps, help_, phones):
    return {"guides": {"start": 3, "done": 2, "stop": 1}, "steps": steps, "help": help_, "slow": 1, "secs": steps * 3.0,
            "versions": {"0.71": {"steps": steps, "help": help_}},
            "screens": {"gal": {"words": GAL, "steps": 4, "help": help_, "phones": phones},
                        "set": {"words": "Settings, Search, Apps", "steps": steps - 4, "help": 0}}}
for i in range(1, 8):            # 2 to 8 Nov
    main._counts_mem["2026-11-%02d" % (9 - i)] = day(i, 10, 2, ["p%d" % i])
for i in range(8, 15):           # 26 Oct to 1 Nov
    d = "2026-11-%02d" % (9 - i) if 9 - i >= 1 else "2026-10-%02d" % (31 + 9 - i)
    main._counts_mem[d] = day(i, 10, 1, ["p1"])
main._launch["live"] = {"0.71": Clock.now - 5 * 86400}

title, body = run(main.digest_text())
assert title == "Users this week: where people got stuck (2 Nov to 8 Nov)", title
assert "- Guides: 21 started, 14 finished, 7 stopped (the week before: 21 started, 14 finished)." in body, body
assert "Help pressed: 14, which is **20.0 per 100 steps** (the week before: 10.0)." in body, body
assert "0.71: 20.0 Help per 100 steps (70 steps)" in body
assert "1. %s: Help 14 times from 7 phones, in 28 steps." % GAL in body, body
assert "Settings, Search, Apps" not in body                            # no Help there: not listed
assert "`@claude look at 1`" in body and "<!-- users-week: 2026-W46 -->" in body

# Sent once on Monday morning, through the keep-awake visits to /health; never twice
async def health_twice():
    await main.health(); await asyncio.sleep(0.05); await main.health(); await asyncio.sleep(0.05)
run(health_twice())
assert len(issues) == 1 and issues[0][2]["title"] == title and "labels" not in issues[0][2], issues
main._digest_state.update(week="", tried=0.0); main._launch["digest"] = ""     # a restart that forgot it was sent
run(main.send_digest("2026-W46"))
assert len(issues) == 1                                                 # GitHub remembers
assert main._launch["digest"] == "2026-W46"

# Not on other days, and not before 07:00 on Monday
Clock.now += 86400; main._digest_state.update(week="", tried=0.0); main._launch["digest"] = ""
run(health_twice()); assert len(issues) == 1
Clock.now = calendar.timegm((2026, 11, 16, 4, 30, 0))                  # Monday 16 Nov, 06:30 in Zambia
run(health_twice()); assert len(issues) == 1

# A quiet week (under 20 steps): nothing is sent
Clock.now = calendar.timegm((2026, 11, 16, 6, 0, 0))
main._counts_mem.clear(); main._counts.clear()
assert run(main.digest_text()) is None
run(main.send_digest("2026-W47")); assert len(issues) == 1 and main._launch["digest"] == "2026-W47"
print("weekly users issue ok")
