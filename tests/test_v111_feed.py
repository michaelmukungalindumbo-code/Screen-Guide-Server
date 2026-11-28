import os, asyncio, json, time
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run

# #115, #117 (the owner's Infinix phone, 28 Nov, "How do I upload content on YouTube?"). YouTube opened on a video that was
# playing. Its page shows other people's videos with their lengths ("44:49", "6:37"), so the rule for a picker of the
# person's own videos took it for one: "Tap the video you want." three times. He tapped one, opened someone else's video,
# and needed 4 steps to get out of it. A screen with Share, More actions, Subscribe or Comments is a feed, not a picker.
# Staged: feed_not_gallery.
# #116: after "Upload Short", YouTube's own page said "Uploading" / "Processing will begin shortly", but the guide went on
# ("Tap You to check"). The upload goes on by itself: done. Staged: upload_started.


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


GOAL = "How do I upload content on YouTube"
# The report's step 2 screen (YouTube's page of a playing video; "…" are words the report leaves out)
WATCH = ["… [text]", "… [tap]", "… [switch off]", "More options [tap]", "… [tap]", "… [switch off]"] + ["… [tap]"] * 12 + \
        ["18:45 [tap]", "… [tap]", "… [switch off]", "44:49 [tap]", "… [tap]", "… [tap]", "… [switch off]", "… [switch off]",
         "… [switch off]", "Share [tap]", "… [tap]", "More actions [tap]", "… [switch off]", "… [text]", "6:37 [tap]"]
# YouTube's own picker after Create (the report's step 10): still a picker
PICKER = ["Video [selected]", "Short [tap]", "Live [tap]", "Close [tap]", "Settings [tap]", "Select more media [tap]",
          "0:04 [tap]", "0:06 [tap]", "0:13 [tap]", "0:21 [tap]", "0:09 [tap]", "0:14 [tap]"]
# The report's step 20 screen, the channel's Shorts after "Upload Short"
CHANNEL = ["Home [selected]", "Shorts [tap]", "Create [tap]", "You [tap]", "Navigate up [tap]", "Shorts [selected]", "Drafts [text]",
           "Uploading [text]", "Processing will begin shortly [text]", "Private [tap]", "Unlisted [tap]", "More actions [tap]"]


def step(outs, labels, goal=GOAL, tester="1", install="v111", told=("Tap “YouTube”.",)):
    main._claude_client = Client(outs)
    b = main.Next(goal=goal, labels=list(labels), lang="en", history=list(told))
    return run(main.next_step(b, x_app_token="tok", x_install_id=install, x_tester=tester))


# 1. The replay: the AI's own step on a playing video's page stands (never "Tap the video you want.")
SAY = "Tap the down arrow at the top left to make the video small, then tap Create."
r = step([ans(SAY)], WATCH)
assert r["say"] != "Tap the video you want." and "down arrow" in r["say"], r
# 2. YouTube's own picker is still a picker
r = step([ans("Tap a video to upload it.")], PICKER, install="v111b", told=("Tap “Create”.",))
assert r["say"] == "Tap the video you want, or tap + if it is not here.", r
# 3. After "Upload Short": "Uploading", "Processing will begin shortly": done
r = step([ans("Tap “You” to check, or tell me if you still see an upload page.", label="You")], CHANNEL, install="v111c",
         told=("Tap the big white button with the words “Upload Short”. Almost done!",))
assert r["done"] is True and r["label"] is None, r
# ...not while an upload is paused or failed, and not for another goal
for w in ("Uploading paused [text]", "Upload failed [text]"):
    r = step([ans("Tap “You”.", label="You")], [l for l in CHANNEL if not l.startswith(("Uploading", "Processing"))] + [w],
             install="v111d" + w[:8])
    assert r["done"] is False, (w, r)
r = step([ans("Tap “You”.", label="You")], CHANNEL, goal="Watch my Shorts", install="v111e")
assert r["done"] is False, r

# 4. Staged: before 24 quiet hours, other phones get the answer as it was
for rule in ("feed_not_gallery", "upload_started"):
    main._launch["live"][main.STAGED[rule]] = time.time()
r = step([ans(SAY)], WATCH, tester="", install="v111f")
assert r["say"] == "Tap the video you want.", r
r = step([ans("Tap “You”.", label="You")], CHANNEL, tester="", install="v111g")
assert r["done"] is False, r
assert main.STAGED["feed_not_gallery"] == "1.11" and main.STAGED["upload_started"] == "1.11" and main.SERVER_VERSION >= "1.11"
print("a feed of other people's videos is not a picker; Uploading / Processing will begin shortly ends an upload ok")
