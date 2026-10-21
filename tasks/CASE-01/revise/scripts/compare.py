"""Comparison matrix, diffs, degradations and C2 consistency of CASE-01 stage B (implementation plan Task 6;
protocol v0.4 sections 12.2 and 14). Reads only the baseline evidence and the candidates' archived files, never a
model answer. Pure file work; Windows and WSL.

Inputs
  baseline   F1 archive originals via baseline.source() after baseline.verify(): verdict.json and the 12
             sta/path_{max,min}_<corner>.rpt. There is no status.json: extra fields that only status.json has are
             "not_applicable".
  candidate  revise/results/r<rnd>/<code>/status.json and attempt<selected_attempt>/ (verdict.json,
             sta/path_{max,min}_<corner>.rpt, archived by run_grade.py). Only candidates whose sta_analysis is
             "pass" get a matrix.

Matrix: 6 std corners x {setup (max), hold (min)} x {global, in2reg, reg2reg, reg2out} = 48 cells, each
{slack: Decimal | "not_applicable", start, end}. Category cells come from verdict.json corners.<c>.categories
(slack already at 6 decimals). Global cells take ws_max / ws_min (raw value) and start / end parsed from the
same corner's path report (path_endpoints). Auxiliary check: a global value more than 0.00001 ns away from the
smallest applicable category slack of the same corner and check raises ConsistencyError (a stop for a manual check;
last-digit differences at 6 decimals are expected and pass).

Command line (from tasks/CASE-01 or anywhere):
  python3 -B revise/scripts/compare.py matrix <code> <rnd> [--check]
      writes revise/compare/r<rnd>_<code>.json and .md; --check recomputes and compares bytes, writes nothing.
      Prints 'MATRIX FAIL: ...' (nothing written) or 'CHECK FAIL ...' and returns 1 then.
  python3 -B revise/scripts/compare.py consistency <local_dir> <c2_dir>
      local_dir: the local attempt directory (status.json in it or in its parent); c2_dir: the C2 run directory
      (verdict.json). Prints {"verdict", "layers"} as JSON; the C2 result never overrides the local one."""
import dataclasses
import json
import os
import re
import sys
from decimal import Decimal, InvalidOperation

import baseline
import revpaths as rp
import status as status_mod

CORNERS = baseline.CORNERS
CHECKS = (("setup", "max", "ws_max"), ("hold", "min", "ws_min"))
CATEGORIES = ("in2reg", "reg2reg", "reg2out")
SCOPES = ("global",) + CATEGORIES
NA = "not_applicable"
NAV = "not_available"
AUX_TOL = Decimal("0.00001")                 # global vs smallest category: the tolerance of the frozen check_sta.py
HOLD_NOTE = "理想时钟、综合后模型下的最小 hold slack"
EXTRA_KEYS = ("area", "cfg_L", "rtl_sim", "gl_sim", "sta_analysis", "numeric_target_met", "state", "topology",
              "checked_rtl", "checked_gl")
ALLOWED_TOOL_DRIFT = ("opensta/bin/sta",)    # contract v1.4 / grade.py ALLOWED_TOOL_DRIFT
VERDICT_TEXT = {"consistent": "复验一致", "display_consistent": "显示级一致", "inconsistent": "复验不一致"}


class CompareError(Exception):
    pass


class EndpointError(CompareError):
    """The start or end of a path report cannot be located uniquely: the cell is not generated (manual check)."""


class MatrixError(CompareError):
    pass


class ConsistencyError(CompareError):
    """A global cell differs from the smallest category slack by more than AUX_TOL (manual check)."""


@dataclasses.dataclass
class Source:
    kind: str                     # "baseline" | "candidate"
    label: str
    verdict: dict
    reports: dict                 # {"max": {corner: path}, "min": {corner: path}}
    status: object                # status.json dict, or None (baseline)
    extra: dict
    files: dict                   # {name shown in the record: absolute path}


@dataclasses.dataclass
class Matrix:
    cells: dict                   # (corner, check, scope) -> {"slack", "start", "end"}
    summary: dict
    extra: dict


def _is_num(v):
    return isinstance(v, (int, Decimal)) and not isinstance(v, bool)


