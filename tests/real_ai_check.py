# The real AI, asked real conversations from the owner's phone tests, before a server update reaches anyone. 6 Nov: a
# change that fixed one conversation broke another, and only a phone test showed it, because the other tests use a
# pretend AI. Each case is in tests/real_ai_cases.json; add one for every chat that goes wrong.
# The AI does not always word things the same way, so a case that fails is asked once more and fails only if it fails
# twice. Run by GitHub ("real-ai" in .github/workflows/tests.yml) with the Anthropic key. Without the key it cannot check
# anything: it says so and does not block the update.
import os, sys, json, asyncio

if not os.getenv("ANTHROPIC_API_KEY"):
    print("::warning::The real-AI check did not run: add ANTHROPIC_API_KEY to this repository's GitHub secrets.")
    sys.exit(0)
for k, v in {"AI_PROVIDER": "claude", "ANTHROPIC_MODEL": "claude-haiku-5-5", "APP_TOKEN": "ci", "ADMIN_KEY": "ci"}.items():
    os.environ.setdefault(k, v)   # the same AI as on Render
import main

CASES = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "real_ai_cases.json"), encoding="utf-8"))["cases"]


def problems(case: dict, r: dict) -> list:
    words = " ".join([r.get("answer", ""), r.get("goal", ""), " ".join(r.get("plan") or [])]).lower().replace("screen guide", "screenguide")
    out = []
    if case.get("kind") and r.get("kind") != case["kind"]:
        out.append("kind %s, wanted %s" % (r.get("kind"), case["kind"]))
    for group in case.get("all", []):
        if not any(w in words for w in group):
            out.append("none of: " + ", ".join(group))
    for w in case.get("none", []):
        if w in words:
            out.append("should not say: " + w)
    return out


async def one(case: dict):
    main._TALLY.set(None)
    # 0.96: as test phones get it (and everyone, 24 hours after an update): every chat answer thought through first
    r = await main._answer(case["question"], "en", [], case.get("history", []), apps=case.get("apps"), tester=True)
    return r, problems(case, r)


async def main_check() -> int:
    failed = 0
    for case in CASES:
        r, bad = await one(case)
        if bad:
            r, bad = await one(case)   # once more: the AI words things differently each time
        mark = "FAIL" if bad else "ok  "
        print("%s %s" % (mark, case["name"]))
        if bad:
            failed += 1
            print("     " + "; ".join(bad))
            print("     answer: %s | goal: %s | plan: %s" % (r.get("answer", "")[:220], r.get("goal", ""), " / ".join(r.get("plan") or [])))
    cost = sum(v.get("cost", 0) for v in main.USAGE.values()) if isinstance(main.USAGE, dict) else 0
    print("%d of %d conversations right. Cost of this check: about US$%.3f" % (len(CASES) - failed, len(CASES), cost))
    return failed


sys.exit(1 if asyncio.run(main_check()) else 0)
