// 公众号封面：2.35:1 主封面（900×383，导出 2 倍）和 1:1 分享图（500×500，导出 2 倍）。
// 内容取自文章 7（setup slack 的时间账）。同文章 2、3、4，封面不放 slack 数字，免得脱离"综合后、理想时钟、不读寄生"和角名的限定。
// 用法：node docs/posts/figs/article7/make_cover.js，再用 Chrome 无头模式按 900×383、500×500 的窗口、2 倍缩放截图导出 PNG
const fs = require("fs");
const path = require("path");
const C = { bg: "#13233a", ink: "#ffffff", ink2: "#b9c6d8", blue: "#4a90e2", orange: "#f07a45", line: "#3a4d68" };
const FONT = "'Microsoft YaHei','PingFang SC','Noto Sans CJK SC',sans-serif";
const T = (x, y, s, o = {}) =>
  `<text x="${x}" y="${y}" font-size="${o.size}" fill="${o.fill || C.ink}" font-weight="${o.bold ? 700 : 400}" text-anchor="${o.anchor || "start"}">${s}</text>`;
// 账本：一条时间轴，实际到达（蓝）和最晚允许到达（竖线）之间的空当就是余量（橙）
const ledger = (x, y, w, h) => {
  const a = x + w * 0.56, d = x + w * 0.92;
  let s = `<rect x="${x}" y="${y}" width="${a - x}" height="${h}" rx="6" fill="${C.blue}"/>`;
  s += `<rect x="${a}" y="${y}" width="${d - a}" height="${h}" fill="${C.orange}"/>`;
  s += `<line x1="${d}" y1="${y - 26}" x2="${d}" y2="${y + h + 26}" stroke="${C.ink}" stroke-width="4"/>`;
  s += T(x + (a - x) / 2, y + h + 40, "实际到达", { size: h * 0.36, fill: C.blue, anchor: "middle", bold: true });
  s += T((a + d) / 2, y + h / 2 + h * 0.13, "余量", { size: h * 0.36, anchor: "middle", bold: true });
  s += T(d, y - 38, "最晚允许", { size: h * 0.36, anchor: "middle", fill: C.ink2 });
  return s;
};
const svg = (w, h, body) => `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" font-family="${FONT}">
<rect width="${w}" height="${h}" fill="${C.bg}"/>
${body}
</svg>
`;
// 主封面 900×383：左边标题，右边账本。编辑器做 1:1 裁剪时，把裁剪框放在左侧标题上（x≈40..423）
{
  let b = "";
  b += T(60, 118, "slack 不是快慢", { size: 46, bold: true });
  b += T(60, 178, "是一笔时间账", { size: 46, bold: true, fill: C.blue });
  b += T(60, 238, "改 6 个条件", { size: 26, fill: C.ink2 });
  b += T(60, 276, "一笔一笔对账", { size: 26, fill: C.ink2 });
  b += T(60, 340, "STA 学习笔记 · OpenSTA + Sky130", { size: 18, fill: C.ink2 });
  b += ledger(470, 160, 390, 64);
  fs.writeFileSync(path.join(__dirname, "cover_235.svg"), svg(900, 383, b));
}
// 分享图 500×500
{
  let b = "";
  b += T(250, 96, "slack 不是快慢", { size: 40, bold: true, anchor: "middle" });
  b += T(250, 150, "是一笔时间账", { size: 40, bold: true, fill: C.blue, anchor: "middle" });
  b += ledger(50, 270, 400, 60);
  b += T(250, 450, "改 6 个条件，一笔一笔对账", { size: 22, fill: C.ink2, anchor: "middle" });
  fs.writeFileSync(path.join(__dirname, "cover_1x1.svg"), svg(500, 500, b));
}
console.log("cover_235.svg cover_1x1.svg");
