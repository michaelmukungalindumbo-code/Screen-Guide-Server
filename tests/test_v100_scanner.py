import os, asyncio, json
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run

# Issues #89 and #90 (25 Nov, the owner's Infinix phone): "Scan a document with Drive". Google's scanner shares no words
# at all, so every step there is answered from a screen picture.
#  - On the camera screen the guide said "Tap the white round button at the bottom"; the person pressed Help.
#  - On the page to check the picture it said "Tap the round “Next” button", but the picture showed a blue round button
#    with a + on it and no word "Next". The server's own picture note told the AI that scanners hide a "Next" word.
#  - Both reports said "pointed at: nothing", yet no "no_point" problem was found: the ring was placed on a spot in the
#    picture, and the report never said so.


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


def ans(say, x=None, y=None, label=None):
    return json.dumps({"label": label, "say": say, "done": False, "x": x, "y": y, "look_for": None})


IMG = "A" * 2000   # a screen picture (its content does not matter to the pretend AI)
GOAL = "Scan a document with Drive"
TOLD = ["Tap “Scan Document”.", "Tap the big round button in the middle at the bottom to take the picture."]


def step(outs, labels=(), tester="1", install="v100", image=IMG, history=TOLD):
    main._claude_client = Client(outs)
    b = main.Next(goal=GOAL, labels=list(labels), lang="en", history=list(history), image=image)
    r = run(main.next_step(b, x_app_token="tok", x_install_id=install, x_tester=tester))
    return r, main._claude_client.messages.calls


# 1. The picture note never tells the AI that a scanner hides a word "Next" any more. It says how to name a button with
#    no word (how it looks and where it is), and what a camera's or scanner's picture button is called.
assert '"Next" in a camera or scanner' not in main.SHOT_NOTE, main.SHOT_NOTE
assert "only if you can read that word" in main.SHOT_NOTE
assert "big round button in the middle at the bottom" in main.SHOT_NOTE

# 2. The page after the photo: "Tap the round “Next” button" on a screen with no words. ScreenGuide cannot read "Next"
#    anywhere, so the AI is asked once more, told to name only words it can read in the picture.
r, calls = step([ans("Good, your picture is taken. Tap the round “Next” button.", 0.86, 0.92),
                 ans("Good, your picture is taken. Tap the blue round button at the bottom right.", 0.86, 0.92)])
assert len(calls) == 2, len(calls)
again = calls[1]["messages"][0]["content"]
again = again if isinstance(again, str) else " ".join(p.get("text", "") for p in again if isinstance(p, dict))
assert "“Next”" in again and "only if you can read that exact word" in again, again[-600:]
assert r["say"] == "Good, your picture is taken. Tap the blue round button at the bottom right.", r
assert r["label"] is None and (r["x"], r["y"]) == (0.86, 0.92), r

# 3. The second answer lost the spot: the first answer's spot is kept, so the ring still shows.
r, calls = step([ans("Tap the round “Next” button.", 0.86, 0.92),
                 ans("Tap the blue round button at the bottom right.")], install="v100b")
assert len(calls) == 2 and r["say"] == "Tap the blue round button at the bottom right." and (r["x"], r["y"]) == (0.86, 0.92), r

# 4. The AI really can read the word in the picture (a scanner that draws "Save" on its button): asked once, kept.
r, calls = step([ans("Tap “Save” at the bottom right.", 0.85, 0.93),
                 ans("Tap “Save” at the bottom right.", 0.85, 0.93)], install="v100c")
assert len(calls) == 2 and r["say"] == "Tap “Save” at the bottom right." and r["x"] == 0.85, r

# 5. Not asked again: no quoted name, or a screen whose words can be read (the name is checked against them there).
r, calls = step([ans("Tap the big round button in the middle at the bottom.", 0.5, 0.88)], install="v100d")
assert len(calls) == 1 and r["x"] == 0.5, (len(calls), r)
r, calls = step([ans("Tap “Scan Document”.", label="Scan Document")],
                labels=["Scan Document [tap]", "Create new [switch off]", "Home [tap]", "Files [text]"], install="v100e")
assert len(calls) == 1 and r["label"] == "Scan Document", (len(calls), r)

# 6. Staged: test phones get it at once; other phones only after 24 quiet hours (one answer, unchanged, before that).
main._launch["live"][main.STAGED["unseen_name"]] = __import__("time").time()
r, calls = step([ans("Tap the round “Next” button.", 0.86, 0.92)], tester="", install="v100f")
assert len(calls) == 1 and r["say"] == "Tap the round “Next” button.", (len(calls), r)
assert main.STAGED["unseen_name"] == main.SERVER_VERSION == "1.00"

# 7. The report says when the ring was placed on a spot in the picture, instead of "pointed at: nothing".
main._sessions.clear()
r, _ = step([ans("Tap the big round button in the middle at the bottom.", 0.5, 0.88)], install="v100g")
s = main._sessions["v100g"]
assert s["steps"][-1]["spot"] is True, s["steps"][-1]
title, body = main._watch_issue(s, {"title": "t", "step": 1, "what": "w", "fix": "f"})[:2]
assert "pointed at: a spot in the screen picture" in body, body[:900]
r, _ = step([ans("Tap “Scan Document”.", label="Scan Document")],
            labels=["Scan Document [tap]", "Home [tap]", "Files [text]"], install="v100g")
assert s["steps"][-1]["spot"] is False and "pointed at: Scan Document" in main._watch_issue(s, {"title": "t", "step": 2, "what": "w", "fix": "f"})[1]

assert main.PROMPT_VERSION >= "67"
print("scanner screens: names only what can be read, the camera's big round button, the spot in the report ok")
