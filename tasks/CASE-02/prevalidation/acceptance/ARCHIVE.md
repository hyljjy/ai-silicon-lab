# 验收运行目录的仓库外归档（外审 R6 S3：大文件不进 git，但要有固定归档位置与校验）

归档位置：`D:\study\eda_archive\case02cceptance\<run_dir>\`，是 `tasks/CASE-02/runs/<run_dir>/` 的整目录复制。下表是**当前 RESULT.md 引用的那一轮**（2026-10-29 规程补记 3 之后的契约）；早先各轮的目录仍在归档里，`SHA256SUMS` 覆盖全部。每个样例目录的 `run.txt` 给出 `run_dir` 和未复制进 git 的大文件哈希。

| 样例 | run_dir | 归档内文件数 | calls.jsonl sha256（前 16 位） |
|---|---|---|---|
| acc_i_core | 20261029-071610-c2-query-acc_i_core-R2-d04f | 61 | 13fa7f678e72c070… |
| acc_ii_noflush | 20261029-071632-c2-query-acc_ii_noflush-R2-aca7 | 61 | 9532d3a82400e23d… |
| acc_iii_six | 20261029-071653-c2-query-acc_iii_six-R2-e810 | 61 | 2da50de8b7ce973d… |
| acc_iv_fullreports | 20261029-072303-c2-query-acc_iv_fullreports-R2-6dd6 | 61 | 23a26fc7d3e327da… |
| acc_v_timeout | 20261029-082307-c2-query-acc_v_timeout-R2-ad44 | 61 | 1edccb9ee94948c1… |
| acc_vi_outlimit | 20261029-081932-c2-query-acc_vi_outlimit-R2-1153 | 61 | e3b0c44298fc1c14… |
| acc_ctrl_correct | 20261029-082117-c2-query-acc_ctrl_correct-R1-0631 | 61 | 0a554692afeb72c4… |

归档目录的总清单：`D:\study\eda_archive\case02cceptance\SHA256SUMS`（854 行）；核对：`cd /d/study/eda_archive/case02/acceptance && sha256sum -c SHA256SUMS`。

注：样例 (v) 在 2026-10-29 08:23 单独重跑（`runs/20261029-082307-…`），因为 07:23 那次运行期间电脑睡眠、WSL 被冻结（SYS-010），那次的目录也在归档里但不被引用。
