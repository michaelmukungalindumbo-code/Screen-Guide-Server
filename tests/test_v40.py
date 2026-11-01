import os, asyncio, json
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run
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
def step(label, say, labels, goal="Upload a file to Google Drive", lang="en", done=False):
    main._claude_client = Client([json.dumps({"label": label, "say": say, "done": done, "x": None, "y": None, "look_for": None})])
    return run(main.next_step(main.Next(goal=goal, labels=labels, lang=lang), x_app_token="tok", x_install_id="v40"))
# 1. Drive's + is "Create new": ring it, no picture needed
DRIVE = ["Search in Drive [tap]", "My Drive [selected]", "Computers [tap]", "Scan Document [tap]", "Create new [switch]", "Home [tap]",
         "Starred [tap]", "Shared [tap]", "Files [tap]"]
r = step(None, "Tap the + button at the bottom right to add a file.", DRIVE)
assert r["label"] == "Create new" and r["say"] == "Tap the + button to add a file." and not r["need_picture"], r
r = step(None, "Tap the + button.", ["Chats [selected]", "New chat [tap]", "Calls [tap]"], goal="Start a new chat on WhatsApp")
assert r["label"] == "New chat", r
r = step(None, "Tap the + button.", ["Chats [selected]", "Calls [tap]"], goal="Start a new chat on WhatsApp")
assert r["label"] is None and r["need_picture"] is True, "no named + on screen: a picture is still the way"
# 2. Android's file list: old steps are replaced by choosing the file
PICK = ["Recent [text]", "Images [tap]", "Audio [tap]", "Videos [tap]", "Documents [tap]", "Show roots [tap]", "Files in other apps [text]",
        "Gallery [tap]", "Photos [tap]"]
r = step(None, "Tap the + button at the bottom right, then tap Upload.", PICK)
assert r["label"] is None and r["say"] == "Tap the file you want to upload.", r
r = step("Documents", "Tap Documents to find your file.", PICK)
assert r["label"] == "Documents", r
r = step(None, "Tap the + button.", PICK, lang="bem")
assert r["say"] == "Kandeni pa fayilo mulefwaya.", r
# 3. "1 upload complete" on screen: done, whatever the AI planned next
r = step("Create new", "Tap Create new so you can upload a file.", DRIVE + ["1 upload complete [text]"])
assert r["done"] is True and r["label"] is None and r["say"].startswith("Done!"), r
r = step("Create new", "Tap Create new.", DRIVE + ["Recently uploaded [tap]"])
assert r["done"] is False and r["label"] == "Create new", "a list heading is not a finished upload"
r = step("Open", "Tap Open.", ["WhatsApp Messenger [text]", "Uninstall [tap]", "Open [tap]"], goal="Install WhatsApp from the Play Store")
assert r["done"] is True, r
r = step("Install", "Tap Install.", ["WhatsApp Messenger [text]", "Install [tap]"], goal="Install WhatsApp from the Play Store")
assert r["done"] is False and r["label"] == "Install", r
assert main.SERVER_VERSION >= "0.40"
print("plus names, file list and finished tasks ok")
