"""사주팔자(년·월·일·시주) + 오행·십성·합충·대운 계산기 (주문 리포트용).

usage:
  python scripts/saju_pillars.py 1999-10-14 08:52 --gender F
  python scripts/saju_pillars.py 1999-10-14 모름 --gender F --json
  python scripts/saju_pillars.py 1999-09-06 08:52 --gender F --lunar   # 음력 입력 (윤달이면 --leap)

- 월주는 절기(태양 황경) 기준으로 계산한다 (오차 약 15분 이내).
- 시주는 한국 표준시 30분 보정 기준(자시 23:30~01:30, 축시 01:30~03:30 …).
- 절기 경계 ±1일, 시 경계 ±20분, 23:30 이후 출생, 서머타임 시기 출생은 WARN을 출력한다 →
  사용자에게 만세력 앱으로 한 번 확인해 달라고 말한다.
"""
import argparse
import datetime as dt
import json
import math

STEMS = "甲乙丙丁戊己庚辛壬癸"
STEMS_KO = "갑을병정무기경신임계"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
BRANCHES_KO = "자축인묘진사오미신유술해"
ANIMALS = "쥐 소 범 토끼 용 뱀 말 양 원숭이 닭 개 돼지".split()
STEM_EL = "木木火火土土金金水水"
BR_EL = "水土木木土火火土金金土水"
EL_KO = {"木": "나무", "火": "불", "土": "흙", "金": "쇠", "水": "물"}
# 지장간 (여기·중기·정기), 마지막이 정기
HIDDEN = {"子": "壬癸", "丑": "癸辛己", "寅": "戊丙甲", "卯": "甲乙", "辰": "乙癸戊", "巳": "戊庚丙",
          "午": "丙己丁", "未": "丁乙己", "申": "戊壬庚", "酉": "庚辛", "戌": "辛丁戊", "亥": "戊甲壬"}
GEN = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CTRL = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
LIUHE = [("子", "丑"), ("寅", "亥"), ("卯", "戌"), ("辰", "酉"), ("巳", "申"), ("午", "未")]
CHONG = [("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"), ("辰", "戌"), ("巳", "亥")]
HAI = [("子", "未"), ("丑", "午"), ("寅", "巳"), ("卯", "辰"), ("申", "亥"), ("酉", "戌")]
SANHE = [("申子辰", "水"), ("亥卯未", "木"), ("寅午戌", "火"), ("巳酉丑", "金")]
STEM_HE = [("甲", "己", "土"), ("乙", "庚", "金"), ("丙", "辛", "水"), ("丁", "壬", "木"), ("戊", "癸", "火")]
XING = [("寅", "巳"), ("巳", "申"), ("丑", "戌"), ("戌", "未"), ("子", "卯")]
JIE = [(315, "입춘"), (345, "경칩"), (15, "청명"), (45, "입하"), (75, "망종"), (105, "소서"),
       (135, "입추"), (165, "백로"), (195, "한로"), (225, "입동"), (255, "대설"), (285, "소한")]


def jd(t):  # t: aware UTC datetime
    return t.timestamp() / 86400 + 2440587.5


def sun_lon(t):
    T = (jd(t) - 2451545.0) / 36525
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
    M = math.radians(357.52911 + 35999.05029 * T - 0.0001537 * T * T)
    C = ((1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M) + (0.019993 - 0.000101 * T) * math.sin(2 * M)
         + 0.000289 * math.sin(3 * M))
    om = math.radians(125.04 - 1934.136 * T)
    return (L0 + C - 0.00569 - 0.00478 * math.sin(om)) % 360


