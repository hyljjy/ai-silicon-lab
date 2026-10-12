"""Test double for claude.exe (tests only). Emits stream-json like Claude Code 2.1.296 in print mode.
Behaviour per model is chosen by FAKE_CLAUDE_SCENARIOS, a JSON object {model flag: scenario}:
  ok | truncated | email | nostdin | workdir | nomemory | crash
--version and `auth status --json` answer from FAKE_CLAUDE_VERSION and FAKE_LOGGED_IN.
"""
import json
import os
import sys

NAMES = {"claude-opus-5-5": ("claude-opus-5-5", "claude-opus-5-5"), "k3[1M]": ("k3[1m]", "k3"),
         "deepseek-v4-pro[1M]": ("deepseek-v4-pro[1m]", "deepseek-v4-pro")}


def main():
    sys.stdout.reconfigure(encoding="utf-8")            # the real claude.exe writes UTF-8 whatever the console
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
    events = [
        {"type": "system", "subtype": "init", "model": init_model, "tools": [], "mcp_servers": [],
         "claude_code_version": "2.1.296", "per_turn_effort_active": model.startswith("claude"),
         "memory_paths": {} if scenario == "nomemory" else {"auto": os.path.join(os.getcwd(), "no-memory-here")},
         "plugins": [{"name": "cc-plugin-agents-md", "source": "cc-plugin-agents-md@builtin"},
                     {"name": "cc-plugin-plugin-authoring", "source": "cc-plugin-plugin-authoring@builtin"}]},
        {"type": "assistant", "message": {"model": msg_model, "content": [{"type": "text", "text": answer}]}},
        {"type": "result", "subtype": "success", "is_error": False, "num_turns": 1,
         "stop_reason": "max_tokens" if scenario == "truncated" else "end_turn", "result": answer,
         "modelUsage": {init_model: {"maxOutputTokens": int(os.environ.get("CLAUDE_CODE_MAX_OUTPUT_TOKENS", "128000"))}}},
    ]
    for e in events:
        sys.stdout.write(json.dumps(e, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
