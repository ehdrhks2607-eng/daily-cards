// A4 세로 10장 PPT — salon/a4_pages.html 의 기본 내용(DEFAULT)을 그대로 읽어서 만든다
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const SP = __dirname;
const SRC = "/home/user/daily-cards/salon/a4_pages.html";
const OUT = process.argv[2] || path.join(SP, "salon.pptx");

const html = fs.readFileSync(SRC, "utf8");
const m = html.match(/const DEFAULT = (\{[\s\S]*?\n\});/);
const data = eval("(" + m[1] + ")");

const FONT = "Malgun Gothic";
const K = { ink: "4A3A2C", sub: "8C7A68", accent: "C4835A", accent2: "8AA37B", soft: "F3E7DA",
            panel: "FFFDF9", paper: "F8F2EA", line: "E2CFBB", tag: "E8EFE2", shadow: "D8C2AA", white: "FFFFFF" };
const W = 8.27, H = 11.69;
const PX = 0.55, PY = 0.6, PW = 7.17, PH = 10.35;
const CX = PX + 0.45, CW = PW - 0.9, CTOP = PY + 1.6, CBOT = PY + PH - 0.4;

const pres = new pptxgen();
pres.defineLayout({ name: "A4P", width: W, height: H });
pres.layout = "A4P";
pres.theme = { headFontFace: FONT, bodyFontFace: FONT };
pres.title = "매장 사용 설명서";
pres.author = data.store.name;

pres.defineSlideMaster({
  title: "A4_PAGE",
  background: { color: K.paper },
  objects: [
    { text: { text: data.store.name + " · 매장 사용 설명서",
              options: { x: PX, y: H - 0.55, w: 5, h: 0.3, fontFace: FONT, fontSize: 9, bold: true, color: K.sub, margin: 0 } } },
  ],
  slideNumber: { x: W - PX - 0.6, y: H - 0.55, w: 0.6, h: 0.3, fontFace: FONT, fontSize: 9, bold: true, color: K.sub, align: "right" },
});

const T = (s, text, o) => s.addText(text, Object.assign({ fontFace: FONT, color: K.ink, margin: 0, isTextBox: true, valign: "top" }, o));
const RR = (s, o) => s.addShape(pres.shapes.ROUNDED_RECTANGLE, Object.assign({ rectRadius: 0.12 }, o));
const dash = (s, x, y, w) => s.addShape(pres.shapes.LINE, { x, y, w, h: 0, line: { color: K.line, width: 1.25, dashType: "dash" } });

function page(label, title, fill) {
  const s = pres.addSlide({ masterName: "A4_PAGE" });
  RR(s, { x: PX + 0.1, y: PY + 0.1, w: PW, h: PH, rectRadius: 0.28, fill: { color: K.shadow }, line: { color: K.shadow }, objectName: "panel shadow" });
  RR(s, { x: PX, y: PY, w: PW, h: PH, rectRadius: 0.28, fill: { color: fill || K.panel }, line: { color: K.ink, width: 2.25 }, objectName: "panel" });
  T(s, label, { x: PX + 0.35, y: PY + 0.2, w: 3, h: 0.25, fontSize: 9, bold: true, charSpacing: 2, color: fill ? K.white : K.sub });
  for (let i = 0; i < 3; i++)
    RR(s, { x: PX + PW - 0.35 - 0.22 - i * 0.3, y: PY + 0.2, w: 0.2, h: 0.2, rectRadius: 0.04, fill: { color: fill ? K.white : K.panel }, line: { color: K.ink, width: 1.25 } });
  if (title) {
    s.addShape(pres.shapes.OVAL, { x: CX, y: PY + 0.83, w: 0.2, h: 0.2, fill: { color: K.accent2 }, line: { color: K.ink, width: 1.5 } });
    T(s, title, { x: CX + 0.32, y: PY + 0.6, w: CW - 0.3, h: 0.65, fontSize: 30, bold: true, valign: "middle" });
  }
  return s;
}

