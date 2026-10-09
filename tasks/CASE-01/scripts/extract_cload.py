"""Extract C_load (spec 4.3): scalar `capacitance` of pin A of sky130_fd_sc_hd__buf_4 in the tt Liberty.

Usage: python3 scripts/extract_cload.py <lib> <MANIFEST.txt>   -> prints JSON, exits 1 on any problem.
The lib's sha256 must match its entry in env/sky130hd_kit/MANIFEST.txt, and the capacitive unit must be pF.
"""
import hashlib
import json
import os
import re
import sys

CELL = "sky130_fd_sc_hd__buf_4"
PIN = "A"


def extract(text, cell=CELL, pin=PIN):
    """Return the scalar capacitance (in library units) of `pin` inside `cell`."""
    unit = re.search(r'capacitive_load_unit\s*\(\s*1(?:\.0*)?\s*,\s*"?(\w+)"?\s*\)', text)
    if not unit or unit.group(1).lower() != "pf":
        raise ValueError("capacitive_load_unit is not 1 pF")
    cm = re.search(r'\bcell\s*\(\s*"%s"\s*\)' % re.escape(cell), text)
    if not cm:
        raise ValueError(f"cell {cell} not found")
    next_cell = re.compile(r'\bcell\s*\(').search(text, cm.end())
    cell_end = next_cell.start() if next_cell else len(text)
    pm = re.compile(r'\bpin\s*\(\s*"%s"\s*\)\s*\{' % re.escape(pin)).search(text, cm.end(), cell_end)
    if not pm:
        raise ValueError(f"pin {pin} not found in {cell}")
    next_pin = re.compile(r'\bpin\s*\(').search(text, pm.end(), cell_end)
    pin_end = next_pin.start() if next_pin else cell_end
    cap = re.compile(r'^\s*capacitance\s*:\s*([0-9.eE+-]+)\s*;', re.M).search(text, pm.end(), pin_end)
    if not cap:
        raise ValueError(f"no scalar capacitance in {cell}/{pin}")
    return float(cap.group(1))


def manifest_sha(manifest_text, lib_name):
    for line in manifest_text.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == lib_name:
            return parts[0]
    raise ValueError(f"{lib_name} not listed in MANIFEST")


def main(argv):
    if len(argv) != 3:
        print("usage: extract_cload.py <lib> <MANIFEST.txt>")
        return 1
    lib, manifest = argv[1], argv[2]
    data = open(lib, "rb").read()
    sha = hashlib.sha256(data).hexdigest()
    want = manifest_sha(open(manifest).read(), os.path.basename(lib))
    if sha != want:
        print(f"FAIL: {lib} sha256 {sha} != MANIFEST {want}")
        return 1
    value = extract(data.decode())
    print(json.dumps({"lib": os.path.basename(lib), "lib_sha256": sha, "cell": CELL, "pin": PIN,
                      "field": "capacitance", "value_pf": value, "unit": "pF"}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except (OSError, ValueError) as e:
        print(f"FAIL: {e}")
        sys.exit(1)
