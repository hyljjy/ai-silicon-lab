// 生成文章 1 公众号版的示意图（SVG）。数字取自 docs/posts/article1_draft.md，出处见各图注释。
// 用法：node docs/posts/figs/article1/make_figs.js   输出到同目录 *.svg
// 版式按手机正文宽度 360–390 px 设计：画布宽 720，导出 2 倍 PNG（1440 px）；
// 主体文字 30 左右（显示约 15 px），辅助文字不小于 24（显示约 12 px）。说明性长句放正文，不放图里。
const fs = require("fs");
const path = require("path");
const OUT = __dirname;
const W = 720;

const C = {
  surface: "#fcfcfb", ink: "#0b0b0b", ink2: "#52514e", muted: "#8a8986",
  grid: "#e4e3df", line: "#c9c8c3", blue: "#2a78d6", orange: "#eb6834",
  blueSoft: "#dbe8f8", orangeSoft: "#fbe3d8", graySoft: "#efeeea",
};
const FONT = "'Microsoft YaHei','PingFang SC','Noto Sans CJK SC','Source Han Sans SC',sans-serif";
const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const num = v => (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v);

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
const write = (name, s) => { fs.writeFileSync(path.join(OUT, name), s); console.log(name); };

// 图 1：这个系列怎么做（PLAN_v1.0 第 2 节）
{
  const steps = [
    ["①", "冻结题目和规则", "", false],
    ["②", "诊断，逐条核对", "本文 · 阶段 A", true],
    ["③", "改 RTL，再复验", "下一篇 · 阶段 B，最多两轮", false],
    ["④", "收益或失败都报告", "", false],
  ];
  let b = T(36, 58, "这个系列怎么做", { size: 36, bold: true });
  let y = 90;
  steps.forEach(([n, t, tag, hi], i) => {
    const h = tag ? 112 : 80;
    b += R(36, y, 648, h, { fill: hi ? C.blueSoft : C.graySoft, stroke: hi ? C.blue : "none" });
    b += T(64, y + 52, n, { size: 34, bold: true, fill: hi ? C.blue : C.ink2 });
    b += T(120, y + 52, t, { size: 32, bold: true });
    if (tag) b += T(120, y + 92, tag, { size: 26, fill: hi ? C.blue : C.ink2 });
    if (i < steps.length - 1) b += L(360, y + h + 2, 360, y + h + 28, { arrow: true });
    y += h + 32;
  });
  write("fig1_series.svg", svg(y - 4, b));
}

// 图 2：RTL 功能示意（draft §1：四路 signed 16×16，34 位和，饱和到 32 位，只有输出寄存器，L = 1）
{
  let b = T(36, 58, "被测电路：RTL 功能示意", { size: 36, bold: true });
  b += T(36, 100, "不是综合后的网表结构", { size: 26, fill: C.ink2 });
  const rows = [
    ["4 对输入，各 16 位有符号", C.graySoft],
    ["4 个乘法", C.graySoft],
    ["4 个乘积相加，34 位", C.graySoft],
    ["饱和到 32 位", C.graySoft],
    ["输出寄存器（只有这一级）", C.blueSoft],
  ];
  let y = 130;
  const ys = [];
  rows.forEach(([t, fill], i) => {
    b += R(110, y, 460, 70, { fill, stroke: i === 4 ? C.blue : "none" });
    b += T(340, y + 46, t, { size: 30, anchor: "middle" });
    ys.push(y);
    if (i < rows.length - 1) b += L(340, y + 72, 340, y + 98, { arrow: true });
    y += 100;
  });
  const top = ys[1], bot = ys[3] + 70;
  b += L(596, top, 596, bot, { stroke: C.orange, sw: 3 });
  b += L(584, top, 608, top, { stroke: C.orange, sw: 3 });
  b += L(584, bot, 608, bot, { stroke: C.orange, sw: 3 });
  b += T(620, (top + bot) / 2 - 8, "同一", { size: 28, fill: C.orange, bold: true });
  b += T(620, (top + bot) / 2 + 30, "拍内", { size: 28, fill: C.orange, bold: true });
  b += T(36, y + 20, "时钟周期 27.91 ns，延迟 L = 1", { size: 28, fill: C.ink2 });
  write("fig2_circuit.svg", svg(y + 50, b));
}

