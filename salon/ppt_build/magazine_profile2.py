# 프로필 페이지를 패션 잡지 인터뷰 스타일로 다시 짜기 (소개 문구 제거)
import json, re
M = "/tmp/claude-0/-home-user-daily-cards/06ef2264-b127-5a98-911e-16c520eb086c/scratchpad/mag/"

pj = json.load(open(M + "profile_bobae.json", encoding="utf-8"))
pj.pop("tagline", None); pj.pop("specialty", None)
pj["no"] = "01"
json.dump(pj, open(M + "profile_bobae.json", "w", encoding="utf-8"), ensure_ascii=False)

CSS = """/* ── 디자이너 프로필 (THE CAST 인터뷰) ── */
.prof { padding:0; }
.prof .hero { position:absolute; left:0; right:0; top:0; height:690px; background-size:cover; background-position:50% 12%;
  -webkit-mask-image:linear-gradient(to bottom, #000 62%, transparent 100%); mask-image:linear-gradient(to bottom, #000 62%, transparent 100%); }
.prof .run, .prof .folio { position:relative; z-index:2; margin:0 46px; }
.prof .art { position:relative; z-index:2; padding:0 46px; }
.prof .no { position:absolute; left:46px; top:84px; z-index:2; font-family:var(--display); font-size:150px; line-height:.8; color:rgba(139,108,132,.9); }
.prof .no small { display:block; font-family:var(--mono); font-size:11px; font-weight:600; letter-spacing:3px; color:var(--ink); margin-bottom:8px; }
.prof .quote { position:absolute; right:46px; top:150px; width:170px; z-index:2; text-align:right; }
.prof .quote .a { font-family:var(--title); font-size:42px; line-height:1.08; margin-top:8px; white-space:pre-line; }
.prof .quote .a::before { content:"“"; color:var(--mauve); } .prof .quote .a::after { content:"”"; color:var(--mauve); }
.prof .name { margin-top:468px; display:flex; align-items:flex-end; gap:18px; }
.prof .pnm { font-family:var(--title); font-size:150px; line-height:.86; letter-spacing:-4px; }
.prof .meta { padding-bottom:10px; }
.prof .meta .rl { display:block; font-size:20px; font-weight:800; }
.prof .meta .mb { display:block; font-family:var(--display); font-size:40px; color:var(--mauve); line-height:1; margin-top:4px; letter-spacing:1px; }
.prof .meta .kk { display:block; font-family:var(--mono); font-size:11px; font-weight:600; letter-spacing:3px; color:var(--graphite); margin-bottom:8px; }
.prof .iv { display:grid; grid-template-columns:1fr 1fr; gap:0 28px; margin-top:22px; padding-top:16px; border-top:3px solid var(--ink); }
.prof .iv .col + .col { border-left:1px solid var(--hair); padding-left:28px; }
.prof .iv h3 { font-family:var(--display); font-weight:400; font-size:22px; letter-spacing:.5px; margin-bottom:6px; }
.prof .qa { padding:10px 0 11px; border-bottom:1px solid var(--hair); }
.prof .qa:last-child { border-bottom:0; }
.prof .qa .q { font-family:var(--mono); font-size:11px; font-weight:600; letter-spacing:.5px; color:var(--mauve); display:flex; gap:7px; align-items:center; }
.prof .qa .q i { font-style:normal; font-family:var(--body); font-weight:900; color:var(--ink); font-size:13px; }
.prof .qa .a { font-size:16.5px; font-weight:800; line-height:1.4; margin-top:4px; white-space:pre-line; word-break:keep-all; }
"""

JS = r'''function profilePage(i){
  const d = data.designers[i], pr = d.profile, base = `designers.${i}.profile`;
  const qa = (path, q, a, mark) => `<div class="qa"><div class="q">${mark ? `<i>${mark}</i>` : "Q."}${ed(path + ".0", q, "", "span")}</div>${ed(path + ".1", a, "a")}</div>`;
  return page(0, `THE CAST · ${esc(pr.no || String(i+1).padStart(2,"0"))}`, `
    <div class="name">
      ${ed(`designers.${i}.name`, d.name, "pnm")}
      <div class="meta"><span class="kk">INTERVIEW</span>${ed(`designers.${i}.role`, d.role, "rl", "span")}${ed(`designers.${i}.mbti`, d.mbti, "mb", "span")}</div>
    </div>
    <div class="iv">
      <div class="col"><h3>HOW TO WORK WITH ME</h3>${pr.work.map((w,j)=>qa(`${base}.work.${j}`, w[0], w[1], j % 2 ? "✕" : "○")).join("")}</div>
      <div class="col"><h3>ABOUT ME</h3>${pr.about.map((a,j)=>qa(`${base}.about.${j}`, a[0], a[1], "")).join("")}</div>
    </div>`, "prof", `
    ${photo(`${base}.photo`, "hero")}
    <div class="no"><small>THE CAST</small>${esc(pr.no || String(i+1).padStart(2,"0"))}</div>
    <div class="quote">${ed(`${base}.oneQ`, pr.oneQ, "label")}${ed(`${base}.oneA`, pr.oneA.replace(/\s+/g, "\n"), "a")}</div>`);
}
'''

js = open(M + "render.js", encoding="utf-8").read()
a = js.index("function profilePage(i){"); b = js.index("function render(){")
js = js[:a] + JS + "\n" + js[b:]
# page()에 배경 레이어(extra)를 넣을 수 있게
old = '''function page(n, sec, inner, cls=""){
  const mg = data.magazine; n = ++PNO;
  return `<section class="page ${cls}">'''
assert old in js
js = js.replace(old, '''function page(n, sec, inner, cls="", extra=""){
  const mg = data.magazine; n = ++PNO;
  return `<section class="page ${cls}">${extra}''')
open(M + "render.js", "w", encoding="utf-8").write(js)

head = open(M + "head.html", encoding="utf-8").read()
a = head.index("/* ── 디자이너 프로필 (THE CAST 인터뷰) ── */"); b = head.index("/* 편집 모드 */")
head = head[:a] + CSS + "\n" + head[b:]
open(M + "head.html", "w", encoding="utf-8").write(head)
print("ok")