def _keys():
    return [(c, chk, s) for c in CORNERS for chk, _, _ in CHECKS for s in SCOPES]


# ------------------------------------------------------------------------------------------- path reports
_OBJ = re.compile(r"^\s*(\S+)\s+\((.*)\)\s*$")
_ARRIVAL_OBJ = re.compile(r"\s[\^v]\s+(\S+)\s+\(([^()]*)\)\s*$")


def _point(line, label):
    m = _OBJ.match(line[len(label):])
    if not m:
        raise EndpointError(f"cannot read the {label} line: {line.strip()!r}")
    name, desc = m.group(1), m.group(2)
    if desc.startswith("input port"):
        return name, "in"
    if desc.startswith("output port"):
        return name, "out"
    if "flip-flop" in desc:
        return name, "reg"
    raise EndpointError(f"{label} {name}: unsupported object type ({desc})")


def _cell(pin):
    return pin.rsplit("/", 1)[0]


def path_endpoints(rpt_text):
    """(start, end) of the first path of an OpenSTA path report, from the part before the first
    'data arrival time' only. Port: the port name. Register start: its one data pin in the arrival part (pin name up to
    the last '/' equal to the cell name, not CLK). Register end: the last pin of that cell in the arrival part, which
    must be the last object of the arrival part. Otherwise EndpointError."""
    head, sep, _ = rpt_text.partition("data arrival time")
    if not sep:
        raise EndpointError("no 'data arrival time' section")
    lines = head.splitlines()
    sp = [ln for ln in lines if ln.startswith("Startpoint:")]
    ep = [ln for ln in lines if ln.startswith("Endpoint:")]
    if len(sp) != 1 or len(ep) != 1:
        raise EndpointError(f"expected one Startpoint and one Endpoint line before 'data arrival time', "
                            f"found {len(sp)} and {len(ep)}")
    s_name, s_kind = _point(sp[0], "Startpoint:")
    e_name, e_kind = _point(ep[0], "Endpoint:")
    objs = []
    for ln in lines:
        m = _ARRIVAL_OBJ.search(ln)
        if m:
            objs.append((m.group(1), m.group(2)))
    if not objs:
        raise EndpointError("no pins in the data arrival part")
    pins = []
    for name, _ in objs:
        if "/" in name and name not in pins:
            pins.append(name)

    if s_kind == "in":
        if not any(n == s_name and d in ("in", "inout") for n, d in objs):
            raise EndpointError(f"start port {s_name} not found in the data arrival part")
        start = s_name
    else:
        cands = [p for p in pins if _cell(p) == s_name and p.rsplit("/", 1)[1] != "CLK"]
        if len(cands) != 1:
            raise EndpointError(f"start register {s_name}: {len(cands)} candidate data pins in the data arrival "
                                f"part ({', '.join(cands) or 'none'})")
        start = cands[0]

    last = objs[-1][0]
    if e_kind == "out":
        if not (last == e_name and objs[-1][1] in ("out", "inout")):
            raise EndpointError(f"end port {e_name} is not the last object of the data arrival part ({last})")
        end = e_name
    else:
        cands = [p for p in pins if _cell(p) == e_name]
        if not cands:
            raise EndpointError(f"end register {e_name}: no pin of this cell in the data arrival part")
        end = cands[-1]
        if end != last or end.rsplit("/", 1)[1] == "CLK":
            raise EndpointError(f"end register {e_name}: its last pin {end} is not the end of the data arrival "
                                f"part ({last})")
    return start, end


def _header(text, label):
    head = text.partition("data arrival time")[0]
    vals = [ln[len(label):].strip() for ln in head.splitlines() if ln.startswith(label)]
    return vals[0] if len(vals) == 1 else None


# ------------------------------------------------------------------------------------------------ sources
def _load(path, what):
    try:
        obj = rp.load_json_decimal(path)
    except (OSError, ValueError) as e:
        raise MatrixError(f"{what}: {path} cannot be read ({e.__class__.__name__}: {e})")
    if not isinstance(obj, dict):
        raise MatrixError(f"{what}: {path} is not a JSON object")
    return obj


