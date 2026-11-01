import asyncio, json
import main
run = asyncio.run
replies = []
async def fake(system, question, images=None, kind="ask", schema=None, **kw):
    fake.q = question; fake.sys = system
    return replies.pop(0) if replies else ""
main._complete = fake

# 1. the recording: "What is YouTube?" then "I want to use it" -> a goal that names YouTube
hist = ["User: What is YouTube", "Helper: YouTube is a website and an app. People use it to watch videos."]
replies[:] = [json.dumps({"kind": "guide", "text": "Find the red YouTube app and tap it.", "goal": "Use it", "plan": [], "needs_apps": False})]
r = run(main._answer("I want to use it", "en", [], hist))
assert "YouTube" in r["goal"], r
replies[:] = [json.dumps({"kind": "guide", "text": "x", "goal": "", "plan": [], "needs_apps": False})]
assert "YouTube" in run(main._answer("I want to use it", "en", [], hist))["goal"]
replies[:] = [json.dumps({"kind": "guide", "text": "x", "goal": "Open the YouTube app", "plan": [], "needs_apps": False})]
assert run(main._answer("I want to use it", "en", [], hist))["goal"] == "Open the YouTube app", "a clear goal is left alone"
assert 'never write "it"' in main.SYSTEM
print("goal ok")

# 2. the step helper never asks the person to talk to it
assert "cannot talk or type to you" in main.NEXT_SYSTEM
print("no voice asks ok")

# 3. "Tap Phone to make a call." with no label still rings Phone (not Phone Master)
labels = ["Messages [tap]", "Phone [tap]", "Phone Master [tap]", "YouTube [tap]", "Recent Apps [text]"]
def step(reply, labs=labels, goal="Make a call"):
    replies[:] = [json.dumps(reply)]
    return run(main.next_step(main.Next(goal=goal, labels=labs), x_app_token="tok", x_install_id="lbl"))
r = step({"label": None, "say": "Tap Phone to make a call.", "done": False, "x": None, "y": None})
assert r["label"] == "Phone", r
r = step({"label": None, "say": "Tap Phone Master.", "done": False, "x": None, "y": None})
assert r["label"] == "Phone Master", r
r = step({"label": None, "say": "Swipe up to see all your apps.", "done": False, "x": None, "y": None})
assert r["label"] is None, r
r = step({"label": None, "say": "Tap Recent Apps.", "done": False, "x": None, "y": None})
assert r["label"] is None, "plain text cannot be tapped"
r = step({"label": None, "say": "Tap Send money.", "done": False, "x": None, "y": None}, labs=labels + ["Send money [tap]"])
assert r["label"] is None and "yourself" in r["say"], "the safety rule still applies"
r = step({"label": None, "say": "Dinani YouTube.", "done": False, "x": None, "y": None})
assert r["label"] == "YouTube", r
print("label from words ok")
