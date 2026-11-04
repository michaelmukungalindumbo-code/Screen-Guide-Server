# ScreenGuide server: instructions for the AI fixer

This is ScreenGuide's server (FastAPI, Python): it decides each guide step (`/next`), answers questions, and keeps crash
reports. It runs on Render, which deploys `main` only after the GitHub tests pass. The owner is a solo developer who works
only on his phone. Write your issue comments in plain English for a non-specialist.

In the AI fixer's run, this repository is checked out in `server/`, next to the app. Work inside `server/`.

## How it is laid out

- All server code is in `main.py`. The prompts for the AI are in it too (for example `NEXT_SYSTEM` for guide steps).
- After the AI answers a step, plain Python rules correct it (for example `_gallery_fix`, `_one_action`). Many bugs live
  in those rules, not in the AI: check them before changing a prompt.
- Tests: `tests/test_*.py`, one small program each, with stand-ins (`tests/stubs`) and a pretend AI, so they need no keys.
  Run all of them with `bash tests/run.sh` (from `server/`), or only some: `bash tests/run.sh test_v54`. See `tests/test_v50.py` for how to replay a screen through
  `next_step` with a pretend AI answer.

## How to fix a guide problem

1. Replay the screen from the issue in a new test first (`tests/test_vNN.py`, NN = the new server version), and run it to
   see it fail. Use the screen words exactly as the issue gives them; "…" stands for words that were removed.
2. Fix the cause, for every screen like this one, not just this screen. Keep the change small.
   A new rule that changes what users see (not watcher-only or test-phone-only changes) is **staged**: add it to
   `STAGED` with the new `SERVER_VERSION`, run it only when `_staged("<name>", x_tester == "1")` is true, and call
   `_fired("<name>")` when it changes an answer. Test phones get it at once, everyone after 24 quiet hours, and it
   pauses itself if people press Help right after it far more than usual (the Launch Bay; see `tests/test_v71_launch.py`).
3. Run `bash tests/run.sh`. Every test must pass.
4. Bump `SERVER_VERSION` in `main.py` (0.57 becomes 0.58). If you change a prompt, bump `PROMPT_VERSION` too.
5. Do not commit or push anything in `server/` yourself. A later step in the run sends your server changes as a pull
   request. Write its title on the first line of `media/server-fix.md`, then a short plain-English description.

## When you cannot reproduce a problem (learned 4 Nov)

- Do not stop at "probably the phone", "probably Android" or "probably the network". Check our own side first: replay
  the screen with the issue's exact words, and look at what the server's rules did to the AI's answer.
- If a test cannot show the cause, add a measurement so the next report proves it (a field on the watcher's step, a
  STATS counter on the report page), the way slow answers now say where the time went. Include it in your change.
- If you still stop without a fix, start your comment with the line `**Needs a deeper look**`, so the owner's next
  session with Claude picks it up.

## Change requests and ideas

Issues titled "Change request: …" or "Idea: …" are not bugs: the developer asked for something to be added, removed or
changed. Changing what ScreenGuide does is allowed for these. Small and clear (wording, a size, a colour, one rule):
make it, with a test where the logic can be tested. Big (more than one screen, a new feature, or a change to what
ScreenGuide does for its users) or unclear: reply on the issue with a short plan in plain English and stop. The owner
answers with @claude.

## Rules

- Never delete, skip or weaken a test to make it pass.
- Privacy: never log or store what people ask or what is on their screen beyond what the code already allows. Never put
  names, messages or numbers in tests: use button names and "…".
- Nyanja (ny) and Bemba (bem): never invent new wording. Use English, or ask the owner for the words.
- Never point ScreenGuide at money, banking, PIN or password screens (`RISKY`).
- If the fix changes what ScreenGuide does in a way the owner should decide, ask one clear question on the issue and stop.
