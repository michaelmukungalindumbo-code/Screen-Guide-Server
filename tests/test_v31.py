import os, asyncio, json, time
os.environ.update(ADMIN_KEY="owner-secret", GOOGLE_CLIENT_ID="web-123.apps.googleusercontent.com", DATABASE_URL="sqlite:")
import main
from fastapi import HTTPException
run = asyncio.run
def err(f):
    try: run(f()); return None
    except HTTPException as e: return e

async def fake_google(tok):
    return {"bad": None, "michael": {"sub": "111", "email": "m@example.com", "name": "Michael"},
            "other": {"sub": "222", "email": "o@example.com", "name": "Other"}}.get(tok)
main._verify_google = fake_google
H = dict(x_app_token="tok")

# 1. config tells the app whether sign-in is on, and which Google client to use
c = run(main.config()); assert c["accounts"] and c["google_client_id"].startswith("web-123")
# 2. sign-in: rejected token, then a new account; the same person again finds the same account
assert err(lambda: main.auth_google(main.GoogleIn(id_token="bad"), x_install_id="phone1", **H)).status_code == 401
r = run(main.auth_google(main.GoogleIn(id_token="michael"), x_install_id="phone1", **H))
sess = r["session"]; assert r["name"] == "Michael" and r["plan"]["tier"] == "free" and r["profile"] == {}
assert main.read_session(sess) == "g:111" and main.read_session(sess[:-1] + "x") is None, "sessions cannot be forged"
assert main._store.count() == 1
# 3. settings and learned tasks are saved, cleaned, and come back on a new phone
prof = {"name": "Michael", "lang": "ny", "voice": True, "rate": "slow", "evil": "x" * 500, "text": "z" * 99}
learned = [{"k": "upload video youtube", "t": "Upload a video on YouTube", "sw": False,
            "st": [{"m": ["YouTube"], "s": {"en": "Tap YouTube."}}, {"m": ["Create"], "s": {"en": "Tap Create."}}]}, {"junk": 1}]
run(main.me_save(main.MeIn(profile=prof, learned=learned), x_install_id="phone1", x_session=sess, **H))
r2 = run(main.auth_google(main.GoogleIn(id_token="michael"), x_install_id="phone2", **H))
assert r2["profile"]["lang"] == "ny" and "evil" not in r2["profile"] and len(r2["profile"]["text"]) == 40, r2["profile"]
assert len(r2["learned"]) == 1 and r2["learned"][0]["st"][1]["m"] == ["Create"]
assert run(main.me(x_install_id="phone2", x_session=r2["session"], **H))["learned"][0]["t"] == "Upload a video on YouTube"
assert err(lambda: main.me(x_install_id="phone2", x_session="nonsense", **H)).status_code == 401
# 4. a Plus plan bought while signed in follows the account to a new phone (with a pass for that phone)
code = main.make_code(4, 7, 1)
run(main.redeem(main.Redeem(code=code), x_install_id="phone1", x_session=sess, **H))
r3 = run(main.auth_google(main.GoogleIn(id_token="michael"), x_install_id="phone3", **H))
assert r3["plan"]["tier"] == "plus" and main.plan_of(r3["plan"]["pass"], "phone3")[0] == "plus" and main.plan_of(r3["plan"]["pass"], "phone9")[0] == "free"
# 5. another person sees nothing of Michael's
o = run(main.auth_google(main.GoogleIn(id_token="other"), x_install_id="phone4", **H))
assert o["profile"] == {} and o["learned"] == [] and o["plan"]["tier"] == "free"
# 6. delete: gone, and the old session no longer finds anything
run(main.me_delete(x_install_id="phone1", x_session=sess, **H))
assert main._store.get("g:111") is None and err(lambda: main.me(x_install_id="phone1", x_session=sess, **H)).status_code == 401
assert main._store.count() == 1
# 7. pages: deletion page, privacy mentions accounts, report shows accounts
assert "Delete your ScreenGuide account" in run(main.account_delete_page()).body
assert "Your account (optional)" in run(main.privacy()).body
rep = run(main.admin_report(key="owner-secret")).body
assert "Accounts: <b>1</b> (database)" in rep and "Sign-in is on" in rep, rep[:300]
# 8. without GOOGLE_CLIENT_ID sign-in is off and says so
main.GOOGLE_CLIENT_ID = ""
assert run(main.config())["accounts"] is False
assert err(lambda: main.auth_google(main.GoogleIn(id_token="michael"), x_install_id="p", **H)).status_code == 503
print("accounts ok")
