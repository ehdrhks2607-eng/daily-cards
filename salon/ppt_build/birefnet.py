# BiRefNet(인물) — 머리카락 경계가 정교한 배경 제거 → mask_bi.png
import sys, numpy as np, onnxruntime as ort
from PIL import Image
D = "/tmp/claude-0/-home-user-daily-cards/06ef2264-b127-5a98-911e-16c520eb086c/scratchpad/minju/"
name = sys.argv[1] if len(sys.argv) > 1 else "in.webp"
src = Image.open(D + name).convert("RGB")
x = np.asarray(src.resize((1024, 1024), Image.LANCZOS)).astype(np.float32) / 255.0
x = ((x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]).transpose(2, 0, 1)[None].astype(np.float32)
sess = ort.InferenceSession(D + "birefnet.onnx", providers=["CPUExecutionProvider"])
p = sess.run(None, {"input_image": x})[0][0, 0]
p = 1 / (1 + np.exp(-p))
m = Image.fromarray((np.clip(p, 0, 1) * 255).astype(np.uint8)).resize(src.size, Image.LANCZOS)
m.save(D + "mask_bi.png")
print("ok")
