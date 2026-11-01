import os, asyncio, json, time
os.environ.update(ADMIN_KEY="k", GITHUB_TOKEN="ghp_test", AI_WATCH_PER_DAY="2")
import main
run = asyncio.run
class Msgs:
    def __init__(self, out): self.out = list(out)
    async def create(self, **kw):
        class U: input_tokens = 900; output_tokens = 40
        class B: type = "text"; text = self.out.pop(0)
        class M: content = [B()]; usage = U(); stop_reason = "end_turn"
        return M()
class Client:
    def __init__(self, out): self.messages = Msgs(out)
issues, posts = [], []
async def fake_github(method, path, payload):
    if method == "GET":
        return list(reversed(issues))
    posts.append(path)
    if path.endswith("/issues"):
        n = 40 + len(issues); issues.append({"number": n, "title": payload["title"], "body": payload["body"],
                                             "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}); return {"number": n}
    return {}
main._github = fake_github

def step(phone, label, say, labels, note="", stuck=False, history=(), tester=True, goal="Turn on Wi-Fi for Mary"):
    main._claude_client = Client([json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})])
    async def go():
        r = await main.next_step(main.Next(goal=goal, labels=labels, note=note, stuck=stuck, history=list(history), device="TECNO phone, Android 13"),
                                 x_app_token="tok", x_install_id=phone, x_tester="1" if tester else "")
        await asyncio.sleep(0.05)
        return r
    return run(go())

def stop(phone):
    async def go():
        await main.event(main.Event(event="stop", guide="wifi"), x_app_token="tok", x_install_id=phone)
        await asyncio.sleep(0.05)
    run(go())

WIFI = ["Wi-Fi [tap]", "Bluetooth [switch]", "Mum [tap]", "0977123456 [text]", "Mobile data [tap]"]

# 1. Not a tester: nothing is watched, even when Help repeats itself
step("n1", "Wi-Fi", "Tap Wi-Fi.", WIFI, note="I don't understand", stuck=True, history=["Tap Wi-Fi."], tester=False)
assert issues == [] and main.STATS["watch:help_repeated"] == 0

# 2. A tester: Help answered with the sentence they had already heard -> an issue at once, cleaned
r = step("t1", "Wi-Fi", "Tap Wi-Fi.", WIFI, note="I don't understand", stuck=True, history=["Tap Wi-Fi."])
assert r["say"] == "Tap Wi-Fi.", r
assert len(issues) == 1 and posts[-1].endswith("/issues/40/labels"), posts
t, b = issues[0]["title"], issues[0]["body"]
assert t.startswith("Guide problem: Help repeated the same sentence"), t
assert "<!-- watch-id: " in b and "the same sentence they had already heard" in b and "I don't understand" in b
assert '"Wi-Fi [tap]"' in b and '"… [tap]"' in b and '"… [text]"' in b and "Bluetooth [switch]" in b
assert "Mum" not in b and "0977" not in b and "Mary" not in b and "t1" not in b, b      # nothing personal reaches GitHub
assert "TECNO phone" in b and "server/CLAUDE.md" in b

# 3. The same problem again (another phone, or after a restart): no second issue
step("t2", "Wi-Fi", "Tap Wi-Fi.", WIFI, note="I don't understand", stuck=True, history=["Tap Wi-Fi."])
main._fix_asked.clear(); main._store.kv.clear()
step("t3", "Wi-Fi", "Tap Wi-Fi.", WIFI, note="I don't understand", stuck=True, history=["Tap Wi-Fi."])
assert len(issues) == 1, [i["title"] for i in issues]

# 4. Still stuck: Help twice on the same screen. Once may be a hard moment; on a second phone it becomes an issue
SET = ["Settings [text]", "Search [tap]", "Network & internet [tap]", "Connected devices [tap]", "Apps [tap]"]
for ph in ("s1", "s2"):
    step(ph, None, "Look for Network & internet and tap it.", SET, note="I can't find it", stuck=True, history=["Tap Settings."], goal="Turn on mobile data")
    step(ph, "Network & internet", "Tap Network & internet.", SET, note="I can't find it", stuck=True, history=["Look for Network & internet and tap it."], goal="Turn on mobile data")
    if ph == "s1":
        assert len(issues) == 1
assert len(issues) == 2 and "still stuck after Help" in issues[1]["title"], issues[1]["title"]

# 5. Gave up after Help: also needs two phones, and the daily limit (2) is already reached, so no third issue today
for ph in ("g1", "g2"):
    step(ph, "Apps", "Tap Apps.", SET, note="It looks different", stuck=True, history=["Tap Settings."], goal="Uninstall an app")
    stop(ph)
assert main.STATS["watch:gave_up"] == 2 and main.STATS["watch_skipped"] >= 1
assert len(issues) == 2

# 6. Help that did not repeat, on a new screen, is not a problem
step("t9", "Search", "The Search box is the bar at the top with a magnifying glass. Tap it.", SET, note="I can't find it", stuck=True, history=["Tap Search."])
assert main.STATS["watch:help_repeated"] == 3 and len(issues) == 2

# Cleaning keeps app and button names, removes people
assert main._clean_text("Send a photo to Mary on WhatsApp") == "Send a photo to … on WhatsApp"
assert main._clean_text('Tap "Mum", then tap “Upload from gallery”.') == "Tap “…”, then tap “Upload from gallery”."
assert main._clean_label("0:09 [text]") == "0:09 [text]" and main._clean_label("Chisomo Phiri [tap]") == "… [tap]"
p = run(main.privacy()); assert "Testers only: guide problems" in str(getattr(p, "body", p))
assert main.SERVER_VERSION >= "0.51"
print("watcher ok")
