"""Record-file comparison for the CASE-02 contexts (protocol v0.3 sections 5.2, 5.3 layer 2, 5.6).

compare(relation, run_dir, base_dir, rules_dir) compares one run's STA records with a baseline:
  correct_vs_f1        correct version against the archived F1 originals: no difference allowed
  missing_vs_correct   missing version against the correct version: only rules/allowed_changes.json may differ,
                       and each allowed difference must pass the semantic checks of numeric_checks()
  restored_vs_correct  restored version against the correct version: no difference allowed
  query_env_vs_formal  a query instance's rebuilt records against the formal run of the same version: no difference
expanded.sdc under missing_vs_correct is checked by the mutation rule (exactly rules/mutation_lines.txt removed;
result["mutation_verified"]), not by the allowed-changes list.
The compared set is fixed (RECORD_FILES, 50 files); metadata files (METADATA_FILES) are neither compared nor counted
as extra. LIB lines are compared normalized (registered prefix stripped, file name must equal the library name) and
raw; both results are reported.
"""
import json
import os
import re
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

SCENES = ["tt_025C_1v80", "tt_100C_1v80", "ss_100C_1v60", "ss_n40C_1v60", "ff_n40C_1v95", "ff_100C_1v95"]
RELATIONS = ("correct_vs_f1", "missing_vs_correct", "restored_vs_correct", "query_env_vs_formal")
RECORD_FILES = frozenset(
    ["expanded.sdc", "sta_results.tsv"]
    + [f"dcalc_{c}_{m}.txt" for c in SCENES for m in ("max", "min")]
    + [f"cat_{c}_{g}_{m}.rpt" for c in SCENES for g in ("in2reg", "reg2out") for m in ("max", "min")]
    + [f"path_{m}_{c}.rpt" for c in SCENES for m in ("max", "min")])
METADATA_FILES = frozenset(["sta.log", "cmd.txt", "valid.json", "SHA256SUMS", "lib_lines_raw.txt", "musts", "snapshot.log"])
EXPECTED_CHECK_SETUP = {"correct": "1", "missing": "0", "restored": "1"}
TARGET_PORTS = [f"in_b[{i}]" for i in range(64)]
ALL_INPUTS = [f"in_a[{i}]" for i in range(64)] + TARGET_PORTS + ["in_valid", "rst"]
WARNING_RE = re.compile(r"^Warning: There are (\d+) input ports missing set_input_delay\.$")
SLACK_RE = re.compile(r"^\s*(-?\d+\.\d+)\s+slack")


class LibPrefixError(ValueError):
    pass


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def _read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def _rules(rules_dir):
    with open(os.path.join(rules_dir, "allowed_changes.json"), encoding="utf-8") as f:
        a = json.load(f)
    records = {r.replace("<c>", c) for r in a["records"] for c in a["scenes"]}
    files = {r.replace("<c>", c) for r in a["files"] for c in a["scenes"]}
    return records, files


def _lib_rules(rules_dir):
    lines = [l.rstrip("\n") for l in _read(os.path.join(rules_dir, "lib_normalize.txt")).splitlines() if l.strip()]
    return re.compile(lines[0]), lines[1:]


def parse_lib_line(line, rules_dir):
    """('library name', 'file name') of a LIB record; LibPrefixError when the directory prefix is not registered or
    the file name does not equal the library name."""
    regex, prefixes = _lib_rules(rules_dir)
    parts = line.rstrip("\n").split("\t")
    if len(parts) != 3 or parts[0] != "LIB":
        raise LibPrefixError(f"not a LIB record: {line!r}")
    m = regex.match(parts[2])
    if not m or m.group("prefix") not in prefixes:
        raise LibPrefixError(f"library directory prefix not registered: {parts[2]}")
    fname = m.group("file")
    if fname[:-len(".lib")] != parts[1]:
        raise LibPrefixError(f"library file name {fname} does not match library name {parts[1]}")
    return parts[1], fname


def _record_key(line):
    f = line.split("\t")
    if f[0] in ("WS",):
        return "\t".join(f[:3])
    if f[0] == "CAT":
        return "\t".join(f[:4])
    if f[0] in ("LIB", "BIND", "PORT", "LOAD"):
        return "\t".join(f[:2])
    return f[0]


