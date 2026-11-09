# 매거진에 디자이너 개인 프로필 페이지 추가 (보배 원장부터)
import base64, io, json
from PIL import Image
SP = "/tmp/claude-0/-home-user-daily-cards/06ef2264-b127-5a98-911e-16c520eb086c/scratchpad/"
M = SP + "mag/"

im = Image.open(SP + "photos/d1.jpg").convert("RGB")
im.thumbnail((1100, 1500))
b = io.BytesIO(); im.save(b, "JPEG", quality=84, optimize=True)
photo = "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()

profile = {
    "photo": photo,
    "tagline": "반포 '단발머리'는 보배",
    "specialty": "단발 · 뿌리펌 전문",
    "oneQ": "나를 한마디로 표현하면?",
    "oneA": "마음도 손도 바쁨",
    "work": [
        ["일할 때 이렇게 대해 주면 좋아요", "\"도와드릴 거 있을까요?\"\n물어봐 주기"],
        ["일할 때 이렇게 대하면 싫어요", "바쁜데 찾아야 할 때\n고객 3분 이상이면 옆에 있어 줘"],
        ["동료가 해 줬으면 하는 행동", "\"원장님, 뭐 도와드릴까요?\"\n물어봐 주기"],
        ["동료가 안 했으면 하는 행동", "1. \"드릴 말씀이…\"\n2. 감정적일 때 말하기"],
    ],
    "about": [
        ["스트레스 받을 때 나는", "눈꼬리가 올라가요"],
        ["피드백은 이렇게", "둘만 있을 때 은밀하게~"],
        ["좋아하는 칭찬 스타일", "귀엽다고 해 주기,\n디테일하게 말해 주기"],
        ["좋아하는 팀 분위기", "고등학교 반 같은,\n재밌고 신나는"],
    ],
}

CSS = """
/* ── 디자이너 프로필 (THE CAST 인터뷰) ── */
.prof .art { padding-top:20px; }
.prof .top { display:grid; grid-template-columns:330px 1fr; gap:28px; height:500px; }
.prof .top .ph { height:100%; background-size:cover; background-position:50% 8%; border-radius:2px; }
.prof .who { display:flex; flex-direction:column; min-width:0; }
.prof .pnm { font-family:var(--title); font-size:118px; line-height:.95; margin-top:6px; letter-spacing:-2px; }
.prof .meta { display:flex; gap:12px; align-items:baseline; margin-top:10px; }
.prof .meta .rl { font-size:20px; font-weight:800; }
.prof .meta .mb { font-family:var(--display); font-size:34px; color:var(--mauve); line-height:1; }
.prof .tagline { font-size:15px; color:var(--graphite); font-weight:600; margin-top:10px; line-height:1.5; }
.prof .one { margin-top:auto; border-top:3px solid var(--ink); padding-top:14px; }
.prof .one .a { font-family:var(--title); font-size:46px; line-height:1.12; margin-top:8px; word-break:keep-all; }
.prof .one .a::before { content:"“"; color:var(--mauve); }
.prof .one .a::after { content:"”"; color:var(--mauve); }
.prof .sech { display:flex; align-items:baseline; gap:12px; margin:24px 0 10px; }
.prof .sech b { font-family:var(--display); font-size:26px; letter-spacing:.5px; }
.prof .work { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.prof .wk { padding:13px 16px 14px; background:var(--paper); }
.prof .wk.yes { background:var(--mist); }
.prof .wk .q { font-family:var(--mono); font-size:11px; font-weight:600; letter-spacing:1px; color:var(--mauve); display:flex; gap:8px; align-items:center; }
.prof .wk .q i { font-style:normal; font-family:var(--body); font-size:15px; font-weight:900; color:var(--ink); }
.prof .wk .a { font-size:17px; font-weight:800; line-height:1.4; margin-top:6px; white-space:pre-line; word-break:keep-all; }
.prof .aboutme { display:grid; grid-template-columns:repeat(4,1fr); border-top:1px solid var(--ink); }
.prof .am { padding:12px 12px 0 0; }
.prof .am + .am { padding-left:12px; border-left:1px solid var(--hair); }
.prof .am .q { font-family:var(--mono); font-size:10.5px; font-weight:600; color:var(--mauve); line-height:1.4; }
.prof .am .a { font-size:15.5px; font-weight:800; line-height:1.4; margin-top:6px; white-space:pre-line; word-break:keep-all; }
"""

