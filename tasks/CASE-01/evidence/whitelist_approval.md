# CASE-01 警告白名单审批记录（检查点 A）

- 批准人：作者（项目作者本人），在 Claude 会话中于检查点 A 批准
- 日期：2026-10-09
- 依据：spec 第 6 节（只能在 F1 之前、只能是窄范围）；`docs/review/CASE01_C3_codex.md` 第 6 节的解释（Liberty/SCL 读取阶段的库属性消息）
- 触发运行：`runs/20261009-064746-pipe2-T20`（夹具 impl.pipe2.cfg，T=20），在 synth 步骤因这条警告判失败；该行位于 yosys.log 第 663 行，紧跟 `read_scl`，在 strash/dc2/&nf 之前；这是日志中唯一一条 Warning
- 条目全文（第 3 行，字段之间为 TAB）：

```text
yosys	^ABC: Warning: Detected 9 multi-output cells \(for example, "sky130_fd_sc_hd__fa_1"\)\.$	Liberty/SCL read-time notice about multi-output cells (e.g. full adders) in the frozen tt library; reviewed in docs/review/CASE01_C3_codex.md section 6; approved by the author on 2026-10-09; does not excuse library parse errors, mapping failures, unlinked cells or functional mismatch
```

- 文件哈希（`sha256sum config/warn_whitelist.txt`）：

```
35f1ef4b8940b67295cb8c2877658e72aff81658b9dd1bf7f054644beead52f6  config/warn_whitelist.txt
```

- 说明："与 `plan/proto/config/warn_whitelist.txt` 不同，属于作者批准的配置差异"
- 范围限制：只对 yosys 生效；整行精确匹配（数量 9、示例 fa_1）；库、工具或排除清单变化时需重新审查；不豁免库解析错误、映射失败、未链接单元或功能不一致；命中次数记入 verdict.json 的 whitelist_hits
