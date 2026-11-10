# 디자이너 인터뷰를 6문항 틀로 통일 + 최고·선우 추가
import base64, io, json
from PIL import Image
SP = "/tmp/claude-0/-home-user-daily-cards/06ef2264-b127-5a98-911e-16c520eb086c/scratchpad/"
M = SP + "mag/"

def photo(n):
    im = Image.open(SP + f"photos/d{n}.jpg").convert("RGB"); im.thumbnail((1100, 1500))
    b = io.BytesIO(); im.save(b, "JPEG", quality=84, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()

Q = ["일할 때 이렇게 해 주면 좋아요", "일할 때 이렇게 하면 싫어요", "피드백은 이렇게", "좋아하는 칭찬 스타일"]
def prof(n, one, good, bad, fb, praise, cheer=""):
    return {"photo": photo(n), "oneQ": "나를 한마디로 표현하면?", "oneA": one,
            "work": [[Q[0], good], [Q[1], bad]], "about": [[Q[2], fb], [Q[3], praise]],
            "cheerQ": "신입 파트너에게 한마디", "cheer": cheer}

P = {
  "보배": prof(1, "마음도 손도 바쁨", "\"도와드릴 거 있을까요?\"\n물어봐 주기",
              "바쁜데 찾아야 할 때\n고객 3분 이상이면 옆에 있어 줘", "둘만 있을 때 은밀하게~",
              "귀엽다고 해 주기,\n디테일하게 말해 주기"),
  "최고": prof(3, "귀요미", "알잘딱깔센", "배려, 매너 없는 행동", "그냥 솔직하게", "고생했다", "나 무서워하지 마"),
  "선우": prof(5, "천사", "고객님께는 친절하고 정확하게,\n매장 식구끼리는 화목하게",
              "건성건성 대충하는, 힘없이\n하기 싫은 티 내면서 고객님 대하는 거",
              "1:1로 대화를 통해서", "무엇이든 칭찬이면 좋아요", "가족같이 화목하게 잘해 봐요 😊"),
}
json.dump(P, open(M + "profiles_designers.json", "w", encoding="utf-8"), ensure_ascii=False)

# assemble.py: 보배 하나만 넣던 부분을 여러 명으로
asm = open(M + "assemble.py", encoding="utf-8").read()
old = '''PROFILE_JSON = json.load(open(M + "profile_bobae.json", encoding="utf-8"))
k = '"name": "보배", "mbti": "ESTJ"'
assert s.count(k) == 1
s = s.replace(k, k + ', "profile": ' + json.dumps(PROFILE_JSON, ensure_ascii=False))'''
new = '''for _n, _p in json.load(open(M + "profiles_designers.json", encoding="utf-8")).items():
    k = '"name": "%s", "mbti": ' % _n
    assert s.count(k) == 1, _n
    s = s.replace(k, '"profile": ' + json.dumps(_p, ensure_ascii=False) + ', ' + k)'''
if old in asm:
    asm = asm.replace(old, new); open(M + "assemble.py", "w", encoding="utf-8").write(asm)

# render.js: 번호 대신 MBTI, 쪽 번호 대신 이름, 한마디 띠 추가
js = open(M + "render.js", encoding="utf-8").read()
a = js.index("function profilePage(i){"); b = js.index("function partnerPage(i){")
js = js[:a] + r'''function profilePage(i){
  const d = data.designers[i], pr = d.profile, base = `designers.${i}.profile`, mg = data.magazine;
  const qa = (path, q, a, mark) => `<div class="qa"><div class="q">${mark ? `<i>${mark}</i>` : "Q."}${ed(path + ".0", q, "", "span")}</div>${ed(path + ".1", a, "a")}</div>`;
  const code = mbtiCode(d.mbti) || "";
  return `<section class="page prof">
    ${photo(`${base}.photo`, "hero")}
    <div class="run"><span class="m">MAISON<small>de idHAIR</small></span><span class="sec">THE CAST · ${esc(d.name)}</span></div>
    <div class="no"><small>THE CAST</small>${esc(code)}</div>
    <div class="quote">${ed(`${base}.oneQ`, pr.oneQ, "label")}${ed(`${base}.oneA`, pr.oneA.replace(/\s+/g, "\n"), "a")}</div>
    <div class="art">
      <div class="name">
        ${ed(`designers.${i}.name`, d.name, "pnm")}
        <div class="meta"><span class="kk">INTERVIEW</span>${ed(`designers.${i}.role`, d.role, "rl", "span")}${ed(`designers.${i}.mbti`, d.mbti, "mb", "span")}</div>
      </div>
      <div class="iv">
        <div class="col"><h3>HOW TO WORK WITH ME</h3>${pr.work.map((w,j)=>qa(`${base}.work.${j}`, w[0], w[1], j % 2 ? "✕" : "○")).join("")}</div>
        <div class="col"><h3>ABOUT ME</h3>${pr.about.map((a,j)=>qa(`${base}.about.${j}`, a[0], a[1], "")).join("")}</div>
      </div>
      ${pr.cheer ? `<div class="pcheer">${ed(`${base}.cheerQ`, pr.cheerQ, "label")}${ed(`${base}.cheer`, pr.cheer, "c")}</div>` : ""}
    </div>
    <div class="folio"><span>MAISON · ${esc(mg.issue)}</span><b>THE CAST · ${esc(d.name)}</b></div>
  </section>`;
}

''' + js[b:]
open(M + "render.js", "w", encoding="utf-8").write(js)

head = open(M + "head.html", encoding="utf-8").read()
if ".pcheer" not in head:
    head = head.replace("/* 편집 모드 */", """.prof .no { font-size:110px; }
.prof .iv h3 { margin-bottom:2px; }
.prof .qa .a { font-size:18px; }
.prof .pcheer { display:flex; align-items:center; justify-content:space-between; gap:16px; background:var(--ink); color:#fff; padding:12px 20px; margin-top:14px; }
.prof .pcheer .label { color:#fff; }
.prof .pcheer .c { font-family:var(--title); font-size:28px; color:#E7D3E2; text-align:right; }
/* 편집 모드 */""", 1)
    open(M + "head.html", "w", encoding="utf-8").write(head)
print("ok")
