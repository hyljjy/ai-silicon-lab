"""Criteria, judgments and TSV views of CASE-01 stage B (implementation plan Task 7; protocol v0.4 sections 10.1,
10.2). Pure Python (standard library); no subprocess; Windows and WSL.

Criteria rows (revise/predictions/r<r>_criteria.jsonl, the only data source; one JSON object per line):
  common       candidate row_type source criteria_version
  prediction   prediction_id extract_index r1_ref id action metric check corner category value_kind direction low
               high unit point basis orientation epsilon source_field comparator  (all strings; extract_index is the
               decimal "index" of the extracted prediction row of the same candidate this row transcribes; the
               model's fields id .. basis are kept verbatim from that row; low / high / point are parsed only when
               judging)
  failure_condition  fc_id r1_ref text expr  (text verbatim from the extracted row with the same fc_id; expr a
               boolean expression, see eval3)
  One-to-one correspondence (Codex BC1-05; protocol 10.1 transcription, 10.2 repeated ids, 10.4 completeness),
  checked per candidate against r<r>_extracted.jsonl (correspondence_problems): every extracted prediction has
  exactly one criteria row (bound by extract_index) and every extracted failure condition exactly one (bound by
  fc_id); no criteria row is unbound or bound twice; a candidate's prediction rows, and its failure-condition rows,
  appear in the extracted order. So "only the first row of a repeated id is judged" follows the extracted order and
  cannot be changed by reordering criteria rows. Rows of different candidates, and a candidate's prediction and
  failure-condition rows, may interleave.
  orientation / epsilon / comparator must agree with revise/rules/metric_directions.json (the values used in
  judging always come from that file): slack increase 0.000001 decimal; area decrease 0.0001 decimal;
  L equal "" integer; function equal "" text. A row whose metric is not one of the four leaves them empty.
  r1_ref is "" in round 1.
  same_as (round >= 2, controller ruling R16; resolved after the correspondence): a prediction row whose id is
  "same_as=<X>" keeps id, action and basis verbatim from its own (extract_index) extracted row; its fields metric check corner category value_kind direction low high
  unit point are those of round rnd-1 extracted row X of the predecessor candidate (mapping prev_code) and are
  checked against that row; source must say it was resolved via same_as. X missing, no predecessor, a field that
  differs from X, or the model's own row filling a field differently from X: CRITERIA FAIL.
  Atoms with < <= == >= > need a finite decimal value (text comparisons use "is"): otherwise CRITERIA FAIL.

Boolean expressions: {"atom": {"field", "op": "<"|"<="|"=="|">="|">"|"is", "value": "<string>"}},
  {"untestable": "<text>"}, {"and": [..]}, {"or": [..]}, {"not": expr}. Fields: status.<status.json key>,
  matrix.<corner>.<setup|hold>.<scope>.slack (candidate cell), matrix.summary.<key>[.<key>] and
  matrix.extra.<key> (candidate side of revise/compare/r<r>_<code>.json). A value that is not_run / not_available /
  indeterminate / not_applicable, a missing field, or no compare document makes the atom unknown. "is" compares text
  (true / false for booleans); the other operators compare decimals (an operand that is not a finite decimal: unknown).

Judgment words: prediction parts 支持 / 反对 / 不判 (range also 格式问题); a row 支持 / 反对 / 未判定 / 无结果 / 不适用,
  and 格式问题 for a repeated id (only the first row of an id is judged); failure conditions 触发 / 未触发 / 未判定.
  For L and function the "range" part holds the point comparison (protocol 10.2: discrete, point only).

Files (relative to tasks/CASE-01):
  in   revise/predictions/r<r>_criteria.jsonl, r<r>_extracted.jsonl, revise/results/r<r>/<code>/status.json,
       revise/compare/r<r>_<code>.json (required when status sta_analysis is "pass"), r2_coverage.jsonl (views 2)
  out  run:   revise/predictions/r<r>_judgments.jsonl (criteria row + actual direction_judgment range_judgment
              judgment format_problems reason evidence) and r<r>_judgments.md
       views: revise/predictions/r<r>_criteria.tsv; round 2 also r2_coverage.tsv
  check=True recomputes and compares bytes with the files on disk, writes nothing ('CHECK FAIL ...').

Command line:  python3 -B revise/scripts/judge.py run|views <rnd> [--check]"""
import json
import os
import re
import sys
from decimal import Decimal, InvalidOperation

import baseline
import revpaths as rp

CORNERS = baseline.CORNERS
CHECKS = ("setup", "hold")
SCOPES = ("global", "in2reg", "reg2reg", "reg2out")
METRICS = ("slack", "area", "L", "function")
VALUE_KINDS = ("absolute", "delta")
UNKNOWN = "未知"
DIRECTIONS = {"改善": "better", "退化": "worse", "不变": "same", UNKNOWN: None}
UNITS = {"slack": ("ns",), "area": ("µm²", "μm²", "um²", "um^2", "um2", "µm^2", "μm^2")}
SENTINELS = ("not_run", "not_available", "indeterminate", "not_applicable")
NO_RESULT, NOT_APPLICABLE, UNKNOWN_OBJECT = "no_result", "not_applicable", "unknown_object"
COMPARATOR = {"slack": "decimal", "area": "decimal", "L": "integer", "function": "text"}
OPS = ("<", "<=", "==", ">=", ">", "is")

COMMON_FIELDS = ("candidate", "row_type", "source", "criteria_version")
EXTRACTED_PREDICTION_COLUMNS = ("id action metric check corner category value_kind direction low high unit point "
                                "basis").split()
PREDICTION_FIELDS = ("prediction_id extract_index r1_ref id action metric check corner category value_kind direction low high "
                     "unit point basis orientation epsilon source_field comparator").split()
