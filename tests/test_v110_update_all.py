import os, asyncio, json, time
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run

# The owner's Infinix phone, 27 Nov: an app said "update required"; ScreenGuide's card offered "Show me how" with the goal
# "Update this app in the Play Store". The guide went to Manage apps & device and rang "Update all": 27 apps, a lot of data
# (people here pay for bundles). "Update all" is rung only when the goal asks for every app. Staged: update_all_asked.


class Msgs:
    def __init__(self, out): self.out = list(out); self.calls = []
    async def create(self, **kw):
        self.calls.append(kw)
        class U: input_tokens = 900; output_tokens = 40
        class B: type = "text"; text = self.out.pop(0)
        class M: content = [B()]; usage = U(); stop_reason = "end_turn"
        return M()
class Client:
    def __init__(self, out): self.messages = Msgs(out)


def ans(say, label=None, done=False):
    return json.dumps({"label": label, "say": say, "done": done, "x": None, "y": None, "look_for": None})


# Play Store's list of updates (the report's step 8)
UPDATES = ["Navigate up [tap]", "Available updates [text]", "Update all [tap]", "Android Auto [text]", "Update [tap]",
           "WhatsApp Messenger [text]", "Update [tap]", "Gmail [text]", "Update [tap]"]


def step(outs, goal, labels=UPDATES, tester="1", install="v110"):
    main._claude_client = Client(outs)
    b = main.Next(goal=goal, labels=list(labels), lang="en", history=["Tap “Manage apps & device”."])
    return run(main.next_step(b, x_app_token="tok", x_install_id=install, x_tester=tester))


# 1. The replay (with no app named): never "Update all"
r = step([ans("Tap “Update all” to update every app.", label="Update all")], "Update this app in the Play Store")
assert r["label"] is None and "update all" not in r["say"].lower().replace("do not tap “update all”", ""), r
assert r["say"] == main._ONE_UPDATE_SAY % "the app", r
# 2. An app named in the goal: its name, never "Update all"
r = step([ans("Tap “Update all”.", label="Update all")], "Update WhatsApp in the Play Store", install="v110b")
assert r["label"] is None and r["say"] == main._ONE_UPDATE_SAY % "“WhatsApp”", r
# 3. Asked for every app: "Update all" stays
for g in ("Update all my apps", "Update every app on my phone", "How do I update all apps?"):
    r = step([ans("Tap “Update all”.", label="Update all")], g, install="v110c" + g[:5])
    assert r["label"] == "Update all", (g, r)
# 4. Staged: before 24 quiet hours, other phones as before
main._launch["live"][main.STAGED["update_all_asked"]] = time.time()
r = step([ans("Tap “Update all”.", label="Update all")], "Update WhatsApp in the Play Store", tester="", install="v110d")
assert r["label"] == "Update all", r
assert main.STAGED["update_all_asked"] == "1.10" and main.SERVER_VERSION >= "1.10"
print("Update all: only when every app was asked for; one app is found in the list ok")
