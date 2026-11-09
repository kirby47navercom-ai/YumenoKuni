"""Read-only climax page/slot/narration metadata for the native publisher.

The existing manuscript and compiled task own answers and dialogue.  This
module neither rewrites a graph nor manufactures a second reconstruction
narration.  It joins those contracts to the *current* correct-candidate atlas,
not the archived six-panel summaries from the earlier production pass.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from v4_comic_geometry import slot_quad

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {1: "BACBAC", 2: "CBACBA", 3: "ACBACB", 4: "CABCAB", 5: "BCABCA", 6: "CABCABCA"}
SOURCE_NAMES = {
    1: "157_1장_재구성만화_슬롯과_실제문답.md",
    2: "158_2장_재구성만화_슬롯과_실제문답.md",
    3: "159_3장_재구성만화_슬롯과_실제문답.md",
    4: "160_4장_재구성만화_슬롯과_실제문답.md",
    5: "161_5장_재구성만화_슬롯과_실제문답.md",
    6: "162_6장_두_시간줄_재구성과_실제문답.md",
}

# Own reduced-board adaptation, not the original game's DAT values. Keep stock
# independent of the chronological hole order and retain authored slot0's
# initial skill eligibility in every logic difficulty.
STOCK_ORIGINS = {6: [4, 1, 3, 0, 5, 2], 8: [6, 3, 1, 7, 0, 5, 2, 4]}


def comic_stock(slots):
    return [{"originSlot": origin, "optionId": slots[origin]["answer"],
             "thresholds": ([0, 0, 0] if origin == 0 else
                            [max(0, rank - 2), max(0, rank - 1), rank])}
            for rank, origin in enumerate(STOCK_ORIGINS[len(slots)])]


# Page boundaries follow the existing event order. Context panels are already
# inspected physical settings/props, never an unfilled solution candidate.
PAGE_GROUPS = {1:[[0,1,2],[3,4],[5]],2:[[0,1],[2,3,4],[5]],
               3:[[0,1],[2,3,4],[5]],4:[[0,1],[2,3],[4,5]],
               5:[[0,1,2],[3,4],[5]],6:[[0,1,2],[3,4,5],[6,7]]}
PAGE_CONTEXT = {
 1:['printer_output','door_A_sensor','right_wrist_brace'],
 2:['chest_open_stays','microphone_base_forensic_r2','chest_exterior'],
 3:['black_eye_cover','mirror_fixed_edge','opposed_benches'],
 4:['normal_fixed_utility_window','blind_second_storage','wet_closed_camera_bag'],
 5:['personal_and_six_cups','protected_ordinary_notes','sealed_fictional_sample'],
 6:['old_current_railing','entry_allocation_records','rabbit_back_tag'],
}
def comic_pages(root,chapter):
    groups=PAGE_GROUPS[chapter]
    assert sorted(i for g in groups for i in g)==list(range(len(EXPECTED[chapter])))
    pages=[]
    for slots,name in zip(groups,PAGE_CONTEXT[chapter]):
        image='art/inspection_v4/delivery/'+name+'.webp'
        if not (root/image).is_file():
            raise ValueError('Reviewed comic context missing: '+image)
        extras={1:'printer_output',2:'player_and_card',3:'sealed_opaque_envelope',4:'normal_hatch_latch',5:'personal_and_six_cups',6:'old_current_railing'}
        contexts=[image] if len(slots)==3 else [image,'art/inspection_v4/delivery/'+extras[chapter]+'.webp']
        assert all((root/c).is_file() for c in contexts)
        pages.append({'slots':slots,'contexts':contexts,
          'screenQuads':{str(i):slot_quad(slots,i,len(contexts)) for i in slots},
          'contextPolicy':'Previously inspected prop/context only; no readable new text, answer panel or additional evidence.'})
    return pages


def _read(root, name):
    return json.loads((root / name).read_text(encoding="utf-8-sig"))


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _image(root, name):
    from PIL import Image
    path = root / name
    with Image.open(path) as image:
        size = list(image.size)
    return {"image": name, "size": size, "sha256": _sha(path)}


def _source(root, filename):
    path = root / "docs/design/rewrite_v4" / filename
    text = path.read_text(encoding="utf-8-sig")
    return {"file": filename, "fileSha256": hashlib.sha256(text.encode("utf8")).hexdigest()}, text.splitlines()


def _ref(source, line):
    return {**source, "line": line}


def _validate_rows(rows, source, lines):
    """Prove actual spoken text still comes from its cited current source."""
    for row in rows:
        ref = row.get("source", {})
        if ref.get("file") != source["file"]:
            raise ValueError("Comic dialogue belongs to another manuscript")
        if ref.get("fileSha256") != source["fileSha256"]:
            raise ValueError("Comic source changed; re-read it before publishing")
        at = ref.get("line", 0)
        if not 1 <= at <= len(lines):
            raise ValueError("Comic dialogue has no real source line")
        if row.get("type") == "say":
            match = re.match(r"^\[[^]]+\]\s*(.*)$", lines[at - 1])
            # Formatting-only emphasis is removed by the story compiler.
            actual = match[1].replace("**", "").strip() if match else None
            if actual != row.get("text"):
                raise ValueError(f"Comic spoken text differs at {source['file']}:{at}")


def _graph_close(graph, task_node, source, lines):
    """3/4/5 close in their existing graph; these references must NOT replay."""
    at = task_node["success"]
    entry = at
    rows = []
    seen = set()
    while at in graph["nodes"]:
        if at in seen:
            raise ValueError("Comic close route loops")
        seen.add(at)
        node = graph["nodes"][at]
        if node.get("source", {}).get("file") != source["file"]:
            break
        if node.get("type") not in ("say", "stage"):
            raise ValueError("Unreviewed input inside authored comic closing dialogue")
        rows.append(copy.deepcopy(node))
        at = node.get("next", "")
    if not rows:
        raise ValueError("Authored graph completion dialogue is missing")
    _validate_rows(rows, source, lines)
    return {"owner": "story-graph", "entry": entry, "returnTo": at,
            "nodeIds": [r["id"] for r in rows], "events": rows,
            "playPolicy": "Keep completed page while these existing nodes execute; do not enqueue another copy."}


def build_comic(root=None):
    """Return a fresh JSON-serializable metadata index; reads only.

    Call once before native publication, then use ``bind_task`` per bundle.
    Asset paths are repository source paths so the publisher's normal image
    mapper can copy/map them.  No generated asset or central graph is written.
    """
    root = Path(root) if root else ROOT
    native = _read(root, "data/v4_story/native_tasks.json")["tasks"]
    catalog = _read(root, "art/v4_production/completion/final_catalog.json")
    pages = {p["chapter"]: p for p in catalog["reconstruction_pages"]}
    cards = {p["id"]: p for p in catalog["reconstruction_candidates"]}
    revision_path=root/'art/v4_production/comic_revisions_20261104/selection.json'
    revisions={}
    if revision_path.is_file():
        for row in _read(root,str(revision_path.relative_to(root)))['rows']:
            key=(row['taskId'],row['slotId'],row['optionId'])
            if key in revisions:raise ValueError('Duplicate reviewed comic image')
            if _sha(root/row['image'])!=row['sha256']:raise ValueError('Reviewed comic image changed')
            revisions[key]=row
    result = {"schemaVersion": 3, "contentVersion": "v4", "tasks": {},
              "gameExecuted": False, "runtimeVisualAcceptance": False,
              "policy": "Existing manuscript answers, options, speech and authored close remain unchanged. Runtime stock uses each hole's correct image once; solved-count gates follow the original mechanic with explicit own reduced-board thresholds."}
    for chapter, expected in EXPECTED.items():
        ident = f"T{chapter}-MG-01"
        task = native[ident]
        if not task.get("ready") or task["stage"]["kind"] != "climax":
            raise ValueError(ident + " is not a bound native comic task")
        source, lines = _source(root, SOURCE_NAMES[chapter])
        if task["source"]["fileSha256"] != source["fileSha256"]:
            raise ValueError(ident + " current manuscript does not match its task")
        slots = task["stage"]["slots"]
        if "".join(str(s["answer"])[-1] for s in slots) != expected:
            raise ValueError(ident + " answer order changed")
        page = pages[chapter]
        cols, rows = page["columns"], page["rows"]
        if cols != (4 if chapter == 6 else 3) or rows != 2:
            raise ValueError("Current reconstruction atlas layout changed")
        asset = _image(root, page["webp"])
        if asset["size"] != [cols * 1920, 2160] or page["native_cell_size"] != [1920, 1080]:
            raise ValueError("Atlas dimensions no longer match actual delivered cells")
        graph = _read(root, f"data/v4_story/chapters/{chapter}.json")
        nodes = [n for n in graph["nodes"].values() if n.get("taskId") == ident]
        if len(nodes) != 1:
            raise ValueError(ident + " needs exactly one authored task call")
        task_node = nodes[0]
        # Exact instruction excerpts are provenance only, never player labels.
        order_lines = [i for i, line in enumerate(lines, 1)
                       if ("순서대로" in line or "차례로 채운다" in line or "맞는 순서는" in line or
                           ("정답" in line and ("→" in line or "배열" in line)))]
        compiled = {"taskId": ident, "source": source, "taskNodeId": task_node["id"],
                    "entry": task_node["id"], "returnTo": task_node["success"],
                    "board": {**asset, "columns": cols, "rows": rows, "cellSize": [1920, 1080],
                              "aspect": cols * 1920 / 2160,
                              "renderBeforeComplete": "Blank neutral tiles plus individually placed correct images; never show the unmasked completed atlas.",
                              "renderAfterComplete": "Render accepted current option images as native page cells, keeping aspect; the archived atlas is provenance only."},
                    "unlock": {"kind": "solved-count-gated-shared-stock", "initialSlotIndex": 0,
                               "next": "player-chosen-unfilled-hole; auto guidance chooses a reachable unused stock piece",
                               "candidateAvailability": "One correct image per hole in shuffled shared stock. Used pieces cannot be reused. Locked pieces show remaining solved count; a newly eligible selected piece must finish its unlock animation before confirmation.",
                               "thresholdPolicy": "Own reduced 6/8-hole adaptation, not original DAT values: shuffled rank i uses [max(0,i-2),max(0,i-1),i] for easy/normal/hard; originSlot0 overrides to [0,0,0] to preserve authored initial skill eligibility.",
                               "mechanicEvidence": "Original 3909a0 rejects threshold>correctCount or used; 390b20 draws max(threshold-correctCount,0) and waits for selected fl_rock completion.",
                               "sources": [_ref(source, i) for i in order_lines]},
                    "pages": comic_pages(root,chapter),
                    "retry": {"sameSlotOnly": True, "preservePlacedSlots": True,
                              "newEvidence": False, "rewindWorld": False,
                              "response": "Wrong placement uses only the chosen option's existing response; correct responses wait for completed-panel replay."},
                    "narration": {"correct": "per-panel-completed-replay-exactly-once",
                                  "completion": "authored-close-exactly-once",
                                  "replayAllCorrectOnCompletion": True,
                                  "newSoloMonologue": False}, "slots": []}
        for index, slot in enumerate(slots):
            number = index + 1
            answer = slot["answer"]
            # The authored section title is a neutral topic cue, not the
            # correct option's caption. Do not reveal an answer as a hole hint.
            option_line = slot["options"][0]["source"]["line"]
            heading_at = next(i for i in range(option_line - 2, -1, -1)
                              if lines[i].startswith("## "))
            heading = lines[heading_at].split(" — ", 1)
            if len(heading) != 2 or not heading[1].strip():
                raise ValueError("Comic hole needs an actual authored topic heading")
            hole_hint = heading[1].strip()
            col, row = index % cols, index // cols
            pkey = f"C{chapter}_S{number:02d}_{str(answer)[-1]}"
            if page["panels"][index] != pkey:
                raise ValueError("Atlas panel order is not the current correct sequence")
            candidate_rows = []
            for option in slot["options"]:
                key = str(option["id"])[-1]
                card_id = f"C{chapter}_S{number:02d}_{key}"
                card = cards[card_id]
                if card["chapter"] != chapter or card["slot"] != number or bool(card["correct"]) != (option["id"] == answer):
                    raise ValueError("Candidate/slot/answer binding mismatch")
                ref = option["source"]
                line = ref.get("line", 0)
                expected_line = f"|{number}{key}|{option['label']}|" + ("정답" if option["id"] == answer else "오답") + "|"
                if ref.get("fileSha256") != source["fileSha256"] or lines[line - 1] != expected_line:
                    raise ValueError(f"Current candidate table differs: {card_id}")
                response = copy.deepcopy(option.get("response", []))
                if not response:
                    raise ValueError("Candidate has no actual authored response")
                _validate_rows(response, source, lines)
                revision=revisions.get((ident,slot['id'],option['id']))
                if revision and (revision['sourceSha256']!=source['fileSha256'] or revision['captionSha256']!=hashlib.sha256(option['label'].encode()).hexdigest()):
                    raise ValueError('Re-review changed comic replacement semantics')
                image=revision['image'] if revision else option['image']
                candidate_rows.append({"id": option["id"],"legacyImage":option['image'],"reviewedReplacement":bool(revision), "caption": option["label"],
                                       "captionRequired": True, "source": copy.deepcopy(ref),
                                       **_image(root, image), "response": response,
                                       "responseOwner": "existing-slot-option-response"})
            if len(candidate_rows) != 3 or {str(o["id"])[-1] for o in candidate_rows} != {"A", "B", "C"}:
                raise ValueError("Expected exactly three distinct authored options")
            compiled["slots"].append({"id": slot["id"], "index": index, "number": number,
                                       "holeHint": hole_hint,
                                       "holeHintSource": {**_ref(source, heading_at + 1), "quote": lines[heading_at]},
                                       "answer": answer, "atlasPanelId": pkey,
                                       "atlasRectPixels": [col * 1920, row * 1080, 1920, 1080],
                                       "atlasUv": [col / cols, row / rows, (col + 1) / cols, (row + 1) / rows],
                                       "blankLabel": str(number), "options": candidate_rows})
        _validate_rows(task["queues"].get("intro", []), source, lines)
        compiled["introOwner"] = "existing-task-intro-queue" if task["queues"].get("intro") else "existing-preceding-story-graph"
        success = task["queues"].get("success", [])
        if success:
            _validate_rows(success, source, lines)
            compiled["completion"] = {"owner": "task-success-queue", "events": copy.deepcopy(success),
                                      "returnTo": task_node["success"],
                                      "playPolicy": "After each correct panel's existing response has replayed exactly once, show the completed page beneath the existing task success queue; do not enqueue another copy of the close."}
        else:
            compiled["completion"] = _graph_close(graph, task_node, source, lines)
        compiled["stock"] = comic_stock(compiled["slots"])
        result["tasks"][ident] = compiled
    return result


def bind_task(bundle, comic=None):
    """Pure copy: attach presentation metadata to one existing native bundle."""
    comic = comic if comic is not None else build_comic()
    out = copy.deepcopy(bundle)
    ident = out.get("taskId", "")
    if ident in comic["tasks"]:
        if out.get("stage", {}).get("kind") != "climax":
            raise ValueError("Comic metadata cannot bind a different mechanic")
        expected = comic["tasks"][ident]
        actual = out["stage"].get("slots", [])
        if [(s["id"], s["answer"]) for s in actual] != [(s["id"], s["answer"]) for s in expected["slots"]]:
            raise ValueError("Comic bundle answer changed since metadata inspection")
        for slot,metadata in zip(actual,expected['slots']):
            pictures={o['id']:o['image'] for o in metadata['options']}
            for option in slot['options']:option['image']=pictures[option['id']]
        # Native slots already own all three responses and the correct answer.
        # Do not double their dialogue or exceed bounded native JSON shards.
        close = expected["completion"]
        out["stage"]["comicPresentation"] = {
            "schemaVersion": 3,
            "pages": copy.deepcopy(expected["pages"]),
            "board": {k: copy.deepcopy(expected["board"][k])
                      for k in ("image", "size", "columns", "rows", "cellSize", "aspect")},
            "unlock": {"kind": expected["unlock"]["kind"], "initialSlotIndex": 0,
                       "initialAutoFillEligibleSlots": [expected["unlock"]["initialSlotIndex"]],
                       "thresholdPolicy": expected["unlock"]["thresholdPolicy"],
                       "autoFillPolicy": "Preserve explicitly authored slot0 initial skill eligibility. Its stock piece is initially available in every logic difficulty; any prefilled hole counts as solved and its piece is used. Correct responses execute exactly once during completed-panel replay."},
            "stock": copy.deepcopy(expected["stock"]),
            "narration": copy.deepcopy(expected["narration"]),
            "completion": {k: copy.deepcopy(close[k]) for k in ("owner", "entry", "nodeIds", "returnTo") if k in close},
            "slots": [{k: copy.deepcopy(s[k]) for k in ("id", "index", "number", "atlasPanelId", "atlasRectPixels", "atlasUv", "holeHint")}
                      for s in expected["slots"]],
        }
        out["stage"]["comicPresentation"]["board"].update(
            image="native-comic:"+ident,
            revealOnCompleteOnly=True, keepAspect=True,
            blankContent="neutral-paper-no-answer-caption")
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_comic()
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf8")
        print(json.dumps({"tasks": len(result["tasks"]), "slots": sum(len(t["slots"]) for t in result["tasks"].values()), "output": str(args.output)}))
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
