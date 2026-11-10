"""Count selected runtime-graph routes without summing exclusive alternatives."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import re
import argparse

ROOT = Path(__file__).resolve().parents[1]


def characters(text):
    return len(re.sub(r"\s", "", text))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', default='', help='Keep earlier frozen audit/traces intact, e.g.20261101')
    parser.add_argument('--export-dialogue', action='store_true', help='Export actually selected dialogue for the native pagination/pacing audit')
    args = parser.parse_args()
    assert not args.tag or args.tag.isdecimal()
    suffix = '-' + args.tag if args.tag else ''
    trace_path = ROOT / ('Game/Saved/campaign-route-traces' + suffix + '.json')
    graphs = {p.stem: json.loads(p.read_text(encoding="utf-8"))
              for p in (ROOT / "data/v4_story/chapters").glob("*.json")}
    tasks = json.loads((ROOT / "data/v4_story/native_tasks.json").read_text(encoding="utf-8"))["tasks"]
    traces = json.loads(trace_path.read_text(encoding="utf-8"))
    assert traces["status"] == "PASS" and traces["taskSuccessInjectedForStructureOnly"]
    results, coverage, selected_dialogue = [], defaultdict(set), []
    for scenario in traces["policies"]:
        totals, sources, seen = defaultdict(Counter), defaultdict(Counter), set()
        phase, last_chapter = "daily", None

        def add(chapter, phase, kind, text, event_id="", source=None, record=None):
            if not isinstance(text, str) or not text:
                return
            key = (chapter, phase)
            totals[key][kind + "Characters"] += characters(text)
            totals[key][kind + "Rows"] += 1
            if args.export_dialogue and kind == 'dialogue':
                selected_dialogue.append({'policy': scenario['policy'], 'chapter': chapter,
                                          'phase': phase, 'text': text, 'id': event_id,
                                          'source': source or {},
                                          'speaker': (record or {}).get('speaker', ''),
                                          'actor': (record or {}).get('actor', ''),
                                          'mono': (record or {}).get('mono', False)})
            if event_id:
                if (chapter, event_id) in seen:
                    totals[key]["reenteredTextRows"] += 1
                seen.add((chapter, event_id))
            if source:
                sources[key][source.get("file", "unattributed")] += characters(text)

        def rows(chapter, phase, values):
            for row in values:
                add(chapter, phase, "dialogue", row.get("text", ""), row.get("id", row.get("eventId", "")), row.get("source"), row)

        for step in scenario["trace"]:
            chapter = step["chapter"]
            if chapter != last_chapter:
                phase, last_chapter = "daily", chapter
            node = traces.get('runtimeNodes', {}).get(chapter + ':' + step['id'], graphs[chapter]["nodes"].get(step["id"]))
            assert node is not None, step['id']
            node.setdefault('id', step['id'])
            source = node.get("source", {})
            file, location = source.get("file", ""), source.get("location", "")
            parent = re.match(r"1[1-6]([abcd])", file)
            if parent:
                phase = {"a": "daily", "b": "investigation", "c": "trial", "d": "aftermath"}[parent[1]]
            elif re.match(r"T\d*[-:]", location):
                phase = "trial"
            elif re.match(r"I\d*[-:]", location):
                phase = "investigation"
            elif re.match(r"R\d*[-:]", location):
                phase = "aftermath"
            if step["kind"] == "task":
                phase = "trial"
            key = (chapter, phase)
            totals[key]["visitedNodes"] += 1
            if step["kind"] == "say":
                add(chapter, phase, "dialogue", node["text"], node["id"], source, node)
                totals[key]["monologueRows" if node.get("mono") else "spokenRows"] += 1
            elif step["kind"] in ("evidence", "document"):
                for text in [node.get("title", node.get('name', '')), node.get("text", ""), *node.get("rows", [])]:
                    add(chapter, phase, "document", text)
            elif step['kind'] == 'stage' and node.get('showRecord'):
                record = node['publicRecords'][0]
                for text in [record.get('title', ''), *record.get('rows', [])]:
                    add(chapter, phase, 'document', text)
            elif step["kind"] == "menu":
                coverage[(chapter, step["id"])].add(step["choice"])
                visible = step.get('visibleOptions', range(len(node['options'])))
                for text in [node.get("q", ""), *[node['options'][i].get("label", "") for i in visible]]:
                    add(chapter, phase, "choiceUI", text)
            elif step["kind"] == "task":
                bundle = tasks[step["taskId"]]
                stage = step.get('preparedStage', bundle["stage"])
                totals[key]["tasks"] += 1
                totals[key]['taskKind_' + stage['kind']] += 1
                rows(chapter, phase, bundle["queues"].get("intro", []))
                rows(chapter, phase, bundle["queues"].get("success", []))
                add(chapter, phase, "taskUI", stage.get("question", ""))
                for option in stage.get('options', []):
                    add(chapter, phase, 'taskUI', option if isinstance(option, str) else option.get('name', option.get('label', '')))
                if stage['kind'] == 'showdown':
                    for line in stage.get('lines', []):
                        add(chapter, phase, 'oneMinigamePresentation', line if isinstance(line, str) else line.get('text', ''))
                if stage['kind'] == 'scrum':
                    for pair in stage.get('pairs', []):
                        add(chapter, phase, 'oneMinigamePresentation', pair.get('themText', ''))
                        add(chapter, phase, 'oneMinigamePresentation', pair.get('usText', ''))
                if stage['kind'] == 'armament':
                    used = set()
                    for wave in stage.get('waves', []):
                        for pair in wave.get('pairs', []):
                            for role in ('claim', 'response'):
                                value = pair.get(role, {})
                                for row in value if isinstance(value, list) else [value]:
                                    text = row if isinstance(row, str) else row.get('text', '')
                                    token = (role, text) if isinstance(row, str) else row.get('id', (role, text))
                                    if token not in used:
                                        add(chapter, phase, 'oneMinigamePresentation', text)
                                        used.add(token)
                    for text in stage.get('final', []):
                        add(chapter, phase, 'taskUI', text if isinstance(text, str) else text.get('text', text.get('label', '')))
                for question in stage.get("questions", []):
                    add(chapter, phase, "taskUI", question.get("q", ""))
                    for text in question["options"]:
                        add(chapter, phase, "taskUI", text)
                    rows(chapter, phase, question.get("success", []))
                for slot in stage.get("slots", []):
                    for option in slot["options"]:
                        add(chapter, phase, "taskUI", option.get("label", ""))
                        if option.get("id") == slot["answer"]:
                            rows(chapter, phase, option.get("response", []))
                # A complete rotation is an accounting scenario, never a claim
                # that players have to hear every line before taking the shot.
                for line in bundle.get("debate", {}).get("lines", []):
                    add(chapter, phase, "oneDebateRotation", line.get("text", ""))
        for key, counts in totals.items():
            shown = sum(counts[k + 'Characters'] for k in ('dialogue', 'document', 'choiceUI', 'taskUI', 'oneMinigamePresentation', 'oneDebateRotation'))
            counts['onePresentationReadingCharacters'] = shown
        results.append({"policy": scenario["policy"], "normalCheckpointResume": scenario["normalCheckpointResume"],
                        "phases": [{"chapter": ch, "phase": ph, **counts,
                                    "dialogueMinutesAssumingCharactersPerMinute": {str(rate): round(counts["dialogueCharacters"] / rate, 2) for rate in (250, 400)},
                                    "onePresentationReadingMinutesAssumingCharactersPerMinute": {str(rate): round(counts['onePresentationReadingCharacters'] / rate, 2) for rate in (250, 400)},
                                    "additionalNonreadingMinutesPerTaskNeededForFiveHours": {str(rate): round(max(0, 300 - counts['onePresentationReadingCharacters'] / rate) / counts['tasks'], 2) for rate in (250, 400)} if ph == 'trial' and counts['tasks'] else None,
                                    "sourceCharacterCounts": dict(sources[(ch, ph)])}
                                   for (ch, ph), counts in totals.items()]})
    missing = []
    for ch, graph in graphs.items():
        for node in graph["nodes"].values():
            if node["type"] == "menu":
                for index, option in enumerate(node["options"]):
                    if index not in coverage[(ch, node["id"])]:
                        missing.append({"chapter": ch, "menu": node["id"], "index": index, "label": option["label"], "requires": option.get("requires", {}), "source": node.get("source")})
    report = {"scope": "Actual C++ routing traces over packaged graph semantics; success injected for structural traversal. No native input or human-duration certificate.",
              "ratesAreExplicitAssumptions": [250, 400], "unselectedTextCountedAsDialogue": False,
              "thinkingWaitingAnimationTravelOrRetryTimeAssigned": False, "originalManuscriptsModified": False,
              "tracesSHA256": hashlib.sha256(trace_path.read_bytes()).hexdigest(),
              "readingIncludesOneMinigamePresentationScenario": True,
              "onePresentationIsNotAMandatoryListenOrMeasuredDuration": True,
              "thinkingTimeInferredFromTarget": False,
              "rasterDocumentTextOCRIncluded": False,
              "humanStudyRequiredAsUnrequestedCompletionGate": False,
              "scenarios": results, "uncoveredMenuOptions": missing,
              "coverageScope": "Three full selected policies and one late normal-save resume. Uncovered alternatives stay pending; not all combinations."}
    output = ROOT / ('Game/Saved/playable-text-route-audit' + suffix + '.json')
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.export_dialogue:
        (ROOT / ('Game/Saved/selected-dialogue' + suffix + '.json')).write_text(
            json.dumps(selected_dialogue, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({"policies": len(results), "uncoveredMenuOptions": len(missing),
                      "normalPolicy": [{k: v for k, v in row.items() if k in ("chapter", "phase", "dialogueCharacters", "tasks", "dialogueMinutesAssumingCharactersPerMinute")} for row in results[0]["phases"]]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