FC_FIELDS = ("fc_id", "r1_ref", "text", "expr")
CRITERIA_COLUMNS = tuple(COMMON_FIELDS) + tuple(PREDICTION_FIELDS) + ("fc_id", "text", "expr")
JUDGMENT_FIELDS = ("actual", "direction_judgment", "range_judgment", "judgment", "format_problems", "reason",
                   "evidence")
PRED_WORDS = ("支持", "反对", "未判定", "无结果", "不适用", "格式问题")
FC_WORDS = ("触发", "未触发", "未判定")

SAME_AS = re.compile(r"same_as\s*=\s*(\S+)")
EXTRACT_INDEX = re.compile(r"[1-9][0-9]*")
SAME_AS_FIELDS = ("metric check corner category value_kind direction low high unit point").split()
_MATRIX_CELL = re.compile(r"^matrix\.([^.]+)\.(setup|hold)\.([^.]+)\.slack$")


class JudgeError(Exception):
    pass


# ---------------------------------------------------------------------------------------------- helpers
def _s(row, key):
    v = row.get(key)
    return v.strip() if isinstance(v, str) else ""


def _dec(v):
    """Finite Decimal from a Decimal, an int (not bool) or a decimal string; else None."""
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return Decimal(v)
    if isinstance(v, Decimal):
        return v if v.is_finite() else None
    if isinstance(v, str) and v not in SENTINELS:
        try:
            d = Decimal(v.strip())
        except InvalidOperation:
            return None
        return d if d.is_finite() else None
    return None


def _dec_out(v):
    return format(v, "f") if isinstance(v, Decimal) else v


def _show(v):
    if isinstance(v, Decimal):
        return rp.fmt6(v)
    if isinstance(v, bool):
        return "true" if v else "false"
    return "" if v is None else str(v)