def _slack_in_report(path):
    value = None
    for line in _read(path).splitlines():
        m = SLACK_RE.match(line)
        if m:
            value = m.group(1)
    return value


def _points_in_report(path):
    start = end = None
    for line in _read(path).splitlines():
        if line.startswith("Startpoint: "):
            start = line.split()[1]
        elif line.startswith("Endpoint: "):
            end = line.split()[1]
        if start and end:
            break
    return start, end


def _round_to(value, places):
    q = Decimal(1).scaleb(-places)
    return str(Decimal(value).quantize(q, rounding=ROUND_HALF_UP))


def numeric_checks(tsv_text, run_dir, allowed_records):
    """Semantic checks of the records allowed to change: finite value, scene known, kind max, report slack equal
    after rounding, start/end points consistent with the CAT record of the same scene."""
    rows = [l.split("\t") for l in tsv_text.splitlines() if l.strip()]
    cats = {r[1]: r for r in rows if r[0] == "CAT" and len(r) >= 4 and r[2] == "in2reg" and r[3] == "max"}
    out = []
    for r in rows:
        key = _record_key("\t".join(r))
        if key not in allowed_records:
            continue
        item = {"record": key, "scene": r[1], "kind": None, "value": None, "report_file": None, "report_value": None,
                "startpoint_ok": True, "endpoint_ok": True, "finite": False, "ok": False}
        try:
            if r[0] == "WS":
                item["kind"], item["value"] = r[2], r[3]
                item["report_file"] = f"path_max_{r[1]}.rpt"
                places = 4
            else:
                item["kind"], item["value"] = r[3], r[4]
                item["report_file"] = f"cat_{r[1]}_in2reg_max.rpt"
                places = 4
            d = Decimal(item["value"])
            item["finite"] = d.is_finite()
            scene_ok = r[1] in SCENES
            kind_ok = item["kind"] == "max"
            rpath = os.path.join(run_dir, item["report_file"])
            if os.path.isfile(rpath):
                item["report_value"] = _slack_in_report(rpath)
                if r[0] == "CAT":
                    # the category report's start/end must be the ones the CAT record names
                    start, end = _points_in_report(rpath)
                    item["startpoint_ok"] = (start == r[5]) if len(r) >= 7 else False
                    item["endpoint_ok"] = (end == r[6].split("/")[0]) if len(r) >= 7 else False
            value_ok = item["finite"] and item["report_value"] is not None and \
                _round_to(item["value"], places) == _round_to(item["report_value"], places)
            item["ok"] = bool(scene_ok and kind_ok and value_ok and item["startpoint_ok"] and item["endpoint_ok"])
        except (InvalidOperation, IndexError, ValueError):
            item["ok"] = False
        out.append(item)
    return out


def _compare_tsv(relation, run_text, base_text, allowed_records, rules_dir, result):
    run_lines = run_text.splitlines()
    base_lines = base_text.splitlines()
    problems = []
    if len(run_lines) != len(base_lines):
        problems.append(f"sta_results.tsv: {len(run_lines)} lines, baseline {len(base_lines)}")
    lib_norm_ok = True
    raw_lines = []
    for i in range(max(len(run_lines), len(base_lines))):
        a = run_lines[i] if i < len(run_lines) else None
        b = base_lines[i] if i < len(base_lines) else None
        if a is None or b is None:
            continue
        key = _record_key(a)
        if key != _record_key(b):
            problems.append(f"sta_results.tsv line {i + 1}: record {key!r} vs baseline {_record_key(b)!r}")
            continue
        if a.startswith("LIB\t"):
            raw_lines.append(a)
            try:
                if parse_lib_line(a, rules_dir) != parse_lib_line(b, rules_dir):
                    lib_norm_ok = False
                    problems.append(f"LIB normalized differs: {key}")
            except LibPrefixError as e:
                lib_norm_ok = False
                problems.append(f"LIB: {e}")
            continue
        if a.startswith("CHECK_SETUP\t"):
            v = a.split("\t")[1]
            if v not in ("0", "1"):
                problems.append(f"CHECK_SETUP must be 0 or 1, got {v!r}")
            exp = {"correct_vs_f1": "1", "missing_vs_correct": "0", "restored_vs_correct": "1"}.get(relation)
            if exp is not None and v != exp:
                problems.append(f"CHECK_SETUP is {v}, expected {exp} for {relation}")
            if relation in ("correct_vs_f1", "restored_vs_correct", "query_env_vs_formal") and a != b:
                problems.append("CHECK_SETUP differs from baseline")
            continue
        if a != b:
            if relation == "missing_vs_correct" and key in allowed_records:
                result["allowed_changes_seen"].append(key)
            else:
                problems.append(f"sta_results.tsv differs: {key}")
    base_raw = [l for l in base_lines if l.startswith("LIB\t")]
    result["lib"] = {"normalized_ok": lib_norm_ok, "raw_identical": raw_lines == base_raw, "raw_lines": raw_lines}
    return problems


