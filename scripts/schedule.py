"""Fill publish_at in post.json from config.json (3 slots a day, weekday/weekend, KST).

usage: python scripts/schedule.py posts/2026-09-28/jak_am/post.json [...]
post.json needs "account", "date" and "slot" (am | lunch | pm; default lunch).
Sat/Sun use the weekend times. Instagram cards go only in the account's instagram_slot
(null = no instagram for that account).
"""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))


def publish_at(acc, day, slot):
    d = date.fromisoformat(day)
    times = CFG["accounts"][acc]["publish_time_kst"]
    table = times["weekend"] if d.weekday() >= 5 else times["weekday"]
    return f"{day}T{table[slot]}:00+09:00"


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        p = Path(arg)
        post = json.loads(p.read_text(encoding="utf-8"))
        slot = post.setdefault("slot", "lunch")
        post["publish_at"] = publish_at(post["account"], post["date"], slot)
        ig_slot = CFG["accounts"][post["account"]]["publish_time_kst"]["instagram_slot"]
        if ig_slot and slot != ig_slot and post.get("instagram", {}).get("images"):
            print(f"WARNING {p}: instagram cards in non-instagram slot ({slot}); expected {ig_slot}")
        p.write_text(json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8")
        wd = "월화수목금토일"[date.fromisoformat(post["date"]).weekday()]
        print(p.parent, "->", post["publish_at"], f"({wd}, {slot})")
