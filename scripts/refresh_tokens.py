"""Refresh long-lived Threads / Instagram tokens and save them back as GitHub secrets.

Long-lived tokens last 60 days; running this weekly keeps them alive forever.
Needs env GH_PAT (fine-grained token with 'Secrets: read & write' on this repo).
"""
import base64
import os

import requests
from nacl import encoding, public

REPO = os.environ["GITHUB_REPOSITORY"]
GH = f"https://api.github.com/repos/{REPO}/actions/secrets"
HEAD = {"Authorization": f"Bearer {os.environ['GH_PAT']}", "Accept": "application/vnd.github+json"}

REFRESH = {
    "THREADS": ("https://graph.threads.net/refresh_access_token", "th_refresh_token"),
    "IG": ("https://graph.instagram.com/refresh_access_token", "ig_refresh_token"),
}


def put_secret(name, value):
    key = requests.get(f"{GH}/public-key", headers=HEAD, timeout=30).json()
    box = public.SealedBox(public.PublicKey(key["key"].encode(), encoding.Base64Encoder()))
    enc = base64.b64encode(box.encrypt(value.encode())).decode()
    r = requests.put(f"{GH}/{name}", headers=HEAD, timeout=30,
                     json={"encrypted_value": enc, "key_id": key["key_id"]})
    r.raise_for_status()


def main():
    for acc in ("JAK", "SEOUL"):
        for kind, (url, grant) in REFRESH.items():
            name = f"{acc}_{kind}_TOKEN"
            tok = os.environ.get(name)
            if not tok:
                continue
            r = requests.get(url, params={"grant_type": grant, "access_token": tok}, timeout=30)
            if r.status_code != 200:
                print(f"{name}: refresh failed {r.status_code} {r.text[:200]}")
                continue
            put_secret(name, r.json()["access_token"])
            print(f"{name}: refreshed, expires in {r.json().get('expires_in')}s")


if __name__ == "__main__":
    main()
