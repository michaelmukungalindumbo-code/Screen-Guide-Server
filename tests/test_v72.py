import os, asyncio, json, time
os.environ.update(ADMIN_KEY="owner-secret", GOOGLE_CLIENT_ID="web-123.apps.googleusercontent.com")
os.environ.pop("DATABASE_URL", None)
import main
from fastapi import HTTPException
run = asyncio.run
def err(f):
    try: run(f()); return None
    except HTTPException as e: return e

# A pretend Upstash: the Redis commands the server uses, kept in a dict
class FakeRedis:
    def __init__(self): self.d, self.calls = {}, []
    def __call__(self, cmd):
        self.calls.append(cmd); op, a = cmd[0], cmd[1:]
        if op == "GET": return self.d.get(a[0])
        if op == "SET": self.d[a[0]] = a[1]; return "OK"
        if op == "DEL": return int(self.d.pop(a[0], None) is not None)
        if op == "MGET": return [self.d.get(k) for k in a]
        if op == "SADD": self.d.setdefault(a[0], set()).add(a[1]); return 1
        if op == "SREM": self.d.setdefault(a[0], set()).discard(a[1]); return 1
        if op == "SCARD": return len(self.d.get(a[0], set()))
        if op == "ZADD": self.d.setdefault(a[0], {})[a[2]] = float(a[1]); return 1
        if op == "ZREM": self.d.setdefault(a[0], {}).pop(a[1], None); return 1
        if op == "ZREVRANGE":
            z = sorted(self.d.get(a[0], {}).items(), key=lambda kv: -kv[1]); return [m for m, _ in z][int(a[1]):int(a[2]) + 1]
        raise AssertionError("command not expected: %s" % cmd)
redis = FakeRedis()
main._upstash_sync = redis
async def fake_upstash(cmd): return redis(cmd)
main._upstash = fake_upstash
main.UPSTASH_URL, main.UPSTASH_TOKEN = "https://example.upstash.io", "t"

async def fake_google(tok):
    return {"bad": None, "michael": {"sub": "111", "email": "m@example.com", "name": "Michael"},
            "other": {"sub": "222", "email": "o@example.com", "name": "Other"}}.get(tok)
main._verify_google = fake_google
H = dict(x_app_token="tok")

# Sign-in on the free plan: accounts are kept in Upstash (no database), so they survive a restart
assert main._store.kind == "Upstash"
assert run(main.config())["accounts"] is True
r = run(main.auth_google(main.GoogleIn(id_token="michael"), x_install_id="phone1", **H))
sess = r["session"]; assert r["name"] == "Michael"
assert main._store.count() == 1 and json.loads(redis.d["sg:user:g:111"])["email"] == "m@example.com"
run(main.me_save(main.MeIn(profile={"lang": "ny"}, learned=[]), x_install_id="phone1", x_session=sess, **H))
main._store.mem.clear()                                                # a restart: nothing in memory
r2 = run(main.auth_google(main.GoogleIn(id_token="michael"), x_install_id="phone2", **H))
assert r2["profile"]["lang"] == "ny", r2                               # settings came back on a new phone
o = run(main.auth_google(main.GoogleIn(id_token="other"), x_install_id="phone3", **H))
assert o["profile"] == {} and main._store.count() == 2
run(main.me_delete(x_install_id="phone1", x_session=sess, **H))
assert main._store.get("g:111") is None and "sg:user:g:111" not in redis.d and main._store.count() == 1
assert err(lambda: main.me(x_install_id="phone1", x_session=sess, **H)).status_code == 401

# Shared, learned and official guides are kept there too, newest first
main._store.kv_put("share", "ABC123", {"title": "Turn on Wi-Fi"}); time.sleep(0.01)
main._store.kv_put("share", "XYZ789", {"title": "Send a photo"})
assert main._store.kv_get("share", "ABC123") == {"title": "Turn on Wi-Fi"}
assert [k for k, _ in main._store.kv_list("share", 10)] == ["XYZ789", "ABC123"]
assert main._store.kv_list("share", 1) == [("XYZ789", {"title": "Send a photo"})]
main._store.kv_delete("share", "XYZ789")
assert main._store.kv_get("share", "XYZ789") is None and [k for k, _ in main._store.kv_list("share", 10)] == ["ABC123"]
assert main._store.kv_list("official", 10) == []

# The owner report says where accounts are kept, and no longer warns about memory
rep = run(main.admin_report(key="owner-secret")).body
assert "Accounts: <b>1</b> (Upstash)" in rep and "Sign-in is on" in rep and "only in memory" not in rep, rep[:400]

# A database, when set, still comes first; with neither, memory (and the report warns)
main.DATABASE_URL = "sqlite:"; main._store = main._Store("sqlite:")
assert main._store.kind == "database"
main.DATABASE_URL = ""; main.UPSTASH_URL = ""; main._store = main._Store("")
assert main._store.kind == "memory"
assert "only in memory" in run(main.admin_report(key="owner-secret")).body
assert main.SERVER_VERSION >= "0.72"
print("accounts kept in upstash")
