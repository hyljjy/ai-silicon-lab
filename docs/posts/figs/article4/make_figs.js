// 生成文章 4（温度反转）的数据图和示意图（SVG）。数据图的数字都从同目录 sta_output.txt（OpenSTA 原样输出）解析，不手填。
// 用法：node docs/posts/figs/article4/make_figs.js   输出到同目录 *.svg；PNG 用 export_png.sh 导出（2 倍，1440 px 宽）。
// 版式沿用文章 1、3：画布宽 720，主体文字 30 左右，辅助文字不小于 22。说明性长句放正文，不放图里。
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
const MONO = "Consolas,Menlo,'Courier New',monospace";
const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const num = (v, d = 3) => (v < 0 ? "−" : "") + Math.abs(v).toFixed(d);

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
  const lh = o.lh || 36, y0 = y + h / 2 - ((lines.length - 1) * lh) / 2 + 9;
  lines.forEach((t, i) => {
    const [txt, to] = Array.isArray(t) ? t : [t, {}];
    s += T(x + w / 2, y0 + i * lh, txt, { size: 24, anchor: "middle", ...to });
  });
  return s;
};
const COND = "综合后、理想时钟、不读寄生、只计引脚电容";
const COND2 = "T = 27.91 ns；输出负载 0.0024 pF";

// ---------- 解析 sta_output.txt ----------
const RAW = fs.readFileSync(path.join(OUT, "sta_output.txt"), "utf8");
const CORNERS = ["tt_025C_1v80", "tt_100C_1v80", "ss_100C_1v60", "ss_n40C_1v60", "ff_n40C_1v95", "ff_100C_1v95"];
// 第一段：六个 -format end 的 setup 行，顺序同 CORNERS
const endRows = [...RAW.matchAll(/^_12026_\/D \(\S+\)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+) \((?:MET|VIOLATED)\)$/gm)];
if (endRows.length !== 6) throw new Error(`expected 6 setup end rows, got ${endRows.length}`);
const setup = {};
CORNERS.forEach((c, i) => { const [, req, arr, slk] = endRows[i]; setup[c] = { req: +req, arr: +arr, slack: +slk }; });
// 后两段：完整路径报告，按 "Startpoint:" 切块
const blocks = RAW.split(/^Startpoint: /m).slice(1).map(b => {
  const g = re => { const m = b.match(re); if (!m) throw new Error(`no match ${re} in block ${b.slice(0, 60)}`); return m; };
  const o = { start: b.split(" ")[0], corner: g(/^Corner: (\S+)/m)[1], type: g(/^Path Type: (\S+)/m)[1] };
  o.arrival = +g(/^\s+(-?[\d.]+)\s+data arrival time$/m)[1];
  o.slack = +g(/^\s+(-?[\d.]+)\s+slack \(/m)[1];
  if (o.type === "min") {
    o.rst = +g(/^\s+(-?[\d.]+)\s+-?[\d.]+ \^ rst \(in\)$/m)[1];
    o.nor = +g(/^\s+(-?[\d.]+)\s+-?[\d.]+ v _11506_\/Y/m)[1];
    o.hold = +g(/^\s+(-?[\d.]+)\s+-?[\d.]+\s+library hold time$/m)[1];
  } else {
    const m = g(/^\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+) \^ _11451_\/Y/m);
    o.u = { cap: +m[1], slew: +m[2], delay: +m[3] };
    o.setupTime = -g(/^\s+(-?[\d.]+)\s+-?[\d.]+\s+library setup time$/m)[1];
  }
  return o;
});
const hold = {}, full = {};
blocks.forEach(b => { (b.type === "min" ? hold : full)[b.corner] = b; });
CORNERS.forEach(c => { if (!hold[c]) throw new Error(`missing hold ${c}`); });
["ss_n40C_1v60", "ss_100C_1v60"].forEach(c => { if (!full[c]) throw new Error(`missing full setup ${c}`); });
// 自检：slack 与报告一致
const close = (a, b, msg) => { if (Math.abs(a - b) > 2e-6) throw new Error(`${msg}: ${a} vs ${b}`); };
["ss_n40C_1v60", "ss_100C_1v60"].forEach(c => {
  close(full[c].slack, setup[c].slack, `setup slack ${c}`);
  close(27.91 - full[c].setupTime - full[c].arrival, full[c].slack, `setup account ${c}`);
});
CORNERS.forEach(c => close(hold[c].arrival - hold[c].hold, hold[c].slack, `hold account ${c}`));

