# 메인 사진 → 흑백 스티커(BiRefNet 마스크), 두 번째 사진 → 컬러 폴라로이드
import sys, numpy as np, onnxruntime as ort
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
D = "/tmp/claude-0/-home-user-daily-cards/06ef2264-b127-5a98-911e-16c520eb086c/scratchpad/minju/"
main, second = sys.argv[1], sys.argv[2]
src = Image.open(main).convert("RGB")

x = np.asarray(src.resize((1024, 1024), Image.LANCZOS)).astype(np.float32) / 255.0
x = ((x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]).transpose(2, 0, 1)[None].astype(np.float32)
sess = ort.InferenceSession(D + "birefnet.onnx", providers=["CPUExecutionProvider"])
p = 1 / (1 + np.exp(-sess.run(None, {"input_image": x})[0][0, 0]))
m = Image.fromarray((np.clip(p, 0, 1) * 255).astype(np.uint8)).resize(src.size, Image.LANCZOS)
m = m.point(lambda v: 0 if v < 40 else (255 if v > 215 else int((v - 40) / 175 * 255))).filter(ImageFilter.GaussianBlur(1.0))
m.save(D + "mask_main.png")

g = ImageOps.grayscale(src)
g = ImageOps.autocontrast(g, cutoff=0.8)
g = ImageEnhance.Contrast(g).enhance(1.12)
g = g.point(lambda v: int(255 * ((v / 255) ** 0.85)))
g = g.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
arr = np.asarray(g).astype(np.float32) + np.random.default_rng(5).normal(0, 6, g.size[::-1])
person = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGB")
person = ImageEnhance.Color(src).enhance(0.92)
person = ImageEnhance.Contrast(person).enhance(1.05)

pad = 40
big = Image.new("L", (src.width + pad * 2, src.height + pad * 2), 0); big.paste(m, (pad, pad))
outline = big.filter(ImageFilter.MaxFilter(25)).filter(ImageFilter.GaussianBlur(2)).point(lambda v: 255 if v > 110 else int(v * 2.3))
canvas = Image.new("RGBA", big.size, (0, 0, 0, 0))
canvas.paste(Image.new("RGBA", big.size, (255, 255, 255, 255)), (0, 0), outline)
pl = Image.new("RGBA", big.size, (0, 0, 0, 0)); pl.paste(person, (pad, pad))
canvas.paste(pl, (0, 0), big)
bbox = canvas.getbbox(); canvas = canvas.crop((bbox[0], bbox[1], bbox[2], canvas.height - pad))
canvas.thumbnail((1100, 1400), Image.LANCZOS)
canvas.save(D + "sticker_c.png", optimize=True)

s = Image.open(second).convert("RGB")
side = int(s.width * 0.70); x0 = int(s.width * 0.20); y0 = int(s.height * 0.16)
pol = s.crop((x0, y0, x0 + side, y0 + side)).resize((560, 560), Image.LANCZOS)
pol = ImageEnhance.Color(pol).enhance(0.9)
ImageOps.grayscale(ImageOps.autocontrast(pol, cutoff=0.8)).convert("RGB").save(D + "snap_g.jpg", quality=86)
print("ok", canvas.size)
