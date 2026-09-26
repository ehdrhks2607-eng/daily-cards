"""Render post.json 'cards' into 1080x1350 PNGs (card_1.png ...) with Playwright.

usage: python scripts/render_cards.py posts/2026-09-26/jak/post.json [...]
card types: cover {title, sub} / tip {label, title, body} / end {title, sub}
"""
import html
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))


def esc(t):
    return html.escape(t or "").replace("\n", "<br>")


def card_html(card, idx, total, acc):
    t = CFG["accounts"][acc]["theme"]
    label = CFG["accounts"][acc]["label"]
    kind = card.get("type", "tip")
    if kind == "cover":
        body = f"""
        <div class="bar"></div>
        <div class="cover-title">{esc(card['title'])}</div>
        <div class="cover-sub">{esc(card.get('sub'))}</div>
        <div class="swipe">넘겨보기 →</div>"""
    elif kind == "end":
        body = f"""
        <div class="end-title">{esc(card['title'])}</div>
        <div class="bar"></div>
        <div class="end-sub">{esc(card.get('sub'))}</div>"""
    else:
        body = f"""
        <div class="label">{esc(card.get('label'))}</div>
        <div class="tip-title">{esc(card['title'])}</div>
        <div class="tip-body">{esc(card.get('body'))}</div>"""
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ width:1080px; height:1350px; background:{t['bg']}; color:{t['fg']};
           font-family:'Noto Sans CJK KR','Noto Sans KR',sans-serif; position:relative;
           word-break:keep-all; }}
    .head {{ position:absolute; top:72px; left:96px; right:96px; display:flex;
            justify-content:space-between; font-size:30px; font-weight:500; color:{t['muted']}; }}
    .wrap {{ position:absolute; left:96px; right:96px; top:0; bottom:0; display:flex;
            flex-direction:column; justify-content:center; }}
    .bar {{ width:88px; height:12px; background:{t['accent']}; border-radius:6px; margin:0 0 48px; }}
    .cover-title {{ font-size:104px; font-weight:900; line-height:1.22; letter-spacing:-3px; }}
    .cover-sub {{ margin-top:48px; font-size:44px; font-weight:500; color:{t['muted']}; line-height:1.5; }}
    .swipe {{ position:fixed; bottom:80px; right:96px; font-size:32px; color:{t['accent']}; font-weight:700; }}
    .label {{ display:inline-block; align-self:flex-start; font-size:34px; font-weight:700;
             color:{t['bg']}; background:{t['accent']}; padding:12px 28px; border-radius:40px; margin-bottom:44px; }}
    .tip-title {{ font-size:78px; font-weight:900; line-height:1.3; letter-spacing:-2px; }}
    .tip-body {{ margin-top:52px; font-size:46px; font-weight:400; line-height:1.65; color:{t['fg']}; opacity:.85; }}
    .end-title {{ font-size:92px; font-weight:900; line-height:1.28; letter-spacing:-2px; margin-bottom:56px; }}
    .end-sub {{ font-size:44px; font-weight:700; color:{t['accent']}; line-height:1.5; }}
    </style></head><body>
    <div class="head"><span>{esc(label)}</span><span>{idx} / {total}</span></div>
    <div class="wrap">{body}</div>
    </body></html>"""


def render(post_path):
    post_path = Path(post_path)
    post = json.loads(post_path.read_text(encoding="utf-8"))
    cards = post["cards"]
    names = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": 1080, "height": 1350})
        for i, c in enumerate(cards, 1):
            page.set_content(card_html(c, i, len(cards), post["account"]))
            page.wait_for_timeout(150)
            name = f"card_{i}.png"
            page.screenshot(path=str(post_path.parent / name))
            names.append(name)
        b.close()
    post.setdefault("instagram", {})["images"] = names
    post_path.write_text(json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8")
    print(post_path.parent, "->", len(names), "cards")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        render(arg)
