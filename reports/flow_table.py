"""월별·기간별(월률분야) 흐름과 연도별(세운) 흐름 계산기 — 신년운·인생사주 리포트용.

usage:
  python reports/flow_table.py --day 辛巳 --natal 壬申,壬子,辛巳,戊戌 --months 2027 [--json]
  python reports/flow_table.py --day 辛巳 --natal 壬申,壬子,辛巳,戊戌 --years 2026 10 [--json]

- 사주의 달은 절기(입춘·경칩…)에 시작한다. 한 달을 지장간이 맡는 기간(월률분야 사령)으로 나눠
  "2월 4일~2월 10일: ○○ 기운"처럼 날짜 구간을 만든다. (사령 일수는 일반적인 월률분야표 기준, 날짜는 ±1일 오차)
- 각 구간·달·해의 간지에 대해 십성(일간 기준)과 원국 지지와의 합·충·형·해를 붙이고, 초안 문장(draft)을 준다.
  draft는 뼈대일 뿐이다. 리포트에는 손님 사주·고민에 맞게 다듬어 쓴다(단정·공포·결정 유도 금지).
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from saju_pillars import (BRANCHES, CHONG, HAI, LIUHE, STEMS, XING, month_index, term_time, ten_god)  # noqa: E402

KST = dt.timezone(dt.timedelta(hours=9))
# 월률분야 사령 (지지: [(천간, 일수), ...])
SARYEONG = {"寅": [("戊", 7), ("丙", 7), ("甲", 16)], "卯": [("甲", 10), ("乙", 20)], "辰": [("乙", 9), ("癸", 3), ("戊", 18)],
            "巳": [("戊", 7), ("庚", 7), ("丙", 16)], "午": [("丙", 10), ("己", 9), ("丁", 11)], "未": [("丁", 9), ("乙", 3), ("己", 18)],
            "申": [("戊", 7), ("壬", 7), ("庚", 16)], "酉": [("庚", 10), ("辛", 20)], "戌": [("辛", 9), ("丁", 3), ("戊", 18)],
            "亥": [("戊", 7), ("甲", 7), ("壬", 16)], "子": [("壬", 10), ("癸", 20)], "丑": [("癸", 9), ("辛", 3), ("己", 18)]}
GOD = {"비견": ("내 페이스로 다지는 기운", "혼자 정리·점검하기 좋아요"),
       "겁재": ("사람·경쟁·지출이 커지는 기운", "함께 쓰는 돈은 기록해 두세요"),
       "식신": ("손재주·꾸준한 결과물의 기운", "무언가 만들어 끝내기 좋아요"),
       "상관": ("말·표현이 강해지는 기운", "알리기 좋지만 말은 부드럽게"),
       "편재": ("움직이는 돈·기회의 기운", "새로운 것을 작게 시험해 보세요"),
       "정재": ("꾸준한 돈·성실의 기운", "정산·저축·고정비를 챙기세요"),
       "편관": ("책임·압박이 커지는 기운", "일정에 여유를 두세요"),
       "정관": ("인정·자리의 기운", "약속과 서류를 단정하게"),
       "편인": ("직감·공부의 기운", "혼자 배우고 정리하기 좋아요"),
       "정인": ("도움·문서의 기운", "조언을 구하고 서류를 챙기기 좋아요")}
# 십성 기운이 들어올 때 MBTI 축별로 어떻게 느끼고 쓰면 좋은지 (축, {극: 문장})
MBTI_AXIS = {
    "비견": (0, {"I": "혼자 정리하는 시간이 잘 맞는 때예요. 하루 30분 나만의 점검 시간을", "E": "혼자 하면 금방 지루해질 수 있어요. 함께 점검할 사람 한 명을"}),
    "겁재": (2, {"T": "손익은 정확히 따지되, 말은 한 번 부드럽게 다듬어서", "F": "정 때문에 지출·부탁을 거절하기 어려워요. 한도를 미리 정해 두세요"}),
    "식신": (3, {"J": "계획대로 하나씩 완성하기 좋아요. 체크리스트를 활용해 보세요", "P": "여러 개를 벌이기 쉬워요. 이번 기간엔 하나만 끝내기"}),
    "상관": (2, {"T": "정확한 말이 날카롭게 들릴 수 있어요. 좋은 점을 먼저 말하기", "F": "감정이 말에 실리기 쉬워요. 중요한 말은 하루 묵혔다 보내기"}),
    "편재": (1, {"S": "검증된 방법으로 작게 시도하면 잘 맞아요", "N": "아이디어가 넘쳐요. 하나만 골라 작게 실험해 보기"}),
    "정재": (3, {"J": "예산표·가계부가 잘 먹히는 때예요", "P": "기록이 귀찮다면 자동이체·자동저축으로 미리 묶어 두기"}),
    "편관": (3, {"J": "계획이 틀어지면 스트레스가 커요. 일정에 빈칸을 꼭 두세요", "P": "마감이 몰리면 미루기 쉬워요. 할 일을 10분 단위로 쪼개기"}),
    "정관": (0, {"E": "사람들 앞에서 보여 줄 기회를 적극적으로 잡아 보세요", "I": "말보다 결과물로 조용히 보여 주는 게 잘 통해요"}),
    "편인": (1, {"S": "실용적인 자격·기술을 배우기 좋은 때예요", "N": "깊이 파는 공부가 잘 맞아요. 배운 건 한 장 노트로 남기기"}),
    "정인": (0, {"E": "조언을 구하러 먼저 다가가 보세요", "I": "믿는 한 사람에게 물어보는 것으로 충분해요"}),
}
REL_MBTI = {"충": (0, {"I": "변화가 생기면 혼자 소화할 시간을 먼저 확보하세요", "E": "변화가 생기면 혼자 끙끙대지 말고 대화로 풀어 보세요"}),
            "형": (3, {"J": "서류·약속 재확인은 체크리스트로", "P": "서류·약속은 미루지 말고 그날 바로 확인"}),
            "육해": (2, {"T": "오해가 생기면 사실보다 마음을 먼저 물어보세요", "F": "서운함을 혼자 키우지 말고 짧게 말로 꺼내 보세요"})}


def mbti_tip(god, mbti, rel=None):
    """mbti: 'INTP' 같은 4글자. 없으면 None."""
    if not mbti or len(mbti) != 4:
        return None
    axis, d = REL_MBTI[rel] if rel in REL_MBTI else MBTI_AXIS[god]
    pole = mbti.upper()[axis]
    return f"{mbti.upper()}라면: {d[pole]}"


SLOT = {0: "년", 1: "월", 2: "일", 3: "시"}
REL_TXT = {"육합": "손을 잡아 부드러워져요", "충": "부딪혀 변화가 생기기 쉬워요(일정 여유)",
           "형": "마찰이 있어 서류·약속을 재확인", "육해": "작은 오해가 생기기 쉬워 말은 부드럽게"}


def rels(branch, natal):
    out = []
    for i, p in enumerate(natal):
        if not p:
            continue
        nb = p[1]
        for name, lst in (("육합", LIUHE), ("충", CHONG), ("형", XING), ("육해", HAI)):
            if (branch, nb) in lst or (nb, branch) in lst:
                out.append({"with": f"{SLOT[i]}지 {nb}", "rel": name, "text": REL_TXT[name], "day": i == 2})
    return out


def pillar_of(si, bi):
    return STEMS[si % 10] + BRANCHES[bi % 12]


def months(year, day, natal, mbti=None):
    ds = day[0]
    rows = []
    t = term_time(dt.datetime(year, 1, 25, tzinfo=dt.timezone.utc), True)  # 입춘 무렵
    while month_index(t + dt.timedelta(hours=1)) != 0:
        t = term_time(t + dt.timedelta(hours=1), True)
    ys = (year - 4) % 10
    for mi in range(12):
        start = t
        end = term_time(start + dt.timedelta(hours=1), True)
        ms, mb = ((ys % 5) * 2 + 2 + mi) % 10, (2 + mi) % 12
        mp = pillar_of(ms, mb)
        g_stem, g_br = ten_god(ds, mp[0]), ten_god(ds, {"子": "癸", "丑": "己", "寅": "甲", "卯": "乙", "辰": "戊", "巳": "丙", "午": "丁", "未": "己", "申": "庚", "酉": "辛", "戌": "戊", "亥": "壬"}[mp[1]])
        periods, cur = [], start.astimezone(KST).date()
        last = end.astimezone(KST).date() - dt.timedelta(days=1)  # 절입 당일은 다음 달로 본다
        segs = SARYEONG[mp[1]]
        for k, (stem, days) in enumerate(segs):
            pend = last if k == len(segs) - 1 else min(last, cur + dt.timedelta(days=days - 1))
            g = ten_god(ds, stem)
            periods.append({"from": cur.isoformat(), "to": pend.isoformat(), "label": f"{cur.month}/{cur.day}~{pend.month}/{pend.day}",
                            "stem": stem, "god": g, "draft": f"{GOD[g][0]} · {GOD[g][1]}", "mbti": mbti_tip(g, mbti)})
            cur = pend + dt.timedelta(days=1)
        r = rels(mp[1], natal)
        rows.append({"month_pillar": mp, "start": start.astimezone(KST).strftime("%Y-%m-%d %H:%M"),
                     "range": f"{start.astimezone(KST):%m/%d}~{last:%m/%d}", "stem_god": g_stem, "branch_god": g_br,
                     "relations": r, "periods": periods, "mbti": mbti_tip(g_stem, mbti),
                     "draft": f"{GOD[g_stem][0]}과 {GOD[g_br][0]}이 함께 들어오는 달" + "".join(f" · {x['with']}와 {x['rel']}: {x['text']}" for x in r)})
        t = end
    return rows


def calendar_months(year, day, natal, mbti=None):
    """양력 1월~12월 기준 12달: 1월은 전년(사주상) 丑월, 2~12월은 그해 寅~子월."""
    return months(year - 1, day, natal, mbti)[-1:] + months(year, day, natal, mbti)[:11]


def score(stem_god, br_rels):
    s = {"식신": 2, "정재": 2, "정관": 1, "정인": 1, "편재": 1, "상관": 0, "편인": 0, "비견": 0, "겁재": -1, "편관": -1}[stem_god]
    for x in br_rels:
        s += {"육합": 2, "충": -2, "형": -1, "육해": -1}[x["rel"]] * (2 if x["day"] else 1)
    return s


BR_MAIN = {"子": "癸", "丑": "己", "寅": "甲", "卯": "乙", "辰": "戊", "巳": "丙", "午": "丁", "未": "己", "申": "庚", "酉": "辛", "戌": "戊", "亥": "壬"}
REL_TIP = {"충": "큰 결정·이사·계약은 한 달 미루고 일정에 여유를 두세요",
           "형": "서류·계약·약속을 한 번 더 확인하세요",
           "육해": "서운한 말은 쌓지 말고 그날 부드럽게 풀어 주세요"}


def month_reason(m, good, mbti=None):
    """달 하나를 왜 힘 받는/쉬어갈 달로 골랐는지 근거와 팁."""
    p = m["month_pillar"]
    why = [f"천간 {p[0]} = {m['stem_god']}({GOD[m['stem_god']][0]})", f"지지 {p[1]} = {m['branch_god']}({GOD[m['branch_god']][0]})"]
    pos = [x for x in m["relations"] if x["rel"] == "육합"]
    neg = [x for x in m["relations"] if x["rel"] != "육합"]
    first, second, pre = (pos, neg, "다만 ") if good else (neg, pos, "그래도 ")
    why += [f"{x['with']}와 {x['rel']} — {x['text']}" for x in first]
    why += [f"{pre}{x['with']}와 {x['rel']} — {x['text']}" for x in second]
    if good:
        tip = GOD[m["stem_god"]][1]
    else:
        bad = [x for x in m["relations"] if x["rel"] in REL_TIP]
        tip = REL_TIP[bad[0]["rel"]] if bad else GOD[m["stem_god"]][1]
    rel = None if good else next((x["rel"] for x in m["relations"] if x["rel"] in REL_MBTI), None)
    return {"month": f"{int(m['start'][5:7])}월", "pillar": p, "range": m["range"], "why": why, "tip": tip,
            "mbti": mbti_tip(m["stem_god"], mbti, rel)}


def years(start, n, day, natal, mbti=None):
    ds = day[0]
    out = []
    for y in range(start, start + n):
        si, bi = (y - 4) % 10, (y - 4) % 12
        yp = pillar_of(si, bi)
        r = rels(yp[1], natal)
        mrows = months(y, day, natal, mbti)
        sc = [(score(m["stem_god"], m["relations"]), i) for i, m in enumerate(mrows)]
        best = [mrows[i] for _, i in sorted(sc, key=lambda x: (-x[0], x[1]))[:2]]
        care = [mrows[i] for _, i in sorted(sc, key=lambda x: (x[0], x[1]))[:2]]
        cal = lambda m: f"{int(m['start'][5:7])}월({m['month_pillar']})"
        g_stem = ten_god(ds, yp[0])
        g_br = ten_god(ds, BR_MAIN[yp[1]])
        out.append({"year": y, "pillar": yp, "stem_god": g_stem, "branch_god": g_br, "relations": r,
                    "best_detail": [month_reason(m, True, mbti) for m in best], "care_detail": [month_reason(m, False, mbti) for m in care],
                    "mbti": mbti_tip(g_stem, mbti),
                    "best_months": [cal(m) for m in best], "care_months": [cal(m) for m in care],
                    "draft": f"{GOD[g_stem][0]}이 중심이 되는 해" + "".join(f" · {x['with']}와 {x['rel']}: {x['text']}" for x in r)
                             + f" / 힘 받는 달 {', '.join(cal(m) for m in best)} · 쉬어갈 달 {', '.join(cal(m) for m in care)}"})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", required=True, help="일주, 예: 辛巳")
    ap.add_argument("--natal", required=True, help="년,월,일,시 주 (시 모르면 -) 예: 壬申,壬子,辛巳,戊戌")
    ap.add_argument("--months", type=int)
    ap.add_argument("--calendar", action="store_true", help="--months를 양력 1~12월 기준으로 (리포트는 이걸 쓴다)")
    ap.add_argument("--years", type=int, nargs=2, metavar=("START", "N"))
    ap.add_argument("--mbti", help="예: INTP — 기간·달·해마다 MBTI 맞춤 팁을 붙인다")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    natal = [None if x in ("-", "") else x for x in a.natal.split(",")]
    if a.months:
        rows = (calendar_months if a.calendar else months)(a.months, a.day, natal, a.mbti)
        if a.json:
            print(json.dumps(rows, ensure_ascii=False, indent=1))
        else:
            for m in rows:
                print(f"\n[{m['month_pillar']}] {m['range']} (절입 {m['start']}) 천간 {m['stem_god']} / 지지 {m['branch_god']}")
                print("  달:", m["draft"])
                for p in m["periods"]:
                    print(f"  {p['label']:13} {p['stem']} {p['god']}: {p['draft']}" + (f" | {p['mbti']}" if p['mbti'] else ""))
    if a.years:
        rows = years(a.years[0], a.years[1], a.day, natal, a.mbti)
        if a.json:
            print(json.dumps(rows, ensure_ascii=False, indent=1))
        else:
            for y in rows:
                print(f"{y['year']} {y['pillar']} {y['stem_god']}: {y['draft']}")


if __name__ == "__main__":
    main()