/* 1. 표지 */
{
  const s = page("WELCOME", null, K.accent);
  T(s, data.store.hello, { x: CX, y: PY + 0.75, w: CW, h: 1.0, fontSize: 20, bold: true, color: K.white, lineSpacingMultiple: 1.2 });
  T(s, data.store.name.replace(/ (?=[^ ]*$)/, "\n"), { x: CX, y: PY + 3.0, w: CW, h: 1.9, fontSize: 40, bold: true, color: K.white, valign: "bottom", lineSpacingMultiple: 1.05 });
  T(s, data.store.title, { x: CX, y: PY + 5.05, w: CW, h: 2.9, fontSize: 70, bold: true, color: K.white,
                           outline: { size: 1.5, color: K.ink }, lineSpacingMultiple: 0.95 });
  T(s, "✂   ♥", { x: CX, y: PY + PH - 1.6, w: 4, h: 1.0, fontSize: 52, color: K.white, valign: "bottom" });
}

/* 2. 매장 정보 */
{
  const st = data.store;
  const s = page("STORE INFO", "우리 매장 정보");
  RR(s, { x: CX, y: CTOP, w: 2.8, h: 0.8, rectRadius: 0.15, fill: { color: K.soft }, line: { color: K.ink, width: 2 } });
  T(s, st.open, { x: CX, y: CTOP, w: 2.8, h: 0.8, fontSize: 28, bold: true, align: "center", valign: "middle" });
  const rows = [["주소", st.addr], ["매장 번호", st.tel], ["대표", st.owner], ["영업시간", st.hours], ["휴무", st.off], ["와이파이", st.wifi]];
  const top = CTOP + 1.25, step = (CBOT - top) / rows.length;
  rows.forEach(([k, v], i) => {
    const y = top + i * step;
    RR(s, { x: CX, y, w: 1.45, h: 0.45, rectRadius: 0.1, fill: { color: K.accent }, line: { color: K.accent } });
    T(s, k, { x: CX, y, w: 1.45, h: 0.45, fontSize: 14, bold: true, color: K.white, align: "center", valign: "middle" });
    T(s, v, { x: CX + 1.75, y: y + 0.02, w: CW - 1.75, h: step - 0.3, fontSize: 19, lineSpacingMultiple: 1.15 });
    if (i < rows.length - 1) dash(s, CX + 1.75, y + step - 0.18, CW - 1.75);
  });
}

/* 3. 디자이너 */
{
  const s = page("DESIGNER", "디자이너 가족들");
  const ds = data.designers, cols = 3, gap = 0.22, cardW = 1.92, ph = cardW - 0.2;
  const cardH = 0.1 + ph + 0.1 + 0.42 + 0.34 + 0.12;
  const rows = Math.ceil(ds.length / cols);
  const rowGap = Math.max(0.12, (CBOT + 0.2 - CTOP - rows * cardH) / Math.max(rows - 1, 1));
  ds.forEach((d, i) => {
    const r = Math.floor(i / cols), inRow = Math.min(cols, ds.length - r * cols), c = i % cols;
    const rowW = inRow * cardW + (inRow - 1) * gap;
    const x = CX + (CW - rowW) / 2 + c * (cardW + gap), y = CTOP + r * (cardH + rowGap);
    RR(s, { x, y, w: cardW, h: cardH, rectRadius: 0.14, fill: { color: K.soft }, line: { color: K.ink, width: 1.75 }, objectName: "card " + d.name });
    s.addImage({ path: path.join(SP, `d${({보배:1,청림:2,최고:3,승철:4,선우:5,지유:6,이윤:7})[d.name] || i + 1}.jpg`), x: x + 0.1, y: y + 0.1, w: ph, h: ph, altText: `${d.name} ${d.role}` });
    s.addShape(pres.shapes.RECTANGLE, { x: x + 0.1, y: y + 0.1, w: ph, h: ph, fill: { type: "none" }, line: { color: K.ink, width: 1.25 } });
    T(s, [{ text: d.name, options: { fontSize: 18, bold: true } }, { text: "  " + d.role, options: { fontSize: 10.5, bold: true, color: K.sub } }],
      { x, y: y + 0.1 + ph + 0.08, w: cardW, h: 0.42, align: "center", valign: "middle" });
    const mb = d.mbti || "", long = mb.length > 11, mw = Math.min(cardW - 0.15, 0.4 + mb.length * (long ? 0.085 : 0.1));
    RR(s, { x: x + (cardW - mw) / 2, y: y + 0.1 + ph + 0.52, w: mw, h: 0.28, rectRadius: 0.14, fill: { color: K.white }, line: { color: K.accent, width: 1.25 } });
    T(s, mb, { x: x + (cardW - mw) / 2, y: y + 0.1 + ph + 0.52, w: mw, h: 0.28, fontSize: long ? 8.5 : 10.5, bold: true, color: K.accent, align: "center", valign: "middle" });
  });
}

