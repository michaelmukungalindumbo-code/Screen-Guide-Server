import os, asyncio, json, time
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run
class Msgs:
    def __init__(self, out, cached=0): self.out = list(out); self.calls = []; self.cached = cached
    async def create(self, **kw):
        self.calls.append(kw)
        c = self.cached
        class U: input_tokens = 900; output_tokens = 300; cache_creation_input_tokens = 0; cache_read_input_tokens = c
        class T: type = "thinking"; thinking = "Wi-Fi is on, so the next step is to go back."
        class B: type = "text"; text = self.out.pop(0)
        class M: content = [T(), B()]; usage = U(); stop_reason = "end_turn"
        return M()
class Client:
    def __init__(self, out, cached=0): self.messages = Msgs(out, cached)
def J(label, say, done=False): return json.dumps({"label": label, "say": say, "done": done, "x": None, "y": None, "look_for": None})
def A(text, kind="answer"): return json.dumps({"kind": kind, "text": text, "goal": "", "plan": [], "needs_apps": False})
main.settings.ANTHROPIC_API_KEY = main.settings.ANTHROPIC_API_KEY or "test"

# The owner (13 Nov, after a guide that kept saying "turn Wi-Fi on"): "it doesn't make any sense if ScreenGuide will keep
# giving me wrong instructions even if its feedback is instant. Users are willing to wait for a few seconds for a valid,
# effective and accurate answer." He chose "careful where it matters": the stronger AI, thinking first, for every chat
# answer, a guide's first step, each new app, and anything that goes wrong; routine taps stay with the fast AI.
APPS = ["Chrome", "Drive", "Settings", "WhatsApp", "AI Studio"]
DRIVE = ["Navigate up [tap]", "Create new [tap]", "My Drive [tap]", "Files [tap]", "Scan document [tap]"]
def step(hist, path, out, i="dev96", tester=True, stuck=False, note="", labels=DRIVE, cached=0):
    main._claude_client = Client(out, cached)
    r = run(main.next_step(main.Next(goal="Scan a document with Drive", labels=labels, history=hist, path=path, apps=APPS,
                                     stuck=stuck, note=note), x_app_token="tok", x_install_id=i, x_tester="1" if tester else ""))
    return r, main._claude_client.messages.calls
def careful(call): return call["model"] == main.STRONG_MODEL and "thinking" not in call["extra_body"] \
    and call["extra_body"]["output_config"]["effort"] == main.CAREFUL_EFFORT and call["max_tokens"] >= main.CAREFUL_MAX_TOKENS
def fast(call): return call["model"] == "claude-haiku-5-5" and call["extra_body"]["thinking"] == {"type": "disabled"} \
    and call["extra_body"]["output_config"]["effort"] == "low"

# Why a step matters
L = {"last": [{"label": 0, "say": 1}]}; P = {"last": [{"label": 5, "say": 1}]}
assert main._careful_why([], [], APPS, P, False, False) == "first step"
assert main._careful_why(["User said: hi"], [], APPS, P, False, False) == "first step"
assert main._careful_why(["Tap “Drive”."], ["Home screen", "Drive"], APPS, P, False, False) == "new app"
assert main._careful_why(["Tap “Drive”.", "Tap “Create new”."], ["Drive", "Create new"], APPS, P, False, False) == ""   # a routine tap
assert main._careful_why(["Tap “Drive”.", "Swipe up."], ["Drive", "Create new"], APPS, L, False, False) == "after no ring"
assert main._careful_why(["Tap “Drive”."], ["Drive", "Create new"], APPS, P, True, False) == "help"
assert main._careful_why(["Tap “Drive”."], ["Drive", "Create new"], APPS, P, False, True) == "going round"
assert main.CAREFUL_EFFORT == "medium" and main.CAREFUL_MAX_TOKENS >= 4000 and main.CAREFUL_PER_DAY >= 100

# A guide's first step: the stronger AI, thinking first, with more time; its thinking is never shown, only its answer
r, calls = step([], ["Home screen"], [J("Create new", "Tap “Create new”.")])
assert len(calls) == 1 and careful(calls[0]) and r["label"] == "Create new" and r["say"] == "Tap “Create new”." and r["strong"] is True, (r, calls[0]["model"])
# The first step inside a new app: careful too
r, calls = step(["Tap “Drive”."], ["Home screen", "Drive"], [J("Create new", "Tap “Create new”.")], i="dev96b")
assert careful(calls[0]), calls[0]["model"]
# A routine tap inside the app: the fast AI, no thinking, as before
r, calls = step(["Tap “Drive”.", "Tap “Create new”."], ["Drive", "Create new"], [J("Scan document", "Tap “Scan document”.")], i="dev96b")
assert fast(calls[0]) and r["label"] == "Scan document" and r["strong"] is False, calls[0]["model"]
# After a step that pointed at nothing: careful
step(["Tap “Drive”.", "Tap “Create new”."], ["Drive", "Create new"], [J(None, "Hold the camera still over the paper.")], i="dev96c")
r, calls = step(["Tap “Drive”.", "Tap “Create new”.", "Hold the camera still over the paper."], ["Drive", "Create new"], [J("Scan document", "Tap “Scan document”.")], i="dev96c")
assert careful(calls[0]), calls[0]["model"]
# Help: careful
r, calls = step(["Tap “Drive”.", "Tap “Create new”."], ["Drive", "Create new"], [J("Scan document", "Tap “Scan document”.")], i="dev96d", stuck=True, note="I can't find it")
assert careful(calls[0]), calls[0]["model"]
# Counted
assert main.STATS["careful_steps"] >= 4 and main.STATS["careful_first_step"] >= 1 and main.STATS["careful_new_app"] >= 1
assert main.USAGE["step+strong+careful"]["calls"] >= 4

