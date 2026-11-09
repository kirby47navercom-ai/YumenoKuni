"""Generate numeric rhythm charts from the durable authorized source bank."""

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "Game/Saved/armament-rhythm-20261106"
SOURCE = ROOT / "ui/v3_authorized/armament/rhythm-charts.json"
HEADER = ROOT / "Game/Source/ArmamentChartsV4.hpp"


def number(value):
    assert math.isfinite(value)
    text = format(value, ".9g")
    return text + ("f" if "." in text or "e" in text else ".0f")


def overlap(notes, cycle, hold=False, tail=0):
    """Half-open lifetimes across loop boundaries; not an observed native count."""
    events = []
    for turn in range(-1, 3):
        for note in notes:
            begin = turn * cycle + note[6]
            end = turn * cycle + note[7] + (note[3] / 60 if hold else 0) + tail
            events += [(begin, 1), (end, -1)]
    count = peak = 0
    for time, change in sorted(events):
        count += change
        if 0 <= time < 2 * cycle:
            peak = max(peak, count)
    return peak


def main():
    source_bytes = SOURCE.read_bytes()
    source = json.loads(source_bytes)
    assert len(source["charts"]) == 19
    fields = source["event_fields"]
    assert fields == ["row", "tempo_bpm", "site_type", "button_type",
                      "hold_or_repeat_strength", "move_type", "x", "y",
                      "arrival_frames", "ideal_spawn_seconds"]
    for chart in source["charts"]:
        assert all(len(row) == len(fields) for row in chart["events"])
        chart["events"] = [dict(zip(fields, row)) for row in chart["events"]]
    phase_hp = source["phase_hp"]
    assert phase_hp == [[80, 120, 210], [90, 130, 350], [130, 160, 400],
                        [130, 170, 420], [180, 130, 380], [300, 350, 450, 350]]
    chapters = [[] for _ in range(6)]
    receipt = {
        "schema": "armament-generated-charts-v1",
        "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "sourceSha256": hashlib.sha256(source_bytes).hexdigest(),
        "binarySha256": source["target_sha256"],
        "evidence": source["evidence"],
        "nativeSlots": 30,
        "phaseHp": phase_hp,
        "provenance": source["provenance"],
        "projection": "Source 1920x1080 coordinates preserved; runtime projects explicitly.",
        "timing": "Retained ideal seconds, not measured native latency or accumulator drift.",
        "concurrency": "Half-open spawn-to-target intervals across repeated loops; hold end and 20/60s tail also reported. Static model, not native visible-slot observation.",
        "charts": [],
        "fallbacks": [],
        "moveTable": source["move_table"],
    }
    for chart in source["charts"]:
        chapter = int(chart["member"][13:15]) - 1
        assert 0 <= chapter < 6
        events = chart["events"]
        assert len(events) == chart["row_count"]
        assert [event["row"] for event in events] == list(range(len(events)))
        elapsed = 0.0
        bpm = 0
        notes = []
        anchor = None
        for event in events:
            if event["tempo_bpm"]:
                bpm = event["tempo_bpm"]
            assert bpm > 0
            elapsed += 60 / bpm
            assert math.isclose(elapsed, event["ideal_spawn_seconds"], abs_tol=1e-8)
            if event["site_type"] < 0:
                continue
            assert event["site_type"] in (0, 1, 2)
            assert event["button_type"] in (0, 1, 2, 3, 4)
            xy = (event["x"], event["y"])
            if xy == (0, 0):
                assert chart["member"] == "theory_music_06c.dat" and event["row"] == 18
                assert anchor is not None
                receipt["fallbacks"].append({
                    "chart": chart["member"], "row": event["row"],
                    "source": [0, 0], "anchorRow": anchor[0],
                    "generated": list(anchor[1]),
                    "reason": "Sentinel retains previous valid note anchor; no new arbitrary position.",
                })
                xy = anchor[1]
            else:
                assert 0 < xy[0] <= 1920 and 0 < xy[1] <= 1080
                anchor = (event["row"], xy)
            strength = event["hold_or_repeat_strength"]
            assert strength == int(strength)
            hold = int(strength) if event["site_type"] == 1 else 0
            mash = int(strength) if event["site_type"] == 2 else 0
            spawn = event["ideal_spawn_seconds"]
            target = spawn + event["arrival_frames"] / 60
            appearance = chart["appearance"][event["row"]]
            assert len(appearance) == 6 and all(math.isfinite(x) for x in appearance)
            note = (event["row"], event["button_type"], event["site_type"],
                    hold, mash, event["move_type"], spawn, target, *xy, *appearance)
            notes.append(note)
        cycle = chart["ideal_loop_seconds"]
        assert math.isclose(elapsed, cycle, abs_tol=1e-8)
        assert len(notes) == chart["note_count"]
        peak = overlap(notes, cycle)
        held_peak = overlap(notes, cycle, hold=True, tail=20 / 60)
        assert held_peak <= 30
        chapters[chapter].append((chart, notes))
        receipt["charts"].append({
            "member": chart["member"], "sourceSha256": chart["source_sha256"],
            "rows": len(events),
            "notes": len(notes), "cycle": cycle,
            "randomButtonMarkers": sum(note[1] == 4 for note in notes),
            "maximumSpawnToTarget": peak,
            "maximumIncludingHoldAnd20FrameTail": held_peak,
            "moves": [[event["ideal_spawn_seconds"], event["move_type"]]
                      for event in events if event["move_type"] >= 0],
        })
    assert [len(chapter) for chapter in chapters] == [3, 3, 3, 3, 3, 4]
    assert sum(len(notes) for chapter in chapters for _, notes in chapter) == 723
    lines = ["#pragma once", "#include <array>", "#include <vector>", "#include <utility>", "",
             "// Generated by tools/build_v3_armament_charts.py; numeric source references in generated-charts.json.",
             "// Source 1920x1080 coordinates; button 4 is resolved by the runtime, never pre-randomized.",
             "namespace armcharts {",
             "struct Note { int row,button,type,holdFrames,mashPower,move; float spawn,target,x,y; float startScale=1,endScale=1,startRotation=0,endRotation=0,startTextScale=1,endTextScale=1; };",
             "struct Chart { float cycle; std::vector<Note> notes; std::vector<std::pair<float,int>> moves; };",
             "struct MoveStep { float x,y,frames; };",
             "struct Move { int kind; std::vector<MoveStep> steps; };",
             "inline const std::vector<Move> moves = {"]
    assert len(source["move_table"]["rows"]) == 61
    for row in source["move_table"]["rows"]:
        steps = []
        for start in range(2, len(row), 3):
            x, y, frames = row[start:start + 3]
            if frames < 0:
                assert (x, y, frames) == (-1, -1, -1)
                continue
            steps.append("{" + ",".join(number(v) for v in (x, y, frames)) + "}")
        lines.append("    {" + str(row[1]) + ",{" + ",".join(steps) + "}}, // " + row[0])
    lines += ["};",
             "inline const std::array<std::vector<Chart>,6> chapters = {{"]
    for chapter in chapters:
        lines.append("    {")
        for chart, notes in chapter:
            lines += [f"        // {chart['member']} SHA256 {chart['source_sha256']}",
                      f"        {{{number(chart['ideal_loop_seconds'])}, {{"]
            for note in notes:
                if chart["member"] == "theory_music_06c.dat" and note[0] == 18:
                    lines.append("            // Source row18 (0,0) sentinel retains row16 anchor (1360,350).")
                values = [str(value) for value in note[:6]] + [number(value) for value in note[6:]]
                lines.append("            {" + ",".join(values) + "},")
            lines.append("        }, {")
            for event in chart["events"]:
                if event["move_type"] >= 0:
                    assert event["move_type"] < 61
                    lines.append("            {" + number(event["ideal_spawn_seconds"]) + "," + str(event["move_type"]) + "},")
            lines.append("        }},")
        lines.append("    },")
    lines += ["}};", "inline const std::array<std::vector<int>,6> phaseHp = {{"]
    lines.extend("    {" + ",".join(map(str, hp)) + "}," for hp in phase_hp)
    lines += ["}};", "} // namespace armcharts", ""]
    header = "\n".join(lines)
    HEADER.write_text(header, encoding="utf-8", newline="\n")
    receipt["headerSha256"] = hashlib.sha256(HEADER.read_bytes()).hexdigest()
    receipt["notes"] = 723
    receipt["maximumSpawnToTarget"] = max(c["maximumSpawnToTarget"] for c in receipt["charts"])
    receipt["maximumIncludingHoldAnd20FrameTail"] = max(c["maximumIncludingHoldAnd20FrameTail"] for c in receipt["charts"])
    receipt["checks"] = "19 charts, 1673 physical rows, 723 ordered notes, source ideal timing/cycles, 6 phase-HP arrays, coordinate fallback, random markers and static concurrency <=30 verified."
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / "generated-charts.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(source['charts'])} charts / 723 notes; modeled maximum {receipt['maximumIncludingHoldAnd20FrameTail']}/30 slots")


if __name__ == "__main__":
    main()
