# 环境快照（`env/`）

> 落实执行计划修订记录 R1 第 5 条的前两项：读者不用访问作者的 HOME 目录，也能看到实验实际用到的脚本、库哈希、工具指纹、安装方法和许可来源。快照日期：2026-10-04。

## 这是什么

实验运行时调用的是 WSL `Ubuntu-24.04` 里的文件（`$SKY130_KIT/synth.tcl` 等）。本目录保存的是它们**逐字节相同的副本**，外加几份校验清单。

- 副本没有做任何修改，所以脚本里的路径仍然通过 `$HOME`、`$PDK_ROOT`、`$SKY130_HD`、`$SKY130_KIT` 这些变量指向 WSL 里的目录布局，变量的定义见 [open_eda_env.sh](open_eda_env.sh)。
- WSL 里的文件是运行用的，本目录是存档记录。两者是否一致，用 `snapshot.sh check` 核对。

## 文件

| 快照文件 | WSL 来源 | 说明 |
|---|---|---|
| `open_eda_env.sh` | `~/tools/open_eda_env.sh` | 环境脚本：PATH 和 PDK 相关变量 |
| `sky130hd_kit/MANIFEST.txt` | `~/pdk/sky130hd_kit/MANIFEST.txt` | PDK 来源，18 个 `.lib` 及 `synth_excluded.cells` 的 sha256 |
| `sky130hd_kit/synth.tcl` | `~/pdk/sky130hd_kit/synth.tcl` | Yosys 综合脚本 |
| `sky130hd_kit/corners.tcl` | `~/pdk/sky130hd_kit/corners.tcl` | OpenSTA 多 corner 设置（`std` / `sweep` 分组） |
| `smoke/sky130/{run.sh,sta.tcl,mac.v,tb.v}` | `~/smoke/sky130/` | 冒烟测试。期望输出见 [SETUP.md 第 4 节](SETUP.md) |
| `tools.sha256` | 由脚本生成 | 6 个工具二进制的 sha256，路径相对于 `~/tools` |
| `SHA256SUMS` | 由脚本生成 | 上面这些文件，加上 `licenses/` 下两份许可原文的 sha256 |
| [INSTALL_RECORD.md](INSTALL_RECORD.md) | — | 安装记录：发行包及校验值、源码 commit、构建步骤、依赖（R1 第 5 条第 1 项） |
| [licenses/](licenses/SOURCES.md) | — | 许可原文和出处 |
| `snapshot.sh` | — | 生成快照、核对现场环境 |

## 用法

```bash
wsl -d Ubuntu-24.04 --exec bash -l /mnt/d/study/ai_native_design/env/snapshot.sh check    # 默认
wsl -d Ubuntu-24.04 --exec bash -l /mnt/d/study/ai_native_design/env/snapshot.sh update
```

`check` 依次核对下面几项。全部一致时打印 `SNAPSHOT OK`、退出码为 0；任何一项不一致都打印 `FAIL` 或 `DRIFT` 行，退出码为 1。

1. 本目录的文件与 `SHA256SUMS` 一致，即快照本身没有被改过；
2. 每个快照文件与 WSL 中的来源文件逐字节相同；
3. PDK 的 18 个 `.lib` 和 `synth_excluded.cells` 与 `MANIFEST.txt` 中的 sha256 一致；
4. 工具二进制与 `tools.sha256` 一致。

`update` 把 WSL 中的来源文件复制过来，并重写 `tools.sha256` 和 `SHA256SUMS`。规则：

- 改动环境（升级工具、修改 kit 脚本、更换 PDK）之前，要先征得作者同意。改完之后依次：重跑冒烟测试 → `update` → `check`，再同步更新 `INSTALL_RECORD.md` 和 `SETUP.md` 里的版本信息。
- 不要为了让 `check` 通过就去跑 `update`。`check` 报 DRIFT，说明环境变了，要先查清楚是谁、为什么改的。
- 建议：CASE-01 的 grader 在每次运行前先跑 `check`，不通过就停下，不产出结果。

## 已验证（2026-10-04）

- 在当前环境下，`check` 输出 `SNAPSHOT OK`。
- 冒烟测试 `run.sh` 输出 `SMOKE OK`，16 个 corner 的 setup / hold 数值与 [SETUP.md](SETUP.md) 第 4 节逐项一致。
- `snapshot.sh` 做了故障注入测试，11 个场景全部符合预期：基线通过；快照文件被改；来源文件被改；来源文件缺失；某个 `.lib` 被改；`.lib` 目录为空；`synth_excluded.cells` 被改；工具二进制被改；没有 login 环境（变量未设置）；参数错误（退出码 2）；`update` 之后再 `check` 通过。测试在 `/tmp` 下的副本上进行，没有动 `$HOME` 和项目文件。
- `run.sh` 的 sha256 是 `717d7d5f…`，与 2026-10-03 会话记录的值一致。

## 不在快照里的东西

- **PDK 文件本身**（`.lib`、Verilog 模型等）：项目里只记录哈希。PDK 发布包被下架时的备用路径（R1 第 5 条第 3 项）已经落实：ciel 的两个发行包、校验值和离线恢复脚本备份在项目外的 `D:\study\eda_archive\pdk\sky130-1689ac3f…\`，2026-10-04 做过端到端验证，结果是恢复出的目录与现有安装逐文件相同，用本目录的脚本跑冒烟得到 `SMOKE OK`。详见那里的 README。这份备份是作者本机的私有备份，不随项目分发。
- **工具的二进制和安装包**：只记录来源、校验值和指纹，见 INSTALL_RECORD。
- **冒烟测试的运行产物**（网表、日志）：期望输出见 [SETUP.md](SETUP.md) 第 4 节。
- **本目录脚本的许可**：还没有决定，见 [licenses/SOURCES.md](licenses/SOURCES.md) 第 3 节。

## 换行符

`SHA256SUMS` 校验的是文件的原始字节，所以本目录必须保持 LF 换行。[.gitattributes](.gitattributes) 里设了 `* -text`，防止 Windows 上 git checkout 时把换行转换成 CRLF。在 Windows 上编辑这些文件时，也要确认编辑器保存的是 LF。
