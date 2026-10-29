"""Unit tests of label_check.py (protocol v0.3 section 6.2; R5 M4). Windows or WSL Python, from tasks/CASE-02/scripts:
  python -B -m unittest -v test_label_check"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "scripts")
              if os.path.basename(os.path.dirname(HERE)) == "impl" else HERE)
import label_check as lc  # noqa: E402

WARNING = "Warning: There are 64 input ports missing set_input_delay.\n"
ANSWER = "二、结论\n我认为 R2 的 in_b 缺失了 input delay（missing constraints），这是假设。\n"


class TestScan(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="label_")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def write(self, rel, text):
        p = os.path.join(self.tmp, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        return p

    def test_tool_warning_text_allowed(self):
        p = self.write("round2/A_results.md", "### 查询 A1（R1）\n输出：\n```text\n" + WARNING + "```\n")
        self.assertEqual(lc.scan_operator_files([p]), [])

    def test_model_prose_allowed(self):
        p = self.write("prompts/round2/A.md", "题目\n<<<第 1 轮回答开始>>>\n" + ANSWER + "<<<第 1 轮回答结束>>>\n=== CASE02 QUERY BEGIN ===\n"
                       + WARNING + "\n")
        self.assertEqual(lc.scan_operator_files([p]), [])

    def test_operator_path_with_version_rejected(self):
        p = self.write("package/summary_missing.tsv", "WS\tx\n")
        found = lc.scan_operator_files([p])
        self.assertTrue(found and "missing" in found[0])

    def test_operator_title_or_metadata_rejected(self):
        p = self.write("package/SOURCES.tsv", "# package file\tsource\nsummary_R1.tsv\tqueries/formal/correct/sta_results.tsv\n")
        self.assertTrue(lc.scan_operator_files([p]))
        q = self.write("prompts/round2/B.md", "### 查询 B1（restored）\n")
        self.assertTrue(lc.scan_operator_files([q]))

    def test_case_insensitive_and_word_boundary(self):
        p = self.write("package/context.md", "## MISSING data\n")
        self.assertTrue(lc.scan_operator_files([p]))
        q = self.write("package/context.md", "## set_wire_load_min_block_size 不在表里\n")
        self.assertEqual(lc.scan_operator_files([q]), [])

    def test_bytes_api_for_prompt(self):
        self.assertEqual(lc.scan_prompt_bytes(("题目\n<<<第 1 轮回答开始>>>\n" + ANSWER + "<<<第 1 轮回答结束>>>\n").encode("utf-8"),
                                              "prompts/round2/A.md"), [])
        self.assertTrue(lc.scan_prompt_bytes("### 查询 A1（correct）\n".encode("utf-8"), "prompts/round2/A.md"))


if __name__ == "__main__":
    unittest.main()
