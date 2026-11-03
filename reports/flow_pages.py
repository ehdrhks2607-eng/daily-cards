"""flow_table 결과로 리포트 페이지(spec의 pages 항목)를 만드는 도우미.

from flow_pages import period_pages, year_overview_page, year_detail_pages
  rows  = flow_table.calendar_months(2027, day, natal, mbti)
  notes = {"辛丑": ("준비", "한 줄 요약"), ...}   # 달마다 태그·요약 (손님에 맞게 직접 쓴다)
  tips  = {"1/5": "다듬은 MBTI 문장", ...}       # (선택) 기간 시작일별 MBTI 문장 덮어쓰기
  pages += period_pages(rows, notes, mbti="ISFP", highlight={"壬寅"}, prefix="PART 4")
"""
import flow_table as ft

STYLE = '<style>.yt td,.yt th{padding:.9mm 2mm;line-height:1.32}</style>'


def _md(x):  # "03/06" -> "3/6"
    return f"{int(x[:2])}/{int(x[3:])}"


def _strip(t, mbti):
    return (t or "").replace(f"{mbti}라면: ", "") if mbti else ""


def period_pages(rows, notes, mbti=None, highlight=(), prefix="PART 4", year=2027, tips=None, per_page=2):
    tips = tips or {}
    pages = []
    for i in range(0, len(rows), per_page):
        grp = rows[i:i + per_page]
        body = ""
        for m in grp:
            tag, note = notes.get(m["month_pillar"], ("", m["draft"]))
            s, e = m["range"].split("~")
            col = "#fff6df" if m["month_pillar"] in highlight else "#f1e8d3"
            body += (f'<tr style="background:{col}"><td colspan="3" class="l" style="padding:2mm 3mm">'
                     f'<b style="color:var(--navy)">{int(s[:2])}월 {int(s[3:])}일 ~ {int(e[:2])}월 {int(e[3:])}일</b> &nbsp;'
                     f'<span class="serif"><b>{m["month_pillar"]}월</b></span>'
                     + (f' <span class="tag t-go" style="margin-left:2mm">{tag}</span>' if tag else "")
                     + f'<br><span style="font-size:9pt">{note}</span></td></tr>')
            for p in m["periods"]:
                lab = f'{_md(p["from"][5:])} ~ {_md(p["to"][5:])}'
                k, tip = p["draft"].split(" · ")
                mb = tips.get(_md(p["from"][5:]), _strip(p.get("mbti"), mbti))
                mline = f'<br><span style="color:#2b3466;font-size:8.6pt">🧠 <b>{mbti}</b> 방식: {mb}</span>' if mbti and mb else ""
                body += (f'<tr><td style="width:22%">{lab}</td><td style="width:30%"><span class="serif">{p["stem"]}</span> {p["god"]}'
                         f'<br><span class="small">{k}</span></td><td class="l">{tip}{mline}</td></tr>')
        head = "이렇게 풀어 보세요 (사주 → MBTI)" if mbti else "이렇게 해 보세요"
        html = ('<p class="small">※ <b>사주</b>로 그 기간에 어떤 기운이 오는지 보고'
                + (', <b>MBTI</b>로 그 기운을 어떻게 풀어 가면 편한지 함께 적었어요.' if mbti else ' 정리했어요.')
                + ' 한 달 안에서도 기운을 맡는 글자(사령)가 바뀌어 기간별로 나눴어요(날짜 ±1일).</p>'
                f'<table style="font-size:8.8pt"><tr><th>기간</th><th>사주: 이 기간의 기운</th><th class="l">{head}</th></tr>{body}</table>')
        a, b = int(grp[0]["start"][5:7]), int(grp[-1]["start"][5:7])
        pages.append({"title": f"{prefix} · {year} 기간별 흐름 ({a}월~{b}월)", "blocks": [{"type": "html", "html": html}]})
    return pages


