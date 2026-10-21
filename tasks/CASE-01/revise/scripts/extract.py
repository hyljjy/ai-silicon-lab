"""Answer parsing, candidate writing and prediction-table extraction (CASE-01 stage B, protocol 7.1 and 10.1).
Python standard library only; no subprocesses; works on Windows and in WSL.

The candidate RTL is produced only here, from the raw answer text, and nobody edits it afterwards (protocol 7)."""
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

from revpaths import CASE, sha256_bytes, write_new_or_same

__all__ = ["Parsed", "CandidateFiles", "ExtractError", "parse_answer", "write_candidate", "extracted_rows",
           "PREDICTION_COLUMNS"]

PREDICTION_COLUMNS = ("id action metric check corner category value_kind direction low high unit point "
                      "basis").split()
PREDICTION_HEADING = "预测表"
FAILURE_HEADING = "失败条件"

_OPEN_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_DECLARED = re.compile(r"DECLARED_L = ([0-9])")
_HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
_ITEM = re.compile(r"^ {0,3}(?:[-*+]|[0-9]{1,9}[.)])[ \t]+(.*)$")
_DELIM_CELL = re.compile(r"^:?-+:?$")
_CODE = re.compile(r"^[A-Za-z0-9_]+$")


class ExtractError(Exception):
    pass


@dataclass
class Parsed:
    status: str                                   # "ok" | "declined" | "delivery_fail"
    reason: Optional[str] = None                  # no_verilog_block unclosed_block no_declared_L
    #                                               conflicting_declared_L no_submission_with_code
    lines: List[int] = field(default_factory=list)
    # lines: 1-based line numbers of the OPENING and (when present) CLOSING fence of the first verilog block:
    # [open, close]; [open] when it is unclosed; [] when no verilog block was found.
    rtl: bytes = b""                              # LF-normalized block content (ok only)
    rtl_sha_raw: Optional[str] = None
    rtl_sha_lf: Optional[str] = None
    declared_L: Optional[int] = None
    unrun_blocks: List[str] = field(default_factory=list)
    predictions: List[dict] = field(default_factory=list)
    prediction_table_problem: Optional[str] = None
    failure_conditions: List[dict] = field(default_factory=list)
    prediction_L_mismatch: bool = False


@dataclass
class CandidateFiles:
    rtl_path: str
    cfg_path: str
    rtl_sha_raw: str
    rtl_sha_lf: str
    cfg_sha: str


def _split_lines(text):
    """Lines with their original line endings (LF or CRLF; a lone CR stays inside the line). Not str.splitlines:
    that also splits on form feed, vertical tab and Unicode separators, which are not line ends here."""
    return re.findall(r"[^\n]*\n|[^\n]+", text)


def _content(raw_line):
    """The line without its ending (one LF, then one CR)."""
    if raw_line.endswith("\n"):
        raw_line = raw_line[:-1]
    if raw_line.endswith("\r"):
        raw_line = raw_line[:-1]
    return raw_line


def _scan(raw_lines):
    """Fence scan. Returns (kinds, blocks): kinds[i] in "out" | "open" | "body" | "close"; blocks is a list of dicts
    {"verilog", "open", "close" (1-based line numbers; close None when unclosed), "body": [raw lines]} in order.

    Fence rule: an opening line is 0-3 spaces, then N >= 3 backticks or N tildes, then an info string (stripped; for
    a backtick fence it must not contain a backtick). A closing line is 0-3 spaces, the SAME character, at least N
    of them, then only whitespace. A verilog block is a backtick fence whose info string is exactly "verilog";
    every other fence is skipped as a whole by the same rule."""
    kinds = ["out"] * len(raw_lines)
    blocks = []
    i = 0
    while i < len(raw_lines):
        m = _OPEN_FENCE.match(_content(raw_lines[i]))
        if not m or (m.group(1)[0] == "`" and "`" in m.group(2)):
            i += 1
            continue
        fence, info = m.group(1), m.group(2).strip()
        ch, n = fence[0], len(fence)
        close_re = re.compile(r"^ {0,3}" + re.escape(ch) + "{" + str(n) + r",}[ \t\f\v]*$")
        blk = {"verilog": ch == "`" and info == "verilog", "open": i + 1, "close": None, "body": []}
        kinds[i] = "open"
        j = i + 1
        while j < len(raw_lines):
            if close_re.match(_content(raw_lines[j])):
                kinds[j] = "close"
                blk["close"] = j + 1
                break
            kinds[j] = "body"
            blk["body"].append(raw_lines[j])
            j += 1
        blocks.append(blk)
        i = j + 1
    return kinds, blocks


