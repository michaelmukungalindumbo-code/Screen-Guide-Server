import os, asyncio
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run
T = """java.lang.NumberFormatException: For input string: "0977123456" from michael@example.com
    at java.lang.Integer.parseInt(Integer.java:615)
    at zm.screenguide.GuideService.refresh(GuideService.kt:301)
    at zm.screenguide.GuideService$refreshRun$1.run(GuideService.kt:258)
    some screen words: Send money to Mum PIN 1234
Caused by: java.lang.IllegalStateException: card 4242424242424242
    at android.os.Handler.handleCallback(Handler.java:942)"""
r = run(main.crash_report(main.CrashIn(trace=T, version="0.55", device="INFINIX phone, Android 14", where="main"), x_app_token="tok", x_install_id="p1"))
assert r["ok"]
rows = main._store.kv_list("crash", 10); assert len(rows) == 1
d = rows[0][1]; t = d["trace"]
assert "0977" not in t and "michael@" not in t and "4242" not in t and "Mum" not in t and "PIN" not in t, t
assert "at zm.screenguide.GuideService.refresh(GuideService.kt:301)" in t and t.startswith("java.lang.NumberFormatException"), t
assert "Caused by: java.lang.IllegalStateException" in t and d["count"] == 1 and d["devices"] == ["INFINIX phone, Android 14"]
# the same crash from another phone, after the code moved a few lines: one row, counted twice, two phones
run(main.crash_report(main.CrashIn(trace=T.replace("GuideService.kt:301", "GuideService.kt:305"), version="0.56", device="Samsung tablet, Android 14"),
                      x_app_token="tok", x_install_id="p2"))
rows = main._store.kv_list("crash", 10); d = rows[0][1]
assert len(rows) == 1 and d["count"] == 2 and len(d["phones"]) == 2 and d["versions"] == ["0.55", "0.56"], d
assert not run(main.crash_report(main.CrashIn(trace=""), x_app_token="tok", x_install_id="p3"))["ok"]
page = run(main.admin_report(key="k")); b = getattr(page, "body", page)
assert "App crashes" in str(b) and "GuideService.kt" in str(b), str(b)[:300]
p = run(main.privacy()); assert "Crash reports" in str(getattr(p, "body", p))
assert main.SERVER_VERSION >= "0.47"
print("crash reports ok")
