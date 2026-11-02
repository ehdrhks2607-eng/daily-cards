"""오늘(또는 지정 날짜)의 간지 계산 — 사주 글에서 일진·년주를 지어내지 않기 위한 도구.

usage: python scripts/ganji.py            # 오늘(KST)
       python scripts/ganji.py 2027-02-04

- 일주(일진): 율리우스일 기반 60갑자 계산, 날짜만 맞으면 정확함 (기준: 2000-01-01 = 戊午일)
- 년주: 입춘(양력 2월 4일 전후) 기준. 2월 3~5일은 경계라 "입춘 확인 필요"로 표시
- 월주는 절기 시각이 필요해 계산하지 않음 (글에서 월주를 단정하지 않는다)
"""
import sys
from datetime import date, datetime, timedelta, timezone

STEMS = "甲乙丙丁戊己庚辛壬癸"
STEMS_KO = "갑을병정무기경신임계"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
BRANCHES_KO = "자축인묘진사오미신유술해"
ANIMALS = ["쥐", "소", "범", "토끼", "용", "뱀", "말", "양", "원숭이", "닭", "개", "돼지"]
ELEM = {"甲": "목", "乙": "목", "丙": "화", "丁": "화", "戊": "토", "己": "토", "庚": "금", "辛": "금", "壬": "수", "癸": "수"}


def pillar(i):
    s, b = STEMS[i % 10], BRANCHES[i % 12]
    return f"{s}{b}", f"{STEMS_KO[i % 10]}{BRANCHES_KO[i % 12]}", s, ANIMALS[i % 12]


def day_pillar(d):
    jdn = d.toordinal() + 1721425  # proleptic Gregorian ordinal -> Julian Day Number
    return pillar((jdn + 49) % 60)


def year_pillar(d):
    y = d.year if (d.month, d.day) >= (2, 4) else d.year - 1
    return pillar((y - 4) % 60), (d.month == 2 and 3 <= d.day <= 5)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        d = date.fromisoformat(sys.argv[1])
    else:
        d = datetime.now(timezone(timedelta(hours=9))).date()
    (dh, dk, ds, da) = day_pillar(d)
    (yh, yk, ys, ya), edge = year_pillar(d)
    print(f"날짜: {d.isoformat()}")
    print(f"일진: {dh}({dk})일 — 천간 {ds}({ELEM[ds]}), {da}날")
    print(f"년주: {yh}({yk})년 — {ya}띠 해" + (" ※입춘 경계, 시각 확인 필요" if edge else ""))
