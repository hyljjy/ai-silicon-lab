// 生成文章 1 公众号版的示意图（SVG）。数字取自 docs/posts/article1_draft.md，出处见各图注释。
// 用法：node docs/posts/figs/article1/make_figs.js   输出到同目录 *.svg
const fs = require("fs");
const path = require("path");
const OUT = __dirname;

const C = {
  surface: "#fcfcfb", ink: "#0b0b0b", ink2: "#52514e", muted: "#8a8986",
  grid: "#e4e3df", line: "#c9c8c3", blue: "#2a78d6", orange: "#eb6834",
  blueSoft: "#dbe8f8", orangeSoft: "#fbe3d8", graySoft: "#efeeea",
};
const FONT = "'Microsoft YaHei','PingFang SC','Noto Sans CJK SC','Source Han Sans SC',sans-serif";
const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function svg(w, h, body) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" font-family="${FONT}">
<rect width="${w}" height="${h}" fill="${C.surface}"/>
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="${C.ink2}"/></marker>
<marker id="arrO" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="${C.orange}"/></marker></defs>
${body}
</svg>
`;
}
const T = (x, y, s, o = {}) =>
  `<text x="${x}" y="${y}" font-size="${o.size || 30}" fill="${o.fill || C.ink}" font-weight="${o.bold ? 700 : 400}" text-anchor="${o.anchor || "start"}" dominant-baseline="${o.base || "alphabetic"}">${esc(s)}</text>`;
const R = (x, y, w, h, o = {}) =>
  `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${o.rx ?? 10}" fill="${o.fill || "none"}" stroke="${o.stroke || "none"}" stroke-width="${o.sw || 2}"${o.dash ? ` stroke-dasharray="${o.dash}"` : ""}/>`;
const L = (x1, y1, x2, y2, o = {}) =>
  `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${o.stroke || C.ink2}" stroke-width="${o.sw || 2}"${o.dash ? ` stroke-dasharray="${o.dash}"` : ""}${o.arrow ? ` marker-end="url(#${o.arrow})"` : ""}/>`;
const write = (name, s) => { fs.writeFileSync(path.join(OUT, name), s); console.log(name); };

// 图 1：这个系列怎么做（PLAN_v1.0 第 1、2 节）
{
  const W = 1080, steps = [
    ["①", "先定题目和规则", "设计、约束、综合和分析配置在 AI 介入前固定", ""],
    ["②", "AI 读报告、下诊断", "逐条核对：对照原文，做查询和对照", "本文 · CASE-01 阶段 A"],
    ["③", "AI 改 RTL", "功能仿真 + 同一配置的时序复验，代价一起报", "下一篇 · 阶段 B，最多两轮"],
    ["④", "结果不好也发表", "没有收益就写失败分析，不试到成功为止", ""],
  ];
  let b = T(60, 80, "这个系列怎么做", { size: 40, bold: true });
  steps.forEach((s, i) => {
    const y = 120 + i * 170;
    const hi = i === 1;
    b += R(60, y, 960, 130, { fill: hi ? C.blueSoft : C.graySoft, stroke: hi ? C.blue : "none" });
    b += T(100, y + 58, s[0], { size: 40, bold: true, fill: hi ? C.blue : C.ink2 });
    b += T(170, y + 56, s[1], { size: 34, bold: true });
    b += T(170, y + 102, s[2], { size: 26, fill: C.ink2 });
    if (s[3]) b += T(990, y + 56, s[3], { size: 24, fill: hi ? C.blue : C.ink2, anchor: "end" });
    if (i < steps.length - 1) b += L(540, y + 132, 540, y + 166, { arrow: "arr" });
  });
  b += T(60, 830, "第二个案例 CASE-02（计划）：同一设计故意漏掉一项输入延迟约束，", { size: 24, fill: C.ink2 });
  b += T(60, 866, "看 AI 能否分清“真的变快”和“约束漏了”。", { size: 24, fill: C.ink2 });
  write("fig1_series.svg", svg(W, 900, b));
}