def _get(d, *path):
    for k in path:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def _impl_L(v):
    L = _get(v, "impl", "L")
    if isinstance(L, bool):
        return None
    if isinstance(L, int):
        return L
    if isinstance(L, str) and re.fullmatch(r"[0-9]+", L):
        return int(L)
    return None


def _dec_or(value):
    """A status.json decimal string back to Decimal; other values unchanged."""
    if isinstance(value, str):
        try:
            d = Decimal(value)
            if d.is_finite():
                return d
        except InvalidOperation:
            pass
    return value


def _reports(base):
    return {kind: {c: os.path.join(base, "sta", f"path_{kind}_{c}.rpt") for c in CORNERS} for kind in ("max", "min")}


def source_baseline(root=None):
    probs = baseline.verify(root)
    if probs:
        raise MatrixError("; ".join(probs))
    src = baseline.source(root)
    v = _load(src["verdict"], "baseline verdict.json")
    met = _get(v, "timing_target", "met")
    L = _impl_L(v)
    extra = {"area": v["area_um2"] if _is_num(v.get("area_um2")) else NAV,
             "cfg_L": L if L is not None else NAV,
             "rtl_sim": NA, "gl_sim": NA, "sta_analysis": NA,
             "numeric_target_met": met if isinstance(met, bool) else NAV,
             "state": NA,
             "topology": v["topology"] if isinstance(v.get("topology"), dict) else NAV,
             "checked_rtl": v["rtl_sim"] if isinstance(v.get("rtl_sim"), str) else NAV,
             "checked_gl": v["gl_sim"] if isinstance(v.get("gl_sim"), str) else NAV}
    pre = f"evidence/F1/archive/{baseline.RUN}/"
    files = {pre + "verdict.json": src["verdict"]}
    for kind in ("max", "min"):
        for c in CORNERS:
            files[pre + f"sta/path_{kind}_{c}.rpt"] = src["path_reports"][kind][c]
    return Source("baseline", f"F1 {baseline.RUN}", v, src["path_reports"], None, extra, files)


def source_candidate(code, rnd, case=None):
    case = case or rp.CASE
    cdir = os.path.join(case, "revise", "results", f"r{rnd}", code)
    st = _load(os.path.join(cdir, "status.json"), f"{code} status.json")
    k = st.get("selected_attempt")
    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        raise MatrixError(f"{code}: status.json has no selected attempt")
    if st.get("sta_analysis") != "pass":
        raise MatrixError(f"{code}: sta_analysis is {st.get('sta_analysis')!r}, not 'pass'; no matrix (protocol 12.2)")
    adir = os.path.join(cdir, f"attempt{k}")
    v = _load(os.path.join(adir, "verdict.json"), f"{code} verdict.json")
    extra = {key: st.get(key, NAV) for key in ("cfg_L", "rtl_sim", "gl_sim", "sta_analysis", "numeric_target_met",
                                              "state", "checked_rtl", "checked_gl")}
    extra["area"] = _dec_or(st.get("area_um2", NAV))
    extra["topology"] = v["topology"] if isinstance(v.get("topology"), dict) else NAV
    reports = _reports(adir)
    rel = os.path.relpath(adir, case).replace(os.sep, "/")
    files = {f"{rel}/verdict.json": os.path.join(adir, "verdict.json")}
    for kind in ("max", "min"):
        for c in CORNERS:
            files[f"{rel}/sta/path_{kind}_{c}.rpt"] = reports[kind][c]
    files[os.path.relpath(os.path.join(cdir, "status.json"), case).replace(os.sep, "/")] = \
        os.path.join(cdir, "status.json")
    return Source("candidate", f"r{rnd} {code} attempt{k}", v, reports, st, {key: extra[key] for key in EXTRA_KEYS},
                  files)


# ------------------------------------------------------------------------------------------------- matrix
def _cat_cell(where, val):
    if val == NA:
        return {"slack": NA, "start": NA, "end": NA}
    if (isinstance(val, dict) and _is_num(val.get("slack")) and isinstance(val.get("start"), str)
            and isinstance(val.get("end"), str)):
        return {"slack": val["slack"], "start": val["start"], "end": val["end"]}
    raise MatrixError(f"{where}: invalid category entry {val!r}")


