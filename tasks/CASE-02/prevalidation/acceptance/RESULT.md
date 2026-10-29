ACCEPTANCE FAIL

执行契约验收（规程 v0.3 第 6.4 节末条；预期值 rules/acceptance/expected.json，运行前写定）。

- acc_i_core: OK raw_lines=198 returned=198 truncated=False status=completed result=完成 attribution=- calls=262 elapsed=16s
- acc_ii_noflush: OK raw_lines=131 returned=131 truncated=False status=completed result=完成 attribution=- calls=261 elapsed=15s
- acc_iii_six: OK raw_lines=1564 returned=1564 truncated=False status=completed result=完成 attribution=- calls=5472 elapsed=308s
- acc_iv_fullreports: OK raw_lines=7635 returned=2001 truncated=True status=completed result=完成 attribution=流程限制：单实例截断 calls=261 elapsed=35s
- acc_v_timeout: FAIL raw_lines=33 returned=33 truncated=False status=completed result=完成 attribution=- calls=4 elapsed=14s
  - exec_result: expected '超出预登记上限', got '完成'
  - attribution: expected '流程限制：时限', got '-'
  - abnormal: expected '超时', got '-'
  - return lacks 'time limit exceeded'
- acc_vi_outlimit: OK raw_lines=134160 returned=656 truncated=True status=output_limit result=完成 attribution=流程限制：输出上限 calls=0 elapsed=57s
- acc_ctrl_correct: OK raw_lines=66 returned=66 truncated=False status=completed result=完成 attribution=- calls=2 elapsed=12s
- acc_vii_budget: OK
