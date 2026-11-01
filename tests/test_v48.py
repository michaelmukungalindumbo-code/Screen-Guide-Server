import os, asyncio
os.environ.update(ADMIN_KEY="k", GITHUB_TOKEN="ghp_test", AI_FIX_PER_DAY="2")
import main
run = asyncio.run
calls = []


async def fake_github(method, path, payload):
    calls.append((method, path, payload))
    return {"number": 7} if path.endswith("/issues") else {}
main._github = fake_github


def crash(trace, phone, version="0.55"):
    async def go():
        r = await main.crash_report(main.CrashIn(trace=trace, version=version, device="TECNO phone, Android 13", where="main"),
                                    x_app_token="tok", x_install_id=phone)
        await asyncio.sleep(0.05)   # let the background issue task finish
        return r
    return run(go())


T = """java.lang.NullPointerException: guide was null for 0977123456
    at zm.screenguide.GuideService.next(GuideService.kt:120)
    at android.os.Handler.handleCallback(Handler.java:942)"""

# A new kind of crash in our code: one issue, then the label in a second call (that is what starts the AI fixer)
assert crash(T, "p1")["ok"]
assert [c[1] for c in calls] == ["/repos/michaelmukungalindumbo-code/Screen-Guide/issues",
                                 "/repos/michaelmukungalindumbo-code/Screen-Guide/issues/7/labels"], calls
title, body = calls[0][2]["title"], calls[0][2]["body"]
assert title == "App crash: java.lang.NullPointerException", title
assert "GuideService.kt:120" in body and "TECNO phone" in body and "CLAUDE.md" in body and "failing unit test" in body
assert "0977" not in body and "p1" not in body, body          # no numbers, no phone ids in a public issue
assert calls[1][2] == {"labels": ["ai-fix"]}
rec = main._store.kv_list("crash", 10)[0][1]
assert rec["issue"] == 7 and rec["asked"], rec

# The same crash again, from another phone: no second issue, and the count is kept
crash(T.replace("kt:120", "kt:124"), "p2")
assert len(calls) == 2, calls
rec = main._store.kv_list("crash", 10)[0][1]
assert rec["count"] == 2 and rec["issue"] == 7, rec

# A crash with none of our code in it: no issue (nothing in our code to fix, and harder to fake)
crash("java.lang.OutOfMemoryError: x\n    at android.graphics.Bitmap.nativeCreate(Native Method)", "p3")
assert len(calls) == 2, calls

# At most AI_FIX_PER_DAY issues a day, because each fix costs AI money
crash(T.replace("NullPointerException", "IllegalStateException").replace("next(", "start("), "p4")
crash(T.replace("NullPointerException", "IndexOutOfBoundsException").replace("next(", "stop("), "p5")
assert len([c for c in calls if c[1].endswith("/issues")]) == 2, calls

# GitHub down or the token wrong: the crash is still kept, nothing breaks, and the error is counted
main._fix_asked.clear(); main._store.kv_put("aifix", main._today(), {"n": 0})
async def broken(method, path, payload):
    raise RuntimeError("GitHub said 401")
main._github = broken
assert crash(T.replace("NullPointerException", "ClassCastException").replace("next(", "pick("), "p6")["ok"]
assert main.STATS["ai_fix_errors"] == 1

# Owner report links the crash to its AI fix issue
page = run(main.admin_report(key="k")); b = str(getattr(page, "body", page))
assert "issues/7'>#7</a>" in b and "AI fix" in b, b[:300]

# Off without a token
main.GITHUB_TOKEN = ""; main._fix_asked.clear(); main._store.kv_put("aifix", main._today(), {"n": 0}); calls.clear()
main._github = fake_github
crash(T.replace("NullPointerException", "ArithmeticException").replace("next(", "sum("), "p7")
assert calls == [], calls
assert main.SERVER_VERSION >= "0.48"
print("AI fixer issues ok")
