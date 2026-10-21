"""Pre-registration checks for the CASE-01 stage B scripts (implementation plan Task 1; protocol v0.4 section 15).

Manifest revise/rules/preregistered.json:
  {"tier1": {"tracked": [<file path from the repository root>, ...], "local_hash": {<path>: <sha256>}},
   "tier2": {"tracked": [...]},
   "generated": [<path prefix of run products>, ...]}
Hash lists (sha256sum text format, "<sha256>  <path from the repository root>"), generated and committed BEFORE the
tag, so the tag contains them:
  revise/rules/scripts.sha256      every file under revise/scripts/
  revise/rules/prereg_tier1.sha256 tier1.tracked + local_hash (never itself)
  revise/rules/prereg_tier2.sha256 both tiers + local_hash (never itself)
problems("smoke") checks against tag revise-prereg-smoke (tier 1, prereg_tier1.sha256, scripts.sha256);
problems("formal") against tag revise-prereg (both tiers and all three lists). The manifest is read from the tag.
git runs as a plain subprocess with a 60 s timeout (it is not one of the processes of the run-limits table).
Python standard library only; Windows and WSL."""
import json
import os
import subprocess

import revpaths as rp

TAGS = {"smoke": "revise-prereg-smoke", "formal": "revise-prereg"}
R = "tasks/CASE-01/revise"
MANIFEST = f"{R}/rules/preregistered.json"
SCRIPTS_DIR = f"{R}/scripts/"
LISTS = {"scripts": f"{R}/rules/scripts.sha256",
         "tier1": f"{R}/rules/prereg_tier1.sha256",
         "tier2": f"{R}/rules/prereg_tier2.sha256"}
LISTS_BY_MODE = {"smoke": ("tier1", "scripts"), "formal": ("tier1", "tier2", "scripts")}
GIT_TIMEOUT = 60
_GIT_ENV_DROP = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_COMMON_DIR")


class PreregError(Exception):
    pass


