import os
os.environ.update(ADMIN_KEY="k")
import main

# 6 Nov: "change my ScreenGuide chat background" went home, rang ScreenGuide's icon and round again. The owner chose:
# Show me works inside ScreenGuide too (app 0.79 guides its own menus itself, with no AI). So the chat offers Show me
# for ScreenGuide's own settings, with a goal that names ScreenGuide, which is how the phone knows.
assert 'use kind "guide": Show me points at each step inside ScreenGuide' in main.SYSTEM, "the chat must offer Show me"
assert 'goal "Change the chat background in ScreenGuide"' in main.SYSTEM
assert "Show me cannot point inside ScreenGuide" not in main.SYSTEM

# The watcher's report showed "…" for ScreenGuide's own name and for "Business" in WhatsApp Business. Those are not
# anyone's personal words; names of people still are hidden.
assert main._clean_text("Tap ScreenGuide to open the app.", ours=True) == "Tap ScreenGuide to open the app."
assert main._clean_text("Open the WhatsApp Business app", ours=True) == "Open the WhatsApp Business app"
assert main._clean_text("Change the chat background in ScreenGuide", ours=True) == "Change the chat background in ScreenGuide"
assert main._clean_word("Customize ScreenGuide") == "Customize ScreenGuide" and main._clean_word("Green") == "Green"
assert main._clean_text("Send a photo to Mary", ours=True) == "Send a photo to …"
assert main._clean_word("Mary") == "…"
assert main.SERVER_VERSION >= "0.80" and main.PROMPT_VERSION >= "57"   # 58 since 0.81
print("Show me for ScreenGuide's own settings; its name is not hidden")