/* 4. 파트너 */
{
  const s = page("PARTNER", "파트너 가족들");
  const ps = data.partners, cols = 3, gap = 0.2, cardW = (CW - gap * (cols - 1)) / cols, pw = cardW - 0.2, ph = pw * 1.3;
  const cardH = 0.1 + ph + 0.1 + 0.4 + 0.3 + 0.12;
  const rows = Math.ceil(ps.length / cols);
  const rowGap = Math.min(0.5, (CBOT - CTOP - rows * cardH) / Math.max(rows - 1, 1));
  ps.forEach((p, i) => {
    const r = Math.floor(i / cols), c = i % cols, x = CX + c * (cardW + gap), y = CTOP + r * (cardH + rowGap);
    RR(s, { x, y, w: cardW, h: cardH, rectRadius: 0.14, fill: { color: K.soft }, line: { color: K.ink, width: 1.75 } });
    s.addImage({ path: path.join(SP, "empty.png"), x: x + 0.1, y: y + 0.1, w: pw, h: ph, altText: "파트너 사진 자리" });
    s.addShape(pres.shapes.RECTANGLE, { x: x + 0.1, y: y + 0.1, w: pw, h: ph, fill: { type: "none" }, line: { color: K.ink, width: 1.25 } });
    T(s, p.name, { x, y: y + 0.1 + ph + 0.1, w: cardW, h: 0.4, fontSize: 17, bold: true, align: "center", valign: "middle" });
    T(s, p.note, { x, y: y + 0.1 + ph + 0.5, w: cardW, h: 0.3, fontSize: 10.5, color: K.sub, align: "center", valign: "middle" });
  });
}

/* 5. 첫날 안내 */
{
  const f = data.firstday, s = page("FIRST DAY", "파트너 첫날 안내");
  [["출근", f.time], ["복장", f.dress], ["준비물", f.bring]].forEach(([k, v], i) => {
    const y = CTOP + i * 0.95;
    RR(s, { x: CX, y, w: 1.0, h: 0.42, rectRadius: 0.1, fill: { color: K.accent }, line: { color: K.accent } });
    T(s, k, { x: CX, y, w: 1.0, h: 0.42, fontSize: 13, bold: true, color: K.white, align: "center", valign: "middle" });
    T(s, v, { x: CX + 1.25, y: y + 0.03, w: CW - 1.25, h: 0.85, fontSize: 17, lineSpacingMultiple: 1.15 });
  });
  const sy = CTOP + 3.05;
  T(s, "첫날 하루 흐름", { x: CX, y: sy, w: 4, h: 0.5, fontSize: 20, bold: true, color: K.accent, valign: "middle" });
  const ty = sy + 0.85, step = (CBOT - ty - 0.3) / Math.max(f.flow.length - 1, 1);
  s.addShape(pres.shapes.LINE, { x: CX + 0.16, y: ty, w: 0, h: step * (f.flow.length - 1) + 0.2, line: { color: K.line, width: 2.5, dashType: "dash" } });
  f.flow.forEach((t, i) => {
    const y = ty + i * step;
    s.addShape(pres.shapes.OVAL, { x: CX + 0.05, y: y - 0.01, w: 0.24, h: 0.24, fill: { color: K.accent2 }, line: { color: K.ink, width: 1.5 } });
    T(s, t, { x: CX + 0.55, y: y - 0.1, w: CW - 0.55, h: 0.45, fontSize: 18, valign: "middle" });
  });
}

