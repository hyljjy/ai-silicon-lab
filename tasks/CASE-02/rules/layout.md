# CASE-02 目录与封存布局（规程 v0.3 第 8、9 节；实现计划 Task 1）

- 封存目录：`D:\study\diag_sandbox\sealed-case02\`，内含 `assign.json`（R1/R2 → 版本的分配，含 salt）、`mapping.json`（模型代号对应表，含 salt）、`sources_full.tsv`（材料包文件 → 版本目录的完整对应）。只由 `scripts/contexts.py` 和 `scripts/run_round.py` 读写；揭盲（规程第 14 步）前不打开。承诺文件 `outputs/assign.sha256`、`outputs/mapping.sha256` 进 git（第二档）。
- 自测分配表：`runs/selftest_assign.json`（固定 `{"R1": "correct", "R2": "missing"}`，不封存，不进 git）。
- 运行目录：`runs/<YYYYmmdd-HHMMSS>-c2-<kind>-<ident>-<4 位随机十六进制>/`，`kind ∈ {ctx, query, acc, smoke}`；永不覆盖（`c2paths.new_run_dir`）。
- 正式三组：`queries/formal/<version>/`；自测三组：`queries/selftest/<version>/`（不进 git）。
- 库目录前缀登记：`rules/lib_normalize.txt` 第 2 行起。
