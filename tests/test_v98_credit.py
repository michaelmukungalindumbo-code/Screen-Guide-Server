import os, asyncio, json
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run
A = json.dumps({"kind": "answer", "text": "Open Facebook, tap Marketplace, then Sell.", "goal": "", "plan": [], "needs_apps": False})
class NoCredit(Exception):
    status_code = 400
    def __init__(self): super().__init__("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': "
                                         "'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing "
                                         "to upgrade or purchase credits.'}}")
class Msgs:
    def __init__(self): self.calls = []
    async def create(self, **kw):
        self.calls.append(kw); raise NoCredit()
class Client:
    def __init__(self): self.messages = Msgs()
main.settings.ANTHROPIC_API_KEY = main.settings.ANTHROPIC_API_KEY or "test"

# The owner's phone (19 Nov): "How do I sell something on Facebook Marketplace?" got "The helper isn't available at the
# moment", and again after Try again. The AI account's credit had run out: the real-AI check that morning said "Your
# credit balance is too low". Every question failed at once as a "wrong request": no backup tried, nobody told.
assert main._no_credit(NoCredit())
assert not main._no_credit(Exception("Error code: 400 - image too large"))
assert not main._no_credit(Exception("overloaded"))

# With a backup AI (Gemini's free tier, when GEMINI_API_KEY is set on Render): it answers
main.settings.GEMINI_API_KEY = "g"
gem = []
async def fake_gemini(model, system, question, images, kind, schema, max_tokens, t0):
    gem.append(model); return A
main._call_gemini = fake_gemini
main._claude_client = Client(); main._down.clear(); main._TALLY.set(None)
n0 = main.STATS["ai_no_credit"]
r = run(main._answer("How do I sell something on Facebook Marketplace?", "en", [], [], tester=True))
assert r["answer"] == "Open Facebook, tap Marketplace, then Sell." and gem, r
assert main.STATS["ai_no_credit"] == n0 + 1
# Every model of that account is left alone for a while (not asked, and failing, on every question)
assert main._down[("claude", main.STRONG_MODEL)] > main.time.time() + 500
assert main._down[("claude", main.settings.ANTHROPIC_MODEL)] > main.time.time() + 500
calls = len(main._claude_client.messages.calls)
r = run(main._answer("How do I post a photo on Facebook?", "en", [], [], tester=True))
assert r["answer"] and len(main._claude_client.messages.calls) == calls        # straight to the backup
# Without a backup: an honest failure (the phone says the helper is not available), as before
main.settings.GEMINI_API_KEY = None; main._down.clear()
try:
    run(main._answer("How do I sell something on Facebook Marketplace?", "en", [], [], tester=True)); raise SystemExit("should fail")
except main.HTTPException as e:
    assert e.status_code == 503, e.status_code
main._down.clear()

# The owner is told once a day, in a GitHub issue, in plain words, with nothing secret in it
i = main._credit_issue("claude", "2026-11-19")
assert i["title"] == "ScreenGuide's AI credit has run out"
assert "console.anthropic.com" in i["body"] and "Plans & Billing" in i["body"] and "Buy credits" in i["body"]
assert "Never paste the API key" in i["body"] and "<!-- no-credit: 2026-11-19 -->" in i["body"]
assert "ai-fix" not in json.dumps(i) and "@claude" not in i["body"]                # not work for the AI fixer
sent = []
async def fake_github(method, path, payload):
    sent.append((method, path, payload)); return [] if method == "GET" else {"number": 1}
main._github = fake_github; main.GITHUB_TOKEN = "t"; main._credit_said["day"] = ""
async def twice():
    main._credit_alert("claude"); main._credit_alert("claude")
    await asyncio.gather(*list(main._bg))
run(twice())
assert [m for m, _, _ in sent] == ["GET", "POST"], sent                           # one issue, not two
assert sent[1][2]["title"] == "ScreenGuide's AI credit has run out"
# GitHub is the memory: after a restart, the day's issue is not opened again
async def seen(method, path, payload):
    sent.append((method, path, payload)); return [{"body": "… <!-- no-credit: %s -->" % main._today()}] if method == "GET" else {}
main._github = seen; main._credit_said["day"] = ""; sent.clear()
async def once():
    main._credit_alert("claude"); await asyncio.gather(*list(main._bg))
run(once())
assert [m for m, _, _ in sent] == ["GET"], sent

# The button the words name first, the same on every server start ("Tap “Add Network”, or tap Navigate up")
W = ["Navigate up [tap]", "Wi-Fi [switch on]", "Add Network [tap]", "Phone [tap]", "Phone Master [tap]"]
assert main._label_from_say("Tap “Add Network”, or tap Navigate up.", W) == "Add Network"
assert main._label_from_say("Tap Navigate up, or tap “Add Network”.", W) == "Navigate up"
assert main._label_from_say("Tap Phone Master to clean the phone.", W) == "Phone Master"
assert main._label_from_say("Tap Phone to make a call.", W) == "Phone"
assert main._label_from_say("Look at the list.", W) is None
assert main.SERVER_VERSION >= "0.98"
print("no credit: the backup answers, the account rests, the owner is told once a day; the first named button")
