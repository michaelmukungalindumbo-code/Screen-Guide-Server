import asyncio, json
import main
run = asyncio.run
class URL: path = "/ask"
class Req: method = "POST"; url = URL()
r = run(main._not_found(Req(), None))
assert r.status_code == 404 and "/ask" in r.body["detail"] and "latest main.py" in r.body["detail"] and main.STATS["not_found"] == 1
v = run(main.version()); assert v["server"] == main.SERVER_VERSION
print("not found and version ok")
