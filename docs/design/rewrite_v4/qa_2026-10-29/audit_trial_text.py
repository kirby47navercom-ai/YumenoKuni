"""Audit trial dialogue bounds. This is not a game runner or a single-route playtime test."""
from pathlib import Path
import collections
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
# Mixed-mode files must contribute only the sections entered during the trial.
CUTS = {
 1: {123: ("## T-01P", None), 93: (None, "## R-05b")},
 2: {97: (None, "## R2-09b"), 169: ("## T2-LIE-01", "## R2-LIE-B"),
     179: ("## T2-18-W179", None), 141: (None, "## R2-09c")},
 3: {110: ("## T3-02a", None), 169: ("## T3-F-T2-LIE-B", "## T4-LIE-01"),
     128: ("## T3-23P", None), 102: (None, "## R3-04a"), 172: ("## T3-39-F-172", None)},
 4: {169: ("## T4-LIE-01", "## R4-LIE-B"), 99: (None, "## R4-07a")},
 5: {100: (None, "## R5-06a"), 169: ("## T5-LIE-01", "## R5-LIE-B")},
 6: {104: (None, "## R6-11a"), 169: ("## T6-LIE-01", "## R6-F-LIE-B")},
}
ROSTER = set("미오 린 나나 사츠키 쇼 하루카 유우 소라 아카리 코토 리쿠 레이 켄 타이가 카에데 아이 래피".split())
LINK = re.compile(r"\]\(([^\n)]+\.md(?:#[^\n)]*)?)\)")
DIALOGUE = re.compile(r"^\[([^\]]+)\]\s+(.+)$")
rows = []
for chapter in range(1, 7):
    parents = sorted(ROOT.glob(str(chapter + 10) + "c*.md"))
    assert len(parents) == (2 if chapter == 1 else 3)
    files = {p.name: p for p in parents}
    for p in parents:
        for ref in LINK.findall(p.read_text(encoding="utf-8")):
            q = ROOT / ref.split("#")[0]
            files[q.name] = q
    if chapter == 5:  # 167 enters this nested block.
        q = next(ROOT.glob("169_*.md"))
        files[q.name] = q
    dialogue, sources, transitions = [], [], collections.Counter()
    for p in files.values():
        full = p.read_text(encoding="utf-8")
        prefix = int(re.match(r"\d+", p.name)[0])
        begin, end = CUTS.get(chapter, {}).get(prefix, (None, None))
        a = full.index(begin) if begin else 0
        b = full.index(end, a + 1) if end else len(full)
        lines = []
        for offset, line in enumerate(full[a:b].splitlines()):
            m = DIALOGUE.match(line)
            if m:
                body = re.sub(r"[*_`~]", "", m[2])
                lines.append({"speaker": m[1], "body": body})
        dialogue.extend(lines)
        spoken = [x["speaker"].split("·")[0] for x in lines
                  if "속말" not in x["speaker"] and x["speaker"].split("·")[0] in ROSTER]
        transitions.update((x, y) for x, y in zip(spoken, spoken[1:]) if x != y)
        sources.append({"path": p.name, "begin": begin, "end_exclusive": end,
                        "full_source_sha256": hashlib.sha256(full.encode()).hexdigest(),
                        "start_line": full[:a].count("\n") + 1,
                        "end_line": full[:b].count("\n") + 1,
                        "dialogue_lines_all_branches": len(lines)})
    chars = sum(len(re.sub(r"\s", "", x["body"])) for x in dialogue)
    spoken = [x for x in dialogue if "속말" not in x["speaker"]
              and x["speaker"].split("·")[0] in ROSTER]
    mio = sum(x["speaker"].split("·")[0] == "미오" for x in spoken)
    rows.append({"chapter": chapter, "dialogue_characters_all_branches_upper_bound": chars,
                 "dialogue_lines_all_branches": len(dialogue),
                 "mio_share_of_spoken_corpus": round(mio / len(spoken), 4),
                 "npc_to_npc_speaker_changes_in_source_blocks": sum(
                     n for (x, y), n in transitions.items() if x != "미오" and y != "미오"),
                 "all_branch_reading_minutes_under_assumptions": {
                     str(rate): round(chars / rate, 1) for rate in (250, 400)},
                 "sources": sources})
report = {"scope": "Explicit dialogue including thoughts in the trial parents and their designated inserts.",
          "single_route": False, "runtime_playtest": False,
          "reading_rates_are_assumptions_not_measured_human_rates": [250, 400],
          "limitations": [
              "All alternatives and authored failures are retained, so these are dialogue bounds, not route totals.",
              "Do not add dialogue from daily setup, result callbacks or whole multi-chapter files.",
              "No duration is assigned to animation, thinking, input, UI prompt reading, travel, failed attempts or forced waiting.",
              "Character transitions count source blocks, not an executed path or the quality of an argument.",
              "Without a repeat or reread, any supported normal route has no more explicit [speaker] dialogue than this bound. UI prompts and stage directions are outside this metric."
          ], "chapters": rows}
output = Path(__file__).with_name("trial_text_bounds.json")
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps([{k: v for k, v in x.items() if k != "sources"} for x in rows], ensure_ascii=False))
