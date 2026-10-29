"""Test double for claude.exe (CASE-02 tests only). Same stream-json shape as tasks/CASE-01/diag/scripts/fake_claude.py
(Claude Code 2.1.296 print mode) plus: a `usage` object in the result event (the budget probe reads it), and the
scenarios bigout (writes ~3 MB to stdout before answering), bigerr (~1 MB to stderr), hang (sleeps 30 s).
Behaviour per model comes from FAKE_CLAUDE_SCENARIOS, a JSON object {model flag: scenario}."""
import json
import os
import sys
import time

NAMES = {"claude-opus-5-5": ("claude-opus-5-5", "claude-opus-5-5"), "k3[1M]": ("k3[1m]", "k3"),
         "deepseek-v4-pro[1M]": ("deepseek-v4-pro[1m]", "deepseek-v4-pro")}
REPORTED_MAX = {"claude-opus-5-5": 128000, "k3[1M]": 32000, "deepseek-v4-pro[1M]": 32000}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    argv = sys.argv[1:]
    if argv == ["--version"]:
        print(os.environ.get("FAKE_CLAUDE_VERSION", "2.1.296") + " (Claude Code)")
        return 0
    if argv[:2] == ["auth", "status"]:
        print(json.dumps({"loggedIn": os.environ.get("FAKE_LOGGED_IN", "1") == "1", "email": os.environ["FAKE_EMAIL"]}))
        return 0
    model = argv[argv.index("--model") + 1]
    system = argv[argv.index("--system-prompt") + 1]
    scenario = json.loads(os.environ.get("FAKE_CLAUDE_SCENARIOS", "{}")).get(model, "ok")
    user = "" if scenario == "nostdin" else sys.stdin.buffer.read().decode("utf-8")
    init_model, msg_model = NAMES[model]
    if scenario == "bigout":
        for _ in range(60):
            sys.stdout.write(json.dumps({"type": "noise", "pad": "y" * 50000}) + "\n")
            sys.stdout.flush()
            time.sleep(0.05)
    if scenario == "bigerr":
        for _ in range(60):
            sys.stderr.write("e" * 20000 + "\n")
            sys.stderr.flush()
            time.sleep(0.05)
    if scenario == "hang":
        time.sleep(30)
    if scenario == "burstexit":                        # a burst over the limit, then a normal exit within one poll
        sys.stdout.write(json.dumps({"type": "noise", "pad": "y" * 150000}) + "\n")
        sys.stdout.flush()
    if scenario == "hangtree":                         # a grandchild that outlives a soft termination of this process
        import subprocess
        subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        time.sleep(30)
    leaked = sorted(k for k in os.environ if k.upper().startswith(("ANTHROPIC_", "CLAUDE"))
                    and k not in ("CLAUDE_CODE_MAX_OUTPUT_TOKENS",))
    answer = f"echo system={len(system)} user={len(user)} leaked={leaked}"
    for canary in ("青松-0427", "白鹭-1010"):
        if canary in system or canary in user:
            answer += " " + canary
    if scenario == "email":
        answer += " contact " + os.environ["FAKE_EMAIL"]
    if scenario == "workdir":
        answer += " cwd " + os.getcwd()
    if scenario == "crash":
        raise SystemExit(3)
    cap = int(os.environ.get("CLAUDE_CODE_MAX_OUTPUT_TOKENS", "32000"))
    capped = "数到 300" in user and cap < 300 and scenario != "nocap"
    if capped:
        answer = (f"API Error: Claude's response exceeded the {cap} output token maximum. To configure this "
                  "behavior, set the CLAUDE_CODE_MAX_OUTPUT_TOKENS environment variable.")
    in_tok = 2000 + len(user.encode("utf-8")) // 4
    events = [
        {"type": "system", "subtype": "init", "model": init_model, "tools": [], "mcp_servers": [],
         "claude_code_version": "2.1.296", "per_turn_effort_active": model.startswith("claude"),
         "memory_paths": {} if scenario == "nomemory" else {"auto": os.path.join(os.getcwd(), "no-memory-here")},
         "plugins": [{"name": "cc-plugin-agents-md", "source": "cc-plugin-agents-md@builtin"},
                     {"name": "cc-plugin-plugin-authoring", "source": "cc-plugin-plugin-authoring@builtin"}]},
        {"type": "assistant", "message": {"model": msg_model, "content": [{"type": "text", "text": answer}]}},
        {"type": "result", "subtype": "success", "is_error": capped, "num_turns": 4 if capped else 1,
         "stop_reason": "stop_sequence" if capped else "max_tokens" if scenario == "truncated" else "end_turn",
         "result": answer,
         "usage": {"input_tokens": in_tok, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 5},
         "modelUsage": {init_model: {"maxOutputTokens": REPORTED_MAX[model], "inputTokens": in_tok,
                                     "cacheCreationInputTokens": 0, "cacheReadInputTokens": 0, "outputTokens": 5}}},
    ]
    for e in events:
        sys.stdout.write(json.dumps(e, ensure_ascii=False) + "\n")
    return 1 if capped else 0


if __name__ == "__main__":
    sys.exit(main())
