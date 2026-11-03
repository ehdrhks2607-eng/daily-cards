"""Check that each account's Threads / Instagram token works, without ever printing the token.

Writes token_check.json: which account each token belongs to (username), and whether
Instagram publishing is allowed (content_publishing_limit). Run by .github/workflows/check-tokens.yml.
"""
import json
import os
from datetime import datetime, timedelta, timezone

import requests

out = {"checked_at": datetime.now(timezone(timedelta(hours=9))).isoformat(), "results": {}}


def get(url, **params):
    r = requests.get(url, params=params, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = {"raw": r.text[:200]}
    return r.status_code, body


for acc in ("JAK", "SEOUL"):
    res = {}
    th = (os.environ.get(f"{acc}_THREADS_TOKEN") or "").strip()
    if th:
        code, b = get("https://graph.threads.net/v1.0/me", fields="id,username", access_token=th)
        res["threads"] = {"ok": code == 200, "username": b.get("username")} if code == 200 else \
                         {"ok": False, "error": str(b.get("error", b))[:300]}
    else:
        res["threads"] = {"ok": False, "error": "secret missing"}
    ig = (os.environ.get(f"{acc}_IG_TOKEN") or "").strip()
    if ig:
        kind = "instagram_login(IGAA)" if ig.startswith("IG") else "facebook_login(EAA)" if ig.startswith("EAA") else "unknown"
        res["instagram_token_type"] = kind
        res["instagram_token_length"] = len(ig)
        res["instagram_token_has_whitespace"] = any(c.isspace() for c in os.environ.get(f"{acc}_IG_TOKEN", ""))
    if ig and ig.startswith("EAA"):
        fb = {}
        code, b = get("https://graph.facebook.com/v21.0/me", fields="id,name", access_token=ig)
        fb["me"] = {"ok": code == 200, "name": b.get("name")} if code == 200 else {"ok": False, "error": str(b.get("error", b))[:300]}
        code, b = get("https://graph.facebook.com/v21.0/me/accounts", fields="name,instagram_business_account{id,username}", access_token=ig)
        if code == 200:
            fb["pages"] = [{"page": x.get("name"), "ig": (x.get("instagram_business_account") or {}).get("username"),
                            "ig_id_present": bool(x.get("instagram_business_account"))} for x in b.get("data", [])]
        else:
            fb["pages_error"] = str(b.get("error", b))[:300]
        res["instagram_via_facebook"] = fb
    if ig:
        code, b = get("https://graph.instagram.com/v21.0/me", fields="user_id,username,account_type", access_token=ig)
        if code == 200:
            info = {"ok": True, "username": b.get("username"), "account_type": b.get("account_type")}
            c2, b2 = get(f"https://graph.instagram.com/v21.0/{b.get('user_id')}/content_publishing_limit",
                         fields="quota_usage,config", access_token=ig)
            info["publish_permission"] = c2 == 200
            if c2 != 200:
                info["publish_error"] = str(b2.get("error", b2))[:300]
            res["instagram"] = info
        else:
            res["instagram"] = {"ok": False, "error": str(b.get("error", b))[:300]}
    else:
        res["instagram"] = {"ok": False, "error": "secret missing"}
    out["results"][acc] = res

text = json.dumps(out, ensure_ascii=False, indent=2)
open("token_check.json", "w", encoding="utf-8").write(text + "\n")
print(text)
