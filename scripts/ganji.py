"""오늘(또는 지정 날짜)의 간지 + 12띠 운세 점수 — 사주 글에서 간지·순위를 지어내지 않기 위한 도구.

usage: python scripts/ganji.py               # 오늘(KST)
       python scripts/ganji.py 2027-02-04
       python scripts/ganji.py --json        # 다른 스크립트/자동 글 작성용

- 일주(일진): 율리우스일 기반 60갑자 계산 (기준: 2000-01-01 = 戊午일)
- 년주: 입춘(양력 2월 4일 전후) 기준. 2월 3~5일은 경계라 "입춘 확인 필요"로 표시
- 월주는 절기 시각이 필요해 계산하지 않음
- 12띠 점수(1~5, 참고·재미용): 오늘 일지(日支)와 각 띠 지지의 관계로 매긴다
    공통: 육합 5 / 삼합 4 / 같은 띠 3 / 특별한 관계 없음 3 / 육해 2 / 충 1
    금전운: 띠 오행이 오늘 천간 오행을 극하면(재성) +1
    연애운: 띠 오행이 오늘 천간 오행을 생하면(식상·표현과 매력) +1, 오늘 일지가 그 띠의 도화면 +1
    재회운: 오늘 천간 오행이 띠 오행을 생하면(인성·돌아오는 기운) +1, 육합이면 +1
    연애·재회운: 연애운·재회운 가점(식상·도화·인성·육합) 중 하나라도 있으면 +1
    종합운(내일의 운세용): 재성·식상·인성 중 하나라도 있으면 +1
    (최대 5, 최소 1)
"""
import json
import sys
from datetime import date, datetime, timedelta, timezone

STEMS = "甲乙丙丁戊己庚辛壬癸"
STEMS_KO = "갑을병정무기경신임계"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
BRANCHES_KO = "자축인묘진사오미신유술해"
ANIMALS = ["쥐", "소", "범", "토끼", "용", "뱀", "말", "양", "원숭이", "닭", "개", "돼지"]
STEM_EL = ["목", "목", "화", "화", "토", "토", "금", "금", "수", "수"]
BRANCH_EL = ["수", "토", "목", "목", "토", "화", "화", "토", "금", "금", "토", "수"]
CONTROLS = {"목": "토", "토": "수", "수": "화", "화": "금", "금": "목"}  # A 극 B
GENERATES = {"목": "화", "화": "토", "토": "금", "금": "수", "수": "목"}  # A 생 B
YUKHAP = {frozenset(p) for p in [(0, 1), (2, 11), (3, 10), (4, 9), (5, 8), (6, 7)]}
SAMHAP = [{8, 0, 4}, {11, 3, 7}, {2, 6, 10}, {5, 9, 1}]
YUKHAE = {frozenset(p) for p in [(0, 7), (1, 6), (2, 5), (3, 4), (8, 11), (9, 10)]}
DOHWA = {8: 9, 0: 9, 4: 9, 2: 3, 6: 3, 10: 3, 5: 6, 9: 6, 1: 6, 11: 0, 3: 0, 7: 0}


def pillar(i):
    return dict(hanja=STEMS[i % 10] + BRANCHES[i % 12], ko=STEMS_KO[i % 10] + BRANCHES_KO[i % 12],
                stem=i % 10, branch=i % 12, animal=ANIMALS[i % 12])


def day_pillar(d):
    return pillar((d.toordinal() + 1721425 + 49) % 60)


def year_pillar(d):
    y = d.year if (d.month, d.day) >= (2, 4) else d.year - 1
    return pillar((y - 4) % 60), (d.month == 2 and 3 <= d.day <= 5)


def relation(day_b, b):
    if b == day_b:
        return 3, "같은 띠(비견)"
    if frozenset((day_b, b)) in YUKHAP:
        return 5, "육합"
    if any(day_b in g and b in g for g in SAMHAP):
        return 4, "삼합"
    if (day_b - b) % 12 == 6:
        return 1, "충"
    if frozenset((day_b, b)) in YUKHAE:
        return 2, "육해"
    return 3, "평이"


def fortunes(d):
    dp = day_pillar(d)
    day_el = STEM_EL[dp["stem"]]
    out = {"금전운": [], "연애운": [], "재회운": [], "연애·재회운": [], "종합운": []}
    for b in range(12):
        base, why = relation(dp["branch"], b)
        for kind in out:
            s, notes = base, [why]
            if kind == "금전운" and CONTROLS[BRANCH_EL[b]] == day_el:
                s += 1; notes.append("재성(띠 오행이 오늘 천간을 극)")
            if kind == "연애운" and GENERATES[BRANCH_EL[b]] == day_el:
                s += 1; notes.append("식상(표현·매력)")
            if kind == "연애운" and DOHWA[b] == dp["branch"]:
                s += 1; notes.append("도화")
            if kind == "재회운" and GENERATES[day_el] == BRANCH_EL[b]:
                s += 1; notes.append("인성(돌아오는 기운)")
            if kind == "재회운" and why == "육합":
                s += 1; notes.append("합(다시 묶이는 기운)")
            if kind == "연애·재회운":
                if GENERATES[BRANCH_EL[b]] == day_el: notes.append("식상(표현·매력)")
                if DOHWA[b] == dp["branch"]: notes.append("도화")
                if GENERATES[day_el] == BRANCH_EL[b]: notes.append("인성(돌아오는 기운)")
                if len(notes) > 1 or why == "육합": s += 1
            if kind == "종합운":
                if CONTROLS[BRANCH_EL[b]] == day_el: notes.append("재성")
                if GENERATES[BRANCH_EL[b]] == day_el: notes.append("식상")
                if GENERATES[day_el] == BRANCH_EL[b]: notes.append("인성")
                if len(notes) > 1: s += 1
            out[kind].append(dict(animal=ANIMALS[b] + "띠", score=max(1, min(5, s)), basis=" + ".join(notes), order=b))
    for kind in out:  # 같은 점수면 일지와의 거리 순 → 매일 순서가 달라짐
        out[kind].sort(key=lambda x: (-x["score"], (x["order"] - dp["branch"]) % 12))
    return dp, out


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    d = date.fromisoformat(args[0]) if args else datetime.now(timezone(timedelta(hours=9))).date()
    dp, f = fortunes(d)
    yp, edge = year_pillar(d)
    if "--json" in sys.argv:
        print(json.dumps(dict(date=d.isoformat(), day=dp, year=yp, year_edge=edge, fortunes=f), ensure_ascii=False, indent=1))
        sys.exit()
    wd = "월화수목금토일"[d.weekday()]
    print(f"날짜: {d.isoformat()} ({wd})")
    print(f"일진: {dp['hanja']}({dp['ko']})일 — 천간 {STEMS[dp['stem']]}({STEM_EL[dp['stem']]}), 일지 {BRANCHES[dp['branch']]}({dp['animal']})")
    print(f"년주: {yp['hanja']}({yp['ko']})년 — {yp['animal']}띠 해" + (" ※입춘 경계, 시각 확인 필요" if edge else ""))
    for kind, rows in f.items():
        print(f"\n[{kind}]")
        for r in rows:
            print(f"  {'★' * r['score']:<5} {r['animal']:<5} ({r['basis']})")
