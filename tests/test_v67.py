import os, asyncio, json
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run

# 3 Nov: "Test an app" with no goal (the goal is optional) was reported as "No guidance given during the test".
# With no goal ScreenGuide only watches, so it has nothing to say. That is not a problem.
seen = []
async def fake_ai(system, user, images, tag, schema, valid):
    seen.append((system, user))
    return None, {"problems": [
        {"step": 1, "kind": "review", "title": "No guidance given during the test", "what": "The goal is empty, so the person was never told what to do.", "fix": "Set a goal."},
        {"step": 1, "kind": "review", "title": "Menu button has no words", "what": "The Menu button is read as … only.", "fix": "Give it a name."}]}
main._ai_json = fake_ai

def session(goal):
    return {"kind": "test", "app": "App", "goal": goal, "problems": [], "end": "", "t": 0,
            "steps": [{"n": 1, "screen": ["Chats [tap]", "New chat [tap]", "Speak [tap]"], "told_before": "", "note": "", "stuck": False,
                       "label": None, "say": "", "picture": False, "secs": 0}]}

cards = run(main._watch_review_cards(session("")))
titles = [c["title"] for c in cards]
assert "No guidance given during the test" not in titles, titles       # no goal: nothing was meant to be said
assert "Menu button has no words" in titles, titles                    # real findings stay
assert "watching only" in seen[-1][1].lower(), seen[-1][1]

cards = run(main._watch_review_cards(session("Upload a video")))
assert "No guidance given during the test" in [c["title"] for c in cards]   # with a goal, silence is still a problem
print("ok")
