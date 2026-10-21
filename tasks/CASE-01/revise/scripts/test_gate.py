"""Tests for gate (contract gate G1-G8; CASE-01 stage B Task 4; protocol v0.5 sections 6.3 part 3, 7.2; revisions
RV-01: two-stage Yosys read). WSL only (Yosys 0.69+187 of the WSL distro; run per module, never with discover).
Every Yosys run writes under a temporary directory in tasks/CASE-01/runs/ (never /tmp). Fixtures:
fixtures/gate/legal_*.v must pass; fixtures/gate/neg_*.v carry the expected hits below."""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

import limits
import revpaths as rp

if os.name != "nt":
    import feedback
    import gate
    import round as rnd_mod

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures", "gate")
RUNS = os.path.join(rp.CASE, "runs")
BASELINE = os.path.join(rp.CASE, "rtl", "dot4sat.v")
GATE_PY = os.path.join(HERE, "gate.py")
GATE_RULES = os.path.join(rp.RULES, "gate_rules.md")
PROTOCOL = os.path.join(rp.REVISE, "protocol.md")
C, X = "contract", "extra"

LEGAL = ("legal_ansi", "legal_nonansi", "legal_localparam_width", "legal_inverted_valid", "legal_escaped_keyword",
         "legal_attr_keep", "legal_signed", "legal_comments_strings", "legal_always_star", "legal_escaped_clk",
         "legal_escaped_module_name", "legal_translate_mention", "legal_wire_clk")

# expected {(rule, line, kind)} of every negative fixture; YOSYS: the two-stage read must fail (yosys_problem set)
NEG = {
    "neg_missing_port": ({("G1", 2, C)}, False),
    "neg_extra_port": ({("G1", 7, C)}, False),
    "neg_width": ({("G1", 9, C)}, False),
    "neg_direction": ({("G1", 5, C)}, False),
    "neg_module_name": ({("G1", 2, C)}, False),
    "neg_localparam_width_wrong": ({("G1", 8, C)}, False),
    "neg_localparam_unevaluable": ({("unrecognized", 6, X)}, True),
    "neg_parameter": ({("G4", 3, X)}, False),
    "neg_timescale": ({("G5", 2, X)}, False),
    "neg_define": ({("G5", 2, X), ("G5", 7, X)}, False),
    "neg_include": ({("G2", 2, C), ("G5", 2, X), ("unrecognized", 0, X)}, True),
    "neg_fopen": ({("G2", 9, C), ("unrecognized", 9, X)}, True),
    "neg_value_plusargs": ({("G2", 9, C), ("unrecognized", 9, X)}, True),
    "neg_two_modules_unused": ({("G3", 14, X)}, False),
    "neg_empty_second_module": ({("G3", 14, X)}, False),
    "neg_second_module_first": ({("G3", 6, X)}, False),
    "neg_duplicate_module": ({("G3", 14, X), ("unrecognized", 14, X)}, True),
    "neg_escaped_second_module": ({("G3", 14, X)}, False),
    "neg_negedge": ({("G6", 7, X), ("G7", 7, X)}, False),
    "neg_initial": ({("G6", 7, X)}, False),
    "neg_delay": ({("G6", 8, X)}, False),
    "neg_async_reset": ({("G6", 7, X)}, False),
    "neg_clk_data": ({("G7", 7, X)}, False),
    "neg_clk_cond": ({("G7", 9, X)}, False),
    "neg_escaped_clk_data": ({("G7", 9, X)}, False),
    "neg_unknown_char": ({("unrecognized", 9, X)}, True),
    "neg_syntax_error": ({("unrecognized", 9, X)}, True),
    "neg_synopsys_full_case": ({("unrecognized", 13, X)}, True),
    # RV-06: the tokenizer flags the translate comments itself; Yosys of this version also fails stage 1 here
    "neg_translate_off_port": ({("unrecognized", 2, X), ("unrecognized", 7, X), ("unrecognized", 9, X)}, True),
    "neg_translate_off_block": ({("unrecognized", 1, X), ("unrecognized", 8, X), ("unrecognized", 10, X)}, True),
    "neg_wire_clk_assign": ({("G7", 7, X)}, False),
}


def fx(name):
    return os.path.join(FIX, name + ".v")


