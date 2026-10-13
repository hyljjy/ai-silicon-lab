"""Unit tests of extract_queries.py and rewrite_query.py. Run: python3 -B -m unittest test_extract_rewrite"""
import unittest

import extract_queries as eq
import rewrite_query as rw

CMDS = {"report_checks", "report_net", "get_pins", "set_load", "read_sdc", "report_units"}

ANSWER = """一、报告事实
- `report_checks` 在第三部分之前出现，不算
四、下一步查询
1. `report_checks -through [get_pins _11509_/Y] -scene ss_n40C_1v60`
2. report_net _11509_/Y
- 看一下扇出最大的那个线网
```tcl
report_units
report_checks -path_delay min
```
```bash
grep o21ai netlist.v
```
- `set_load 0.1 x` 与 `report_checks -format end` 两条
普通的一段说明文字，不是列表
### 五、可能的修改
- `report_checks` 在第五部分，不算
"""

REVIEW = """## 四、下一步查询
```bash
report_checks -through [get_pins _11509_/Y]
```
```shell
report_net _11509_/Y
```
```python
print("x")
```
1. `report_timing -max_paths 5 -nworst 2`
2. **确认扇出**：report_net _11509_/Y
3. 步骤 3: report_units
- set the load to 0.1 and rerun
```bash
# 先看网表
grep o21ai netlist.v
```
```bash
set pe [lindex [find_timing_paths -path_delay max] 0]
puts [get_property $pe slack]
```
## 五、可能的修改
"""


class TestExtract(unittest.TestCase):
    def test_units(self):
        units = eq.extract(ANSWER, CMDS)
        self.assertEqual([k for k, _, _ in units], ["inline", "line", "text", "codeblock", "nontcl", "inline"])
        self.assertEqual(units[0][2], "report_checks -through [get_pins _11509_/Y] -scene ss_n40C_1v60")
        self.assertEqual(units[1][2], "report_net _11509_/Y")
        self.assertEqual(units[3][2], "report_units\nreport_checks -path_delay min")
        self.assertEqual(units[3][1], 7)
        # several command spans in one list item are one query, in order (set_load must act on the report)
        self.assertEqual(units[5][2], "set_load 0.1 x\nreport_checks -format end")

    def test_real_command_set_and_review_cases(self):
        # review DP2 R2: language tags, other tools' timing commands and labels must not hide a written command
        units = eq.extract(REVIEW, eq.commands())
        self.assertEqual([k for k, _, _ in units],
                         ["codeblock", "codeblock", "nontcl", "inline", "line", "line", "text", "nontcl", "codeblock"])
        self.assertEqual([u[2] for u in units[3:6]], ["report_timing -max_paths 5 -nworst 2",
                                                      "report_net _11509_/Y", "report_units"])
        self.assertEqual(units[8][2], "set pe [lindex [find_timing_paths -path_delay max] 0]\nputs [get_property $pe slack]")

    def test_missing_part4(self):
        with self.assertRaises(ValueError):
            eq.extract("一、报告事实\n- x\n", CMDS)

    def test_heading_variants(self):
        for h in ("四. 下一步查询", "## 四、下一步查询", "**四．下一步查询**"):
            self.assertEqual(len(eq.extract(h + "\n- `report_units`\n五、修改\n", CMDS)), 1, h)


class TestRewrite(unittest.TestCase):
    def test_r2(self):
        out = "CASE01-ERROR: Error 514: diag_query.tcl line 1, '-corners' is not a known keyword or flag.\n"
        new, applied = rw.rewrite("report_checks -corners ss_n40C_1v60 -format end\n", out)
        self.assertEqual((new, applied), ("report_checks -scenes ss_n40C_1v60 -format end\n", ["R2"]))

    def test_r3(self):
        out = 'CASE01-ERROR: invalid command name "report_timing"\n'
        new, applied = rw.rewrite("report_timing -max_paths 5 -nworst 2 -delay_type max\n", out)
        self.assertEqual(new, "report_checks -group_path_count 5 -endpoint_path_count 2 -path_delay max\n")
        self.assertEqual(applied, ["R3"])

    def test_no_trigger_no_rewrite(self):
        self.assertEqual(rw.rewrite("report_timing -max_paths 5\n", "some other error\n"),
                         ("report_timing -max_paths 5\n", []))


if __name__ == "__main__":
    unittest.main()
