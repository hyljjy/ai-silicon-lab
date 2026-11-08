// 生成文章 8（判预测）的示意图（SVG）。图里的数字都从 tasks/CASE-01/revise/predictions 的判定文件解析，不手填。
// 用法：node docs/posts/figs/article8/make_figs.js   输出到同目录 *.svg；PNG 用 export_png.sh 导出（2 倍，1440 px 宽）。
// 版式沿用文章 3–6：画布宽 720，主体文字 30 左右，辅助文字不小于 22。说明性长句放正文，不放图里。
const fs = require("fs");
const path = require("path");
const OUT = __dirname;
const PRED = path.join(__dirname, "..", "..", "..", "..", "tasks", "CASE-01", "revise", "predictions");
const W = 720;

const C = {
  surface: "#fcfcfb", ink: "#0b0b0b", ink2: "#52514e", muted: "#8a8986",
  grid: "#e4e3df", line: "#c9c8c3", blue: "#2a78d6", orange: "#eb6834",
  blueSoft: "#dbe8f8", orangeSoft: "#fbe3d8", graySoft: "#efeeea",
};
const FONT = "'Microsoft YaHei','PingFang SC','Noto Sans CJK SC','Source Han Sans SC',sans-serif";
const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
function svg(h, body) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${h}" viewBox="0 0 ${W} ${h}" font-family="${FONT}">
<rect width="${W}" height="${h}" fill="${C.surface}"/>
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="${C.ink2}"/></marker></defs>
${body}
</svg>
`;
}
const T = (x, y, s, o = {}) =>
  `<text x="${x}" y="${y}" font-size="${o.size || 30}" fill="${o.fill || C.ink}" font-weight="${o.bold ? 700 : 400}" text-anchor="${o.anchor || "start"}">${esc(s)}</text>`;
const R = (x, y, w, h, o = {}) =>
  `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${o.rx ?? 10}" fill="${o.fill || "none"}" stroke="${o.stroke || "none"}" stroke-width="${o.sw || 2}"${o.dash ? ` stroke-dasharray="${o.dash}"` : ""}/>`;
const L = (x1, y1, x2, y2, o = {}) =>
  `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${o.stroke || C.ink2}" stroke-width="${o.sw || 2}"${o.dash ? ` stroke-dasharray="${o.dash}"` : ""}${o.arrow ? ` marker-end="url(#arr)"` : ""}/>`;
const title = (t, sub) => T(36, 58, t, { size: 36, bold: true }) + (sub ? T(36, 100, sub, { size: 24, fill: C.ink2 }) : "");
const write = (name, s) => { fs.writeFileSync(path.join(OUT, name), s); console.log(name); };

// ---------- 从判定文件取数 ----------
// 表格列：候选 | 编号 | id | 指标 | 检查 | 角 | 类别 | 值类型 | 实际值 | 方向 | 范围 | 汇总 | 理由 | 说明
function row(round, pid) {
  const line = fs.readFileSync(path.join(PRED, `r${round}_judgments.md`), "utf8").split(/\r?\n/)
    .find(l => l.split("|")[2] && l.split("|")[2].trim() === pid);
  if (!line) throw new Error(`no row ${pid} in round ${round}`);
  const c = line.split("|").map(s => s.trim());
  const detail = c[14] || "";
  const rng = detail.match(/范围 \[([^,]+), ([^\]]+)\]/);
  const pt = detail.match(/点估计 (\S+) 不判/);
  return { metric: c[4], category: c[7], actual: Number(c[9]), judgment: c[12],
    low: rng ? Number(rng[1]) : null, high: rng ? Number(rng[2]) : null, point: pt ? Number(pt[1]) : null };
}
const p1 = row(2, "cand_u2pe.P1"), p4 = row(2, "cand_u2pe.P4");
const c1 = row(1, "cand_9pbi.P6"), c2 = row(2, "cand_u2pe.P6"), k2 = row(2, "cand_3yvg.P4");
const f2 = v => (v < 0 ? "−" : "+") + Math.abs(v).toFixed(2);
if (p1.judgment !== "支持" || c1.judgment !== "反对" || c2.judgment !== "支持" || k2.judgment !== "反对")
  throw new Error("judgments no longer match the article text");

