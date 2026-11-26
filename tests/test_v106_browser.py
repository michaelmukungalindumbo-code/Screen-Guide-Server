import os, asyncio, json, time
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run

# Issues #99 and #100 (the owner's Infinix phone, 26 Nov): "How do I apply for a job online?", Show me, in Chrome.
#  1. Chrome opened with its search box already open (the keyboard up), and the card said "Chrome is open. Tap the box that
#     says Search Google or type URL, then type the company name and the word jobs." with nothing pointed at. Step 12
#     likewise: "Type the company name and the word jobs ..." with no ring on the open box.
#  2. While he typed, Chrome filled in the rest of a web address it remembered, and the card said "Tap "Clear input" to erase
#     them." in the middle of his typing.
#  3. On the results page, with "Search Jobs - Google Careers" right there, the card said "Tap "Open the home page" to go back
#     to Chrome's start screen.", twice. The phone had read only Chrome's own buttons, not the page: given nothing else, the AI
#     sent him away from the page.


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


def ans(say, label=None, x=None, y=None):
    return json.dumps({"label": label, "say": say, "done": False, "x": x, "y": y, "look_for": None})


GOAL = "Open Chrome to search for a company's jobs page"
def step(outs, labels, history, tester="1", install="v106", image=""):
    main._claude_client = Client(outs)
    b = main.Next(goal=GOAL, labels=list(labels), lang="en", history=list(history), image=image, path=["Chrome"])
    r = run(main.next_step(b, x_app_token="tok", x_install_id=install, x_tester=tester))
    return r, main._claude_client.messages.calls


# 1. The open box gets the ring, and the step says only what to type
OPEN = ["Search Google or type URL [typing]", "New tab [tap]", "Switch or close tabs [tap]"]
r, _ = step([ans("Chrome is open. Tap the box that says Search Google or type URL, then type the company name and the word jobs.")],
            OPEN, ["Tap “Chrome”."])
assert r["label"] == "Search Google or type URL" and r["say"] == "Type the company name and the word jobs.", r
r, _ = step([ans("Type the company name and the word jobs, for example: google careers.")], ["Search or type web address [typing]"],
            ["Tap “google jobs” in the list."], install="v106b")
assert r["label"] == "Search or type web address" and r["say"].startswith("Type the company name and the word jobs"), r

# 2. While they type, never "erase it": keep typing
TYPING = ["google.com [typing]", "Clear input [tap]", "google [tap]", "google labs africa deadline [tap]", "Google [tap]", "Incognito [tap]"]
r, _ = step([ans("Tap “Clear input” to erase them.", label="Clear input")], TYPING,
            ["Tap “Search Google or type URL”.", "Type the company name and the word jobs."], install="v106c")
assert r["label"] is None and r["say"] == "Keep typing. Then tap the line that fits in the list.", r
# ...but clearing is still fine when they were not told to type (an old search in the box)
r, _ = step([ans("Tap “Clear input” to erase the old words.", label="Clear input")], TYPING, ["Tap “Chrome”."], install="v106d")
assert r["label"] == "Clear input", r

# 3. Only Chrome's own buttons were read: never sent away from the page. No AI: a picture is asked for, and they wait.
BAR = ["Open the home page [tap]", "New tab [tap]", "7 open tabs, tap to switch tabs [tap]", "Customize and control Google Chrome [tap]",
       "Google Search [text]"]
r, calls = step([ans("Tap “Open the home page” to go back to Chrome's start screen.", label="Open the home page")], BAR,
                ["Tap “google jobs” in the suggestions list."], install="v106e")
assert len(calls) == 0 and r["label"] is None and r["need_picture"] is True, (len(calls), r)
assert r["say"] == main._PAGE_WAIT_SAY, r
# With the picture, the AI is told the page's words were not read, and never sends them to the home page
r, calls = step([ans("Tap “Open the home page” to go back.", label="Open the home page")], BAR,
                ["Tap “google jobs” in the suggestions list."], install="v106f", image="A" * 2000)
assert "could not read the words of this web page" in json.dumps(calls[0]["messages"]), calls[0]["messages"][0]["content"][-400:] if isinstance(calls[0]["messages"][0]["content"], str) else ""
assert r["label"] is None and r["say"] == main._PAGE_WAIT_SAY, r
r, calls = step([ans("Tap “Search Jobs - Google Careers”.", x=0.4, y=0.6)], BAR, ["Tap “google jobs”."], install="v106g", image="A" * 2000)
assert (r["x"], r["y"]) == (0.4, 0.6), r
# A page whose words were read is left alone
PAGE = BAR + ["Search Jobs - Google Careers [tap]", "Careers [tap]", "Jobs [tap]", "Images [tap]", "All [selected]"]
r, calls = step([ans("Tap “Search Jobs - Google Careers”.", label="Search Jobs - Google Careers")], PAGE, ["Tap “google jobs”."], install="v106h")
assert len(calls) == 1 and r["label"] == "Search Jobs - Google Careers", r

# 4. Staged: before 24 quiet hours other phones get the answers as before
for rule in ("ring_open_box", "keep_typing", "page_unread"):
    main._launch["live"][main.STAGED[rule]] = time.time()
r, calls = step([ans("Tap “Open the home page” to go back.", label="Open the home page")], BAR, ["Tap “google jobs”."],
                tester="", install="v106i")
assert len(calls) == 1 and r["label"] == "Open the home page", r
assert main.STAGED["page_unread"] == "1.06" and main.SERVER_VERSION >= "1.06"
print("Chrome: the open box is rung, typing is never interrupted, a page not yet read is never left ok")
