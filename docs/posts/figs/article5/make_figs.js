// 生成文章 5（造题）的示意图（SVG）。图里的数字都从 tasks/CASE-02 的文件解析，不手填。
// 用法：node docs/posts/figs/article5/make_figs.js   输出到同目录 *.svg；PNG 用 export_png.sh 导出（2 倍，1440 px 宽）。
// 版式沿用文章 3、4：画布宽 720，主体文字 30 左右，辅助文字不小于 22。说明性长句放正文，不放图里。
const fs = require("fs");
const path = require("path");
const OUT = __dirname;
const CASE = path.join(__dirname, "..", "..", "..", "..", "tasks", "CASE-02");
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

// ---------- 从 CASE-02 的文件取数 ----------
const formal = v => path.join(CASE, "queries", "formal", v);
const lines = f => fs.readFileSync(f, "utf8").split("\n").filter(Boolean);
const expanded = v => lines(path.join(formal(v), "expanded.sdc"));
const nCorrect = expanded("correct").length, nMissing = expanded("missing").length;
const mutation = lines(path.join(CASE, "rules", "mutation_lines.txt"));
const diffHead = lines(path.join(CASE, "prevalidation", "expanded_correct_vs_missing.diff"))[0];
const valid = JSON.parse(fs.readFileSync(path.join(formal("missing"), "valid.json"), "utf8"));
const nAllowed = valid.allowed_changes_seen.length, nWarn = valid.warning_block.count;
if (nCorrect - nMissing !== mutation.length) throw new Error("expanded line counts do not match the mutation list");
const ws = v => {
  const row = lines(path.join(formal(v), "sta_results.tsv")).find(l => l.startsWith("WS\tss_n40C_1v60\tmax"));
  return Number(row.split("\t")[3]);
};
const f6 = v => (v < 0 ? "−" : "") + Math.abs(v).toFixed(6);

// ---------- 图 1：两边手里的东西 ----------
{
  const y0 = 130, h = 400, w = 312;
  const col = (x, head, fill, color, items) => {
    let s = R(x, y0, w, h, { fill });
    s += T(x + w / 2, y0 + 50, head, { size: 28, bold: true, fill: color, anchor: "middle" });
    items.forEach((t, i) => { s += T(x + 28, y0 + 112 + i * 56, t, { size: 25, fill: C.ink }); });
    return s;
  };
  let b = title("两边手里的东西不一样", "同一道题，出题人和模型各看到什么");
  b += col(36, "出题人", C.orangeSoft, C.orange, ["两份 SDC", "展开后的约束", `${mutation.length} 条删除清单`, "覆盖检查的输出", "R1、R2 对应另行封存"]);
  b += col(372, "模型", C.blueSoft, C.blue, ["接口要求", "两份摘要", "两份路径报告", "RTL", "背景说明"]);
  b += T(36, 582, "第 1 轮不提供任何 SDC，也不告知是否有 bug。", { size: 26, fill: C.ink2 });
  write("fig1_two_sides.svg", svg(612, b));
}

// ---------- 图 2：删哪里 ----------
{
  const card = (y, head, sub, tag, fill, color) =>
    R(36, y, 648, 150, { fill }) +
    T(58, y + 50, head, { size: 28, bold: true }) +
    T(58, y + 92, sub[0], { size: 24, fill: C.ink2 }) +
    (sub[1] ? T(58, y + 128, sub[1], { size: 24, fill: C.ink2 }) : "") +
    T(662, y + 50, tag, { size: 26, bold: true, fill: color, anchor: "end" });
  let b = title("删哪里，决定最差 setup 值动不动", "基线六个角的最差起点都在 in_b");
  b += card(130, "删 in_b（64 位）", [`最差 ${f6(ws("correct"))} → ${f6(ws("missing"))} ns`, "起点 in_b[2] → in_a[34]（ss_n40C_1v60）"], "实测", C.blueSoft, C.blue);
  b += card(298, "删 in_a（同样 64 位）", ["最差路径还在", "最差 setup 值预计不变"], "推断", C.graySoft, C.ink2);
  b += card(466, "删 in_valid（1 位）", ["不在最差路径的起点上", "最差 setup 值预计不变"], "推断", C.graySoft, C.ink2);
  b += T(36, 664, "关键不是删得多，是删到最差路径的起点。", { size: 26, fill: C.ink2 });
  write("fig2_where.svg", svg(694, b));
}

