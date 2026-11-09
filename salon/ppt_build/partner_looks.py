# 셀카를 매거진 톤으로: A 흑백 필름 / B 모브 듀오톤 / C 컷아웃 흑백(스튜디오)
import numpy as np
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw, ImageFont
D = "/tmp/claude-0/-home-user-daily-cards/06ef2264-b127-5a98-911e-16c520eb086c/scratchpad/minju/"
src = Image.open(D + "in.webp").convert("RGB")
W, H = src.size

def face_crop(im, ratio=4/5):
    # 얼굴 중심(셀카 기준 오른쪽 위)으로 4:5 크롭 — 모든 파트너 같은 비율
    th = int(H * 0.92); tw = int(th * ratio)
    cx, cy = int(W * 0.60), int(H * 0.40)
    x0 = max(0, min(W - tw, cx - tw // 2)); y0 = max(0, min(H - th, cy - int(th * 0.42)))
    return im.crop((x0, y0, x0 + tw, y0 + th))

def grain(im, s=9, seed=1):
    a = np.asarray(im).astype(np.float32)
    n = np.random.default_rng(seed).normal(0, s, a.shape[:2])
    if a.ndim == 3: n = n[..., None]
    return Image.fromarray(np.clip(a + n, 0, 255).astype(np.uint8))

def bw(im):
    g = ImageOps.grayscale(im)
    g = ImageOps.autocontrast(g, cutoff=1)
    g = ImageEnhance.Contrast(g).enhance(1.18)
    g = g.point(lambda v: int(255 * ((v / 255) ** 0.92)))          # 중간톤 살짝 밝게
    return g

# A) 흑백 필름: 원래 배경 그대로, 흑백+입자+비네트
a = face_crop(src)
ga = bw(a)
arr = np.asarray(ga).astype(np.float32); h, w = arr.shape
yy, xx = np.mgrid[0:h, 0:w]
vig = 1 - 0.28 * (((xx - w / 2) / w) ** 2 + ((yy - h / 2) / h) ** 2) * 2.5
A = grain(Image.fromarray(np.clip(arr * vig, 0, 255).astype(np.uint8)), 10).convert("RGB")

# B) 모브 듀오톤: 어두운 곳 잉크, 밝은 곳 연보라
B = ImageOps.colorize(bw(a), black=(30, 28, 26), white=(238, 226, 235), mid=(139, 108, 132))
B = grain(B, 7, 2)

# C) 컷아웃 흑백: 2차 스튜디오 합성본을 흑백으로
c = Image.open(D + "minju_studio2.jpg").convert("RGB")
c = c.crop((0, int(c.height * 0.0), c.width, int(c.width * 5 / 4)))
C = grain(bw(c), 8, 3).convert("RGB")

tiles = [(A, "A  흑백 필름"), (B, "B  모브 듀오톤"), (C, "C  배경 교체 + 흑백")]
for im, name in tiles:
    im.save(D + f"look_{name[0]}.jpg", quality=92)
hh = 640
row = [im.resize((int(im.width * hh / im.height), hh), Image.LANCZOS) for im, _ in tiles]
sheet = Image.new("RGB", (sum(r.width for r in row) + 20 * 4, hh + 70), (233, 232, 230))
dr = ImageDraw.Draw(sheet)
try: font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 30)
except Exception: font = None
x = 20
for r, (_, name) in zip(row, tiles):
    sheet.paste(r, (x, 20)); dr.text((x, hh + 28), name, fill=(30, 28, 26), font=font); x += r.width + 20
sheet.save(D + "looks.jpg", quality=90)
print("ok", font is not None)