def matrix(source):
    v = source.verdict
    corners = v.get("corners")
    if not isinstance(corners, dict):
        raise MatrixError(f"{source.label}: verdict.json has no corners")
    missing = [c for c in CORNERS if c not in corners]
    other = [c for c in corners if c not in CORNERS]
    if missing or other:
        raise MatrixError(f"{source.label}: corners missing {missing}, unexpected {other}")
    cells = {}
    for c in CORNERS:
        co = corners[c]
        cats = co.get("categories") if isinstance(co, dict) else None
        if not isinstance(cats, dict):
            raise MatrixError(f"{source.label}: {c}: no categories")
        for chk, kind, wskey in CHECKS:
            for cat in CATEGORIES:
                key = f"{cat}_{kind}"
                if key not in cats:
                    raise MatrixError(f"{source.label}: {c}: category {key} missing")
                cells[(c, chk, cat)] = _cat_cell(f"{source.label}: {c}.{key}", cats[key])
            ws = co.get(wskey)
            if not _is_num(ws):
                raise MatrixError(f"{source.label}: {c}: {wskey} missing or not a number")
            path = source.reports[kind][c]
            try:
                text = rp.read_bytes(path).decode("utf-8")
            except (OSError, UnicodeDecodeError) as e:
                raise MatrixError(f"{source.label}: {path} cannot be read ({e.__class__.__name__})")
            if _header(text, "Corner:") != c or _header(text, "Path Type:") != kind:
                raise MatrixError(f"{source.label}: {os.path.basename(path)}: header Corner / Path Type is not "
                                  f"{c} / {kind}")
            try:
                start, end = path_endpoints(text)
            except EndpointError as e:
                raise EndpointError(f"{source.label}: {os.path.basename(path)}: {e}")
            applicable = [cells[(c, chk, cat)]["slack"] for cat in CATEGORIES
                          if cells[(c, chk, cat)]["slack"] != NA]
            if not applicable:
                raise ConsistencyError(f"{source.label}: {c} {chk}: no applicable category for the auxiliary check")
            low = min(applicable)
            if abs(ws - low) > AUX_TOL:
                raise ConsistencyError(f"{source.label}: {c} {chk}: global {format(ws, 'f')} differs from the "
                                       f"smallest category slack {format(low, 'f')} by more than {AUX_TOL} ns")
            cells[(c, chk, "global")] = {"slack": ws, "start": start, "end": end}
    ws, wh = v.get("worst_setup"), v.get("worst_hold")
    if not (isinstance(ws, dict) and _is_num(ws.get("slack")) and isinstance(ws.get("corner"), str)
            and isinstance(ws.get("category"), str)):
        raise MatrixError(f"{source.label}: worst_setup missing or invalid")
    if not (isinstance(wh, dict) and _is_num(wh.get("slack")) and isinstance(wh.get("corner"), str)):
        raise MatrixError(f"{source.label}: worst_hold missing or invalid")
    summary = {"worst_setup": {"slack": ws["slack"], "corner": ws["corner"], "category": ws["category"]},
               "worst_hold": {"slack": wh["slack"], "corner": wh["corner"]}}
    return Matrix(cells=cells, summary=summary, extra=dict(source.extra))


# -------------------------------------------------------------------------------------- diffs, degradations
def _judge(delta, spec):
    signed = delta if spec["better"] == "increase" else -delta
    if signed > spec["epsilon"]:
        return "better"
    if signed < -spec["epsilon"]:
        return "worse"
    return "same"


def diff(base, cand):
    spec = rp.directions()["slack"]
    out = {}
    for key in _keys():
        if key not in base.cells or key not in cand.cells:
            raise MatrixError(f"cell {key} missing")
        b, c = base.cells[key], cand.cells[key]
        bn, cn = b["slack"] != NA, c["slack"] != NA
        if bn and cn:
            delta = c["slack"] - b["slack"]
            out[key] = {"delta": delta, "change": _judge(delta, spec),
                        "same_path": (b["start"], b["end"]) == (c["start"], c["end"])}
        elif cn:
            out[key] = {"delta": NA, "change": "introduced", "same_path": False}
        elif bn:
            out[key] = {"delta": NA, "change": "removed", "same_path": False}
        else:
            out[key] = {"delta": NA, "change": "same", "same_path": True}
    return out


