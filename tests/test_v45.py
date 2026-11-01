import os, asyncio, json
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run
H = dict(x_app_token="tok", x_install_id="gran")
def err(f):
    try: run(f); return None
    except main.HTTPException as e: return e
# 1. Start: a long link id (never guessable) and a separate key for the phone
s = run(main.live_start(**H)); lid, key = s["id"], s["key"]
assert len(lid) >= 16 and len(key) >= 20 and s["url"].endswith("/live/" + lid)
page = run(main.live_page(lid)).body
assert "Help on their phone" in page and lid in page and "never tap for them" in page
# 2. The phone sends its screen; the helper page gets it once per change; numbers hidden, odd values clamped
SC = {"app": "Drive", "ratio": 2.1, "items": [{"t": "Create new", "x": .8, "y": .85, "w": .15, "h": .07, "k": "tap"},
      {"t": "Call 0977123456", "x": .1, "y": .1, "w": .8, "h": .05, "k": "text"}, {"t": "", "x": 2, "y": -1, "w": .1, "h": .1, "k": "weird"}, "junk"]}
r = run(main.live_screen(lid, main.LiveScreen(key=key, screen=SC), **H))
assert r == {"point": None, "helper": False}, r
v = run(main.live_view(lid)).body
items = v["screen"]["items"]
assert v["screen"]["app"] == "Drive" and items[0]["t"] == "Create new" and "0977" not in items[1]["t"] and "••••" in items[1]["t"], items
assert len(items) == 2, "a box with no words that is plain text is dropped; junk is skipped"
assert run(main.live_view(lid, v=v["v"])).body["screen"] is None, "unchanged: nothing resent"
assert run(main.live_screen(lid, main.LiveScreen(key=key), **H))["helper"] is True, "the helper's page was seen"
e = err(main.live_screen(lid, main.LiveScreen(key="wrong", screen=SC), **H)); assert e.status_code == 403
# 3. The helper points or writes; the phone gets the newest point once
assert run(main.live_point(lid, main.LivePoint(x=.8, y=.85, w=.15, h=.07, label="Create new")))["id"] == 1
assert run(main.live_point(lid, main.LivePoint(say="Now tap Upload")))["id"] == 2
p = run(main.live_screen(lid, main.LiveScreen(key=key, last_point=0), **H))["point"]
assert p["id"] == 2 and p["say"] == "Now tap Upload" and "x" not in p, p
assert run(main.live_screen(lid, main.LiveScreen(key=key, last_point=2), **H))["point"] is None
e = err(main.live_point(lid, main.LivePoint())); assert e.status_code == 400
# 4. Private screens stay private
run(main.live_screen(lid, main.LiveScreen(key=key, screen={"private": True, "app": "Airtel Money", "items": [{"t": "PIN"}]}), **H))
assert run(main.live_view(lid)).body["screen"] == {"private": True, "app": "Airtel Money"}
# 5. Ending: everything 404s, the page says it ended
run(main.live_end(lid, main.LiveScreen(key=key), **H))
assert err(main.live_view(lid)).status_code == 404 and err(main.live_point(lid, main.LivePoint(say="hi"))).status_code == 404
assert run(main.live_page(lid)).status_code == 404 and run(main.live_page("nonsense")).status_code == 404
# 6. Idle sessions are tidied away; one phone cannot hold many
s2 = run(main.live_start(**H)); main.LIVE[s2["id"]]["seen"] -= 3600; main._live_tidy(main.time.time()); assert s2["id"] not in main.LIVE
for _ in range(3): run(main.live_start(x_app_token="tok", x_install_id="busy"))
assert err(main.live_start(x_app_token="tok", x_install_id="busy")).status_code == 429
p = run(main.privacy()); b = getattr(p, "body", p); assert "Live help" in str(b)
assert main.SERVER_VERSION >= "0.45"
print("live help ok")
