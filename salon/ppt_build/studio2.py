# 더 자연스럽게: 실제 스튜디오 배경(디자이너 사진에서 인물만 지운 것) + 조명 톤 맞추기 + 경계 다듬기 + 입자
import numpy as np, onnxruntime as ort
from PIL import Image, ImageFilter, ImageEnhance
D = "/tmp/claude-0/-home-user-daily-cards/06ef2264-b127-5a98-911e-16c520eb086c/scratchpad/minju/"
P = D + "../photos/"
sess = ort.InferenceSession(D + "u2net_human_seg.onnx", providers=["CPUExecutionProvider"])

def seg(im):
    x = np.asarray(im.convert("RGB").resize((320, 320), Image.LANCZOS)).astype(np.float32) / 255.0
    x = ((x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]).transpose(2, 0, 1)[None].astype(np.float32)
    p = sess.run(None, {sess.get_inputs()[0].name: x})[0][0, 0]
    p = (p - p.min()) / (p.max() - p.min() + 1e-8)
    return np.asarray(Image.fromarray((p * 255).astype(np.uint8)).resize(im.size, Image.LANCZOS)).astype(np.float32) / 255

def blur(a, r):
    a = np.asarray(a, np.float32); mx = float(a.max()) or 1.0
    im = Image.fromarray(np.clip(a / mx * 65535, 0, 65535).astype(np.uint16), mode="I;16").convert("I")
    # PIL은 16비트 블러를 지원하지 않아 상·하위 8비트로 나눠 블러
    hi = Image.fromarray((np.asarray(im) >> 8).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
    lo = Image.fromarray((np.asarray(im) & 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
    return (np.asarray(hi).astype(np.float32) * 256 + np.asarray(lo)) / 65535 * mx

# 1) 실제 스튜디오 배경 만들기: 디자이너(지유) 사진에서 인물을 지우고 주변 배경으로 메우기
ref = Image.open(P + "d6.jpg").convert("RGB")
ref = ref.resize((1100, int(1100 * ref.height / ref.width)), Image.LANCZOS)
rm = seg(ref)
keep = (blur(rm, 6) < 0.05).astype(np.float32)
ra = np.asarray(ref).astype(np.float32)
fill = np.zeros_like(ra)
for c in range(3):
    num = blur(ra[..., c] * keep, 140); den = blur(keep, 140) + 1e-6
    fill[..., c] = num / den
bgref = ra * keep[..., None] + fill * (1 - keep[..., None])
bgref = np.stack([blur(bgref[..., c], 18) for c in range(3)], -1)          # 매끈한 무지 배경
grain = np.random.default_rng(3).normal(0, 3.0, bgref.shape[:2])[..., None]
bgref = np.clip(bgref + grain, 0, 255)

# 2) 인물 분리 + 색 보정 (주황 조명 → 중성, 밝기 올리고 차분하게)
src = Image.open(D + "in.webp").convert("RGB")
W, H = src.size
m = seg(src)
a = np.asarray(src).astype(np.float32)
body = m > 0.7
# 셔츠(밝은 영역)를 기준으로 화이트밸런스: 크림색 셔츠를 오프화이트로
bright = body & (a.mean(-1) > np.percentile(a[body].mean(-1), 80))
ref_white = a[bright].mean(0)
gain = ref_white.mean() / ref_white
gain = 1 + (gain - 1) * 0.75
a = a * gain
a = a * 1.10 + 6                                                         # 노출 +
img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
img = ImageEnhance.Color(img).enhance(0.80)
img = ImageEnhance.Contrast(img).enhance(1.04)
img = img.filter(ImageFilter.SMOOTH)                                     # 폰 노이즈 살짝 정리
a = np.asarray(img).astype(np.float32)

# 3) 배경을 인물 크기에 맞춰 배치
bg = Image.fromarray(bgref.astype(np.uint8)).resize((W, int(W * bgref.shape[0] / bgref.shape[1])), Image.LANCZOS)
bg = np.asarray(bg.crop((0, 0, W, H))).astype(np.float32)

# 4) 경계 다듬기: 알파를 약간 좁히고 부드럽게, 가장자리 색에 배경빛 섞기(라이트 랩)
al = np.clip((m - 0.15) / 0.75, 0, 1)
al = blur(al, 1.6)
edge = np.clip(1 - np.abs(al - 0.5) * 2, 0, 1)                          # 경계일수록 1
wrap = np.stack([blur(bg[..., c], 12) for c in range(3)], -1)
a = a * (1 - 0.35 * edge[..., None]) + wrap * (0.35 * edge[..., None])
out = a * al[..., None] + bg * (1 - al[..., None])

# 5) 전체에 같은 입자 + 아주 약한 비네트
out += np.random.default_rng(11).normal(0, 2.4, out.shape[:2])[..., None]
yy, xx = np.mgrid[0:H, 0:W]
v = 1 - 0.10 * (((xx - W * 0.55) / W) ** 2 + ((yy - H * 0.4) / H) ** 2) * 2.2
out = np.clip(out * v[..., None], 0, 255).astype(np.uint8)
res = Image.fromarray(out)

th = H - 24; tw = int(th * 3 / 4); x0 = W - 66 - tw
res = res.crop((x0, 0, x0 + tw, th))
res.save(D + "minju_studio2.jpg", quality=92)
res.resize((600, 800), Image.LANCZOS).save(D + "minju2_600.jpg", quality=86)

# 비교 이미지: 원본 | 1차 | 2차 | 디자이너 참고
o = src.crop((x0, 0, x0 + tw, th))
tiles = [o, Image.open(D + "minju_studio.jpg"), res, Image.open(P + "d6.jpg").convert("RGB")]
h = 620; row = [t.resize((int(t.width * h / t.height), h), Image.LANCZOS) for t in tiles]
sheet = Image.new("RGB", (sum(t.width for t in row) + 30, h), "white")
x = 0
for t in row: sheet.paste(t, (x, 0)); x += t.width + 10
sheet.save(D + "compare.jpg", quality=90)
print("ok")
