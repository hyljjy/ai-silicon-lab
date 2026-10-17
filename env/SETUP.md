# 搭建复现环境（Ubuntu 24.04）

本项目的实验在 WSL2 的 Ubuntu 24.04 里运行。原生 Ubuntu 24.04 也可以，步骤相同。本文只讲"装什么、装到哪、怎么验证"；每个工具的来源、版本、校验值和构建细节见 [INSTALL_RECORD.md](INSTALL_RECORD.md)，这里不重复。

复现时最重要的是**版本一致**：Yosys/ABC 和 OpenSTA 的版本不同，网表和时序数字就可能不同。

## 1. 目录约定

所有路径都相对于运行用户的 `$HOME`。**要复现 CASE-01，运行用户必须是 `eda`，HOME 必须是 `/home/eda`**：F1 的证据里记着 liberty 文件的绝对路径 `/home/eda/pdk/...`，复现时要逐字节比对，见 [REPRODUCE.md](../REPRODUCE.md) 第 1 节。项目脚本通过 [open_eda_env.sh](open_eda_env.sh) 里的变量找到工具和单元库，所以请按下面的布局安装：

```
~/src/            源码（OpenSTA、CUDD）
~/tools/          安装目录：opensta/、cudd/、oss-cad-suite/、ciel-venv/、open_eda_env.sh
~/pdk/            ciel 管理的 PDK（= $PDK_ROOT）
~/pdk/sky130hd_kit/   项目的综合与多 corner 脚本（= $SKY130_KIT）
~/smoke/sky130/   冒烟测试
```

## 2. 安装

按 [INSTALL_RECORD.md](INSTALL_RECORD.md) 的顺序执行：

1. 第 2 节：用 apt 装系统包（编译器、Tcl、SWIG、CMake、Ninja、Python 3.12 等）。
2. 第 3.1 节：下载 OSS CAD Suite `2026-10-03` 发行包，先核对 sha256，再解压到 `~/tools/oss-cad-suite`。它提供 Yosys、ABC、Icarus Verilog。
3. 第 3.2 节：从源码构建 CUDD 3.0.0（固定 commit），安装到 `~/tools/cudd`。
4. 第 3.3 节：从源码构建 OpenSTA，**必须用 commit `7a034b56de14b485ddf8fd97b420a6f37a91c00d`**，安装到 `~/tools/opensta`。
5. 第 3.4 节：建 ciel 的 venv，安装 Sky130 PDK `1689ac3f2dc763876eaf967227c7dfe831b031ae`，只装 `sky130_fd_sc_hd`。

## 3. 放置环境脚本和项目脚本

在仓库根目录执行（`<repo>` 换成你的克隆路径）：

```bash
cp <repo>/env/open_eda_env.sh ~/tools/open_eda_env.sh
echo 'source $HOME/tools/open_eda_env.sh' >> ~/.profile
echo 'source $HOME/tools/open_eda_env.sh' >> ~/.bashrc
mkdir -p ~/pdk/sky130hd_kit ~/smoke/sky130
cp <repo>/env/sky130hd_kit/{MANIFEST.txt,synth.tcl,corners.tcl} ~/pdk/sky130hd_kit/
cp <repo>/env/smoke/sky130/{run.sh,sta.tcl,mac.v,tb.v} ~/smoke/sky130/
chmod +x ~/smoke/sky130/run.sh
```

注意 `open_eda_env.sh` 只把 OSS CAD Suite 的 `bin/` **追加**到 PATH 末尾，不要 source 包里自带的 `environment`：它会把包里的 Python 3.11 放到最前面，遮住系统的 python3。工具只在 login shell 里可用，从 Windows 调用时要用 `wsl -d Ubuntu-24.04 --exec bash -l ...`。

## 4. 验证

**冒烟测试。** 在一个新的 login shell 里运行：

```bash
~/smoke/sky130/run.sh
```

它依次做 RTL 仿真、综合、门级仿真和 16 个 corner 的 STA，最后一行应为 `SMOKE OK`。期望输出：

```
SIM PASS acc=36
   Chip area for module '\mac': 3336.950400
SIM PASS acc=36
set    corner             setup_ws    hold_ws
std    tt_025C_1v80          0.778      0.272
std    tt_100C_1v80          0.811      0.268
std    ss_100C_1v60         -3.641      0.345
std    ss_n40C_1v60         -4.775      0.340
std    ff_n40C_1v95          2.475      0.249
std    ff_100C_1v95          2.420      0.245
sweep  ff_100C_1v65          1.710      0.254
sweep  ff_n40C_1v56          0.848      0.271
sweep  ff_n40C_1v65          1.418      0.265
sweep  ff_n40C_1v76          1.919      0.258
sweep  ss_100C_1v40         -7.736      0.397
sweep  ss_n40C_1v28        -27.570      0.592
sweep  ss_n40C_1v35        -17.474      0.485
sweep  ss_n40C_1v40        -13.136      0.435
sweep  ss_n40C_1v44        -10.734      0.409
sweep  ss_n40C_1v76         -2.019      0.310
SMOKE OK
```

面积或任何一个 slack 不同，说明工具或单元库的版本和原实验不一致，后面的复现结果也不可信。

**环境快照。**

```bash
bash <repo>/env/snapshot.sh check
```

它核对 4 项：快照文件本身、`~/tools` 和 `~/pdk/sky130hd_kit` 下的脚本是否与快照逐字节相同、18 个 `.lib` 的 sha256、工具二进制的指纹。在作者的机器上输出 `SNAPSHOT OK`。

在另一台机器上，**前三项应当通过；第 4 项预计会报 `DRIFT: tool binaries differ from tools.sha256`**：OpenSTA 和 CUDD 是从源码编译的，即使 commit 相同，编译出的二进制哈希也会因编译器和构建路径而不同。OSS CAD Suite 是预编译包，它的几个二进制应当相同。这种情况下，复现脚本要加 `--allow-tool-drift`，见仓库根目录的 [REPRODUCE.md](../REPRODUCE.md)。工具是否真的等价，由网表哈希和查询输出是否逐字节一致来判断。

## 5. 已知限制

- 作者只在自己的机器上从干净克隆跑通过完整复现，还没有在另一台机器上从零装环境验证过。
- 安装时下载的发行包没有随项目分发，校验值来自 GitHub 发布页（见 INSTALL_RECORD 第 3 节）。如果发布页下架，需要另找来源，并核对同一个 sha256。