// 图 1：六个角的最差 setup slack（sta_output.txt 第一段）
{
  const pairs = [["ss", "1.60 V", "ss_n40C_1v60", "−40 °C", "ss_100C_1v60", "100 °C"],
    ["tt", "1.80 V", "tt_025C_1v80", "25 °C", "tt_100C_1v80", "100 °C"],
    ["ff", "1.95 V", "ff_n40C_1v95", "−40 °C", "ff_100C_1v95", "100 °C"]];
  const lo = -5, hi = 17, x0 = 150, x1 = 560, X = v => x0 + (v - lo) / (hi - lo) * (x1 - x0);
  let b = title("六个角的最差 setup slack", "每对工艺和电压相同，只差温度；越往左越差");
  let y = 140;
  pairs.forEach(([p, v, cc, tc, ch, th]) => {
    b += T(36, y + 30, `${p}，${v}`, { size: 26, bold: true });
    [[cc, tc, C.blue], [ch, th, C.orange]].forEach(([c, t, col], k) => {
      const s = setup[c].slack, yy = y + 44 + k * 44;
      const xa = Math.min(X(0), X(s)), w = Math.abs(X(s) - X(0));
      b += T(36, yy + 30, t, { size: 22, fill: col, bold: true });
      b += `<rect x="${xa}" y="${yy + 8}" width="${w}" height="30" rx="3" fill="${col}"/>`;
      b += T(684, yy + 31, num(s), { size: 24, anchor: "end", fill: col, bold: true, mono: true });
    });
    y += 150;
  });
  b += L(X(0), 136, X(0), y - 14, { stroke: C.ink2 });
  b += T(X(0), y + 14, "0", { size: 22, anchor: "middle", fill: C.muted });
  b += T(684, y + 14, "单位 ns", { size: 22, anchor: "end", fill: C.muted });
  b += R(36, y + 36, 648, 70, { fill: C.orangeSoft });
  b += T(56, y + 81, `只看 ss 高温：${num(setup.ss_100C_1v60.slack)}；低温：${num(setup.ss_n40C_1v60.slack)}`, { size: 24, bold: true });
  b += T(36, y + 140, "CASE-01 网表，Sky130 HD；" + COND2, { size: 22, fill: C.ink2 });
  b += T(36, y + 172, COND, { size: 22, fill: C.ink2 });
  write("fig1_corners.svg", svg(y + 196, b));
}

// 图 2：两股力量（示意，无数字）
{
  let b = title("降温时，两股力量方向相反", "示意图");
  b += box(220, 130, 280, 70, [["温度降低", { bold: true, size: 28 }]]);
  b += L(300, 202, 190, 262, { arrow: true }) + L(420, 202, 530, 262, { arrow: true });
  b += box(36, 268, 312, 200, [["路更好走", { bold: true, fill: C.blue, size: 28 }], "迁移率变大", "电流变大", ["单元更快", { bold: true }]], { fill: C.blueSoft });
  b += box(372, 268, 312, 200, [["门槛更高", { bold: true, fill: C.orange, size: 28 }], "Vth 升高，余量变小", "电流变小", ["单元更慢", { bold: true }]], { fill: C.orangeSoft });
  b += L(192, 470, 192, 520, { arrow: true }) + L(528, 470, 528, 520, { arrow: true });
  b += box(36, 526, 648, 120, [["谁赢，看余量本来有多大", { bold: true, size: 28 }], "余量 = 栅压 − 门槛（Vth）"], { fill: "#ffffff", stroke: C.ink2 });
  b += T(36, 692, "余量小：门槛一边可能占优，低温更慢", { size: 24 });
  b += T(36, 730, "余量大：迁移率一边可能占优，高温更慢", { size: 24 });
  write("fig2_forces.svg", svg(760, b));
}

