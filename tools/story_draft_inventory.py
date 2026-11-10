"""Measure authored v4 text without presenting branch totals as play time."""
from pathlib import Path
from datetime import date
import hashlib
import json
import re


ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "docs/design/rewrite_v4"
DIALOGUE = re.compile(r"^\[([^\]]+)\]\s+(.+)$")
rows = []
for path in sorted(DRAFT.glob("*.md")):
    source = path.read_text(encoding="utf-8")
    if "\ufffd" in source:
        raise ValueError(f"Invalid replacement character: {path.name}")
    speech = []
    speakers = {}
    for line in source.splitlines():
        match = DIALOGUE.match(line)
        if match:
            speaker, body = match.groups()
            speech.append(body)
            speakers[speaker] = speakers.get(speaker, 0) + 1
    rows.append({
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "text_characters": len(source),
        "dialogue_lines_all_branches": len(speech),
        "dialogue_characters_without_whitespace_all_branches": sum(
            len(re.sub(r"\s+", "", body)) for body in speech
        ),
        "speakers": speakers,
    })

manuscripts = [row for row in rows if row["dialogue_lines_all_branches"]]
report = {
    "as_of": date.today().isoformat(),
    "status": "in_progress",
    "method": "Count explicit [speaker] dialogue; include thoughts and all authored alternative branches. Do not count design-table examples as playable dialogue.",
    "limitations": [
        "All-branch totals are not the amount read on one playthrough.",
        "No reading-speed, route-playtime or runtime claim is made.",
        "A long design document does not satisfy manuscript length.",
        "The full six-chapter rewrite and requested duration remain unfinished.",
    ],
    "manuscript_files": len(manuscripts),
    "dialogue_lines_all_branches": sum(row["dialogue_lines_all_branches"] for row in rows),
    "dialogue_characters_without_whitespace_all_branches": sum(
        row["dialogue_characters_without_whitespace_all_branches"] for row in rows
    ),
    "files": rows,
}
output = DRAFT / "draft_inventory.json"
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: report[key] for key in (
    "status", "manuscript_files", "dialogue_lines_all_branches",
    "dialogue_characters_without_whitespace_all_branches",
)}, ensure_ascii=False))
