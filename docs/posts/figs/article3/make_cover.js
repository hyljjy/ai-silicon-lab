// 公众号封面：2.35:1 主封面（900×383，导出 2 倍）和 1:1 分享图（500×500，导出 2 倍）。
// 内容取自文章 3：缺失版删掉 in_b[63:0] 的 set_input_delay（min/max 共 128 条），130 个非时钟输入里
// 只剩 in_a 64 + in_valid + rst = 66 个受约束（public §1、§2；draft §2.3）。
// 封面同文章 2，不放 slack 数字，免得脱离"综合后、理想时钟、不读寄生、只计引脚电容"和角名的限定。
// 用法：node docs/posts/figs/article3/make_cover.js
const fs = require("fs");
const path = require("path");
const C = { bg: "#13233a", ink: "#ffffff", ink2: "#b9c6d8", blue: "#4a90e2", orange: "#f07a45", line: "#3a4d68" };
const FONT = "'Microsoft YaHei','PingFang SC','Noto Sans CJK SC',sans-serif";
const T = (x, y, s, o = {}) =>
  `<text x="${x}" y="${y}" font-size="${o.size}" fill="${o.fill || C.ink}" font-weight="${o.bold ? 700 : 400}" text-anchor="${o.anchor || "start"}">${s}</text>`;
// 一个 8×8 端口块：实心蓝 = 有 input delay，空心橙虚线 = 删掉了
const block = (x0, y0, p, r, on) => {
  let s = "";
  for (let i = 0; i < 8; i++) for (let j = 0; j < 8; j++) {
    const cx = x0 + j * p + p / 2, cy = y0 + i * p + p / 2;
    s += on ? `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${C.blue}"/>`
      : `<circle cx="${cx}" cy="${cy}" r="${r - 0.8}" fill="none" stroke="${C.orange}" stroke-width="1.6" stroke-dasharray="2 1.6"/>`;
  }
  return s;
};
// 端口图：in_a、in_b 两块，下面 in_valid、rst 两个点，再下面图例
const ports = (x0, y0, p, gap, f) => {
  const w = 8 * p, r = p * 0.36;
  let s = "";
  s += T(x0 + w / 2, y0 - 12, "in_a[63:0]", { size: f, fill: C.ink2, anchor: "middle" });
  s += T(x0 + w + gap + w / 2, y0 - 12, "in_b[63:0]", { size: f, fill: C.orange, anchor: "middle", bold: true });
  s += block(x0, y0, p, r, true) + block(x0 + w + gap, y0, p, r, false);
  const y1 = y0 + w + p * 1.2;
  s += `<circle cx="${x0 + p / 2}" cy="${y1}" r="${r}" fill="${C.blue}"/>`;
  s += `<circle cx="${x0 + p * 1.5}" cy="${y1}" r="${r}" fill="${C.blue}"/>`;
  s += T(x0 + p * 2.4, y1 + f * 0.35, "in_valid、rst", { size: f * 0.9, fill: C.ink2 });
  const y2 = y1 + f * 2.2;
  s += `<circle cx="${x0 + p / 2}" cy="${y2 - f * 0.35}" r="${r}" fill="${C.blue}"/>`;
  s += T(x0 + p * 1.4, y2, "66 个有 delay", { size: f * 0.9, fill: C.ink2 });
  s += `<circle cx="${x0 + w + gap + p / 2}" cy="${y2 - f * 0.35}" r="${r - 0.8}" fill="none" stroke="${C.orange}" stroke-width="1.6" stroke-dasharray="2 1.6"/>`;
  s += T(x0 + w + gap + p * 1.4, y2, "64 个删了 delay", { size: f * 0.9, fill: C.orange });
  return s;
};
const svg = (w, h, body) => `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" font-family="${FONT}">
<rect width="${w}" height="${h}" fill="${C.bg}"/>
${body}
</svg>
`;
// 主封面 900×383：左边标题，右边端口图。编辑器做 1:1 裁剪时，把裁剪框放在左侧标题上（x≈40..423）
{
  let b = "";
  b += T(60, 120, "约束漏了 128 条", { size: 44, bold: true });
  b += T(60, 178, "slack 反而变好", { size: 44, bold: true, fill: C.orange });
  b += T(60, 238, "三个大模型拿到同一道题", { size: 26, fill: C.ink2 });
  b += T(60, 276, "能不能查出缺了什么", { size: 26, fill: C.ink2 });
  b += T(60, 340, "AI 提出的时序建议，用工程实验验证 · CASE-02", { size: 18, fill: C.ink2 });
  b += ports(520, 98, 17, 36, 17);
  fs.writeFileSync(path.join(__dirname, "cover_235.svg"), svg(900, 383, b));
}
// 分享图 500×500
{
  let b = "";
  b += T(250, 84, "约束漏了 128 条", { size: 38, bold: true, anchor: "middle" });
  b += T(250, 136, "slack 反而变好", { size: 38, bold: true, fill: C.orange, anchor: "middle" });
  b += ports(84, 210, 19, 28, 17);
  b += T(250, 476, "三个大模型能不能查出缺了什么", { size: 20, fill: C.ink2, anchor: "middle" });
  fs.writeFileSync(path.join(__dirname, "cover_1x1.svg"), svg(500, 500, b));
}
console.log("cover_235.svg cover_1x1.svg");