// 图 3：同样的门槛变化，在余量大小不同时占比不同（示意，不按比例，不是 Sky130 数值）
{
  let b = title("同样升高一截门槛，占比不一样", "示意图，不按比例，不是 Sky130 的数值");
  const bar = (y, label, vdd, vth, dv, note) => {
    const k = 520 / 2.0, x0 = 140;
    let s = T(36, y + 34, label, { size: 26, bold: true });
    s += `<rect x="${x0}" y="${y}" width="${vth * k}" height="48" rx="4" fill="${C.line}"/>`;
    s += `<rect x="${x0 + vth * k}" y="${y}" width="${dv * k}" height="48" fill="${C.orange}"/>`;
    s += `<rect x="${x0 + (vth + dv) * k}" y="${y}" width="${(vdd - vth - dv) * k}" height="48" rx="4" fill="${C.blue}"/>`;
    s += T(x0 + vth * k / 2, y + 33, "门槛", { size: 22, anchor: "middle" });
    s += T(x0 + (vth + dv + (vdd - vth - dv) / 2) * k, y + 33, "余量", { size: 22, anchor: "middle", fill: "#ffffff" });
    s += T(36, y + 92, note, { size: 24, fill: C.ink2 });
    return s;
  };
  b += bar(160, "低电压", 1.3, 0.75, 0.2, "橙色那一截，吃掉了余量的一大块");
  b += bar(320, "高电压", 1.95, 0.75, 0.2, "同样一截，只占余量的一小块");
  b += R(36, 470, 648, 48, { fill: C.orange, rx: 4 });
  b += T(360, 503, "橙色：降温让门槛升高的那一截", { size: 24, anchor: "middle", fill: "#ffffff", bold: true });
  b += T(36, 572, "要比的是比例，不是绝对量。", { size: 26, bold: true });
  b += T(36, 610, "另一边的迁移率变化，比例和电压关系不大。", { size: 24, fill: C.ink2 });
  write("fig3_overdrive.svg", svg(640, b));
}

// 图 4：低温比高温差多少（sta_output.txt 第一段，低温 slack − 高温 slack 取反）
{
  const rows = [["ss，1.60 V", "−40 / 100 °C", setup.ss_100C_1v60.slack - setup.ss_n40C_1v60.slack],
    ["tt，1.80 V", "25 / 100 °C", setup.tt_100C_1v80.slack - setup.tt_025C_1v80.slack],
    ["ff，1.95 V", "−40 / 100 °C", setup.ff_100C_1v95.slack - setup.ff_n40C_1v95.slack]];
  const k = 300 / 3.6, xb = 230;
  let b = title("三对角的低温 slack 损失不同", "低温比高温的最差 setup slack 差多少");
  let y = 150;
  rows.forEach(([n, t, d]) => {
    b += T(36, y + 30, n, { size: 26, bold: true }) + T(36, y + 64, t, { size: 22, fill: C.ink2 });
    b += `<rect x="${xb}" y="${y + 8}" width="${Math.max(d * k, 3)}" height="40" rx="3" fill="${C.orange}"/>`;
    b += T(xb + Math.max(d * k, 3) + 12, y + 38, num(d) + " ns", { size: 26, bold: true, fill: C.orange });
    y += 110;
  });
  b += L(xb, 146, xb, y - 20, { stroke: C.ink2 });
  b += T(36, y + 30, "tt 这一对只差 75 °C，另两对差 140 °C；", { size: 24, fill: C.ink2 });
  b += T(36, y + 66, "三对之间工艺也不同，不能单独归因于电压。", { size: 24, fill: C.ink2 });
  b += T(36, y + 112, "CASE-01 网表，Sky130 HD；" + COND2, { size: 22, fill: C.ink2 });
  b += T(36, y + 144, COND, { size: 22, fill: C.ink2 });
  write("fig4_trend.svg", svg(y + 170, b));
}

