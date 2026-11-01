import os, asyncio, base64
os.environ.update(ADMIN_KEY="k")
import main
run = asyncio.run
def err(f):
    try: run(f); return None
    except main.HTTPException as e: return e
audio = base64.b64encode(b"\x00" * 3000).decode()
assert err(main.voice_upload(main.VoiceIn(lang="bem", key="tap", audio=audio), x_admin_key="wrong")) is not None, "only the owner can publish"
assert run(main.voice_upload(main.VoiceIn(lang="bem", key="tap", audio=audio), x_admin_key="k"))["ok"]
assert err(main.voice_upload(main.VoiceIn(lang="fr", key="tap", audio=audio), x_admin_key="k")).status_code == 400
assert err(main.voice_upload(main.VoiceIn(lang="bem", key="../x", audio=audio), x_admin_key="k")).status_code == 400
assert err(main.voice_upload(main.VoiceIn(lang="bem", key="tap", audio="not base64!"), x_admin_key="k")).status_code == 400
assert err(main.voice_upload(main.VoiceIn(lang="bem", key="tap", audio=base64.b64encode(b"x").decode()), x_admin_key="k")).status_code == 413
lst = run(main.voices(x_app_token="tok"))["clips"]
assert list(lst) == ["bem_tap"] and lst["bem_tap"] > 0, lst
assert run(main.voice_get("bem_tap", x_app_token="tok"))["audio"] == audio
assert err(main.voice_get("bem_tap", x_app_token="bad")).status_code == 401 and err(main.voice_get("ny_tap", x_app_token="tok")).status_code == 404
assert main.SERVER_VERSION >= "0.46"
print("voices ok")