// 图 3：最差路径的时间账（draft §1：5.5820、5.8911、31.5439、27.3541、0.5559、27.91）
{
  const x0 = 36, k = 20, X = t => x0 + t * k; // 0..32 ns → 36..676
  let b = T(36, 58, "最差路径的时间账", { size: 36, bold: true });
  b += T(36, 100, "ss，1.60 V，−40 °C", { size: 26, fill: C.ink2 });
  const y = 200, h = 90;
  b += `<rect x="${X(0)}" y="${y}" width="${X(5.582) - X(0) - 2}" height="${h}" rx="4" fill="${C.muted}"/>`;
  b += `<rect x="${X(5.582)}" y="${y}" width="${X(5.8911) - X(5.582)}" height="${h}" fill="${C.ink2}"/>`;
  b += `<rect x="${X(5.8911) + 2}" y="${y}" width="${X(31.5439) - X(5.8911) - 2}" height="${h}" rx="4" fill="${C.blue}"/>`;
  b += T(X(2.79), y + 38, "外部", { size: 26, anchor: "middle", fill: "#ffffff" });
  b += T(X(2.79), y + 72, "5.58", { size: 26, anchor: "middle", fill: "#ffffff" });
  b += T(X(17.5), y + 40, "37 个组合单元", { size: 30, anchor: "middle", fill: "#ffffff" });
  b += T(X(17.5), y + 76, "25.65", { size: 30, anchor: "middle", fill: "#ffffff", bold: true });
  b += L(X(5.74), y - 4, X(7.5), y - 34, { stroke: C.ink2, sw: 1.5 });
  b += T(X(7.7), y - 38, "端口驱动 0.31", { size: 26, fill: C.ink2 });
  // 要求时刻
  b += L(X(27.3541), 150, X(27.3541), y + h + 6, { stroke: C.orange, sw: 3 });
  b += T(X(27.3541) - 8, 140, "最晚应到 27.35", { size: 26, fill: C.orange, anchor: "end", bold: true });
  // 刻度
  const ay = y + h + 16;
  b += L(X(0), ay, X(32), ay, { stroke: C.line });
  for (let t = 0; t <= 32; t += 8) {
    b += L(X(t), ay, X(t), ay + 8, { stroke: C.line });
    b += T(t === 32 ? X(t) + 8 : X(t), ay + 36, t === 32 ? "32 ns" : `${t}`, { size: 24, anchor: t === 32 ? "end" : "middle", fill: C.muted });
  }
  // 实际到达与晚到
  const ly = ay + 80;
  b += `<rect x="${X(27.3541)}" y="${ly}" width="${X(31.5439) - X(27.3541)}" height="14" rx="4" fill="${C.orange}"/>`;
  b += T(X(27.3541) - 14, ly + 14, "晚了 4.19 ns", { size: 32, anchor: "end", fill: C.orange, bold: true });
  b += T(X(31.5439), ly + 60, "实际到达 31.54", { size: 26, anchor: "end", fill: C.blue });
  b += T(X(31.5439), ly + 100, "setup slack = −4.19", { size: 26, anchor: "end", fill: C.orange });
  write("fig3_budget.svg", svg(ly + 126, b));
}

