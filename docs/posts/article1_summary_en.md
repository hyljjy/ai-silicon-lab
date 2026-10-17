# Can LLMs read a timing report? Checking the diagnoses of Claude Opus 5.5, Kimi K3 and DeepSeek V4 Pro with OpenSTA

*AI timing advice, checked by engineering experiments · CASE-01, stage A · English summary*

This is a summary of article 1. The Chinese [WeChat version](article1_public.md) is the readable article; the Chinese [full version](article1_draft.md) gives the source file and line of every number. To check the results yourself, see [REPRODUCE.en.md](../../REPRODUCE.en.md).

## What we did

We gave the same timing report to three large language models and asked them why a path fails timing and how to fix it. We did not judge whether the answers sounded right. We split each answer into individual claims and checked every claim that could be checked: statements about numbers and objects in the report against the report itself; statements of the form "if we change this, then that" with a query or a controlled run in a fixed analysis model, using criteria written down before running anything. Claims that could not be settled were labelled *undecided*; proposed RTL changes were left for the next stage.

The three models were identified by the parameters of the calls and the model names in the responses: `claude-opus-5-5`, `k3` and `deepseek-v4-pro`. Kimi and DeepSeek were reached through their Anthropic-compatible endpoints, so which model actually answered cannot be verified independently.

## The design and the failing path

The design under test is small: four signed 16×16 products are summed into a 34-bit exact sum and saturated to 32 bits. The whole computation sits in one clock cycle; only the output is registered (latency L = 1).

The clock period was set to 27.91 ns by a calibration rule fixed in advance, so that the worst setup slack is about −15% of the period: a design that clearly fails, for the models to diagnose.

At the worst of the six PVT corners checked (slow-slow, 1.60 V, −40 °C), the reported worst path runs from input `in_b[2]` through 37 combinational cells to an output register. Data arrives at 31.54 ns but must arrive by 27.35 ns (the period minus a 0.56 ns setup requirement): setup slack −4.19 ns. Of that arrival time, 5.58 ns is the external input delay set by the constraints (0.2T). Only the two slow-slow corners fail; the four typical and fast corners have large positive slack.

The analysis model is deliberately simple, and every conclusion is limited to it: post-synthesis, ideal clocks, no wire RC (pin capacitance and output load are counted), input driver transition set to 0 ns, a synthesis recipe specific to this case with no clock or IO timing targets and no physical repair, and only these six corners. Nothing here predicts silicon or post-route timing.

## How the experiment was run

- **Same input.** All three models received the same material: the path report, the SDC, a slack summary per corner, the RTL, and a one-page background note.
- **Same shell.** All three were called through the same version of the Claude Code command-line client (2.1.296) with tools disabled, the same system prompt and an output cap of 32,000 tokens. Server-side and compatibility-layer differences remain.
- **Two rounds.** In round 1 each model read the material and wrote a diagnosis. In round 2 each model received the tool output of *its own* round-1 queries and could revise its claims.
- **Partial blinding.** The answers were randomly coded A, B and C before they were split and labelled. The code-to-model mapping was salted, kept outside the repository, and its hash committed before round 1.
- **Same-model risk.** The operator who split the answers, wrote the criteria and assigned the labels is itself a Claude model, the same model as the one under test. Writing the criteria before running the checks was meant to limit this bias.

Facts were labelled *confirmed*, *refuted* or *unverifiable*; hypotheses *supported*, *refuted*, *undecided* or *needs stage B*. "Supported" only means the part actually tested was supported, not that the whole explanation is right; "undecided" does not mean the model was wrong.

## Three findings

**1. Fixing a local bottleneck is not fixing the design.** All three models pointed to a high-fan-out control signal near the end of the path; we call it X. X feeds logic that leads to 31 of the 32 output bits. Claude made the most specific claim: X is driven by a weak cell that adds about 2.5–3 ns. It also stated how to refute this: replace the driver with a stronger one, and if the *worst slack of the whole design* improves by less than 1 ns, the claim does not hold.

We did exactly that. After upsizing the cell that drives X:

- the original path improved by 2.30 ns,
- but the worst slack of the whole design improved by only 0.67 ns.

The worst path simply moved to a neighbouring signal, Y, which also has 31 loads; the design has 27 endpoints tied at the worst slack. By Claude's own criterion its claim is refuted. In round 2, after seeing the 0.67 ns result, Claude itself downgraded X from "adds 2.5–3 ns" to "a secondary factor". A practical lesson: watching one path improve is not enough; watch the design's worst slack.

