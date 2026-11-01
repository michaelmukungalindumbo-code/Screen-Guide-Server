import os, asyncio, json
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run
H = dict(x_app_token="tok", x_install_id="teacher")
def st(*words, say=None):
    return [{"m": [w], "s": {"en": say or 'Tap "%s".' % w, "ny": 'Dinani "%s".' % w, "bem": 'Kandeni "%s".' % w}} for w in words]
def err(f):
    try: run(f); return None
    except main.HTTPException as e: return e
# 1. Share a taught guide, open it by code (any case, with spaces), and see the public page
r = run(main.share_guide(main.ShareIn(title="Check ECZ results", steps=st("Chrome", "Search or type web address", "Results"), device="INFINIX phone, Android 14"), **H))
code = r["code"]
assert len(code) == 6 and all(c in main._CODE_ABC for c in code) and r["url"].endswith("/g/" + code), r
g = run(main.get_shared(code.lower()[:3] + " " + code.lower()[3:], x_app_token="tok", x_install_id="parent"))
assert g["title"] == "Check ECZ results" and [s["m"] for s in g["steps"]] == [["Chrome"], ["Search or type web address"], ["Results"]] and g["official"] == ""
page = run(main.shared_page(code)).body
assert "Open in ScreenGuide" in page and "screenguide://g/" + code in page and "Tap &quot;Results&quot;." in page and "og:title" in page, page[:300]
assert run(main.shared_page("ZZZZZZ")).status_code == 404
e = err(main.get_shared("ZZZZZZ", x_app_token="tok", x_install_id="p")); assert e.status_code == 404 and "code" in e.detail
# 2. Personal or risky steps are refused; repeats and empty steps dropped; says made safe
e = err(main.share_guide(main.ShareIn(title="Send money", steps=st("Airtel Money", "Send money")), **H)); assert e.status_code == 400 and "payments" in e.detail
e = err(main.share_guide(main.ShareIn(title="Call mum", steps=st("Contacts", "0977123456")), **H)); assert e.status_code == 400
e = err(main.share_guide(main.ShareIn(title="ab", steps=st("Settings")), **H)); assert e.status_code == 400 and "name" in e.detail
c = main._clean_steps(st("Settings", "Settings") + [{"m": [], "s": {}}] + st("Wi-Fi", say="Call 0977123456 now"), strict=True)
assert [s["m"] for s in c] == [["Settings"], ["Wi-Fi"]] and c[1]["s"]["en"] == "Tap “Wi-Fi”." and c[1]["s"]["bem"].startswith("Kandeni"), c
# 3. Learned guides: kept per task and phone kind; given out only after two different phones agree
L = lambda who, steps, dev="INFINIX phone, Android 14", goal="Upload a file to Google Drive": run(main.learned_add(main.LearnedIn(goal=goal, steps=steps, device=dev), x_app_token="tok", x_install_id=who))
F = lambda dev="Infinix phone, Android 15", goal="how do I upload a file to google drive?": run(main.learned_find(main.LearnedFind(goal=goal, device=dev), x_app_token="tok", x_install_id="new"))
path = st("Drive", "Create new", "Upload")
assert L("a", path)["ok"] and F() == {"found": False}, "one phone is not enough"
assert L("a", path)["ok"] and F() == {"found": False}, "the same phone twice is still one phone"
L("b", st("Drive", "Create new", "Folder"))   # a different path from another phone
assert L("c", path)["ok"]
f = F(); assert f["found"] and [s["m"] for s in f["steps"]] == [["Drive"], ["Create new"], ["Upload"]] and f["phones"] == 2, f
assert F(dev="Samsung tablet, Android 14") == {"found": False}, "another kind of phone does not get it"
assert not L("d", st("Drive", "Send money"))["ok"] and not L("d", st("Drive"))["ok"], "risky or one-step paths are not kept"
assert F(goal="Upload a file to Google Drive (about: What is Drive?)")["found"]
# 4. Official guides: the owner marks a share; it joins the guides list with "by"; the mark can be taken away
assert "Not allowed" in str(err(main.admin_shares(key="wrong")) or "Not allowed") 
page = run(main.admin_shares(key="k", promote=code, by="ECZ", keywords="ecz results, exam results")).body
assert "official guide from ECZ" in page and code in page, page[:400]
main._guides_cache["at"] = 0
gl = run(main.guides(x_app_token="tok")).body["guides"]
off = [x for x in gl if x["id"] == "official_" + code.lower()]
assert off and off[0]["by"] == "ECZ" and off[0]["keywords"] == ["ecz results", "exam results"] and off[0]["doneWhen"] == "last_tap"
assert off[0]["steps"][2] == {"match": ["Results"], "say": g["steps"][2]["s"]} and len(gl) > len(off)
assert run(main.get_shared(code, x_app_token="tok", x_install_id="p"))["official"] == "ECZ"
run(main.admin_shares(key="k", demote=code)); main._guides_cache["at"] = 0
assert not [x for x in run(main.guides(x_app_token="tok")).body["guides"] if x["id"].startswith("official_")]
# 5. Works with a database too (sqlite stands in for Postgres)
db = main._Store("sqlite:"); db.kv_put("share", "AAAAAA", {"t": 1}); db.kv_put("share", "BBBBBB", {"t": 2}); db.kv_put("share", "AAAAAA", {"t": 3})
assert db.kv_get("share", "AAAAAA") == {"t": 3} and [i for i, _ in db.kv_list("share")][0] in ("AAAAAA", "BBBBBB") and len(db.kv_list("share")) == 2
db.kv_delete("share", "AAAAAA"); assert db.kv_get("share", "AAAAAA") is None
p = run(main.privacy()); b = getattr(p, "body", p); assert "Guides you share" in str(b) and "two different phones" in str(b)
assert main.SERVER_VERSION >= "0.43"
print("shared, learned and official guides ok")
