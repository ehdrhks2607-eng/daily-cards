# 룩북 표지를 잡지 표지 스타일로 교체
import base64, io
from PIL import Image
L = "/tmp/claude-0/-home-user-daily-cards/06ef2264-b127-5a98-911e-16c520eb086c/scratchpad/"
F = "/home/user/daily-cards/salon/a4_lookbook.html"

im = Image.open(L + "photos/d1.jpg").convert("RGB")
im.thumbnail((1100, 1500))
b = io.BytesIO(); im.save(b, "JPEG", quality=82, optimize=True)
photo = "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()

COVER = '''  cover: {
    photo: "%s",
    issue: "VOL.01 · NEW PARTNER ISSUE",
    kicker: "COVER STORY",
    headline: "우리 매장\\n사용 설명서",
    lines: [
      { num: "7", text: "디자이너 7인\\nMBTI 대공개" },
      { num: "6", text: "DAY 1부터 6까지\\n1주일 OJT 완전 정복" },
      { num: "18", text: "고객님 마음 여는\\n멘트 총정리" }
    ],
    badge: "신입 파트너\\n필독",
    signals: "1번 · 2번 · M · T · H\\n매장 신호 해독법",
    caption: "COVER · 보배 원장"
  },
''' % photo

CSS = """
/* ── 표지: 잡지 커버 ── */
.mag { display:block; background:#DAD8D6; }
.mag .top { position:absolute; left:40px; right:40px; top:30px; display:flex; justify-content:space-between; z-index:4;
  font-family:var(--mono); font-size:11.5px; font-weight:600; letter-spacing:2px; text-transform:uppercase; }
.mag .masthead { position:absolute; left:0; right:0; top:44px; text-align:center; z-index:1; font-family:var(--display);
  font-size:238px; line-height:.8; letter-spacing:-3px; color:var(--ink); }
.mag .sub { position:absolute; right:44px; top:236px; z-index:4; font-family:var(--mono); font-size:13px; font-weight:600;
  letter-spacing:4px; color:var(--mauve); text-transform:uppercase; }
.mag .photo { position:absolute; left:0; right:0; top:262px; bottom:0; z-index:2; border-radius:0; background-color:transparent;
  background-size:auto 108%; background-position:78% 0; background-repeat:no-repeat;
  -webkit-mask-image:linear-gradient(to right, transparent 18%, #000 40%, #000 92%, transparent 100%);
          mask-image:linear-gradient(to right, transparent 18%, #000 40%, #000 92%, transparent 100%); }
.mag .left { position:absolute; left:40px; top:290px; width:330px; z-index:3; }
.mag .kicker { font-family:var(--mono); font-size:12px; font-weight:600; letter-spacing:3px; color:var(--mauve); }
.mag .headline { font-family:var(--title); font-size:72px; line-height:1.02; margin:6px 0 30px; white-space:pre-line; letter-spacing:-1px; }
.mag .cl { display:grid; grid-template-columns:auto 1fr; gap:14px; align-items:center; margin-bottom:22px; }
.mag .cl .n { font-family:var(--display); font-size:62px; line-height:.9; color:var(--mauve); min-width:56px; }
.mag .cl .t { font-size:18px; font-weight:800; line-height:1.3; white-space:pre-line; }
.mag .badge { position:absolute; right:52px; top:318px; z-index:3; width:132px; height:132px; border-radius:50%; background:var(--mauve);
  color:#fff; display:flex; align-items:center; justify-content:center; text-align:center; font-family:var(--title); font-size:22px;
  line-height:1.15; white-space:pre-line; transform:rotate(8deg); }
.mag .signals { position:absolute; left:40px; bottom:150px; z-index:3; font-size:17px; font-weight:800; line-height:1.4; white-space:pre-line;
  background:var(--ink); color:#fff; padding:10px 14px; border-radius:4px; }
.mag .hello { position:absolute; left:40px; bottom:52px; z-index:3; font-size:19px; font-weight:700; white-space:pre-line; line-height:1.45; }
.mag .cap { position:absolute; right:40px; bottom:40px; z-index:3; font-family:var(--mono); font-size:11px; font-weight:600; letter-spacing:2px;
  color:#fff; text-transform:uppercase; }
"""

JS_OLD_START = '  P.push(page(1, "WELCOME", "", "", `'
JS_NEW = '''  const cv = data.cover;
  P.push(`<section class="page mag">
    <div class="top"><span>${esc(cv.issue)}</span><span>${esc(s.open)} · ${esc(s.name.replace(/^.*아이디헤어\\s*/, "") || s.name)}</span></div>
    <div class="masthead" aria-label="Maison de idHAIR">MAISON</div>
    <div class="sub">de idHAIR</div>
    <div class="ph photo" data-photo="cover.photo" style="background-image:url('${cv.photo}')"></div>
    <div class="left">
      ${ed("cover.kicker", cv.kicker, "kicker")}
      ${ed("cover.headline", cv.headline, "headline")}
      ${cv.lines.map((l,i)=>`<div class="cl">${ed(`cover.lines.${i}.num`, l.num, "n", "span")}${ed(`cover.lines.${i}.text`, l.text, "t", "span")}</div>`).join("")}
    </div>
    ${ed("cover.badge", cv.badge, "badge")}
    ${ed("cover.signals", cv.signals, "signals")}
    ${ed("store.hello", s.hello, "hello")}
    ${ed("cover.caption", cv.caption, "cap")}
  </section>`);'''

s = open(F, encoding="utf-8").read()
assert "  talk: {" in s and JS_OLD_START in s
s = s.replace("  talk: {", COVER + "  talk: {", 1)
a = s.index(JS_OLD_START); b = s.index('`, "cover"));', a) + len('`, "cover"));')
s = s[:a] + JS_NEW + s[b:]
s = s.replace("</style>", CSS + "</style>", 1)
open(F, "w", encoding="utf-8").write(s)
print("ok", len(s) // 1024, "KB")
