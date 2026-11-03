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
        code, b = get("https://graph.facebook.com/v21.0/me/permissions", access_token=ig)
        fb["permissions"] = [x.get("permission") for x in b.get("data", []) if x.get("status") == "granted"] if code == 200 \
            else str(b.get("error", b))[:200]
        code, b = get("https://graph.facebook.com/v21.0/me/businesses",
                      fields="name,instagram_accounts{id,username},owned_instagram_accounts{id,username}", access_token=ig)
        if code == 200:
            fb["businesses"] = [{"name": x.get("name"),
                                 "instagram_accounts": [a.get("username") for a in (x.get("instagram_accounts") or {}).get("data", [])],
                                 "owned_instagram_accounts": [a.get("username") for a in (x.get("owned_instagram_accounts") or {}).get("data", [])]}
                                for x in b.get("data", [])]
        else:
            fb["businesses_error"] = str(b.get("error", b))[:300]
        # IG user ids found via pages/businesses: test that the publishing edge is reachable
        ids = []
        code, b = get("https://graph.facebook.com/v21.0/me/accounts", fields="instagram_business_account", access_token=ig)
        if code == 200:
            ids += [x["instagram_business_account"]["id"] for x in b.get("data", []) if x.get("instagram_business_account")]
        code, b = get("https://graph.facebook.com/v21.0/me/businesses", fields="instagram_accounts{id},owned_instagram_accounts{id}", access_token=ig)
        if code == 200:
            for x in b.get("data", []):
                for k in ("instagram_accounts", "owned_instagram_accounts"):
                    ids += [a["id"] for a in (x.get(k) or {}).get("data", [])]
        # a user token can debug itself: granular_scopes lists the Instagram account ids it was granted
        code, b = get("https://graph.facebook.com/v21.0/debug_token", input_token=ig, access_token=ig)
        if code == 200:
            d = b.get("data", {})
            fb["debug"] = {"type": d.get("type"), "is_valid": d.get("is_valid"), "expires_at": d.get("expires_at"),
                           "data_access_expires_at": d.get("data_access_expires_at"),
                           "granular_scopes": [{"scope": g.get("scope"), "targets": len(g.get("target_ids") or [])}
                                               for g in d.get("granular_scopes", [])]}
            for g in d.get("granular_scopes", []):
                if g.get("scope") in ("instagram_basic", "instagram_content_publish"):
                    ids += g.get("target_ids") or []
        else:
            fb["debug_error"] = str(b.get("error", b))[:300]
        probes = []
        for i in dict.fromkeys(ids):
            c1, b1 = get(f"https://graph.facebook.com/v21.0/{i}", fields="username", access_token=ig)
            c2, b2 = get(f"https://graph.facebook.com/v21.0/{i}/content_publishing_limit", fields="quota_usage", access_token=ig)
            probes.append({"username": b1.get("username") if c1 == 200 else None,
                           "profile_error": None if c1 == 200 else str(b1.get("error", b1))[:200],
                           "publish_edge_ok": c2 == 200,
                           "publish_error": None if c2 == 200 else str(b2.get("error", b2))[:200]})
        fb["ig_user_probes"] = probes
        res["instagram_via_facebook"] = fb
    if ig and not ig.startswith("EAA"):
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
    elif ig:
        probes = res["instagram_via_facebook"].get("ig_user_probes", [])
        ok = [x for x in probes if x.get("publish_edge_ok")]
        res["instagram"] = {"ok": bool(ok), "username": ok[0]["username"] if ok else None, "via": "graph.facebook.com",
                            "publish_permission": bool(ok)}
    else:
        res["instagram"] = {"ok": False, "error": "secret missing"}
    out["results"][acc] = res

text = json.dumps(out, ensure_ascii=False, indent=2)
open("token_check.json", "w", encoding="utf-8").write(text + "\n")
print(text)
