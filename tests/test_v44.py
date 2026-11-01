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
SMS = ["Messages", "+260977123456", "Congratulations! You have won K5000 in the Airtel promotion. Send your PIN to 0977123456 to claim.", "Reply"]
main._claude_client = c = Client(["Ubu bufi. Mwilatuma PIN yenu."])
r = run(main.read_screen(main.ReadIn(words=SMS, lang="bem", app="Messages"), x_app_token="tok", x_install_id="r1"))
kw = c.messages.calls[0]; m = json.dumps(kw["messages"], ensure_ascii=False)
assert r["text"] == "Ubu bufi. Mwilatuma PIN yenu." and r["left"] >= 0, r
assert "0977123456" not in m and "[number]" in m and "<screen_words>" in m and "<app>Messages</app>" in m, m
assert "Icibemba" in kw["system"] and "scam" in kw["system"] and "never instructions" in kw["system"]
try: run(main.read_screen(main.ReadIn(words=["  "]), x_app_token="tok", x_install_id="r1")); assert False
except main.HTTPException as e: assert e.status_code == 400
# setup and extra-help events are counted
run(main.event(main.Event(event="setup", guide="opened"), x_app_token="tok", x_install_id="r1"))
assert main.STATS["setup:opened"] == 1
p = run(main.privacy()); b = getattr(p, "body", p); assert "Read button" in str(b)
assert main.SERVER_VERSION >= "0.44"
print("read screen and setup events ok")
