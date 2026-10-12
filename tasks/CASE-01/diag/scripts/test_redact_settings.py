"""Unit tests of redact_settings.py (synthetic settings only). Run: python -B -m unittest test_redact_settings"""
import contextlib
import io
import json
import os
import tempfile
import unittest

import redact_settings as rs


class TestRedact(unittest.TestCase):
    def test_secrets_hidden_other_values_kept(self):
        red, problems = rs.redact({"env": {"ANTHROPIC_BASE_URL": "https://x", "ANTHROPIC_AUTH_TOKEN": "sk-secret",
                                           "ANTHROPIC_MODEL": "m", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
                                           "API_TIMEOUT_MS": "600000", "MY_PRIVATE_THING": "v",
                                           "SOME_SETTING": "sk-another", "LONG": "a" * 40}})
        self.assertEqual(red["env"], {"ANTHROPIC_BASE_URL": "https://x", "ANTHROPIC_AUTH_TOKEN": rs.HIDDEN,
                                      "ANTHROPIC_MODEL": "m", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
                                      "API_TIMEOUT_MS": "600000", "MY_PRIVATE_THING": rs.HIDDEN,
                                      "SOME_SETTING": rs.HIDDEN, "LONG": rs.HIDDEN})
        self.assertEqual(problems, [])

    def test_risks(self):
        _, problems = rs.redact({"env": {"CLAUDE_CODE_MAX_OUTPUT_TOKENS": "64000", "DISABLE_AUTOUPDATER": "0",
                                         "MAX_THINKING_TOKENS": "1"}, "model": "opus", "hooks": {}}, "k3[1M]")
        self.assertEqual(len(problems), 5)
        self.assertTrue(any("top-level key 'model'" in p for p in problems))
        self.assertTrue(any("MAX_THINKING_TOKENS" in p for p in problems))

    def test_matching_model_and_schema_allowed(self):
        red, problems = rs.redact({"$schema": "s", "model": "k3[1M]", "env": {}}, "k3[1M]")
        self.assertEqual((red, problems), ({"$schema": "s", "model": "k3[1M]", "env": {}}, []))


class TestMain(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="redact_test_")
        self.addCleanup(self.tmp.cleanup)
        self.src, self.out = (os.path.join(self.tmp.name, d) for d in ("src", "out"))
        os.makedirs(self.src)
        for n in rs.NAMES:
            self.settings(n, {"env": {"ANTHROPIC_AUTH_TOKEN": "sk-secret-" + n}})

    def settings(self, name, data, encoding="utf-8"):
        with open(os.path.join(self.src, f"{name}.json"), "w", encoding=encoding) as f:
            json.dump(data, f)

    def test_byte_order_mark_accepted(self):
        self.settings("deepseek", {"env": {"ANTHROPIC_AUTH_TOKEN": "sk-x"}}, encoding="utf-8-sig")  # Notepad
        rc, out = self.main()
        self.assertEqual(rc, 0, out)

    def main(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = rs.main([self.src, self.out])
        return rc, buf.getvalue()

    def test_risk_writes_nothing_then_fixed_run_writes(self):
        self.settings("kimi", {"env": {"ANTHROPIC_AUTH_TOKEN": "sk-x", "MAX_THINKING_TOKENS": "8000"}})
        rc, out = self.main()
        self.assertEqual(rc, 1)
        self.assertIn("OVERRIDE RISK kimi: env key 'MAX_THINKING_TOKENS'", out)
        self.assertFalse(os.path.exists(self.out))
        self.settings("kimi", {"env": {"ANTHROPIC_AUTH_TOKEN": "sk-x"}})
        rc, out = self.main()
        self.assertEqual(rc, 0)
        self.assertEqual(sorted(os.listdir(self.out)), ["claude.json", "deepseek.json", "kimi.json",
                                                        "originals.sha256"])
        for n in os.listdir(self.out):
            with open(os.path.join(self.out, n), encoding="utf-8") as f:
                self.assertNotIn("sk-", f.read(), n)
        self.assertNotIn("sk-", out)


if __name__ == "__main__":
    unittest.main()
