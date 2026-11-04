// 公众号封面：2.35:1 主封面（900×383，导出 2 倍）和 1:1 分享图（500×500，导出 2 倍）。
// 内容取自文章 4（温度反转）。同文章 2、3，封面不放 slack 数字，免得脱离"综合后、理想时钟、不读寄生"和角名的限定。
// 用法：node docs/posts/figs/article4/make_cover.js，再用 Chrome 无头模式按 900×383、500×500 的窗口、2 倍缩放截图导出 PNG
const fs = require("fs");
const path = require("path");
const C = { bg: "#13233a", ink: "#ffffff", ink2: "#b9c6d8", blue: "#4a90e2", orange: "#f07a45", line: "#3a4d68" };
const FONT = "'Microsoft YaHei','PingFang SC','Noto Sans CJK SC',sans-serif";
const T = (x, y, s, o = {}) =>
  `<text x="${x}" y="${y}" font-size="${o.size}" fill="${o.fill || C.ink}" font-weight="${o.bold ? 700 : 400}" text-anchor="${o.anchor || "start"}">${s}</text>`;
// 温度计：玻璃管 + 液柱 + 底部球，fill 0..1 为液柱高度比例
const thermo = (x, y, h, fill, col, label) => {
  const w = h * 0.16, r = w * 0.95;
  let s = `<rect x="${x - w / 2}" y="${y}" width="${w}" height="${h}" rx="${w / 2}" fill="none" stroke="${C.ink2}" stroke-width="3"/>`;
  s += `<circle cx="${x}" cy="${y + h + r * 0.6}" r="${r}" fill="${col}" stroke="${C.ink2}" stroke-width="3"/>`;
  const lh = (h - w / 2) * fill;
  s += `<rect x="${x - w / 2 + 5}" y="${y + h - lh}" width="${w - 10}" height="${lh + r * 0.4}" rx="${(w - 10) / 2}" fill="${col}"/>`;
  for (let i = 1; i < 5; i++) s += `<line x1="${x + w / 2 + 4}" y1="${y + h * i / 5}" x2="${x + w / 2 + 14}" y2="${y + h * i / 5}" stroke="${C.ink2}" stroke-width="2"/>`;
  s += T(x, y + h + r * 2.2 + 18, label, { size: h * 0.13, fill: col, anchor: "middle", bold: true });
  return s;
};
const svg = (w, h, body) => `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" font-family="${FONT}">
<rect width="${w}" height="${h}" fill="${C.bg}"/>
${body}
</svg>
`;
// 主封面 900×383：左边标题，右边两支温度计。编辑器做 1:1 裁剪时，把裁剪框放在左侧标题上（x≈40..423）
{
  let b = "";
  b += T(60, 118, "芯片冷的时候", { size: 46, bold: true });
  b += T(60, 178, "反而更慢？", { size: 46, bold: true, fill: C.blue });
  b += T(60, 238, "亲手跑一遍温度反转", { size: 26, fill: C.ink2 });
  b += T(60, 276, "再看三个大模型怎么解释", { size: 26, fill: C.ink2 });
  b += T(60, 340, "STA 学习笔记 · OpenSTA + Sky130", { size: 18, fill: C.ink2 });
  b += thermo(600, 70, 190, 0.18, C.blue, "−40 °C");
  b += thermo(760, 70, 190, 0.85, C.orange, "100 °C");
  fs.writeFileSync(path.join(__dirname, "cover_235.svg"), svg(900, 383, b));
}
// 分享图 500×500
{
  let b = "";
  b += T(250, 84, "芯片冷的时候", { size: 40, bold: true, anchor: "middle" });
  b += T(250, 138, "反而更慢？", { size: 40, bold: true, fill: C.blue, anchor: "middle" });
  b += thermo(170, 170, 170, 0.18, C.blue, "−40 °C");
  b += thermo(330, 170, 170, 0.85, C.orange, "100 °C");
  b += T(250, 470, "亲手跑一遍温度反转", { size: 22, fill: C.ink2, anchor: "middle" });
  fs.writeFileSync(path.join(__dirname, "cover_1x1.svg"), svg(500, 500, b));
}
console.log("cover_235.svg cover_1x1.svg");