// ---------- 图 1：哪一个 slack ----------
{
  let b = title("一句\"slack 变好\"，指的是哪一个", "Claude 第 2 轮的候选，setup，ss_n40C_1v60");
  const card = (y, head, sub, val, fill, color) =>
    R(36, y, 648, 120, { fill }) + T(58, y + 50, head, { size: 27, bold: true }) +
    T(58, y + 92, sub, { size: 23, fill: C.ink2 }) + T(662, y + 74, `${val} ns`, { size: 34, bold: true, fill: color, anchor: "end" });
  b += card(130, "全设计最差", "落在寄存器到寄存器的新路径上", f2(p1.actual), C.blueSoft, C.blue);
  b += card(270, "输入到寄存器这一类", "基线那条最差路径所在的类", f2(p4.actual), C.orangeSoft, C.orange);
  b += T(36, 444, "预测表要写清：", { size: 26, bold: true });
  b += T(36, 486, "setup 还是 hold · 哪个角 · 哪类路径", { size: 25, fill: C.ink2 });
  b += T(36, 524, "数值本身还是相对基线的差", { size: 25, fill: C.ink2 });
  write("fig1_which.svg", svg(556, b));
}

// ---------- 图 2：先看缺的是哪一边 ----------
{
  let b = title("先看缺的是哪一边", "slack、面积这类数值预测；先看工具，再看模型");
  const x0 = 196, y0 = 170, cw = 244, ch = 150;
  b += T(x0 + cw / 2, y0 - 16, "工具出了数", { size: 24, fill: C.ink2, anchor: "middle" });
  b += T(x0 + cw * 1.5 + 4, y0 - 16, "工具没出数", { size: 24, fill: C.ink2, anchor: "middle" });
  b += T(36, y0 + 82, "模型给了", { size: 24, fill: C.ink2 });
  b += T(36, y0 + ch + 86, "模型没给", { size: 24, fill: C.ink2 });
  const cell = (cx, cy, head, sub, fill, color) =>
    R(cx, cy, cw, ch - 8, { fill }) + T(cx + cw / 2, cy + 64, head, { size: 28, bold: true, fill: color, anchor: "middle" }) +
    T(cx + cw / 2, cy + 106, sub, { size: 22, fill: C.ink2, anchor: "middle" });
  b += cell(x0, y0, "支持 / 反对", "按方向和范围判", C.blueSoft, C.blue);
  b += cell(x0 + cw + 8, y0, "无结果", "不判对错", C.graySoft, C.ink);
  b += cell(x0, y0 + ch, "未判定", "有实际值，但没可判的", C.orangeSoft, C.orange);
  b += cell(x0 + cw + 8, y0 + ch, "无结果", "本次也出现过", C.graySoft, C.ink);
  b += T(36, 518, "延迟和功能直接比较；另有\"不适用\"。", { size: 24, fill: C.ink2 });
  write("fig2_labels.svg", svg(548, b));
}

// ---------- 图 3：AND 和 OR ----------
{
  let b = title("同样两项，AND 和 OR 结果不同", "\"STA 再次因网表语法错误失败\"");
  const item = (y, head, val, fill, color) =>
    R(36, y, 648, 86, { fill }) + T(58, y + 54, head, { size: 26 }) + T(662, y + 54, val, { size: 28, bold: true, fill: color, anchor: "end" });
  b += item(130, "第一项：STA 这一步失败", "真", C.blueSoft, C.blue);
  b += item(230, "第二项：失败原因是语法错误", "未知", C.orangeSoft, C.orange);
  b += T(58, 362, "字段只记成不成功，不记原因，查不了", { size: 23, fill: C.ink2 });
  const res = (x, head, val, note, fill, color) =>
    R(x, 400, 312, 150, { fill }) + T(x + 156, 448, head, { size: 26, fill: C.ink2, anchor: "middle" }) +
    T(x + 156, 498, val, { size: 32, bold: true, fill: color, anchor: "middle" }) +
    T(x + 156, 534, note, { size: 22, fill: C.ink2, anchor: "middle" });
  b += res(36, "按原意转写：AND", "未判定", "真 AND 未知 = 未知", C.orangeSoft, C.orange);
  b += res(372, "假如转写成 OR", "触发", "真 OR 未知 = 真", C.graySoft, C.ink);
  write("fig3_fc.svg", svg(580, b));
}

