// 生成文章 6（判一句话）的示意图（SVG）。图里的数字都从 tasks/CASE-01 的文件解析，不手填。
// 用法：node docs/posts/figs/article6/make_figs.js   输出到同目录 *.svg；PNG 用 export_png.sh 导出（2 倍，1440 px 宽）。
// 版式沿用文章 3–5：画布宽 720，主体文字 30 左右，辅助文字不小于 22。说明性长句放正文，不放图里。
const fs = require("fs");
const path = require("path");
const OUT = __dirname;
const DIAG = path.join(__dirname, "..", "..", "..", "..", "tasks", "CASE-01", "diag");
const W = 720;

const C = {
  surface: "#fcfcfb", ink: "#0b0b0b", ink2: "#52514e", muted: "#8a8986",
  grid: "#e4e3df", line: "#c9c8c3", blue: "#2a78d6", orange: "#eb6834",
  blueSoft: "#dbe8f8", orangeSoft: "#fbe3d8", graySoft: "#efeeea",
};
const FONT = "'Microsoft YaHei','PingFang SC','Noto Sans CJK SC','Source Han Sans SC',sans-serif";
const MONO = "Consolas,Menlo,'Courier New',monospace";
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
  `<text x="${x}" y="${y}" font-size="${o.size || 30}" fill="${o.fill || C.ink}" font-weight="${o.bold ? 700 : 400}" text-anchor="${o.anchor || "start"}"${o.mono ? ` font-family="${MONO}"` : ""}>${esc(s)}</text>`;
const R = (x, y, w, h, o = {}) =>
  `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${o.rx ?? 10}" fill="${o.fill || "none"}" stroke="${o.stroke || "none"}" stroke-width="${o.sw || 2}"${o.dash ? ` stroke-dasharray="${o.dash}"` : ""}/>`;
const L = (x1, y1, x2, y2, o = {}) =>
  `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${o.stroke || C.ink2}" stroke-width="${o.sw || 2}"${o.dash ? ` stroke-dasharray="${o.dash}"` : ""}${o.arrow ? ` marker-end="url(#arr)"` : ""}/>`;
const title = (t, sub) => T(36, 58, t, { size: 36, bold: true }) + (sub ? T(36, 100, sub, { size: 24, fill: C.ink2 }) : "");
const write = (name, s) => { fs.writeFileSync(path.join(OUT, name), s); console.log(name); };