def compare(relation, run_dir, base_dir, rules_dir):
    if relation not in RELATIONS:
        raise ValueError(f"unknown relation {relation!r}; one of {RELATIONS}")
    allowed_records, allowed_files = _rules(rules_dir) if relation == "missing_vs_correct" else (set(), set())
    result = {"ok": False, "relation": relation, "problems": [], "allowed_changes_seen": [], "lib": {}, "numeric": [],
              "extra_files": [], "missing_files": [], "mutation_verified": None}
    present = {n for n in os.listdir(run_dir) if n not in METADATA_FILES}
    result["extra_files"] = sorted(present - RECORD_FILES)
    result["missing_files"] = sorted(RECORD_FILES - present)
    problems = [f"file not in the record set: {n}" for n in result["extra_files"]]
    problems += [f"record file missing: {n}" for n in result["missing_files"]]
    for name in sorted(RECORD_FILES & present):
        rp, bp = os.path.join(run_dir, name), os.path.join(base_dir, name)
        if not os.path.isfile(bp):
            problems.append(f"baseline lacks {name}")
            continue
        if name == "sta_results.tsv":
            problems += _compare_tsv(relation, _read(rp), _read(bp), allowed_records, rules_dir, result)
            continue
        same = _read_bytes(rp) == _read_bytes(bp)
        if same:
            if name == "expanded.sdc" and relation == "missing_vs_correct":
                problems.append("expanded.sdc is identical to the correct version: mutation not applied")
                result["mutation_verified"] = False
            continue
        if name == "expanded.sdc" and relation == "missing_vs_correct":
            mut = _read(os.path.join(rules_dir, "mutation_lines.txt")).splitlines()
            ok, why = expanded_diff_is_exactly(_read(bp), _read(rp), mut)
            result["mutation_verified"] = ok
            if not ok:
                problems += ["expanded.sdc: " + w for w in why]
            continue
        if name in allowed_files:
            result["allowed_changes_seen"].append(name)
        else:
            problems.append(f"{name} differs from baseline")
    if relation == "missing_vs_correct" and "sta_results.tsv" in present:
        result["numeric"] = numeric_checks(_read(os.path.join(run_dir, "sta_results.tsv")), run_dir, allowed_records)
        problems += [f"semantic check failed: {n['record']}" for n in result["numeric"] if not n["ok"]]
    result["problems"] = problems
    result["ok"] = not problems
    return result


def _mutation_ports(mutation_lines_path):
    ports = []
    for line in _read(mutation_lines_path).splitlines():
        m = re.search(r"\[get_ports \{(.+?)\}\]", line)
        if m:
            ports.append(m.group(1))
    return ports