def triples(res):
    return {(h.rule, h.line, h.kind) for h in res.hits}


def lines_of(path):
    with open(path, "rb") as f:
        return f.read().decode("utf-8").split("\n")


def limited(rc=0, timed_out=False, stdout_over=False, stderr_over=False, stderr=b"", alive=(), unconfirmed=False,
            output_error=None):
    return limits.Limited(rc=rc, timed_out=timed_out, stdout_over=stdout_over, stderr_over=stderr_over, stdout=b"",
                          stderr=stderr, stdout_bytes=0, stderr_bytes=len(stderr), killed_pids_alive=list(alive),
                          cleanup_unconfirmed=unconfirmed, output_error=output_error)


@unittest.skipIf(os.name == "nt", "test_gate runs only in WSL")
class GateTest(unittest.TestCase):
    def setUp(self):
        os.makedirs(RUNS, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="gate_", dir=RUNS, ignore_cleanup_errors=True)
        self.work = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def run_gate(self, path, L=1):
        return gate.gate(path, L, work_dir=self.work)

    # ---------------------------------------------------------------- protocol 6.3 part 3 (gate) and RV-01
    def test_baseline_passes(self):
        res = self.run_gate(BASELINE)
        self.assertEqual(res.hits, [])
        self.assertIsNone(res.yosys_problem)
        self.assertTrue(res.passed)

    def test_legal_variants_pass(self):
        for name in LEGAL:
            with self.subTest(name=name):
                res = self.run_gate(fx(name))
                self.assertEqual(triples(res), set())
                self.assertIsNone(res.yosys_problem)
                self.assertTrue(res.passed)

    def check_neg(self, name):
        want, yosys_fails = NEG[name]
        res = self.run_gate(fx(name))
        self.assertFalse(res.passed)
        self.assertEqual(triples(res), want)
        if yosys_fails:
            self.assertIsInstance(res.yosys_problem, str)
            self.assertTrue(res.yosys_problem)
        else:
            self.assertIsNone(res.yosys_problem)
        return res

    def test_neg_missing_port(self):
        self.check_neg("neg_missing_port")

    def test_neg_extra_port(self):
        self.check_neg("neg_extra_port")

    def test_neg_width_line(self):
        self.check_neg("neg_width")

    def test_neg_direction(self):
        self.check_neg("neg_direction")

    def test_neg_module_name(self):
        self.check_neg("neg_module_name")

    def test_neg_localparam_width_wrong(self):
        self.check_neg("neg_localparam_width_wrong")

    def test_neg_localparam_unevaluable_is_unrecognized(self):
        res = self.check_neg("neg_localparam_unevaluable")
        self.assertIn("stage 1", res.yosys_problem)

    def test_neg_parameter_still_g4(self):
        self.check_neg("neg_parameter")

    def test_neg_timescale(self):
        self.check_neg("neg_timescale")

    def test_neg_define(self):
        self.check_neg("neg_define")

    def test_neg_include(self):
        self.check_neg("neg_include")

    def test_neg_fopen(self):
        self.check_neg("neg_fopen")

    def test_neg_value_plusargs(self):
        self.check_neg("neg_value_plusargs")

    def test_neg_two_modules_unused(self):
        self.check_neg("neg_two_modules_unused")

    def test_neg_empty_second_module(self):
        self.check_neg("neg_empty_second_module")

    def test_neg_second_module_first(self):
        self.check_neg("neg_second_module_first")

    def test_neg_duplicate_module_keeps_g3(self):
        self.check_neg("neg_duplicate_module")

    def test_neg_escaped_second_module(self):
        self.check_neg("neg_escaped_second_module")

    def test_neg_negedge(self):
        self.check_neg("neg_negedge")

    def test_neg_initial(self):
        self.check_neg("neg_initial")

    def test_neg_delay(self):
        self.check_neg("neg_delay")

    def test_neg_async_reset(self):
        self.check_neg("neg_async_reset")

    def test_neg_clk_data(self):
        self.check_neg("neg_clk_data")

    def test_neg_clk_cond(self):
        self.check_neg("neg_clk_cond")

    def test_neg_escaped_clk_data(self):
        self.check_neg("neg_escaped_clk_data")

    def test_neg_syntax_error(self):
        res = self.check_neg("neg_syntax_error")
        self.assertIn("stage 1", res.yosys_problem)

    def test_neg_synopsys_full_case_is_unrecognized(self):
        res = self.check_neg("neg_synopsys_full_case")       # Yosys parses the comment; pinned (fix round 1)
        self.assertIn("TOK_SYNOPSYS_FULL_CASE", res.yosys_problem)

    def test_neg_translate_off_port_never_passes(self):
        res = self.check_neg("neg_translate_off_port")       # the reviewer's probe (RV-06)
        self.assertIn(("unrecognized", 7, X), triples(res))
        self.assertEqual(res.hits[1].text, "    // synopsys translate_off")

    def test_neg_translate_off_block(self):
        self.check_neg("neg_translate_off_block")

    def test_neg_wire_clk_assign(self):
        self.check_neg("neg_wire_clk_assign")

    def test_translate_comment_rule(self):
        flagged = ["// synopsys translate_off", "//synthesis translate_on", "//   Synopsys \t TRANSLATE_OFF  rest",
                   "/* synthesis translate_off */", "/*\n  synopsys translate_on */", "// SYNTHESIS translate_on;"]
        ordinary = ["// no synopsys translate_off here", "// synopsys full_case", "// synopsys parallel_case",
                    "/* synthesis keep */", "// synopsys_translate_off", "// synopsys translate_offx",
                    "// translate_off", "// pragma translate_off"]
        for c in flagged:
            with self.subTest(flagged=c):
                toks = gate.tokenize(f"module m;\nwire a; {c}\nendmodule")
                self.assertEqual([t.kind for t in toks if t.kind == "translate"], ["translate"])
                self.assertEqual([(h.rule, h.line, h.kind) for h in gate.token_rules(toks)],
                                 [("unrecognized", 2, X)])
                self.assertNotIn("translate_off", [t.text for t in toks if t.kind != "translate"])
        for c in ordinary:
            with self.subTest(ordinary=c):
                toks = gate.tokenize(f"module m;\nwire a; {c}\nendmodule")
                self.assertFalse(any(t.kind == "translate" for t in toks))
                self.assertEqual(gate.token_rules(toks), [])

    def test_every_negative_fixture_has_a_test(self):
        names = {f[:-2] for f in os.listdir(FIX) if f.startswith("neg_") and f.endswith(".v")}
        self.assertEqual(names - {"neg_body_undeclared"}, set(NEG))
        self.assertEqual({f[:-2] for f in os.listdir(FIX) if f.startswith("legal_")}, set(LEGAL))

    def test_systask_names_keep_dollar_and_compare_without(self):
        toks = gate.tokenize("x = $fopen(f); y = $value$plusargs(s, k); z = $signed(a); w = $fopenx(q);")
        sys_t = [t.text for t in toks if t.kind == "systask"]
        self.assertEqual(sys_t, ["$fopen", "$value$plusargs", "$signed", "$fopenx"])
        lint = gate.lint_systf()
        self.assertIn("fopen", lint)
        self.assertIn("value$plusargs", lint)
        self.assertNotIn("$fopen", lint)
        hits = gate.token_rules(gate.tokenize("module m; initial; endmodule\n$fopen $value$plusargs $signed $fopenx"))
        self.assertEqual([(h.rule, h.line, h.kind) for h in hits if h.rule == "G2"], [("G2", 2, C)])
        self.assertEqual(sum(1 for h in hits if h.rule == "G2"), 1)       # deduplicated per (rule, line, kind)

    def test_escaped_keyword_is_identifier(self):
        toks = gate.tokenize("\\begin  \\module \\parameter\tx")
        self.assertEqual([(t.kind, t.text) for t in toks],
                         [("esc_ident", "begin"), ("esc_ident", "module"), ("esc_ident", "parameter"),
                          ("ident", "x")])
        hits = gate.token_rules(gate.tokenize("module dot4sat; wire \\parameter  = 1'b0; wire \\module ; endmodule"))
        self.assertEqual(hits, [])
        self.assertTrue(self.run_gate(fx("legal_escaped_keyword")).passed)

    def test_attribute_not_misread(self):
        toks = gate.tokenize("(* keep, parameter = \"clk\" *) wire x;\nalways @(*) a = b;\nalways @( * ) c = d;")
        self.assertEqual(toks[0].kind, "attr")
        self.assertEqual(toks[0].line, 1)
        ops = [t.text for t in toks if t.line == 2 and t.kind == "op"]
        self.assertEqual(ops[:4], ["@", "(", "*", ")"])
        self.assertFalse(any(t.kind == "attr" for t in toks[1:]))
        src = "module dot4sat;\n(* parameter *) wire x;\n(* clk *) reg y;\nalways @(*) y = x;\nendmodule\n"
        self.assertEqual(gate.token_rules(gate.tokenize(src)), [])
        self.assertTrue(self.run_gate(fx("legal_attr_keep")).passed)

    def test_unrecognized_is_reported_not_proven(self):
        res = self.run_gate(fx("neg_unknown_char"))
        self.assertFalse(res.passed)
        self.assertEqual({h.rule for h in res.hits}, {"unrecognized"})
        self.assertTrue(all(h.kind == X for h in res.hits))
        toks = gate.tokenize("a § b")
        self.assertEqual([t.kind for t in toks], ["ident", "unknown", "ident"])
        hits = gate.token_rules(gate.tokenize("module m;\n wire x = a \u00a7 b;\nendmodule"))
        self.assertEqual([(h.rule, h.line, h.kind) for h in hits], [("unrecognized", 2, X)])

    def test_declared_L_out_of_range(self):
        for L in (0, 4, -1, True, "2", None):
            with self.subTest(L=L):
                res = self.run_gate(BASELINE, L)
                self.assertFalse(res.passed)
                self.assertEqual(triples(res), {("G8", 0, X)})
                self.assertIsNone(res.hits[0].text)
        for L in (1, 2, 3):
            with self.subTest(L=L):
                self.assertTrue(self.run_gate(BASELINE, L).passed)

    # ---------------------------------------------------------------- tokenizer details
    def test_tokenizer_drops_comments_and_strings(self):
        src = ('a // parameter `define clk\nb /* parameter\n `x clk */ c "str \\" parameter clk" d\n'
               '/* synopsys full_case */ e')
        toks = gate.tokenize(src)
        self.assertEqual([(t.kind, t.text, t.line) for t in toks],
                         [("ident", "a", 1), ("ident", "b", 2), ("ident", "c", 3), ("ident", "d", 3),
                          ("ident", "e", 4)])

    def test_tokenizer_numbers_directives_delay(self):
        toks = gate.tokenize("34'sd2147483647 32'h7FFF_FFFF 'b0 4 'b1 12 1.5 `timescale #3 x$y")
        self.assertEqual([(t.kind, t.text) for t in toks],
                         [("number", "34'sd2147483647"), ("number", "32'h7FFF_FFFF"), ("number", "'b0"),
                          ("number", "4"), ("number", "'b1"), ("number", "12"), ("number", "1.5"),
                          ("directive", "`timescale"), ("delay", "#"), ("number", "3"), ("ident", "x$y")])

    def test_tokenizer_unterminated_is_unknown(self):
        for src in ("a /* never closed", "a \"never closed\nb", "(* never closed", "a ` b", "a $ b", "a ' b", "\\"):
            with self.subTest(src=src):
                self.assertIn("unknown", [t.kind for t in gate.tokenize(src)])

    def test_tokenizer_line_is_first_character(self):
        toks = gate.tokenize("\n\n(* a\n b *)\nx")
        self.assertEqual([(t.kind, t.line) for t in toks], [("attr", 3), ("ident", 5)])

    def test_g6_forms(self):
        ok = ["always @(posedge clk) a <= b;", "always @* a = b;", "always @(*) a = b;", "always @( * ) a = b;",
              "always @ ( posedge clk ) a <= b;", "always @(posedge \\clk ) a <= b;"]
        bad = ["always @(posedge clk or posedge rst) a <= b;", "always begin a = b; end", "always @(a or b) c = a;",
               "always @(posedge rst) a <= b;", "always @(posedge clk) begin @(posedge clk) a <= b; end",
               "initial a = 0;", "assign #2 a = b;", "always @(negedge rst) a <= b;"]
        for body in ok:
            with self.subTest(ok=body):
                hits = gate.token_rules(gate.tokenize(f"module m (clk);\ninput clk;\n{body}\nendmodule"))
                self.assertEqual(hits, [])
        for body in bad:
            with self.subTest(bad=body):
                hits = gate.token_rules(gate.tokenize(f"module m (clk);\ninput clk;\n{body}\nendmodule"))
                self.assertIn(("G6", 3, X), [(h.rule, h.line, h.kind) for h in hits])

    def test_g7_positions(self):
        ok = ["module m (clk, a);\ninput clk;", "module m (input wire clk, input a);",
              "module m (a, clk);\ninput wire a, clk;", "module m (\\clk , a);\ninput [0:0] \\clk ;",
              "module m (clk);\ninput clk;\nwire clk;",                          # RV-07
              "module m (clk);\ninput clk;\nwire /* c */ clk // c\n ;", "module m (clk);\nwire clk;\ninput clk;",
              "module m (clk);\ninput clk;\nwire \\clk ;"]
        bad = [("module m (clk);\ninput clk;\noutput reg x = clk;", 3), ("module m (clk);\ninput clk;\nwire y = clk;", 3),
               ("module m (clk);\ninput clk;\nwire clk = 1'b0;", 3), ("module m (clk);\ninput clk;\nwire [0:0] clk;", 3),
               ("module m (clk);\ninput clk;\nwire clk, x;", 3), ("module m (a);\ninput a;\nwire clk;", 3),
               ("module m (clk);\ninput clk;\nreg clk;", 3), ("module m (clk);\ninput clk;\nassign y = f(wire clk;);", 3),
               ("module m (clk);\ninput clk;\nassign y = \\clk ;", 3), ("module m (clk);\ninput clk;\nwire clk2 = clk;", 3),
               ("module m (input [clk:0] a);", 1), ("module m (clk);\ninput clk;\nalways @(negedge clk) a <= b;", 3)]
        for src in ok:
            with self.subTest(ok=src):
                hits = gate.token_rules(gate.tokenize(src + "\nendmodule"))
                self.assertEqual([h for h in hits if h.rule == "G7"], [])
        for src, line in bad:
            with self.subTest(bad=src):
                hits = gate.token_rules(gate.tokenize(src + "\nendmodule"))
                self.assertIn(("G7", line, X), [(h.rule, h.line, h.kind) for h in hits])

    def test_g3_zero_modules(self):
        hits = gate.token_rules(gate.tokenize("wire x;"))
        self.assertEqual([(h.rule, h.line, h.kind) for h in hits], [("G3", 0, X)])

    # ---------------------------------------------------------------- RV-01: the two-stage read
    def test_two_stage_commands_fresh_processes_no_synthesis_passes(self):
        calls = []
        real = limits.run_limited

        def spy(argv, kind, **kw):
            calls.append((list(argv), kind, kw.get("cwd")))
            return real(argv, kind, **kw)

        with mock.patch.object(gate.limits, "run_limited", side_effect=spy):
            res = self.run_gate(BASELINE)
        self.assertTrue(res.passed)
        self.assertEqual(len(calls), 2)
        (a1, k1, cwd1), (a2, k2, cwd2) = calls
        self.assertEqual((k1, k2), ("yosys", "yosys"))
        self.assertEqual(a1, ["yosys", "-q", "-p", "read_verilog dot4sat.v"])
        self.assertEqual(a2[:3], ["yosys", "-q", "-p"])
        self.assertRegex(a2[3], r"^read_verilog -lib dot4sat\.v; write_json \S+\.json$")
        self.assertEqual(cwd1, os.path.dirname(BASELINE))
        for word in ("proc", "hierarchy", "synth", "flatten", "opt", "clean", "prep"):
            self.assertNotRegex(a1[3] + a2[3], rf"\b{word}\b")
        self.assertEqual([s["rc"] for s in (res.evidence["stage1"], res.evidence["stage2"])], [0, 0])

    def test_stage1_failure_skips_stage2(self):
        calls = []
        real = limits.run_limited
        with mock.patch.object(gate.limits, "run_limited",
                               side_effect=lambda a, k, **kw: calls.append(a) or real(a, k, **kw)):
            res = self.run_gate(fx("neg_syntax_error"))
        self.assertEqual(len(calls), 1)
        self.assertNotIn("stage2", res.evidence)
        self.assertIn("syntax error", res.yosys_problem)

    def fake_stages(self, stage1, stage2, json_text=None):
        """run_limited stand-in: stage1 / stage2 are Limited results or exceptions; stage 2 writes json_text to the
        write_json path when given."""
        def fake(argv, kind, **kw):
            cmd = argv[3]
            if "-lib" not in cmd:
                if isinstance(stage1, BaseException):
                    raise stage1
                return stage1
            if json_text is not None:
                with open(cmd.split("write_json ", 1)[1], "w", encoding="utf-8") as f:
                    f.write(json_text)
            if isinstance(stage2, BaseException):
                raise stage2
            return stage2
        return fake

    def good_json(self):
        return json.dumps({"modules": {"dot4sat": {"ports": {
            p: {"direction": d, "bits": list(range(w))} for p, d, w in gate.EXPECTED_PORTS}}}})

    def test_yosys_read_failures_are_unrecognized(self):
        # RV-01 item 4: non-zero exit, timeout, output over the limit or incomplete -> unrecognized in the result
        bad_cases = {
            "rc": limited(rc=1, stderr=b"x.v:3: ERROR: boom\n"),
            "timeout": limited(rc=-9, timed_out=True),
            "stdout over": limited(stdout_over=True),
            "stderr over": limited(stderr_over=True),
            "output error": limited(output_error="disk"),
        }
        for stage in (1, 2):
            for what, bad in bad_cases.items():
                with self.subTest(stage=stage, what=what):
                    s1, s2 = (bad, limited()) if stage == 1 else (limited(), bad)
                    with mock.patch.object(gate.limits, "run_limited",
                                           side_effect=self.fake_stages(s1, s2, self.good_json())):
                        res = self.run_gate(BASELINE)
                    self.assertFalse(res.passed)
                    self.assertIn(f"stage {stage}", res.yosys_problem)
                    self.assertEqual({h.rule for h in res.hits}, {"unrecognized"})

    def test_infrastructure_faults_raise_never_a_result(self):
        # fix round 1: KILL FAIL, start and supervision failures raise GateInfraError (never a gate.json)
        cases = {
            "kill fail alive": (limited(rc=-9, alive=[1234]), True),
            "kill fail unconfirmed": (limited(rc=-9, unconfirmed=True), True),
            "kill fail with timeout": (limited(rc=-9, timed_out=True, alive=[55]), True),
            "supervision": (limits.SupervisionError("boom", killed_pids_alive=[], cleanup_unconfirmed=False), False),
            "supervision kill fail": (limits.SupervisionError("boom", pid=9, killed_pids_alive=[7],
                                                              cleanup_unconfirmed=True), True),
            "isolation": (limits.IsolationFail("ISOLATION FAIL: x"), False),
            "oserror": (FileNotFoundError(2, "No such file", "yosys"), False),
        }
        for stage in (1, 2):
            for what, (bad, kill) in cases.items():
                with self.subTest(stage=stage, what=what):
                    s1, s2 = (bad, limited()) if stage == 1 else (limited(), bad)
                    with mock.patch.object(gate.limits, "run_limited",
                                           side_effect=self.fake_stages(s1, s2, self.good_json())):
                        with self.assertRaises(gate.GateInfraError) as cm:
                            self.run_gate(BASELINE)
                    e = cm.exception
                    self.assertIsInstance(e, gate.GateError)
                    self.assertEqual(e.kill_fail, kill)
                    self.assertIn(f"stage {stage}", str(e))
                    self.assertEqual(e.evidence["stage"], stage)
                    self.assertTrue(os.path.isdir(e.evidence["dir"]))
                    json.dumps(e.evidence)                    # plain values: fit a stop record
                    if kill:
                        self.assertIn("KILL FAIL", str(e))
                        self.assertTrue(e.evidence["killed_pids_alive"] or e.evidence["cleanup_unconfirmed"])
                    with open(os.path.join(e.evidence["dir"], "evidence.json"), encoding="utf-8") as f:
                        self.assertEqual(json.load(f)["kill_fail"], kill)

    def test_unusable_path_raises(self):
        odd = os.path.join(self.work, "odd name.v")
        with open(BASELINE, "rb") as f, open(odd, "wb") as g:
            g.write(f.read())
        with self.assertRaises(gate.GateInfraError) as cm:
            self.run_gate(odd)
        self.assertFalse(cm.exception.kill_fail)

    def test_cli_infrastructure_fault_exit_2(self):
        out_json = os.path.join(self.work, "never.json")
        env = dict(os.environ, PATH="/usr/bin:/bin")         # the WSL Yosys lives elsewhere: not startable
        r = limits.run_limited([sys.executable, "-B", GATE_PY, BASELINE, "1", "--json", out_json, "--work-dir",
                                self.work], "test", cwd=self.work, env=env)
        self.assertEqual(r.rc, 2, r.stdout)
        out = r.stdout.decode("utf-8")
        self.assertTrue(out.startswith("GATE ERROR: stage 1 (read_verilog): could not start"), out)
        self.assertNotIn("GATE FAIL", out)
        self.assertFalse(os.path.exists(out_json))

    def test_unreadable_json_is_unrecognized(self):
        for what, text in {"missing": None, "empty": "", "not json": "{nope", "no modules": "{}",
                           "no ports": '{"modules": {"dot4sat": {}}}',
                           "bad direction": '{"modules": {"dot4sat": {"ports": {"clk": {"direction": "sideways", '
                                            '"bits": [2]}}}}}',
                           "bits not a list": '{"modules": {"dot4sat": {"ports": {"clk": {"direction": "input", '
                                              '"bits": 3}}}}}'}.items():
            with self.subTest(what=what):
                with mock.patch.object(gate.limits, "run_limited",
                                       side_effect=self.fake_stages(limited(), limited(), text)):
                    res = self.run_gate(BASELINE)
                self.assertFalse(res.passed)
                self.assertIn("stage 2", res.yosys_problem)
                self.assertEqual({h.rule for h in res.hits}, {"unrecognized"})

    def test_stale_json_never_reused(self):
        first = self.run_gate(BASELINE)
        self.assertTrue(first.passed)
        stale = [os.path.join(dp, f) for dp, _, fs in os.walk(self.work) for f in fs if f.endswith(".json")]
        self.assertTrue(stale)
        with mock.patch.object(gate.limits, "run_limited",
                               side_effect=self.fake_stages(limited(), limited(), None)):
            res = self.run_gate(BASELINE)
        self.assertFalse(res.passed)
        self.assertIn("stage 2", res.yosys_problem)
        self.assertNotEqual(first.evidence["dir"], res.evidence["dir"])

    def test_count_mismatch_is_unrecognized_and_keeps_g3(self):
        one = {"dot4sat": {p: (d, w) for p, d, w in gate.EXPECTED_PORTS}}
        with mock.patch.object(gate, "yosys_ports", return_value=(one, None)):
            res = self.run_gate(fx("neg_two_modules_unused"))
        self.assertEqual(triples(res), {("G3", 14, X), ("unrecognized", 0, X)})
        two = dict(one, extra={})
        with mock.patch.object(gate, "yosys_ports", return_value=(two, None)):
            res = self.run_gate(BASELINE)
        self.assertEqual(triples(res), {("unrecognized", 0, X)})

    def test_body_warning_kept_as_evidence_not_a_rule(self):
        res = self.run_gate(fx("neg_body_undeclared"))
        self.assertTrue(res.passed)                   # RV-01 item 5: no "any warning rejects" rule
        self.assertIn("implicitly declared", res.evidence["stage1"]["stderr"])
        with open(os.path.join(res.evidence["dir"], "evidence.json"), encoding="utf-8") as f:
            saved = json.load(f)
        self.assertIn("implicitly declared", saved["stage1"]["stderr"])

    def test_relative_work_dir(self):
        rel = os.path.relpath(self.work)
        res = gate.gate(BASELINE, 1, work_dir=rel)
        self.assertTrue(res.passed, res.yosys_problem)
        self.assertTrue(os.path.isabs(res.evidence["dir"]))

    def test_veto_samples_reach_author_review(self):
        sdir = os.path.join(rp.REVISE, "review", "samples")
        names = sorted(f for f in os.listdir(sdir) if f.endswith(".v"))
        self.assertEqual(len(names), 7)
        for f in names:
            with self.subTest(sample=f):
                self.assertTrue(self.run_gate(os.path.join(sdir, f), 2).passed)    # V1/V2 are not gate rules

    # ---------------------------------------------------------------- output formats
    def test_hit_text_is_the_rtl_line(self):
        for name in ("neg_include", "neg_define", "neg_width", "neg_duplicate_module"):
            with self.subTest(name=name):
                res = self.run_gate(fx(name))
                src = lines_of(fx(name))
                for h in res.hits:
                    if h.line > 0:
                        self.assertEqual(h.text, src[h.line - 1])
                    else:
                        self.assertIsNone(h.text)
        res = self.run_gate(fx("neg_include"))
        self.assertEqual({h.text for h in res.hits if h.line == 2}, {'`include "helper.vh"'})

    def test_gate_json_format_and_round_bytes(self):
        res = self.run_gate(fx("neg_include"))
        doc = gate.to_doc(res)
        self.assertEqual(list(doc), ["passed", "hits", "yosys_problem"])
        for h in doc["hits"]:
            self.assertEqual(list(h), ["rule", "line", "kind", "text"])
        self.assertEqual(gate.doc_bytes(res), rnd_mod.gate_bytes(res))
        self.assertEqual(json.loads(gate.doc_bytes(res).decode("utf-8")), doc)

    def test_rerun_is_byte_identical(self):
        for name in ("neg_fopen", "neg_include", "neg_two_modules_unused", "legal_ansi"):
            with self.subTest(name=name):
                a = gate.doc_bytes(self.run_gate(fx(name)))
                b = gate.doc_bytes(self.run_gate(fx(name)))
                self.assertEqual(a, b)

    def test_cli(self):
        out_json = os.path.join(self.work, "cli_gate.json")
        cases = [([BASELINE, "1"], 0, ["GATE PASS"]),
                 ([fx("neg_width"), "2", "--json", out_json], 1, ["GATE FAIL G1 line 9 (contract)"]),
                 ([BASELINE, "4"], 1, ["GATE FAIL G8 line 0 (extra)"])]
        for args, rc, want in cases:
            with self.subTest(args=args[1:]):
                r = limits.run_limited([sys.executable, "-B", GATE_PY, *args, "--work-dir", self.work], "test",
                                       cwd=self.work)
                self.assertEqual(r.rc, rc, r.stderr)
                lines = r.stdout.decode("utf-8").splitlines()
                self.assertEqual([ln for ln in lines if ln.startswith("GATE")], want)
        with open(out_json, "rb") as f:
            data = f.read()
        self.assertEqual(data, gate.doc_bytes(self.run_gate(fx("neg_width"), 2)))

    def test_lint_list_loaded_without_side_effects(self):
        scripts = os.path.join(rp.CASE, "scripts")

        def snapshot():
            out = {}
            for dp, _, fs in os.walk(scripts):
                for f in fs:
                    st = os.stat(os.path.join(dp, f))
                    out[os.path.join(dp, f)] = (st.st_size, st.st_mtime_ns)
            return out

        before_files, before_path = snapshot(), list(sys.path)
        before_mods = set(sys.modules)
        gate._LINT = None
        with mock.patch.object(sys, "dont_write_bytecode", False):
            lint = gate.lint_systf()
        self.assertIsInstance(lint, tuple)
        self.assertIn("dumpvars", lint)
        self.assertEqual(snapshot(), before_files)    # no __pycache__ written, nothing changed
        self.assertEqual(sys.path, before_path)
        for name in set(sys.modules) - before_mods:
            f = getattr(sys.modules[name], "__file__", None) or ""
            self.assertFalse(os.path.abspath(f).startswith(scripts + os.sep), name)
        for bare in ("grade", "check_sim", "logcheck"):
            self.assertNotIn(bare, sys.modules)

    def test_gate_rules_md_rows(self):
        texts = feedback.gate_rule_texts(GATE_RULES)
        self.assertEqual(set(texts), {f"G{i}" for i in range(1, 9)} | {"unrecognized"})
        given = feedback.gate_rule_texts(PROTOCOL)        # protocol v0.5 section 7.2 (RV-07 text of G7)
        for i in range(1, 9):
            self.assertEqual(texts[f"G{i}"], given[f"G{i}"])
        with open(GATE_RULES, encoding="utf-8") as f:
            md = f.read()
        self.assertIn("read_verilog -lib", md)
        for kw in gate.KEYWORDS:
            self.assertIn(f"`{kw}`", md)


if __name__ == "__main__":
    unittest.main()
