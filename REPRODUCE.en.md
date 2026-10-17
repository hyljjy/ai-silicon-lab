# Reproducing CASE-01, stage A

[中文版](REPRODUCE.md)

This guide is for readers who want to check the conclusions of article 1 themselves: start from the public material, run everything again without using the author's results, and compare with what is recorded in this repository.

The experiment has three layers, which reproduce to different degrees:

| Layer | What it is | What a reproduction should give |
|---|---|---|
| Tools | Synthesis, STA, 6 base checks, 18 rechecks and controls | **Byte-identical** netlist and query outputs, given the same tool versions |
| Judgments | Splitting each answer into claims and labelling them by rule | Your own claim table, to compare with `claims.tsv` |
| Models | Asking the three models to read the material and answer again | **Not** identical answers; this is a new run, to compare whether the conclusions are similar |

Paths below are relative to `tasks/CASE-01/` unless they start at the repository root.

## 1. Environment

Follow [env/SETUP.md](env/SETUP.md) to install OSS CAD Suite, OpenSTA and the Sky130 PDK on Ubuntu 24.04 (native, or in WSL2) and pass the smoke test. The guide is in Chinese, but it is mostly commands; the versions, sources, checksums and build steps are in [env/INSTALL_RECORD.md](env/INSTALL_RECORD.md). In short:

- OSS CAD Suite release `2026-10-03` (Yosys 0.69+187, ABC, Icarus Verilog), installed under `~/tools/oss-cad-suite`;
- CUDD 3.0.0 and OpenSTA at commit `7a034b56de14b485ddf8fd97b420a6f37a91c00d`, built from source into `~/tools`;
- Sky130 PDK `1689ac3f2dc763876eaf967227c7dfe831b031ae` via ciel 3.0.0, `sky130_fd_sc_hd` only, under `~/pdk`;
- `env/open_eda_env.sh` copied to `~/tools/` and sourced from `~/.profile` and `~/.bashrc`; the kit scripts in `env/sky130hd_kit/` copied to `~/pdk/sky130hd_kit/`; the smoke test in `env/smoke/sky130/` copied to `~/smoke/sky130/`;
- `~/smoke/sky130/run.sh` must end with `SMOKE OK` and print the numbers listed in `env/SETUP.md` section 4.

The versions must match: a different Yosys/ABC or OpenSTA can give a different netlist and different timing numbers.

**Install and run as user `eda` with HOME `/home/eda`.** The F1 evidence `evidence/F1/sta_results.tsv` records the absolute liberty paths `/home/eda/pdk/...`, and the replication compares it byte for byte; under another user that check necessarily fails.

Run every command below in a login shell, from `tasks/CASE-01/`.

## 2. Tool layer

**Step 1: regenerate the F1 baseline.** The frozen grader runs RTL simulation, synthesis, gate-level simulation and STA at the six PVT corners, starting from the RTL:

```bash
python3 scripts/grade.py --impl config/impl.base.cfg
# on another machine, where you built OpenSTA yourself, add: --allow-tool-drift
```

The first line is `RUN_ID=<id>`; the last line should be `GRADE OK`, with `worst_setup` slack `-4.189726…` (ss_n40C_1v60), `worst_hold` `0.059112…` (ff_100C_1v95) and area `45383.5264`. The results go to `runs/<id>/`, which is not tracked by git.

**Step 2: re-run all base checks and rechecks and compare with the committed outputs.**

```bash
python3 -B diag/scripts/replicate.py --f1-run runs/<id>
# on another machine, where you built OpenSTA yourself, add: --allow-tool-drift
```

[diag/scripts/replicate.py](tasks/CASE-01/diag/scripts/replicate.py) does three things:

1. It checks the regenerated baseline: the netlist sha256 must equal the F1 netlist of the study, and `sta_results.tsv` and the worst-path report given to the models must equal the copies in `evidence/F1/` byte for byte.
2. It runs the 6 base checks in `diag/queries/base/` and the 18 rechecks in `diag/queries/recheck/` again on the new baseline, each with the `query.tcl` that was actually run, the same mode and `--strict-log`.
3. It compares each new `query_full.txt` with the committed one: `identical` (byte for byte), `identical-masked` (equal once object addresses are masked; OpenSTA prints a different address in every process), or `different`.

When everything holds it prints `REPLICATION OK` and writes a report to `runs/<time>-replicate.md`.

