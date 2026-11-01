// 生成文章 3 的框图、流程图和数据图（SVG）。数字取自 docs/posts/article3_draft.md 及其引用的 tasks/CASE-02 文件，出处见各图注释。
// 用法：node docs/posts/figs/article3/make_figs.js   输出到同目录 *.svg；PNG 用 export_png.sh 导出（2 倍，1440 px 宽）。
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

const box = (x, y, w, h, lines, o = {}) => {
  let s = R(x, y, w, h, { fill: o.fill || C.graySoft, stroke: o.stroke, dash: o.dash });
  const lh = o.lh || 38, y0 = y + h / 2 - ((lines.length - 1) * lh) / 2 + 9;
  lines.forEach((t, i) => {
    const [txt, to] = Array.isArray(t) ? t : [t, {}];
    s += T(x + w / 2, y0 + i * lh, txt, { size: 26, anchor: "middle", ...to });
  });
  return s;
};

// 图 1：实验怎么设的（draft §2.1、§2.2；queries/formal/{correct,missing}/sta_results.tsv 的 ss_n40C_1v60 in2reg max 行）
{
  let b = title("同一张网表，跑两次 STA", "只改约束，网表一个门都没动");
  b += box(160, 130, 400, 70, [["综合后网表（同一张）", { bold: true }]]);
  b += L(300, 202, 200, 250, { arrow: true }) + L(420, 202, 520, 250, { arrow: true });
  b += box(36, 256, 312, 150, [["正确版", { bold: true, fill: C.blue }], "130 个输入", "都有 set_input_delay"], { fill: C.blueSoft });
  b += box(372, 256, 312, 150, [["缺失版", { bold: true, fill: C.orange }], "删掉 in_b[63:0] 的", "min、max，共 128 条"], { fill: C.orangeSoft });
  b += L(192, 408, 192, 446, { arrow: true }) + L(528, 408, 528, 446, { arrow: true });
  b += box(36, 452, 312, 130, ["最差 setup slack", ["−4.189726 ns", { bold: true, size: 30 }], ["起点 in_b[2]", { mono: true, size: 24 }]], { fill: "#ffffff", stroke: C.blue });
  b += box(372, 452, 312, 130, ["最差 setup slack", ["−4.172595 ns", { bold: true, size: 30 }], ["起点 in_a[34]", { mono: true, size: 24 }]], { fill: "#ffffff", stroke: C.orange });
  b += T(360, 636, "缺失版“好了”0.017 ns，起点也换了", { size: 28, bold: true, anchor: "middle", fill: C.orange });
  b += T(360, 676, "输入到寄存器；ss，1.60 V，−40 °C", { size: 22, anchor: "middle", fill: C.ink2 });
  b += T(360, 706, "综合后、理想时钟、不读寄生、只计引脚电容", { size: 22, anchor: "middle", fill: C.ink2 });
  write("fig1_setup.svg", svg(736, b));
}

// 图 2：为什么漏了约束 slack 反而变好（draft §2.3：130 个非时钟输入 = in_a 64 + in_b 64 + in_valid + rst；缺失版只剩 66 个受约束）
{
  let b = title("最差值只在“受约束”的路径里挑", "缺失版：in_b 没有时钟参考，被分到另一组");
  const ports = [["in_a[63:0]", "64 位", true], ["in_valid", "1 位", true], ["rst", "1 位", true], ["in_b[63:0]", "64 位", false]];
  let y = 150;
  ports.forEach(([n, w, ok]) => {
    const yy = ok ? y : y + 60;
    b += R(36, yy, 230, 64, { fill: ok ? C.blueSoft : C.orangeSoft });
    b += T(52, yy + 41, n, { size: 24, mono: true }) + T(254, yy + 41, w, { size: 22, anchor: "end", fill: C.ink2 });
    b += ok ? L(268, yy + 32, 398, 200 + (yy - 150) / 2, { arrow: true, stroke: C.blue }) : L(268, yy + 32, 398, yy + 32, { arrow: true, stroke: C.orange, dash: "8 6" });
    y += 80;
  });
  b += box(404, 160, 280, 180, [["受约束的检查", { bold: true, fill: C.blue }], "66 个输入", "参加最差 slack 统计"], { fill: C.blueSoft, stroke: C.blue });
  b += box(404, 410, 280, 140, [["未约束", { bold: true, fill: C.orange }], "路径还在", "不进最差 slack"], { fill: "#ffffff", stroke: C.orange, dash: "8 6" });
  b += T(36, 630, "正确版：130 个输入都在上面那一组，", { size: 26 });
  b += T(36, 670, "最差的那条恰好从 in_b 出发。", { size: 26 });
  b += T(36, 726, "缺失版：in_b 整组被挪走，", { size: 26 });
  b += T(36, 766, "最差值只能从剩下的 66 个里挑。", { size: 26, bold: true, fill: C.orange });
  b += T(36, 812, "示意图；这是本例 OpenSTA 设置下的行为", { size: 22, fill: C.ink2 });
  write("fig2_mechanism.svg", svg(842, b));
}

