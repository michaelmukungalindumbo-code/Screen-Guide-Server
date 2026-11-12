import os, json
os.environ.update(ADMIN_KEY="k")
import main

# The owner (12 Nov), after comparing ScreenGuide with Gemini Live: "I think ScreenGuide should be able to answer general
# questions too." The helper said "I can only help with phone tasks" to anything else. Now it answers any question,
# briefly and simply, with the same safety rules: money stays advice only, nothing harmful, and health, legal or
# emergency questions also point to a real professional or service.
S = main.SYSTEM
assert "you can only help with phone tasks" not in S
assert "Answer any question the user asks" in S
assert "a doctor, a nurse or a clinic" in S and "Never give instructions that could hurt someone" in S
assert "never Show me" in S                                           # a general question is kind "answer": nothing to tap
assert main.PROMPT_VERSION >= "64" and main.SERVER_VERSION >= "0.91"
cases = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "real_ai_cases.json"), encoding="utf-8"))["cases"]
gen = [c for c in cases if c["name"].startswith("12 Nov: a general question")]
assert len(gen) >= 2 and all(c.get("kind") == "answer" for c in gen)
assert all("only help with phone" in " ".join(c["none"]) for c in gen)
print("any question is answered, briefly and safely; a general question is an answer, never Show me")
