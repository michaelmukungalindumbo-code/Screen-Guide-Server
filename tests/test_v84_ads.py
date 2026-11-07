import os, asyncio, base64, time
os.environ.update(ADMIN_KEY="k")
import main
from fastapi import HTTPException, Request
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
run = asyncio.run
H = dict(x_app_token="tok", x_install_id="devAds", x_pass="")

# v0.84, the owner's choice (7 Nov): a free user who used today's help may watch a short ad: 5 more questions and 20 more
# guided steps for 24 hours, up to 3 ads a day. Plus users never see ads.
p = run(main.plan(**H))
assert p["ads"] == {"on": True, "left": 3, "ask": 5, "steps": 20}, p
assert main._ads_status("devAds", "plus") == {"on": False, "left": 0, "ask": 5, "steps": 20}

# Today's questions used up: no more, until an ad
now = time.time()
main._day["devAds"].extend([now] * main.LIMITS["free"][0])
assert main._allow("devAds", "free") == "day" and main._left("devAds", "free") == 0
r = run(main.ads_claim(main.AdClaim(nonce="ad-1"), **H))       # test ads: the phone's own "watched" counts
assert r["left"] == 5 and r["ads"]["left"] == 2, r
assert main._allow("devAds", "free") == ""                       # one more question now
r = run(main.ads_claim(main.AdClaim(nonce="ad-1"), **H))       # the same ad again: not twice
assert r["ads"]["left"] == 2, r
run(main.ads_claim(main.AdClaim(nonce="ad-2"), **H)); r = run(main.ads_claim(main.AdClaim(nonce="ad-3"), **H))
assert r["ads"]["left"] == 0
r = run(main.ads_claim(main.AdClaim(nonce="ad-4"), **H))       # at most 3 a day
assert r["ads"]["left"] == 0 and main._ad_bonus("devAds") == (15, 60)
# Guided steps get their share too
main._s_day["devAds"].extend([now] * main.LIMITS["free"][1])
assert main._allow_step("devAds", "free") == ""                  # 60 + 3 x 20

# With real ads, only Google's own message counts: the phone's word is not enough
main.ADS_TEST_CLAIMS = False
r = run(main.ads_claim(main.AdClaim(nonce="ad-5"), **dict(H, x_install_id="devAds2")))
assert r["ads"]["left"] == 3, r

# Google's message (server-side verification): signed with Google's key, checked here, counted once
key = ec.generate_private_key(ec.SECP256R1())
pem = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
main._ads_keys.update(at=time.time(), keys={"3335741209": pem})
def google(user, tx, good=True):
    msg = ("ad_network=5450213213286189855&ad_unit=1234567890&custom_data=sg&reward_amount=1&reward_item=help"
           "&timestamp=1730960000000&transaction_id=%s&user_id=%s" % (tx, user))
    sig = key.sign(msg.encode() if good else (msg + "x").encode(), ec.ECDSA(hashes.SHA256()))
    return msg + "&signature=" + base64.urlsafe_b64encode(sig).decode().rstrip("=") + "&key_id=3335741209"
assert run(main.ads_ssv(Request(google("devAds2", "tx-1")))) == {"ok": True}
assert main._ads_status("devAds2", "free")["left"] == 2
run(main.ads_ssv(Request(google("devAds2", "tx-1"))))           # Google may call twice: counted once
assert main._ads_status("devAds2", "free")["left"] == 2
try:
    run(main.ads_ssv(Request(google("devAds2", "tx-2", good=False)))); raise SystemExit("a wrong signature must be refused")
except HTTPException as e:
    assert e.status_code == 403
assert main._ads_status("devAds2", "free")["left"] == 2
assert run(main.ads_ssv(Request(""))) == {"ok": True}           # AdMob checking the address: nothing counted
assert main.STATS["ads_rewarded"] >= 4 and main.STATS["ads_bad_signature"] >= 1
print("an ad watched gives 5 questions and 20 steps, 3 a day, counted once; only Google's signed message once real")
