# 验收运行目录的仓库外归档（外审 R6 S3：大文件不进 git，但要有固定归档位置与校验）

归档位置：`D:\study\eda_archive\case02cceptance\<run_dir>\`，是 `tasks/CASE-02/runs/<run_dir>/` 的整目录复制（2026-10-29 最终执行器下的那一轮）。每个样例目录的 `run.txt` 给出 `run_dir` 和未复制进 git 的大文件哈希。

| 样例 | run_dir | 归档内文件数 | calls.jsonl sha256（前 16 位） |
|---|---|---|---|
| acc_i_core | 20261029-050735-c2-query-acc_i_core-R2-8147 | 61 | 93dc9e4a591f60fe… |
| acc_ii_noflush | 20261029-050750-c2-query-acc_ii_noflush-R2-a377 | 61 | a0eca9095167548f… |
| acc_iii_six | 20261029-050805-c2-query-acc_iii_six-R2-a6d3 | 61 | 4bd7a222c7a19d30… |
| acc_iv_fullreports | 20261029-051252-c2-query-acc_iv_fullreports-R2-63e4 | 61 | c339031dace07dd5… |
| acc_v_timeout | 20261029-051323-c2-query-acc_v_timeout-R2-5820 | 61 | 0c79affc4696a217… |
| acc_vi_outlimit | 20261029-052338-c2-query-acc_vi_outlimit-R2-e179 | 61 | e3b0c44298fc1c14… |
| acc_ctrl_correct | 20261029-052430-c2-query-acc_ctrl_correct-R1-770e | 61 | fae7b50d745d9c21… |

归档目录的总清单：`D:\study\eda_archive\case02cceptance\SHA256SUMS`（427 行）；核对：`cd /d/study/eda_archive/case02/acceptance && sha256sum -c SHA256SUMS`。
