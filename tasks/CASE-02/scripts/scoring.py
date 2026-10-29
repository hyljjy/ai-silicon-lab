"""Scoring helpers shared by the operator's table work (protocol v0.3 sections 6.3, 7). Task 7 provides
core_window; Task 8 adds the field vocabularies used by claims_stats."""
import re

HEADINGS = [re.compile(r"^\s*(?:#+\s*)?一\s*[、.．]\s*观察"), re.compile(r"^\s*(?:#+\s*)?二\s*[、.．]\s*结论"),
            re.compile(r"^\s*(?:#+\s*)?三\s*[、.．]\s*证据"), re.compile(r"^\s*(?:#+\s*)?四\s*[、.．]\s*检查请求")]
CORE_LINES = 120


def core_window(answer_text, limit=CORE_LINES):
    """The part of an answer that enters the core scoring: from the first of the four section headings, the first
    `limit` lines (protocol 6.3: 四栏合计不超过 120 行). Without any heading, the first `limit` lines of the text."""
    lines = answer_text.splitlines()
    start = next((i for i, l in enumerate(lines) if any(h.match(l) for h in HEADINGS)), 0)
    return "".join(l + "\n" for l in lines[start:start + limit])
