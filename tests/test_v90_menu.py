import os, json
os.environ.update(ADMIN_KEY="k")
import main

# The owner (12 Nov): "Where can I find teach a task recording in ScreenGuide" was answered "Tap the three dots, tap
# Teach a task": that starts a new recording. App 0.116 keeps them in the menu under "Your taught tasks" (start, share,
# delete), and the helper is told so. Its menu list is also brought up to date with this week's app.
S = main.SYSTEM
assert "Your taught tasks" in S and "start, share or delete" in S
assert "a recording not yet saved" in S
assert "Get help from someone" in S and "Open a shared guide" in S                      # in the app's menu, missing from the list
assert "Voice" in S and "Read button in the pull-down panel" in S and "Check for updates" in S
assert main.PROMPT_VERSION >= "63" and main.SERVER_VERSION >= "0.90"
cases = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "real_ai_cases.json"), encoding="utf-8"))["cases"]
c = [x for x in cases if "teach a task" in x["question"].lower()][0]
assert ["your taught tasks"] in c["all"]
print("where taught tasks are: Your taught tasks in the menu; the menu list is this week's")