// 图 2：被测电路（draft §1）
{
  const W = 1080;
  let b = T(60, 70, "被测电路：四路乘加，饱和后输出", { size: 38, bold: true });
  const ys = [130, 220, 310, 400];
  ys.forEach((y, i) => {
    b += T(60, y + 42, `a${i}, b${i}`, { size: 26, fill: C.ink2 });
    b += L(150, y + 34, 200, y + 34, { arrow: "arr" });
    b += R(205, y, 110, 68, { fill: C.graySoft });
    b += T(260, y + 46, "×", { size: 36, anchor: "middle", bold: true });
    b += L(318, y + 34, 395, 300 + (i - 1.5) * 30, { arrow: "arr" });
  });
  b += R(400, 220, 170, 150, { fill: C.graySoft });
  b += T(485, 285, "四个乘积", { size: 26, anchor: "middle" });
  b += T(485, 322, "相加（34 位）", { size: 26, anchor: "middle" });
  b += L(572, 295, 625, 295, { arrow: "arr" });
  b += R(630, 220, 170, 150, { fill: C.graySoft });
  b += T(715, 285, "饱和到", { size: 26, anchor: "middle" });
  b += T(715, 322, "32 位", { size: 26, anchor: "middle" });
  b += L(802, 295, 855, 295, { arrow: "arr" });
  b += R(860, 220, 160, 150, { fill: C.blueSoft, stroke: C.blue });
  b += T(940, 285, "输出寄存器", { size: 26, anchor: "middle" });
  b += T(940, 322, "（只有这一级）", { size: 24, anchor: "middle", fill: C.ink2 });
  // 组合逻辑范围
  b += L(200, 500, 800, 500, { stroke: C.muted });
  b += L(200, 488, 200, 512, { stroke: C.muted });
  b += L(800, 488, 800, 512, { stroke: C.muted });
  b += T(500, 548, "全部组合逻辑挤在同一拍里（延迟 L = 1）", { size: 28, anchor: "middle", fill: C.ink2 });
  // 高扇出控制信号
  b += T(715, 410, "末端有高扇出的公共控制信号", { size: 22, anchor: "middle", fill: C.orange });
  b += T(715, 440, "（下文的 X、Y，各驱动 31 位）", { size: 22, anchor: "middle", fill: C.orange });
  b += T(60, 610, "时钟周期 27.91 ns。最差路径从输入 in_b[2] 出发，经过 37 个组合单元到达输出寄存器。", { size: 24, fill: C.ink2 });
  write("fig2_circuit.svg", svg(W, 650, b));
}