// 图 3：数轴（ss_n40C_1v60；−4.189726 in_b[2]、−4.172595 in_a[34] 见 sta_results.tsv；in_b[35] −4.1808 见 round2/B_results.md 的 R2 输出，draft §2.3）
{
  const lo = -4.196, hi = -4.166, x0 = 60, x1 = 660, X = v => x0 + (v - lo) / (hi - lo) * (x1 - x0);
  let b = title("删掉的不只是最差的那一条", "ss，1.60 V，−40 °C；输入到寄存器的 setup slack");
  const ay = 330;
  b += L(x0, ay, x1, ay, { stroke: C.ink2, sw: 3 });
  [-4.19, -4.18, -4.17].forEach(t => {
    b += L(X(t), ay, X(t), ay + 10, { stroke: C.ink2 });
    b += T(X(t), ay + 40, t.toFixed(2).replace("-", "−"), { size: 22, anchor: "middle", fill: C.muted });
  });
  b += T(x1, ay + 40, "ns", { size: 22, anchor: "end", fill: C.muted });
  b += T(x0, ay + 76, "← 更差", { size: 22, fill: C.muted }) + T(x1, ay + 76, "更好 →", { size: 22, anchor: "end", fill: C.muted });
  const pt = (v, col, cross) => `<circle cx="${X(v)}" cy="${ay}" r="12" fill="${cross ? "#ffffff" : col}" stroke="${col}" stroke-width="4"/>` +
    (cross ? L(X(v) - 8, ay - 8, X(v) + 8, ay + 8, { stroke: col, sw: 3 }) + L(X(v) - 8, ay + 8, X(v) + 8, ay - 8, { stroke: col, sw: 3 }) : "");
  b += pt(-4.189726, C.blue, true) + pt(-4.1808, C.blue, true) + pt(-4.172595, C.orange, false);
  b += L(X(-4.189726), ay - 16, X(-4.189726), 204, { stroke: C.line });
  b += T(X(-4.189726) - 14, 166, "in_b[2]  −4.1897", { size: 22, mono: true });
  b += T(X(-4.189726) - 14, 194, "正确版的最差", { size: 22, fill: C.blue });
  b += L(X(-4.1808), ay - 16, X(-4.1808), 274, { stroke: C.line });
  b += T(X(-4.1808) - 14, 238, "in_b[35]  −4.1808", { size: 22, mono: true });
  b += T(X(-4.1808) - 14, 266, "正确版里也有", { size: 22, fill: C.blue });
  b += L(X(-4.172595), ay + 16, X(-4.172595), 448, { stroke: C.line });
  b += T(X(-4.172595) + 14, 474, "in_a[34]  −4.1726", { size: 22, mono: true, anchor: "end" });
  b += T(X(-4.172595) + 14, 502, "缺失版的最差", { size: 22, fill: C.orange, anchor: "end", bold: true });
  b += T(36, 572, "打叉：缺失版里这些 in_b 路径都不算了。", { size: 24, fill: C.ink2 });
  b += T(36, 608, "所以缺失版的最差，不是正确版的“第二差”。", { size: 24, fill: C.ink2 });
  write("fig3_numberline.svg", svg(638, b));
}

