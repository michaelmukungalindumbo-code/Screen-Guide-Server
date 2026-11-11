import os, json
os.environ.update(ADMIN_KEY="k")
import main

# The owner's phone (11 Nov, 0.115): "How do I check my ECZ results online?" was answered "You can check your ECZ results
# on the Past Papers ZM app, which is already on your phone", with made-up steps ("Look for the Results option").
# Past Papers ZM is for past exam papers. The helper picked it from its name, because it is told to prefer an app
# already on the phone. "These mistakes are really demotivating."
S = main.SYSTEM
assert "Never choose an app because of its name" in S
assert "you are sure" in S and "does exactly this job" in S
# Something done "online", on a website, or with an organisation (results, applications, registration): the browser
assert "the phone's browser" in S and "Chrome" in S
assert "Never say an app can do something you are not sure it does" in S
assert "never make up the names of buttons or menus inside an app or a website you do not know" in S
assert int(main.PROMPT_VERSION) >= 62 and main.SERVER_VERSION >= "0.89"
# The real AI is asked this very question before any update reaches people
cases = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "real_ai_cases.json"), encoding="utf-8"))["cases"]
c = [x for x in cases if x["question"] == "How do I check my ECZ results online?"][0]
assert "Past Papers ZM" in c["apps"] and "Chrome" in c["apps"]
assert any(n in c["none"] for n in ("past papers zm app", "on the past papers")) and ["chrome", "browser", "website"] in c["all"]
print("an app is never chosen by its name; something done online is done in the browser; no made-up menus")