// 图 3：最差路径的时间账（draft §1：5.5820、5.8911、31.5439、27.3541、0.5559、27.91）
{
  const W = 1080, x0 = 70, k = 28.5, X = t => x0 + t * k;
  let b = T(60, 70, "最差路径的时间账（ss，1.60 V，−40 °C）", { size: 38, bold: true });
  const y = 200, h = 70;
  // 刻度
  for (let t = 0; t <= 32; t += 4) {
    b += L(X(t), y + h + 10, X(t), y + h + 20, { stroke: C.line });
    b += T(X(t), y + h + 52, `${t}`, { size: 22, anchor: "middle", fill: C.muted });
  }
  b += T(X(32) + 28, y + h + 52, "ns", { size: 22, fill: C.muted });
  b += L(X(0), y + h + 10, X(32.5), y + h + 10, { stroke: C.line });
  // 段
  b += `<rect x="${X(0)}" y="${y}" width="${X(5.582) - X(0) - 2}" height="${h}" rx="4" fill="${C.muted}"/>`;
  b += `<rect x="${X(5.582)}" y="${y}" width="${X(5.8911) - X(5.582)}" height="${h}" fill="${C.ink2}"/>`;
  b += `<rect x="${X(5.8911) + 2}" y="${y}" width="${X(31.5439) - X(5.8911) - 2}" height="${h}" rx="4" fill="${C.blue}"/>`;
  b += T(X(2.8), y + 46, "外部延迟", { size: 24, anchor: "middle", fill: "#ffffff" });
  b += T(X(2.8), y - 16, "5.58", { size: 24, anchor: "middle", fill: C.ink2 });
  b += T(X(18.7), y + 46, "37 个组合单元  25.65", { size: 26, anchor: "middle", fill: "#ffffff" });
  b += L(X(5.74), y - 4, X(7.2), y - 40, { stroke: C.ink2, sw: 1.5 });
  b += T(X(7.4), y - 44, "端口驱动 0.31", { size: 22, fill: C.ink2 });
  // 竖线
  const vline = (t, col, dash, label, ly, anchor) => {
    let s = L(X(t), t > 31 ? y - 6 : 130, X(t), y + h + 10, { stroke: col, sw: 3, dash });
    s += T(X(t) + (anchor === "end" ? -10 : 10), ly, label, { size: 24, fill: col, anchor });
    return s;
  };
  b += vline(27.91, C.muted, "8 6", "时钟周期 27.91", 150, "start");
  b += vline(27.3541, C.orange, "", "最晚应到 27.35", 150, "end");
  b += T(X(27.3541) - 10, 180, "（周期减 setup 0.56）", { size: 20, fill: C.orange, anchor: "end" });
  b += vline(31.5439, C.blue, "", "实际到达 31.54", y + h + 95, "end");
  // 晚到区间
  b += `<rect x="${X(27.3541)}" y="${y + h + 120}" width="${X(31.5439) - X(27.3541)}" height="16" rx="4" fill="${C.orange}"/>`;
  b += T(X(29.45), y + h + 175, "晚了 4.19 ns", { size: 28, anchor: "middle", fill: C.orange, bold: true });
  b += T(X(29.45), y + h + 210, "setup slack = −4.19", { size: 24, anchor: "middle", fill: C.orange });
  b += T(60, 560, "setup slack = 要求的最晚到达时刻 − 实际到达时刻；负数就是没赶上。", { size: 24, fill: C.ink2 });
  b += T(60, 596, "综合后、理想时钟、不计布线电阻电容（计引脚和输出负载）。", { size: 24, fill: C.ink2 });
  write("fig3_budget.svg", svg(W, 630, b));
}

// 图 4：6 个角的最差 setup slack（draft §1 slack_summary：-4.189726 -0.687278 11.185458 11.317222 15.871506 15.894229）
{
  const W = 1080, rows = [
    ["ss  1.60 V  −40 °C", -4.19], ["ss  1.60 V  100 °C", -0.69],
    ["tt  1.80 V  25 °C", 11.19], ["tt  1.80 V  100 °C", 11.32],
    ["ff  1.95 V  −40 °C", 15.87], ["ff  1.95 V  100 °C", 15.89],
  ];
  const x0 = 560, k = 22, X = v => x0 + v * k; // −5 … +17
  let b = T(60, 70, "6 个角的最差 setup slack（ns）", { size: 38, bold: true });
  b += T(60, 112, "只有两个慢工艺角违例", { size: 26, fill: C.ink2 });
  for (let v = -5; v <= 15; v += 5) {
    b += L(X(v), 140, X(v), 140 + rows.length * 70, { stroke: C.grid, sw: 1.5 });
    b += T(X(v), 140 + rows.length * 70 + 36, (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v), { size: 22, anchor: "middle", fill: C.muted });
  }
  rows.forEach(([name, v], i) => {
    const y = 150 + i * 70, h = 46, neg = v < 0;
    b += T(60, y + 33, name, { size: 26 });
    const xa = Math.min(X(0), X(v)), w = Math.abs(X(v) - X(0));
    b += `<rect x="${xa}" y="${y}" width="${w}" height="${h}" rx="4" fill="${neg ? C.orange : C.blue}"/>`;
    b += T(neg ? xa - 10 : xa + w + 10, y + 33, (v > 0 ? "+" : "−") + Math.abs(v).toFixed(2), { size: 26, anchor: neg ? "end" : "start", fill: C.ink, bold: neg });
  });
  b += L(X(0), 140, X(0), 140 + rows.length * 70, { stroke: C.ink2, sw: 2.5 });
  const ly = 140 + rows.length * 70 + 80;
  b += `<rect x="60" y="${ly - 22}" width="26" height="26" rx="4" fill="${C.orange}"/>` + T(98, ly, "违例（负数）", { size: 24, fill: C.ink2 });
  b += `<rect x="300" y="${ly - 22}" width="26" height="26" rx="4" fill="${C.blue}"/>` + T(338, ly, "有富余（正数）", { size: 24, fill: C.ink2 });
  write("fig4_corners.svg", svg(W, ly + 40, b));
}