// 图 4：6 个角的最差 setup slack（slack_summary.tsv 的 WS 行：-4.189726 -0.687278 11.185458 11.317222 15.871506 15.894229）
{
  const rows = [
    ["ss", "−40 °C", -4.19], ["ss", "100 °C", -0.69],
    ["tt", "25 °C", 11.19], ["tt", "100 °C", 11.32],
    ["ff", "−40 °C", 15.87], ["ff", "100 °C", 15.89],
  ];
  const x0 = 300, k = 19, X = v => x0 + v * k; // −5..+16 → 205..604
  let b = T(36, 58, "6 个角的最差 setup slack", { size: 36, bold: true });
  b += T(36, 100, "单位 ns；只有两个 ss 角违例", { size: 26, fill: C.ink2 });
  const top = 130, rh = 74;
  for (const v of [-5, 0, 5, 10, 15]) {
    b += L(X(v), top, X(v), top + rows.length * rh, { stroke: v === 0 ? C.ink2 : C.grid, sw: v === 0 ? 2.5 : 1.5 });
    b += T(X(v), top + rows.length * rh + 34, num(v), { size: 24, anchor: "middle", fill: C.muted });
  }
  rows.forEach(([p, temp, v], i) => {
    const y = top + i * rh + 12, h = 50, neg = v < 0;
    b += T(36, y + 36, p, { size: 30, bold: true });
    b += T(80, y + 36, temp, { size: 28, fill: C.ink2 });
    const xa = Math.min(X(0), X(v)), w = Math.abs(X(v) - X(0));
    b += `<rect x="${xa}" y="${y}" width="${w}" height="${h}" rx="4" fill="${neg ? C.orange : C.blue}"/>`;
    b += T(neg ? X(0) + 12 : xa + w + 10, y + 36, (v > 0 ? "+" : "−") + Math.abs(v).toFixed(2), { size: 28, bold: neg });
  });
  b += T(36, top + rows.length * rh + 80, "电压：ss 1.60 V，tt 1.80 V，ff 1.95 V", { size: 24, fill: C.ink2 });
  write("fig4_corners.svg", svg(top + rows.length * rh + 108, b));
}

// 图 5：主要流水候选（Kimi round1 B.md:520-526、DeepSeek round1 C.md:146-148；L = 2 的两种见 draft §4）
{
  const reg = s => ({ t: s, reg: true }), comb = s => ({ t: s, reg: false });
  const rows = [
    ["候选 1：先寄存输入（L = 2）", [reg(["输入", "寄存"]), comb(["乘·加", "·饱和"]), reg(["输出", "寄存"])]],
    ["候选 2：乘积后寄存（L = 2）", [comb(["乘法", ""]), reg(["乘积", "寄存"]), comb(["加·饱和", ""]), reg(["输出", "寄存"])]],
    ["备选：乘积后、求和后各寄存（L = 3）", [comb(["乘法", ""]), reg(["乘积", "寄存"]), comb(["求和", ""]), reg(["和", "寄存"]), comb(["饱和", ""]), reg(["输出", "寄存"])]],
  ];
  let b = T(36, 58, "主要的流水候选", { size: 36, bold: true });
  b += T(36, 100, "蓝框是寄存器；都要到阶段 B 才验证", { size: 26, fill: C.ink2 });
  let y = 150;
  rows.forEach(([title, boxes]) => {
    b += T(36, y, title, { size: 28, bold: true });
    const n = boxes.length, gap = 14, bw = Math.min(150, (648 - gap * (n - 1)) / n), bh = 82;
    let x = 36;
    boxes.forEach((bx, i) => {
      const yy = y + 20;
      b += R(x, yy, bw, bh, { fill: bx.reg ? C.blueSoft : C.graySoft, stroke: bx.reg ? C.blue : "none" });
      if (bx.t[1]) {
        b += T(x + bw / 2, yy + 36, bx.t[0], { size: 26, anchor: "middle" });
        b += T(x + bw / 2, yy + 68, bx.t[1], { size: 26, anchor: "middle" });
      } else {
        b += T(x + bw / 2, yy + 52, bx.t[0], { size: 26, anchor: "middle" });
      }
      if (i < n - 1) b += L(x + bw + 1, yy + bh / 2, x + bw + gap - 1, yy + bh / 2, { sw: 2 });
      x += bw + gap;
    });
    y += 160;
  });
  write("fig5_cuts.svg", svg(y - 30, b));
}