def warning_block(sta_log_text, mutation_lines_path):
    """The check_setup warning block of the missing version: exactly one warning line followed by exactly the 64
    target port names, each once (protocol 5.6)."""
    target = set(_mutation_ports(mutation_lines_path))
    lines = sta_log_text.splitlines()
    blocks = []
    i = 0
    while i < len(lines):
        m = WARNING_RE.match(lines[i])
        if m:
            names = []
            j = i + 1
            while j < len(lines) and lines[j].startswith("  ") and lines[j].strip():
                names.append(lines[j].strip())
                j += 1
            blocks.append((int(m.group(1)), names))
            i = j
        else:
            i += 1
    out = {"present": bool(blocks), "count": None, "names_ok": False, "problems": []}
    if not blocks:
        return out
    if len(blocks) != 1:
        out["problems"].append(f"{len(blocks)} warning blocks, expected 1")
    count, names = blocks[0]
    out["count"] = count
    if count != len(target):
        out["problems"].append(f"warning says {count} ports, expected {len(target)}")
    if len(names) != len(set(names)):
        out["problems"].append("duplicate port names in the warning block")
    if set(names) != target:
        out["problems"].append(f"port set differs: missing {sorted(target - set(names))[:5]}, "
                               f"foreign {sorted(set(names) - target)[:5]}")
    if len(names) != len(target):
        out["problems"].append(f"{len(names)} names listed, expected {len(target)}")
    out["names_ok"] = not out["problems"]
    return out


def expanded_diff_is_exactly(correct_text, missing_text, mutation_lines):
    """True when missing == correct with exactly the contiguous block mutation_lines removed, in order, and no other
    difference."""
    c = correct_text.splitlines()
    m = missing_text.splitlines()
    mut = [l.rstrip("\n") for l in mutation_lines]
    problems = []
    n = len(mut)
    if n == 0:
        return False, ["empty mutation list"]
    starts = [i for i in range(len(c) - n + 1) if c[i:i + n] == mut]
    if len(starts) != 1:
        return False, [f"mutation block found {len(starts)} times in the correct expanded.sdc"]
    s = starts[0]
    expected = c[:s] + c[s + n:]
    if expected != m:
        for k, (a, b) in enumerate(zip(expected, m)):
            if a != b:
                problems.append(f"first difference at missing line {k + 1}: {b!r} vs expected {a!r}")
                break
        if len(expected) != len(m):
            problems.append(f"missing has {len(m)} lines, expected {len(expected)}")
        return False, problems
    return True, []


_DELAY_RE = re.compile(r"^set_input_delay (\S+) -clock \[get_clocks \{(\w+)\}\](?P<opts>.*) \[get_ports \{(.+?)\}\]$")
_DRIVE_RE = re.compile(r"^set_driving_cell -lib_cell (\S+) .* \[get_ports \{(.+?)\}\]$")


def expanded_constraints(expanded_text):
    """Per input port: min/max input delay values, reference clock, edge, rise/fall flags and driving cell, parsed
    from the expanded SDC (protocol 5.3 layer 2)."""
    out = {p: {"min": None, "max": None, "clock": None, "edge": None, "rise": False, "fall": False, "driver": None}
           for p in ALL_INPUTS}
    for line in expanded_text.splitlines():
        m = _DELAY_RE.match(line)
        if m:
            value, clock, opts, port = m.group(1), m.group(2), m.group("opts"), m.group(4)
            if port not in out:
                continue
            e = out[port]
            kind = "min" if " -min" in opts else ("max" if " -max" in opts else None)
            if kind:
                e[kind] = value
            e["clock"] = clock
            e["edge"] = "fall" if " -clock_fall" in opts else "rise"
            has_rise, has_fall = " -rise" in opts, " -fall" in opts
            if has_rise or has_fall:
                e["rise"] = e["rise"] or has_rise
                e["fall"] = e["fall"] or has_fall
            else:
                e["rise"] = e["fall"] = True
            continue
        m = _DRIVE_RE.match(line)
        if m and m.group(2) in out:
            out[m.group(2)]["driver"] = m.group(1)
    return out


def layer2_check(constraints, version):
    problems = []
    for p in ALL_INPUTS:
        e = constraints.get(p)
        if e is None:
            problems.append(f"{p}: not parsed")
            continue
        if e["driver"] != "sky130_fd_sc_hd__buf_2":
            problems.append(f"{p}: driver {e['driver']}")
        complete = e["min"] is not None and e["max"] is not None and e["clock"] == "clk" and e["edge"] == "rise" \
            and e["rise"] and e["fall"]
        absent = e["min"] is None and e["max"] is None
        if version == "missing" and p in TARGET_PORTS:
            if not absent:
                problems.append(f"{p}: should have no input delay in the missing version")
        elif not complete:
            problems.append(f"{p}: input delay incomplete ({e})")
    return (not problems), problems