In a wider control we upsized all 37 combinational cells on the original path. That path was still short by about 2.12 ns: this sizing change did not remove the violation.

**2. Positive slack can come from changing the budget, not the circuit.** All three models predicted what would happen without the 5.58 ns external input delay. Setting it to zero gives +1.39 ns, and all three predictions were supported. But nothing was improved: the RTL and the circuit are unchanged, only the time the constraints assign to the outside world was removed. Likewise, raising the period to 33.15 ns while scaling the input and output delays to 6.63 ns gives about +0.002 ns: the check changed, the circuit did not get faster. Such controls help check a diagnosis; they cannot be counted as optimization.

This matters for the next stage. "Register the inputs first" moves the long combinational logic between two registers, so it no longer pays the input delay of the same transaction; it may close timing, but the gain has to be explained, and the cost is one more cycle of latency and more registers.

**3. A clean second round does not mean the first round's errors were corrected.** By the splitting and labelling rules used, every round-2 statement classed as a fact was confirmed. But by the judgment-id links, none of the five refuted round-1 facts received a round-2 review entry. The errors did not disappear: DeepSeek still wrote "130 paths" in a round-2 missing-evidence item, a premise refuted in round 1. The models were never shown our labels, so they got no item-by-item feedback. Measuring correction would require deciding in advance whether to show the disputed items and asking for an answer to each.

## Where the models went wrong

By the rules of this study, five round-1 facts were refuted: 3 of Claude's 43, 2 of DeepSeek's 13, and none of Kimi's 35; one more Claude fact could not be verified. These counts describe these three answers only. Answer lengths and splitting granularity differ, and each model ran once, so they must not be used to rank the models.

- **Misreading a table.** DeepSeek wrote that there are "130 input-to-register paths". The column counts *startpoints*; one startpoint can reach many paths.
- **Rounding across a boundary.** Two of Claude's approximate values, about 25.65 and 12.85, should read 25.7 and 12.9 at one decimal, but were written as 25.6 and 12.8. The tolerance rule, fixed in advance and applied to every model, judges this as refuted.
- One generalization by Claude about the delay range of a cell type, and one subtraction error by DeepSeek.

**Queries.** In round 2 we ran the queries the models wrote. All three answers contained command or option errors in this OpenSTA version: commands that do not exist, invalid options, or an object passed to a command that expects a name. Some code blocks still returned partial results. Proposing what to look at and writing a command that runs in the current tool version are two different skills, and the gap directly limits what a model learns in round 2.

## Where we went wrong

- The author's reference answer, written before the models ran, subtracted two rounded numbers and wrote −4.1897 where 27.3541 − 31.5439 = −4.1898, and claimed there was no last-digit difference.
- One control meant to make the input drivers ideal used a command that the constraints overrode, so it had no effect.
- **16 labels were corrected after unblinding**, for reasons including criteria that did not follow the model's own refutation condition, numeric windows of inconsistent strictness, and citations that covered only part of a sentence. Most of the corrections went against Claude. The original labels and the final statistics are both in the repository; the item-by-item rulings are not published.

## What the models proposed, and what comes next

All three proposed adding pipeline stages, but at different places: registering the inputs, registering the products, or registering both the products and the sum (L = 3). Kimi also ranked arithmetic optimizations without pipelining first. These are candidates only.

Stage B will let the models change the RTL, at most two rounds, each with a prediction written down first. Each candidate must pass the same functional tests (including gate-level simulation), keep L ≤ 3 and one transaction per cycle, leave the interface and IO constraints unchanged, stay within 1.25× the baseline area, and be checked for setup and hold at all six corners — new register-to-register paths need a hold check, since the baseline's smallest hold margin is about 0.06 ns. If two rounds bring no gain, the failure analysis will be published.

## Bottom line

All three answers pointed to directions worth testing. But reading numbers correctly, forming hypotheses, writing queries that run, and actually improving the RTL are four different things; this stage checked only the first ones. Treat an LLM's timing diagnosis as a starting point to verify, not as a conclusion.

## Reproducibility

The tool layer has been replicated from a clean clone on the author's machine: the regenerated netlist and baseline match the study byte for byte, and all 24 base checks and rechecks reproduce (23 byte-identical, 1 identical once object addresses are masked). See [REPRODUCE.en.md](../../REPRODUCE.en.md) for how to run it yourself, and for what that run did not cover.

Repository: https://github.com/hyljjy/ai-silicon-lab