// ---------- 图 4：面积增量的范围和实测 ----------
{
  const lo = 0, hi = 12000, xa = 60, xb = 670;
  const X = v => xa + (v - lo) / (hi - lo) * (xb - xa);
  let b = title("面积增量：两轮的范围和实测", "单位 µm²；方框是预测范围，圆点是实测");
  const line = (y, head, r, judge, color) => {
    let s = T(36, y, head, { size: 25, bold: true }) + T(684, y, judge, { size: 25, bold: true, fill: color, anchor: "end" });
    s += L(xa, y + 46, xb, y + 46, { stroke: C.line, sw: 2 });
    if (r.low !== null) s += R(X(r.low), y + 28, X(r.high) - X(r.low), 36, { fill: color === C.blue ? C.blueSoft : C.orangeSoft, stroke: color, rx: 4 });
    s += `<circle cx="${X(r.actual)}" cy="${y + 46}" r="9" fill="${C.ink}"/>`;
    s += T(X(r.actual), y + 92, r.actual.toFixed(0), { size: 22, fill: C.ink2, anchor: "middle" });
    return s;
  };
  b += line(160, "Claude 第 1 轮", c1, "反对", C.orange);
  b += line(290, "Claude 第 2 轮", c2, "支持 · 改对", C.blue);
  b += line(420, "Kimi 第 2 轮", k2, "反对 · 改错", C.orange);
  b += T(36, 560, "Kimi 第 1 轮只写\"面积增加\"，判支持。", { size: 24, fill: C.ink2 });
  b += T(36, 598, "0", { size: 22, fill: C.muted }) + T(684, 598, "12000", { size: 22, fill: C.muted, anchor: "end" });
  write("fig4_area.svg", svg(628, b));
}

// ---------- 图 5：范围写得宽 ----------
{
  const lo = -2, hi = 24, xa = 60, xb = 670;
  const X = v => xa + (v - lo) / (hi - lo) * (xb - xa);
  const y = 220;
  let b = title("范围写得宽，支持就容易", "Claude 第 2 轮：全设计最差 setup slack");
  b += R(X(p1.low), y - 30, X(p1.high) - X(p1.low), 60, { fill: C.blueSoft, rx: 4 });
  b += T((X(p1.low) + X(p1.high)) / 2, y - 46, `预测范围 ${p1.low} 到 ${p1.high} ns`, { size: 25, bold: true, fill: C.blue, anchor: "middle" });
  b += L(xa, y, xb, y, { sw: 3, stroke: C.ink2 });
  b += L(X(p1.point), y - 30, X(p1.point), y + 30, { sw: 3, stroke: C.ink2, dash: "6 5" });
  b += T(X(p1.point) + 8, y + 64, `点估计 ${p1.point}`, { size: 24, fill: C.ink2 });
  b += `<circle cx="${X(p1.actual)}" cy="${y}" r="11" fill="${C.orange}"/>`;
  b += T(X(p1.actual) - 8, y + 64, `实测 ${f2(p1.actual)}`, { size: 24, bold: true, fill: C.orange, anchor: "end" });
  b += T(36, 350, `判支持。范围宽 ${(p1.high - p1.low).toFixed(1)} ns，点估计差 ${(p1.point - p1.actual).toFixed(1)} ns。`, { size: 26, fill: C.ink2 });
  write("fig5_wide.svg", svg(382, b));
}
