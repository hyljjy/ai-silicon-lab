"""Test double for claude.exe in the CASE-01 stage B tests (test_run_revise only; never a real model call).

Emits stream-json like Claude Code 2.1.296 in print mode. It limits ITSELF to 10 s of run time and 1 MB of output
(a watchdog thread exits the process), whatever the wrapper does.

Configuration (environment; the wrapper removes ANTHROPIC_* and CLAUDE* but keeps these):
  FAKE_CLAUDE_PLAN  path of a JSON file {<--model value>: [scenario of call 1, scenario of call 2, ...]}; a call
                    beyond the list uses the last entry; a model not in the plan uses "ok_case01". The call index
                    per model is counted in <plan>.count.<n> files next to the plan.
  FAKE_CLAUDE_LOG   optional JSONL file: one line per invocation {argv (system prompt replaced by its sha256),
                    model, scenario, stdin_sha256, cwd, max_output_tokens, leaked_env, pid}.
  FAKE_CLAUDE_VERSION (default 2.1.296), FAKE_LOGGED_IN ("1" default), FAKE_VERSION_RC / FAKE_AUTH_RC (exit code
  of --version / auth status, default 0; the expected text is printed anyway).
Scenarios: ok_case01 max_tokens max_tokens_bad_lines cap_text_only multiturn_no_limit wrong_model hang prompt_echo
private_in_rtl partial_limit_then_hang. Under CLAUDE_CODE_MAX_OUTPUT_TOKENS < 300 a "从 1 数到 300" prompt is cut
off like the real CLI, and cap_text_only emits the same shape (protocol v0.5 RV-05, the stage A smoke records): an
assistant event whose message.content[0].text and a result event (is_error true, num_turns 4) whose result both
start with the CLI error sentence (cap_error), and no max_tokens anywhere."""
import hashlib
import json
import os
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import classify  # noqa: E402  (CAP_RE: cap_error must match the prefix the classifier looks for)

MAX_SECONDS = 10
MAX_BYTES = 1024 * 1024
PLUGINS = [{"name": "cc-plugin-agents-md", "source": "cc-plugin-agents-md@builtin"},
           {"name": "cc-plugin-plugin-authoring", "source": "cc-plugin-plugin-authoring@builtin"}]

_written = [0]


def cap_error(cap):
    """The CLI error sentence of the stage A smoke records (RV-05), for an output cap of `cap` tokens."""
    text = (f"API Error: Claude's response exceeded the {cap} output token maximum. To configure this behavior, "
            f"set the CLAUDE_CODE_MAX_OUTPUT_TOKENS environment variable.")
    assert classify.CAP_RE.match(text)
    return text


def _watchdog():
    time.sleep(MAX_SECONDS)
    os._exit(9)


def out(text):
    data = text.encode("utf-8")
    if _written[0] + len(data) > MAX_BYTES:
        os._exit(8)
    _written[0] += len(data)
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


def emit(event):
    out(json.dumps(event, ensure_ascii=False) + "\n")


CASE01_ANSWER = """## 预测表

| id | action | metric | check | corner | category | value_kind | direction | low | high | unit | point | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 加一级流水 | L | eq | all | all | exact | none |  |  | cycle | 1 | 结构 |

## 失败条件

- 若 setup slack 变差则判定失败

DECLARED_L = 1

```verilog
module dot4sat(input clk, input rst);
  // fake candidate
endmodule
```
"""

# a Windows user-directory path, assembled at run time so that this source file passes the privacy check itself
PRIVATE_DIR = "\\".join(["C:", "Us" + "ers", "someone"])
PRIVATE_ANSWER = ("## 预测表\r\n\r\n没有表。\r\n\r\nDECLARED_L = 1\r\n\r\n```verilog\r\n"
                  "module dot4sat(input clk, input rst);\r\n"
                  "  // built from " + PRIVATE_DIR + "\\work\\x.v\r\n"
                  "endmodule\r\n```\r\n")


def next_index(plan_path, model):
    key = hashlib.sha256(model.encode("utf-8")).hexdigest()[:12]
    path = f"{plan_path}.count.{key}"
    try:
        with open(path, encoding="ascii") as f:
            n = int(f.read().strip() or "0")
    except OSError:
        n = 0
    with open(path, "w", encoding="ascii") as f:
        f.write(str(n + 1))
    return n