// 图 5：ss 两个角差的 3.5 ns 拆成两笔（sta_output.txt 第三段两条完整 setup 报告）
{
  const c = full.ss_n40C_1v60, h = full.ss_100C_1v60;
  const dArr = c.arrival - h.arrival, dSet = c.setupTime - h.setupTime, tot = dArr + dSet;
  let b = title("ss 两个角差的 slack，拆成两笔", "ss，1.60 V：−40 °C 比 100 °C");
  const k = 600 / 3.6, x0 = 60;
  b += `<rect x="${x0}" y="150" width="${dArr * k}" height="60" rx="3" fill="${C.orange}"/>`;
  b += `<rect x="${x0 + dArr * k}" y="150" width="${Math.max(dSet * k, 4)}" height="60" fill="${C.ink2}"/>`;
  // 用 4 位小数，两笔相加与合计在显示精度下对得上
  b += T(x0 + 12, 190, `到达时间晚了 ${num(dArr, 4)}`, { size: 26, bold: true, fill: "#ffffff" });
  b += L(x0 + dArr * k + dSet * k / 2, 214, x0 + dArr * k + dSet * k / 2, 262, { stroke: C.ink2 });
  b += T(684, 292, `setup 要求多了 ${num(dSet, 4)}`, { size: 24, anchor: "end", fill: C.ink2, bold: true });
  b += T(36, 360, `合计 ${num(tot, 4)} ns`, { size: 30, bold: true });
  const rows = [["", "−40 °C", "100 °C"],
    ["数据到达时间", num(c.arrival), num(h.arrival)],
    ["setup 要求", num(c.setupTime), num(h.setupTime)],
    ["slack", num(c.slack), num(h.slack)],
    ["最差路径起点", c.start, h.start]];
  let y = 400;
  rows.forEach((r, i) => {
    if (i % 2 === 1) b += R(36, y - 30, 648, 44, { fill: C.graySoft, rx: 4 });
    b += T(56, y, r[0], { size: 24, bold: i === 0 });
    b += T(470, y, r[1], { size: 24, anchor: "end", mono: i > 0, bold: i === 0 });
    b += T(660, y, r[2], { size: 24, anchor: "end", mono: i > 0, bold: i === 0 });
    y += 48;
  });
  b += T(36, y + 10, "两个角的最差路径起点不同，终点相同（_12026_）", { size: 22, fill: C.ink2 });
  b += T(36, y + 42, "slack = 周期 27.91 − setup 要求 − 到达时间；单位 ns", { size: 22, fill: C.ink2 });
  b += T(36, y + 74, COND, { size: 22, fill: C.ink2 });
  write("fig5_ss_split.svg", svg(y + 102, b));
}

// 图 6：最差 hold 路径，ff 两个角（sta_output.txt 第二段 ff 两块）
{
  const c = hold.ff_n40C_1v95, h = hold.ff_100C_1v95;
  let b = title("最差 hold：被触发器自己的要求抢走", "ff，1.95 V；起点是输入端口 rst");
  b += box(36, 130, 150, 64, [["rst 端口", { mono: true }]]);
  b += L(188, 162, 266, 162, { arrow: true });
  b += box(270, 130, 170, 64, [["nor2b 门", {}]]);
  b += L(442, 162, 520, 162, { arrow: true });
  b += box(524, 130, 160, 64, [["寄存器 D", { bold: true }]], { fill: C.blueSoft });
  const rows = [["", "−40 °C", "100 °C"],
    ["数据到达时间", num(c.arrival, 4), num(h.arrival, 4)],
    ["库的 hold 要求", num(c.hold, 4), num(h.hold, 4)],
    ["hold slack", num(c.slack, 4), num(h.slack, 4)]];
  let y = 262;
  rows.forEach((r, i) => {
    if (i % 2 === 1) b += R(36, y - 30, 648, 44, { fill: C.graySoft, rx: 4 });
    b += T(56, y, r[0], { size: 24, bold: i === 0 });
    b += T(470, y, r[1], { size: 24, anchor: "end", mono: i > 0, bold: i === 0 });
    b += T(660, y, r[2], { size: 24, anchor: "end", mono: i > 0, bold: i === 0 });
    y += 48;
  });
  // 变化量换成 ps、三位小数；净变化取 dA − dH，免得两份各自舍入过的 slack 相减后末位对不上
  const dA = (h.arrival - c.arrival) * 1000, dH = (h.hold - c.hold) * 1000, dS = dA - dH;
  const k = 24, xb = 380;
  y += 24;
  b += T(36, y, "从 −40 °C 到 100 °C（单位 ps）：", { size: 26, bold: true });
  y += 30;
  [["数据更慢了（有利）", dA, C.blue], ["hold 要求涨了（不利）", dH, C.orange], ["slack 净变化", dS, C.ink2]].forEach(([t, v, col]) => {
    b += T(56, y + 30, t, { size: 24 });
    const w = Math.abs(v) * k;
    b += `<rect x="${xb}" y="${y + 8}" width="${w}" height="30" rx="3" fill="${col}"/>`;
    b += T(xb + w + 10, y + 32, (v < 0 ? "−" : "+") + Math.abs(v).toFixed(3), { size: 22, bold: true, fill: col, mono: true });
    y += 50;
  });
  b += T(36, y + 26, "hold slack = 到达时间 − hold 要求；表中单位 ns", { size: 22, fill: C.ink2 });
  b += T(36, y + 58, "到达时间含输入端口驱动模型那一段；图中只画网表内部", { size: 22, fill: C.ink2 });
  b += T(36, y + 90, "变化量由报告里已舍入的分项算出，末位可能差 1", { size: 22, fill: C.ink2 });
  b += T(36, y + 122, COND, { size: 22, fill: C.ink2 });
  write("fig6_hold.svg", svg(y + 150, b));
}

