# 셀카 → 디자이너 프로필처럼: 회색 스튜디오 배경 + 차분한 색감 + 3:4 상반신
import sys
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
D = "/tmp/claude-0/-home-user-daily-cards/06ef2264-b127-5a98-911e-16c520eb086c/scratchpad/minju/"

src = Image.open(D + "in.webp").convert("RGB")
cut = Image.open(D + "cut.png").convert("RGBA")          # rembg 결과 (투명 배경)
alpha = cut.split()[3].filter(ImageFilter.GaussianBlur(1.2))

# 1) 인물 색 보정: 나무 조명의 주황 기운 빼고(화이트밸런스), 채도 낮추고, 살짝 대비
a = np.asarray(src).astype(np.float32)
m = np.asarray(alpha).astype(np.float32) / 255.0
w = m > 0.6
mean = a[w].mean(axis=0)
gray = mean.mean()
a = a * (gray / mean) * 0.55 + a * 0.45                  # 절반만 중립화 (피부톤 유지)
img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
img = ImageEnhance.Color(img).enhance(0.72)
img = ImageEnhance.Contrast(img).enhance(1.06)
img = ImageEnhance.Brightness(img).enhance(1.03)

# 2) 스튜디오 배경: 디자이너 사진처럼 가운데 밝고 가장자리 어두운 회색 비네트
W, H = src.size
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
cx, cy = W * 0.5, H * 0.32
r = np.sqrt(((xx - cx) / (W * 0.9)) ** 2 + ((yy - cy) / (H * 0.9)) ** 2)
light, dark = np.array([214, 212, 210], np.float32), np.array([150, 149, 148], np.float32)
t = np.clip(r, 0, 1)[..., None] ** 1.4
bg = light * (1 - t) + dark * t
noise = np.random.default_rng(7).normal(0, 2.2, (H, W, 1))  # 사진 같은 미세 입자
bg = Image.fromarray(np.clip(bg + noise, 0, 255).astype(np.uint8))

# 3) 합성 + 인물 아래 아주 옅은 그림자
shadow = Image.new("L", (W, H), 0)
shadow.paste(alpha.point(lambda v: int(v * 0.35)), (14, 18))
shadow = shadow.filter(ImageFilter.GaussianBlur(28))
bg = Image.composite(Image.new("RGB", (W, H), (110, 108, 106)), bg, shadow)
out = Image.composite(img, bg, alpha)

# 4) 3:4로 자르기 (머리 위 여백 조금)
th = H - 24; tw = int(th * 3 / 4)
x0 = W - 66 - tw; y0 = 0          # 오른쪽 끝 나무 배경이 걸친 부분을 잘라 냄
out = out.crop((x0, y0, x0 + tw, y0 + th))
out.save(D + "minju_studio.jpg", quality=92)
out.resize((600, 800), Image.LANCZOS).save(D + "minju_600.jpg", quality=86)
print(out.size)
