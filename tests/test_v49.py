import os, asyncio, time
os.environ.update(ADMIN_KEY="k", GITHUB_TOKEN="ghp_test", AI_FIX_PER_DAY="3")
import main
run = asyncio.run
issues, posts = [], []
now = lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


async def fake_github(method, path, payload):
    if method == "GET":
        assert "labels=ai-fix" in path and "state=all" in path, path
        return list(reversed(issues))
    posts.append(path)
    if path.endswith("/issues"):
        n = 20 + len(issues); issues.append({"number": n, "body": payload["body"], "created_at": now()}); return {"number": n}
    return {}
main._github = fake_github


def crash(trace, phone):
    async def go():
        r = await main.crash_report(main.CrashIn(trace=trace, version="0.56", device="ITEL phone, Android 12"), x_app_token="tok", x_install_id=phone)
        await asyncio.sleep(0.05)
        return r
    return run(go())


def restart():   # the free server restarts when idle, and without a database it forgets every crash
    main._fix_asked.clear(); main._store.kv.clear()


T = "java.lang.IllegalStateException: no guide\n    at zm.screenguide.MainActivity.open(MainActivity.kt:40)"
crash(T, "p1")
assert posts == ["/repos/michaelmukungalindumbo-code/Screen-Guide/issues", "/repos/michaelmukungalindumbo-code/Screen-Guide/issues/20/labels"], posts
assert "<!-- crash-id: " in issues[0]["body"]

# After a restart the same crash comes in again: GitHub already has its issue, so no second issue (and no second AI bill)
restart()
crash(T, "p2")
assert len(posts) == 2, posts
rec = main._store.kv_list("crash", 10)[0][1]
assert rec["issue"] == 20, rec      # the owner report still links it

# The daily limit is counted on GitHub too, so restarts cannot get around it
restart()
crash(T.replace("open(", "a("), "p3"); crash(T.replace("open(", "b("), "p4")
assert len([p for p in posts if p.endswith("/issues")]) == 3
restart()
crash(T.replace("open(", "c("), "p5")
assert len([p for p in posts if p.endswith("/issues")]) == 3, posts
assert main.STATS["ai_fix_skipped"] >= 2

# Issues you labelled ai-fix yourself (no crash-id) do not use up the crash limit
issues.append({"number": 99, "body": "Please fix the Bemba voice", "created_at": now()})
main.AI_FIX_PER_DAY = 4; restart()
crash(T.replace("open(", "d("), "p6")
assert len([p for p in posts if p.endswith("/issues")]) == 4, posts
assert main.SERVER_VERSION >= "0.49"
print("AI fixer remembers on GitHub ok")