def degradations(diff_, base_area, cand_area):
    """Every 'worse' cell (hold included, with HOLD_NOTE), then the area when it grew by more than its epsilon."""
    out = []
    for key in _keys():
        d = diff_.get(key)
        if d and d["change"] == "worse":
            out.append({"kind": "slack", "cell": list(key), "delta": d["delta"], "same_path": d["same_path"],
                        "note": HOLD_NOTE if key[1] == "hold" else None})
    if not (_is_num(base_area) and _is_num(cand_area)):
        raise MatrixError(f"area not available (baseline {base_area!r}, candidate {cand_area!r})")
    delta = cand_area - base_area
    if _judge(delta, rp.directions()["area"]) == "worse":
        out.append({"kind": "area", "cell": None, "delta": delta, "base": base_area, "cand": cand_area,
                    "note": None})
    return out


# ---------------------------------------------------------------------------------------- matrix records
def _dec_out(v):
    return format(v, "f") if isinstance(v, Decimal) else v


def _dump(obj):
    return (json.dumps(obj, indent=1, ensure_ascii=False, default=_dec_out) + "\n").encode("utf-8")


def _show(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, Decimal):
        return rp.fmt6(v)
    if isinstance(v, dict):
        return ", ".join(f"{k} {val}" for k, val in v.items())
    return str(v)


def build(code, rnd, case=None, base_root=None):
    """(json bytes, md bytes) of revise/compare/r<rnd>_<code>; raises CompareError on any stop."""
    bs = source_baseline(base_root)
    cs = source_candidate(code, rnd, case=case)
    mb, mc = matrix(bs), matrix(cs)
    d = diff(mb, mc)
    area_delta = mc.extra["area"] - mb.extra["area"] if _is_num(mc.extra["area"]) and _is_num(mb.extra["area"]) \
        else NA
    deg = degradations(d, mb.extra["area"], mc.extra["area"])
    cells = [{"corner": k[0], "check": k[1], "scope": k[2], "base": mb.cells[k], "cand": mc.cells[k], **d[k]}
             for k in _keys()]
    doc = {"code": code, "rnd": rnd, "hold_note": HOLD_NOTE,
           "baseline": {"label": bs.label, "files": {n: rp.sha256(p) for n, p in bs.files.items()},
                        "summary": mb.summary, "extra": mb.extra},
           "candidate": {"label": cs.label, "files": {n: rp.sha256(p) for n, p in cs.files.items()},
                         "summary": mc.summary, "extra": mc.extra},
           "area": {"base": mb.extra["area"], "cand": mc.extra["area"], "delta": area_delta},
           "cells": cells, "degradations": deg}
    return _dump(doc), _markdown(doc).encode("utf-8")


