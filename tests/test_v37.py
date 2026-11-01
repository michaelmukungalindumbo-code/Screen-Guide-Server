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
def step(label, say, labels, goal, lang="en", note="", look=None):
    main._claude_client = Client([json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": look})])
    return run(main.next_step(main.Next(goal=goal, labels=labels, lang=lang, note=note), x_app_token="tok", x_install_id="v37"))

# WhatsApp attach menu: "Gallery" and "Camera" are the right taps, not album menus
ATTACH = ["Document [tap]", "Camera [tap]", "Gallery [tap]", "Audio [tap]", "Location [tap]", "Contact [tap]"]
r = step("Gallery", "Tap Gallery.", ATTACH, "Send a photo to Mum on WhatsApp")
assert r["label"] == "Gallery" and r["say"] == "Tap Gallery." and not r["need_picture"], r
r = step("Camera", "Tap Camera.", ATTACH, "Take a photo and send it on WhatsApp")
assert r["label"] == "Camera", r
# WhatsApp picker with only some photos allowed ("Manage")
WA = ["Recents [tap]", "Manage [tap]", "Photo taken on 30 Oct 2026 [tap]", "Photo taken on 29 Oct 2026 [tap]"]
r = step("Recents", "Tap Recents to choose a photo.", WA, "Send a photo to Mum on WhatsApp")
assert r["label"] is None and r["say"] == "Tap the photo you want, or tap “Manage” if it is not here.", r
r = step("Photo taken on 29 Oct 2026", "Tap the photo taken on 29 Oct.", WA, "Send a photo on WhatsApp")
assert r["label"] is None, "never choose one of several personal photos for them"
# Android's own photo picker
PICK = ["Photos [selected]", "Albums [tap]", "Video, 0:14, taken on 31 Oct [tap]", "Photo taken on 30 Oct [tap]", "Add [tap]"]
r = step("Photo taken on 30 Oct", "Tap the photo.", PICK, "Upload a video to YouTube")
assert r["label"] == "Video, 0:14, taken on 31 Oct" and r["say"] == "Tap your video.", r
r = step("Add", "Tap Add.", PICK, "Upload a video to YouTube")
assert r["label"] == "Add" and r["say"] == "Tap Add.", "past choosing: left alone"
# TikTok: All | Videos | Photos tabs
TT = ["All [selected]", "Videos [tap]", "Photos [tap]", "0:21 [text]", "0:09 [text]", "Next [tap]"]
r = step("Videos", "Tap Videos.", TT, "Post a video on TikTok", lang="bem")
assert r["label"] is None and r["say"] == "Kandeni pa vidiyo mulefwaya.", r
print("pickers ok")

# icons with no name: the phone is asked for a picture; never on a picker, never with a ring or a look_for
WAHOME = ["Chats [selected]", "Updates [tap]", "Communities [tap]", "Calls [tap]", "Mum [tap]"]
r = step(None, "Tap the + button.", WAHOME, "Start a new chat on WhatsApp")
assert r["need_picture"] is True, r
r = step(None, "Tap the three dots.", WAHOME, "Open WhatsApp settings")
assert r["need_picture"] is True
r = step("Mum", "Tap Mum.", WAHOME, "Send a message to Mum")
assert r["need_picture"] is False
r = step(None, "Tap your video, or tap + if it is not here.", ["Videos [tap]", "Select more media [tap]", "0:14 [text]", "1:02 [text]"], "Upload a video")
assert r["need_picture"] is False, "a picker is not an icon hunt"
r = step(None, "Scroll down to find Storage.", ["Wi-Fi [tap]", "Bluetooth [tap]"], "Check storage", look="Storage")
assert r["look_for"] == "Storage" and r["need_picture"] is False
assert main.STATS["picture_wanted"] == 2
print("icons ok")

# Samsung: Storage is not in the list; once the phone says so, the AI may not send them scrolling for it again
r = step(None, "Scroll down to find Storage.", ["Wi-Fi [tap]", "Battery and device care [tap]", "Apps [tap]"], "Check storage",
         note="They scrolled the list twice but “Storage” is not in it.", look="Storage")
assert r["look_for"] is None, r
print("look_for limit ok")

sysp = main.NEXT_SYSTEM
for want in ("Press and hold", "Allow all", "Sponsored", "Not now", "Tap the + button", "Battery and device care"):
    assert want in sysp, want
assert "buttons without words" in run(main.privacy()).body
print("prompt and privacy ok")
