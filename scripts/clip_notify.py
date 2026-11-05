"""도아도령 네이버 클립 업로드 알림 (ntfy 푸시).

릴스 게시 시간(config.json seoul reel_am/reel/reel_pm, 평일·주말)에 맞춰
"클립 올릴 시간" 알림을 폰(ntfy 앱)으로 보낸다. 토픽 이름은 GitHub Secret NTFY_TOPIC.
FORCE=1 이면 시간과 상관없이 테스트 알림을 보낸다.
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
PAGE = "https://ehdrhks2607-eng.github.io/daily-cards/clip.html"
NAMES = {"reel_am": ("💰 금전운", "seoul_reel_am"), "reel": ("💕 연애·재회운", "seoul_reel"), "reel_pm": ("🔮 내일의 운세", "seoul_reel_pm")}

topic = (os.environ.get("NTFY_TOPIC") or "").strip()
if not topic:
    print("NTFY_TOPIC secret not set — skip"); sys.exit(0)

now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
times = cfg["accounts"]["seoul"]["publish_time_kst"]["weekend" if now.weekday() >= 5 else "weekday"]

slot = None
if os.environ.get("FORCE") == "1":
    slot = "reel_am"
else:
    for s in NAMES:
        h, m = map(int, times[s].split(":"))
        t = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if -10 <= (now - t).total_seconds() / 60 <= 50:  # GitHub cron은 늦게 돌 수 있어 여유를 둔다
            slot = s
            break
if not slot:
    print("not a clip time", now.isoformat()); sys.exit(0)

name, folder = NAMES[slot]
date = now.strftime("%Y-%m-%d")
title = f"{name} 클립·당근 스토리 올릴 시간이에요 🌙"
msg = f"{date} {name} 영상이 인스타에 올라갔어요.\n눌러서 영상 저장 → 네이버 클립 · 당근 스토리에 문구·댓글 붙여넣기"
if os.environ.get("FORCE") == "1":
    title = "🔔 테스트 알림 — 도아도령 클립"
r = requests.post(f"https://ntfy.sh/{topic}", data=msg.encode("utf-8"), timeout=20,
                  headers={"Title": title.encode("utf-8"), "Click": f"{PAGE}#{folder}", "Tags": "crescent_moon", "Priority": "default"})
print(r.status_code, slot)
r.raise_for_status()
