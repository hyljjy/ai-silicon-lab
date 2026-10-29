ACCEPTANCE OK

执行契约验收（规程 v0.3 第 6.4 节末条；预期值 rules/acceptance/expected.json，运行前写定）。

- acc_i_core: OK raw_lines=198 returned=198 truncated=False status=completed result=完成 attribution=- calls=262 elapsed=15s
- acc_ii_noflush: OK raw_lines=131 returned=131 truncated=False status=completed result=完成 attribution=- calls=261 elapsed=14s
- acc_iii_six: OK raw_lines=1564 returned=1564 truncated=False status=completed result=完成 attribution=- calls=5472 elapsed=287s
- acc_iv_fullreports: OK raw_lines=7635 returned=2001 truncated=True status=completed result=完成 attribution=流程限制：单实例截断 calls=261 elapsed=30s
- acc_v_timeout: OK raw_lines=7403 returned=2001 truncated=True status=completed result=超出预登记上限 attribution=流程限制：时限 calls=5550 elapsed=610s
- acc_vi_outlimit: OK raw_lines=133048 returned=656 truncated=True status=output_limit result=完成 attribution=流程限制：输出上限 calls=0 elapsed=51s
- acc_ctrl_correct: OK raw_lines=66 returned=66 truncated=False status=completed result=完成 attribution=- calls=2 elapsed=11s
- acc_vii_budget: OK