// 图 5：流水切点的候选（draft §4、§9）
{
  const W = 1080;
  let b = T(60, 70, "三家提出的流水切点（都还是候选）", { size: 38, bold: true });
  const boxes = [["输入", 60], ["乘法", 270], ["相加", 480], ["饱和", 690], ["输出寄存器", 880]];
  const y = 260, h = 90;
  boxes.forEach(([s, x], i) => {
    const w = i === 4 ? 160 : 140;
    b += R(x, y, w, h, { fill: i === 4 ? C.blueSoft : C.graySoft, stroke: i === 4 ? C.blue : "none" });
    b += T(x + w / 2, y + 56, s, { size: 28, anchor: "middle" });
    if (i < 4) b += L(x + w + 4, y + h / 2, boxes[i + 1][1] - 6, y + h / 2, { arrow: "arr" });
  });
  const cut = (x, label, sub, ly) => {
    let s = L(x, ly + 16, x, y + h + 30, { stroke: C.orange, sw: 4, dash: "10 7" });
    s += T(x, ly - 30, label, { size: 26, anchor: "middle", fill: C.orange, bold: true });
    s += T(x, ly, sub, { size: 22, anchor: "middle", fill: C.ink2 });
    return s;
  };
  b += cut(235, "先寄存输入", "两拍（L = 2）", 170);
  b += cut(445, "乘积后寄存", "两拍（L = 2）", 170);
  b += T(560, 430, "也有三拍（L = 3）的备选：两处都切", { size: 26, anchor: "middle", fill: C.ink2 });
  b += T(60, 500, "加一级寄存器，一笔计算分两拍完成，稳态仍每拍处理一笔。", { size: 24, fill: C.ink2 });
  b += T(60, 536, "合同要求：延迟最多 3 拍，接口和输入输出约束不变，面积不超过原来的 1.25 倍。", { size: 24, fill: C.ink2 });
  b += T(60, 572, "有没有效，要到阶段 B 改了 RTL、重新综合和仿真才知道。", { size: 24, fill: C.ink2 });
  write("fig5_cuts.svg", svg(W, 610, b));
}

