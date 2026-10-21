"""Call classification for CASE-01 stage B (protocol v0.5 section 6.2, revision RV-05). Pure function module: no files, no processes.

Mapping of the protocol table to flags (expect shape = diag/rules/expected.json, one model's entry):
  F_MODEL        init.model or any assistant message.model differs (init_model, assistant_model)
  F_SHELL        tools / mcp_servers not empty, plugins differ, claude_code_version differs (plugins, cli_version)
  F_PROMPT       prompt_ok is false (system prompt / stdin byte hash mismatch)
  F_MEMORY       memory_dir_clean is false
  F_OTHER_MODEL  result.modelUsage has models other than init_model
  F_MAXTOK_FIELD modelUsage[init_model].maxOutputTokens != expect max_output_tokens
  F_EXIT         exit code not 0, is_error true, result.subtype not success
  F_RECORD       unparsable line, no init/result, memory_dir_clean None (init lacks memory_paths.auto),
                 timeout, over_limit, interrupted, exit code unknown
  F_LIMIT        output-cap evidence: (1) stop_reason == "max_tokens" on any event (incl. message.stop_reason);
                 (2) RV-05: a type "result" event whose `result` string, or a type "assistant" event whose
                 message.content[i].text string, STARTS WITH the verified CLI sentence (CAP_RE, case-sensitive).
                 The phrase elsewhere (mid-text, later line, other fields or event types, `_unparsed` raw lines)
                 is not evidence; num_turns > 1 alone is not evidence
  F_MULTITURN    num_turns > 1 without cap evidence
  F_STOP         result.stop_reason is neither end_turn nor max_tokens
api_retry events are only counted (Verdict.api_retries).
Cap evidence is searched in all readable events; an incomplete record never short-circuits it."""
import re
from collections import namedtuple

import revpaths

void_check = revpaths.load_diag("void_check")   # read-only reuse of stage A, loaded by explicit path (no sys.path)

parse_stream = void_check.parse_stream
answer_text = void_check.answer_text

# RV-05: the fixed prefix of the CLI error sentence the author verified in the stage A smoke records
# ("API Error: Claude's response exceeded the 64 output token maximum. To configure this behavior, ...")
CAP_RE = re.compile(r"API Error: Claude's response exceeded the [0-9]+ output token maximum\.")

F_MODEL = "模型不符"
F_SHELL = "外壳不符"
F_PROMPT = "题目字节不符"
F_MEMORY = "记忆目录非空"
F_OTHER_MODEL = "混入其他模型"
F_MAXTOK_FIELD = "maxOutputTokens 不符"
F_EXIT = "退出码非 0"
F_RECORD = "记录不完整"
F_LIMIT = "输出上限"
F_MULTITURN = "异常多轮"
F_STOP = "stop_reason 异常"

Verdict = namedtuple("Verdict", "flags delivery retry_allowed global_stop api_retries parse_ok")


def _starts_cap(s):
    return isinstance(s, str) and CAP_RE.match(s) is not None


def _cap_text(e):
    """RV-05 evidence two: only result.result or assistant message.content[i].text, matched at the start."""
    if e.get("type") == "result":
        return _starts_cap(e.get("result"))
    if e.get("type") == "assistant":
        msg = e.get("message")
        content = msg.get("content") if isinstance(msg, dict) else None
        return isinstance(content, list) and any(isinstance(b, dict) and _starts_cap(b.get("text")) for b in content)
    return False


def _max_tokens_stop(e):
    msg = e.get("message")
    return e.get("stop_reason") == "max_tokens" or (isinstance(msg, dict) and msg.get("stop_reason") == "max_tokens")