def git(args, cwd):
    """Run git in cwd; returns (returncode, stdout bytes). The repository is the one containing cwd."""
    env = {k: v for k, v in os.environ.items() if k not in _GIT_ENV_DROP}
    try:
        r = subprocess.run(["git", *args], cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=GIT_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise PreregError(f"git {' '.join(args)} could not run in {cwd}: {e}") from e
    return r.returncode, r.stdout


def blob_at(rev, path):
    """Bytes of file `path` (absolute or relative to the current directory) in revision `rev` (commit or tag);
    None when the file is not in that revision or the revision does not exist."""
    path = os.path.abspath(path)
    d, name = os.path.split(path)
    if not os.path.isdir(d):
        return None
    rc, out = git(["cat-file", "blob", f"{rev}:./{name}"], d)
    return out if rc == 0 else None


def committed_unchanged(path):
    """True when `path` is tracked by git, is in HEAD, and the working file holds exactly the HEAD bytes."""
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        return False
    d, name = os.path.split(path)
    rc, _ = git(["ls-files", "--error-unmatch", "--", name], d)
    if rc != 0:
        return False
    head = blob_at("HEAD", path)
    return head is not None and head == rp.read_bytes(path)


def _abs(repo, rel):
    return os.path.join(repo, *rel.split("/"))


def _tracked_under(repo, prefix):
    rc, out = git(["ls-files", "-z", "--", prefix], repo)
    if rc != 0:
        raise PreregError(f"git ls-files {prefix} failed")
    return sorted(p for p in out.decode("utf-8").split("\0") if p)


def _untracked_under(repo, prefix):
    """Files under prefix that git does not track, ignored ones included; __pycache__/ is left out."""
    rc, out = git(["ls-files", "-z", "--others", "--", prefix], repo)
    if rc != 0:
        raise PreregError(f"git ls-files --others {prefix} failed")
    return sorted(p for p in out.decode("utf-8").split("\0")
                  if p and "__pycache__/" not in p and not p.endswith("/__pycache__"))


def _list_text(repo, rels, overlay=None):
    lines = []
    for rel in rels:
        data = overlay[rel] if overlay and rel in overlay else rp.read_bytes(_abs(repo, rel))
        lines.append(f"{rp.sha256_bytes(data)}  {rel}\n")
    return "".join(lines)


def _list_members(manifest, which, repo):
    if which == "scripts":
        rels = _tracked_under(repo, SCRIPTS_DIR)
    else:
        rels = list(manifest["tier1"]["tracked"]) + list(manifest["tier1"]["local_hash"])
        if which == "tier2":
            rels += list(manifest["tier2"]["tracked"])
    own = LISTS[which]
    return sorted(set(r for r in rels if r != own))


def _check_manifest(m):
    ok = (isinstance(m, dict) and isinstance(m.get("tier1"), dict) and isinstance(m.get("tier2"), dict)
          and isinstance(m["tier1"].get("tracked"), list) and isinstance(m["tier1"].get("local_hash"), dict)
          and isinstance(m["tier2"].get("tracked"), list) and isinstance(m.get("generated"), list))
    if not ok:
        raise PreregError("preregistered.json: expected tier1.tracked, tier1.local_hash, tier2.tracked, generated")
    return m


def expected_hash_lists(names=("scripts.sha256", "prereg_tier1.sha256", "prereg_tier2.sha256"), repo=None):
    """{list file name: text} for the requested hash lists (scripts.sha256, prereg_tier1.sha256,
    prereg_tier2.sha256) from the current working files and the working manifest. Lists are built in that order, and
    a later list hashes the new text of an earlier requested list (lists not requested are hashed as they are)."""
    repo = repo or rp.REPO
    manifest = _check_manifest(json.loads(rp.read_bytes(_abs(repo, MANIFEST)).decode("utf-8")))
    by_name = {LISTS[w].rsplit("/", 1)[1]: w for w in LISTS}
    unknown = set(names) - set(by_name)
    if unknown:
        raise ValueError(f"unknown hash lists: {sorted(unknown)}")
    overlay, out = {}, {}
    for which in ("scripts", "tier1", "tier2"):
        name = LISTS[which].rsplit("/", 1)[1]
        if name not in names:
            continue
        text = _list_text(repo, _list_members(manifest, which, repo), overlay)
        overlay[LISTS[which]] = text.encode("utf-8")
        out[name] = text
    return out


def problems(mode, repo=None):
    """List of problems of the pre-registration in this mode; empty means everything matches (see module doc)."""
    if mode not in TAGS:
        raise ValueError(f"mode must be one of {sorted(TAGS)}, not {mode!r}")
    repo = repo or rp.REPO
    tag = TAGS[mode]
    probs = []
    rc, _ = git(["rev-parse", "--verify", "-q", f"refs/tags/{tag}^{{commit}}"], repo)
    if rc != 0:
        return [f"PREREG FAIL: tag {tag} does not exist (mode {mode})"]

    tag_ref = f"refs/tags/{tag}"
    raw = blob_at(tag_ref, _abs(repo, MANIFEST))
    if raw is None:
        return [f"PREREG FAIL: {MANIFEST} is not in tag {tag}"]
    try:
        manifest = _check_manifest(json.loads(raw.decode("utf-8")))
    except (ValueError, PreregError) as e:
        return [f"PREREG FAIL: {MANIFEST} in tag {tag} is unreadable: {e}"]

    tracked = list(manifest["tier1"]["tracked"])
    if mode == "formal":
        tracked += list(manifest["tier2"]["tracked"])
    prefixes = [str(g) for g in manifest["generated"]]
    for rel in tracked:
        if any(rel.startswith(g) for g in prefixes):
            probs.append(f"PREREG FAIL: {rel} is listed as preregistered but lies under a generated prefix")

    def same_in_tag(rel, what):
        path = _abs(repo, rel)
        if not os.path.isfile(path):
            probs.append(f"PREREG FAIL: {what} {rel} is missing")
            return False
        if not committed_unchanged(path):
            probs.append(f"PREREG FAIL: {what} {rel} is not tracked or differs from HEAD")
            return False
        if blob_at(tag_ref, path) != rp.read_bytes(path):
            probs.append(f"PREREG FAIL: {what} {rel} is not in tag {tag} or differs from the tagged version")
            return False
        return True

    same_in_tag(MANIFEST, "manifest")
    try:
        for rel in _untracked_under(repo, SCRIPTS_DIR):
            probs.append(f"PREREG FAIL: untracked file {rel} under {SCRIPTS_DIR} (not preregistered; it could shadow "
                         f"an import of the preregistered scripts)")
    except PreregError as e:
        probs.append(f"PREREG FAIL: {e}")
    for rel in sorted(set(tracked)):
        same_in_tag(rel, "preregistered file")

    for rel, want in sorted(manifest["tier1"]["local_hash"].items()):
        try:
            got = rp.sha256(_abs(repo, rel))
        except OSError as e:
            probs.append(f"PREREG FAIL: local file {rel} cannot be read ({e.__class__.__name__})")
            continue
        if got != str(want).lower():
            probs.append(f"PREREG FAIL: local file {rel}: sha256 {got} != preregistered {want}")

    for which in LISTS_BY_MODE[mode]:
        lst = LISTS[which]
        same_in_tag(lst, "hash list")
        if not os.path.isfile(_abs(repo, lst)):
            continue
        listed = {}
        for ln in rp.read_bytes(_abs(repo, lst)).decode("utf-8").splitlines():
            parts = ln.split(None, 1)
            if len(parts) != 2 or len(parts[0]) != 64:
                probs.append(f"PREREG FAIL: {lst}: malformed line {ln!r}")
                continue
            want, rel = parts[0].lower(), parts[1].strip()
            listed[rel] = want
            try:
                got = rp.sha256(_abs(repo, rel))
            except OSError as e:
                probs.append(f"PREREG FAIL: {lst}: {rel} cannot be read ({e.__class__.__name__})")
                continue
            if got != want:
                probs.append(f"PREREG FAIL: {lst}: {rel}: sha256 {got} != listed {want}")
        try:
            members = _list_members(manifest, which, repo)
        except PreregError as e:
            probs.append(f"PREREG FAIL: {lst}: {e}")
            continue
        for rel in members:
            if rel not in listed:
                probs.append(f"PREREG FAIL: {lst} does not list {rel}")
    return probs
