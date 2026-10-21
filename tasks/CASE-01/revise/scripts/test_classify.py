"""Tests for classify (CASE-01 stage B, Task 2, protocol section 6.2). Run per module, never with discover.
Events are built in the real stream-json shape read by void_check.parse_stream."""
import copy
import json
import unittest

import classify as c

EXPECT = {"init_model": "claude-opus-5-5", "assistant_model": "claude-opus-5-5", "cli_version": "2.1.296",
          "max_output_tokens": 128000,
          "plugins": ["cc-plugin-agents-md@builtin", "cc-plugin-plugin-authoring@builtin"]}

INIT = {"type": "system", "subtype": "init", "model": "claude-opus-5-5", "tools": [], "mcp_servers": [],
        "plugins": [{"name": "agents-md", "source": "cc-plugin-agents-md@builtin"},
                    {"name": "plugin-authoring", "source": "cc-plugin-plugin-authoring@builtin"}],
        "claude_code_version": "2.1.296", "memory_paths": {"auto": "x"}}
ASSISTANT = {"type": "assistant", "message": {"model": "claude-opus-5-5", "stop_reason": "end_turn",
                                              "content": [{"type": "text", "text": "hi"}]}}
RESULT = {"type": "result", "subtype": "success", "is_error": False, "num_turns": 1, "stop_reason": "end_turn",
          "result": "hi", "modelUsage": {"claude-opus-5-5": {"maxOutputTokens": 128000}}}
# the CLI sentence verified by the author in the stage A smoke records (protocol v0.5 RV-05)
CAP_SENTENCE = ("API Error: Claude's response exceeded the 64 output token maximum. To configure this behavior, "
                "set the CLAUDE_CODE_MAX_OUTPUT_TOKENS environment variable.")


def stream(*events, tail=""):
    return ("\n".join(json.dumps(e) for e in events) + "\n" + tail).encode("utf-8")


def good():
    return [copy.deepcopy(INIT), copy.deepcopy(ASSISTANT), copy.deepcopy(RESULT)]


def run(events=None, raw=None, exit_code=0, timed_out=False, over_limit=False, interrupted=False, prompt_ok=True,
        memory_dir_clean=True):
    raw = raw if raw is not None else stream(*(events if events is not None else good()))
    return c.classify(raw, EXPECT, exit_code, timed_out, over_limit, interrupted, prompt_ok, memory_dir_clean)


def cats(v):
    return [f[0] for f in v.flags]


def mutated(index, key, value):
    ev = good()
    ev[index][key] = value
    return ev