def main():
    threading.Thread(target=_watchdog, daemon=True).start()
    argv = sys.argv[1:]
    if argv == ["--version"]:
        out(os.environ.get("FAKE_CLAUDE_VERSION", "2.1.296") + " (Claude Code)\n")
        return int(os.environ.get("FAKE_VERSION_RC", "0"))
    if argv[:2] == ["auth", "status"]:
        out(json.dumps({"loggedIn": os.environ.get("FAKE_LOGGED_IN", "1") == "1"}) + "\n")
        return int(os.environ.get("FAKE_AUTH_RC", "0"))
    model = argv[argv.index("--model") + 1]
    system = argv[argv.index("--system-prompt") + 1]
    plan_path = os.environ.get("FAKE_CLAUDE_PLAN")
    scenario = "ok_case01"
    if plan_path:
        with open(plan_path, encoding="utf-8") as f:
            plan = json.load(f)
        seq = plan.get(model) or ["ok_case01"]
        i = next_index(plan_path, model)
        scenario = seq[min(i, len(seq) - 1)]
    stdin = sys.stdin.buffer.read(MAX_BYTES)
    cap = int(os.environ.get("CLAUDE_CODE_MAX_OUTPUT_TOKENS", "32000"))
    log = os.environ.get("FAKE_CLAUDE_LOG")
    if log:
        shown = list(argv)
        shown[argv.index("--system-prompt") + 1] = "sha256:" + hashlib.sha256(system.encode("utf-8")).hexdigest()
        leaked = sorted(k for k in os.environ if k.upper().startswith(("ANTHROPIC_", "CLAUDE"))
                        and k != "CLAUDE_CODE_MAX_OUTPUT_TOKENS")
        with open(log, "a", encoding="utf-8") as f:
            f.write(json.dumps({"argv": shown, "model": model, "scenario": scenario,
                                "stdin_sha256": hashlib.sha256(stdin).hexdigest(), "cwd": os.getcwd(),
                                "max_output_tokens": cap, "leaked_env": leaked, "pid": os.getpid(),
                                "time": time.time()}, ensure_ascii=False) + "\n")
    user = stdin.decode("utf-8", "replace")
    init = {"type": "system", "subtype": "init", "model": "other-model" if scenario == "wrong_model" else model,
            "tools": [], "mcp_servers": [], "claude_code_version": "2.1.296",
            "memory_paths": {"auto": os.path.join(os.getcwd(), "no-memory-here")}, "plugins": PLUGINS}
    usage = {model: {"maxOutputTokens": 32000}}

    def assistant(text, stop="end_turn"):
        return {"type": "assistant", "message": {"model": model, "stop_reason": stop,
                                                 "content": [{"type": "text", "text": text}]}}

    def result(text, stop="end_turn", turns=1, is_error=False, subtype="success"):
        return {"type": "result", "subtype": subtype, "is_error": is_error, "num_turns": turns,
                "stop_reason": stop, "result": text, "modelUsage": usage}

    emit(init)
    if ("数到 300" in user and cap < 300) or scenario == "cap_text_only":
        text = cap_error(cap)
        emit(assistant(text, "stop_sequence"))
        emit(result(text, "stop_sequence", 4, True))
        return 1
    if scenario in ("hang", "partial_limit_then_hang"):
        if scenario == "partial_limit_then_hang":
            emit(assistant("## 预测表\n部分答复", "max_tokens"))
        time.sleep(MAX_SECONDS + 5)                 # the watchdog ends the process after MAX_SECONDS
        return 9
    if scenario == "max_tokens":
        partial = CASE01_ANSWER[:200]
        emit(assistant(partial, "max_tokens"))
        emit(result(partial, "max_tokens"))
        return 0
    if scenario == "max_tokens_bad_lines":
        partial = CASE01_ANSWER[:120]
        emit(assistant(partial, "max_tokens"))
        out("{not json\n")
        emit(result(partial, "max_tokens"))
        return 0
    if scenario == "multiturn_no_limit":
        emit(assistant("第一段"))
        emit(assistant("第二段"))
        emit(result(CASE01_ANSWER, "end_turn", 3))
        return 0
    if scenario == "prompt_echo":
        text = f"系统提示原文：{system}\n题目原文：{user}\n"
        emit(assistant(text))
        emit(result(text))
        return 0
    text = PRIVATE_ANSWER if scenario == "private_in_rtl" else CASE01_ANSWER   # ok_case01, wrong_model
    emit(assistant(text))
    emit(result(text))
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except BaseException:
        os._exit(7)
    sys.stdout.flush()
    os._exit(rc)
