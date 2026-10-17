"""Turn docs/posts/article1_public.md into an HTML page for pasting into the WeChat Official Account editor.

  python -I docs/posts/wechat/make_wechat.py            (from the repository root)

The WeChat editor keeps inline styles and drops style sheets, so every element carries its own style. It does not
upload local images, so each image becomes a placeholder box naming the PNG to insert by hand. The page has a
"copy" button that copies only the article body; the title, the summary and the instructions stay outside it.
Only the Markdown used in the article is supported: one H1, H2, paragraphs, "- " lists, "> " quotes, images, **bold**,
`code` and bare URLs.
"""
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SRC = os.path.join(ROOT, "docs", "posts", "article1_public.md")
OUT = os.path.join(ROOT, "docs", "posts", "wechat", "article1_wechat.html")
FIGS = "docs/posts/figs/article1"

INK, INK2, ACCENT, SOFT = "#222222", "#555555", "#2a78d6", "#f5f6f8"
S_P = f"margin:0 0 18px 0;font-size:16px;line-height:1.8;letter-spacing:0.5px;color:{INK};text-align:justify;"
S_H2 = (f"margin:36px 0 16px 0;padding:2px 0 2px 12px;border-left:4px solid {ACCENT};font-size:19px;"
        f"font-weight:bold;line-height:1.5;color:{INK};")
S_UL = "margin:0 0 18px 0;padding-left:22px;"
S_LI = f"margin:0 0 8px 0;font-size:16px;line-height:1.8;letter-spacing:0.5px;color:{INK};"
S_QUOTE = (f"margin:0 0 20px 0;padding:12px 16px;background:{SOFT};border-left:3px solid #c9c8c3;"
           f"font-size:14px;line-height:1.75;color:{INK2};")
S_CODE = "font-family:Menlo,Consolas,monospace;font-size:14px;background:#eef0f3;padding:1px 4px;border-radius:3px;"
S_FIG = ("margin:8px 0 22px 0;padding:22px 12px;border:2px dashed #eb6834;border-radius:6px;background:#fff7f3;"
         "text-align:center;font-size:15px;line-height:1.7;color:#b4441c;")


def inline(text):
    t = html.escape(text, quote=False)
    t = re.sub(r"`([^`]+)`", lambda m: f'<code style="{S_CODE}">{m.group(1)}</code>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", lambda m: f'<strong style="color:{INK};">{m.group(1)}</strong>', t)
    t = re.sub(r"(https?://[^\s<）)]+)", lambda m: f'<span style="color:{ACCENT};word-break:break-all;">{m.group(1)}</span>', t)
    return t


def convert(md):
    lines = md.splitlines()
    title, body, figs = None, [], []
    i = 0
    para = []

    def flush():
        if para:
            body.append(f'<p style="{S_P}">{inline(" ".join(para))}</p>')
            para.clear()
    while i < len(lines):
        line = lines[i]
        if line.startswith("# "):
            flush(); title = line[2:].strip()
        elif line.startswith("## "):
            flush(); body.append(f'<h2 style="{S_H2}">{inline(line[3:].strip())}</h2>')
        elif line.startswith("!["):
            flush()
            m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", line)
            n = len(figs) + 1
            name = os.path.basename(m.group(2))
            figs.append((n, m.group(1), name))
            body.append(f'<section style="{S_FIG}"><strong>【图 {n}】在此插入图片</strong><br>'
                        f'{html.escape(name)}<br><span style="color:#888;font-size:13px;">{html.escape(m.group(1))}</span>'
                        f'</section>')
        elif line.startswith("- "):
            flush(); items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(lines[i][2:].strip()); i += 1
            body.append(f'<ul style="{S_UL}">' + "".join(f'<li style="{S_LI}">{inline(x)}</li>' for x in items) + "</ul>")
            continue
        elif line.startswith(">"):
            flush(); block, cur = [], []
            while i < len(lines) and lines[i].startswith(">"):
                s = lines[i][1:].strip()
                if s.startswith("- "):          # a list inside a quote: one bullet per line
                    if cur:
                        block.append(" ".join(cur)); cur = []
                    block.append("• " + s[2:])
                elif s:
                    cur.append(s)
                elif cur:
                    block.append(" ".join(cur)); cur = []
                i += 1
            if cur:
                block.append(" ".join(cur))
            body.append(f'<section style="{S_QUOTE}">' + "<br>".join(inline(x) for x in block) + "</section>")
            continue
        elif not line.strip():
            flush()
        else:
            para.append(line.strip())
        i += 1
    flush()
    return title, body, figs


def page(title, body, figs):
    fig_rows = "".join(f"<li>图 {n}：<code style='overflow-wrap:anywhere;word-break:break-all;'>{FIGS}/{html.escape(name)}</code>（{html.escape(alt)}）</li>" for n, alt, name in figs)
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>公众号排版 · 文章 1</title></head>
<body style="margin:0;background:#eceef1;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;">
<div style="max-width:720px;margin:0 auto;padding:16px;box-sizing:border-box;overflow-wrap:anywhere;">
<div style="background:#fffbe6;border:1px solid #f0d58a;border-radius:8px;padding:14px 18px;margin-bottom:16px;font-size:14px;line-height:1.7;color:#5c4a00;">
<p style="margin:0 0 6px 0;"><strong>用法</strong>（这一块不会被复制）</p>
<ol style="margin:0;padding-left:20px;">
<li>标题填到公众号编辑器的标题栏：<strong>{html.escape(title or "")}</strong></li>
<li>点下面的"复制正文"，到编辑器正文区粘贴。</li>
<li>正文里有 {len(figs)} 个橙色虚线框，逐个点中，替换成对应的图片（PNG，2 倍分辨率）：<ul style="margin:4px 0;padding-left:18px;">{fig_rows}</ul></li>
<li>文末的仓库链接在公众号里不能点，保留为文字；仓库公开后读者可以复制访问。</li>
<li>发布前用编辑器的"预览"在手机上看一遍。</li>
</ol>
<button id="copy" style="margin-top:10px;padding:8px 18px;font-size:15px;border:0;border-radius:6px;background:#2a78d6;color:#fff;cursor:pointer;">复制正文</button>
<span id="msg" style="margin-left:10px;"></span>
</div>
<div id="article" style="background:#ffffff;padding:24px 18px;border-radius:8px;">
<section style="font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;">
{chr(10).join(body)}
</section>
</div>
</div>
<script>
document.getElementById('copy').onclick = function () {{
  var el = document.getElementById('article'), r = document.createRange(), s = window.getSelection();
  s.removeAllRanges(); r.selectNodeContents(el); s.addRange(r);
  var ok = false; try {{ ok = document.execCommand('copy'); }} catch (e) {{}}
  s.removeAllRanges();
  document.getElementById('msg').textContent = ok ? '已复制，去编辑器粘贴' : '复制失败，请手动全选正文复制';
}};
</script>
</body></html>
"""


def main():
    with open(SRC, encoding="utf-8") as f:
        title, body, figs = convert(f.read())
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(page(title, body, figs))
    sys.stdout.buffer.write(f"{os.path.relpath(OUT, ROOT)}: {len(body)} blocks, {len(figs)} figures\n".encode())


if __name__ == "__main__":
    main()
