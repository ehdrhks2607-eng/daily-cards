# 매거진에 파트너 개인 페이지(NEW FACES 콜라주) 추가 — 민주부터
import base64, json
M = "/tmp/claude-0/-home-user-daily-cards/06ef2264-b127-5a98-911e-16c520eb086c/scratchpad/mag/"
MJ = "/tmp/claude-0/-home-user-daily-cards/06ef2264-b127-5a98-911e-16c520eb086c/scratchpad/minju/"
b64 = lambda p, t: f"data:{t};base64," + base64.b64encode(open(p, "rb").read()).decode()

profile = {
    "sticker": b64(MJ + "sticker.png", "image/png"),
    "snap": b64(MJ + "snap.jpg", "image/jpeg"),
    "joined": "20○○.○○",
    "oneQ": "나를 한마디로 표현하면?",
    "oneA": "생각보다 정부자",
    "work": [["일할 때 이렇게 해 주면 좋아요", "알잘딱깔센"],
             ["일할 때 이렇게 하면 싫어요", "똑같은 질문 여러 번 해서\n똑같은 대답 계속하게 만들기"]],
    "about": [["피드백은 이렇게", "둘이서만 있을 때 해 주세요"],
              ["좋아하는 칭찬 스타일", "어느 부분에서 어떤 게 괜찮았는지\n세세한 칭찬이 좋아요"]],
    "cheerQ": "신입 파트너에게 한마디",
    "cheer": "화이팅!"
}
json.dump(profile, open(M + "profile_minju.json", "w", encoding="utf-8"), ensure_ascii=False)

CSS = """
/* ── 파트너 개인 페이지 (NEW FACES 콜라주) ── */
.np { padding:0; display:block; }
.np .run { position:absolute; left:46px; right:46px; top:0; z-index:5; }
.np .block { position:absolute; left:46px; right:46px; top:96px; height:530px; background:var(--mauve); }
.np .block .kick { position:absolute; left:22px; top:18px; font-family:var(--mono); font-size:12px; font-weight:600; letter-spacing:3px; color:#fff; }
.np .bigname { position:absolute; left:22px; top:58px; font-family:var(--title); font-size:220px; line-height:.98; color:#F4EEF2; white-space:pre-line; }
.np .stk { position:absolute; right:-18px; bottom:-30px; width:440px; height:540px; transform:rotate(-2deg); z-index:2;
  background-color:transparent; background-size:contain; background-position:right bottom; background-repeat:no-repeat;
  filter:drop-shadow(0 10px 18px rgba(0,0,0,.28)); overflow:visible; }
.np .snap { position:absolute; left:236px; bottom:-56px; width:150px; background:#fff; padding:9px 9px 34px; transform:rotate(-6deg);
  box-shadow:0 8px 18px rgba(0,0,0,.25); z-index:3; }
.np .snap .ph { width:100%; aspect-ratio:1; background-size:cover; background-position:center; }
.np .snap span { position:absolute; left:0; right:0; bottom:9px; text-align:center; font-family:var(--mono); font-size:10.5px; font-weight:600; letter-spacing:2px; color:var(--graphite); }
.np .snap::before { content:""; position:absolute; left:50%; top:-10px; width:64px; height:20px; background:rgba(233,232,230,.85); transform:translateX(-50%) rotate(4deg); z-index:2; }
.np .nfbadge { position:absolute; right:-16px; top:-26px; width:118px; height:118px; border-radius:50%; background:var(--ink); color:#fff; z-index:4;
  display:flex; flex-direction:column; align-items:center; justify-content:center; transform:rotate(10deg); }
.np .nfbadge b { font-family:var(--display); font-weight:400; font-size:30px; line-height:1; } .np .nfbadge span { font-family:var(--mono); font-size:10px; letter-spacing:2px; margin-top:4px; }
.np .lower { position:absolute; left:46px; right:46px; top:668px; bottom:62px; display:flex; flex-direction:column; }
.np .meta { display:flex; justify-content:space-between; align-items:baseline; border-bottom:3px solid var(--ink); padding-bottom:12px; }
.np .meta .who { font-family:var(--title); font-size:34px; display:flex; align-items:baseline; gap:10px; }
.np .meta .who small { font-family:var(--mono); font-size:12px; color:var(--mauve); letter-spacing:2px; }
.np .meta .join { font-family:var(--mono); font-size:12px; font-weight:600; letter-spacing:2px; color:var(--graphite); display:flex; gap:8px; }
.np .quote { padding:16px 0 12px; border-bottom:1px solid var(--hair); display:flex; align-items:baseline; gap:20px; }
.np .q { font-family:var(--mono); font-size:11px; font-weight:600; color:var(--mauve); letter-spacing:.5px; display:flex; gap:4px; }
.np .q i { font-style:normal; font-family:var(--body); font-weight:900; color:var(--ink); margin-right:4px; }
.np .quote .big { font-family:var(--title); font-size:42px; line-height:1.1; }
.np .quote .big::before { content:"“"; color:var(--mauve); } .np .quote .big::after { content:"”"; color:var(--mauve); }
.np .qa2 { flex:1; display:grid; grid-template-columns:1fr 1fr; gap:0 26px; padding:14px 0; }
.np .qa2 > div + div { border-left:1px solid var(--hair); padding-left:26px; }
.np .qa2 .a { font-size:17px; font-weight:800; line-height:1.45; margin:6px 0 16px; white-space:pre-line; word-break:keep-all; }
.np .cheer { display:flex; align-items:center; justify-content:space-between; background:var(--ink); color:#fff; padding:10px 20px; }
.np .cheer .q { color:#fff; font-size:11px; letter-spacing:2px; }
.np .cheer .c { font-family:var(--title); font-size:30px; color:#E7D3E2; }
.np .folio { position:absolute; left:46px; right:46px; bottom:0; margin:0; }
.editing .np .stk { outline-offset:-20px; }
"""

