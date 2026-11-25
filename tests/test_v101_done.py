import os, asyncio, json, time
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run

# The owner (25 Nov, "Scan a document with Drive", the guide of issues #89 and #90): "The guide ended before I uploaded
# the scanned documents." Step 4 was a screen that shares no words (Google's scanner); the AI looked at the picture and
# said "Your scan is saved. You can see the new PDF file in your list. Well done!" with done true. Drive then showed its
# "Upload to Drive" page with Upload still to tap, but the guide had already ended. Where nothing on the screen can be
# read, nothing can confirm the goal is finished: the AI is asked again, and the guide only goes on (never ends) there.


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


def ans(say, done=False, x=None, y=None, label=None):
    return json.dumps({"label": label, "say": say, "done": done, "x": x, "y": y, "look_for": None})


def text_of(call):
    c = call["messages"][0]["content"]
    return c if isinstance(c, str) else " ".join(p.get("text", "") for p in c if isinstance(p, dict))


IMG = "A" * 2000
GOAL = "Scan a document with Drive"
TOLD = ["Tap “Scan Document”.", "Tap the big round button in the middle at the bottom to take the picture.",
        "Good, your picture is taken. Tap the blue round button at the bottom right."]
SAVED = "Your scan is saved. You can see the new PDF file in your list. Well done!"


def step(outs, labels=(), tester="1", install="v101", image=IMG, lang="en"):
    main._claude_client = Client(outs)
    b = main.Next(goal=GOAL, labels=list(labels), lang=lang, history=list(TOLD), image=image)
    r = run(main.next_step(b, x_app_token="tok", x_install_id=install, x_tester=tester))
    return r, main._claude_client.messages.calls


# 1. The replay: "saved, well done" on a screen with no words. Asked again, the AI gives the step it can see; not done.
r, calls = step([ans(SAVED, done=True), ans("Wait a moment. When you see Upload at the top right, tap it.")])
assert len(calls) == 2, len(calls)
assert "cannot see that the task is finished" in text_of(calls[1]) and "done must be false" in text_of(calls[1])
assert r["done"] is False and r["say"] == "Wait a moment. When you see Upload at the top right, tap it.", r

# 2. It says done again: the guide still goes on, with a plain sentence (never "saved, well done").
r, calls = step([ans(SAVED, done=True), ans(SAVED, done=True)], install="v101b")
assert len(calls) == 2 and r["done"] is False, r
assert r["say"] == main._UNSEEN_DONE_SAY, r
assert "Upload" in main._UNSEEN_DONE_SAY and "carry on when the screen changes" in main._UNSEEN_DONE_SAY

# 3. Nyanja: no new Nyanja wording is made up. The guide goes on (done false) with the AI's own Nyanja words.
r, calls = step([ans("Zatheka!", done=True), ans("Zatheka!", done=True)], install="v101c", lang="ny")
assert r["done"] is False and r["say"] == "Zatheka!", r

# 4. A screen whose words can be read (Drive's list with the new PDF): done is taken as it is, nothing asked again.
r, calls = step([ans("Your scan is in Drive. Well done!", done=True)],
                labels=["My Drive [text]", "Scan 25 Nov 2026 [tap]", "Home [tap]", "Files [text]"], install="v101d")
assert len(calls) == 1 and r["done"] is True, (len(calls), r)

# 5. Not done on a screen with no words: nothing changes, one answer.
r, calls = step([ans("Tap the big round button in the middle at the bottom.", x=0.5, y=0.88)], install="v101e")
assert len(calls) == 1 and r["done"] is False and r["x"] == 0.5, (len(calls), r)

# 6. Staged: before 24 quiet hours, other phones get the answer as it was.
main._launch["live"][main.STAGED["unseen_done"]] = time.time()
r, calls = step([ans(SAVED, done=True)], tester="", install="v101f")
assert len(calls) == 1 and r["done"] is True, (len(calls), r)
assert main.STAGED["unseen_done"] == "1.01" and main.SERVER_VERSION >= "1.01"

# 7. The AI knows Drive's scan is saved only after Upload on its "Upload to Drive" page.
assert "Upload to Drive" in main.NEXT_SYSTEM and main.PROMPT_VERSION >= "68"
print("a screen with no words never ends a guide: asked again, and the guide goes on until Upload ok")