// 图 6：局部变好 ≠ 整体解决（draft §5.2、§7：2.2970、0.673015、阈值 1 ns）
{
  const W = 1080;
  let b = T(60, 70, "把驱动 X 的单元换强以后", { size: 38, bold: true });
  // 示意
  b += R(60, 120, 170, 80, { fill: C.blueSoft, stroke: C.blue });
  b += T(145, 172, "信号 X", { size: 28, anchor: "middle" });
  b += R(60, 230, 170, 80, { fill: C.orangeSoft, stroke: C.orange });
  b += T(145, 282, "信号 Y", { size: 28, anchor: "middle" });
  for (let i = 0; i < 5; i++) {
    b += L(232, 160, 330, 128 + i * 16, { stroke: C.blue, sw: 1.5 });
    b += L(232, 270, 330, 238 + i * 16, { stroke: C.orange, sw: 1.5 });
  }
  b += T(345, 172, "驱动 31 个输出位", { size: 24, fill: C.ink2 });
  b += T(345, 282, "也驱动 31 个负载", { size: 24, fill: C.ink2 });
  b += T(640, 172, "换强了：经过 X 的路径变好", { size: 24, fill: C.blue });
  b += T(640, 282, "最差位置转到了 Y 这一支", { size: 24, fill: C.orange });
  // 柱
  const x0 = 380, k = 230, X = v => x0 + v * k; // 0..2.5
  const bars = [["原来那条路径", 2.30, C.blue], ["全设计最差", 0.67, C.orange]];
  const top = 410;
  for (let v = 0; v <= 2.5; v += 0.5) {
    b += L(X(v), top - 10, X(v), top + 170, { stroke: C.grid, sw: 1.5 });
    b += T(X(v), top + 205, v.toFixed(1), { size: 22, anchor: "middle", fill: C.muted });
  }
  b += T(X(2.5) + 30, top + 205, "ns", { size: 22, fill: C.muted });
  bars.forEach(([name, v, col], i) => {
    const y = top + i * 85;
    b += T(60, y + 40, name + "改善", { size: 26 });
    b += `<rect x="${X(0)}" y="${y}" width="${X(v) - X(0)}" height="56" rx="4" fill="${col}"/>`;
    b += T(X(v) + 12, y + 40, v.toFixed(2), { size: 28, bold: true });
  });
  b += L(X(1), top - 70, X(1), top + 180, { stroke: C.ink, sw: 3, dash: "10 7" });
  b += T(X(1) + 12, top - 62, "Claude 自己写的门槛：", { size: 22, fill: C.ink });
  b += T(X(1) + 12, top - 34, "最差 slack 改善不到 1 ns 就推翻", { size: 22, fill: C.ink });
  b += T(60, top + 260, "只盯着一条路径看是不够的，要看全设计的最差值有没有动。", { size: 26, fill: C.ink2 });
  write("fig6_local_global.svg", svg(W, top + 300, b));
}

// 图 7：改约束 vs 改电路（draft §5.2：基线 -4.1897；输入延迟清零 +1.392277；周期 33.15 + IO 6.63 +0.0023；37 单元全换 -2.1155）
{
  const W = 1080;
  const rows = [
    ["原来", -4.19, C.muted, "基线"],
    ["输入外部延迟清零", 1.39, C.orange, "改约束"],
    ["周期 33.15、外部延迟 6.63", 0.0023, C.orange, "改约束"],
    ["37 个单元全换强驱动", -2.12, C.blue, "改电路"],
  ];
  const x0 = 720, k = 60, X = v => x0 + v * k; // −5..+2
  let b = T(60, 70, "同一条路径，几组对照的 setup slack（ns）", { size: 38, bold: true });
  const top = 130;
  for (let v = -4; v <= 2; v += 2) {
    b += L(X(v), top - 10, X(v), top + rows.length * 80, { stroke: C.grid, sw: 1.5 });
    b += T(X(v), top + rows.length * 80 + 34, (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v), { size: 22, anchor: "middle", fill: C.muted });
  }
  rows.forEach(([name, v, col, tag], i) => {
    const y = top + i * 80, h = 50;
    b += T(60, y + 34, name, { size: 26 });
    b += T(60, y + 62, tag, { size: 20, fill: col === C.muted ? C.ink2 : col });
    const xa = Math.min(X(0), X(v)), w = Math.max(Math.abs(X(v) - X(0)), 4);
    b += `<rect x="${xa}" y="${y}" width="${w}" height="${h}" rx="4" fill="${col}"/>`;
    const lab = v >= 0 ? "+" + (v < 0.01 ? "0.002" : v.toFixed(2)) : "−" + Math.abs(v).toFixed(2);
    b += T(v < 0 ? xa - 10 : xa + w + 10, y + 35, lab, { size: 26, anchor: v < 0 ? "end" : "start", bold: true });
  });
  b += L(X(0), top - 10, X(0), top + rows.length * 80, { stroke: C.ink2, sw: 2.5 });
  const ny = top + rows.length * 80 + 90;
  b += T(60, ny, "改约束的两组转正了，但 RTL 没变、电路没变，只是检查条件变了，不能算优化。", { size: 24, fill: C.ink2 });
  b += T(60, ny + 36, "改电路的这组（只换单元尺寸）仍然违例。流水方案的效果要到阶段 B 才验证。", { size: 24, fill: C.ink2 });
  write("fig7_controls.svg", svg(W, ny + 70, b));
}
