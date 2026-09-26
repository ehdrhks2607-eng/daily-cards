"""Fill publish_at in post.json from config.json (weekday / weekend times, KST).

usage: python scripts/schedule.py posts/2026-09-27/jak/post.json [...]
The post's "date" field decides the day; Sat/Sun use the weekend time.
"""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))


def publish_at(acc, day):
    d = date.fromisoformat(day)
    times = CFG["accounts"][acc]["publish_time_kst"]
    hm = times["weekend"] if d.weekday() >= 5 else times["weekday"]
    return f"{day}T{hm}:00+09:00"


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        p = Path(arg)
        post = json.loads(p.read_text(encoding="utf-8"))
        post["publish_at"] = publish_at(post["account"], post["date"])
        p.write_text(json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8")
        wd = "월화수목금토일"[date.fromisoformat(post["date"]).weekday()]
        print(p.parent, "->", post["publish_at"], f"({wd})")
