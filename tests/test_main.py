import asyncio, json, main
from fastapi import HTTPException
replies = []
async def fake(system, question, images=None, kind="ask", schema=None, **kw):
    fake.last = (system, question, images)
    return replies.pop(0)
main._complete = fake
run = asyncio.run

# 1. the ring bug: AI drops the tag
labels = ["Settings [tap]", "Personal Hotspot [switch]", "Portable hotspot [text]", "Wi-Fi [tap]"]
for ai_label, want in [("Settings", "Settings"), ("Settings [tap]", "Settings"), ('"settings"', "Settings"),
                       ("Personal Hotspot", "Personal Hotspot"), ("wi fi", "Wi-Fi"), ("Bluetooth", None), (None, None)]:
    replies.append(json.dumps({"label": ai_label, "say": "Tap it.", "done": False}))
    r = run(main.next_step(main.Next(goal="g", labels=labels), x_app_token="tok", x_install_id="i"))
    assert r["label"] == want, (ai_label, r); assert r["x"] is None
print("label matching ok")

# 2. picture: x,y only when no label and a picture was sent
replies.append(json.dumps({"label": None, "say": "Tap the plus.", "done": False, "x": 0.5, "y": 0.92}))
r = run(main.next_step(main.Next(goal="g", labels=labels, image="AAAA", plan=["Open YouTube", "Tap plus"]), x_app_token="tok", x_install_id="i"))
assert r["x"] == 0.5 and r["y"] == 0.92 and r["label"] is None, r
assert "picture of the user's screen" in fake.last[0] and fake.last[2] == ["AAAA"] and "<plan>1. Open YouTube" in fake.last[1]
replies.append(json.dumps({"label": None, "say": "x", "done": False, "x": 1.7, "y": 0.2}))
r = run(main.next_step(main.Next(goal="g", labels=labels, image="AAAA"), x_app_token="tok", x_install_id="i"))
assert r["x"] is None and r["y"] is None
replies.append(json.dumps({"label": None, "say": "x", "done": False, "x": 0.4, "y": 0.2}))
r = run(main.next_step(main.Next(goal="g", labels=labels), x_app_token="tok", x_install_id="i"))
assert r["x"] is None, "no picture, no point"
print("picture points ok")

# 3. /ask returns goal and plan only for guides
replies.append(json.dumps({"kind": "guide", "text": "Use the Clock app. Tap Show me and I will point to each step.", "goal": "Set a reminder in the Clock app", "plan": ["Open Clock", "Tap +"], "needs_apps": False}))
r = run(main.ask(main.Ask(question="how do I set a reminder"), x_app_token="tok", x_install_id="i"))
assert r["kind"] == "guide" and r["goal"].startswith("Set a reminder") and r["plan"] == ["Open Clock", "Tap +"], r
replies.append(json.dumps({"kind": "answer", "text": "Yes, I am an AI helper.", "goal": "x", "plan": ["y"]}))
r = run(main.ask(main.Ask(question="are you AI?", history=["User: hi", "Helper: hello"]), x_app_token="tok", x_install_id="i"))
assert r["kind"] == "answer" and r["goal"] == "" and r["plan"] == [], r
assert "<conversation>" in fake.last[1] and "<user_message>" in fake.last[1]
# cut-off reply: readable words, no raw code
replies.append('{"kind": "guide", "text": "Open the Clock app.\\nTap the plus sign", "goal": "Set a rem')
r = run(main.ask(main.Ask(question="q cut one"), x_app_token="tok", x_install_id="i"))
assert r["answer"] == "Open the Clock app." and r["kind"] == "guide", r
replies.append('{"kind": "answer", "text": "A SIM card is a small chip')
r = run(main.ask(main.Ask(question="q cut two"), x_app_token="tok", x_install_id="i"))
assert "_partial" not in r and r["answer"] == "A SIM card is a small chip\u2026", r
replies.append(json.dumps({"kind": "answer", "text": "fresh answer"}))
r = run(main.ask(main.Ask(question="q cut two"), x_app_token="tok", x_install_id="i"))
assert r["answer"] == "fresh answer", "a cut-off reply must not be reused"
replies.append("Plain text reply")
r = run(main.ask(main.Ask(question="q plain"), x_app_token="tok", x_install_id="i"))
assert r["answer"] == "Plain text reply" and r["kind"] == "answer"
print("ask ok")

# 4. token checks and self-test limit
for f in (lambda: main.ask(main.Ask(question="q"), x_app_token="bad", x_install_id="i"),
          lambda: main.selftest(token="bad")):
    try: run(f()); raise SystemExit("token not checked")
    except HTTPException as e: assert e.status_code == 401
for n in range(3):
    replies.extend([json.dumps({"kind": "answer", "text": "t%d" % i}) for i in range(len(main.SELFTEST))])
    page = run(main.selftest(token="tok")).body
    assert page.count("<tr>") == len(main.SELFTEST) + 1, page[:300]
try: run(main.selftest(token="tok")); raise SystemExit("limit not applied")
except HTTPException as e: assert e.status_code == 429
print("selftest ok;", len(main.SELFTEST), "questions")