def _parse(row):
    """(info, problems). info: metric, object_ok, check, corner, category, value_kind, direction (better / worse /
    same / None), low, high (Decimal or None), range_bad (low > high), point (L: int, function: text, else None)."""
    probs = []
    info = {"metric": None, "object_ok": False, "check": None, "corner": None, "category": None,
            "value_kind": None, "direction": None, "low": None, "high": None, "range_bad": False, "point": None}
    metric = _s(row, "metric")
    if metric not in METRICS:
        probs.append(f"metric {row.get('metric')!r} 不在允许取值内（{' / '.join(METRICS)}）")
        return info, probs
    info["metric"] = metric
    ok = True
    if metric == "slack":
        for key, allowed in (("check", CHECKS), ("corner", ("all",) + CORNERS), ("category", SCOPES)):
            v = _s(row, key)
            if v in allowed:
                info[key] = v
            else:
                probs.append(f"{key} {row.get(key)!r} 不在允许取值内")
                ok = False
    if metric in ("slack", "area"):
        vk = _s(row, "value_kind")
        if vk in VALUE_KINDS:
            info["value_kind"] = vk
        else:
            probs.append(f"value_kind {row.get('value_kind')!r} 不在允许取值内（absolute / delta）")
            ok = False
        d = _s(row, "direction")
        if d in DIRECTIONS:
            info["direction"] = DIRECTIONS[d]
        else:
            probs.append(f"direction {row.get('direction')!r} 不在允许取值内（改善 / 退化 / 不变 / 未知），视为未知")
        bounds = {}
        for key in ("low", "high"):
            v = _s(row, key)
            if v == UNKNOWN:
                bounds[key] = None
                continue
            d = None
            if re.fullmatch(r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?", v):
                d = _dec(v)
            if d is None:
                probs.append(f"{key} {row.get(key)!r} 不是有限数，视为未知")
            bounds[key] = d
        unit = _s(row, "unit")
        unit_ok = unit in UNITS[metric]
        if not unit_ok and unit not in ("", UNKNOWN):
            probs.append(f"unit {row.get('unit')!r} 不明（{metric} 应为 {' / '.join(UNITS[metric])}）")
        if (bounds["low"] is not None or bounds["high"] is not None) and not unit_ok:
            if unit in ("", UNKNOWN):
                probs.append(f"unit {row.get('unit')!r} 不明，范围视为未知")
            bounds = {"low": None, "high": None}
        info["low"], info["high"] = bounds["low"], bounds["high"]
        if info["low"] is not None and info["high"] is not None and info["low"] > info["high"]:
            probs.append(f"low {row.get('low')!r} > high {row.get('high')!r}，范围不判")
            info["range_bad"] = True
    elif metric == "L":
        pt = _s(row, "point")
        if re.fullmatch(r"[0-9]+", pt):
            info["point"] = int(pt)
        else:
            probs.append(f"point {row.get('point')!r} 不是整数（metric L），视为未知")
    else:
        pt = _s(row, "point")
        if pt in ("pass", "fail"):
            info["point"] = pt
        else:
            probs.append(f"point {row.get('point')!r} 不是 pass / fail（metric function），视为未知")
    info["object_ok"] = ok
    return info, probs


def format_problems(row):
    """Field format problems of one prediction row (protocol 10.2); each such field is only treated as unknown."""
    return _parse(row)[1]


# ---------------------------------------------------------------------------------------------- matrix access
def _cell_index(matrix):
    if not isinstance(matrix, dict) or not isinstance(matrix.get("cells"), list):
        return None
    idx = {}
    for x in matrix["cells"]:
        if isinstance(x, dict):
            idx[(x.get("corner"), x.get("check"), x.get("scope"))] = x
    return idx


def _cell_slack(cell, side):
    part = cell.get(side) if isinstance(cell, dict) else None
    v = part.get("slack") if isinstance(part, dict) else None
    if v == NOT_APPLICABLE:
        return NOT_APPLICABLE
    d = _dec(v)
    if d is None:
        raise JudgeError(f"compare document: cell {cell.get('corner')}/{cell.get('check')}/{cell.get('scope')} "
                         f"{side}.slack {v!r} is neither a number nor not_applicable")
    return d


def _cell_field(corner, check, scope, side):
    return f"cells[{corner},{check},{scope}].{side}.slack"


def actual_with_evidence(row, status, matrix):
    """(value, evidence): value Decimal / int / "pass" / "fail" or no_result / not_applicable / unknown_object;
    evidence [(source label "status" | "matrix" | "baseline", field)]."""
    info, _ = _parse(row)
    if not info["object_ok"]:
        return UNKNOWN_OBJECT, []
    status = status if isinstance(status, dict) else {}
    metric = info["metric"]
    if metric == "function":
        r, g = status.get("rtl_sim"), status.get("gl_sim")
        ev = [("status", "rtl_sim"), ("status", "gl_sim")]
        if r == "pass" and g == "pass":
            return "pass", ev
        if "fail" in (r, g):
            return "fail", ev
        return NO_RESULT, ev
    if metric == "L":
        v = status.get("cfg_L")
        ok = isinstance(v, int) and not isinstance(v, bool)
        return (v if ok else NO_RESULT), [("status", "cfg_L")]
    if metric == "area":
        ev = [("status", "area_um2")]
        cand = _dec(status.get("area_um2"))
        if cand is None:
            return NO_RESULT, ev
        if info["value_kind"] == "absolute":
            return cand, ev
        base, label, field = None, "matrix", "baseline.extra.area"
        if isinstance(matrix, dict) and isinstance(matrix.get("baseline"), dict):
            base = _dec((matrix["baseline"].get("extra") or {}).get("area"))
            if matrix.get("_baseline_file"):
                label, field = "baseline", "area_um2"
        ev.append((label, field))
        if base is None:
            return NO_RESULT, ev
        return cand - base, ev
    # slack
    ev = [("status", "sta_analysis")]
    idx = _cell_index(matrix)
    if status.get("sta_analysis") != "pass" or idx is None:
        return NO_RESULT, ev
    corners = CORNERS if info["corner"] == "all" else (info["corner"],)
    cand_vals, base_vals = [], []
    for c in corners:
        key = (c, info["check"], info["category"])
        if key not in idx:
            raise JudgeError(f"compare document has no cell {key}")
        cand_vals.append(_cell_slack(idx[key], "cand"))
        ev.append(("matrix", _cell_field(*key, "cand")))
    cand = [v for v in cand_vals if v != NOT_APPLICABLE]
    if not cand:
        return NOT_APPLICABLE, ev
    if info["value_kind"] == "absolute":
        return min(cand), ev
    for c in corners:
        key = (c, info["check"], info["category"])
        base_vals.append(_cell_slack(idx[key], "base"))
        ev.append(("matrix", _cell_field(*key, "base")))
    base = [v for v in base_vals if v != NOT_APPLICABLE]
    if not base:
        return NOT_APPLICABLE, ev
    return min(cand) - min(base), ev


def actual(row, status, matrix):
    """The row's actual value by value_kind (protocol 10.1, 10.2); see actual_with_evidence."""
    return actual_with_evidence(row, status, matrix)[0]


# ---------------------------------------------------------------------------------------------- judgments
def direction_judgment(row, actual_delta):
    info, _ = _parse(row)
    if info["metric"] not in ("slack", "area") or info["direction"] is None or not isinstance(actual_delta, Decimal):
        return "不判"
    spec = rp.directions()[info["metric"]]
    signed = actual_delta if spec["better"] == "increase" else -actual_delta
    if signed > spec["epsilon"]:
        cls = "better"
    elif signed < -spec["epsilon"]:
        cls = "worse"
    else:
        cls = "same"
    return "支持" if cls == info["direction"] else "反对"


def range_judgment(row, value):
    info, _ = _parse(row)
    metric = info["metric"]
    if metric == "L":
        if info["point"] is None or not isinstance(value, int) or isinstance(value, bool):
            return "不判"
        return "支持" if value == info["point"] else "反对"
    if metric == "function":
        if info["point"] is None or value not in ("pass", "fail"):
            return "不判"
        return "支持" if value == info["point"] else "反对"
    if metric not in ("slack", "area"):
        return "不判"
    if info["range_bad"]:
        return "格式问题"
    if info["low"] is None and info["high"] is None:
        return "不判"
    if not isinstance(value, Decimal):
        return "不判"
    if info["low"] is not None and value < info["low"]:
        return "反对"
    if info["high"] is not None and value > info["high"]:
        return "反对"
    return "支持"


def combine(dir_j, range_j, actual_value):
    if actual_value == NO_RESULT:
        return "无结果"
    if actual_value == NOT_APPLICABLE:
        return "不适用"
    parts = [j for j in (dir_j, range_j) if j in ("支持", "反对")]
    if "反对" in parts:
        return "反对"
    if parts:
        return "支持"
    return "未判定"


# ---------------------------------------------------------------------------------------------- expressions
def expr_problems(expr, where="expr"):
    """Structural problems of a boolean expression (empty list: well formed)."""
    if not isinstance(expr, dict) or len(expr) != 1:
        return [f"{where}: expected an object with exactly one key, got {expr!r}"]
    (k, v), = expr.items()
    if k == "atom":
        if not isinstance(v, dict) or set(v) != {"field", "op", "value"}:
            return [f"{where}.atom: expected keys field, op, value"]
        probs = []
        if v["op"] not in OPS:
            probs.append(f"{where}.atom: op {v['op']!r} not one of {' '.join(OPS)}")
        if not isinstance(v["value"], str):
            probs.append(f"{where}.atom: value must be a string")
        elif v["op"] in OPS and v["op"] != "is" and _dec(v["value"]) is None:
            probs.append(f"{where}.atom: op {v['op']} needs a finite decimal value, not {v['value']!r} "
                         f"(use \"is\" for text)")
        f = v["field"]
        ok = isinstance(f, str) and (
            re.fullmatch(r"status\.[^.\s]+", f) or re.fullmatch(r"matrix\.(summary|extra)(\.[^.\s]+)+", f)
            or (_MATRIX_CELL.match(f) and _MATRIX_CELL.match(f).group(1) in CORNERS
                and _MATRIX_CELL.match(f).group(3) in SCOPES))
        if not ok:
            probs.append(f"{where}.atom: field {f!r} is not in the namespaces status.<key>, "
                         f"matrix.<corner>.<setup|hold>.<scope>.slack, matrix.summary.<key>, matrix.extra.<key>")
        return probs
    if k == "untestable":
        return [] if isinstance(v, str) else [f"{where}.untestable: expected a string"]
    if k in ("and", "or"):
        if not isinstance(v, list) or not v:
            return [f"{where}.{k}: expected a non-empty list"]
        out = []
        for i, e in enumerate(v):
            out += expr_problems(e, f"{where}.{k}[{i}]")
        return out
    if k == "not":
        return expr_problems(v, f"{where}.not")
    return [f"{where}: unknown key {k!r}"]


def _fetch(field, status, matrix):
    """(value or None when unknown, (label, field) evidence)."""
    if field.startswith("status."):
        key = field[len("status."):]
        ev = ("status", key)
        v = status.get(key) if isinstance(status, dict) else None
    else:
        m = _MATRIX_CELL.match(field)
        cand = matrix.get("candidate") if isinstance(matrix, dict) else None
        if m:
            ev = ("matrix", _cell_field(m.group(1), m.group(2), m.group(3), "cand"))
            idx = _cell_index(matrix)
            cell = idx.get((m.group(1), m.group(2), m.group(3))) if idx else None
            part = cell.get("cand") if isinstance(cell, dict) else None
            v = part.get("slack") if isinstance(part, dict) else None
        else:
            path = field.split(".")[1:]                    # summary|extra, keys...
            ev = ("matrix", "candidate." + ".".join(path))
            v = cand
            for p in path:
                v = v.get(p) if isinstance(v, dict) else None
    if v is None or (isinstance(v, str) and v in SENTINELS):
        return None, ev
    return v, ev


def _text(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, Decimal):
        return format(v, "f")
    if isinstance(v, (str, int)):
        return str(v)
    return json.dumps(v, ensure_ascii=False, default=_dec_out)


def eval3_with_evidence(expr, status, matrix):
    """(True | False | None, evidence list) by the three-valued logic of protocol 10.2."""
    ev = []

    def rec(e):
        (k, v), = e.items()
        if k == "untestable":
            return None
        if k == "atom":
            val, where = _fetch(v["field"], status, matrix)
            ev.append(where)
            if val is None:
                return None
            if v["op"] == "is":
                return _text(val) == v["value"]
            a, b = _dec(val), _dec(v["value"])
            if a is None or b is None:
                return None
            return {"<": a < b, "<=": a <= b, "==": a == b, ">=": a >= b, ">": a > b}[v["op"]]
        if k == "not":
            r = rec(v)
            return None if r is None else not r
        rs = [rec(x) for x in v]
        if k == "and":
            return False if False in rs else (True if all(r is True for r in rs) else None)
        return True if True in rs else (False if all(r is False for r in rs) else None)

    probs = expr_problems(expr)
    if probs:
        raise JudgeError("; ".join(probs))
    return rec(expr), ev


def eval3(expr, status, matrix):
    return eval3_with_evidence(expr, status, matrix)[0]


# ---------------------------------------------------------------------------------------------- one row
def judge_row(row, status, matrix):
    """The judgment fields of one criteria row (evidence as (label, field) pairs; run maps labels to files).
    Repeated ids are handled by run."""
    if row.get("row_type") == "failure_condition":
        val, ev = eval3_with_evidence(row["expr"], status, matrix)
        word = {True: "触发", False: "未触发", None: "未判定"}[val]
        return {"actual": {True: "true", False: "false", None: "unknown"}[val], "direction_judgment": None,
                "range_judgment": None, "judgment": word, "format_problems": [],
                "reason": f"布尔式三值结果为{ {True: '真', False: '假', None: '未知'}[val] }", "evidence": ev}
    info, probs = _parse(row)
    value, ev = actual_with_evidence(row, status, matrix)
    dir_j, delta = "不判", None
    if info["metric"] in ("slack", "area") and info["object_ok"]:
        if info["value_kind"] == "delta":
            delta = value
        else:
            delta, ev2 = actual_with_evidence(dict(row, value_kind="delta"), status, matrix)
            ev += [e for e in ev2 if e not in ev]
        dir_j = direction_judgment(row, delta)
    rng_j = range_judgment(row, value)
    word = combine(dir_j, rng_j, value)
    reason = []
    if value == UNKNOWN_OBJECT:
        reason.append("对象字段无法解析，不判")
    elif value == NO_RESULT:
        reason.append("所需字段没有有效结果（未执行、不可用或不确定）")
    elif value == NOT_APPLICABLE:
        reason.append("预测的对象在候选或基线中不存在")
    else:
        reason.append(f"实际值 {_show(value)}")
        if info["metric"] in ("slack", "area"):
            if isinstance(delta, Decimal):
                reason.append(f"相对 F1 基线的变化 {_show(delta)}")
            reason.append(f"方向 {_s(row, 'direction') or '（空）'}：{dir_j}")
            reason.append(f"范围 [{_s(row, 'low')}, {_s(row, 'high')}]：{rng_j}")
            if _s(row, "point"):
                reason.append(f"点估计 {_s(row, 'point')} 不判")
        else:
            reason.append(f"点 {_s(row, 'point')}：{rng_j}")
    if info["metric"] == "L" and isinstance(status, dict) and status.get("prediction_L_mismatch") is True:
        reason.append("预测不一致：预测表中的 L 与 DECLARED_L 不一致，照常按 cfg_L 判定")
    return {"actual": value, "direction_judgment": dir_j, "range_judgment": rng_j, "judgment": word,
            "format_problems": probs, "reason": "；".join(reason), "evidence": ev}


def summary_counts(rows):
    counts = {w: 0 for w in PRED_WORDS + FC_WORDS[:2]}
    for r in rows:
        w = r.get("judgment")
        counts[w] = counts.get(w, 0) + 1
    return counts


# ---------------------------------------------------------------------------------------------- files
def read_jsonl(path):
    try:
        text = rp.read_bytes(path).decode("utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise JudgeError(f"{path} cannot be read ({e.__class__.__name__})")
    if text and not text.endswith("\n"):
        raise JudgeError(f"{path}: the last line does not end with LF")
    rows = []
    for n, line in enumerate(text.split("\n")[:-1] if text else [], 1):
        try:
            obj = json.loads(line, parse_float=Decimal)
        except ValueError as e:
            raise JudgeError(f"{path}: line {n} is not JSON ({e})")
        if not isinstance(obj, dict):
            raise JudgeError(f"{path}: line {n} is not a JSON object")
        rows.append(obj)
    return rows


def ref_of(row):
    return row.get("prediction_id") if row.get("row_type") == "prediction" else row.get("fc_id")


def prev_fn(prev, rnd=2):
    """{code: previous code} dict or callable as given; None -> mapping.prev_code on mapping.load(rnd)."""
    if callable(prev):
        return prev
    if isinstance(prev, dict):
        return prev.get
    import mapping                                         # only when the real mapping is needed
    m = mapping.load(rnd)
    return lambda c: mapping.prev_code(m, c)


def _same_as_problems(r, where, x, rnd, bound, prev_extracted, prev, cache):
    """Round >= 2 row whose id is same_as=<x>: id, action and basis verbatim from its own extracted row `bound` (the
    row named by extract_index; None: unbound, reported by correspondence_problems); the object and criterion fields
    SAME_AS_FIELDS equal round rnd-1 extracted row x of the predecessor candidate."""
    probs = []
    own = []
    if bound is not None:
        if all(bound.get(c) == r[c] for c in ("id", "action", "basis")):
            own = [bound]
        else:
            probs.append(f"{where}: extracted prediction index {r['extract_index']} of {r['candidate']} does not "
                         f"have exactly this id, action and basis (kept verbatim)")
    if "same_as" not in r["source"]:
        probs.append(f"{where}: source must record that the row was resolved via same_as")
    if "fn" not in cache:
        try:
            cache["fn"] = prev_fn(prev, rnd)
        except Exception as e:                             # mapping.MappingError and file errors
            cache["fn"] = None
            cache["err"] = str(e)
    if cache["fn"] is None:
        probs.append(f"{where}: same_as cannot be resolved: the round-{rnd} mapping cannot be loaded "
                     f"({cache.get('err')})")
        return probs
    try:
        pc = cache["fn"](r["candidate"])
    except Exception:
        pc = None
    if not pc:
        probs.append(f"{where}: same_as cannot be resolved: {r['candidate']} has no predecessor candidate")
        return probs
    if prev_extracted is None:
        probs.append(f"{where}: same_as cannot be resolved: r{rnd - 1}_extracted.jsonl is not available")
        return probs
    xs = [e for e in prev_extracted if e.get("row_type") == "prediction" and e.get("code") == pc
          and isinstance(e.get("id"), str) and e["id"].strip() == x]
    if not xs:
        probs.append(f"{where}: same_as={x}: round {rnd - 1} candidate {pc} has no extracted prediction {x!r}")
        return probs
    src = xs[0]
    diff = [c for c in SAME_AS_FIELDS if r[c] != src.get(c)]
    if diff:
        probs.append(f"{where}: same_as={x}: fields {' '.join(diff)} differ from round {rnd - 1} extracted row {x} "
                     f"of {pc} (they are carried verbatim)")
    for e in own:
        clash = [c for c in SAME_AS_FIELDS if (e.get(c) or "").strip() and e.get(c) != src.get(c)]
        if clash:
            probs.append(f"{where}: same_as={x}: the model's own row fills {' '.join(clash)} differently from {x}")
    return probs


def _index_key(v):
    """The extracted row's index as the decimal string extract_index must equal (None: not a positive int)."""
    return str(v) if isinstance(v, int) and not isinstance(v, bool) and v >= 1 else None


def _extracted_by_code(extracted):
    """({code: [(index string, row)]}, {code: [(fc_id, row)]}, problems), each list in the extracted order."""
    preds, fcs, probs = {}, {}, []
    for n, e in enumerate(extracted, 1):
        code, rt = e.get("code"), e.get("row_type")
        if rt == "prediction":
            k = _index_key(e.get("index"))
            if k is None:
                probs.append(f"extracted row {n}: prediction of {code} has index {e.get('index')!r}, not a positive "
                             f"integer")
                continue
            if any(k == j for j, _ in preds.get(code, [])):
                probs.append(f"extracted row {n}: prediction index {k} of {code} is repeated")
                continue
            preds.setdefault(code, []).append((k, e))
        elif rt == "failure_condition":
            f = e.get("fc_id")
            if not isinstance(f, str) or not f:
                probs.append(f"extracted row {n}: failure condition of {code} has no fc_id")
                continue
            if any(f == j for j, _ in fcs.get(code, [])):
                probs.append(f"extracted row {n}: failure condition {f} of {code} is repeated")
                continue
            fcs.setdefault(code, []).append((f, e))
    return preds, fcs, probs


def correspondence_problems(rows, extracted, codes=None):
    """One-to-one correspondence of criteria rows and extracted rows per candidate (Codex BC1-05; see the module
    doc). rows: criteria rows (need not be otherwise valid); extracted: r<r>_extracted.jsonl rows; codes: the
    candidates to check (None: every candidate of either file)."""
    preds, fcs, probs = _extracted_by_code(extracted)
    crit_p, crit_f = {}, {}
    for n, r in enumerate(rows, 1):
        if not isinstance(r, dict):
            continue
        rt, code = r.get("row_type"), r.get("candidate")
        if rt == "prediction":
            crit_p.setdefault(code, []).append((n, r.get("extract_index"), r.get("prediction_id")))
        elif rt == "failure_condition":
            crit_f.setdefault(code, []).append((n, r.get("fc_id"), r.get("fc_id")))
    every = set(preds) | set(fcs) | set(crit_p) | set(crit_f)
    want = every if codes is None else every & set(codes)
    for code in sorted(want, key=str):
        for kind, ext, crit, key_name in (
                ("prediction", preds.get(code, []), crit_p.get(code, []), "extract_index"),
                ("failure condition", fcs.get(code, []), crit_f.get(code, []), "fc_id")):
            pos = {k: i for i, (k, _) in enumerate(ext)}
            bound, order = {}, []
            for n, key, ref in crit:
                if not isinstance(key, str) or key not in pos:
                    probs.append(f"criteria row {n}: {key_name} {key!r} names no {kind} of {code} in the extracted "
                                 f"rows")
                    continue
                bound.setdefault(key, []).append((n, ref))
                order.append(pos[key])
            for k, e in ext:
                what = (f"extracted prediction index {k} (id {e.get('id')!r})" if kind == "prediction"
                        else f"extracted failure condition {k}")
                got = bound.get(k, [])
                if not got:
                    probs.append(f"{code}: {what} has no criteria row (every extracted {kind} is transcribed "
                                 f"exactly once)")
                elif len(got) > 1:
                    probs.append(f"{code}: {what} is transcribed by {len(got)} criteria rows "
                                 f"({', '.join(f'row {n} {ref!r}' for n, ref in got)}; exactly one required)")
            if any(b <= a for a, b in zip(order, order[1:])):
                probs.append(f"{code}: the {kind} criteria rows are not in the extracted order ({key_name} sequence "
                             f"{' '.join(ext[i][0] for i in order)}; extracted {' '.join(k for k, _ in ext)})")
    return probs


def criteria_problems(rows, rnd, extracted=None, prev_extracted=None, prev=None):
    """Problems of the criteria rows of round rnd; extracted: the r<rnd>_extracted.jsonl rows (one-to-one
    correspondence, then each row checked verbatim against the extracted row it is bound to);
    prev_extracted: the r<rnd-1>_extracted.jsonl rows and prev: the code mapping (see prev_fn), both used only to
    resolve same_as=<X> rows (protocol 10.1, 10.4)."""
    probs = []
    cache = {}
    dirs = rp.directions()
    seen_pid, seen_ref = set(), set()
    ext_pred, ext_fc, _ = _extracted_by_code(extracted or [])
    if extracted is not None:
        probs += correspondence_problems(rows, extracted)
    for n, r in enumerate(rows, 1):
        where = f"criteria row {n}"
        rt = r.get("row_type")
        if rt == "prediction":
            want = tuple(COMMON_FIELDS) + tuple(PREDICTION_FIELDS)
        elif rt == "failure_condition":
            want = tuple(COMMON_FIELDS) + tuple(FC_FIELDS)
        else:
            probs.append(f"{where}: row_type {rt!r} is not prediction / failure_condition")
            continue
        if list(r) != list(want):
            probs.append(f"{where}: fields must be exactly, in order: {' '.join(want)}")
            continue
        bad = [k for k in want if k != "expr" and not isinstance(r[k], str)]
        if bad:
            probs.append(f"{where}: fields must be strings: {' '.join(bad)}")
            continue
        if not r["candidate"] or not r["criteria_version"]:
            probs.append(f"{where}: candidate and criteria_version must not be empty")
        if rnd == 1 and r["r1_ref"]:
            probs.append(f"{where}: r1_ref must be empty in round 1")
        ref = ref_of(r)
        if not ref:
            probs.append(f"{where}: {'prediction_id' if rt == 'prediction' else 'fc_id'} must not be empty")
        elif (r["candidate"], ref) in seen_ref:
            probs.append(f"{where}: reference {ref!r} repeated for candidate {r['candidate']}")
        seen_ref.add((r["candidate"], ref))
        if rt == "prediction":
            if ref in seen_pid:
                probs.append(f"{where}: prediction_id {ref!r} repeated")
            seen_pid.add(ref)
            if not EXTRACT_INDEX.fullmatch(r["extract_index"]):
                probs.append(f"{where}: extract_index {r['extract_index']!r} must be the decimal index of the "
                             f"extracted prediction row it transcribes")
            bound = dict(ext_pred.get(r["candidate"], [])).get(r["extract_index"])
            metric = _s(r, "metric")
            if metric in METRICS:
                spec = dirs.get(metric)
                if spec is None:
                    probs.append(f"{where}: metric {metric} missing from metric_directions.json")
                else:
                    want_o = spec.get("better", "equal")
                    eps_ok = (r["epsilon"] == "" if "epsilon" not in spec else
                              (_dec(r["epsilon"]) is not None and _dec(r["epsilon"]) == spec["epsilon"]))
                    if r["orientation"] != want_o or not eps_ok or r["comparator"] != COMPARATOR[metric]:
                        probs.append(f"{where}: orientation / epsilon / comparator {r['orientation']!r} "
                                     f"{r['epsilon']!r} {r['comparator']!r} disagree with metric_directions.json "
                                     f"({want_o} {spec.get('epsilon', '')} {COMPARATOR[metric]})")
            elif r["orientation"] or r["epsilon"] or r["comparator"]:
                probs.append(f"{where}: metric {metric!r} is not judged; orientation / epsilon / comparator must be "
                             f"empty")
            same_as = SAME_AS.fullmatch(_s(r, "id"))
            if same_as and rnd >= 2:
                probs += _same_as_problems(r, where, same_as.group(1), rnd, bound, prev_extracted, prev, cache)
            elif bound is not None and not all(bound.get(c) == r[c] for c in EXTRACTED_PREDICTION_COLUMNS):
                probs.append(f"{where}: extracted prediction index {r['extract_index']} of {r['candidate']} does not "
                             f"have exactly these fields {' '.join(EXTRACTED_PREDICTION_COLUMNS)} (they are kept "
                             f"verbatim)")
        else:
            probs += expr_problems(r["expr"], f"{where}.expr")
            bound = dict(ext_fc.get(r["candidate"], [])).get(r["fc_id"])
            if bound is not None and bound.get("text") != r["text"]:
                probs.append(f"{where}: extracted failure condition {r['fc_id']} of {r['candidate']} does not have "
                             f"exactly this text (kept verbatim)")
    return probs


def _paths(case, rnd):
    pred = os.path.join(case, "revise", "predictions")
    return {"criteria": os.path.join(pred, f"r{rnd}_criteria.jsonl"),
            "extracted": os.path.join(pred, f"r{rnd}_extracted.jsonl"),
            "tsv": os.path.join(pred, f"r{rnd}_criteria.tsv"),
            "judgments": os.path.join(pred, f"r{rnd}_judgments.jsonl"),
            "md": os.path.join(pred, f"r{rnd}_judgments.md"),
            "coverage": os.path.join(pred, "r2_coverage.jsonl"),
            "coverage_tsv": os.path.join(pred, "r2_coverage.tsv")}


def load_criteria(case, rnd, prev=None):
    """Validated criteria rows of round rnd (JudgeError with every problem). same_as rows (round >= 2) also read
    r<rnd-1>_extracted.jsonl and the code mapping (prev, see prev_fn)."""
    p = _paths(case, rnd)
    rows = read_jsonl(p["criteria"])
    extracted = read_jsonl(p["extracted"])
    prev_extracted = None
    if rnd >= 2 and any(r.get("row_type") == "prediction" and SAME_AS.fullmatch(_s(r, "id")) for r in rows):
        prev_extracted = read_jsonl(_paths(case, rnd - 1)["extracted"])
    probs = criteria_problems(rows, rnd, extracted, prev_extracted, prev)
    if probs:
        raise JudgeError("; ".join(probs))
    return rows


def _rel(case, path):
    return os.path.relpath(path, case).replace(os.sep, "/")


def load_candidate(case, rnd, code, base_root=None, need_baseline_area=False):
    """(status, matrix, files): files maps the evidence labels to paths relative to tasks/CASE-01.
    status.json must exist; the compare document must exist when sta_analysis is "pass". Without a compare document
    and with need_baseline_area, matrix carries only the F1 baseline area (read after baseline.verify)."""
    sp = os.path.join(case, "revise", "results", f"r{rnd}", code, "status.json")
    mp = os.path.join(case, "revise", "compare", f"r{rnd}_{code}.json")
    if not os.path.isfile(sp):
        raise JudgeError(f"{_rel(case, sp)} is missing")
    try:
        st = rp.load_json_decimal(sp)
    except (OSError, ValueError) as e:
        raise JudgeError(f"{_rel(case, sp)} cannot be read ({e.__class__.__name__})")
    files = {"status": _rel(case, sp), "matrix": _rel(case, mp)}
    mx = None
    if os.path.isfile(mp):
        try:
            mx = rp.load_json_decimal(mp)
        except (OSError, ValueError) as e:
            raise JudgeError(f"{_rel(case, mp)} cannot be read ({e.__class__.__name__})")
    elif isinstance(st, dict) and st.get("sta_analysis") == "pass":
        raise JudgeError(f"{_rel(case, mp)} is missing although sta_analysis is pass")
    elif need_baseline_area:
        probs = baseline.verify(base_root)
        if probs:
            raise JudgeError("; ".join(probs))
        vp = baseline.source(base_root)["verdict"]
        try:
            v = rp.load_json_decimal(vp)
        except (OSError, ValueError) as e:
            raise JudgeError(f"baseline verdict.json cannot be read ({e.__class__.__name__}: {e})")
        if not isinstance(v, dict) or _dec(v.get("area_um2")) is None:
            raise JudgeError("baseline verdict.json has no numeric area_um2")
        mx = {"baseline": {"extra": {"area": v.get("area_um2")}}, "_baseline_file": True}
        files["baseline"] = f"evidence/F1/archive/{baseline.RUN}/verdict.json"
    return st, mx, files


def judgment_rows(case, rnd, base_root=None, prev=None):
    rows = load_criteria(case, rnd, prev)
    cache = {}
    out = []
    seen = set()
    for r in rows:
        code = r["candidate"]
        need_area = (r["row_type"] == "prediction" and _s(r, "metric") == "area")
        key = (code, need_area)
        if key not in cache:
            cache[key] = load_candidate(case, rnd, code, base_root, need_area)
        st, mx, files = cache[key]
        if r["row_type"] == "prediction" and (code, _s(r, "id")) in seen:
            res = {"actual": None, "direction_judgment": "不判", "range_judgment": "不判", "judgment": "格式问题",
                   "format_problems": [f"同一编号 {_s(r, 'id')!r} 重复出现，只判第一条"],
                   "reason": "编号重复，不判", "evidence": []}
        else:
            if r["row_type"] == "prediction":
                seen.add((code, _s(r, "id")))
            res = judge_row(r, st, mx)
        ev = []
        for label, field in res["evidence"]:
            item = {"file": files[label], "field": field}
            if item not in ev:
                ev.append(item)
        res["evidence"] = ev
        out.append({**r, **res})
    return out


def _dump_jsonl(rows):
    return "".join(json.dumps(r, ensure_ascii=False, default=_dec_out) + "\n" for r in rows).encode("utf-8")


def _markdown(rnd, rows):
    L = [f"# 第 {rnd} 轮判定", "",
         f"由 `revise/scripts/judge.py run {rnd}` 从 `r{rnd}_criteria.jsonl` 生成；原值见 `r{rnd}_judgments.jsonl`，"
         f"数值显示 6 位小数（ROUND_HALF_UP）。\"未判定\"\"不适用\"的说明由操作者另写 `r{rnd}_notes.jsonl`，作者复核。", ""]
    codes = []
    for r in rows:
        if r["candidate"] not in codes:
            codes.append(r["candidate"])
    L += ["## 计数", "", "| 候选 | " + " | ".join(PRED_WORDS) + " | 触发 | 未触发 | 失败条件未判定 |",
          "|---" * (len(PRED_WORDS) + 4) + "|"]
    for code in codes:
        pr = summary_counts([r for r in rows if r["candidate"] == code and r["row_type"] == "prediction"])
        fr = summary_counts([r for r in rows if r["candidate"] == code and r["row_type"] == "failure_condition"])
        L.append(f"| {code} | " + " | ".join(str(pr[w]) for w in PRED_WORDS) +
                 f" | {fr['触发']} | {fr['未触发']} | {fr['未判定']} |")
    L += ["", "## 预测", "",
          "| 候选 | prediction_id | id | metric | check | corner | category | value_kind | 实际 | 方向 | 范围 | 判定 | 格式问题 | 说明 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    esc = lambda s: str(s).replace("|", "\\|").replace("\n", " ")
    for r in rows:
        if r["row_type"] != "prediction":
            continue
        L.append("| " + " | ".join(esc(x) for x in (
            r["candidate"], r["prediction_id"], r["id"], r["metric"], r["check"], r["corner"], r["category"],
            r["value_kind"], _show(r["actual"]), r["direction_judgment"], r["range_judgment"], r["judgment"],
            "；".join(r["format_problems"]), r["reason"])) + " |")
    L += ["", "## 失败条件", "", "| 候选 | fc_id | 原文 | 判定 | 证据字段 |", "|---|---|---|---|---|"]
    for r in rows:
        if r["row_type"] != "failure_condition":
            continue
        L.append("| " + " | ".join(esc(x) for x in (
            r["candidate"], r["fc_id"], r["text"], r["judgment"],
            ", ".join(e["field"] for e in r["evidence"]))) + " |")
    return ("\n".join(L) + "\n").encode("utf-8")


def _write_or_check(case, targets, check):
    problems = []
    for path, data in targets:
        if check:
            try:
                same = rp.read_bytes(path) == data
            except OSError:
                same = False
            if not same:
                problems.append(f"CHECK FAIL: {_rel(case, path)} differs from the recomputed content")
    if not check:
        for path, data in targets:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(data)
    return problems


def run(rnd, check=False, case=None, base_root=None, prev=None):
    """Write (or with check=True compare) r<rnd>_judgments.jsonl and .md. Returns 0 or 1 (problems printed)."""
    case = case or rp.CASE
    try:
        rows = judgment_rows(case, rnd, base_root, prev)
    except (JudgeError, rp.RevpathsError) as e:
        print(f"CRITERIA FAIL: {e}", flush=True)
        return 1
    p = _paths(case, rnd)
    problems = _write_or_check(case, [(p["judgments"], _dump_jsonl(rows)), (p["md"], _markdown(rnd, rows))], check)
    for x in problems:
        print(x, flush=True)
    return 1 if problems else 0


# ---------------------------------------------------------------------------------------------- TSV views
def tsv_cell(v):
    if v is None:
        return ""
    if isinstance(v, str):
        if any(ch in v for ch in "\t\n\r") or v.startswith('"'):
            return json.dumps(v, ensure_ascii=False)
        return v
    return json.dumps(v, ensure_ascii=False, default=_dec_out)


def tsv_bytes(rows, columns):
    lines = ["\t".join(columns)]
    lines += ["\t".join(tsv_cell(r.get(c)) for c in columns) for r in rows]
    return ("\n".join(lines) + "\n").encode("utf-8")


def views(rnd, check=False, case=None, prev=None):
    """r<rnd>_criteria.tsv (and in round 2 r2_coverage.tsv, after coverage.validate) from the JSONL files."""
    case = case or rp.CASE
    p = _paths(case, rnd)
    try:
        rows = load_criteria(case, rnd, prev)
        targets = [(p["tsv"], tsv_bytes(rows, CRITERIA_COLUMNS))]
        if rnd == 2:
            import coverage                                # local import: coverage imports judge
            r1 = load_criteria(case, 1)
            cov = read_jsonl(p["coverage"])
            probs = coverage.validate(r1, rows, cov, prev=prev)
            if probs:
                raise JudgeError("; ".join(probs))
            targets.append((p["coverage_tsv"], tsv_bytes(cov, coverage.COVERAGE_COLUMNS)))
    except (JudgeError, rp.RevpathsError) as e:
        print(f"CRITERIA FAIL: {e}", flush=True)
        return 1
    problems = _write_or_check(case, targets, check)
    for x in problems:
        print(x, flush=True)
    return 1 if problems else 0


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    if len(args) != 2 or args[0] not in ("run", "views") or not args[1].isdigit() or int(args[1]) < 1:
        print("usage: judge.py run|views <rnd> [--check]", file=sys.stderr)
        return 2
    fn = run if args[0] == "run" else views
    return fn(int(args[1]), check=check)


if __name__ == "__main__":
    sys.exit(main())
