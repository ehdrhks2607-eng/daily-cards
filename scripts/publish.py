"""Publish due posts to Threads and Instagram via the official Meta APIs.

Runs inside GitHub Actions. For every posts/<date>/<account>/post.json that is
approved (or approval not required) and whose publish_at has passed, it posts:
  - Threads: text post, then the first comment (coupang link) as a reply
  - Instagram: carousel of the card PNGs with the caption
Results are written back into post.json so a platform is never posted twice.

Secrets (env): <ACCOUNT>_THREADS_TOKEN, <ACCOUNT>_IG_TOKEN  e.g. JAK_THREADS_TOKEN
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
KST = timezone(timedelta(hours=9))
THREADS = "https://graph.threads.net/v1.0"
IG = "https://graph.instagram.com/v21.0"
PLACEHOLDER = "[쿠팡링크"
DRY_RUN = os.environ.get("DRY_RUN") == "1"


def log(*a):
    print(datetime.now(KST).strftime("%H:%M:%S"), *a, flush=True)


def call(method, url, **params):
    if DRY_RUN:
        log("DRY", method, url.split("?")[0], {k: v for k, v in params.items() if k != "access_token"})
        return {"id": "dry-run-id", "status_code": "FINISHED"}
    r = requests.request(method, url, params=params, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"{r.status_code} {url.split('?')[0]}: {r.text[:500]}")
    return r.json()


# ---------------- Threads ----------------
def threads_uid(token):
    return call("GET", f"{THREADS}/me", fields="id", access_token=token)["id"]


def threads_post(token, text, reply_to=None):
    uid = threads_uid(token)
    params = {"media_type": "TEXT", "text": text, "access_token": token}
    if reply_to:
        params["reply_to_id"] = reply_to
    c = call("POST", f"{THREADS}/{uid}/threads", **params)
    time.sleep(3 if DRY_RUN else 10)
    p = call("POST", f"{THREADS}/{uid}/threads_publish", creation_id=c["id"], access_token=token)
    return p["id"]


# ---------------- Instagram ----------------
def ig_wait(token, container_id):
    for _ in range(30):
        s = call("GET", f"{IG}/{container_id}", fields="status_code", access_token=token)
        if s.get("status_code") == "FINISHED":
            return
        if s.get("status_code") == "ERROR":
            raise RuntimeError(f"IG container {container_id} ERROR")
        time.sleep(0 if DRY_RUN else 5)
    raise RuntimeError(f"IG container {container_id} timeout")


def ig_uid(token):
    r = call("GET", f"{IG}/me", fields="user_id", access_token=token)
    return r.get("user_id") or r["id"]


def ig_carousel(token, image_urls, caption):
    uid = ig_uid(token)
    children = []
    for url in image_urls:
        c = call("POST", f"{IG}/{uid}/media", image_url=url, is_carousel_item="true", access_token=token)
        ig_wait(token, c["id"])
        children.append(c["id"])
    parent = call("POST", f"{IG}/{uid}/media", media_type="CAROUSEL",
                  children=",".join(children), caption=caption, access_token=token)
    ig_wait(token, parent["id"])
    p = call("POST", f"{IG}/{uid}/media_publish", creation_id=parent["id"], access_token=token)
    return p["id"]


def raw_url(rel_path):
    repo = os.environ.get("GITHUB_REPOSITORY", "OWNER/REPO")
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{rel_path}"


# ---------------- main ----------------
def process(post_file, cfg, now):
    try:
        post = json.loads(post_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        log(post_file.parent, "SKIPPED: broken JSON ->", e)
        return False
    if post.get("status") in ("posted", "expired", "skipped"):
        return False
    if cfg["require_approval"] and not post.get("approved"):
        return False
    due = datetime.fromisoformat(post["publish_at"])
    if now < due:
        return False
    if not post.get("result") and now - due > timedelta(hours=cfg["skip_if_late_hours"]):
        post["status"] = "expired"
        log(post_file.parent, "expired (too late)")
        post_file.write_text(json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8")
        return True

    acc = post["account"].upper()
    res = post.setdefault("result", {})
    errors = []
    changed = False

    th_token = os.environ.get(f"{acc}_THREADS_TOKEN")
    if th_token and not res.get("threads"):
        try:
            res["threads"] = threads_post(th_token, post["threads"]["text"])
            log(acc, "threads posted", res["threads"])
            changed = True
        except Exception as e:
            errors.append(f"threads: {e}")
    comment = post["threads"].get("comment", "")
    if th_token and res.get("threads") and not res.get("threads_comment") and comment:
        if PLACEHOLDER in comment:
            log(acc, "comment skipped: coupang link placeholder not replaced")
        else:
            try:
                res["threads_comment"] = threads_post(th_token, comment, reply_to=res["threads"])
                changed = True
            except Exception as e:
                errors.append(f"threads comment: {e}")

    ig_token = os.environ.get(f"{acc}_IG_TOKEN")
    if ig_token and not res.get("instagram"):
        try:
            rel_dir = post_file.parent.relative_to(ROOT).as_posix()
            urls = [raw_url(f"{rel_dir}/{img}") for img in post["instagram"]["images"]]
            res["instagram"] = ig_carousel(ig_token, urls, post["instagram"]["caption"])
            log(acc, "instagram posted", res["instagram"])
            changed = True
        except Exception as e:
            errors.append(f"instagram: {e}")

    need = [k for k, tok in (("threads", th_token), ("instagram", ig_token)) if tok]
    if th_token and comment:
        need.append("threads_comment")  # waits until the coupang link is filled in
    if need and all(res.get(k) for k in need):
        post["status"] = "posted"
        post["posted_at"] = now.isoformat()
        changed = True
    if errors:
        post["last_error"] = " | ".join(errors)[:1000]
        log(acc, "ERRORS:", post["last_error"])
        changed = True
    if changed:
        post_file.write_text(json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8")
    return changed


def main():
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    now = datetime.now(KST)
    if os.environ.get("NOW"):  # for testing
        now = datetime.fromisoformat(os.environ["NOW"])
    files = sorted(ROOT.glob("posts/*/*/post.json"))
    log(f"checking {len(files)} posts at {now.isoformat()}")
    for f in files:
        process(f, cfg, now)


if __name__ == "__main__":
    sys.exit(main())