def classify(raw_stdout, expect, exit_code, timed_out, over_limit, interrupted, prompt_ok, memory_dir_clean):
    text = bytes(raw_stdout or b"").decode("utf-8", errors="replace")
    events = [e if isinstance(e, dict) else {"type": "_unparsed", "raw": str(e)[:200]} for e in parse_stream(text)]
    flags = []
    init = next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), None)
    result = next((e for e in events if e.get("type") == "result"), None)
    unparsed = any(e.get("type") == "_unparsed" for e in events)
    api_retries = sum(e.get("subtype") == "api_retry" for e in events)

    cap = any(_max_tokens_stop(e) for e in events) or any(_cap_text(e) for e in events)
    turns = (result or {}).get("num_turns")
    multi = isinstance(turns, int) and turns > 1
    if cap:
        flags.append((F_LIMIT, "输出上限证据"))
    elif multi:
        flags.append((F_MULTITURN, f"num_turns={turns}"))

    if interrupted:
        flags.append((F_RECORD, "运行中断"))
    if timed_out:
        flags.append((F_RECORD, "调用超时"))
    if over_limit:
        flags.append((F_RECORD, "超限，输出不完整"))
    if unparsed:
        flags.append((F_RECORD, "无法解析的行"))
    if init is None:
        flags.append((F_RECORD, "缺少 init 记录"))
    if result is None:
        flags.append((F_RECORD, "缺少 result 记录"))

    if exit_code is None:
        flags.append((F_RECORD, "退出码未知"))
    elif exit_code != 0:
        flags.append((F_EXIT, f"exit {exit_code}"))
    if not prompt_ok:
        flags.append((F_PROMPT, "题目字节与预登记不符"))
    if memory_dir_clean is None:
        flags.append((F_RECORD, "init 中没有 memory_paths.auto"))
    elif not memory_dir_clean:
        flags.append((F_MEMORY, "auto memory 目录非空"))

    if init is not None:
        if init.get("model") != expect["init_model"]:
            flags.append((F_MODEL, f"init.model={init.get('model')!r}"))
        if init.get("tools") != [] or init.get("mcp_servers") != []:
            flags.append((F_SHELL, f"tools={init.get('tools')!r} mcp={init.get('mcp_servers')!r}"))
        plugins = sorted(str(p.get("source")) if isinstance(p, dict) else str(p) for p in init.get("plugins") or [])
        if plugins != sorted(expect["plugins"]):
            flags.append((F_SHELL, f"plugins={plugins}"))
        if init.get("claude_code_version") != expect["cli_version"]:
            flags.append((F_SHELL, f"cli={init.get('claude_code_version')!r}"))
    models = {(e.get("message") or {}).get("model") for e in events if e.get("type") == "assistant"}
    if models and models != {expect["assistant_model"]}:
        flags.append((F_MODEL, f"assistant models={sorted(map(str, models))}"))

    if result is not None:
        if result.get("subtype") != "success" or result.get("is_error") is not False:
            flags.append((F_EXIT, f"subtype={result.get('subtype')} is_error={result.get('is_error')}"))
        if result.get("stop_reason") not in ("end_turn", "max_tokens"):
            flags.append((F_STOP, f"stop_reason={result.get('stop_reason')!r}"))
        usage = result.get("modelUsage")
        usage = usage if isinstance(usage, dict) else {}
        if set(usage) != {expect["init_model"]}:
            flags.append((F_OTHER_MODEL, f"modelUsage={sorted(usage)}"))
        else:
            mot = usage[expect["init_model"]]
            mot = mot.get("maxOutputTokens") if isinstance(mot, dict) else None
            if mot != expect["max_output_tokens"]:
                flags.append((F_MAXTOK_FIELD, f"maxOutputTokens={mot}"))

    has_limit = any(c == F_LIMIT for c, _ in flags)
    if has_limit:
        delivery, retry_allowed = "delivery_fail", False
    elif flags:
        delivery, retry_allowed = "retry", True
    else:
        delivery, retry_allowed = "parse", False
    parse_ok = not (unparsed or result is None or timed_out or over_limit or interrupted)
    return Verdict(flags, delivery, retry_allowed, any(c == F_PROMPT for c, _ in flags), api_retries, parse_ok)
