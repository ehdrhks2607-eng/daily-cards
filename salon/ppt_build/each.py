# 사진마다 ① 흑백 스티커(투명 PNG + 모브 배경 JPG) ② 컬러 폴라로이드(JPG)
import sys, numpy as np, onnxruntime as ort
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw, ImageFont
D = "/tmp/claude-0/-home-user-daily-cards/06ef2264-b127-5a98-911e-16c520eb086c/scratchpad/minju/"
OUT = "/home/user/daily-cards/salon/partner_demo/"
sess = ort.InferenceSession(D + "birefnet.onnx", providers=["CPUExecutionProvider"])
FONT = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 26)

def mask(src):
    x = np.asarray(src.resize((1024, 1024), Image.LANCZOS)).astype(np.float32) / 255.0
    x = ((x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]).transpose(2, 0, 1)[None].astype(np.float32)
    p = 1 / (1 + np.exp(-sess.run(None, {"input_image": x})[0][0, 0]))
    m = Image.fromarray((np.clip(p, 0, 1) * 255).astype(np.uint8)).resize(src.size, Image.LANCZOS)
    return m.point(lambda v: 0 if v < 40 else (255 if v > 215 else int((v - 40) / 175 * 255))).filter(ImageFilter.GaussianBlur(1.0))

def sticker(src, seed):
    m = mask(src)
    g = ImageOps.autocontrast(ImageOps.grayscale(src), cutoff=0.8)
    g = ImageEnhance.Contrast(g).enhance(1.12).point(lambda v: int(255 * ((v / 255) ** 0.85)))
    g = g.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    arr = np.asarray(g).astype(np.float32) + np.random.default_rng(seed).normal(0, 6, g.size[::-1])
    person = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGB")
    pad = 40
    big = Image.new("L", (src.width + pad * 2, src.height + pad * 2), 0); big.paste(m, (pad, pad))
    outline = big.filter(ImageFilter.MaxFilter(25)).filter(ImageFilter.GaussianBlur(2)).point(lambda v: 255 if v > 110 else int(v * 2.3))
    c = Image.new("RGBA", big.size, (0, 0, 0, 0))
    c.paste(Image.new("RGBA", big.size, (255, 255, 255, 255)), (0, 0), outline)
    pl = Image.new("RGBA", big.size, (0, 0, 0, 0)); pl.paste(person, (pad, pad)); c.paste(pl, (0, 0), big)
    b = c.getbbox(); c = c.crop((b[0], b[1], b[2], c.height - pad))
    c.thumbnail((1400, 1800), Image.LANCZOS)
    return c

def on_mauve(st):
    W, H = 1080, 1350
    bg = Image.new("RGB", (W, H), (139, 108, 132))
    s = st.copy(); s.thumbnail((int(W * 0.9), int(H * 0.88)), Image.LANCZOS)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x, y = (W - s.width) // 2, H - s.height
    shadow = Image.new("L", (W, H), 0); shadow.paste(s.split()[3].point(lambda v: int(v * 0.35)), (x + 10, y + 16))
    bg.paste((60, 45, 56), (0, 0, W, H), shadow.filter(ImageFilter.GaussianBlur(18)))
    bg.paste(s, (x, y), s)
    return bg

def polaroid(src, box, label):
    s = src.crop(box).resize((900, 900), Image.LANCZOS)
    s = ImageEnhance.Color(s).enhance(0.9)
    fr = Image.new("RGB", (900 + 70, 900 + 200), "white"); fr.paste(s, (35, 35))
    d = ImageDraw.Draw(fr); w = d.textlength(label, font=FONT)
    d.text(((fr.width - w) / 2, 900 + 95), label, fill=(111, 107, 103), font=FONT)
    return fr

U = [sys.argv[2]]; START = int(sys.argv[1])
for i, path in enumerate(U, START):
    src = Image.open(path).convert("RGB")
    st = sticker(src, i)
    st.save(OUT + f"민주_{i}_흑백스티커.png", optimize=True)
    on_mauve(st).save(OUT + f"민주_{i}_흑백스티커_모브배경.jpg", quality=92)
    W, H = src.size; side = int(min(W, H) * 0.72)
    cx, cy = (int(W * 0.47), int(H * 0.42)) if i == 1 else (int(W * 0.50), int(H * 0.45))
    box = (max(0, cx - side // 2), max(0, cy - side // 2), 0, 0)
    box = (box[0], box[1], box[0] + side, box[1] + side)
    polaroid(src, box, "UNFILTERED").save(OUT + f"민주_{i}_폴라로이드.jpg", quality=92)
    print("done", i)
