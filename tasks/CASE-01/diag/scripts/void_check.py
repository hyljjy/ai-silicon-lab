"""Void criteria for one model run (protocol v0.5 section 5.3). Pure functions, no model is called.

check_run(events, expect, exit_code, prompt_ok, memory_dir_clean) returns a list of (category, detail):
an empty list means the run is valid. memory_dir_clean is None when init does not name the auto memory directory
(then the record is incomplete), else whether that directory is missing or empty after the run (the working directory
is new, so a memory directory that existed before the run would still be there). Categories are generic on purpose: they may be shown to the operator before
unblinding, so they never name the model; details (which may name it) stay in the sealed records.
"""
import json

CAT_MODEL = "模型名不符"
CAT_SHELL = "外壳状态不符"            # tools, MCP servers, plugins, CLI version
CAT_END = "运行未正常结束"            # result subtype / is_error / stop_reason / turns
CAT_LIMIT = "输出上限不符"
CAT_OTHER_MODEL = "混入其他模型"
CAT_PROMPT = "题目字节不符"
CAT_MEMORY = "记忆目录非空"
CAT_EXIT = "退出码非 0"
CAT_RECORD = "记录不完整"
CAT_INTERRUPTED = "运行中断"         # set by run_round --resume, never by check_run


def parse_stream(text):
    """stream-json lines -> list of events; malformed lines become {'type': '_unparsed'}."""
    events = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except ValueError:
            events.append({"type": "_unparsed", "raw": line[:200]})
    return events


def answer_text(events):
    result = next((e for e in events if e.get("type") == "result"), None)
    return (result or {}).get("result") or ""


def check_run(events, expect, exit_code, prompt_ok, memory_dir_clean):
    problems = []
    init = next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), None)
    result = next((e for e in events if e.get("type") == "result"), None)
    if exit_code != 0:
        problems.append((CAT_EXIT, f"exit {exit_code}"))
    if not prompt_ok:
        problems.append((CAT_PROMPT, "prompt bytes differ from the pre-registered build"))
    if init is None or result is None:
        problems.append((CAT_RECORD, "init or result record missing"))
        return problems
    if any(e.get("type") == "_unparsed" for e in events):
        problems.append((CAT_RECORD, "unparsable stream-json line"))
    if init.get("model") != expect["init_model"]:
        problems.append((CAT_MODEL, f"init.model={init.get('model')!r}"))
    assistant_models = {e.get("message", {}).get("model") for e in events if e.get("type") == "assistant"}
    if assistant_models != {expect["assistant_model"]}:
        problems.append((CAT_MODEL, f"assistant models={sorted(map(str, assistant_models))}"))
    if init.get("tools") != [] or init.get("mcp_servers") != []:
        problems.append((CAT_SHELL, f"tools={init.get('tools')!r} mcp={init.get('mcp_servers')!r}"))
    plugins = sorted(p.get("source") for p in init.get("plugins") or [])
    if plugins != sorted(expect["plugins"]):
        problems.append((CAT_SHELL, f"plugins={plugins}"))
    if init.get("claude_code_version") != expect["cli_version"]:
        problems.append((CAT_SHELL, f"cli={init.get('claude_code_version')!r}"))
    if (result.get("subtype"), result.get("is_error"), result.get("num_turns")) != ("success", False, 1):
        problems.append((CAT_END, f"subtype={result.get('subtype')} is_error={result.get('is_error')} "
                                  f"turns={result.get('num_turns')}"))
    if result.get("stop_reason") != "end_turn":
        problems.append((CAT_END, f"stop_reason={result.get('stop_reason')!r}"))
    usage = result.get("modelUsage") or {}
    if set(usage) != {expect["init_model"]}:
        problems.append((CAT_OTHER_MODEL, f"modelUsage={sorted(usage)}"))
    elif usage[expect["init_model"]].get("maxOutputTokens") != expect["max_output_tokens"]:
        problems.append((CAT_LIMIT, f"maxOutputTokens={usage[expect['init_model']].get('maxOutputTokens')}"))
    if memory_dir_clean is None:
        problems.append((CAT_RECORD, "init has no memory_paths.auto"))
    elif not memory_dir_clean:
        problems.append((CAT_MEMORY, "auto memory directory exists and is not empty"))
    return problems


def categories(problems):
    """Distinct categories in first-seen order: the only void information shown before unblinding."""
    seen = []
    for cat, _ in problems:
        if cat not in seen:
            seen.append(cat)
    return seen
