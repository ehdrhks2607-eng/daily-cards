"""도아도령 '오늘의 행운 카드' (인스타 피드 1장, 1080x1350) 렌더러.

usage: python scripts/render_luck_card.py posts/<날짜>/seoul_card/post.json
post.json의 luck_card: {date_label, keyword, line1, line2, character(default|love|career|reunion), cta?}
→ 같은 폴더에 card_1.png 를 만들고 instagram.images = ["card_1.png"] 로 맞춘다.
"""
import base64
import html
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "scripts" / "reel_assets"


def b64(p):
    return "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode()


def page_html(c):
    e = lambda t: html.escape(t or "").replace("\n", "<br>")
    ch = c.get("character") or "default"
    img = ASSETS / f"doa_full_{ch}.jpg"
    if not img.exists():
        img = ASSETS / "doa_full_default.jpg"
    cta = c.get("cta") or "📌 저장해 두고 오늘 한 번 더 보기 · 댓글에 '받을게요' + 띠"
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;background:radial-gradient(ellipse 90% 60% at 50% 35%,#1b2356 0%,#0E1330 55%,#060914 100%);
 color:#F3E6C4;font-family:'Noto Serif CJK KR','Noto Serif KR','Noto Sans CJK KR',serif;position:relative;overflow:hidden;word-break:keep-all}}
.f1{{position:absolute;inset:28px;border:4px solid #E8B54F;border-radius:26px}}
.f2{{position:absolute;inset:46px;border:1.5px solid rgba(232,181,79,.55);border-radius:18px}}
.corner{{position:absolute;width:70px;height:70px;border:4px solid #E8B54F}}
.c1{{left:60px;top:60px;border-right:0;border-bottom:0;border-radius:18px 0 0 0}}.c2{{right:60px;top:60px;border-left:0;border-bottom:0;border-radius:0 18px 0 0}}
.c3{{left:60px;bottom:60px;border-right:0;border-top:0;border-radius:0 0 0 18px}}.c4{{right:60px;bottom:60px;border-left:0;border-top:0;border-radius:0 0 18px 0}}
.top{{position:absolute;top:92px;left:0;right:0;text-align:center;font-family:'Noto Sans CJK KR',sans-serif;font-size:32px;letter-spacing:6px;color:#E8B54F;font-weight:700}}
.date{{position:absolute;top:142px;left:0;right:0;text-align:center;font-family:'Noto Sans CJK KR',sans-serif;font-size:28px;color:#9AA0B8}}
.arch{{position:absolute;left:290px;top:205px;width:500px;height:560px;border-radius:250px 250px 24px 24px;overflow:hidden;
 border:5px solid #E8B54F;box-shadow:0 0 60px rgba(232,181,79,.35);background:url({b64(img)}) center 18%/cover}}
.sun{{position:absolute;left:470px;top:178px;width:140px;height:56px;text-align:center;font-size:44px}}
.kw{{position:absolute;top:790px;left:0;right:0;text-align:center;font-size:150px;font-weight:900;color:#E8B54F;letter-spacing:-2px;
 text-shadow:0 0 40px rgba(232,181,79,.45),0 6px 24px rgba(0,0,0,.8)}}
.l{{position:absolute;top:985px;left:110px;right:110px;text-align:center;font-size:44px;line-height:1.55;font-weight:600}}
.cta{{position:absolute;bottom:128px;left:120px;right:120px;text-align:center;font-family:'Noto Sans CJK KR',sans-serif;font-size:29px;font-weight:700;
 color:#0E1330;background:#E8B54F;border-radius:40px;padding:16px 20px}}
.foot{{position:absolute;bottom:80px;left:0;right:0;text-align:center;font-family:'Noto Sans CJK KR',sans-serif;font-size:22px;color:#9AA0B8}}
</style></head><body>
<div class="f1"></div><div class="f2"></div><div class="corner c1"></div><div class="corner c2"></div><div class="corner c3"></div><div class="corner c4"></div>
<div class="top">☾ 도아도령 · 오늘의 행운 카드 ☀</div><div class="date">{e(c.get('date_label'))}</div>
<div class="arch"></div>
<div class="kw">{e(c.get('keyword'))}</div>
<div class="l">{e(c.get('line1'))}<br>{e(c.get('line2'))}</div>
<div class="cta">{e(cta)}</div>
<div class="foot">@doa.doryeong · 참고와 재미로 보는 콘텐츠예요</div>
</body></html>"""


def render(post_path):
    post_path = Path(post_path)
    post = json.loads(post_path.read_text(encoding="utf-8"))
    c = post.get("luck_card")
    if not c:
        print(post_path, "no luck_card, skipped"); return
    out = post_path.parent / "card_1.png"
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        pg.set_content(page_html(c))
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(800)
        pg.screenshot(path=str(out))
        b.close()
    post.setdefault("instagram", {})["images"] = ["card_1.png"]
    post_path.write_text(json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8")
    print(post_path.parent, "-> card_1.png")


if __name__ == "__main__":
    for a in sys.argv[1:]:
        render(a)