// 图 4：六个角的变化（sta_results.tsv in2reg max/min 行；差值 = 缺失版 − 正确版）
{
  const rows = [
    ["ss，1.60 V，−40 °C", -4.189726, "in_b[2]", -4.172595, "in_a[34]"],
    ["ss，1.60 V，100 °C", -0.687278, "in_b[35]", -0.679952, "in_a[34]"],
    ["tt，1.80 V，25 °C", 11.185458, "in_b[35]", 11.191043, "in_a[34]"],
    ["tt，1.80 V，100 °C", 11.317222, "in_b[35]", 11.321179, "in_a[34]"],
    ["ff，1.95 V，−40 °C", 15.871506, "in_b[2]", 15.881205, "in_a[3]"],
    ["ff，1.95 V，100 °C", 15.894229, "in_b[2]", 15.902845, "in_a[3]"],
  ];
  let b = title("六个角：都“好了”一点，起点都换了", "缺失版减正确版，输入到寄存器的最差 setup slack");
  const k = 210 / 0.018, xb = 380;
  let y = 150;
  rows.forEach(([name, c, cs, m, ms]) => {
    const d = m - c;
    b += T(36, y + 28, name, { size: 24, bold: true });
    b += `<rect x="${xb}" y="${y + 6}" width="${d * k}" height="30" rx="3" fill="${C.orange}"/>`;
    b += T(xb + d * k + 10, y + 30, "+" + d.toFixed(4), { size: 22, bold: true, fill: C.orange });
    b += T(36, y + 64, `起点 ${cs} → ${ms}`, { size: 22, mono: true, fill: C.ink2 });
    y += 96;
  });
  b += L(xb, 146, xb, y - 46, { stroke: C.ink2 });
  b += T(684, y - 10, "单位 ns", { size: 22, anchor: "end", fill: C.muted });
  b += R(36, y + 10, 648, 74, { fill: C.graySoft });
  b += T(56, y + 56, "最小 hold slack：六个角两版完全相同（起点 rst）", { size: 24 });
  b += T(36, y + 122, "综合后、理想时钟、不读寄生、只计引脚电容", { size: 22, fill: C.ink2 });
  write("fig4_corners.svg", svg(y + 150, b));
}

// 图 5：哪些检查看得出来（draft §2.4 表、§2.5；NOTES 必查项 M01–M13 的缺失版结果）
{
  const rows = [
    ["check_setup -verbose", "列出 64 个缺 input delay 的端口名", 2, "给出名单"],
    ["逐端口 min/max 计数", "ss 角：64 个端口受约束的 min、max 都是 0", 2, "看出缺口"],
    ["report_checks -from in_b[*]", "六个角都是 No paths found.", 1],
    ["同上加 -unconstrained", "每个角一条未约束路径", 1],
    ["check_setup -unconstrained_endpoints", "无输出", 0],
    ["全局最小 hold slack", "两版一模一样（摘要里就有）", 0],
  ];
  const mark = [["看不出", C.orange, C.orangeSoft], ["只见现象", C.ink2, C.graySoft], ["直接看出", C.blue, C.blueSoft]];
  let b = title("哪些检查看得出来", "缺失版上的输出");
  let y = 130;
  rows.forEach(([cmd, out, lv, tag]) => {
    b += R(36, y, 648, 96, { fill: mark[lv][2] });
    b += T(56, y + 38, cmd, { size: 22, mono: true, bold: true });
    b += T(56, y + 76, out, { size: 22, fill: C.ink2 });
    b += T(664, y + 76, tag || mark[lv][0], { size: 24, bold: true, anchor: "end", fill: mark[lv][1] });
    y += 112;
  });
  b += T(36, y + 20, "覆盖检查是操作者预先跑的，没放进给模型的材料；", { size: 22, fill: C.ink2 });
  b += T(36, y + 52, "hold 最小值在两次运行的摘要里就有。", { size: 22, fill: C.ink2 });
  b += T(36, y + 84, "要确认缺的是什么，得名单加逐端口状态一起看。", { size: 22, fill: C.ink2 });
  write("fig5_checks.svg", svg(y + 112, b));
}