class ClassifyTests(unittest.TestCase):
    def test_clean_run_parses(self):
        v = run()
        self.assertEqual(v.flags, [])
        self.assertEqual((v.delivery, v.retry_allowed, v.global_stop, v.api_retries, v.parse_ok),
                         ("parse", False, False, 0, True))

    def test_each_non_content_flag_retries(self):
        def assistant_other():
            ev = good()
            ev[1]["message"]["model"] = "other"
            return ev

        cases = {
            "init.model": (dict(events=mutated(0, "model", "x")), c.F_MODEL),
            "assistant model": (dict(events=assistant_other()), c.F_MODEL),
            "tools": (dict(events=mutated(0, "tools", ["Bash"])), c.F_SHELL),
            "mcp": (dict(events=mutated(0, "mcp_servers", [{"name": "m"}])), c.F_SHELL),
            "plugins": (dict(events=mutated(0, "plugins", [])), c.F_SHELL),
            "cli version": (dict(events=mutated(0, "claude_code_version", "9")), c.F_SHELL),
            "prompt": (dict(prompt_ok=False), c.F_PROMPT),
            "memory": (dict(memory_dir_clean=False), c.F_MEMORY),
            "other model": (dict(events=mutated(2, "modelUsage", {"claude-opus-5-5": {"maxOutputTokens": 128000},
                                                                  "z": {}})), c.F_OTHER_MODEL),
            "maxOutputTokens": (dict(events=mutated(2, "modelUsage", {"claude-opus-5-5": {"maxOutputTokens": 1}})),
                                c.F_MAXTOK_FIELD),
            "exit": (dict(exit_code=1), c.F_EXIT),
            "is_error": (dict(events=mutated(2, "is_error", True)), c.F_EXIT),
            "subtype": (dict(events=mutated(2, "subtype", "error_during_execution")), c.F_EXIT),
            "unparsable": (dict(raw=stream(*good(), tail="{broken")), c.F_RECORD),
            "no result": (dict(events=good()[:2]), c.F_RECORD),
            "timeout": (dict(timed_out=True), c.F_RECORD),
            "over limit": (dict(over_limit=True), c.F_RECORD),
            "interrupted": (dict(interrupted=True), c.F_RECORD),
            "stop_reason": (dict(events=mutated(2, "stop_reason", "stop_sequence")), c.F_STOP),
            "multiturn": (dict(events=mutated(2, "num_turns", 3)), c.F_MULTITURN),
        }
        for name, (kw, cat) in cases.items():
            with self.subTest(name):
                v = run(**kw)
                self.assertIn(cat, cats(v))
                self.assertNotIn(c.F_LIMIT, cats(v))
                self.assertEqual((v.delivery, v.retry_allowed), ("retry", True))

    def test_memory_field_missing_is_record_incomplete(self):
        v = run(memory_dir_clean=None)
        self.assertEqual(cats(v), [c.F_RECORD])
        self.assertEqual(v.delivery, "retry")

    def test_limit_with_other_flags_never_retries(self):
        ev = good()
        ev[1]["message"]["stop_reason"] = "max_tokens"
        v = run(events=ev, exit_code=1, memory_dir_clean=False, timed_out=True)
        self.assertIn(c.F_LIMIT, cats(v))
        self.assertIn(c.F_EXIT, cats(v))
        self.assertEqual((v.delivery, v.retry_allowed), ("delivery_fail", False))

    def test_cap_text_without_max_tokens_is_limit(self):
        # the real shape (protocol v0.5 RV-05): assistant text and result both start with the CLI sentence,
        # num_turns 4, is_error true, no max_tokens anywhere
        ev = good()
        ev[1]["message"]["content"][0]["text"] = CAP_SENTENCE
        ev[1]["message"]["stop_reason"] = "stop_sequence"
        ev[2].update(result=CAP_SENTENCE, num_turns=4, is_error=True, stop_reason="stop_sequence")
        v = run(events=ev, exit_code=1)
        self.assertIn(c.F_LIMIT, cats(v))
        self.assertNotIn(c.F_MULTITURN, cats(v))
        self.assertEqual((v.delivery, v.retry_allowed), ("delivery_fail", False))

    def test_cap_text_in_result_only_is_limit(self):
        v = run(events=mutated(2, "result", CAP_SENTENCE))
        self.assertIn(c.F_LIMIT, cats(v))
        self.assertEqual(v.delivery, "delivery_fail")
        # the fixed prefix alone (any digit count) is enough
        v = run(events=mutated(2, "result", "API Error: Claude's response exceeded the 128000 output token maximum."))
        self.assertIn(c.F_LIMIT, cats(v))

    def test_cap_text_in_assistant_only_is_limit(self):
        ev = good()
        ev[1]["message"]["content"] = [{"type": "thinking", "thinking": "x"},
                                       {"type": "text", "text": CAP_SENTENCE}]
        v = run(events=ev)
        self.assertIn(c.F_LIMIT, cats(v))
        self.assertEqual(v.delivery, "delivery_fail")

    def test_cap_text_in_partial_stream_is_limit(self):
        ev = good()[:2]
        ev[1]["message"]["content"][0]["text"] = CAP_SENTENCE
        v = run(raw=stream(*ev, tail='{"type": "result", "res'))
        self.assertIn(c.F_LIMIT, cats(v))
        self.assertIn(c.F_RECORD, cats(v))
        self.assertEqual(v.delivery, "delivery_fail")
        self.assertFalse(v.parse_ok)

    def test_cap_phrase_not_at_start_is_not_limit(self):
        quoted = "The CLI says: " + CAP_SENTENCE
        later = "My answer.\n" + CAP_SENTENCE
        mid = "Note: a response may hit the 32000 output token maximum, so I keep this short."
        for name, text in (("quoted", quoted), ("later line", later), ("mid text", mid),
                           ("leading space", " " + CAP_SENTENCE), ("lower case", CAP_SENTENCE.lower()),
                           ("no number", "API Error: Claude's response exceeded the output token maximum.")):
            with self.subTest(name):
                ev = good()
                ev[1]["message"]["content"][0]["text"] = text
                ev[2]["result"] = text
                v = run(events=ev)
                self.assertNotIn(c.F_LIMIT, cats(v))
                self.assertEqual(v.delivery, "parse")

    def test_cap_sentence_in_other_fields_is_not_limit(self):
        cases = {
            "init field": mutated(0, "note", CAP_SENTENCE),
            "result other field": mutated(2, "error", CAP_SENTENCE),
            "system event": good()[:1] + [{"type": "system", "subtype": "notice", "text": CAP_SENTENCE}] + good()[1:],
            "user event text": good()[:2] + [{"type": "user", "message": {"content": [
                {"type": "text", "text": CAP_SENTENCE}]}}] + good()[2:],
            "stream_event result": good()[:2] + [{"type": "stream_event", "result": CAP_SENTENCE}] + good()[2:],
        }
        ev = good()
        ev[1]["message"]["content"][0]["thinking"] = CAP_SENTENCE      # not the text field
        cases["assistant other key"] = ev
        ev = good()
        ev[1]["message"]["text"] = CAP_SENTENCE                        # not inside content[i]
        cases["assistant message.text"] = ev
        for name, events in cases.items():
            with self.subTest(name):
                v = run(events=events)
                self.assertNotIn(c.F_LIMIT, cats(v))
                self.assertEqual(v.delivery, "parse")

    def test_cap_sentence_in_unparsed_line_is_not_limit(self):
        v = run(raw=stream(*good(), tail=CAP_SENTENCE + "\n"))
        self.assertNotIn(c.F_LIMIT, cats(v))
        self.assertIn(c.F_RECORD, cats(v))
        self.assertEqual(v.delivery, "retry")

    def test_cap_re_is_the_fixed_prefix(self):
        self.assertTrue(c.CAP_RE.match(CAP_SENTENCE))
        self.assertIsNone(c.CAP_RE.match("x" + CAP_SENTENCE))
        self.assertIsNone(c.CAP_RE.match("API Error: Claude's response exceeded the 64 output token maximum"))

    def test_limit_in_partial_stream_found(self):
        ev = good()[:2]
        ev[1]["message"]["stop_reason"] = "max_tokens"
        v = run(raw=stream(*ev, tail='{"type": "result", "res'))
        self.assertIn(c.F_LIMIT, cats(v))
        self.assertEqual(v.delivery, "delivery_fail")
        self.assertFalse(v.parse_ok)
        ev2 = good()[:2]
        ev2.insert(1, {"type": "stream_event", "stop_reason": "max_tokens"})
        self.assertIn(c.F_LIMIT, cats(run(raw=stream(*ev2, tail="{bad"))))

    def test_limit_plus_prompt_mismatch(self):
        ev = good()
        ev[2]["stop_reason"] = "max_tokens"
        v = run(events=ev, prompt_ok=False)
        self.assertEqual((v.delivery, v.global_stop, v.retry_allowed), ("delivery_fail", True, False))

    def test_prompt_mismatch_without_limit(self):
        v = run(prompt_ok=False)
        self.assertEqual((v.delivery, v.global_stop, v.retry_allowed), ("retry", True, True))

    def test_unreadable_without_limit_evidence_is_record_incomplete(self):
        v = run(raw=stream(good()[0], tail="{garbage\n\x00\xff"))
        self.assertIn(c.F_RECORD, cats(v))
        self.assertNotIn(c.F_LIMIT, cats(v))
        self.assertEqual((v.delivery, v.retry_allowed, v.parse_ok), ("retry", True, False))
        v = run(raw=b"")
        self.assertEqual((v.delivery, v.parse_ok), ("retry", False))

    def test_interrupted_flag(self):
        v = run(interrupted=True)
        self.assertIn((c.F_RECORD, "运行中断"), v.flags)
        self.assertFalse(v.parse_ok)
        self.assertEqual(v.delivery, "retry")

    def test_multiturn_without_limit_is_retry(self):
        v = run(events=mutated(2, "num_turns", 2))
        self.assertEqual(cats(v), [c.F_MULTITURN])
        self.assertEqual((v.delivery, v.retry_allowed), ("retry", True))
        ev = mutated(2, "num_turns", 2)
        ev[2]["stop_reason"] = "max_tokens"
        self.assertEqual(run(events=ev).delivery, "delivery_fail")

    def test_api_retry_counted_not_flagged(self):
        ev = good()
        ev.insert(1, {"type": "system", "subtype": "api_retry", "attempt": 1})
        ev.insert(1, {"type": "system", "subtype": "api_retry", "attempt": 2})
        v = run(events=ev)
        self.assertEqual((v.flags, v.api_retries, v.delivery), ([], 2, "parse"))


if __name__ == "__main__":
    unittest.main()
