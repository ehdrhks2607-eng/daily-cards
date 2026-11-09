# U2Net(사람 분할) 모델로 배경 제거 → cut.png (투명 배경)
import numpy as np, onnxruntime as ort
from PIL import Image
D = "/tmp/claude-0/-home-user-daily-cards/06ef2264-b127-5a98-911e-16c520eb086c/scratchpad/minju/"
src = Image.open(D + "in.webp").convert("RGB")
x = np.asarray(src.resize((320, 320), Image.LANCZOS)).astype(np.float32) / 255.0
x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
x = x.transpose(2, 0, 1)[None].astype(np.float32)
sess = ort.InferenceSession(D + "u2net_human_seg.onnx", providers=["CPUExecutionProvider"])
pred = sess.run(None, {sess.get_inputs()[0].name: x})[0][0, 0]
pred = (pred - pred.min()) / (pred.max() - pred.min() + 1e-8)
mask = Image.fromarray((pred * 255).astype(np.uint8)).resize(src.size, Image.LANCZOS)
out = src.copy(); out.putalpha(mask)
out.save(D + "cut.png")
mask.save(D + "mask.png")
print("ok", src.size)