// 图 6：怎么考（draft §3.1–3.5；契约数字见 rules/contract.json：2000 行、600 秒、12 条、600000 token、评分窗口 120 行）
{
  let b = title("怎么考", "三家拿同一份材料，走同一套公开规则");
  const steps = [
    ["材料：意图、摘要、路径报告、RTL、背景说明", "没有约束脚本，也没说脚本改过", C.graySoft],
    ["第 1 轮：写初判，点名要查什么", "", C.blueSoft],
    ["执行器按公开规则跑查询", "只取答复前 120 行；每条 ≤ 2000 行、≤ 600 秒", C.graySoft],
    ["查询结果交还给模型", "模型只拿到自己点名要的", C.graySoft],
    ["第 2 轮：拿着结果写复判", "", C.blueSoft],
    ["评分：三个问题", "当没当成变快？分没分清要求和实际？话说到哪一步？", C.graySoft],
    ["揭盲：R1 是缺失版，代号对应到模型", "", C.orangeSoft],
  ];
  let y = 130;
  steps.forEach(([t, s, fill], i) => {
    const h = s ? 96 : 66;
    b += R(36, y, 648, h, { fill });
    b += T(56, y + 42, t, { size: 24, bold: true });
    if (s) b += T(56, y + 78, s, { size: 22, fill: C.ink2 });
    if (i < steps.length - 1) b += L(360, y + h + 2, 360, y + h + 22, { arrow: true });
    y += h + 26;
  });
  write("fig6_flow.svg", svg(y + 4, b));
}

// 图 7：第 2 轮证据走到哪一层（draft §3.4 证据层次、§5、§7 两种口径表；NOTES §7）
{
  const lv = ["线索", "现象级", "目标集合完整"];
  const xs = [250, 420, 600];
  let b = title("第 2 轮：证据走到哪一层", "实心：作者揭盲前接受的口径；空心：预登记的字面");
  b += L(xs[0], 186, xs[2], 186, { stroke: C.line, sw: 4 });
  lv.forEach((t, i) => { b += L(xs[i], 176, xs[i], 196, { stroke: C.line, sw: 4 }) + T(xs[i], 160, t, { size: 24, anchor: "middle", bold: true, fill: C.ink2 }); });
  const rows = [
    ["Claude", null, 2, "完成本次诊断", true, "两种口径相同"],
    ["Kimi", 1, 2, "完成本次诊断（作者裁定）", true, "字面：现象级，结论的确定程度高于证据"],
    ["DeepSeek", 0, 1, "完成现象级诊断（作者裁定）", false, "字面：只有线索，判断合理"],
  ];
  let y = 260;
  rows.forEach(([n, lit, acc, verdict, over, note]) => {
    b += T(36, y + 10, n, { size: 28, bold: true });
    b += L(xs[0], y, xs[2], y, { stroke: C.grid, sw: 2 });
    if (lit !== null) {
      b += `<circle cx="${xs[lit]}" cy="${y}" r="13" fill="#ffffff" stroke="${C.ink2}" stroke-width="3"/>`;
      b += L(xs[lit] + 16, y, xs[acc] - 20, y, { stroke: C.ink2, dash: "6 5", arrow: true });
    }
    b += `<circle cx="${xs[acc]}" cy="${y}" r="15" fill="${C.blue}"/>`;
    b += T(36, y + 52, "判定：" + verdict, { size: 22, fill: C.blue });
    if (over) b += T(684, y + 52, "另记：范围超出证据", { size: 22, anchor: "end", fill: C.orange });
    b += T(36, y + 86, note, { size: 22, fill: C.ink2 });
    y += 146;
  });
  b += R(36, y - 20, 648, 70, { fill: C.graySoft });
  b += T(56, y + 24, "第 1 轮：三家都停在“合理假设”", { size: 24 });
  b += T(36, y + 96, "结论只覆盖各自查过的角，不是六个角全部核验", { size: 22, fill: C.ink2 });
  write("fig7_levels.svg", svg(y + 124, b));
}
