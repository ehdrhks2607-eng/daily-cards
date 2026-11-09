# 디자이너 사진을 웹 화면과 같은 정사각형(상반신 확대)으로 자르고, 파트너용 빈 사진(실루엣) 만들기
from PIL import Image, ImageDraw
SP = "/tmp/claude-0/-home-user-daily-cards/06ef2264-b127-5a98-911e-16c520eb086c/scratchpad/"
for i in range(1, 8):
    im = Image.open(f"{SP}photos/d{i}.jpg").convert("RGB")
    w, h = im.size
    h = min(h, int(w * 4 / 3))          # 웹과 같은 3:4 상단 크롭
    side = int(w / 1.5)                 # 150% 확대
    x0 = (w - side) // 2
    y0 = int((h - side) * 0.03)
    sq = im.crop((x0, y0, x0 + side, y0 + side)).resize((700, 700), Image.LANCZOS)
    sq.save(f"{SP}ppt/d{i}.jpg", quality=88)

S = 600
im = Image.new("RGB", (S, int(S * 1.3)), (255, 253, 249))
d = ImageDraw.Draw(im)
c = (214, 203, 190)
d.ellipse((S*0.33, S*0.25, S*0.67, S*0.59), fill=c)
d.ellipse((S*0.14, S*0.68, S*0.86, S*1.4), fill=c)
im = im.crop((0, 0, S, int(S * 1.3)))
im.save(f"{SP}ppt/empty.png")
print("ok")
