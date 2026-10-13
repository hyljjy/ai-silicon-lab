"""Unit tests of void_check.py. Run: python -B -m unittest test_void_check"""
import copy
import unittest

import void_check as vc

EXPECT = {"init_model": "k3[1m]", "assistant_model": "k3", "cli_version": "2.1.296", "max_output_tokens": 32000,
          "plugins": ["cc-plugin-agents-md@builtin", "cc-plugin-plugin-authoring@builtin"]}


def good_events():
    return [
        {"type": "system", "subtype": "init", "model": "k3[1m]", "tools": [], "mcp_servers": [],
         "claude_code_version": "2.1.296",
         "plugins": [{"name": "cc-plugin-agents-md", "source": "cc-plugin-agents-md@builtin"},
                     {"name": "cc-plugin-plugin-authoring", "source": "cc-plugin-plugin-authoring@builtin"}]},
        {"type": "assistant", "message": {"model": "k3", "content": [{"type": "thinking"}]}},
        {"type": "assistant", "message": {"model": "k3", "content": [{"type": "text", "text": "答复"}]}},
        {"type": "result", "subtype": "success", "is_error": False, "num_turns": 1, "stop_reason": "end_turn",
         "result": "答复", "modelUsage": {"k3[1m]": {"maxOutputTokens": 32000}}},
    ]


def cats(events, **kw):
    args = dict(exit_code=0, prompt_ok=True, memory_dir_clean=True)
    args.update(kw)
    return vc.categories(vc.check_run(events, EXPECT, **args))


class TestVoidCheck(unittest.TestCase):
    def test_good_run_is_valid(self):
        self.assertEqual(vc.check_run(good_events(), EXPECT, 0, True, True), [])
        self.assertEqual(vc.answer_text(good_events()), "答复")

    def mutate(self, index, path, value):
        ev = copy.deepcopy(good_events())
        obj = ev[index]
        for key in path[:-1]:
            obj = obj[key]
        obj[path[-1]] = value
        return ev

    def test_each_criterion(self):
        self.assertEqual(cats(self.mutate(0, ["model"], "k3")), [vc.CAT_MODEL])
        self.assertEqual(cats(self.mutate(1, ["message", "model"], "claude-opus-5-5")), [vc.CAT_MODEL])
        self.assertEqual(cats(self.mutate(0, ["tools"], ["Read"])), [vc.CAT_SHELL])
        self.assertEqual(cats(self.mutate(0, ["mcp_servers"], [{"name": "x"}])), [vc.CAT_SHELL])
        self.assertEqual(cats(self.mutate(0, ["plugins"], [])), [vc.CAT_SHELL])
        self.assertEqual(cats(self.mutate(0, ["claude_code_version"], "2.1.300")), [vc.CAT_SHELL])
        self.assertEqual(cats(self.mutate(3, ["subtype"], "error_max_turns")), [vc.CAT_END])
        self.assertEqual(cats(self.mutate(3, ["is_error"], True)), [vc.CAT_END])
        self.assertEqual(cats(self.mutate(3, ["num_turns"], 2)), [vc.CAT_END])
        self.assertEqual(cats(self.mutate(3, ["stop_reason"], "max_tokens")), [vc.CAT_END])
        self.assertEqual(cats(self.mutate(3, ["modelUsage"], {"k3[1m]": {"maxOutputTokens": 32000},
                                                              "claude-haiku": {"maxOutputTokens": 1}})),
                         [vc.CAT_OTHER_MODEL])
        self.assertEqual(cats(self.mutate(3, ["modelUsage"], {"k3[1m]": {"maxOutputTokens": 128000}})),
                         [vc.CAT_LIMIT])
        self.assertEqual(cats(good_events(), exit_code=1), [vc.CAT_EXIT])
        self.assertEqual(cats(good_events(), prompt_ok=False), [vc.CAT_PROMPT])
        self.assertEqual(cats(good_events(), memory_dir_clean=False), [vc.CAT_MEMORY])
        self.assertEqual(cats(good_events(), memory_dir_clean=None), [vc.CAT_RECORD])

    def test_missing_records(self):
        self.assertEqual(cats(good_events()[:3]), [vc.CAT_RECORD])
        self.assertEqual(cats([]), [vc.CAT_RECORD])

    def test_parse_stream(self):
        ev = vc.parse_stream('{"type": "result"}\n\nnot json\n')
        self.assertEqual([e["type"] for e in ev], ["result", "_unparsed"])

    def test_categories_do_not_name_the_model(self):
        problems = vc.check_run(self.mutate(0, ["model"], "deepseek-v4-pro[1m]"), EXPECT, 0, True, True)
        self.assertIn("deepseek", problems[0][1])                 # detail (sealed) may name it
        self.assertNotIn("deepseek", " ".join(vc.categories(problems)))   # category (shown) never does


if __name__ == "__main__":
    unittest.main()
