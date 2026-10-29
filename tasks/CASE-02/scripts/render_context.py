"""Produce the tier-1 frozen package_src/context.md = package_src/context_body.md + a blank line + the execution
contract rendered from rules/contract.json (contract.render_context_section). The frozen file is what every model
sees; after any change the author re-confirms it (package_src/CONFIRMED.md).
  python3 -B scripts/render_context.py            # write package_src/context.md (refused if label_check finds a label)
  python3 -B scripts/render_context.py --force    # overwrite an existing (differing) file: only before tier 1, then the
                                                  # author re-confirms the wording (package_src/CONFIRMED.md)
  python3 -B scripts/render_context.py --check    # compare only; exit 1 when the file differs"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from c2paths import CASE, PACKAGE_SRC, RULES, read_bytes, write_new_or_same  # noqa: E402
import contract as contract_mod  # noqa: E402
import label_check as lc  # noqa: E402


def render():
    c = contract_mod.load(os.path.join(RULES, "contract.json"))
    section = contract_mod.render_context_section(c, os.path.join(RULES, "allow_query.txt"), os.path.join(RULES, "allow_whatif.txt"),
                                                  os.path.join(RULES, "setup_commands.txt"))
    body = read_bytes(os.path.join(PACKAGE_SRC, "context_body.md")).decode("utf-8")
    return (body.rstrip("\n") + "\n\n" + section).encode("utf-8")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    data = render()
    path = os.path.join(PACKAGE_SRC, "context.md")
    found = lc.scan_text(data.decode("utf-8"), "package/context.md")
    if found:
        print("CONTEXT FAIL: internal label in the rendered context: " + "; ".join(found))
        return 1
    if "--check" in argv:
        same = os.path.exists(path) and read_bytes(path) == data
        print(f"CONTEXT {'OK' if same else 'DIFFERS'}: {os.path.relpath(path, CASE)}")
        return 0 if same else 1
    if "--force" in argv:
        with open(path, "wb") as f:
            f.write(data)
    else:
        write_new_or_same(path, data)
    print(f"CONTEXT OK: {os.path.relpath(path, CASE)} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
