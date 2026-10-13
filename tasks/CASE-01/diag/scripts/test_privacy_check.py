"""Unit tests of privacy_check.py. Run: python3 -B -m unittest test_privacy_check
Sample paths are assembled at run time so that this file itself passes the privacy check."""
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import privacy_check as pc

EMAIL = "someone.test@example.org"
U = "Users"
HERE = os.path.dirname(os.path.abspath(__file__))
BS = "\\"


class TestPrivacy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="privacy_test_")
        self.addCleanup(self.tmp.cleanup)
        os.environ["CASE01_PRIVACY_EMAIL"] = EMAIL
        self.addCleanup(os.environ.pop, "CASE01_PRIVACY_EMAIL", None)

    def file(self, text, name="f.md"):
        p = os.path.join(self.tmp.name, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p

    def kinds(self, text):
        return [k for _, k in pc.scan(self.file(text), EMAIL)]

    def test_email_any_case(self):
        self.assertEqual(self.kinds("contact: Someone.Test@Example.org\n"), ["账号邮箱"])

    def test_user_dir_spellings(self):
        samples = ["C:" + BS + U + BS + "alice" + BS + "x",
                   "c:/" + U + "/alice/x",
                   '"C:' + BS * 2 + U + BS * 2 + "alice" + BS * 2 + 'x"',
                   "/c/" + U + "/alice/x",
                   "/mnt/c/" + U + "/alice/x",
                   "D:" + BS + U.lower() + BS + "bob"]
        for s in samples:
            self.assertEqual(self.kinds(s + "\n"), ["用户目录路径"], s)

    def test_allowed_paths(self):
        for s in ("/home/eda/pdk/sky130A/libs.ref", "%USERPROFILE%" + BS + ".diag-models" + BS + "kimi.json",
                  "D:" + BS + "study" + BS + "diag_sandbox" + BS + "sealed", "/mnt/d/study/ai_native_design",
                  U + " guide"):
            self.assertEqual(self.kinds(s + "\n"), [], s)

    def test_nul_bytes_fail_and_utf16_is_decoded(self):
        self.assertEqual(pc.scan_bytes(b"\0" + EMAIL.encode(), EMAIL), [(0, "含 NUL 字节，无法检查")])
        self.assertEqual(pc.scan_bytes(("x\n" + EMAIL + "\n").encode("utf-16"), EMAIL), [(2, "账号邮箱")])

    def test_main_reports_location_not_value(self):
        self.file("ok\nmail " + EMAIL + "\n", "a.md")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = pc.main([self.tmp.name])
        self.assertEqual(rc, 1)
        self.assertIn("a.md:2 账号邮箱", buf.getvalue())
        self.assertNotIn(EMAIL, buf.getvalue())

    def test_main_clean(self):
        self.file("nothing here\n")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(pc.main([self.tmp.name]), 0)


class TestStaged(unittest.TestCase):
    """--staged scans what would be committed, plus the message; run as a child process without PYTHONIOENCODING."""

    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="privacy_staged_")
        self.addCleanup(shutil.rmtree, self.repo, True)
        for a in (["init", "-q"], ["config", "user.email", "t@example.org"], ["config", "user.name", "t"]):
            self.git(*a)

    def git(self, *a):
        subprocess.run(["git", "-C", self.repo] + list(a), capture_output=True, check=True)

    def write(self, name, text):
        with open(os.path.join(self.repo, name), "w", encoding="utf-8") as f:
            f.write(text)

    def check(self, *args):
        env = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
        env["CASE01_PRIVACY_EMAIL"] = EMAIL
        p = subprocess.run([sys.executable, "-B", os.path.join(HERE, "privacy_check.py"), "--staged"] + list(args),
                           cwd=self.repo, env=env, capture_output=True)
        return p.returncode, p.stdout.decode("utf-8")

    def test_staged_blob_not_working_tree(self):
        self.write("a.md", "mail " + EMAIL + "\n")
        self.git("add", "a.md")
        self.write("a.md", "clean now, but the staged copy is not\n")
        rc, out = self.check()
        self.assertEqual(rc, 1)
        self.assertIn("PRIVACY HIT a.md:1 账号邮箱", out)

    def test_message_and_clean(self):
        self.write("a.md", "clean\n")
        self.git("add", "a.md")
        self.assertEqual(self.check()[0], 0)
        rc, out = self.check("--message", "note " + EMAIL)
        self.assertEqual(rc, 1)
        self.assertIn("<commit message>:1 账号邮箱", out)
        self.assertNotIn(EMAIL, out)


if __name__ == "__main__":
    unittest.main()
