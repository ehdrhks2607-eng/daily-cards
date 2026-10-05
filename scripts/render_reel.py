"""Render a post.json 'reel' into a 15s vertical MP4 (1080x1920, H.264, 30fps) + a contact sheet.

usage: python scripts/render_reel.py posts/2026-10-06/jak_reel/post.json [...]
       python scripts/render_reel.py --fps 30 --sheet-only posts/.../post.json   (preview frames only)

post.json "reel" schema (text: \n = line break, *word* = accent color in hook/pain/item/cta):
{
  "series":   "DAY 9",                       optional tag above the hook
  "hook":     "연휴 배달비\n*얼마* 나왔어?",     <= 2 lines, <= 7 chars per line
  "count":    {"to": 68000, "suffix": "원", "label": "연휴 4번 배달"},   optional counter
  "pain":     "먹고 나면 더부룩하고\n점심값도 또 나가",   <= 2 lines, <= 12 chars per line
  "tips_title": "그래서 3일만 해보기로 함",    optional
  "tips":     ["배달앱 내역 열기", "냉장고 먼저 확인", "데우는 단백질"],   3 items, <= 9 chars
  "item_lead": "그래서 찾아본 것",             optional
  "item":     "닭가슴살",                     <= 6 chars per line
  "item_sub": "리뷰 많은 걸로 골라둠",
  "cta":      "골라둔 닭가슴살은\n프로필 링크에",  <= 2 lines, <= 9 chars per line
  "caption":  "...",                           Instagram caption (honorific, + disclosure + hashtags)
  "video":    "reel.mp4"                       filled in by this script
}
Writes reel.mp4 and reel_sheet.png (6 key frames) next to post.json.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
TEMPLATE = (ROOT / "scripts" / "reel_template.html").read_text(encoding="utf-8")
W, H = 1080, 1920
SHEET_TIMES = [1.6, 5.6, 9.8, 12.2, 14.6]


def build_html(post):
    themes = {k: dict(v["theme"], label=v["label"], handle=v.get("handle", v["label"]))
              for k, v in CFG["accounts"].items()}
    data = dict(post["reel"], account=post["account"])
    return (TEMPLATE.replace("/*__REEL_DATA__*/", json.dumps(data, ensure_ascii=False))
                    .replace("/*__THEMES__*/", json.dumps(themes, ensure_ascii=False)))


def contact_sheet(page, out):
    """Small 5-up strip of key frames to eyeball text clipping / broken glyphs."""
    from PIL import Image
    import io
    shots = []
    for t in SHEET_TIMES:
        page.evaluate(f"window.__setTime({t})")
        shots.append(Image.open(io.BytesIO(page.screenshot(type="png"))).resize((W // 3, H // 3)))
    sheet = Image.new("RGB", (len(shots) * W // 3 + (len(shots) - 1) * 12, H // 3), "white")
    for i, im in enumerate(shots):
        sheet.paste(im, (i * (W // 3 + 12), 0))
    sheet.save(out)


def render(post_path, fps=30, sheet_only=False):
    post_path = Path(post_path)
    post = json.loads(post_path.read_text(encoding="utf-8"))
    if not post.get("reel"):
        print(post_path, "has no 'reel' field, skipped")
        return
    out_mp4 = post_path.parent / "reel.mp4"
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": W, "height": H})
        page.set_content(build_html(post))
        page.wait_for_function("window.__ready === true", timeout=20000)
        page.wait_for_timeout(300)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        dur = page.evaluate("window.__duration")
        contact_sheet(page, post_path.parent / "reel_sheet.png")
        if not sheet_only:
            n = int(round(dur * fps))
            ff = subprocess.Popen(
                ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps),
                 "-c:v", "mjpeg", "-i", "-",
                 # silent stereo track: some Reels pipelines reject video without audio
                 "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                 "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                 "-pix_fmt", "yuv420p", "-profile:v", "high", "-r", str(fps), "-g", str(fps * 2),
                 "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out_mp4)],
                stdin=subprocess.PIPE)
            for i in range(n):
                page.evaluate(f"window.__setTime({i / fps})")
                ff.stdin.write(page.screenshot(type="jpeg", quality=92))
            ff.stdin.close()
            if ff.wait() != 0:
                raise RuntimeError("ffmpeg failed")
        b.close()
        if errors:
            raise RuntimeError(f"template JS error: {errors}")
    if not sheet_only:
        post["reel"]["video"] = out_mp4.name
        post_path.write_text(json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8")
        size = out_mp4.stat().st_size / 1e6
        print(post_path.parent, f"-> reel.mp4 ({dur:.0f}s, {size:.1f} MB) + reel_sheet.png")
    else:
        print(post_path.parent, "-> reel_sheet.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("posts", nargs="+")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--sheet-only", action="store_true")
    a = ap.parse_args()
    for f in a.posts:
        render(f, a.fps, a.sheet_only)
