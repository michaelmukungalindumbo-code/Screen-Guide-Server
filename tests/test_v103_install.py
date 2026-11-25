import os
os.environ.update(ADMIN_KEY="k")
import main

# The owner's phone, 25 Nov: "How do I sell something on Facebook Marketplace?" with no Facebook on the phone. The answer
# offered Chrome or installing Facebook, then six steps in one paragraph, and no Show me: nothing to tap for a first-time
# user. The chat is told to make it a guide that installs the app, and only that. How the real AI answers is checked by
# tests/real_ai_cases.json ("25 Nov: selling on Facebook Marketplace ..."), before every update.
assert 'A task done in a named app that is not in <installed_apps>' in main.SYSTEM
assert 'The goal is "Install <name> from the Play Store"' in main.SYSTEM
assert "Offer only that one way" in main.SYSTEM
assert main.PROMPT_VERSION >= "69" and main.SERVER_VERSION >= "1.03"
print("a task in an app that is not on the phone: a guide that installs it ok")