JS_PROFILE = r'''
function profilePage(i){
  const d = data.designers[i], pr = d.profile, base = `designers.${i}.profile`;
  const yes = j => j % 2 === 0;
  return page(0, `THE CAST · ${String(i+1).padStart(2,"0")}`, `
    <div class="top">
      ${photo(`${base}.photo`)}
      <div class="who">
        <div class="kicker">THE CAST · INTERVIEW</div>
        ${ed(`designers.${i}.name`, d.name, "pnm")}
        <div class="meta">${ed(`designers.${i}.role`, d.role, "rl", "span")}${ed(`designers.${i}.mbti`, d.mbti, "mb", "span")}</div>
        <div class="tagline">${ed(`${base}.tagline`, pr.tagline, "", "span")}<br>${ed(`${base}.specialty`, pr.specialty, "", "span")}</div>
        <div class="one">${ed(`${base}.oneQ`, pr.oneQ, "label")}${ed(`${base}.oneA`, pr.oneA, "a")}</div>
      </div>
    </div>
    <div class="sech"><b>HOW TO WORK WITH ME</b><span class="label">같이 일하는 법</span></div>
    <div class="work">${pr.work.map((w,j)=>`
      <div class="wk ${yes(j) ? "yes" : "no"}">
        <div class="q"><i>${yes(j) ? "○" : "✕"}</i>${ed(`${base}.work.${j}.0`, w[0], "", "span")}</div>
        ${ed(`${base}.work.${j}.1`, w[1], "a")}
      </div>`).join("")}
    </div>
    <div class="sech"><b>ABOUT ME</b><span class="label">나에 대해</span></div>
    <div class="aboutme">${pr.about.map((a,j)=>`
      <div class="am">${ed(`${base}.about.${j}.0`, a[0], "q")}${ed(`${base}.about.${j}.1`, a[1], "a")}</div>`).join("")}
    </div>`, "prof");
}
'''

# render.js: 쪽 번호를 자동으로 매기고, THE CAST 다음에 프로필 페이지를 넣는다
js = open(M + "render.js", encoding="utf-8").read()
old_page = '''function page(n, sec, inner){
  const mg = data.magazine;
  return `<section class="page">'''
assert old_page in js
js = js.replace(old_page, '''let PNO = 1;
function page(n, sec, inner, cls=""){
  const mg = data.magazine; n = ++PNO;
  return `<section class="page ${cls}">''')
js = js.replace("  const s = data.store, mg = data.magazine, P = [];", "  PNO = 1;\n  const s = data.store, mg = data.magazine, P = [];")
anchor = "  /* 4. NEW FACES */"
assert anchor in js
js = js.replace(anchor, "  data.designers.forEach((d,i) => { if (d.profile) P.push(profilePage(i)); });\n\n" + anchor)
js = js.replace("function render(){", JS_PROFILE + "\nfunction render(){", 1)
open(M + "render.js", "w", encoding="utf-8").write(js)

head = open(M + "head.html", encoding="utf-8").read()
if "디자이너 프로필 (THE CAST 인터뷰)" not in head:
    head = head.replace("/* 편집 모드 */", CSS + "\n/* 편집 모드 */", 1)
    open(M + "head.html", "w", encoding="utf-8").write(head)

# assemble.py: 보배 원장 데이터에 profile 추가
asm = open(M + "assemble.py", encoding="utf-8").read()
if "PROFILE_JSON" not in asm:
    asm = asm.replace('open("/home/user/daily-cards/salon/a4_magazine.html", "w"',
        'import json\nPROFILE_JSON = json.load(open(M + "profile_bobae.json", encoding="utf-8"))\n'
        'k = \'"name": "보배", "mbti": "ESTJ"\'\nassert s.count(k) == 1\n'
        's = s.replace(k, k + \', "profile": \' + json.dumps(PROFILE_JSON, ensure_ascii=False))\n'
        'open("/home/user/daily-cards/salon/a4_magazine.html", "w"')
    open(M + "assemble.py", "w", encoding="utf-8").write(asm)
json.dump(profile, open(M + "profile_bobae.json", "w", encoding="utf-8"), ensure_ascii=False)
print("ok")
