// 公众号封面：2.35:1 主封面（900×383，导出 2 倍）和 1:1 分享图（500×500，导出 2 倍）。
// 内容取自文章 2：三家各改两轮共 6 份，都过了功能回归，只有 Claude 第 2 轮在冻结流程里拿到有效时序结果，
// 其余 5 份卡在 STA（public §1、§5）。封面不放 slack 数字，免得脱离"理想时钟、综合后、只计引脚电容"的限定。
// 用法：node docs/posts/figs/article2/make_cover.js
const fs = require("fs");
const path = require("path");
const C = { bg: "#13233a", ink: "#ffffff", ink2: "#b9c6d8", blue: "#4a90e2", orange: "#f07a45", line: "#3a4d68",
  cell: "#1d3150", ok: "#2f9e6e" };
const FONT = "'Microsoft YaHei','PingFang SC','Noto Sans CJK SC',sans-serif";
const T = (x, y, s, o = {}) =>
  `<text x="${x}" y="${y}" font-size="${o.size}" fill="${o.fill || C.ink}" font-weight="${o.bold ? 700 : 400}" text-anchor="${o.anchor || "start"}">${s}</text>`;
// 3×2 格子：行是模型，列是轮次；每格上一行"回归 ✓"，下一行 STA 结果
const grid = (x0, y0, lw, cw, ch, gap, f) => {
  let s = "";
  ["第 1 轮", "第 2 轮"].forEach((r, j) =>
    s += T(x0 + lw + j * (cw + gap) + cw / 2, y0 - 14, r, { size: f, fill: C.ink2, anchor: "middle" }));
  ["Claude", "Kimi", "DeepSeek"].forEach((m, i) => {
    const y = y0 + i * (ch + gap);
    s += T(x0, y + ch / 2 + f * 0.35, m, { size: f, fill: C.ink2 });
    [0, 1].forEach(j => {
      const x = x0 + lw + j * (cw + gap), ok = i === 0 && j === 1;
      s += `<rect x="${x}" y="${y}" width="${cw}" height="${ch}" rx="6" fill="${ok ? C.ok : C.cell}" stroke="${ok ? C.ok : C.line}"/>`;
      s += T(x + cw / 2, y + ch * 0.42, "回归 ✓", { size: f * 0.85, fill: ok ? C.ink : C.ink2, anchor: "middle" });
      s += T(x + cw / 2, y + ch * 0.80, ok ? "时序结果 ✓" : "卡在 STA", { size: f * 0.95, bold: true,
        fill: ok ? C.ink : C.orange, anchor: "middle" });
    });
  });
  return s;
};
const svg = (w, h, body) => `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" font-family="${FONT}">
<rect width="${w}" height="${h}" fill="${C.bg}"/>
${body}
</svg>
`;
// 主封面 900×383：左边标题，右边 6 格。编辑器做 1:1 裁剪时，把裁剪框放在左侧标题上（x≈40..423）
{
  let b = "";
  b += T(60, 120, "让大模型", { size: 46, bold: true });
  b += T(60, 178, "动手改 RTL", { size: 46, bold: true, fill: C.orange });
  b += T(60, 238, "6 份过了回归", { size: 26, fill: C.ink2 });
  b += T(60, 276, "1 份拿到有效时序结果", { size: 26, fill: C.ink2 });
  b += T(60, 340, "AI 提出的时序建议，用工程实验验证", { size: 18, fill: C.ink2 });
  b += grid(500, 88, 100, 120, 70, 14, 18);
  fs.writeFileSync(path.join(__dirname, "cover_235.svg"), svg(900, 383, b));
}
// 分享图 500×500
{
  let b = "";
  b += T(250, 84, "让大模型", { size: 40, bold: true, anchor: "middle" });
  b += T(250, 136, "动手改 RTL", { size: 40, bold: true, fill: C.orange, anchor: "middle" });
  b += grid(62, 210, 104, 126, 62, 12, 18);
  b += T(250, 468, "6 份过了回归，1 份拿到有效时序结果", { size: 20, fill: C.ink2, anchor: "middle" });
  fs.writeFileSync(path.join(__dirname, "cover_1x1.svg"), svg(500, 500, b));
}
console.log("cover_235.svg cover_1x1.svg");