def _to_lf(text):
    return text.replace("\r\n", "\n").replace("\r", "\n")


def parse_answer(text: str, rnd: int) -> Parsed:
    """Parse the raw answer text (protocol 7.1).

    Block content = the raw lines strictly between the opening and the closing fence, concatenated with their
    ORIGINAL line endings. rtl_sha_raw is the sha256 of that content encoded as UTF-8, before any newline
    conversion; rtl (and rtl_sha_lf) is the content with CRLF and lone CR converted to LF, encoded as UTF-8.
    status is "ok" | "declined" | "delivery_fail"; predictions and failure conditions are extracted only for "ok"."""
    raw_lines = _split_lines(text)
    kinds, blocks = _scan(raw_lines)
    first = next((b for b in blocks if b["verilog"]), None)
    unrun = ["".join(b["body"]) for b in blocks if b is not first]

    declared, no_submission = [], False
    for i, raw in enumerate(raw_lines):
        if kinds[i] != "out":
            continue
        s = _content(raw).strip()
        if s.startswith(">"):
            continue
        m = _DECLARED.fullmatch(s)
        if m:
            declared.append(int(m.group(1)))
        elif s == "NO_SUBMISSION":
            no_submission = True
    no_submission = no_submission and rnd == 2        # in round 1 it has no effect
    lines = [] if first is None else [first["open"]] + ([first["close"]] if first["close"] else [])
    distinct = sorted(set(declared))
    decl = distinct[0] if len(distinct) == 1 else None

    def result(status, reason=None, **kw):
        return Parsed(status=status, reason=reason, lines=lines, declared_L=decl, unrun_blocks=unrun, **kw)

    if no_submission:
        if first is None:
            return result("declined")
        return result("delivery_fail", "no_submission_with_code")
    if first is None:
        return result("delivery_fail", "no_verilog_block")
    if first["close"] is None:
        return result("delivery_fail", "unclosed_block")
    if not distinct:
        return result("delivery_fail", "no_declared_L")
    if len(distinct) > 1:
        return result("delivery_fail", "conflicting_declared_L")

    block_text = "".join(first["body"])
    rtl = _to_lf(block_text).encode("utf-8")
    parsed = result("ok", rtl=rtl, rtl_sha_raw=sha256_bytes(block_text.encode("utf-8")),
                    rtl_sha_lf=sha256_bytes(rtl))
    parsed.predictions, parsed.prediction_table_problem = _predictions(raw_lines, kinds)
    parsed.failure_conditions = _failure_conditions(raw_lines, kinds)
    parsed.prediction_L_mismatch = _L_mismatch(parsed.predictions, decl)
    return parsed


def _heading(raw, kind):
    """(level, text) of an ATX heading line outside fences, else None."""
    if kind != "out":
        return None
    m = _HEADING.match(_content(raw))
    if not m:
        return None
    return len(m.group(1)), (m.group(2) or "").strip()


def _split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells, cur, i = [], [], 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur.append("|")
            i += 2
            continue
        if s[i] == "|":
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(s[i])
        i += 1
    cells.append("".join(cur).strip())
    return cells


def _is_delim(line):
    if "|" not in line and "-" not in line:
        return False
    cells = _split_row(line)
    return bool(cells) and all(_DELIM_CELL.match(c) for c in cells) and "-" in line


def _predictions(raw_lines, kinds):
    """The first Markdown table after the first heading whose text is exactly "预测表" (outside fences)."""
    start = None
    for i, raw in enumerate(raw_lines):
        h = _heading(raw, kinds[i])
        if h and h[1] == PREDICTION_HEADING:
            start = i + 1
            break
    if start is None:
        return [], "no_prediction_heading"
    i = start
    while i + 1 < len(raw_lines):
        head, nxt = _content(raw_lines[i]), _content(raw_lines[i + 1])
        if (kinds[i] == "out" and kinds[i + 1] == "out" and "|" in head and "|" in nxt and _is_delim(nxt)
                and len(_split_row(head)) == len(_split_row(nxt))):
            break
        i += 1
    else:
        return [], "no_prediction_table"
    cols = _split_row(_content(raw_lines[i]))
    want = set(PREDICTION_COLUMNS)
    if len(cols) != len(set(cols)) or set(cols) != want:
        missing, extra = sorted(want - set(cols)), sorted(set(cols) - want)
        dup = sorted({c for c in cols if cols.count(c) > 1})
        return [], f"bad_columns: missing={missing} extra={extra} duplicated={dup}"
    rows = []
    j = i + 2
    while j < len(raw_lines) and kinds[j] == "out" and "|" in _content(raw_lines[j]):
        cells = _split_row(_content(raw_lines[j]))
        if len(cells) != len(cols):
            return [], f"row_cell_count: row {len(rows) + 1}"
        rows.append(dict(zip(cols, cells)))
        j += 1
    if not rows:
        return [], "empty_table"
    return rows, None