JS = r'''
function partnerPage(i){
  const p = data.partners[i], pr = p.profile, base = `partners.${i}.profile`, mg = data.magazine;
  const ph = (path, cls) => `<div class="ph ${cls}" data-photo="${path}" style="background-image:url('${getP(path)}')"></div>`;
  const qa = (path, q, a, mark) => `<div class="q">${mark ? `<i>${mark}</i>` : "Q."}${ed(path + ".0", q, "", "span")}</div>${ed(path + ".1", a, "a")}`;
  return `<section class="page np">
    <div class="run"><span class="m">MAISON<small>de idHAIR</small></span><span class="sec">NEW FACES</span></div>
    <div class="block">
      <div class="kick">NEW FACES · PARTNER</div>
      <div class="bigname">${esc([...p.name].join("\n"))}</div>
      ${ph(`${base}.sticker`, "stk")}
      <div class="snap">${ph(`${base}.snap`, "")}<span>UNFILTERED</span></div>
      <div class="nfbadge"><b>NEW</b><span>FACE</span></div>
    </div>
    <div class="lower">
      <div class="meta"><span class="who">${ed(`partners.${i}.name`, p.name, "", "span")}<small>PARTNER</small></span><span class="join">JOINED ${ed(`${base}.joined`, pr.joined, "", "span")}</span></div>
      <div class="quote">${ed(`${base}.oneQ`, pr.oneQ, "q")}${ed(`${base}.oneA`, pr.oneA, "big")}</div>
      <div class="qa2">
        <div>${pr.work.map((w,j)=>qa(`${base}.work.${j}`, w[0], w[1], j ? "✕" : "○")).join("")}</div>
        <div>${pr.about.map((w,j)=>qa(`${base}.about.${j}`, w[0], w[1], "")).join("")}</div>
      </div>
      <div class="cheer">${ed(`${base}.cheerQ`, pr.cheerQ, "q")}${ed(`${base}.cheer`, pr.cheer, "c")}</div>
    </div>
    <div class="folio"><span>MAISON · ${esc(mg.issue)}</span><b>NEW FACES · ${esc(p.name)}</b></div>
  </section>`;
}
'''

js = open(M + "render.js", encoding="utf-8").read()
if "function partnerPage" not in js:
    js = js.replace("function render(){", JS + "\nfunction render(){", 1)
    anchor = "  /* 5. A DAY IN THE SALON */"
    assert anchor in js
    js = js.replace(anchor, "  data.partners.forEach((p,i) => { if (p.profile) { P.push(partnerPage(i)); PNO++; } });\n\n" + anchor)
    open(M + "render.js", "w", encoding="utf-8").write(js)

head = open(M + "head.html", encoding="utf-8").read()
if "파트너 개인 페이지 (NEW FACES 콜라주)" not in head:
    head = head.replace("/* 편집 모드 */", CSS + "\n/* 편집 모드 */", 1)
    open(M + "head.html", "w", encoding="utf-8").write(head)

asm = open(M + "assemble.py", encoding="utf-8").read()
old = '''s = s.replace(_old, '{ photo:"' + _mj + '", name:"민주", note:"파트너" }')'''
if old in asm:
    asm = asm.replace(old, '''_pm = json.load(open(M + "profile_minju.json", encoding="utf-8"))
_mj = _pm["snap"]
s = s.replace(_old, '{ photo:"' + _mj + '", name:"민주", note:"파트너", profile:' + json.dumps(_pm, ensure_ascii=False) + ' }')''')
    open(M + "assemble.py", "w", encoding="utf-8").write(asm)
print("ok")
