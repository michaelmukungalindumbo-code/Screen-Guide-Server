import os
os.environ.update(ADMIN_KEY="k")
import main

# The owner's phone (12 Nov, 0.118, "Which app is using up my data?"): the guide reached Phone Master's "App data usage
# ranking" (Block Blast! 219 MB, YouTube 63.75 MB, Chrome 41.81 MB…) and finished with "The app at the top, YouTube, uses
# the most data, with 219 MB": the first app's number with the second app's name. And on the way, "Tap "Settings" to go
# back": a row named Settings inside the app, not a way back.
S = main.NEXT_SYSTEM
assert "copy each name and number exactly as it is in <screen_words>, and keep each number with the name just before it" in S
assert "the first item of a list is the first one in <screen_words>" in S
assert "Never call a row or button “go back”" in S and "Navigate up" in S
assert main.PROMPT_VERSION >= "65" and main.SERVER_VERSION >= "0.94"
print("what is read out from a screen is copied from it, names with their own numbers; a row is never a way back")
