// 生成文章 2 的框图、时序图和数据图（SVG）。数字取自 docs/posts/article2_draft.md 及其引用的文件，出处见各图注释。
// 用法：node docs/posts/figs/article2/make_figs.js   输出到同目录 *.svg；PNG 用 export_png.sh 导出（2 倍，1440 px 宽）。
// 版式沿用文章 1：画布宽 720，主体文字 30 左右，辅助文字不小于 24。说明性长句放正文，不放图里。
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
const sgn = (v, d = 2) => (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(d);

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
const P = (d, o = {}) =>
  `<path d="${d}" fill="${o.fill || "none"}" stroke="${o.stroke || C.ink2}" stroke-width="${o.sw || 2}"/>`;
const title = (t, sub) => T(36, 58, t, { size: 36, bold: true }) + (sub ? T(36, 100, sub, { size: 24, fill: C.ink2 }) : "");
const write = (name, s) => { fs.writeFileSync(path.join(OUT, name), s); console.log(name); };
// 寄存器：蓝色窄条，底部带时钟三角
const REG = (x, y, h, w = 24) =>
  R(x, y, w, h, { rx: 3, fill: C.blue }) + P(`M${x} ${y + h - 16} L${x + 9} ${y + h - 8} L${x} ${y + h}`, { stroke: "#ffffff", sw: 2 });

// 图 1：复验流程和六份候选走到哪一步（draft §2、§3：6 份全部过门槛、合同审查、RTL/门级仿真；5 份失败在 STA）
{
  const steps = [
    ["AI 交付：RTL、声明的延迟 L、预测", "", "top"],
    ["① 规则检查：端口、复位、时钟用法", "6 / 6", ""],
    ["② 作者合同审查（只看随机编号）", "6 / 6", ""],
    ["③ RTL 功能仿真", "6 / 6", ""],
    ["④ 综合（冻结的综合配方）", "6 / 6", ""],
    ["⑤ 门级功能仿真", "6 / 6", ""],
    ["⑥ STA，6 个角", "1 / 6", "fail"],
    ["⑦ 分析有效性检查", "1 / 6", ""],
    ["⑧ 和基线对照：完整时序矩阵", "1 / 6", "top"],
  ];
  let b = title("每份候选要过的关", "右边是六份候选里通过这一关的份数");
  let y = 130;
  steps.forEach(([t, n, kind], i) => {
    const h = 74;
    const fill = kind === "fail" ? C.orangeSoft : kind === "top" ? C.blueSoft : C.graySoft;
    b += R(36, y, 648, h, { fill, stroke: kind === "fail" ? C.orange : "none" });
    b += T(60, y + 47, t, { size: 28, bold: kind !== "" });
    if (n) b += T(660, y + 47, n, { size: 30, bold: true, anchor: "end", fill: kind === "fail" ? C.orange : C.ink2 });
    if (i < steps.length - 1) b += L(360, y + h + 2, 360, y + h + 22, { arrow: true });
    y += h + 26;
  });
  b += T(36, y + 14, "5 份卡在 ⑥：OpenSTA 读不进综合网表", { size: 26, fill: C.orange, bold: true });
  y += 44;
  b += R(36, y, 648, 112, { fill: "none", stroke: C.blue, dash: "8 6" });
  b += T(60, y + 44, "预测和失败条件：6 份都判", { size: 28, bold: true, fill: C.blue });
  b += T(60, y + 86, "按已有字段判；缺时序结果的记“无结果”或“未判定”", { size: 22, fill: C.ink2 });
  write("fig1_flow.svg", svg(y + 136, b));
}

// 图 2：基线框图和最差路径的时间账（draft §1；时间账数字同文章 1 图 3：5.582、31.5439、27.3541，ss_n40C_1v60）
{
  let b = title("基线：所有运算挤在一拍里", "RTL 功能框图，不是网表结构；L = 1");
  // 数据通路
  b += T(36, 178, "in_a", { size: 26, mono: true });
  b += T(36, 210, "64 位", { size: 22, fill: C.ink2 });
  b += T(36, 258, "in_b", { size: 26, mono: true });
  b += T(36, 290, "64 位", { size: 22, fill: C.ink2 });
  b += L(110, 186, 160, 186, { arrow: true });
  b += L(110, 266, 160, 266, { arrow: true });
  b += R(164, 136, 380, 180, { fill: C.graySoft });
  b += T(354, 182, "4 个 16×16 有符号乘法", { size: 26, anchor: "middle" });
  b += T(354, 232, "4 个乘积相加（34 位）", { size: 26, anchor: "middle" });
  b += T(354, 282, "饱和到 32 位", { size: 26, anchor: "middle" });
  b += L(546, 226, 572, 226, { arrow: true });
  b += REG(576, 136, 180);
  b += L(602, 226, 626, 226, { arrow: true });
  b += T(632, 222, "out_", { size: 24, mono: true });
  b += T(632, 248, "data", { size: 24, mono: true });
  b += T(588, 346, "输出寄存器", { size: 22, fill: C.blue, anchor: "middle" });
  // valid
  b += T(36, 400, "in_valid", { size: 24, mono: true });
  b += L(160, 392, 572, 392, { arrow: true });
  b += REG(576, 372, 44);
  b += L(602, 392, 626, 392, { arrow: true });
  b += T(632, 386, "out_", { size: 24, mono: true });
  b += T(632, 410, "valid", { size: 24, mono: true });
  // 时间账
  const x0 = 36, k = 20, X = t => x0 + t * k;
  const y = 580, h = 70;
  b += T(36, 470, "最差路径的时间账（ns）", { size: 28, bold: true });
  b += T(36, 504, "ss，1.60 V，−40 °C；理想时钟、综合后、只计引脚电容", { size: 22, fill: C.ink2 });
  b += `<rect x="${X(0)}" y="${y}" width="${X(5.582) - X(0) - 2}" height="${h}" rx="4" fill="${C.muted}"/>`;
  b += `<rect x="${X(5.582)}" y="${y}" width="${X(31.5439) - X(5.582)}" height="${h}" rx="4" fill="${C.blue}"/>`;
  b += T(X(2.79), y + 44, "外部 5.58", { size: 22, anchor: "middle", fill: "#ffffff" });
  b += T(X(16.5), y + 44, "端口驱动 + 37 个组合单元", { size: 24, anchor: "middle", fill: "#ffffff" });
  b += L(X(27.3541), y - 20, X(27.3541), y + h + 6, { stroke: C.orange, sw: 3 });
  b += T(X(27.3541) - 8, y - 26, "最晚应到 27.35", { size: 22, fill: C.orange, anchor: "end", bold: true });
  const ay = y + h + 14;
  b += L(X(0), ay, X(32), ay, { stroke: C.line });
  for (let t = 0; t <= 32; t += 8) {
    b += L(X(t), ay, X(t), ay + 8, { stroke: C.line });
    b += T(t === 32 ? X(t) + 8 : X(t), ay + 34, t === 32 ? "32 ns" : `${t}`, { size: 22, anchor: t === 32 ? "end" : "middle", fill: C.muted });
  }
  const ly = ay + 70;
  b += `<rect x="${X(27.3541)}" y="${ly}" width="${X(31.5439) - X(27.3541)}" height="14" rx="4" fill="${C.orange}"/>`;
  b += T(X(27.3541) - 14, ly + 14, "实际到达 31.54，晚到 4.19", { size: 26, anchor: "end", fill: C.orange, bold: true });
  b += T(X(27.3541) - 14, ly + 54, "setup slack = −4.19", { size: 26, anchor: "end", fill: C.orange, bold: true });
  write("fig2_baseline.svg", svg(ly + 84, b));
}

// 图 3：三家两轮的流水切法（draft §3"三种方案"；RTL：rtl/dot4sat_cand_*.v）
{
  // 元素：R = 寄存器；字符串 = 组合逻辑框
  const rows = [
    ["基线", "L = 1", ["乘法 + 求和 + 饱和", "R"], true],
    ["Claude 第 1、2 轮", "L = 3", ["R", "乘法", "R", "求和 + 饱和", "R"]],
    ["Kimi 第 1 轮", "L = 2", ["R", "乘法 + 求和 + 饱和", "R"]],
    ["Kimi 第 2 轮", "L = 2", ["R", "乘法 + 求和 + 饱和*", "R"]],
    ["DeepSeek 第 1 轮", "L = 2", ["乘法", "R", "求和 + 饱和", "R"]],
    ["DeepSeek 第 2 轮", "L = 2", ["R", "乘法 + 求和 + 饱和", "R"]],
  ];
  let b = title("三家怎么切流水", "蓝条是寄存器，灰框是组合逻辑；左边接输入，右边是输出");
  let y = 130;
  const rw = 24, gap = 16, x0 = 36, x1 = 684;
  rows.forEach(([name, lat, els, base]) => {
    b += T(36, y + 30, name, { size: 28, bold: true, fill: base ? C.ink2 : C.ink });
    b += T(684, y + 30, lat, { size: 28, bold: true, anchor: "end", fill: base ? C.ink2 : C.blue });
    const nReg = els.filter(e => e === "R").length, nBox = els.length - nReg;
    const boxW = (x1 - x0 - nReg * rw - (els.length - 1) * gap) / nBox;
    let x = x0;
    const by = y + 50, bh = 66;
    els.forEach((e, i) => {
      if (e === "R") { b += REG(x, by, bh, rw); x += rw; }
      else {
        b += R(x, by, boxW, bh, { fill: C.graySoft });
        b += T(x + boxW / 2, by + 43, e, { size: 26, anchor: "middle" });
        x += boxW;
      }
      if (i < els.length - 1) { b += L(x + 1, by + bh / 2, x + gap - 1, by + bh / 2, { stroke: C.line }); x += gap; }
    });
    y += 150;
  });
  b += T(36, y + 6, "* 第 2 轮改成按和的高三位判断是否饱和", { size: 24, fill: C.ink2 });
  write("fig3_cuts.svg", svg(y + 34, b));
}

// 图 4：延迟 L 的定义（合同 spec.md §2.1–2.2：I_n 在 R_n 采样，结果在 R_(n+L−1) 之后形成，TB 在 F_(n+L−1) 读到，记为 O_(n+L)；
// TB 在下降沿先读输出、再驱动下一拍输入）
{
  const x0 = 200, cw = 68, N = 7, X = c => x0 + c * cw;
  let b = title("延迟 L 是什么", "第 n 笔输入在上升沿 Rn 采样；经过 L 级寄存器后出结果");
  const rows = [["clk", "clk"], ["in_valid", "valid"], ["输入", "bus", "D"], ["L = 1 输出", "out", 1], ["L = 2 输出", "out", 2], ["L = 3 输出", "out", 3]];
  const top = 150, rh = 76, hh = 38, s = 7;
  const hex = (xa, xb, yt, yb, txt, soft, line) => {
    const ym = (yt + yb) / 2;
    return `<path d="M${xa} ${ym} L${xa + s} ${yt} L${xb - s} ${yt} L${xb} ${ym} L${xb - s} ${yb} L${xa + s} ${yb} z" fill="${soft}" stroke="${line}" stroke-width="2"/>` +
      T((xa + xb) / 2, ym + 8, txt, { size: 22, anchor: "middle", bold: true, fill: line === C.blue ? C.blue : C.ink });
  };
  // 上升沿 R0..R5 在 X(1)..X(6)
  for (let c = 1; c < N; c++) {
    b += L(X(c), 136, X(c), top + rows.length * rh - 10, { stroke: C.grid, sw: 1.5, dash: "4 6" });
    b += T(X(c), 140, `R${c - 1}`, { size: 22, anchor: "middle", fill: C.muted });
  }
  let y = top;
  rows.forEach(([name, kind, arg]) => {
    const yt = y + 8, yb = y + 8 + hh, ym = (yt + yb) / 2;
    b += T(36, ym + 9, name, { size: 24, mono: name === "clk" || name === "in_valid" });
    if (kind === "clk") {
      let d = `M${X(0)} ${yb}`;
      for (let c = 0; c < N; c++) d += ` L${X(c)} ${yt} L${X(c) + cw / 2} ${yt} L${X(c) + cw / 2} ${yb} L${X(c + 1)} ${yb}`;
      b += P(d, { stroke: C.ink, sw: 2.5 });
    } else if (kind === "valid") {
      const a = X(1) - cw / 2, e = X(4) - cw / 2;
      b += P(`M${X(0)} ${yb} L${a} ${yb} L${a} ${yt} L${e} ${yt} L${e} ${yb} L${X(N)} ${yb}`, { stroke: C.ink, sw: 2.5 });
    } else if (kind === "bus") {
      // TB 在下降沿驱动：D_k 从 F_(k−1) 保持到 F_k，覆盖采样沿 R_k
      const a = X(1) - cw / 2;
      b += P(`M${X(0)} ${ym} L${a} ${ym} M${X(4) - cw / 2} ${ym} L${X(N)} ${ym}`, { stroke: C.muted, sw: 2 });
      for (let k = 0; k < 3; k++) b += hex(X(k + 1) - cw / 2, X(k + 2) - cw / 2, yt, yb, `D${k}`, C.graySoft, C.ink2);
    } else {
      // Q_k 在 R_(k+L−1) 之后变化，TB 在 F_(k+L−1) 读到
      const L0 = arg, d = 6, a = X(L0) + d, e = X(L0 + 3) + d;
      b += P(`M${X(0)} ${ym} L${a} ${ym} M${e} ${ym} L${X(N)} ${ym}`, { stroke: C.muted, sw: 2 });
      for (let k = 0; k < 3; k++) {
        b += hex(X(k + L0) + d, X(k + L0 + 1) + d, yt, yb, `Q${k}`, C.blueSoft, C.blue);
        b += `<circle cx="${X(k + L0) + cw / 2}" cy="${yb + 9}" r="5" fill="${C.orange}"/>`;
      }
    }
    y += rh;
  });
  b += T(36, y + 16, "Qn 是 Dn 的结果，有效时 out_valid 同时为 1", { size: 22, fill: C.ink2 });
  b += T(36, y + 50, "橙点：测试台在下降沿读输出", { size: 22, fill: C.orange });
  b += T(36, y + 84, "流水填满后，每拍仍出一笔", { size: 22, fill: C.ink2 });
  write("fig4_latency.svg", svg(y + 110, b));
}

// 图 5：signed 声明怎么让 STA 失败（draft §4；声明个数见 revise/notes/netlist_diagnosis_results.md §3）
{
  let b = title("五份候选卡在哪", "本次冻结流程中：仿真器读得进，OpenSTA 读不进");
  const box = (y, h, head, code, o = {}) =>
    R(36, y, 648, h, { fill: o.fill || C.graySoft, stroke: o.stroke || "none" }) +
    T(60, y + 40, head, { size: 26, bold: true, fill: o.headFill || C.ink }) +
    T(60, y + 84, code, { size: 24, mono: true });
  b += box(130, 110, "候选 RTL 里的写法（合同允许）", "wire signed [15:0] a0 = a_q[15:0];");
  b += L(360, 244, 360, 290, { arrow: true });
  b += T(380, 274, "冻结的综合配方写出网表", { size: 22, fill: C.ink2 });
  b += box(296, 110, "综合网表里保留了 signed", "wire signed [15:0] a0;");
  b += L(200, 410, 200, 452, { arrow: true });
  b += L(520, 410, 520, 452, { arrow: true });
  b += R(36, 458, 312, 130, { fill: C.blueSoft, stroke: C.blue });
  b += T(192, 500, "门级仿真（iverilog）", { size: 24, anchor: "middle", bold: true });
  b += T(192, 540, "读得进", { size: 26, anchor: "middle", fill: C.blue, bold: true });
  b += T(192, 574, "功能回归通过", { size: 22, anchor: "middle", fill: C.ink2 });
  b += R(372, 458, 312, 130, { fill: C.orangeSoft, stroke: C.orange });
  b += T(528, 500, "STA（OpenSTA）", { size: 24, anchor: "middle", bold: true });
  b += T(528, 540, "syntax error", { size: 26, anchor: "middle", fill: C.orange, bold: true, mono: true });
  b += T(528, 574, "没有任何时序数字", { size: 22, anchor: "middle", fill: C.ink2 });
  // 个数表
  const rows = [["", "第 1 轮", "第 2 轮"], ["Claude", "16", "0"], ["Kimi", "8", "8"], ["DeepSeek", "8", "8"]];
  b += T(36, 646, "网表里 wire signed 声明的个数（基线为 0）", { size: 24, bold: true });
  let y = 672;
  rows.forEach((r, i) => {
    if (i > 0) b += L(36, y, 684, y, { stroke: C.grid, sw: 1.5 });
    b += T(60, y + 36, r[0], { size: 24, bold: i === 0 });
    b += T(400, y + 36, r[1], { size: 24, anchor: "middle", bold: i === 0 });
    const ok = r[0] === "Claude";
    b += T(580, y + 36, r[2], { size: 24, anchor: "middle", bold: i === 0 || ok, fill: ok ? C.blue : C.ink });
    y += 52;
  });
  b += T(36, y + 30, "第 2 轮只有 Claude 的网表里没有 signed 声明，STA 正常完成", { size: 22, fill: C.blue });
  write("fig5_signed.svg", svg(y + 56, b));
}

// 图 6：插流水以后每一拍的时间怎么分（只做规程 §12.4 的结构性说明，不按比例，不说明收益各占多少）
{
  let b = title("插流水以后，路径预算怎么变", "示意图，不按比例；输入输出约束都没变");
  const x0 = 170, wT = 510, wIn = wT * 0.2;
  const row = (y, label, segs) => {
    let s = T(36, y + 44, label, { size: 26, bold: true });
    let x = x0;
    segs.forEach(([w, text, fill, col]) => {
      s += R(x, y, w - 4, 66, { rx: 4, fill });
      s += T(x + (w - 4) / 2, y + 42, text, { size: w < 120 ? 19 : 22, anchor: "middle", fill: col || "#ffffff" });
      x += w;
    });
    return s;
  };
  b += T(36, 160, "基线（L = 1）", { size: 28, bold: true, fill: C.ink2 });
  b += row(180, "唯一一拍", [[wIn, "外部 0.2T", C.muted], [wT - wIn, "输入 → 输出寄存器：全部运算", C.orange]]);
  b += T(36, 330, "Claude 第 2 轮（L = 3）", { size: 28, bold: true, fill: C.blue });
  b += row(350, "第 1 拍", [[wIn, "外部 0.2T", C.muted], [wT - wIn, "输入 → 输入寄存器", C.blue]]);
  b += row(436, "第 2 拍", [[wT, "寄存器 → 寄存器：用整个周期", C.blue]]);
  b += row(522, "第 3 拍", [[wT, "寄存器 → 输出寄存器：用整个周期", C.blue]]);
  b += L(x0, 614, x0 + wT - 4, 614, { stroke: C.line });
  b += L(x0, 606, x0, 622, { stroke: C.line });
  b += L(x0 + wT - 4, 606, x0 + wT - 4, 622, { stroke: C.line });
  b += T(x0 + wT / 2, 650, "一个时钟周期 T = 27.91 ns", { size: 22, anchor: "middle", fill: C.muted });
  write("fig6_budget.svg", svg(680, b));
}

// 图 7：ss_n40C_1v60 各类路径的最差 setup slack（revise/compare/r2_cand_u2pe.md；reg2reg 基线没有这类路径）
{
  const rows = [
    ["全局最差", -4.189726, 6.104896],
    ["输入 → 寄存器（in2reg）", -4.189726, 21.704105],
    ["寄存器 → 寄存器（reg2reg）", null, 6.104897],
    ["寄存器 → 输出（reg2out）", 21.692432, 21.692432],
  ];
  const k = 20, x0 = 36 + 5 * k, X = v => x0 + v * k;
  let b = title("各类路径的最差 setup slack", "ss，1.60 V，−40 °C；理想时钟、综合后、只计引脚电容；ns");
  b += `<rect x="${X(-5) }" y="128" width="20" height="20" fill="${C.muted}"/>` + T(X(-5) + 28, 146, "基线", { size: 22, fill: C.ink2 });
  b += `<rect x="${X(-5) + 110}" y="128" width="20" height="20" fill="${C.blue}"/>` + T(X(-5) + 138, 146, "Claude 第 2 轮", { size: 22, fill: C.ink2 });
  let y = 178;
  rows.forEach(([name, base, cand]) => {
    b += T(36, y + 26, name, { size: 26, bold: true });
    [[base, C.muted], [cand, C.blue]].forEach(([v, col], j) => {
      const by = y + 42 + j * 40, h = 30;
      if (v === null) { b += T(X(0) + 10, by + 24, "基线没有这类路径", { size: 22, fill: C.muted }); return; }
      const xa = Math.min(X(0), X(v)), w = Math.abs(X(v) - X(0));
      b += `<rect x="${xa}" y="${by}" width="${w}" height="${h}" rx="3" fill="${col}"/>`;
      b += T(v < 0 ? X(0) + 10 : xa + w + 10, by + 24, sgn(v), { size: 24, bold: true, fill: v < 0 ? C.orange : C.ink });
    });
    b += L(X(0), y + 36, X(0), y + 118, { stroke: C.ink2, sw: 2 });
    y += 140;
  });
  b += T(X(0), y + 18, "0", { size: 22, anchor: "middle", fill: C.muted });
  write("fig7_categories.svg", svg(y + 40, b));
}

// 图 8 / 图 9：六个角的全局最差 setup 和最小 hold slack（revise/compare/r2_cand_u2pe.md 的 global 行）
const CORNERS = ["ss，1.60 V，−40 °C", "ss，1.60 V，100 °C", "tt，1.80 V，25 °C", "tt，1.80 V，100 °C", "ff，1.95 V，−40 °C", "ff，1.95 V，100 °C"];
function cornerFig(file, head, sub, sub2, base, cand, lo, hi, d, unit) {
  const k = (684 - 36 - 100) / (hi - lo), x0 = 36 - lo * k, X = v => x0 + v * k;
  let b = title(head, sub) + T(36, 134, sub2, { size: 24, fill: C.ink2 });
  b += `<rect x="36" y="160" width="20" height="20" fill="${C.muted}"/>` + T(64, 178, "基线", { size: 22, fill: C.ink2 });
  b += `<rect x="146" y="160" width="20" height="20" fill="${C.blue}"/>` + T(174, 178, "Claude 第 2 轮", { size: 22, fill: C.ink2 });
  let y = 208;
  CORNERS.forEach((name, i) => {
    b += T(36, y + 24, name, { size: 24, bold: true });
    [[base[i], C.muted], [cand[i], C.blue]].forEach(([v, col], j) => {
      const by = y + 36 + j * 34, h = 26;
      const xa = Math.min(X(0), X(v)), w = Math.abs(X(v) - X(0));
      b += `<rect x="${xa}" y="${by}" width="${w}" height="${h}" rx="3" fill="${col}"/>`;
      b += T(v < 0 ? X(0) + 10 : xa + w + 8, by + 21, sgn(v, d), { size: 22, bold: true, fill: v < 0 ? C.orange : C.ink });
    });
    b += L(X(0), y + 30, X(0), y + 102, { stroke: C.ink2, sw: 2 });
    y += 118;
  });
  b += T(X(0), y + 12, "0", { size: 22, anchor: "middle", fill: C.muted });
  b += T(684, y + 12, unit, { size: 22, anchor: "end", fill: C.muted });
  write(file, svg(y + 36, b));
}
cornerFig("fig8_setup.svg", "六个角的最差 setup slack", "理想时钟、综合后、只计引脚电容", "单位 ns",
  [-4.189726, -0.687278, 11.185458, 11.317221, 15.871505, 15.894229],
  [6.104896, 8.810737, 18.599773, 18.778149, 22.154275, 22.143077], -5, 23, 2, "ns");
cornerFig("fig9_hold.svg", "六个角的最小 hold slack", "理想时钟、综合后模型下的最小 hold slack", "只计引脚电容；单位 ns",
  [0.185004, 0.185679, 0.093054, 0.089830, 0.063473, 0.059113],
  [0.079827, 0.089585, 0.040983, 0.043611, 0.023094, 0.025111], 0, 0.22, 3, "ns");

// 图 10：怎么判"支持"——Claude 第 2 轮 P1（revise/predictions/r2_judgments.md：范围 [0, 21.7]，点估计 9，实测 6.104896）
{
  const k = 26, x0 = 70, X = v => x0 + v * k;
  let b = title("预测怎么判", "Claude 第 2 轮第 1 条：六个角里最差的 setup slack");
  const y = 190;
  b += R(X(0), y, X(21.7) - X(0), 50, { rx: 6, fill: C.blueSoft, stroke: C.blue });
  b += T(X(0), y - 14, "它写的范围 0 ~ 21.7", { size: 24, fill: C.blue, bold: true });
  b += `<circle cx="${X(9)}" cy="${y + 25}" r="11" fill="#ffffff" stroke="${C.ink2}" stroke-width="3"/>`;
  b += T(X(9), y + 90, "点估计 9", { size: 24, anchor: "middle", fill: C.ink2 });
  b += `<path d="M${X(6.104896)} ${y + 8} L${X(6.104896) + 14} ${y + 25} L${X(6.104896)} ${y + 42} L${X(6.104896) - 14} ${y + 25} z" fill="${C.orange}"/>`;
  b += T(X(6.104896), y + 126, "实测 +6.10", { size: 24, anchor: "middle", fill: C.orange, bold: true });
  const ay = y + 150;
  b += L(X(0), ay, X(24), ay, { stroke: C.line });
  for (let t = 0; t <= 24; t += 4) {
    b += L(X(t), ay, X(t), ay + 8, { stroke: C.line });
    b += T(X(t), ay + 34, `${t}`, { size: 22, anchor: "middle", fill: C.muted });
  }
  b += T(684, ay - 14, "ns", { size: 22, anchor: "end", fill: C.muted });
  const ty = ay + 90;
  b += T(36, ty, "方向：变好了 ✓", { size: 26 });
  b += T(36, ty + 44, "范围：落在 0 ~ 21.7 里 ✓", { size: 26 });
  b += T(36, ty + 88, "点估计 9：只展示，不参与判定", { size: 26, fill: C.ink2 });
  b += T(36, ty + 140, "→ 判定：支持", { size: 30, bold: true, fill: C.blue });
  b += T(36, ty + 188, "实测：理想时钟、综合后、只计引脚电容；", { size: 22, fill: C.ink2 });
  b += T(36, ty + 220, "最差角 ss_n40C_1v60（ss，1.60 V，−40 °C）", { size: 22, fill: C.ink2 });
  write("fig10_judge.svg", svg(ty + 248, b));
}

// 图 11：面积预测改对和改错（draft §7；revise/predictions/r1_judgments.md、r2_judgments.md）
{
  const rows = [
    ["Claude 第 1 轮", 4000, 11345.9, 3407.0176, "反对"],
    ["Claude 第 2 轮", 2500, 5500, 3283.1488, "支持"],
    ["Kimi 第 1 轮", null, null, 2599.9936, "支持"],
    ["Kimi 第 2 轮", 2000, 2600, 2786.4224, "反对"],
  ];
  const k = 0.05, x0 = 60, X = v => x0 + v * k;
  let b = title("面积增量的预测：改对和改错", "单位 µm²；蓝色块是模型给的范围，菱形是实测");
  let y = 150;
  rows.forEach(([name, lo, hi, act, verdict]) => {
    const ok = verdict === "支持";
    b += T(36, y + 28, name, { size: 26, bold: true });
    b += T(684, y + 28, verdict, { size: 26, bold: true, anchor: "end", fill: ok ? C.blue : C.orange });
    const by = y + 46;
    if (lo === null) {
      b += `<rect x="${X(0)}" y="${by}" width="${X(12000) - X(0)}" height="34" rx="4" fill="${C.graySoft}"/>`;
      b += T(X(12000) - 12, by + 25, "只写了“面积会增加”，没给范围", { size: 22, anchor: "end", fill: C.ink2 });
    } else {
      b += R(X(lo), by, X(hi) - X(lo), 34, { rx: 4, fill: C.blueSoft, stroke: C.blue });
      b += T(name.length > 10 ? 250 : 210, y + 28, `范围 ${lo}~${hi}`, { size: 22, fill: C.blue });
    }
    {
      const xa = X(act);
      b += `<path d="M${xa} ${by - 4} L${xa + 12} ${by + 17} L${xa} ${by + 38} L${xa - 12} ${by + 17} z" fill="${C.orange}"/>`;
      b += T(xa, by + 66, "实测 " + act.toFixed(1), { size: 22, anchor: "middle", fill: C.orange, bold: true });
    }
    y += 132;
  });
  const ay = y + 4;
  b += L(X(0), ay, X(12000), ay, { stroke: C.line });
  for (let t = 0; t <= 12000; t += 4000) {
    b += L(X(t), ay, X(t), ay + 8, { stroke: C.line });
    b += T(X(t), ay + 34, `${t}`, { size: 22, anchor: "middle", fill: C.muted });
  }
  write("fig11_area.svg", svg(ay + 60, b));
}

// 图 12：网表兼容性诊断（revise/notes/netlist_diagnosis_results.md §4；不是正式结果）
{
  const rows = [
    ["基线", -4.189726, "base"],
    ["Claude 第 1 轮", 8.708432], ["Claude 第 2 轮", 6.104896, "formal"],
    ["Kimi 第 1 轮", 1.557034], ["Kimi 第 2 轮", 1.542086],
    ["DeepSeek 第 1 轮", 5.004687], ["DeepSeek 第 2 轮", 1.557034],
  ];
  const k = 30, x0 = 36 + 5 * k + 160, X = v => x0 + v * k;
  let b = title("事后诊断：删掉 signed 以后再测", "不是正式结果；六个角最差 setup slack，ns");
  b += T(36, 132, "理想时钟、综合后、只计引脚电容；最差角都是 ss，1.60 V，−40 °C", { size: 22, fill: C.ink2 });
  let y = 160;
  rows.forEach(([name, v, kind]) => {
    b += T(36, y + 30, name, { size: 24, bold: kind === "base" });
    const col = kind === "base" ? C.muted : C.graySoft;
    const xa = Math.min(X(0), X(v)), w = Math.abs(X(v) - X(0));
    b += `<rect x="${xa}" y="${y + 8}" width="${w}" height="32" rx="3" fill="${kind === "base" ? C.orange : kind === "formal" ? C.blue : C.ink2}" fill-opacity="${kind ? 1 : 0.55}"/>`;
    b += T(v < 0 ? X(0) + 10 : xa + w + 8, y + 32, sgn(v), { size: 22, bold: true, fill: v < 0 ? C.orange : C.ink });
    y += 64;
  });
  b += L(X(0), 160, X(0), y, { stroke: C.ink2, sw: 2 });
  b += T(X(0), y + 26, "0", { size: 22, anchor: "middle", fill: C.muted });
  b += T(36, y + 70, "蓝色一份本来就没有 signed，和正式结果相同", { size: 22, fill: C.blue });
  write("fig12_diag.svg", svg(y + 96, b));
}

// 图 13：附录 B，最差 setup 路径落在哪一级（诊断运行 tasks/CASE-01/runs/revise-diag-netlist/*/sta/cat_ss_n40C_1v60_{in2reg,reg2reg}_max.rpt；
// 端点名对照各对象 netlist.v 的 .Q 连线；不是正式结果）
{
  const rows = [
    ["DeepSeek 第 1 轮", ["乘法", "R", "求和 + 饱和", "R"], 0, "最慢：输入 → 乘积寄存器", 5.004687],
    ["DeepSeek 第 2 轮", ["R", "乘法 + 求和 + 饱和", "R"], 1, "最慢：三段运算在同一拍", 1.557034],
    ["Claude 第 1 轮", ["R", "乘法", "R", "求和 + 饱和", "R"], 1, "最慢：乘法这一级", 8.708432],
    ["Claude 第 2 轮", ["R", "乘法", "R", "求和 + 饱和", "R"], 3, "最慢：求和饱和这一级", 6.104896],
  ];
  let b = title("最慢的一段落在哪里", "事后诊断，不是正式结果；ss，1.60 V，−40 °C");
  b += T(36, 134, "理想时钟、综合后、只计引脚电容；橙框是最差 setup 路径所在段", { size: 22, fill: C.ink2 });
  b += T(36, 164, "右侧数字：诊断的全局最差 setup slack", { size: 22, fill: C.ink2 });
  let y = 200;
  const rw = 24, gap = 16, x0 = 36, x1 = 684;
  rows.forEach(([name, els, hl, note, v]) => {
    b += T(36, y + 30, name, { size: 28, bold: true });
    const nReg = els.filter(e => e === "R").length, nBox = els.length - nReg;
    const boxW = (x1 - x0 - nReg * rw - (els.length - 1) * gap) / nBox;
    let x = x0;
    const by = y + 48, bh = 62;
    els.forEach((e, i) => {
      if (e === "R") { b += REG(x, by, bh, rw); x += rw; }
      else {
        const on = i === hl;
        b += R(x, by, boxW, bh, { fill: on ? C.orangeSoft : C.graySoft, stroke: on ? C.orange : "none", sw: 3 });
        b += T(x + boxW / 2, by + 41, e, { size: 24, anchor: "middle", bold: on });
        x += boxW;
      }
      if (i < els.length - 1) { b += L(x + 1, by + bh / 2, x + gap - 1, by + bh / 2, { stroke: C.line }); x += gap; }
    });
    b += T(36, by + bh + 38, note, { size: 24, fill: C.ink2 });
    b += T(684, by + bh + 38, sgn(v) + " ns", { size: 26, bold: true, anchor: "end", fill: C.orange });
    y += 186;
  });
  b += T(36, y + 6, "DeepSeek 第 1 轮的第一段还要先扣 5.58 ns 外部输入延迟", { size: 22, fill: C.ink2 });
  write("fig13_stage.svg", svg(y + 34, b));
}
