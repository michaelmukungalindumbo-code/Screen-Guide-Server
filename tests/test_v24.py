import asyncio, json
import main
run = asyncio.run
replies = []
async def fake(system, question, images=None, kind="ask", schema=None, **kw):
    fake.kw = kw; return replies.pop(0) if replies else ""
main._complete = fake

# 1. the screenshot case: a cut-off reply never ends on a dangling word
cut = '{"kind": "guide", "text": "Open your mobile money menu, choose Send Money, and'
replies[:] = [cut, cut, cut]
r = run(main._answer("How do I send money?", "en", [], []))
assert not r["answer"].endswith("and"), r
assert r["answer"].endswith("…") or r["answer"][-1] in ".!?", r
replies[:] = ['{"kind": "answer", "text": "Open the app. Tap Settings. Then tap the', "x", "x"]
r = run(main._answer("q one", "en", [], []))
assert r["answer"] == "Open the app. Tap Settings.", r
print("cut-off ok")

# 2. money questions are advice, never a Show me guide
replies[:] = [json.dumps({"kind": "guide", "text": "Dial your mobile money code and choose Send Money. Check the name before you confirm. Tap Show me and I will point to each step.",
                          "goal": "Send money with mobile money", "plan": ["Dial", "Choose Send Money"], "needs_apps": False})]
r = run(main._answer("How do I send money?", "en", [], []))
assert r["kind"] == "answer" and r["goal"] == "" and r["plan"] == [] and "Show me" not in r["answer"] and "Check the name" in r["answer"], r
for q in ("how do i withdraw from airtel money", "send money to my mum on momo", "how to pay a bill"):
    replies[:] = [json.dumps({"kind": "guide", "text": "Do it. Tap Show me and I will point to each step.", "goal": "x", "plan": [], "needs_apps": False})]
    assert run(main._answer(q, "en", [], []))["kind"] == "answer", q
for q in ("how do I turn on wifi", "how do I buy data bundles", "how do I upload a video on youtube"):
    replies[:] = [json.dumps({"kind": "guide", "text": "Tap Show me and I will point to each step.", "goal": "Do it", "plan": ["a"], "needs_apps": False})]
    assert run(main._answer(q, "en", [], []))["kind"] == "guide", q
assert "Money tasks" in main.SYSTEM and "never mention Show me" in main.SYSTEM
print("money ok")
