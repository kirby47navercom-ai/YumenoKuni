"""Check the shipped Nonstop mark progression against its authored lines."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "data/v4_story"
tasks = json.loads((ROOT / "native_tasks.json").read_text(encoding="utf-8"))["tasks"]
direction = json.loads((ROOT / "trial_direction.json").read_text(encoding="utf-8"))
import sys
sys.path.insert(0,str(ROOT.parents[1]/'tools'))
from v4_noise_bindings import apply_noise
for task in tasks.values():
    if task['stage']['kind']=='nonstop':assert apply_noise(task)==task
chapters = {}
# White Noise starts at the fourth actual Nonstop in the graph.
intro_quiet = {"T1-NS-A01", "T1-NS-A02", "T1-NS-A03"}
chapter = json.loads((ROOT / "chapters/1.json").read_text(encoding="utf-8"))
ordered = sorted((n for n in chapter["nodes"].values() if n.get("taskId", "").startswith("T1-NS-") and n.get("source", {}).get("file", "").startswith("11c1_")), key=lambda n:n["source"]["line"])
assert [n["taskId"] for n in ordered[:5]] == ["T1-NS-A01", "T1-NS-A02", "T1-NS-A03", "T1-NS-A05", "T1-NS-T05e"]

for task_id, task in tasks.items():
    if task["stage"]["kind"] != "nonstop":
        continue
    chapter = int(task_id[1])
    count = Counter()
    rows = task["debate"]["lines"] + direction["extra"].get(task_id, [])
    evidence = {row["id"] for row in task["stage"]["options"]}
    ammo = direction["nonstopAmmo"][task_id]
    assert 3 <= len(ammo) <= 5 and len(set(ammo)) == len(ammo), task_id
    assert set(task["requiresEvidence"]) <= set(ammo), task_id
    transformed = task.get("transformation", {}).get("sourceEvidenceId")
    assert not transformed or transformed in ammo, task_id
    for row in rows:
        direction_row = direction["debate"].get(row["id"], {})
        mark = direction_row.get("decoy")
        opening = direction_row.get("openingRefutation")
        kind = row.get("kind", "plain")
        if mark:
            assert kind == "plain" and mark["word"] in row["text"], (task_id, row["id"])
            kind = mark["kind"]
        if opening:
            assert chapter == 1 and kind == "agree" and row["agree"] in evidence, task_id
            assert opening["word"] in opening["text"], task_id
            kind = "weak"
        if row.get("weak"):
            assert row["weak"]["answer"] in evidence, task_id
            assert row["weak"]["answer"] in ammo, task_id
        if row.get("agree"):
            assert row["agree"] in ammo, task_id
        if row.get("lieWeak"):
            assert row["lieWeak"]["answer"] in ammo, task_id
        count[kind] += 1
    assert count["weak"] >= 2, task_id
    assert (count["agree"] == 0 if chapter == 1 else count["agree"] >= 1), task_id
    if task_id in intro_quiet:
        assert not direction["noise"].get(task_id) and not count["noise"], task_id
    else:
        assert direction["noise"].get(task_id) or count["noise"], task_id
    chapters.setdefault(chapter, Counter()).update(rounds=1, yellow=count["weak"], blue=count["agree"])
first_lie = tasks["T1-LIE-01"]
assert first_lie["transformation"]["intentionalHold"]
assert any(row.get("lieWeak") for row in first_lie["debate"]["lines"])
assert {route["judgment"] for route in first_lie["outcomes"].values()} == {"refute", "lie"}
followup = json.loads((ROOT.parents[1]/'data/presentation/nonstop_followup.json').read_text(encoding='utf-8'))['tasks']
assert set(followup) == {tid for tid,task in tasks.items() if task['stage']['kind']=='nonstop'}
for tid, row in followup.items():
    assert 20 < len(row['hint']) < 150,tid
    assert not any(term in row['hint'] for term in ['범인은','정답은','언령을','쏘면','맞혀','논파','위증','동의','찬성','힌트','좌클릭','우클릭','버튼']),tid
    for option in tasks[tid]['stage']['options']:
        label = option.get('label',option.get('text',''))
        if len(label)>=8: assert label not in row['hint'],(tid,label)
assert len({row['hint'] for row in followup.values()}) == len(followup), 'Each round needs its own reasoning'
print(json.dumps(chapters, ensure_ascii=False))
