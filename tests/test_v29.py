import asyncio, json
import main
run = asyncio.run
async def fake(system, question, images=None, kind="ask", schema=None, **kw):
    return json.dumps({"label": "Personal Hotspot", "say": "Tap the switch.", "done": False, "x": None, "y": None})
main._complete = fake
run(main.next_step(main.Next(goal="Turn on hotspot", labels=["Portable hotspot [text]", "Personal Hotspot [switch]", "Call 0977123456 [tap]"], stuck=True),
                   x_app_token="tok", x_install_id="st1"))
run(main.next_step(main.Next(goal="not stuck", labels=["A [tap]"]), x_app_token="tok", x_install_id="st2"))
assert len(main._stuck) == 1
x = main._stuck[-1]
assert x["label"] == "Personal Hotspot" and "Portable hotspot" in x["words"] and "0977" not in x["words"], x
page = run(main.admin_report(key="k")).body if main.ADMIN_KEY else ""
assert "Help during a guide" in run(main.privacy()).body
print("stuck screens ok")
main.ADMIN_KEY = "k"
page = run(main.admin_report(key="k")).body
assert "Where people tapped Help" in page and "Personal Hotspot" in page and "0977" not in page
print("report shows stuck screens ok")
