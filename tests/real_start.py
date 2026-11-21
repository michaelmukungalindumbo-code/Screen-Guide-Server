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
    # 0.99 Status: post, list, look, get, report and remove, through the real web framework
    h, v = {"x-app-token": "ci", "x-install-id": "ci-maker"}, {"x-app-token": "ci", "x-install-id": "ci-viewer"}
    r = c.post("/status", json={"title": "Turn on the torch", "steps": [{"m": ["Torch"], "s": {"en": "Tap “Torch”."}}]}, headers=h)
    assert r.status_code == 200, r.text
    sid = r.json()["id"]
    assert c.get("/status", headers=v).json()["items"][0]["id"] == sid
    assert c.get("/status/" + sid, headers=v).json()["says"] == ["Tap “Torch”."]
    assert c.post("/status/%s/get" % sid, headers=v).json()["steps"][0]["m"] == ["Torch"]
    assert c.post("/status/%s/report" % sid, json={"why": "test"}, headers=v).json() == {"ok": True}
    assert c.post("/status/%s/remove" % sid, headers=v).status_code == 403
    assert c.post("/status/%s/remove" % sid, headers=h).json() == {"ok": True}
    assert c.post("/status", json={"title": "Send money", "steps": [{"m": ["Send money"], "s": {"en": "x"}}]}, headers=h).status_code == 400
print("the server starts with the real libraries")