// 图 6：局部变好 ≠ 整体解决（draft §5.2、§7：2.2970、0.673015；1 ns 是 Claude 自己写的推翻条件）
{
  let b = T(36, 58, "把驱动 X 的单元换强以后", { size: 36, bold: true });
  const fan = (y, label, col, soft, l1, l2) => {
    let s = R(36, y, 150, 76, { fill: soft, stroke: col });
    s += T(111, y + 50, label, { size: 30, anchor: "middle" });
    for (let i = 0; i < 5; i++) s += L(188, y + 38, 250, y + 6 + i * 16, { stroke: col, sw: 1.5 });
    s += T(270, y + 32, l1, { size: 26, fill: C.ink2 });
    s += T(270, y + 68, l2, { size: 26, fill: col, bold: true });
    return s;
  };
  b += fan(100, "信号 X", C.blue, C.blueSoft, "通向 31 个输出位", "换强后，这一支变好");
  b += fan(206, "信号 Y", C.orange, C.orangeSoft, "也有 31 个负载", "最差位置转到这一支");
  const x0 = 36, k = 230, X = v => x0 + v * k; // 0..2.5 → 36..611
  const top = 350;
  const bars = [["原来那条路径的改善", 2.2970, C.blue], ["全设计最差的改善", 0.673015, C.orange]];
  bars.forEach(([name, v, col], i) => {
    const y = top + i * 120;
    b += T(36, y, name, { size: 28 });
    b += `<rect x="${X(0)}" y="${y + 16}" width="${X(v) - X(0)}" height="56" rx="4" fill="${col}"/>`;
    const lx = i === 1 ? X(1) + 14 : X(v) + 12;
    b += T(lx, y + 56, v.toFixed(2) + " ns", { size: 30, bold: true });
  });
  b += L(X(1), top + 10, X(1), top + 210, { stroke: C.ink, sw: 3, dash: "9 6" });
  b += T(36, top + 262, "虚线：Claude 自己写的推翻条件——", { size: 26, fill: C.ink });
  b += T(36, top + 298, "全设计最差改善不到 1 ns，假设不成立", { size: 26, fill: C.ink });
  write("fig6_local_global.svg", svg(top + 326, b));
}

// 图 7：同一起终点的几组独立对照（draft §5.2：基线 -4.189726；输入延迟清零 +1.392277；
// 周期 33.15 且输入/输出 max delay 6.63 时 +0.0023；37 个单元换强驱动 -2.1155）
{
  const rows = [
    ["原来（周期 27.91）", "基线", -4.19, C.muted],
    ["输入外部延迟清零", "改约束", 1.39, C.orange],
    ["周期 33.15，输入/输出延迟 6.63", "改约束", 0.0023, C.orange],
    ["37 个单元换强驱动", "改电路", -2.12, C.blue],
  ];
  const x0 = 426, k = 90, X = v => x0 + v * k; // −4.5..+2.5 → 21..651
  let b = T(36, 58, "同一起终点，几组独立对照", { size: 36, bold: true });
  b += T(36, 100, "setup slack，单位 ns；每组都从基线出发", { size: 26, fill: C.ink2 });
  const top = 140, rh = 128;
  rows.forEach(([name, tag, v, col], i) => {
    const y = top + i * rh;
    b += T(36, y + 30, name, { size: 28 });
    b += T(684, y + 30, tag, { size: 26, anchor: "end", fill: col === C.muted ? C.ink2 : col, bold: true });
    const by = y + 48, h = 50;
    b += L(X(0), by - 8, X(0), by + h + 8, { stroke: C.ink2, sw: 2.5 });
    if (Math.abs(v) < 0.05) {
      b += `<path d="M${X(v)} ${by + 4} L${X(v) + 14} ${by + h / 2} L${X(v)} ${by + h - 4} L${X(v) - 14} ${by + h / 2} z" fill="${col}"/>`;
      b += T(X(v) + 26, by + 36, "+0.002（近零）", { size: 26, bold: true });
    } else {
      const xa = Math.min(X(0), X(v)), w = Math.abs(X(v) - X(0));
      b += `<rect x="${xa}" y="${by}" width="${w}" height="${h}" rx="4" fill="${col}"/>`;
      b += T(v < 0 ? X(0) + 12 : xa + w + 10, by + 36, (v > 0 ? "+" : "−") + Math.abs(v).toFixed(2), { size: 28, bold: true });
    }
  });
  const by = top + rows.length * rh;
  for (const v of [-4, -2, 0, 2]) b += T(X(v), by + 32, num(v), { size: 24, anchor: "middle", fill: C.muted });
  write("fig7_controls.svg", svg(by + 56, b));
}
