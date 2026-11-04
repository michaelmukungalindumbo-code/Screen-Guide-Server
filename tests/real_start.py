# Starts the server with the real libraries (not the stand-ins in tests/stubs) and opens a few pages, so a change that
# only breaks on Render (an import, a startup or shutdown hook, a page) is caught before it is deployed. No AI is called.
from fastapi.testclient import TestClient
import main

with TestClient(main.app) as c:   # runs the startup and shutdown hooks too
    assert c.get("/health").json() == {"ok": True}
    assert c.get("/version").json()["server"] == main.SERVER_VERSION
    r = c.get("/admin/report", params={"key": "ci"})
    assert r.status_code == 200 and "Real users" in r.text and "Launch Bay" in r.text, r.text[:300]
    r = c.post("/event", json={"event": "start", "guide": "ai"}, headers={"x-app-token": "ci", "x-install-id": "ci-phone"})
    assert r.status_code == 200 and r.json() == {"ok": True}, r.text
    assert main._counts[main._today()]["guides"]["start"] == 1
    assert c.get("/privacy").status_code == 200
print("the server starts with the real libraries")