// ---------- 图 3：三个版本，比三次 ----------
{
  const node = (x, y, w, s, fill, color) =>
    R(x, y, w, 76, { fill }) + T(x + w / 2, y + 48, s, { size: 28, bold: true, anchor: "middle", fill: color || C.ink });
  const cx = 360;
  let b = title("三个版本，比三次", "比的是展开约束和全部记录文件");
  b += node(230, 130, 260, "F1 归档", C.graySoft);
  b += L(cx, 206, cx, 306, { arrow: false, sw: 3 });
  b += T(cx + 22, 248, "全部一致", { size: 26, bold: true, fill: C.blue });
  b += T(cx + 22, 284, "golden 没变", { size: 24, fill: C.ink2 });
  b += node(230, 306, 260, "正确版", C.blueSoft, C.blue);
  b += L(290, 382, 170, 510, { sw: 3 });
  b += L(430, 382, 550, 510, { sw: 3 });
  b += node(50, 510, 260, "缺失版", C.orangeSoft, C.orange);
  b += node(410, 510, 260, "恢复版", C.blueSoft, C.blue);
  b += T(180, 628, `数值和路径报告 ${nAllowed} 项`, { size: 26, bold: true, fill: C.orange, anchor: "middle" });
  b += T(180, 664, "差别只在预期处", { size: 24, fill: C.ink2, anchor: "middle" });
  b += T(540, 628, "逐字节相同", { size: 26, bold: true, fill: C.blue, anchor: "middle" });
  b += T(540, 664, "同样的输入能重现", { size: 24, fill: C.ink2, anchor: "middle" });
  b += T(36, 730, "恢复版就是用原始 SDC 再跑一遍，不发给模型。", { size: 26, fill: C.ink2 });
  write("fig3_runs.svg", svg(760, b));
}

// ---------- 图 4：看工具实际吃进去的东西 ----------
{
  let b = title("看工具实际吃进去的东西", "源脚本的差异说明不了问题");
  b += R(36, 130, 648, 196, { fill: C.graySoft });
  b += T(58, 176, "源脚本：改动不止一行", { size: 26, bold: true });
  b += T(58, 222, "原：set ins  → 130 位", { size: 24, mono: true });
  b += T(58, 260, "改：set ins_drive → 130 位", { size: 24, mono: true });
  b += T(106, 298, "set ins_delay → 66 位", { size: 24, mono: true });
  b += L(360, 330, 360, 392, { arrow: true, sw: 3 });
  b += T(382, 370, "write_sdc 写出", { size: 24, fill: C.ink2 });
  b += R(36, 398, 648, 196, { fill: C.blueSoft });
  b += T(58, 444, "展开约束：差异只有一块", { size: 26, bold: true, fill: C.blue });
  b += T(58, 490, `正确版 ${nCorrect} 行，缺失版 ${nMissing} 行`, { size: 25 });
  b += T(58, 528, diffHead, { size: 25, mono: true });
  b += T(58, 566, `只删 ${mutation.length} 行，新增 0 行`, { size: 25 });
  const chip = (x, top, bottom, w) =>
    R(x, 618, w, 110, { stroke: C.line }) +
    T(x + w / 2, 660, top, { size: 24, fill: C.ink2, anchor: "middle" }) +
    T(x + w / 2, 702, bottom, { size: 26, bold: true, anchor: "middle" });
  b += chip(36, "输入端", `${mutation.length} 行`, 204);
  b += chip(258, "数值和路径报告", `${nAllowed} 项`, 204);
  b += chip(480, "工具自己说", `${nWarn} 个端口名`, 204);
  write("fig4_expanded.svg", svg(756, b));
}

// ---------- 图 5：线索是难度旋钮 ----------
{
  let b = title("线索是难度旋钮", "本题给了约束线索，只能观察有提示时的表现");
  const y = 176;
  b += L(60, y, 660, y, { sw: 6, stroke: C.line });
  b += T(60, y + 44, "线索多", { size: 25, fill: C.ink2 });
  b += T(660, y + 44, "线索少", { size: 25, fill: C.ink2, anchor: "end" });
  b += `<circle cx="170" cy="${y}" r="15" fill="${C.orange}"/>`;
  b += T(170, y - 28, "这道题", { size: 25, bold: true, fill: C.orange, anchor: "middle" });
  const card = (y0, h, head, items, fill, color) => {
    let s = R(36, y0, 648, h, { fill }) + T(58, y0 + 46, head, { size: 27, bold: true, fill: color });
    items.forEach((t, i) => { s += T(58, y0 + 92 + i * 42, t, { size: 25 }); });
    return s;
  };
  b += card(250, 216, "测得到", ["把 slack 变好当成电路变快了吗", "分清要求加什么、实际加了什么了吗", "结论和证据对得上吗"], C.blueSoft, C.blue);
  b += card(486, 132, "测不到", ["没有提示时，能不能自己想到查约束"], C.orangeSoft, C.orange);
  write("fig5_dial.svg", svg(648, b));
}
