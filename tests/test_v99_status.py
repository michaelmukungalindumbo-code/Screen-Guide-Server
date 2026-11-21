import os, asyncio, json
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run
def H(who): return dict(x_app_token="tok", x_install_id=who)
def st(*words, app=None):
    return [dict({"m": [w], "s": {"en": "Tap “%s”." % w, "ny": "Dinani “%s”." % w, "bem": "Kandeni “%s”." % w}}, **({"a": app} if app else {})) for w in words]
def err(f):
    try: run(f); return None
    except main.HTTPException as e: return e
DRIVE = "com.google.android.apps.docs"

# The owner (21 Nov): "someone can put it on the app as a status just like WhatsApp, where someone can view, and if they
# like the guide, they can then request for it". He chose: everyone sees it, after an automatic check; one tap gets it;
# it stays until its maker removes it.
SCAN = [{"m": ["Drive"], "s": {"en": "Tap “Drive” to open it."}, "a": "home"}] + st("Create new", "Scan", app=DRIVE) + [{"m": ["Next"], "s": {"en": "Tap “Next”."}, "a": "com.google.android.gms", "i": True}]

# 1. Post: the maker's first name only, the phone kind, and where each step was taught (kept: a step is looked for there)
p = run(main.status_post(main.StatusIn(title="Scan a document with Drive", steps=SCAN, device="INFINIX phone, Android 14", name="michael mukunga 0977"), **H("maker")))
sid = p["id"]; assert len(sid) == 6 and p["updated"] is False, p
d = main._store.kv_get("status", sid)
assert d["name"] == "Michael" and d["device"] == "infinix phone" and d["gets"] == 0 and d["hidden"] is False, d
assert [s.get("a") for s in d["steps"]] == ["home", DRIVE, DRIVE, "com.google.android.gms"] and d["steps"][3].get("i") is True, d["steps"]
assert main._status_name("") == "" and main._status_name("@@ 12") == "" and main._status_name("Thandiwe") == "Thandiwe"
# The same name again: the post is brought up to date, not doubled
p2 = run(main.status_post(main.StatusIn(title="scan a document with drive", steps=SCAN, device="INFINIX phone"), **H("maker")))
assert p2["id"] == sid and p2["updated"] is True and main._store.kv_get("status", sid)["name"] == ""

# 2. Everyone sees it; its maker sees it under "mine"
L = run(main.status_list(**H("viewer")))
assert [i["id"] for i in L["items"]] == [sid] and L["mine"] == [], L
i = L["items"][0]
assert i["title"] == "Scan a document with drive" or i["title"].lower() == "scan a document with drive"
assert i["steps"] == 4 and i["device"] == "infinix phone" and i["gets"] == 0 and i["mine"] is False, i
M = run(main.status_list(**H("maker")))
assert M["items"] == [] and [x["id"] for x in M["mine"]] == [sid]
# Looking first: what each step says, nothing counted
v = run(main.status_view(sid.lower(), **H("viewer")))
assert v["says"][:2] == ["Tap “Drive” to open it.", "Tap “Create new”."] and v["gets"] == 0, v

# 3. Get it: the steps to keep; each phone counts once; the maker's own does not count
g = run(main.status_get(sid, **H("viewer")))
assert g["title"] and [s["m"] for s in g["steps"]][:2] == [["Drive"], ["Create new"]] and g["steps"][1]["a"] == DRIVE, g
run(main.status_get(sid, **H("viewer"))); run(main.status_get(sid, **H("maker"))); run(main.status_get(sid, **H("viewer2")))
assert main._store.kv_get("status", sid)["gets"] == 2
assert run(main.status_list(**H("maker")))["mine"][0]["gets"] == 2              # the maker sees how many got it

# 4. The automatic check: nothing about money, passwords, personal numbers, links, or the phone's safety
def bad(title, steps, word):
    e = err(main.status_post(main.StatusIn(title=title, steps=steps), **H("maker2")))
    assert e is not None and e.status_code == 400 and word in e.detail, (title, e and e.detail)
bad("Send money to my sister", st("Airtel Money", "Send money"), "money")
bad("Call my sister", st("Contacts", "0977123456"), "personal numbers")
bad("Get free data", st("Chrome", "www.freedata.xyz"), "link")
bad("Install a better WhatsApp", st("Settings", "Install unknown apps", "Allow from this source"), "safe")
bad("Let my friend help me", st("Play Store", "AnyDesk", "Install"), "safe")
bad("Pay a bill", st("Settings"), "money")
bad("ab", st("Settings"), "name")
bad("Check my balance", [{"m": ["Balance"], "s": {"en": "Tap “Balance”."}, "a": "com.mtn.momo"}], "money")
assert main._store.kv_list("status", 100)[0][0] == sid                           # none of them was posted

# 5. Reports: three different phones hide it; the maker's own report and repeats do not count
for who in ("maker", "r1", "r1"):
    run(main.status_report(sid, main.ReportIn(why="wrong steps"), **H(who)))
assert not main._store.kv_get("status", sid)["hidden"]
run(main.status_report(sid, main.ReportIn(why="call 0977123456"), **H("r2")))
assert not main._store.kv_get("status", sid)["hidden"]
run(main.status_report(sid, main.ReportIn(why="rude"), **H("r3")))
assert main._store.kv_get("status", sid)["hidden"] and "0977123456" not in json.dumps(main._store.kv_get("statusr", sid))
assert run(main.status_list(**H("viewer")))["items"] == []
assert err(main.status_get(sid, **H("viewer3"))).status_code == 404
assert err(main.status_view(sid, **H("viewer3"))).status_code == 404
# The owner looks, and shows it again
page = run(main.admin_status(key="k", show=sid)).body
assert "shown again" in page and "Reports" in page
assert not main._store.kv_get("status", sid)["hidden"]
assert err(main.admin_status(key="wrong")) is not None

# 6. Only its maker removes it
assert err(main.status_remove(sid, **H("viewer"))).status_code == 403
run(main.status_remove(sid, **H("maker")))
assert main._store.kv_get("status", sid) is None and run(main.status_list(**H("viewer")))["items"] == []

# 7. Limits: five a day
for n in range(5):
    run(main.status_post(main.StatusIn(title="Task number %s" % "abcde"[n], steps=st("Settings", "Display")), **H("busy")))
e = err(main.status_post(main.StatusIn(title="Task number f", steps=st("Settings", "Display")), **H("busy")))
assert e.status_code == 429, e
assert main.SERVER_VERSION >= "0.99"
print("status: post after a check, everyone sees it, one tap gets it, reports hide it, only its maker removes it")
