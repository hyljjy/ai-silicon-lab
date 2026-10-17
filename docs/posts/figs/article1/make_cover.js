// 公众号封面：2.35:1 主封面（900×383，导出 2 倍）和 1:1 分享图（500×500，导出 2 倍）。
// 数字取自文章 1：原路径改善 2.30 ns，全设计最差只改善 0.67 ns（draft §5.2、§7）。
// 用法：node docs/posts/figs/article1/make_cover.js
const fs = require("fs");
const path = require("path");
const C = { bg: "#13233a", ink: "#ffffff", ink2: "#b9c6d8", blue: "#4a90e2", orange: "#f07a45", line: "#3a4d68" };
const FONT = "'Microsoft YaHei','PingFang SC','Noto Sans CJK SC',sans-serif";
const T = (x, y, s, o = {}) =>
  `<text x="${x}" y="${y}" font-size="${o.size}" fill="${o.fill || C.ink}" font-weight="${o.bold ? 700 : 400}" text-anchor="${o.anchor || "start"}">${s}</text>`;
const bars = (x0, y0, k, h, gap, label) => {
  // 两根柱子：原路径 2.30、全设计最差 0.67
  let s = "";
  [["这条路径", 2.30, C.blue], ["全设计最差", 0.67, C.orange]].forEach(([name, v, col], i) => {
    const y = y0 + i * (h + gap);
    s += T(x0, y - 10, name, { size: label, fill: C.ink2 });
    s += `<rect x="${x0}" y="${y}" width="${v * k}" height="${h}" rx="5" fill="${col}"/>`;
    s += T(x0 + v * k + 12, y + h * 0.75, `+${v.toFixed(2)}`, { size: h * 0.78, bold: true });
  });
  return s;
};
const svg = (w, h, body) => `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" font-family="${FONT}">
<rect width="${w}" height="${h}" fill="${C.bg}"/>
${body}
</svg>
`;
// 主封面 900×383：左边标题，右边两根柱子。编辑器做 1:1 裁剪时，把裁剪框放在左侧标题上（x≈40..423）
{
  let b = "";
  b += T(60, 128, "大模型看时序报告", { size: 46, bold: true });
  b += T(60, 186, "靠谱吗？", { size: 46, bold: true, fill: C.orange });
  b += T(60, 246, "用 OpenSTA 逐条核对", { size: 26, fill: C.ink2 });
  b += T(60, 284, "Claude · Kimi · DeepSeek", { size: 26, fill: C.ink2 });
  b += T(60, 340, "AI 提出的时序建议，用工程实验验证", { size: 18, fill: C.ink2 });
  b += T(480, 82, "换强一个单元后的 slack 改善（ns）", { size: 18, fill: C.ink2 });
  b += bars(480, 150, 105, 54, 64, 20);
  fs.writeFileSync(path.join(__dirname, "cover_235.svg"), svg(900, 383, b));
}
// 分享图 500×500
{
  let b = "";
  b += T(250, 92, "大模型看时序报告", { size: 40, bold: true, anchor: "middle" });
  b += T(250, 146, "靠谱吗？", { size: 40, bold: true, fill: C.orange, anchor: "middle" });
  b += bars(70, 250, 110, 50, 58, 20);
  b += T(250, 452, "用 OpenSTA 逐条核对", { size: 22, fill: C.ink2, anchor: "middle" });
  fs.writeFileSync(path.join(__dirname, "cover_1x1.svg"), svg(500, 500, b));
}
console.log("cover_235.svg cover_1x1.svg");