// ---------- 从 CASE-01 的文件取数 ----------
const read = (...p) => fs.readFileSync(path.join(DIAG, ...p), "utf8").split(/\r?\n/);
const slackOf = ls => Number(ls.find(l => /slack \(/.test(l)).trim().split(/\s+/)[0]);
const report = read("package", "path_report.rpt");
const summary = read("package", "slack_summary.tsv");
const base6 = Number(summary.find(l => l.startsWith("WS\tss_n40C_1v60\tmax")).split("\t")[3]);
const base4 = slackOf(report);
const xPath = slackOf(read("queries", "recheck", "rc_A-1-083", "query_full.txt"));
const xWorst = slackOf(read("queries", "recheck", "rc_A-2-034", "query_full.txt"));
const gainPath = xPath - base4, gainWorst = xWorst - base6;
const portRow = ls => ls.find(l => /in_b\[2\] \(in\)/.test(l)).trim().split(/\s+/);
const repPort = portRow(report);                     // 扇出 电容 slew 延迟 时刻 ^ in_b[2] (in)
const portBase = repPort[3];
const h6 = read("queries", "recheck", "rc_A-1-099", "query_full.txt");
const portCtl = portRow(h6)[0], slackCtl = slackOf(h6);
const b02 = read("queries", "base", "base_B02_worst_path_d6", "query_full.txt");
const arrival = Number(b02.find(l => /data arrival time/.test(l)).trim().split(/\s+/)[0]);
const portTime = Number(portRow(b02)[4]);
const truth = arrival - portTime;
const tol = 2 * 0.00005 + 0.05;                      // 两个操作数的舍入误差，加一位小数的半个末位
const claimed = 25.6, over = (truth - claimed) - tol;
const neg = (v, d) => (v < 0 ? "−" : "") + Math.abs(v).toFixed(d);
if (portBase !== portCtl) throw new Error("control run changed the port delay; figure 4 text no longer holds");
if (slackCtl !== base4) throw new Error("control run changed the slack; figure 4 text no longer holds");
if (!(gainWorst < 1 && gainPath > 1)) throw new Error("the two gains no longer straddle 1 ns");

// ---------- 图 1：判定这句话需要什么 ----------
{
  const card = (y, say, where, tag, why, fill, color) =>
    R(36, y, 648, 134, { fill }) +
    T(58, y + 44, say, { size: 25, bold: true }) +
    T(58, y + 84, where, { size: 22, fill: C.ink2 }) +
    T(58, y + 118, why, { size: 23, fill: C.ink2 }) +
    T(662, y + 84, tag, { size: 30, bold: true, fill: color, anchor: "end" });
  let b = title("判定这句话需要什么", "不看写在哪，也不看语气");
  b += card(130, "_11509_ 的 fanout 为 31", "写在事实部分", "事实", "报告里直接读到", C.blueSoft, C.blue);
  b += card(278, "_11509_ 是饱和判断", "规程举的例子", "假设", "材料没有网表，对不上 RTL", C.orangeSoft, C.orange);
  b += card(426, "buf_2 驱动 19 个负载只耗时 0.309 ns", "写在假设部分", "事实", "报告一行写全，再比大小", C.blueSoft, C.blue);
  b += card(574, "_12026_ 是 out_data[0] 的输出寄存器", "写在事实部分", "假设", "要看网表", C.orangeSoft, C.orange);
  write("fig1_split.svg", svg(738, b));
}

// ---------- 图 2：同一次换单元，两个数 ----------
{
  const x0 = 58, scale = 200; // 每 ns 的像素
  let b = title("同一次换单元，两个数", "模型的条件：最差 slack 改善不到 1 ns 就算推翻");
  const bar = (y, head, sub, gain, fill, color) =>
    T(x0, y, head, { size: 26, bold: true }) +
    T(x0, y + 36, sub, { size: 23, fill: C.ink2 }) +
    R(x0, y + 54, gain * scale, 54, { fill, rx: 6 }) +
    L(x0 + scale, y + 46, x0 + scale, y + 116, { dash: "8 6", stroke: C.ink2 }) +
    T(Math.max(x0 + gain * scale, x0 + scale) + 12, y + 92, `${gain.toFixed(2)} ns`, { size: 28, bold: true, fill: color });
  b += bar(160, "经过 X 的那条路径", `${neg(base4, 4)} → ${neg(xPath, 4)} ns`, gainPath, C.line, C.ink2);
  b += bar(320, "全设计输入到寄存器路径的最差值", `${neg(base6, 6)} → ${neg(xWorst, 6)} ns`, gainWorst, C.orange, C.orange);
  const x1 = x0 + scale;
  b += T(x1, 468, "1 ns", { size: 24, fill: C.ink2, anchor: "middle" });
  b += T(36, 528, "模型说的是最差 slack，看第二个数：判反对。", { size: 26, fill: C.ink2 });
  write("fig2_x.svg", svg(558, b));
}

// ---------- 图 3：容差数轴 ----------
{
  const lo = 25.55, hi = 25.75, xa = 50, xb = 670;
  const X = v => xa + (v - lo) / (hi - lo) * (xb - xa);
  const y = 300;
  let b = title(`超了 ${over.toFixed(4)}，也算超线`, "模型写\"约 25.6 ns\"");
  b += R(X(truth - tol), y - 34, X(truth + tol) - X(truth - tol), 68, { fill: C.blueSoft, rx: 4 });
  b += T(X(truth), y - 50, `容差 ±${tol.toFixed(4)}`, { size: 25, fill: C.blue, anchor: "middle", bold: true });
  b += L(xa, y, xb, y, { sw: 3, stroke: C.ink2 });
  b += L(X(truth), y - 34, X(truth), y + 34, { sw: 4, stroke: C.blue });
  b += T(X(truth), y + 72, `真实值 ${truth.toFixed(6)}`, { size: 25, bold: true, anchor: "middle" });
  b += `<circle cx="${X(claimed)}" cy="${y}" r="11" fill="${C.orange}"/>`;
  b += T(X(claimed), y - 92, "模型写的 25.6", { size: 25, bold: true, fill: C.orange, anchor: "middle" });
  b += L(X(claimed), y - 80, X(claimed), y - 14, { stroke: C.orange });
  b += T(36, 440, `实际差 ${(truth - claimed).toFixed(4)}，容差 ${tol.toFixed(4)}：判推翻。`, { size: 26, fill: C.ink2 });
  b += T(36, 482, "写成 25.7 就在线内。", { size: 26, fill: C.ink2 });
  write("fig3_tol.svg", svg(512, b));
}

// ---------- 图 4：先看对照有没有生效 ----------
{
  const row = (y, head, val, note, fill, color) =>
    R(36, y, 648, 104, { fill }) +
    T(58, y + 44, head, { size: 26, bold: true }) +
    T(58, y + 82, note, { size: 23, fill: C.ink2 }) +
    T(662, y + 66, val, { size: 34, bold: true, fill: color, anchor: "end" });
  let b = title("先看对照有没有生效", "看被改的那一级：in_b[2] 端口的延迟");
  b += row(130, "原报告", `${portBase} ns`, "基线", C.graySoft, C.ink);
  b += row(250, "set_drive 0 本该得到", "约 0 ns", "判定条件写的生效标志", C.blueSoft, C.blue);
  b += row(370, "实际跑出来", `${portCtl} ns`, `slack 也还是 ${neg(slackCtl, 4)} ns`, C.orangeSoft, C.orange);
  b += T(36, 524, "这一级没变，对照没生效：记未判定。", { size: 26, fill: C.ink2 });
  write("fig4_h6.svg", svg(554, b));
}

// ---------- 图 5：两关 ----------
{
  let b = title("依据工具输出判假设，要过两关");
  const gate = (y, h, head, items, fill, color) => {
    let s = R(36, y, 648, h, { fill }) + T(58, y + 46, head, { size: 28, bold: true, fill: color });
    items.forEach((t, i) => { s += T(58, y + 92 + i * 38, t, { size: 24 }); });
    return s;
  };
  b += gate(96, 294, "第一关：通用五项", ["工具正常结束", "日志没有 Error（严格模式：无未审阅 Warning）", "输出非空", "查的对象对得上", "环境核对已通过"], C.blueSoft, C.blue);
  b += T(662, 142, "H6 过了", { size: 26, bold: true, fill: C.blue, anchor: "end" });
  b += L(360, 394, 360, 440, { arrow: true, sw: 3 });
  b += gate(446, 136, "第二关：这条假设自己的判定条件", ["H6 的第一句：先确认对照生效"], C.orangeSoft, C.orange);
  b += T(662, 562, "H6 卡在这里", { size: 26, bold: true, fill: C.orange, anchor: "end" });
  b += L(360, 586, 360, 632, { arrow: true, sw: 3 });
  b += T(360, 672, "支持 / 反对 / 未判定", { size: 28, bold: true, anchor: "middle" });
  write("fig5_gates.svg", svg(702, b));
}
