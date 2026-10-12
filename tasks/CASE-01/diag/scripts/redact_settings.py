"""Key-free copies of the per-model Claude Code settings files (protocol v0.5 sections 5.1 and 3 step 4).

Run by the AUTHOR (the operator never reads the originals), from Git Bash in the repository root, with Windows Python
because the files live in the Windows user profile:
  python -B tasks/CASE-01/diag/scripts/redact_settings.py

Reads %USERPROFILE%/.diag-models/{claude,kimi,deepseek}.json and checks them first. When any file sets something that
could change a run, it prints OVERRIDE RISK lines (key names only), writes NOTHING and exits 1; the author edits the
original and runs it again. Risks: a top-level key other than "env", "$schema" and a "model" equal to that model's
--model flag in rules/run_order.json; an env key starting with CLAUDE, ANTHROPIC_, DISABLE_, ENABLE_ or MAX_ that is
not in KEEP or SECRET_OK (for example CLAUDE_CODE_MAX_OUTPUT_TOKENS, DISABLE_AUTOUPDATER, MAX_THINKING_TOKENS).
Without risks it writes diag/models/<name>.json, in which a value is replaced by "<已隐去>" when its key name looks
secret (TOKEN, KEY, SECRET, PASS, AUTH, COOKIE, CREDENTIAL, HEADER, PRIVATE) or the value looks like a credential
("sk-" or "Bearer " prefix, or 32+ characters without spaces that are not a URL); every other value is kept. It also
writes diag/models/originals.sha256. It prints key names and kept values only; the author reads the copies before
committing them.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagpaths import DIAG, RULES, sha256_bytes, write_new_or_same  # noqa: E402

NAMES = ("claude", "kimi", "deepseek")
KEEP = {"ANTHROPIC_BASE_URL", "ANTHROPIC_MODEL", "ANTHROPIC_DEFAULT_OPUS_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL",
        "ANTHROPIC_DEFAULT_HAIKU_MODEL", "ANTHROPIC_SMALL_FAST_MODEL", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"}
SECRET_OK = {"ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY"}          # expected secret keys: hidden, not a risk
RISK_PREFIXES = ("CLAUDE", "ANTHROPIC_", "DISABLE_", "ENABLE_", "MAX_")
SECRET_NAME = re.compile(r"TOKEN|KEY|SECRET|PASS|AUTH|COOKIE|CREDENTIAL|HEADER|PRIVATE", re.I)
SECRET_VALUE = re.compile(r"^(?:sk-|Bearer\s)|^(?!https?://)\S{32,}$")
HIDDEN = "<已隐去>"


def redact(settings, model_flag=None):
    """Return (redacted dict, [risk descriptions with key names only])."""
    problems, out = [], {}
    for k, v in settings.items():
        if k == "$schema":
            out[k] = v
        elif k == "model" and v == model_flag:
            out[k] = v
        elif k != "env":
            problems.append(f"top-level key {k!r}")
    env = {}
    for k, v in (settings.get("env") or {}).items():
        if k.upper().startswith(RISK_PREFIXES) and k not in KEEP and k not in SECRET_OK:
            problems.append(f"env key {k!r} could change the run")
        secret = k in SECRET_OK or SECRET_NAME.search(k) or SECRET_VALUE.search(str(v))
        env[k] = HIDDEN if secret else v
    out["env"] = env
    return out, problems


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    argv = sys.argv[1:] if argv is None else argv
    src_dir = argv[0] if argv else os.path.join(os.path.expanduser("~"), ".diag-models")
    out_dir = argv[1] if len(argv) > 1 else os.path.join(DIAG, "models")
    with open(os.path.join(RULES, "run_order.json"), encoding="utf-8") as f:
        flags = {m["name"]: m["model"] for m in json.load(f)["models"]}
    copies, sums, all_problems = {}, [], []
    for name in NAMES:
        with open(os.path.join(src_dir, f"{name}.json"), "rb") as f:
            raw = f.read()
        sums.append(f"{sha256_bytes(raw)}  %USERPROFILE%/.diag-models/{name}.json\n")
        red, problems = redact(json.loads(raw.decode("utf-8-sig")), flags[name])
        all_problems += [f"{name}: {p}" for p in problems]
        copies[name] = red
        env = red["env"]
        print(f"{name}: kept {[(k, env[k]) for k in sorted(env) if env[k] != HIDDEN]}, "
              f"hidden {sorted(k for k in env if env[k] == HIDDEN)}")
    for p in all_problems:
        print(f"OVERRIDE RISK {p}")
    if all_problems:
        print(f"SETTINGS FAIL: {len(all_problems)} problem(s); nothing written")
        return 1
    for name, red in copies.items():
        write_new_or_same(os.path.join(out_dir, f"{name}.json"),
                          (json.dumps(red, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    write_new_or_same(os.path.join(out_dir, "originals.sha256"), "".join(sums).encode())
    print("SETTINGS OK: copies and originals.sha256 written; read the copies before committing them")
    return 0


if __name__ == "__main__":
    sys.exit(main())