# Every chat answer: careful, even an easy first question (it used to go to the fast AI)
main._claude_client = Client([A("Open Settings, then tap Wi-Fi.")]); main._TALLY.set(None)
r = run(main._answer("How do I turn on Wi-Fi?", "en", [], [], tester=True))
assert careful(main._claude_client.messages.calls[0]) and r["answer"] == "Open Settings, then tap Wi-Fi.", r
assert main.STATS["chat_careful"] >= 1

# The long instructions go as one block kept in the AI service's cache, the same words as "system"
c = main._claude_client.messages.calls[0]
assert c["extra_body"]["system"] == [{"type": "text", "text": c["system"], "cache_control": {"type": "ephemeral"}}]
assert all(k["extra_body"]["system"][0]["cache_control"] == {"type": "ephemeral"} for k in calls)
# Their cost: a cached part costs a twentieth on the stronger AI (a tenth on the fast one), and writing it a quarter more
main.USAGE.clear()
main._count("x", 1000, 100, "claude", "claude-sonnet-5-5", cw=0, cr=2600)
assert abs(main.USAGE["x"]["cost"] - (1000 * 2.0 + 2600 * 2.0 * 0.05 + 100 * 10.0) / 1e6) < 1e-12, main.USAGE["x"]
main._count("y", 1000, 100, "claude", "claude-haiku-5-5", cw=2600, cr=0)
assert abs(main.USAGE["y"]["cost"] - (1000 * 0.10 + 2600 * 0.10 * 1.25 + 100 * 0.50) / 1e6) < 1e-12, main.USAGE["y"]
main._count("z", 1000, 100, "claude", "claude-haiku-5-5", cw=0, cr=2600)
assert abs(main.USAGE["z"]["cost"] - (1000 * 0.10 + 2600 * 0.10 * 0.1 + 100 * 0.50) / 1e6) < 1e-12, main.USAGE["z"]
assert main.USAGE["z"]["in"] == 3600

# The day's limit: then the fast AI, as before
main._careful_day[main._today()] = main.CAREFUL_PER_DAY
r, calls = step([], ["Home screen"], [J("Create new", "Tap “Create new”.")], i="dev96e")
assert fast(calls[0]), calls[0]["model"]
main._careful_day.clear()
# If the stronger AI fails, the fast one answers: the step never fails because of it
class Down(Msgs):
    async def create(self, **kw):
        if kw["model"] == main.STRONG_MODEL:
            self.calls.append(kw); raise RuntimeError("overloaded")
        return await super().create(**kw)
main._claude_client = Client([]); main._claude_client.messages = Down([J("Create new", "Tap “Create new”.")])
r = run(main.next_step(main.Next(goal="Scan a document with Drive", labels=DRIVE, history=[], path=["Home screen"], apps=APPS),
                       x_app_token="tok", x_install_id="dev96f", x_tester="1"))
assert r["label"] == "Create new" and [k["model"] for k in main._claude_client.messages.calls] == [main.STRONG_MODEL, "claude-haiku-5-5"]
assert fast(main._claude_client.messages.calls[1])                      # the backup does not think first
main._down.clear()                                                       # (the failed AI is skipped for 30 seconds)
# Users' phones: staged
main._launch["live"][main.STAGED["careful"]] = time.time()
r, calls = step([], ["Home screen"], [J("Create new", "Tap “Create new”.")], i="user96", tester=False)
assert fast(calls[0]), calls[0]["model"]                                 # not yet
main._launch["live"][main.STAGED["careful"]] = time.time() - 25 * 3600
r, calls = step([], ["Home screen"], [J("Create new", "Tap “Create new”.")], i="user96b", tester=False)
assert careful(calls[0]), calls[0]["model"]
assert main.STAGED["careful"] == "0.96" and main.SERVER_VERSION >= "0.96"
print("careful where it matters: chat answers, first steps, new apps and hard moments think first; routine taps stay fast")
# If the AI service ever refuses the cache, the answer comes without it, as before (never a step lost to it)
class NoCache(Msgs):
    async def create(self, **kw):
        if "system" in kw.get("extra_body", {}):
            self.calls.append(kw)
            class E(Exception): status_code = 400
            raise E("system.0.cache_control: Extra inputs are not permitted")
        return await super().create(**kw)
main._claude_client = Client([]); main._claude_client.messages = NoCache([J("Create new", "Tap “Create new”.")])
r = run(main.next_step(main.Next(goal="Scan a document with Drive", labels=DRIVE, history=["Tap “Drive”.", "Tap “Create new”."],
                                 path=["Drive", "Create new"], apps=APPS), x_app_token="tok", x_install_id="dev96g", x_tester="1"))
assert r["label"] == "Create new" and main._feats("claude-haiku-5-5")["cache"] is False, r
main._feat.clear()
print("and without the cache if the AI service refuses it")
