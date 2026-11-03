"""주문 리포트 PDF 빌더 (도아도령).

usage:
  python reports/build_report.py <spec.json> <out.pdf>

spec.json 형식은 reports/README.md "spec 형식" 참고. 예시: reports/example_spec.json (가상 인물).
※ 손님 spec·PDF는 저장소에 두지 말고 스크래치패드(임시 폴더)에서 만든다 — 저장소는 공개다.
"""
import html
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

TPL = Path(__file__).parent / "template"
DISCLAIMER = ("이 리포트는 전통 사주명리학의 틀을 바탕으로 AI가 해석하고 구성한 참고용 엔터테인먼트 콘텐츠입니다. "
              "실제 미래를 예측하거나 특정 결과를 보장하지 않습니다. 건강·재정·법률·진로처럼 삶에 중요한 결정은 반드시 "
              "해당 분야 전문가와 상의해 주세요. 힘든 시기에는 혼자 견디지 마시고 가까운 사람이나 전문 상담 기관의 도움을 "
              "받으시기를 권합니다. 보내 주신 정보는 리포트 제작과 발송에만 사용되며, 발송 후 3일 안에 삭제됩니다.")
MBTI_NOTE = "※ 사주 기질을 MBTI 축에 비춰 보는 방식은 도아도령의 해석 틀이며, 전통 명리나 공식 MBTI 검사가 아니에요."


def card(c):
    return (f'<div class="sc"><div class="q"><i>{c.get("n", "")}</i>{c["q"]}</div>'
            f'<div class="why"><b>{c.get("lab1", "사주")}</b><span>{c["saju"]}</span></div>'
            f'<div class="why"><b>{c.get("lab2", "MBTI")}</b><span>{c["mbti"]}</span></div>'
            f'<div class="tip">→ {c["tip"]}</div></div>')


def pillars_table(p):
    """p: {"hour":"戊辰","day":"己亥","month":"甲戌","year":"己卯"} (hour 없으면 null)"""
    cols = [p.get("hour"), p["day"], p["month"], p["year"]]
    st = "".join(f'<td class="serif"{" style=\"color:var(--gold)\"" if i == 1 else ""}><b>{c[0] if c else "-"}</b></td>' for i, c in enumerate(cols))
    br = "".join(f'<td class="serif"><b>{c[1] if c else "-"}</b></td>' for c in cols)
    return (f'<table><tr><th></th><th>시</th><th>일 (나)</th><th>월</th><th>년</th></tr>'
            f'<tr><th>천간</th>{st}</tr><tr><th>지지</th>{br}</tr></table>')


def block(b):
    t = b.get("type", "html")
    if t == "html":
        return b["html"]
    if t == "p":
        return f'<p>{b["text"]}</p>'
    if t == "h3":
        return f'<h3>{b["text"]}</h3>'
    if t == "small":
        return f'<p class="small">{b["text"]}</p>'
    if t == "pair":
        return '<div class="pair">' + "".join(
            f'<div><div class="k">{x["k"]}</div><div class="v">{x["v"]}</div><div class="small">{x.get("s", "")}</div></div>'
            for x in b["items"]) + "</div>"
    if t == "pillars":
        return pillars_table(b["pillars"])
    if t == "summary":
        return '<div class="summary">' + "".join(
            f'<div class="row"><span class="k">{k}</span><span{" class=\"hl\"" if i == 0 and b.get("first_hl", True) else ""}>{v}</span></div>'
            for i, (k, v) in enumerate(b["rows"])) + "</div>"
    if t == "cards":
        inner = "".join(card(c) for c in b["cards"]) + (f'<p class="small">{MBTI_NOTE}</p>' if b.get("note") else "")
        return f'<div class="fire">{inner}</div>' if b.get("fire", True) else inner
    if t == "table":
        head = "".join(f'<th{" class=\"l\"" if i == len(b["head"]) - 1 else ""}>{h}</th>' for i, h in enumerate(b["head"]))
        rows = ""
        for r in b["rows"]:
            hl = r[0] == "*"
            cells = r[1:] if hl else r
            rows += (f'<tr{" style=\"background:#fff6df\"" if hl else ""}>' +
                     "".join(f'<td class="{"l" if i == len(cells) - 1 else "serif" if i == 1 else ""}">{c}</td>' for i, c in enumerate(cells)) + "</tr>")
        return f'<table style="font-size:{b.get("size", "9.6pt")}"><tr>{head}</tr>{rows}</table>'
    if t == "qa":
        return f'<div class="ex" style="margin-top:4mm;font-size:9.8pt"><b>Q.</b> {b["q"]}<br><br>{b["a"]}</div>'
    if t == "check":
        return f'<div class="check" style="margin-top:4mm"><div class="t">✦ {b["title"]}</div>{b["text"]}</div>'
    raise ValueError(f"unknown block type {t}")