def year_overview_page(ys, daeun_of, intro, summary, prefix="PART 6", highlight=()):
    """ys = flow_table.years(...), daeun_of(year)->'丁丑' """
    tr = ""
    for y in ys:
        rel = [x for x in y["relations"] if x["day"]] or y["relations"]
        reltxt = f'<br><span class="small">{rel[0]["with"]}와 {rel[0]["rel"]} — {rel[0]["text"]}</span>' if rel else ""
        hl = ' style="background:#fff6df"' if y["year"] in highlight else ""
        tr += (f'<tr{hl}><td><b>{y["year"]}</b></td><td class="serif">{y["pillar"]}<br><span class="small">{daeun_of(y["year"])} 대운</span></td>'
               f'<td class="l">{ft.GOD[y["stem_god"]][0]} ({y["stem_god"]}){reltxt}</td>'
               f'<td>{"<br>".join(y["best_months"])}</td><td>{"<br>".join(y["care_months"])}</td></tr>')
    html = (STYLE + f'<p>{intro}</p>'
            '<table class="yt" style="font-size:8.4pt"><tr><th style="width:11%">연도</th><th style="width:14%">세운</th><th class="l">그해의 기운</th>'
            '<th style="width:15%">힘 받는 달</th><th style="width:15%">쉬어갈 달</th></tr>' + tr + "</table>"
            f'<div class="check" style="margin-top:3mm"><div class="t">✦ 10년 흐름 한 줄</div>{summary}</div>'
            '<p class="small" style="margin-top:2mm">※ 힘 받는 달·쉬어갈 달은 그해 월건과 원국의 합·충과 십성을 바탕으로 고른 참고용이에요. 중요한 결정은 전문가와 상의해 주세요.</p>')
    return {"title": f"{prefix} · 앞으로 10년 한눈에 (세운)", "blocks": [{"type": "html", "html": html}]}


def year_detail_pages(ys, daeun_of, name="고객님", mbti=None, prefix="PART 6", extra=None):
    """extra: {연도: '손님에 맞춘 한 줄'} — 머리 박스 끝에 붙는다."""
    extra = extra or {}
    pages = []
    for i in range(0, len(ys), 2):
        html = ""
        for y in ys[i:i + 2]:
            g1, g2 = ft.GOD[y["stem_god"]], ft.GOD[y["branch_god"]]
            rel = "".join(f"<br>· {x['with']}와 <b>{x['rel']}</b> — {x['text']}" for x in y["relations"][:3]) \
                or "<br>· 원국과 크게 부딪히거나 묶이는 글자가 없어 <b>흐름이 비교적 고른 해</b>예요."
            mline = f'<br><span style="color:#2b3466">🧠 <b>{mbti}</b> 방식으로 풀면: {_strip(y.get("mbti"), mbti)}</span>' if mbti else ""
            ex = f'<br>{extra[y["year"]]}' if y["year"] in extra else ""
            html += (f'<div class="ex" style="margin:1.5mm 0 1mm;font-size:8.8pt;line-height:1.55"><b style="font-size:12pt;color:var(--navy)">{y["year"]}년 · '
                     f'<span class="serif">{y["pillar"]}</span>년</b> <span class="small">({daeun_of(y["year"])} 대운)</span> &nbsp;'
                     f'<span class="hl">{g1[0]}이 중심이 되는 해</span><br>천간 <span class="serif">{y["pillar"][0]}</span>은 {name}에게 '
                     f'<b>{y["stem_god"]}</b>({g1[0]}), 지지 <span class="serif">{y["pillar"][1]}</span>은 <b>{y["branch_god"]}</b>({g2[0]})예요.{rel}{ex}{mline}</div>')
            tr = ""
            for kind, lst, col in (("힘 받는 달", y["best_detail"], "#fff6df"), ("쉬어갈 달", y["care_detail"], "#eef0f7")):
                for d in lst:
                    a, z = d["range"].split("~")
                    mb = f'<br><span style="color:#2b3466;font-size:8pt">🧠 {_strip(d.get("mbti"), mbti)}</span>' if mbti else ""
                    tr += (f'<tr style="background:{col}"><td style="width:15%"><b>{kind}</b><br>{d["month"]} <span class="serif">{d["pillar"]}</span><br>'
                           f'<span class="small">{_md(a)}~{_md(z)}</span></td>'
                           f'<td class="l" style="font-size:7.9pt">{"<br>".join("· " + w for w in d["why"][:3])}</td>'
                           f'<td class="l" style="width:30%">{d["tip"]}{mb}</td></tr>')
            head = f"이렇게 풀어 보세요 (사주 → {mbti})" if mbti else "이렇게 해 보세요"
            html += (f'<table class="yt" style="font-size:8.5pt;margin:0 0 2mm"><tr><th>달</th><th class="l">왜 그런가요 (근거)</th><th class="l">{head}</th></tr>{tr}</table>')
        pages.append({"title": f"{prefix} · 연도별 흐름 {ys[i]['year']}–{ys[min(i + 1, len(ys) - 1)]['year']}",
                      "blocks": [{"type": "html", "html": STYLE + html}]})
    return pages
