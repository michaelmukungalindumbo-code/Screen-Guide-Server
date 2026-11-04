import os, asyncio, json
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run
class Msgs:
    def __init__(self, out): self.out = list(out); self.calls = []
    async def create(self, **kw):
        self.calls.append(kw)
        class U: input_tokens = 2000; output_tokens = 100
        class B: type = "text"; text = self.out.pop(0)
        class M: content = [B()]; usage = U(); stop_reason = "end_turn"
        return M()
class Client:
    def __init__(self, out): self.messages = Msgs(out)
def J(label, say): return json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})
SET = ["Settings [text]", "Search [tap]", "Network & internet [tap]", "Apps [tap]"]
def step(i, stuck=False, tester=True, note=""):
    main._claude_client = Client([J("Apps", "Tap “Apps”.")])
    r = run(main.next_step(main.Next(goal="Uninstall an app", labels=SET, stuck=stuck, note=note),
                           x_app_token="tok", x_install_id=i, x_tester="1" if tester else ""))
    return r, [c["model"] for c in main._claude_client.messages.calls]

# 4 Nov, the owner chose: hard moments in a guide get a stronger AI. A hard moment is a Help press.
assert main.STAGED["strong_on_help"] == "0.75" and main.STRONG_MODEL == "claude-sonnet-5-5"
r, models = step("t1")
assert models == ["claude-haiku-5-5"], models                         # a normal step: the usual fast AI
r, models = step("t1", stuck=True, note="I can't find it")
assert models == ["claude-sonnet-5-5"] and r["label"] == "Apps", (models, r)
# Its cost is counted at its own price (US$2 / US$10 per million tokens): 2000 in + 100 out = US$0.005
assert abs(main.USAGE["step+strong"]["cost"] - 0.005) < 1e-9, main.USAGE["step+strong"]
assert abs(main.USAGE["step"]["cost"] - (2000 * 0.10 + 100 * 0.50) / 1e6) < 1e-12, main.USAGE["step"]
st = main._sessions["t1"]["steps"][-1]
assert st["strong"] is True and "the stronger AI" in main._step_time(st)

# Staged: users' phones get it once 0.75 has been live 24 hours
main._launch["live"]["0.75"] = main.time.time()
r, models = step("u1", stuck=True, tester=False); assert models == ["claude-haiku-5-5"], models
main._launch["live"]["0.75"] -= 25 * 3600
r, models = step("u1", stuck=True, tester=False); assert models == ["claude-sonnet-5-5"], models

# At most STRONG_PER_DAY a day; then the usual AI again
main._strong_day[main._today()] = main.STRONG_PER_DAY
r, models = step("t1", stuck=True); assert models == ["claude-haiku-5-5"], models
main._strong_day.clear()

# If the stronger AI fails, the usual one answers: the step never fails because of it
class Down(Msgs):
    async def create(self, **kw):
        if kw["model"] == "claude-sonnet-5-5":
            self.calls.append(kw); raise RuntimeError("overloaded")
        return await super().create(**kw)
main._claude_client = Client([]); main._claude_client.messages = Down([J("Apps", "Tap “Apps”.")])
r = run(main.next_step(main.Next(goal="Uninstall an app", labels=SET, stuck=True), x_app_token="tok", x_install_id="t2", x_tester="1"))
assert r["label"] == "Apps" and [c["model"] for c in main._claude_client.messages.calls] == ["claude-sonnet-5-5", "claude-haiku-5-5"]
assert main.SERVER_VERSION >= "0.75"
print("stronger AI on Help")
