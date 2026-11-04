// 公众号封面：2.35:1 主封面（900×383，导出 2 倍）和 1:1 分享图（500×500，导出 2 倍）。
// 内容取自文章 5（造题）。同文章 2–4，封面不放 slack 数字，免得脱离分析条件和角名的限定。
// 用法：node docs/posts/figs/article5/make_cover.js，再用 Chrome 无头模式按 900×383、500×500 的窗口、2 倍缩放截图导出 PNG
const fs = require("fs");
const path = require("path");
const C = { bg: "#13233a", ink: "#ffffff", ink2: "#b9c6d8", blue: "#4a90e2", orange: "#f07a45", line: "#3a4d68" };
const FONT = "'Microsoft YaHei','PingFang SC','Noto Sans CJK SC',sans-serif";
const T = (x, y, s, o = {}) =>
  `<text x="${x}" y="${y}" font-size="${o.size}" fill="${o.fill || C.ink}" font-weight="${o.bold ? 700 : 400}" text-anchor="${o.anchor || "start"}">${s}</text>`;
// 三个版本的方块，缺失版用橙色
const tag = (x, y, w, h, s, col, size) =>
  `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="10" fill="none" stroke="${col}" stroke-width="3"/>` +
  T(x + w / 2, y + h / 2 + size * 0.36, s, { size, fill: col, anchor: "middle", bold: true });
const svg = (w, h, body) => `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" font-family="${FONT}">
<rect width="${w}" height="${h}" fill="${C.bg}"/>
${body}
</svg>
`;
// 主封面 900×383：左边标题，右边三个版本。编辑器做 1:1 裁剪时，把裁剪框放在左侧标题上（x≈40..423）
{
  let b = "";
  b += T(60, 118, "给 AI 出时序题", { size: 46, bold: true });
  b += T(60, 178, "bug 埋对了吗？", { size: 46, bold: true, fill: C.orange });
  b += T(60, 238, "正确版、缺失版、恢复版", { size: 26, fill: C.ink2 });
  b += T(60, 276, "比三次，证明恰好是这一个", { size: 26, fill: C.ink2 });
  b += T(60, 340, "测 AI 的方法 · 造题", { size: 18, fill: C.ink2 });
  b += tag(620, 70, 220, 72, "正确版", C.blue, 30);
  b += tag(620, 160, 220, 72, "缺失版", C.orange, 30);
  b += tag(620, 250, 220, 72, "恢复版", C.blue, 30);
  fs.writeFileSync(path.join(__dirname, "cover_235.svg"), svg(900, 383, b));
}
// 分享图 500×500
{
  let b = "";
  b += T(250, 84, "给 AI 出时序题", { size: 40, bold: true, anchor: "middle" });
  b += T(250, 138, "bug 埋对了吗？", { size: 40, bold: true, fill: C.orange, anchor: "middle" });
  b += tag(140, 176, 220, 66, "正确版", C.blue, 28);
  b += tag(140, 258, 220, 66, "缺失版", C.orange, 28);
  b += tag(140, 340, 220, 66, "恢复版", C.blue, 28);
  b += T(250, 460, "测 AI 的方法 · 造题", { size: 22, fill: C.ink2, anchor: "middle" });
  fs.writeFileSync(path.join(__dirname, "cover_1x1.svg"), svg(500, 500, b));
}
console.log("cover_235.svg cover_1x1.svg");
