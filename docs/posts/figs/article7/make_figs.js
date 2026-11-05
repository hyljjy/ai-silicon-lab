// 生成文章 7（setup slack 的时间账）的数据图和示意图（SVG）。数据图的数字都从同目录 sta_output.txt（OpenSTA 原样输出）解析，不手填。
// 用法：node docs/posts/figs/article7/make_figs.js   输出到同目录 *.svg；PNG 用 export_png.sh 导出（2 倍，1440 px 宽）。
// 版式沿用文章 1、3、4：画布宽 720，主体文字 30 左右，辅助文字不小于 22。说明性长句放正文，不放图里。
const fs = require("fs");
const path = require("path");
const OUT = __dirname;
const W = 720;
const C = {
  surface: "#fcfcfb", ink: "#0b0b0b", ink2: "#52514e", muted: "#8a8986",
  grid: "#e4e3df", line: "#c9c8c3", blue: "#2a78d6", orange: "#eb6834", red: "#c8321e",
  blueSoft: "#dbe8f8", orangeSoft: "#fbe3d8", graySoft: "#efeeea", gray: "#8f8e89",
};
const FONT = "'Microsoft YaHei','PingFang SC','Noto Sans CJK SC','Source Han Sans SC',sans-serif";
const MONO = "Consolas,Menlo,'Courier New',monospace";
const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const num = (v, d = 3) => (v < 0 ? "−" : "") + Math.abs(v).toFixed(d);
const sgn = (v, d = 3) => (Math.abs(v) < 0.0005 ? "0" : (v < 0 ? "−" : "+") + Math.abs(v).toFixed(d));
function svg(h, body) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${h}" viewBox="0 0 ${W} ${h}" font-family="${FONT}">
<rect width="${W}" height="${h}" fill="${C.surface}"/>
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="${C.ink2}"/></marker></defs>
${body}
</svg>
`;
}
const T = (x, y, s, o = {}) =>
  `<text x="${x}" y="${y}" font-size="${o.size || 30}" fill="${o.fill || C.ink}" font-weight="${o.bold ? 700 : 400}" text-anchor="${o.anchor || "start"}"${o.mono ? ` font-family="${MONO}"` : ""}>${esc(s)}</text>`;
const R = (x, y, w, h, o = {}) =>
  `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${o.rx ?? 10}" fill="${o.fill || "none"}" stroke="${o.stroke || "none"}" stroke-width="${o.sw || 2}"${o.dash ? ` stroke-dasharray="${o.dash}"` : ""}/>`;
const L = (x1, y1, x2, y2, o = {}) =>
  `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${o.stroke || C.ink2}" stroke-width="${o.sw || 2}"${o.dash ? ` stroke-dasharray="${o.dash}"` : ""}${o.arrow ? ` marker-end="url(#arr)"` : ""}/>`;
const title = (t, sub) => T(36, 58, t, { size: 36, bold: true }) + (sub ? T(36, 100, sub, { size: 24, fill: C.ink2 }) : "");
const write = (name, s) => { fs.writeFileSync(path.join(OUT, name), s); console.log(name); };
const box = (x, y, w, h, lines, o = {}) => {
  let s = R(x, y, w, h, { fill: o.fill || C.graySoft, stroke: o.stroke, dash: o.dash });
  const lh = o.lh || 34, y0 = y + h / 2 - ((lines.length - 1) * lh) / 2 + 9;
  lines.forEach(t => {
    const [txt, to] = Array.isArray(t) ? t : [t, {}];
    s += T(x + w / 2, y0 + lines.indexOf(t) * lh, txt, { size: 24, anchor: "middle", ...to });
  });
  return s;
};
const COND = "CASE-01 网表，Sky130 HD；T = 27.91 ns";
const COND2 = "综合后、理想时钟、不读寄生";