def month_index(t):  # 0 = 寅월 (입춘~경칩)
    return int(((sun_lon(t) - 315) % 360) // 30)


def term_time(t, forward):
    """t 이후(forward) 또는 이전의 가장 가까운 절(節) 시각."""
    mi = month_index(t)
    step = dt.timedelta(hours=6)
    s = t
    while month_index(s) == mi:
        s = s + step if forward else s - step
    a, b = (s - step, s) if forward else (s, s + step)
    for _ in range(40):
        m = a + (b - a) / 2
        if (month_index(m) == mi) == forward:
            a = m
        else:
            b = m
    return b if forward else a


def kst_offset(d):
    if dt.date(1954, 3, 21) <= d < dt.date(1961, 8, 10):
        return 8.5
    return 9.0


DST_YEARS = {1948, 1949, 1950, 1951, 1955, 1956, 1957, 1958, 1959, 1960, 1987, 1988}


def ten_god(day_stem, other_stem):
    de, oe = STEM_EL[STEMS.index(day_stem)], STEM_EL[STEMS.index(other_stem)]
    same = (STEMS.index(day_stem) % 2) == (STEMS.index(other_stem) % 2)
    if oe == de:
        return "비견" if same else "겁재"
    if GEN[de] == oe:
        return "식신" if same else "상관"
    if CTRL[de] == oe:
        return "편재" if same else "정재"
    if CTRL[oe] == de:
        return "편관" if same else "정관"
    return "편인" if same else "정인"


def pillar(si, bi):
    return {"hanja": STEMS[si] + BRANCHES[bi], "ko": STEMS_KO[si] + BRANCHES_KO[bi]}


def compute(date, time, gender, lunar=False, leap=False):
    warns = []
    if lunar:
        try:
            from korean_lunar_calendar import KoreanLunarCalendar
        except ImportError:
            raise SystemExit("음력 변환: pip install korean-lunar-calendar 후 다시 실행")
        c = KoreanLunarCalendar()
        c.setLunarDate(date.year, date.month, date.day, leap)
        date = dt.date.fromisoformat(c.SolarIsoFormat())
        warns.append(f"음력 → 양력 {date.isoformat()} 로 변환해서 계산함")
    no_time = time is None
    local = dt.datetime.combine(date, time or dt.time(12, 0))
    off = kst_offset(date)
    utc = (local - dt.timedelta(hours=off)).replace(tzinfo=dt.timezone.utc)
    if date.year in DST_YEARS:
        warns.append(f"{date.year}년은 서머타임이 있던 해 — 여름 출생이면 1시간 빼서 다시 확인")

    # 년주: 입춘 기준
    y = date.year
    ipchun = term_time(dt.datetime(y, 1, 20, tzinfo=dt.timezone.utc), True)  # 소한~입춘 구간 다음 절 = 입춘
    if month_index(dt.datetime(y, 1, 20, tzinfo=dt.timezone.utc)) != 11:
        ipchun = term_time(dt.datetime(y, 2, 1, tzinfo=dt.timezone.utc), True)
    if utc < ipchun:
        y -= 1
    ys, yb = (y - 4) % 10, (y - 4) % 12
    # 월주
    mi = month_index(utc)
    ms = ((ys % 5) * 2 + 2 + mi) % 10
    mb = (2 + mi) % 12
    prev_t, next_t = term_time(utc, False), term_time(utc, True)
    for name, tt in (("이전 절기", prev_t), ("다음 절기", next_t)):
        if abs((utc - tt).total_seconds()) < 86400 * 1.0:
            warns.append(f"절기 경계 근처 출생({name} {tt.astimezone(dt.timezone(dt.timedelta(hours=9))):%m-%d %H:%M}) — 월주 만세력 확인")
    # 일주 (현지 날짜 기준)
    di = (date.toordinal() + 1721425 + 49) % 60
    ds, db = di % 10, di % 12
    # 시주 (30분 보정)
    hour = None
    if not no_time:
        mins = local.hour * 60 + local.minute
        hb = ((mins + 30) // 120) % 12  # 23:30~01:29 → 子
        if mins >= 23 * 60 + 30:
            warns.append("23:30 이후 출생 — 야자시/조자시 해석이 갈림, 일주·시주 만세력 확인")
        edge = (mins + 30) % 120
        if edge < 20 or edge > 100:
            warns.append("시(時) 경계 ±20분 출생 — 시주 만세력 확인")
        hs = ((ds % 5) * 2 + hb) % 10
        hour = pillar(hs, hb)
    else:
        warns.append("태어난 시간 모름 — 시주 제외하고 해석, 리포트 앞에 '시주 제외' 명시")

    pillars = {"year": pillar(ys, yb), "month": pillar(ms, mb), "day": pillar(ds, db), "hour": hour}
    dstem = STEMS[ds]
    chars = [p["hanja"] for p in pillars.values() if p]
    stems = [c[0] for c in chars]
    brs = [c[1] for c in chars]
    count = {e: 0 for e in "木火土金水"}
    for s in stems:
        count[STEM_EL[STEMS.index(s)]] += 1
    for b in brs:
        count[BR_EL[BRANCHES.index(b)]] += 1
    gods = {}
    for k, p in pillars.items():
        if not p:
            continue
        s, b = p["hanja"]
        gods[k] = {"stem": "일간(나)" if k == "day" else ten_god(dstem, s),
                   "branch": ten_god(dstem, HIDDEN[b][-1]),
                   "hidden": [(h, ten_god(dstem, h)) for h in HIDDEN[b]]}
    rel = []
    labels = {"year": "년", "month": "월", "day": "일", "hour": "시"}
    keys = [k for k in pillars if pillars[k]]
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            x, y_ = pillars[a]["hanja"][1], pillars[b]["hanja"][1]
            sx, sy = pillars[a]["hanja"][0], pillars[b]["hanja"][0]
            tag = f"{labels[a]}-{labels[b]}"
            for name, lst in (("육합", LIUHE), ("충", CHONG), ("육해", HAI), ("형", XING)):
                if (x, y_) in lst or (y_, x) in lst:
                    rel.append(f"{tag} {x}{y_} {name}")
            for s1, s2, el in STEM_HE:
                if {sx, sy} == {s1, s2}:
                    rel.append(f"{tag} {sx}{sy} 천간합({el})")
    for grp, el in SANHE:
        hit = [c for c in grp if c in brs]
        if len(hit) >= 2:
            rel.append(f"{''.join(hit)} {'삼합' if len(hit) == 3 else '반합'}({el}) — 빠진 글자: {''.join(c for c in grp if c not in brs) or '없음'}")
    # 대운
    forward = (ys % 2 == 0) == (gender.upper() == "M")
    tt = next_t if forward else prev_t
    days = abs((tt - utc).total_seconds()) / 86400
    start = max(1, round(days / 3))
    daeun = []
    for n in range(1, 9):
        k = n if forward else -n
        daeun.append({"age": start + (n - 1) * 10, "pillar": pillar((ms + k) % 10, (mb + k) % 12)["hanja"]})
    return {
        "solar_date": date.isoformat(), "time": None if no_time else time.strftime("%H:%M"), "gender": gender,
        "pillars": pillars, "day_master": f"{dstem}{STEM_EL[ds]} ({EL_KO[STEM_EL[ds]]})",
        "animal": ANIMALS[yb] + "띠", "elements": count, "ten_gods": gods, "relations": rel,
        "daeun": {"direction": "순행" if forward else "역행", "start_age": start, "list": daeun},
        "warnings": warns,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("date")
    ap.add_argument("time", help="HH:MM (24h) 또는 '모름'")
    ap.add_argument("--gender", default="F", help="M/F (대운 방향)")
    ap.add_argument("--lunar", action="store_true")
    ap.add_argument("--leap", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    t = None if a.time in ("모름", "unknown", "-") else dt.time.fromisoformat(a.time)
    r = compute(dt.date.fromisoformat(a.date), t, a.gender, a.lunar, a.leap)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return
    p = r["pillars"]
    print("      시     일     월     년")
    print("     ", "   ".join((p[k]["hanja"] if p[k] else "--") for k in ("hour", "day", "month", "year")))
    print("일간:", r["day_master"], "/", r["animal"])
    print("오행:", " ".join(f"{EL_KO[e]}{n}" for e, n in r["elements"].items()))
    for k in ("year", "month", "day", "hour"):
        g = r["ten_gods"].get(k)
        if g:
            print(f"{k:5}: 천간 {g['stem']} / 지지 {g['branch']} / 지장간 " + " ".join(f"{h}{n}" for h, n in g["hidden"]))
    print("관계:", "; ".join(r["relations"]) or "없음")
    d = r["daeun"]
    print(f"대운: {d['direction']} {d['start_age']}세 시작 —", " ".join(f"{x['age']}{x['pillar']}" for x in d["list"]))
    for w in r["warnings"]:
        print("WARN:", w)


if __name__ == "__main__":
    main()