def _markdown(doc):
    b, c = doc["baseline"], doc["candidate"]
    L = [f"# 对照矩阵 r{doc['rnd']} {doc['code']}", "",
         f"基线：{b['label']}；候选：{c['label']}。数值显示 6 位小数（ROUND_HALF_UP），原值见同名 `.json`。"
         f"hold 一律是{doc['hold_note']}。", "",
         "## 来源文件", "", "| 文件 | sha256 |", "|---|---|"]
    for side in (b, c):
        L += [f"| `{n}` | `{h}` |" for n, h in side["files"].items()]
    L += ["", "## 全局最差（verdict.json 原值）", "", "| 项 | 基线 | 候选 |", "|---|---|---|"]
    for name in ("worst_setup", "worst_hold"):
        for k in b["summary"][name]:
            L.append(f"| {name}.{k} | {_show(b['summary'][name][k])} | {_show(c['summary'][name][k])} |")
    L += ["", "## 其他字段", "", "| 字段 | 基线 | 候选 |", "|---|---|---|"]
    L += [f"| {k} | {_show(b['extra'][k])} | {_show(c['extra'][k])} |" for k in EXTRA_KEYS]
    a = doc["area"]
    L += [f"| 面积差值 (µm²) | | {_show(a['delta'])} |", "",
          "## 矩阵", "",
          "| corner | 检查 | 范围 | 基线 slack | 基线起点 → 终点 | 候选 slack | 候选起点 → 终点 | 差值 | 变化 | 同一路径 |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for x in doc["cells"]:
        L.append(f"| {x['corner']} | {x['check']} | {x['scope']} | {_show(x['base']['slack'])} | "
                 f"{x['base']['start']} → {x['base']['end']} | {_show(x['cand']['slack'])} | "
                 f"{x['cand']['start']} → {x['cand']['end']} | {_show(x['delta'])} | {x['change']} | "
                 f"{'是' if x['same_path'] else '否'} |")
    L += ["", "## 退化项", ""]
    if not doc["degradations"]:
        L.append("无。")
    for x in doc["degradations"]:
        if x["kind"] == "area":
            L.append(f"- 面积：{_show(x['base'])} → {_show(x['cand'])}，增大 {_show(x['delta'])} µm²")
        else:
            corner, chk, scope = x["cell"]
            note = f"（{x['note']}）" if x["note"] else ""
            path = "" if x["same_path"] else "；不是同一条路径"
            L.append(f"- {corner} {chk} {scope}：差值 {_show(x['delta'])} ns{path}{note}")
    return "\n".join(L) + "\n"


def write_matrix(code, rnd, check=False, case=None, base_root=None):
    case = case or rp.CASE
    try:
        data_json, data_md = build(code, rnd, case=case, base_root=base_root)
    except CompareError as e:
        print(f"MATRIX FAIL: {e.__class__.__name__}: {e}", flush=True)
        return 1
    out = os.path.join(case, "revise", "compare")
    targets = [(os.path.join(out, f"r{rnd}_{code}.json"), data_json), (os.path.join(out, f"r{rnd}_{code}.md"), data_md)]
    if check:
        bad = []
        for path, data in targets:
            try:
                same = rp.read_bytes(path) == data
            except OSError:
                same = False
            if not same:
                bad.append(f"CHECK FAIL {code}: revise/compare/{os.path.basename(path)} differs from the recomputed "
                           f"content")
        for p in bad:
            print(p, flush=True)
        return 1 if bad else 0
    os.makedirs(out, exist_ok=True)
    for path, data in targets:
        with open(path, "wb") as f:
            f.write(data)
    return 0


# -------------------------------------------------------------------------------------------- consistency
class _Missing:
    def __repr__(self):
        return "missing"


MISSING = _Missing()


def _num(v):
    return v if _is_num(v) else MISSING


def _str(v):
    return v if isinstance(v, str) and v else MISSING


def _bool(v):
    return v if isinstance(v, bool) else MISSING


def _eq(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    return a == b


def _cfg_L_c2(v):
    """cfg_L from impl.L; on success (functional_pass true) it must equal latency_L, else invalid."""
    L = _impl_L(v)
    if L is None:
        return MISSING
    if v.get("functional_pass") is True:
        lat = v.get("latency_L")
        if not (isinstance(lat, int) and not isinstance(lat, bool) and lat == L):
            return MISSING
    return L


def _hold_category(v):
    """(category, tie) derived from the worst_hold corner: the category with the smallest min slack; ties go to
    in2reg, reg2reg, reg2out in this order."""
    corner = _get(v, "worst_hold", "corner")
    cats = _get(v, "corners", corner, "categories") if isinstance(corner, str) else None
    if not isinstance(cats, dict):
        return MISSING, False
    vals = []
    for cat in CATEGORIES:
        e = cats.get(f"{cat}_min")
        if isinstance(e, dict) and _is_num(e.get("slack")):
            vals.append((cat, e["slack"]))
        elif e != NA:
            return MISSING, False
    if not vals:
        return MISSING, False
    low = min(s for _, s in vals)
    hits = [cat for cat, s in vals if s == low]
    return hits[0], len(hits) > 1


def _research(v, st):
    """Layer 6 by the local rules (protocol 9.2, 9.3); author_veto and declared_L inherited from the local status."""
    keys = ("eligible", "numeric_target_met", "eligible_target_met", "improvement")
    if v is None:
        return dict.fromkeys(keys, MISSING)
    met = _bool(_get(v, "timing_target", "met"))
    veto = st.get("author_veto") if isinstance(st, dict) else None
    dL = st.get("declared_L") if isinstance(st, dict) else None
    if not isinstance(veto, bool) or not isinstance(dL, int) or isinstance(dL, bool):
        return {"eligible": MISSING, "numeric_target_met": met, "eligible_target_met": MISSING,
                "improvement": MISSING}
    cfg_L = _cfg_L_c2(v)
    eligible = (v.get("functional_pass") is True and v.get("analysis_valid") is True and cfg_L is not MISSING
                and 1 <= dL <= 3 and dL == cfg_L and _get(v, "area", "within_cap") is True and veto is False)
    slack = _get(v, "worst_setup", "slack")
    if not eligible:
        improvement = NA
    elif _is_num(slack):
        improvement = slack - status_mod.BASE_WORST_SETUP > status_mod.EPS_SLACK
    else:
        improvement = MISSING
    return {"eligible": eligible, "numeric_target_met": met, "eligible_target_met": bool(eligible and met is True),
            "improvement": improvement}


def _drift(v):
    if v is None:
        return MISSING
    if "env_snapshot" not in v:
        return {}                                            # local run without the field: no drift
    es = v["env_snapshot"]
    if isinstance(es, dict) and isinstance(es.get("tool_drift"), dict) and \
            all(isinstance(x, str) for x in es["tool_drift"].values()):
        return dict(es["tool_drift"])
    return MISSING


def _field(name, a, b, numeric=False, display=False, **more):
    if a is MISSING or b is MISSING:
        state = "missing"
    elif _eq(a, b):
        state = "same"
    elif numeric and display and _is_num(a) and _is_num(b) and rp.fmt6(a) == rp.fmt6(b):
        state = "display_same"
    else:
        state = "different"
    out = {"field": name, "local": "missing" if a is MISSING else a, "c2": "missing" if b is MISSING else b,
           "status": state}
    out.update(more)
    return out


def _layer(n, name, fields):
    states = [f["status"] for f in fields]
    return {"layer": n, "name": name, "fields": fields,
            "missing": [f["field"] for f in fields if f["status"] == "missing"],
            "same": all(s == "same" for s in states),
            "display_only": all(s in ("same", "display_same") for s in states) and "display_same" in states}


def _load_opt(path):
    try:
        obj = rp.load_json_decimal(path)
    except (OSError, ValueError):
        return None
    return obj if isinstance(obj, dict) else None


def consistency(local_dir, c2_dir, local_status=None):
    """(verdict, layers): verdict 'consistent' | 'display_consistent' | 'inconsistent' (protocol 14)."""
    lv = _load_opt(os.path.join(local_dir, "verdict.json"))
    cv = _load_opt(os.path.join(c2_dir, "verdict.json"))
    if local_status is None:
        own = os.path.join(local_dir, "status.json")
        local_status = own if os.path.isfile(own) else os.path.join(os.path.dirname(os.path.abspath(local_dir)),
                                                                    "status.json")
    st = _load_opt(local_status)
    sides = (lv or {}, cv or {})

    def both(fn):
        return [fn(s) if v is not None else MISSING for s, v in zip(sides, (lv, cv))]

    layers = []
    layers.append(_layer(1, "netlist", [_field("netlist_sha256", *both(lambda v: _str(v.get("netlist_sha256"))))]))
    layers.append(_layer(2, "flags", [
        _field("functional_pass", *both(lambda v: _bool(v.get("functional_pass")))),
        _field("analysis_valid", *both(lambda v: _bool(v.get("analysis_valid")))),
        _field("cfg_L", *both(_cfg_L_c2)),
        _field("timing_target.met", *both(lambda v: _bool(_get(v, "timing_target", "met"))))]))
    hl = _hold_category(lv) if lv is not None else (MISSING, False)
    hc = _hold_category(cv) if cv is not None else (MISSING, False)
    layers.append(_layer(3, "worst", [
        _field("worst_setup.slack", *both(lambda v: _num(_get(v, "worst_setup", "slack"))), numeric=True,
               display=True),
        _field("worst_setup.corner", *both(lambda v: _str(_get(v, "worst_setup", "corner")))),
        _field("worst_setup.category", *both(lambda v: _str(_get(v, "worst_setup", "category")))),
        _field("worst_hold.slack", *both(lambda v: _num(_get(v, "worst_hold", "slack"))), numeric=True,
               display=True),
        _field("worst_hold.corner", *both(lambda v: _str(_get(v, "worst_hold", "corner")))),
        _field("worst_hold.category", hl[0], hc[0], derived=True, tie_local=hl[1], tie_c2=hc[1])]))
    f4 = []
    for c in CORNERS:
        for wskey in ("ws_max", "ws_min"):
            f4.append(_field(f"{c}.{wskey}", *both(lambda v, c=c, k=wskey: _num(_get(v, "corners", c, k))),
                             numeric=True, display=True))
        for cat in CATEGORIES:
            for kind in ("max", "min"):
                key = f"{cat}_{kind}"

                def part(v, which, c=c, key=key):
                    e = _get(v, "corners", c, "categories", key)
                    if e == NA:
                        return False if which == "applicable" else NA
                    if not (isinstance(e, dict) and _is_num(e.get("slack")) and isinstance(e.get("start"), str)
                            and isinstance(e.get("end"), str)):
                        return MISSING
                    return True if which == "applicable" else e[which]
                f4.append(_field(f"{c}.{key}.applicable", *both(lambda v: part(v, "applicable")), derived=True))
                f4.append(_field(f"{c}.{key}.slack", *both(lambda v: part(v, "slack")), numeric=True, display=True))
                f4.append(_field(f"{c}.{key}.start", *both(lambda v: part(v, "start"))))
                f4.append(_field(f"{c}.{key}.end", *both(lambda v: part(v, "end"))))
    layers.append(_layer(4, "corners", f4))
    layers.append(_layer(5, "area_topology", [
        _field("area_um2", *both(lambda v: _num(v.get("area_um2"))), numeric=True),
        _field("topology", *both(lambda v: v["topology"] if isinstance(v.get("topology"), dict) else MISSING))]))
    rl, rc = _research(lv, st), _research(cv, st)
    layers.append(_layer(6, "research", [_field(k, rl[k], rc[k]) for k in rl]))
    dl, dc = _drift(lv), _drift(cv)
    ok = dl is not MISSING and dc is not MISSING and dl == {} and set(dc) <= set(ALLOWED_TOOL_DRIFT)
    f7 = {"field": "tool_drift", "local": "missing" if dl is MISSING else dl, "c2": "missing" if dc is MISSING else dc,
          "status": "same" if ok else ("missing" if MISSING in (dl, dc) else "different"),
          "allowed": list(ALLOWED_TOOL_DRIFT)}
    layers.append(_layer(7, "tool_drift", [f7]))

    by = {x["layer"]: x for x in layers}
    if all(x["same"] for x in layers):
        verdict = "consistent"
    elif all(by[n]["same"] for n in (1, 2, 5, 6, 7)) and all(by[n]["same"] or by[n]["display_only"] for n in (3, 4)):
        verdict = "display_consistent"
    else:
        verdict = "inconsistent"
    return verdict, layers


# --------------------------------------------------------------------------------------------- command line
def main(argv=None, case=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) in (3, 4) and args[0] == "matrix" and args[2].isdigit() and (len(args) == 3 or args[3] == "--check"):
        return write_matrix(args[1], int(args[2]), check=len(args) == 4, case=case)
    if len(args) == 3 and args[0] == "consistency":
        verdict, layers = consistency(args[1], args[2])
        print(json.dumps({"verdict": verdict, "verdict_text": VERDICT_TEXT[verdict], "layers": layers}, indent=1,
                         ensure_ascii=False, default=_dec_out), flush=True)
        return 0
    print("usage: compare.py matrix <code> <rnd> [--check] | compare.py consistency <local_dir> <c2_dir>",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