def build_html(s):
    name, run = s["name"], s["run"]
    c = s["cover"]
    pages = [f'''<section class="page cover">
  <div class="fr"></div><div class="fr2"></div><div class="moon"></div><div class="ph"></div>
  <div class="ttl"><div class="k">{c["kicker"]}</div><div class="m">{c["title"]}</div><div class="s">{c["sub"]}</div></div>
  <div class="who"><div class="n">{name}의 사주</div><div class="d">{c["birth"]}</div></div>
  <div class="brand">도아도령</div>
  <div class="foot">작성일 {s["date"]} · 참고와 재미로 보는 콘텐츠예요</div>
</section>''']
    n = 0
    if s.get("toc"):
        pages.append("@TOC@")
    for pg in s["pages"]:
        n += 1
        body = "".join(block(b) for b in pg["blocks"])
        pages.append(f'<section class="page inner"><div class="runhead"><span>{run}</span><span>{name}</span></div>'
                     f'<div class="num">{n:02d}</div><h2>{pg["title"]}</h2><div class="rule"></div>{body}</section>')
    n += 1
    paras = "".join(f"<p>{x}</p>" for x in s["closing"])
    pages.append(f'''<section class="page closing">
  <div class="runhead" style="color:#9aa0b8"><span>{run}</span><span>{name}</span></div>
  <div style="padding-top:8mm"><div class="num">{n:02d}</div><h2>마무리 메시지</h2><div class="rule"></div></div>
  {paras}
  <div style="text-align:center;margin:14mm 0 4mm"><div style="display:inline-block;width:40mm;height:40mm;border-radius:50%;background:url(cover.jpg) center/cover;box-shadow:0 0 0 1mm #e8b54f,0 0 14mm rgba(232,181,79,.4)"></div>
  <div class="serif" style="color:#e8b54f;font-size:13pt;letter-spacing:4px;margin-top:5mm">도아도령</div></div>
  <div class="disc">{DISCLAIMER}</div>
</section>''')
    if s.get("toc"):
        items = "".join(f'<li><span><b>{i:02d}</b>{p["title"]}</span><span>{i + 2}</span></li>' for i, p in enumerate(s["pages"], 1))
        items += f'<li><span><b>{n:02d}</b>마무리 메시지</span><span>{n + 2}</span></li>'
        pages[1] = (f'<section class="page inner"><div class="runhead"><span>{run}</span><span>{name}</span></div>'
                    f'<div class="num">CONTENTS</div><h2>목차</h2><div class="rule"></div><ul class="toc{" tight" if n > 12 else ""}">{items}</ul></section>')
    out = []
    for i, p in enumerate(pages, 1):
        if i > 1:
            col = ' style="color:#9aa0b8"' if "page closing" in p[:40] else ""
            p = p.replace("</section>", f'<div class="pno"{col}>{i}</div></section>')
        out.append(p)
    css = (TPL / "style.css").read_text(encoding="utf-8")
    return ('<!doctype html><html lang="ko"><head><meta charset="utf-8"><link rel="stylesheet" href="fonts.css">'
            f"<style>{css}</style></head><body>" + "\n".join(out) + "</body></html>")


def main():
    spec, out = Path(sys.argv[1]), Path(sys.argv[2])
    s = json.loads(spec.read_text(encoding="utf-8"))
    from playwright.sync_api import sync_playwright
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for f in ("fonts.css", "cover.jpg"):
            shutil.copy(TPL / f, tmp / f)
        shutil.copytree(TPL / "fonts", tmp / "fonts")
        (tmp / "r.html").write_text(build_html(s), encoding="utf-8")
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 794, "height": 1123})
            pg.goto((tmp / "r.html").as_uri())
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(1500)
            over = pg.evaluate("""Array.from(document.querySelectorAll('.page')).map((p,i)=>{const r=p.getBoundingClientRect();let m=0;
              p.querySelectorAll('*').forEach(e=>{if(e.closest('.pno')||e.closest('.runhead')||e.classList.contains('fr')||e.classList.contains('fr2'))return;
              const s=getComputedStyle(e);if(s.position==='absolute'&&!e.closest('.cover'))return;const b=e.getBoundingClientRect();if(b.height>0)m=Math.max(m,b.bottom-r.top)});
              return [i+1,Math.round(m)]}).filter(x=>x[1]>1080)""")
            pg.pdf(path=str(out), format="A4", print_background=True, prefer_css_page_size=True)
            npages = pg.evaluate("document.querySelectorAll('.page').length")
            b.close()
    print(f"ok {out} pages={npages}")
    if over:
        print("WARN 넘친 페이지(글을 줄이거나 나눌 것):", over)


if __name__ == "__main__":
    main()
