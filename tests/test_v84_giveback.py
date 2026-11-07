import os, asyncio
os.environ.update(ADMIN_KEY="k")
import main
from fastapi import HTTPException
run = asyncio.run

# v0.84, the owner's test (7 Nov, no AI credit): "How do I use safe folder" got "Sorry, the helper is busy" every time,
# and each failed try still used one of the day's free questions. During an outage, "Try again" used up the person's day
# (and then offered an ad). A question or step the helper could not answer is not counted.
class Down:
    class messages:
        @staticmethod
        async def create(**kw):
            raise RuntimeError("Your credit balance is too low to access the Anthropic API.")
main.settings.ANTHROPIC_API_KEY = main.settings.ANTHROPIC_API_KEY or "test"
main.settings.GEMINI_API_KEY = ""
main._claude_client = Down()
H = dict(x_app_token="tok", x_install_id="devDown", x_pass="")

def fails(f):
    try:
        run(f); raise SystemExit("the helper is down: it must fail")
    except HTTPException as e:
        assert e.status_code >= 500, e.status_code
        return e

left = main._left("devDown", "free")
for i in range(3):   # "Try again", three times
    fails(main.ask(main.Ask(question="How do I use safe folder", lang="en"), **H))
assert main._left("devDown", "free") == left, (main._left("devDown", "free"), left)

steps = len(main._s_day["devDown"])
for i in range(3):
    fails(main.next_step(main.Next(goal="Open Safe folder in Files", labels=["Safe folder [tap]", "Starred [tap]", "Downloads [tap]"]),
                         x_app_token="tok", x_install_id="devDown", x_tester=""))
assert len(main._s_day["devDown"]) == steps, (len(main._s_day["devDown"]), steps)

fails(main.read_screen(main.ReadIn(words=["Safe folder", "Starred"], lang="en"), **H))
assert main._left("devDown", "free") == left
assert main.STATS["given_back"] >= 7
print("a question or step the helper could not answer is not counted against the day")
