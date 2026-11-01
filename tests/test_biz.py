import os, sys, asyncio, json, time
os.environ.update(ADMIN_KEY="owner-secret", FREE_ASK_PER_DAY="3", FREE_STEPS_PER_DAY="2", PLUS_ASK_PER_DAY="6", PLUS_STEPS_PER_DAY="5",
                  REVOKED_BATCHES="9", PRICE_IN_PER_MILLION="1", PRICE_OUT_PER_MILLION="5", PHONES_PER_CODE="2")
import main
from fastapi import HTTPException
run = asyncio.run
calls = []
async def fake(system, question, images=None, kind="ask", schema=None, **kw):
    calls.append(kind); main._count(kind, 400, 120)
    return json.dumps({"kind": "answer", "text": "ok %d" % len(calls)})
main._complete = fake
def err(f):
    try: run(f()); return None
    except HTTPException as e: return e

# codes
c1, c2 = main.make_code(4, 1, 1), main.make_code(4, 1, 2)
assert c1 != c2 and len(c1) == 15, (c1, c2)
assert main.read_code(c1) == (4, 1, 1) and main.read_code(c1.lower().replace("-", " ")) == (4, 1, 1)
bad = c1[:-1] + ("0" if c1[-1] != "0" else "1")
assert main.read_code(bad) is None and main.read_code("hello") is None
assert main.read_code(main.make_code(2, 9, 5)) is None, "revoked batch"
oc = main.make_code(3, 2, 7).replace("0", "O")
assert main.read_code(oc) == (3, 2, 7), "O typed for 0"
print("codes ok:", c1, c2)

# redeem and plan
r = run(main.redeem(main.Redeem(code=c1), x_app_token="tok", x_install_id="phoneA"))
p = r["pass"]
assert r["plan"] == "plus" and abs(r["expires"] - (time.time() + 28 * 86400)) < 5
assert main.plan_of(p, "phoneA")[0] == "plus" and main.plan_of(p, "phoneB")[0] == "free" and main.plan_of(p + "x", "phoneA")[0] == "free"
run(main.redeem(main.Redeem(code=c1), x_app_token="tok", x_install_id="phoneB"))
e = err(lambda: main.redeem(main.Redeem(code=c1), x_app_token="tok", x_install_id="phoneC"))
assert e and "already been used" in e.detail
e = err(lambda: main.redeem(main.Redeem(code=bad), x_app_token="tok", x_install_id="phoneD"))
assert e and e.status_code == 400
pl = run(main.plan(x_app_token="tok", x_install_id="phoneA", x_pass=p))
assert pl["plan"] == "plus" and pl["per_day"] == 6
print("redeem ok")

# daily limits: free 3 questions, plus 6
for i in range(3):
    run(main.ask(main.Ask(question="question %d about phone" % i), x_app_token="tok", x_install_id="free1"))
e = err(lambda: main.ask(main.Ask(question="one more question"), x_app_token="tok", x_install_id="free1"))
assert e and e.status_code == 429 and "free questions" in e.detail and "code" in e.detail, e and e.detail
for i in range(6):
    r = run(main.ask(main.Ask(question="plus question %d" % i), x_app_token="tok", x_install_id="phoneA", x_pass=p))
assert r["tier"] == "plus" and r["left"] == 0
e = err(lambda: main.ask(main.Ask(question="plus extra"), x_app_token="tok", x_install_id="phoneA", x_pass=p))
assert e and "comes back tomorrow" in e.detail
print("limits ok")

# cache: same question again costs nothing and does not use the allowance
n = len(calls)
r1 = run(main.ask(main.Ask(question="What is a SIM card?"), x_app_token="tok", x_install_id="c1"))
r2 = run(main.ask(main.Ask(question="what is a sim card"), x_app_token="tok", x_install_id="c2"))
assert len(calls) == n + 1 and r1["answer"] == r2["answer"] and r2["left"] == 3
run(main.ask(main.Ask(question="what is a sim card", history=["User: hi"]), x_app_token="tok", x_install_id="c3"))
run(main.ask(main.Ask(question="is 4821 a good pin"), x_app_token="tok", x_install_id="c3"))
run(main.ask(main.Ask(question="is 4821 a good pin"), x_app_token="tok", x_install_id="c4"))
assert len(calls) == n + 4, "history and numbers are never cached"
print("cache ok")

# step limits
labels = ["Settings [tap]"]
async def fake_step(system, question, images=None, kind="step", schema=None, **kw):
    main._count(kind, 900, 40); return json.dumps({"label": "Settings", "say": "Tap Settings.", "done": False})
main._complete = fake_step
for i in range(2):
    run(main.next_step(main.Next(goal="g", labels=labels), x_app_token="tok", x_install_id="s1"))
e = err(lambda: main.next_step(main.Next(goal="g", labels=labels), x_app_token="tok", x_install_id="s1"))
assert e and "step-by-step" in e.detail
print("step limits ok")

# guides, events, privacy, owner pages
g = run(main.guides(x_app_token="tok"))
import json as _j, os as _o
_want = _j.load(open(_o.path.join(_o.path.dirname(_o.path.abspath(main.__file__)), "guides.json")))
_items = _want.get("guides", []) if isinstance(_want, dict) else _want
assert len(g.body["guides"]) == len(_items) >= 9 and g.body["version"] >= 1, (g.body["version"], len(g.body["guides"]))
for ev in [("start", "wifi"), ("done", "wifi"), ("start", "ai"), ("stop", "ai"), ("start", "Wi-Fi<script>")]:
    run(main.event(main.Event(event=ev[0], guide=ev[1]), x_app_token="tok", x_install_id="e1"))
assert main.STATS["done:wifi"] == 1 and main.STATS["start:wi-fiscript"] == 1
assert "<script>" not in run(main.admin_report(key="owner-secret")).body
assert "ScreenGuide privacy policy" in run(main.privacy()).body
assert err(lambda: main.admin_report(key="wrong")).status_code == 401
assert err(lambda: main.admin_codes(key="")).status_code == 401
page = run(main.admin_codes(key="owner-secret", weeks=4, count=3, batch=1, start=10)).body
assert page.count("<tr><td>") == 3 and main.make_code(4, 1, 10) in page
rep = run(main.admin_report(key="owner-secret")).body
assert "AI cost per finished guide" in rep and "$" in rep
print("pages ok")
import re
print(re.sub(r"<[^>]+>", " ", rep.split("<h3>AI use</h3>")[1].split("<h3>Other")[0])[:600])
