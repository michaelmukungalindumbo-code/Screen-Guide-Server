import os, asyncio, json
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run
class Msgs:
    def __init__(self, out): self.out = list(out)
    async def create(self, **kw):
        class U: input_tokens = 900; output_tokens = 40
        class B: type = "text"; text = self.out.pop(0)
        class M: content = [B()]; usage = U(); stop_reason = "end_turn"
        return M()
class Client:
    def __init__(self, out): self.messages = Msgs(out)
J = lambda label, say: json.dumps({"label": label, "say": say, "done": False, "x": None, "y": None, "look_for": None})
# The second message in the Help chat: the phone sends the earlier chat as "User said: …" and "Told: …" lines.
H = ["Tap Wi-Fi.", "User said: I can't find it", "Told: Tap Wi-Fi.", "User said: I don't understand"]
assert main._last_told(H) == "Tap Wi-Fi." and main._last_told(["Tap Apps."]) == "Tap Apps." and main._last_told([]) == ""
WIFI = ["Wi-Fi [tap]", "Bluetooth [switch]", "Mobile data [tap]"]
main.event  # the watcher must still see the repeat on the second Help message
run(main.event(main.Event(event="start", guide="ai"), x_app_token="tok", x_install_id="dev53", x_tester="1"))
main._claude_client = Client([J("Wi-Fi", "Tap Wi-Fi.")])
r = run(main.next_step(main.Next(goal="Turn on Wi-Fi", labels=WIFI, note="I don't understand", stuck=True, history=H),
                       x_app_token="tok", x_install_id="dev53", x_tester="1"))
assert r["watch"] == 1 and main._sessions["dev53"]["problems"][0]["kind"] == "help_repeated", main._sessions["dev53"]["problems"]
assert main._sessions["dev53"]["steps"][0]["told_before"] == "Tap Wi-Fi."
# Gallery: the explanation is used on a second Help message too
YT = ["Upload from gallery [text]", "Videos [tap]", "Select more media [tap]", "0:09 [text]", "0:14 [text]"]
SAME = "Tap the video you want, or tap + if it is not here."
main._claude_client = Client([J(None, SAME)])
r = run(main.next_step(main.Next(goal="Upload a video in the YouTube app", labels=YT, note="I don't understand", stuck=True,
                                 history=[SAME, "User said: I can't find it", "Told: " + SAME, "User said: I don't understand"]),
                       x_app_token="tok", x_install_id="dev53b"))
assert r["say"].startswith("Your videos are the small pictures"), r
assert main.SERVER_VERSION >= "0.53"
print("Help chat history ok")