def _failure_conditions(raw_lines, kinds):
    """List items after the first heading "失败条件" up to the next heading of the same or a higher level.
    A top-level item starts at 0-3 spaces; following non-blank lines indented by at least two spaces (including
    nested list markers) are continuation text, joined with LF. source is "line <n>" of the item's first line."""
    start = level = None
    for i, raw in enumerate(raw_lines):
        h = _heading(raw, kinds[i])
        if h and h[1] == FAILURE_HEADING:
            start, level = i + 1, h[0]
            break
    if start is None:
        return []
    items = []                                     # [first line number, [text lines]]
    open_item = False
    for i in range(start, len(raw_lines)):
        h = _heading(raw_lines[i], kinds[i])
        if h and h[0] <= level:
            break
        s = _content(raw_lines[i])
        m = _ITEM.match(s) if kinds[i] == "out" else None
        if m:
            items.append([i + 1, [m.group(1).strip()]])
            open_item = True
        elif open_item and s.strip() and re.match(r"^ {2,}\S", s):
            items[-1][1].append(s.strip())
        elif not s.strip():
            continue
        else:
            open_item = False
    return [{"fc_id": f"F{k}", "source": f"line {n}", "text": "\n".join(t)} for k, (n, t) in enumerate(items, 1)]


def _L_mismatch(predictions, declared):
    """True when some prediction row has metric L whose point is not the declared L (an unparsable point counts)."""
    for row in predictions:
        if row.get("metric") != "L":
            continue
        pt = row.get("point", "")
        if not re.fullmatch(r"[0-9]+", pt) or int(pt) != declared:
            return True
    return False


def write_candidate(code: str, parsed: Parsed, dest_root: str = CASE) -> CandidateFiles:
    """Write <dest_root>/rtl/dot4sat_<code>.v and <dest_root>/config/impl.<code>.cfg, both via write_new_or_same
    (an existing file must hold exactly these bytes). Only for status "ok". Smoke runs pass a dest_root under runs/."""
    if not isinstance(code, str) or not _CODE.match(code):
        raise ExtractError(f"bad candidate code {code!r}")
    if parsed.status != "ok" or parsed.declared_L is None or parsed.rtl_sha_lf is None:
        raise ExtractError(f"cannot write a candidate from status {parsed.status!r}")
    if sha256_bytes(parsed.rtl) != parsed.rtl_sha_lf:
        raise ExtractError("rtl bytes do not match rtl_sha_lf")
    rtl_path = os.path.join(dest_root, "rtl", f"dot4sat_{code}.v")
    cfg_path = os.path.join(dest_root, "config", f"impl.{code}.cfg")
    cfg = (f"name = {code}\ntop = dot4sat\nrtl = rtl/dot4sat_{code}.v\nL = {parsed.declared_L}\n").encode("utf-8")
    write_new_or_same(rtl_path, parsed.rtl)
    write_new_or_same(cfg_path, cfg)
    return CandidateFiles(rtl_path, cfg_path, parsed.rtl_sha_raw, parsed.rtl_sha_lf, sha256_bytes(cfg))


def extracted_rows(code, parsed):
    """Rows of r<r>_extracted.jsonl: one per prediction-table row (original fields, verbatim strings), one per
    failure condition, or one problem row when the table could not be extracted."""
    rows = []
    for k, p in enumerate(parsed.predictions, 1):
        rows.append({"code": code, "row_type": "prediction", "index": k, **p})
    if parsed.prediction_table_problem:
        rows.append({"code": code, "row_type": "prediction_table_problem",
                     "problem": parsed.prediction_table_problem})
    for fc in parsed.failure_conditions:
        rows.append({"code": code, "row_type": "failure_condition", **fc})
    return rows
