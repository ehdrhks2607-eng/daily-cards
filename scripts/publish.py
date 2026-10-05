"""Publish due posts to Threads and Instagram via the official Meta APIs.

Runs inside GitHub Actions. For every posts/<date>/<account>/post.json that is
approved (or approval not required) and whose publish_at has passed, it posts:
  - Threads: text post (or video post when threads.video is set), then the first comment (coupang link) as a reply
  - Instagram: carousel of the card PNGs with the caption
  - Instagram Reels: reel.mp4 (rendered by render_reel.py) with reel.caption
Results are written back into post.json so a platform is never posted twice.

Secrets (env): <ACCOUNT>_THREADS_TOKEN, <ACCOUNT>_IG_TOKEN  e.g. JAK_THREADS_TOKEN
"""
import json
import os
import posixpath
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


def threads_wait(token, container_id, tries=60):
    if DRY_RUN:
        return
    for _ in range(tries):
        s = call("GET", f"{THREADS}/{container_id}", fields="status", access_token=token)
        if s.get("status") == "FINISHED":
            return
        if s.get("status") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Threads container {container_id} {s.get('status')}: {s.get('error_message', '')}")
        time.sleep(0 if DRY_RUN else 5)
    raise RuntimeError(f"Threads container {container_id} timeout")


def threads_post(token, text, reply_to=None, video_urls=None):
    """Text post, or (video_urls given) a VIDEO post; tries each public URL in turn."""
    uid = threads_uid(token)
    if not video_urls:
        params = {"media_type": "TEXT", "text": text, "access_token": token}
        if reply_to:
            params["reply_to_id"] = reply_to
        c = call("POST", f"{THREADS}/{uid}/threads", **params)
        time.sleep(3 if DRY_RUN else 10)
    else:
        errs = []
        for url in video_urls:
            try:
                c = call("POST", f"{THREADS}/{uid}/threads", media_type="VIDEO", video_url=url,
                         text=text, access_token=token)
                threads_wait(token, c["id"])
                break
            except Exception as e:
                errs.append(str(e)[:200])
                log("threads video via url failed, trying next:", errs[-1])
        else:
            raise RuntimeError(" / ".join(errs))
    p = call("POST", f"{THREADS}/{uid}/threads_publish", creation_id=c["id"], access_token=token)
    return p["id"]


# ---------------- Instagram ----------------
def ig_wait(token, container_id, tries=30):
    for _ in range(tries):
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


def ig_reel(token, video_urls, local_file, caption):
    """Publish a Reel. Tries public video URLs first (jsDelivr serves video/mp4),
    then falls back to a resumable upload of the local file."""
    uid = ig_uid(token)
    errs = []
    for url in video_urls:
        try:
            c = call("POST", f"{IG}/{uid}/media", media_type="REELS", video_url=url,
                     caption=caption, share_to_feed="true", access_token=token)
            ig_wait(token, c["id"], tries=60)
            p = call("POST", f"{IG}/{uid}/media_publish", creation_id=c["id"], access_token=token)
            return p["id"]
        except Exception as e:
            errs.append(f"{url.split('/')[2]}: {e}")
            log("reel via url failed, trying next:", str(e)[:200])
    try:
        c = call("POST", f"{IG}/{uid}/media", media_type="REELS", upload_type="resumable",
                 caption=caption, share_to_feed="true", access_token=token)
        if not DRY_RUN:
            data = Path(local_file).read_bytes()
            r = requests.post(c.get("uri") or f"https://rupload.facebook.com/ig-api-upload/v21.0/{c['id']}",
                              headers={"Authorization": f"OAuth {token}", "offset": "0",
                                       "file_size": str(len(data))}, data=data, timeout=300)
            if r.status_code >= 400:
                raise RuntimeError(f"rupload {r.status_code}: {r.text[:300]}")
        ig_wait(token, c["id"], tries=60)
        p = call("POST", f"{IG}/{uid}/media_publish", creation_id=c["id"], access_token=token)
        return p["id"]
    except Exception as e:
        errs.append(f"resumable: {e}")
    raise RuntimeError(" / ".join(errs))


def cdn_url(rel_path):
    repo = os.environ.get("GITHUB_REPOSITORY", "OWNER/REPO")
    ref = os.environ.get("GITHUB_SHA") or os.environ.get("GITHUB_REF_NAME", "main")
    return f"https://cdn.jsdelivr.net/gh/{repo}@{ref}/{rel_path}"


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

    has_threads = bool(post.get("threads", {}).get("text"))
    has_ig = bool(post.get("instagram", {}).get("images"))
    th_token = os.environ.get(f"{acc}_THREADS_TOKEN") if has_threads else None
    if th_token and not res.get("threads"):
        try:
            video = post["threads"].get("video")  # path relative to this post folder, e.g. ../jak_reel/reel.mp4
            vurls = None
            if video:
                rel = posixpath.normpath(f"{post_file.parent.relative_to(ROOT).as_posix()}/{video}")
                vurls = [cdn_url(rel), raw_url(rel)]
            res["threads"] = threads_post(th_token, post["threads"]["text"], video_urls=vurls)
            log(acc, "threads posted", res["threads"])
            changed = True
        except Exception as e:
            errors.append(f"threads: {e}")
    comment = post.get("threads", {}).get("comment", "")
    if th_token and res.get("threads") and not res.get("threads_comment") and comment:
        if PLACEHOLDER in comment:
            log(acc, "comment skipped: coupang link placeholder not replaced")
        else:
            try:
                res["threads_comment"] = threads_post(th_token, comment, reply_to=res["threads"])
                changed = True
            except Exception as e:
                errors.append(f"threads comment: {e}")

    ig_token = os.environ.get(f"{acc}_IG_TOKEN") if has_ig else None
    if ig_token and not res.get("instagram"):
        try:
            rel_dir = post_file.parent.relative_to(ROOT).as_posix()
            urls = [raw_url(f"{rel_dir}/{img}") for img in post["instagram"]["images"]]
            res["instagram"] = ig_carousel(ig_token, urls, post["instagram"]["caption"])
            log(acc, "instagram posted", res["instagram"])
            changed = True
        except Exception as e:
            errors.append(f"instagram: {e}")

    has_reel = bool(post.get("reel", {}).get("video"))
    reel_token = os.environ.get(f"{acc}_IG_TOKEN") if has_reel else None
    if reel_token and not res.get("reel"):
        try:
            rel = f"{post_file.parent.relative_to(ROOT).as_posix()}/{post['reel']['video']}"
            res["reel"] = ig_reel(reel_token, [cdn_url(rel), raw_url(rel)], ROOT / rel,
                                  post["reel"].get("caption", ""))
            log(acc, "reel posted", res["reel"])
            changed = True
        except Exception as e:
            errors.append(f"reel: {e}")

    need = [k for k, tok in (("threads", th_token), ("instagram", ig_token), ("reel", reel_token)) if tok]
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