/* 6. 1주일 OJT */
{
  const s = page("TO DO", "두근두근 1주일 OJT");
  RR(s, { x: CX, y: CTOP - 0.1, w: CW, h: 1.2, rectRadius: 0.14, fill: { color: K.soft }, line: { color: K.soft } });
  T(s, data.todoNote || "", { x: CX + 0.25, y: CTOP, w: CW - 0.5, h: 1.0, fontSize: 14, color: K.sub, lineSpacingMultiple: 1.25, valign: "middle" });
  const top = CTOP + 1.45, step = (CBOT - top) / data.todo.length;
  data.todo.forEach((t, i) => {
    const y = top + i * step, [a, b] = t.split("\n");
    RR(s, { x: CX, y: y + 0.05, w: 0.75, h: 0.45, rectRadius: 0.1, fill: { color: K.soft }, line: { color: K.ink, width: 1.75 } });
    T(s, (i + 1) + "일", { x: CX, y: y + 0.05, w: 0.75, h: 0.45, fontSize: 14, bold: true, align: "center", valign: "middle" });
    T(s, [{ text: a, options: { fontSize: 17, breakLine: !!b } }].concat(b ? [{ text: b, options: { fontSize: 16, color: K.accent, bold: true } }] : []),
      { x: CX + 1.0, y: y + 0.02, w: CW - 1.0, h: step - 0.2, lineSpacingMultiple: 1.2 });
    if (i < data.todo.length - 1) dash(s, CX, y + step - 0.12, CW);
  });
}

/* 7. 고객님께 멘트하기 (한 장) */
{
  const tk = data.talk, s = page("TALK", tk.title);
  const cols = 2, gap = 0.2, cw = (CW - gap) / cols, bottom = CBOT - 0.85;
  const rows = Math.ceil(tk.parts.length / cols), ch = (bottom - CTOP - gap * (rows - 1)) / rows;
  tk.parts.forEach((pt, i) => {
    const x = CX + (i % cols) * (cw + gap), y = CTOP + Math.floor(i / cols) * (ch + gap);
    RR(s, { x, y, w: cw, h: ch, rectRadius: 0.16, fill: { color: K.soft }, line: { color: K.ink, width: 1.75 }, objectName: "talk " + pt.when });
    const pw = Math.min(cw - 0.3, 0.45 + pt.when.length * 0.15);
    RR(s, { x: x + 0.15, y: y + 0.14, w: pw, h: 0.34, rectRadius: 0.17, fill: { color: K.accent2 }, line: { color: K.ink, width: 1.25 } });
    T(s, pt.when, { x: x + 0.15, y: y + 0.14, w: pw, h: 0.34, fontSize: 12, bold: true, color: K.white, align: "center", valign: "middle" });
    let by = y + 0.6;
    pt.lines.forEach((l) => {
      const n = l.split("\n").length, bh = 0.12 + n * 0.21;
      RR(s, { x: x + 0.15, y: by, w: cw - 0.3, h: bh, rectRadius: 0.08, fill: { color: K.panel }, line: { color: K.line, width: 1 } });
      T(s, l, { x: x + 0.24, y: by, w: cw - 0.46, h: bh, fontSize: 11.5, valign: "middle", lineSpacingMultiple: 1.1 });
      by += bh + 0.08;
    });
  });
  dash(s, CX, CBOT - 0.68, CW);
  RR(s, { x: CX, y: CBOT - 0.48, w: 0.6, h: 0.34, rectRadius: 0.08, fill: { color: K.accent }, line: { color: K.accent } });
  T(s, "TIP", { x: CX, y: CBOT - 0.48, w: 0.6, h: 0.34, fontSize: 11, bold: true, color: K.white, align: "center", valign: "middle" });
  T(s, tk.tip, { x: CX + 0.8, y: CBOT - 0.53, w: CW - 0.8, h: 0.44, fontSize: 14, color: K.sub, valign: "middle" });
}

/* 8. 에티켓 */
{
  const s = page("ETIQUETTE", "기본 에티켓 지켜요!");
  const top = CTOP + 0.2, step = (CBOT - top) / data.etiquette.length;
  data.etiquette.forEach((t, i) => {
    const y = top + i * step;
    RR(s, { x: CX, y, w: 0.55, h: 0.55, rectRadius: 0.1, fill: { color: K.soft }, line: { color: K.ink, width: 1.75 } });
    T(s, String(i + 1), { x: CX, y, w: 0.55, h: 0.55, fontSize: 17, bold: true, align: "center", valign: "middle" });
    T(s, t, { x: CX + 0.85, y: y - 0.02, w: CW - 0.85, h: 0.6, fontSize: 21, valign: "middle" });
    if (i < data.etiquette.length - 1) dash(s, CX, y + step - 0.3, CW);
  });
}

pres.writeFile({ fileName: OUT }).then(() => console.log("wrote", OUT));