// ---------- 解析 sta_output.txt：按 "### 段名" 分段，段内按 "Startpoint:" 切块 ----------
const RAW = fs.readFileSync(path.join(OUT, "sta_output.txt"), "utf8");
const seg = {};
RAW.split(/^### /m).slice(1).forEach(s => {
  const name = s.split("\n")[0].trim();
  seg[name] = s.split(/^Startpoint: /m).slice(1).map(b => {
    const g = (re, opt) => { const m = b.match(re); if (!m) { if (opt) return null; throw new Error(`no match ${re} in ${name}`); } return m; };
    const o = { start: b.split(" ")[0], end: g(/^Endpoint: (\S+)/m)[1], corner: g(/^Corner: (\S+)/m)[1] };
    o.arr = +g(/^\s+(-?[\d.]+)\s+data arrival time$/m)[1];
    o.req = +g(/^\s+(-?[\d.]+)\s+data required time$/m)[1];
    o.slack = +g(/^\s+(-?[\d.]+)\s+slack \(/m)[1];
    const f = re => { const m = g(re, true); return m ? +m[1] : 0; };
    o.ind = f(/^\s+(-?[\d.]+)\s+-?[\d.]+ \S+ input external delay$/m);
    o.outd = -f(/^\s+(-?[\d.]+)\s+-?[\d.]+\s+output external delay$/m);
    o.setup = -f(/^\s+(-?[\d.]+)\s+-?[\d.]+\s+library setup time$/m);
    o.unc = -f(/^\s+(-?[\d.]+)\s+-?[\d.]+\s+clock uncertainty$/m);
    const net = [...b.matchAll(/^\s+(-?[\d.]+)\s+-?[\d.]+\s+clock network delay \(ideal\)$/gm)].map(m => +m[1]);
    [o.launch, o.capture] = net;
    return o;
  });
});
const close = (a, b, msg) => { if (Math.abs(a - b) > 5e-6) throw new Error(`${msg}: ${a} vs ${b}`); };
// 自检：每一块都按第 2 节的公式对账
const PERIOD = { period: 26.91 };
Object.entries(seg).forEach(([n, bs]) => bs.forEach((o, i) => {
  const T0 = PERIOD[n] ?? 27.91;
  close(o.req - o.arr, o.slack, `slack ${n}#${i}`);
  close(T0 + o.capture - o.unc - o.setup - o.outd, o.req, `required ${n}#${i}`);
}));
const IN = n => seg[n][0], OUTP = n => seg[n][1];
const base = IN("base"), baseOut = OUTP("base"), ssBase = seg.base[2];
if (ssBase.corner !== "ss_n40C_1v60") throw new Error("ss block order");
const ssIO = seg.io_0p1T[2];
if (seg.one_reg[0].end !== "_12027_") throw new Error("one_reg worst endpoint");
const own = seg.one_reg[2];
if (own.end !== "_12026_") throw new Error("one_reg own endpoint");
const tie = [...RAW.split(/^### /m)[1].matchAll(/^_\d+_\/D \(\S+\)\s+\S+\s+\S+\s+(\S+) \(MET\)$/gm)].filter(m => m[1] === "11.185458").length;
if (tie !== 27) throw new Error(`ties ${tie}`);
if (!/^No paths found\.$/m.test(RAW) || !/^registers: 33$/m.test(RAW)) throw new Error("structure facts");

const SC = (x0, x1, max) => v => x0 + v / max * (x1 - x0);
function bar(y, h, X, parts) {
  let s = "", t = 0;
  parts.forEach(([v, col]) => { s += `<rect x="${X(t)}" y="${y}" width="${X(t + v) - X(t)}" height="${h}" fill="${col}"/>`; t += v; });
  return s;
}
// 图 1：一笔账画在时间轴上
{
  const X = SC(36, 684, 27.91), pd = base.arr - base.ind;
  let b = title("把一笔账画在时间轴上", "tt 1.80 V 25 °C，全设计最差路径（输入到寄存器）");
  const y = 190, h = 56;
  b += bar(y, h, X, [[base.ind, C.gray], [pd, C.blue], [base.slack, C.orangeSoft], [base.setup, C.ink]]);
  b += T((X(0) + X(base.ind)) / 2, y + 36, "input delay", { size: 20, anchor: "middle", fill: "#fff", bold: true });
  b += T((X(base.ind) + X(base.arr)) / 2, y + 37, "路径延迟", { size: 24, anchor: "middle", fill: "#fff", bold: true });
  b += T((X(base.arr) + X(base.req)) / 2, y + 37, "slack", { size: 26, anchor: "middle", fill: C.orange, bold: true });
  b += T((X(0) + X(base.ind)) / 2, y - 14, num(base.ind), { size: 24, anchor: "middle", mono: true });
  b += T((X(base.ind) + X(base.arr)) / 2, y - 14, num(pd), { size: 24, anchor: "middle", mono: true });
  b += T((X(base.arr) + X(base.req)) / 2, y - 14, num(base.slack), { size: 24, anchor: "middle", mono: true, fill: C.orange, bold: true });
  b += L(X(base.arr), y - 6, X(base.arr), y + h + 22, { stroke: C.blue });
  b += T(X(base.arr), y + h + 50, `实际到达 ${num(base.arr)}`, { size: 24, anchor: "end", fill: C.blue, bold: true });
  b += L(X(base.req), y - 6, X(base.req), y + h + 22, { stroke: C.ink });
  b += T(684, y + h + 50, `最晚允许 ${num(base.req)}`, { size: 24, anchor: "end", bold: true });
  b += T(684, y + h + 86, `T ${num(27.91, 2)} − 库 setup ${num(base.setup)}`, { size: 22, anchor: "end", fill: C.ink2 });
  b += R(36, 370, 648, 70, { fill: C.orangeSoft });
  b += T(56, 415, `slack = ${num(base.req)} − ${num(base.arr)} = ${num(base.slack)} ns`, { size: 26, bold: true });
  b += T(36, 476, COND, { size: 22, fill: C.ink2 });
  b += T(36, 508, COND2 + "；路径延迟含输入驱动模型", { size: 22, fill: C.ink2 });
  write("fig1_ledger.svg", svg(530, b));
}
// 图 2：三条路径的账
{
  const X = SC(36, 684, 32);
  let b = title("三条路径的账", "同一把尺子，单位 ns；竖线是最晚允许到达");
  const rows = [
    ["tt 1.80 V 25 °C，输入到寄存器", base, C.blue],
    ["tt 1.80 V 25 °C，寄存器到输出", baseOut, C.blue],
    ["ss 1.60 V −40 °C，输入到寄存器", ssBase, C.red],
  ];
  let y = 136;
  rows.forEach(([name, o, col]) => {
    b += T(36, y + 26, name, { size: 26, bold: true });
    const yb = y + 42, h = 36;
    b += bar(yb, h, X, [[o.arr, col]]);
    if (o.slack > 0) b += `<rect x="${X(o.arr)}" y="${yb}" width="${X(o.req) - X(o.arr)}" height="${h}" fill="${C.orangeSoft}"/>`;
    b += L(X(o.req), yb - 10, X(o.req), yb + h + 10, { stroke: C.ink, sw: 3 });
    b += T(36, yb + h + 36, `实际 ${num(o.arr)}，允许 ${num(o.req)}`, { size: 22, fill: C.ink2 });
    b += T(684, yb + h + 36, `slack ${num(o.slack)}`, { size: 26, anchor: "end", bold: true, fill: o.slack < 0 ? C.red : C.orange, mono: true });
    y += 148;
  });
  b += T(36, y + 16, COND, { size: 22, fill: C.ink2 });
  b += T(36, y + 48, COND2, { size: 22, fill: C.ink2 });
  write("fig2_three_paths.svg", svg(y + 72, b));
}
// 图 3：设计结构
{
  let b = title("这个设计的数据怎么走", "寄存器只在输出端打一拍");
  const y = 150, h = 120;
  b += box(36, y, 110, h, ["输入", "端口"], { fill: C.graySoft });
  b += box(186, y, 210, h, ["全部组合逻辑", ["乘加、饱和", { size: 22, fill: C.ink2 }]], { fill: C.blueSoft });
  b += box(436, y, 120, h, ["33 个", "寄存器"], { fill: C.orangeSoft });
  b += box(596, y, 88, h, ["输出", "端口"], { fill: C.graySoft });
  b += L(146, y + h / 2, 184, y + h / 2, { arrow: true }) + L(396, y + h / 2, 434, y + h / 2, { arrow: true }) + L(556, y + h / 2, 594, y + h / 2, { arrow: true });
  b += T(290, y + h + 44, `到达 ${num(base.arr)} ns`, { size: 24, anchor: "middle", fill: C.blue, bold: true });
  b += T(290, y + h + 76, `其中 input delay ${num(base.ind)}`, { size: 22, anchor: "middle", fill: C.ink2 });
  b += T(684, y + h + 44, `clk→Q ${num(baseOut.arr)} ns`, { size: 24, anchor: "end", fill: C.orange, bold: true });
  b += R(36, 370, 648, 74, { fill: C.graySoft });
  b += T(56, 416, "寄存器到寄存器：", { size: 24, bold: true });
  b += T(254, 416, "No paths found.", { size: 26, mono: true, fill: C.red, bold: true });
  b += T(36, 482, "tt 1.80 V 25 °C；" + COND, { size: 22, fill: C.ink2 });
  b += T(36, 514, COND2, { size: 22, fill: C.ink2 });
  b += T(36, 546, "33 个 = 32 位 out_data + 1 位 out_valid", { size: 22, fill: C.ink2 });
  write("fig3_structure.svg", svg(568, b));
}
// 图 4：6 个改动让 slack 变了多少
{
  const rows = [["周期减 1 ns", "period"], ["input delay 加 1 ns", "input_delay"], ["uncertainty 0.3 ns", "uncertainty"],
    ["单个时钟晚 0.3 ns", "one_reg"], ["整个时钟晚 0.3 ns", "whole_clock"], ["IO delay 改成 0.1T", "io_0p1T"]];
  const lo = -1.2, hi = 3.0, x0 = 290, x1 = 580, X = v => x0 + (v - lo) / (hi - lo) * (x1 - x0);
  let b = title("6 个改动让 slack 变了多少", "和基线相比，单位 ns");
  b += R(36, 116, 22, 22, { rx: 3, fill: C.blue }) + T(66, 136, "全设计最差", { size: 22, fill: C.ink2 });
  b += R(216, 116, 22, 22, { rx: 3, fill: C.orange }) + T(246, 136, "到输出端口最差", { size: 22, fill: C.ink2 });
  let y = 166;
  rows.forEach(([name, k]) => {
    const dI = IN(k).slack - base.slack, dO = OUTP(k).slack - baseOut.slack;
    b += T(36, y + 40, name, { size: 24, bold: true });
    [[dI, C.blue], [dO, C.orange]].forEach(([d, col], i) => {
      const yy = y + 6 + i * 34, xa = Math.min(X(0), X(d)), w = Math.abs(X(d) - X(0));
      b += `<rect x="${xa}" y="${yy}" width="${w}" height="26" rx="2" fill="${col}"/>`;
      b += T(684, yy + 22, sgn(d), { size: 24, anchor: "end", fill: col, bold: true, mono: true });
    });
    y += 82;
  });
  b += L(X(0), 160, X(0), y - 6, { stroke: C.ink2 });
  b += T(36, y + 26, "tt 1.80 V 25 °C；基线 T = 27.91 ns，周期改动项 26.91 ns", { size: 22, fill: C.ink2 });
  b += T(36, y + 58, "CASE-01 网表，Sky130 HD；" + COND2, { size: 22, fill: C.ink2 });
  write("fig4_changes.svg", svg(y + 80, b));
}
// 图 5：时钟晚到，动一个和动全部
{
  let b = title("时钟晚到：动一个和动全部", "时钟都晚 0.3 ns，slack 变化，单位 ns");
  const one = seg.one_reg, whole = seg.whole_clock;
  const panel = (y, head, col, rows, foot) => {
    let s = R(36, y, 648, 226, { fill: col });
    s += T(56, y + 44, head, { size: 26, bold: true });
    rows.forEach(([a, c, d], i) => {
      const yy = y + 92 + i * 44;
      s += T(56, yy, a, { size: 24 });
      s += T(420, yy, c, { size: 24, mono: true });
      s += T(664, yy, d, { size: 24, mono: true, anchor: "end", bold: true });
    });
    s += T(56, y + 200, foot, { size: 24, bold: true, fill: C.ink2 });
    return s;
  };
  b += panel(120, "只动 _12026_ 一个寄存器", C.blueSoft, [
    ["收数据（自己的 D 端）", `${num(base.slack)} →`, num(own.slack)],
    ["发数据（到 out_data[0]）", `${num(baseOut.slack)} →`, num(one[1].slack)],
  ], "时间从后一段挪给前一段");
  b += panel(362, "整个时钟一起动", C.graySoft, [
    ["全设计最差", `${num(base.slack)} →`, num(whole[0].slack)],
    ["到输出端口最差", `${num(baseOut.slack)} →`, num(whole[1].slack)],
  ], "launch、capture 都加 0.3，抵消");
  b += T(36, 626, `基线有 27 个终点并列；只挪走一个，全设计最差仍是 ${num(one[0].slack)}`, { size: 22, fill: C.ink2 });
  b += T(36, 658, "tt 1.80 V 25 °C；" + COND, { size: 22, fill: C.ink2 });
  b += T(36, 690, "理想时钟、不读寄生；延迟为手动设置，不是真实时钟树", { size: 22, fill: C.ink2 });
  write("fig5_clock_shift.svg", svg(712, b));
}
// 图 6：改预算
{
  const add = IN("io_0p1T").slack - base.slack;
  close(ssIO.slack - ssBase.slack, add, "budget delta");
  const lo = -5, hi = 15, x0 = 36, x1 = 684, X = v => x0 + (v - lo) / (hi - lo) * (x1 - x0);
  let b = title("改预算：报告变了，电路没变", "IO delay 从 0.2T 改成 0.1T，最差 slack，单位 ns");
  const rows = [["tt 1.80 V 25 °C", base.slack, IN("io_0p1T").slack], ["ss 1.60 V −40 °C", ssBase.slack, ssIO.slack]];
  let y = 136;
  rows.forEach(([name, a, c]) => {
    b += T(36, y + 26, name, { size: 26, bold: true });
    [["0.2T（原约束）", a, C.blue], ["0.1T（改后约束）", c, C.orange]].forEach(([t, v, col], i) => {
      const yy = y + 44 + i * 76, xa = Math.min(X(0), X(v)), w = Math.abs(X(v) - X(0));
      b += T(36, yy + 22, t, { size: 22, fill: col, bold: true });
      b += T(684, yy + 22, num(v), { size: 24, anchor: "end", fill: col, bold: true, mono: true });
      b += `<rect x="${xa}" y="${yy + 32}" width="${w}" height="26" rx="2" fill="${col}"/>`;
      b += L(X(0), yy + 26, X(0), yy + 64, { stroke: C.ink2 });
    });
    y += 212;
  });
  b += R(36, y, 648, 70, { fill: C.orangeSoft });
  b += T(56, y + 45, `两个角都多了 ${num(add)} ns，全部来自改约束`, { size: 25, bold: true });
  b += T(36, y + 106, COND, { size: 22, fill: C.ink2 });
  b += T(36, y + 138, COND2 + "；网表相同，只改约束", { size: 22, fill: C.ink2 });
  b += T(36, y + 170, "假设外部接口要求仍是 0.2T 时，要按 0.2T 那一行算", { size: 22, fill: C.ink2 });
  write("fig6_budget.svg", svg(y + 192, b));
}
// 图 7：setup 要求从哪来（示意）
{
  let b = title("setup 要求从哪来", "示意图，不是实测；触发器内部本文没有验证");
  b += R(250, 130, 300, 260, { fill: C.graySoft, stroke: C.line });
  b += T(400, 164, "触发器内部", { size: 22, anchor: "middle", fill: C.ink2 });
  b += R(420, 190, 90, 130, { rx: 6, fill: C.orangeSoft, stroke: C.orange });
  b += T(465, 262, "门", { size: 28, anchor: "middle", bold: true, fill: C.orange });
  b += T(36, 240, "新数据 D", { size: 26, bold: true, fill: C.blue });
  b += L(160, 232, 416, 232, { stroke: C.blue, sw: 4, arrow: true });
  b += T(320, 208, "走到门口站稳", { size: 22, anchor: "middle", fill: C.blue });
  b += T(36, 350, "时钟沿", { size: 26, bold: true });
  b += `<path d="M130,342 L465,342 L465,324" fill="none" stroke="${C.ink2}" stroke-width="4" marker-end="url(#arr)"/>`;
  b += T(345, 374, "走到门、下令关门", { size: 22, anchor: "middle", fill: C.ink2 });
  b += R(36, 410, 648, 74, { fill: C.blueSoft });
  b += T(360, 456, "setup ≈ 数据走到门口站稳 − 时钟走到门", { size: 26, anchor: "middle", bold: true });
  b += T(36, 524, "比喻不能代替库的查表。上述路径报告中的 setup 要求：", { size: 22, fill: C.ink2 });
  b += T(36, 556, `tt 1.80 V 25 °C ${num(base.setup)} ns，ss 1.60 V −40 °C ${num(ssBase.setup)} ns`, { size: 22, fill: C.ink2 });
  write("fig7_door.svg", svg(578, b));
}
