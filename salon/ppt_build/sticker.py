# 파트너 페이지용 소재: ① 흑백 컷아웃 + 흰 스티커 테두리(PNG 투명) ② 컬러 원본 폴라로이드 컷
import sys, numpy as np
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
D = "/tmp/claude-0/-home-user-daily-cards/06ef2264-b127-5a98-911e-16c520eb086c/scratchpad/minju/"
mask_file = sys.argv[1] if len(sys.argv) > 1 else "mask.png"
src = Image.open(D + "in.webp").convert("RGB")
m = Image.open(D + mask_file).convert("L").resize(src.size, Image.LANCZOS)

# 마스크 정리: 오른쪽 끝 나무 걸친 부분 자르고, 경계 부드럽게
W, H = src.size
crop_box = (0, 0, W - 40, H)
src, m = src.crop(crop_box), m.crop(crop_box)
m = m.point(lambda v: 0 if v < 40 else (255 if v > 215 else int((v - 40) / 175 * 255))).filter(ImageFilter.GaussianBlur(1.1))

# 흑백 인물 (밝고 또렷하게)
g = ImageOps.grayscale(src)
g = ImageOps.autocontrast(g, cutoff=0.8)
g = ImageEnhance.Contrast(g).enhance(1.15)
g = g.point(lambda v: int(255 * ((v / 255) ** 0.88)))
g = g.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
arr = np.asarray(g).astype(np.float32)
arr += np.random.default_rng(5).normal(0, 6, arr.shape)                # 인쇄 입자
person = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGB")

# 흰 스티커 테두리: 마스크를 넓혀서 흰색 판 만들기
pad = 40
big = Image.new("L", (src.width + pad * 2, src.height + pad * 2), 0); big.paste(m, (pad, pad))
outline = big.filter(ImageFilter.MaxFilter(25)).filter(ImageFilter.GaussianBlur(2)).point(lambda v: 255 if v > 110 else int(v * 2.3))
canvas = Image.new("RGBA", big.size, (0, 0, 0, 0))
canvas.paste(Image.new("RGBA", big.size, (255, 255, 255, 255)), (0, 0), outline)
pl = Image.new("RGBA", big.size, (0, 0, 0, 0)); pl.paste(person, (pad, pad))
canvas.paste(pl, (0, 0), big)
# 아래쪽은 잘린 몸이라 테두리 없이 곧게
bbox = canvas.getbbox(); canvas = canvas.crop((bbox[0], bbox[1], bbox[2], canvas.height - pad))
canvas.thumbnail((1000, 1300), Image.LANCZOS)
canvas.save(D + "sticker.png", optimize=True)

# 컬러 원본 폴라로이드 컷 (정사각, 살짝 따뜻함 유지)
s = Image.open(D + "in.webp").convert("RGB")
side = int(s.width * 0.82); x0 = int(s.width * 0.18); y0 = int(s.height * 0.08)
pol = s.crop((x0, y0, x0 + side, y0 + side)).resize((520, 520), Image.LANCZOS)
pol = ImageEnhance.Color(pol).enhance(0.9)
pol.save(D + "snap.jpg", quality=86)
print("ok", canvas.size)