// 图 7：hold 要求从哪来（示意，无数字）
{
  let b = title("hold 要求从哪来：把触发器想成一扇门", "示意图");
  b += T(36, 160, "时钟沿到达", { size: 26, bold: true });
  b += L(190, 152, 300, 152, { arrow: true });
  b += box(304, 120, 220, 64, ["内部时钟路径"], { fill: C.graySoft });
  b += L(526, 152, 600, 152, { arrow: true });
  b += box(604, 120, 80, 64, [["关门", { bold: true }]], { fill: C.blueSoft });
  b += T(36, 270, "新数据到 D", { size: 26, bold: true });
  b += L(190, 262, 300, 262, { arrow: true });
  b += box(304, 230, 220, 64, ["内部数据路径"], { fill: C.graySoft });
  b += L(526, 262, 600, 262, { arrow: true });
  b += box(604, 230, 80, 64, [["门口", { bold: true }]], { fill: C.orangeSoft });
  b += R(36, 340, 648, 110, { fill: "#ffffff", stroke: C.ink2 });
  b += T(360, 384, "hold 要求 ≈ 关门用时 − 数据走到门口用时", { size: 26, anchor: "middle", bold: true });
  b += T(360, 424, "数据走得比关门还慢，要求就是负的", { size: 24, anchor: "middle", fill: C.ink2 });
  b += T(36, 500, "两段都随温度变，但变的幅度不一样，", { size: 24 });
  b += T(36, 538, "差值往哪边移都有可能，不跟着“哪个角更快”走。", { size: 24 });
  b += T(36, 586, "触发器内部结构在本文环境里看不到，按通用原理画", { size: 22, fill: C.ink2 });
  write("fig7_door.svg", svg(616, b));
}

// 供正文核对用：打印本文引用的数字
const pr = (k, v, d = 6) => console.log(`  ${k}: ${v.toFixed(d)}`);
console.log("numbers used in article4_public.md:");
CORNERS.forEach(c => pr(`setup slack ${c}`, setup[c].slack));
pr("ss diff", setup.ss_100C_1v60.slack - setup.ss_n40C_1v60.slack);
pr("tt diff", setup.tt_100C_1v80.slack - setup.tt_025C_1v80.slack);
pr("ff diff", setup.ff_100C_1v95.slack - setup.ff_n40C_1v95.slack);
["ss_n40C_1v60", "ss_100C_1v60"].forEach(c => {
  const f = full[c];
  console.log(`  ${c}: start ${f.start} arrival ${f.arrival} setup ${f.setupTime} _11451_/Y cap ${f.u.cap} slew ${f.u.slew} delay ${f.u.delay}`);
});
CORNERS.forEach(c => { const o = hold[c]; console.log(`  hold ${c}: start ${o.start} rst ${o.rst} nor2b ${o.nor} arrival ${o.arrival} hold ${o.hold} slack ${o.slack}`); });