**About `--allow-tool-drift`.** Both the grader and the query executor run `env/snapshot.sh check`, which compares the tool binaries with `env/tools.sha256`. OpenSTA and CUDD are built from source, so on another machine their binaries will differ even at the same commit.

Both scripts take this flag, but they relax the check to different degrees:

- `grade.py` accepts only a different `opensta/bin/sta` fingerprint and nothing else in the snapshot log. The OSS CAD Suite tools from the release tarball, the kit scripts, the liberty files and the snapshot files must all still match. The drifted binary and its sha256 are recorded under `env_snapshot` in `verdict.json`. This is the frozen revision v1.4 of the contract (version record in `tasks/CASE-01/spec.md`).
- `replicate.py` applies the same rule to each query and reports an accepted one as "tool drift".

Whether the tools are really equivalent is decided by the netlist hash and the query outputs.

**About the pre-registration.** The query executor `run_query.py` was changed after the study (to kill child process trees on Windows; behaviour on Linux is unchanged), so it no longer matches the pre-registered executor manifest, and run directly it refuses to run. `replicate.py` skips only that self-check; every other environment check still runs: environment snapshot, netlist hash, frozen inputs, STA records byte for byte against the baseline, log check. Every replicated `result.json` carries a `"replication"` field.

## 3. Judgment layer

This layer tests whether the claims were split and labelled correctly, and needs none of the author's results:

1. Read the material `diag/package/` and the six answers `diag/outputs/round1/{A,B,C}.md` and `diag/outputs/round2/{A,B,C}.md`. The code-to-model mapping is in `diag/outputs/mapping.json`; to stay blind, do not open it yet.
2. Split the answers into claims by section 6 of the protocol [diag/protocol.md](tasks/CASE-01/diag/protocol.md) and label them by section 7.3. The additional splitting rules G1–G12 are in the comment block at the top of [diag/claims.tsv](tasks/CASE-01/diag/claims.tsv). (The protocol and the claim table are in Chinese.)
3. Check facts against the material or the tool-layer outputs; check hypotheses with tool-layer queries or controls against criteria you write down first. New queries can be written as `.tcl` files and run the same way, through `diag/scripts/run_query.py`.
4. Compare your table with `diag/claims.tsv`. Its `label` column holds the labels as first assigned (statistics in `diag/stats.md`); the article uses the final labels after the post-unblinding correction (statistics in `diag/stats_revised.md`).

If your table uses the column format of `claims.tsv`, `diag/scripts/claims_stats.py --claims <your table>` gives statistics in the same format.

## 4. Model layer

The material, the prompts of both rounds (`diag/prompts/`), the system prompt and the model settings with keys removed (`diag/models/`) are in the repository. A re-run will not reproduce the original answers word for word: the models are stochastic, and the hosted models may change. Such a re-run is a new experiment, useful to compare whether the conclusions are similar and whether the same kinds of mistakes recur.

`diag/scripts/run_round.py` hard-codes the author's path to the command-line client; change it to yours, and supply your own keys. The author has not verified this layer.

## 5. Not in this repository

The execution and implementation plans with their prototype code, the review records, the intervention log, the item-by-item rulings of the post-unblinding review, and the author's environment debugging notes are not published. Therefore:

- the final statistics `diag/stats_revised.md` can be read but not recomputed from public files;
- `diag/impl_plan.md`, listed in the pre-registration manifest `diag/rules/preregistered.txt`, cannot be checked.

## Measured replication

On 2026-10-17, on the author's machine (WSL2 Ubuntu 24.04, environment identical to the `env/` snapshot), starting from a clean clone of this repository and following section 2:

| Step | Result |
|---|---|
| `env/snapshot.sh check` | `SNAPSHOT OK` |
| `grade.py --impl config/impl.base.cfg` | `GRADE OK`; worst setup −4.189726 ns (ss_n40C_1v60, in2reg), worst hold +0.059113 ns (ff_100C_1v95), area 45383.5264 |
| F1 baseline | netlist sha256, `sta_results.tsv` and the worst-path report byte-identical to the study |
| 6 base checks | 6 `identical` |
| 18 rechecks and controls | 17 `identical`; `rc_A-1-093` `identical-masked` (it prints object addresses) |
| Overall | `REPLICATION OK`, about 6 minutes from regenerating the baseline to the last comparison |

Not covered by this run:

- another machine with a fresh installation; the `--allow-tool-drift` path was not exercised (the snapshot matched exactly on the author's machine);
- an independent redo of the judgment layer by someone else;
- a re-run of the model layer.
