"""Static source/atlas/ownership checks; never launches or builds Game."""
import copy
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops
from v4_comic_presentation import ROOT, EXPECTED, SOURCE_NAMES, STOCK_ORIGINS, build_comic, bind_task


def assert_stock_reachable(stock, column, prefilled):
    """Every legal placement order can finish, including retained skill prefill."""
    full = (1 << len(stock)) - 1
    pending = [1 if prefilled else 0]
    seen = set()
    while pending:
        mask = pending.pop()
        if mask in seen:
            continue
        seen.add(mask)
        if mask == full:
            continue
        solved = mask.bit_count()
        reachable = [p["originSlot"] for p in stock
                     if not mask & (1 << p["originSlot"]) and p["thresholds"][column] <= solved]
        assert reachable, (column, prefilled, mask, "Stock softlock")
        pending.extend(mask | (1 << origin) for origin in reachable)
    assert full in seen
    return len(seen)


def main():
    native_path = ROOT / "data/v4_story/native_tasks.json"
    before = native_path.read_bytes()
    manuscripts = {name: (ROOT / "docs/design/rewrite_v4" / name).read_bytes()
                   for name in SOURCE_NAMES.values()}
    selection_path = ROOT / 'art/v4_production/comic_revisions_20261104/selection.json'
    selection_before = selection_path.read_bytes()
    index = build_comic()
    assert index["schemaVersion"] == 3
    native = json.loads(before)["tasks"]
    panels = options = speech = exact_cells = revised_images = 0
    owners = {}
    stock_pieces = reachable_states = 0
    for chapter, expected_order in EXPECTED.items():
        ident = f"T{chapter}-MG-01"
        metadata = index["tasks"][ident]
        original = copy.deepcopy(native[ident])
        bound = bind_task(original, index)
        assert original == native[ident], "Binding must not mutate source task"
        assert bind_task(bound, index) == bound, "Repeated native publication must be idempotent"
        added = bound["stage"].pop("comicPresentation")
        for source_slot,bound_slot in zip(original['stage']['slots'],bound['stage']['slots']):
            for source_option,bound_option in zip(source_slot['options'],bound_slot['options']):
                bound_option['image']=source_option['image']
        assert bound == original, "No answer, input, queue, retry or routing changes"
        assert len(json.dumps(added, ensure_ascii=False).encode("utf8")) < 6000
        assert added['schemaVersion']==3
        stock = added['stock']
        assert stock == metadata['stock']
        assert len(stock) == len(expected_order)
        assert [p['originSlot'] for p in stock] == STOCK_ORIGINS[len(expected_order)]
        assert sorted(p['originSlot'] for p in stock) == list(range(len(expected_order)))
        assert [p['originSlot'] for p in stock] != list(range(len(expected_order)))
        for rank, piece in enumerate(stock):
            assert set(piece) == {'originSlot', 'optionId', 'thresholds'}
            origin = piece['originSlot']
            assert piece['optionId'] == metadata['slots'][origin]['answer']
            assert piece['thresholds'] == ([0, 0, 0] if origin == 0 else
                                          [max(0, rank-2), max(0, rank-1), rank])
        assert added['unlock']['initialAutoFillEligibleSlots'] == [0]
        assert 'not original DAT values' in added['unlock']['thresholdPolicy']
        assert 'originSlot0' in added['unlock']['thresholdPolicy']
        for column in range(3):
            for prefilled in (False, True):
                reachable_states += assert_stock_reachable(stock, column, prefilled)
        stock_pieces += len(stock)
        assert len(added['pages'])==3
        assert sorted(i for p in added['pages'] for i in p['slots'])==list(range(len(expected_order)))
        assert all(1<=len(p['slots'])<=3 for p in added['pages'])
        assert len({i for p in added['pages'] for i in p['slots']})==len(expected_order)
        for p in added['pages']:
            assert all((ROOT/c).is_file() for c in p['contexts'])
            assert all(c not in [o['image'] for s in metadata['slots'] for o in s['options']] for c in p['contexts']), 'Fixed context must not be a missing answer candidate'
        assert "events" not in added["completion"], "Do not duplicate native/graph narration"
        close = metadata["completion"]
        owners[ident] = close["owner"]
        assert close["owner"] == ("story-graph" if chapter in (3, 4, 5) else "task-success-queue")
        assert metadata["narration"]["correct"] == 'per-panel-completed-replay-exactly-once'
        assert metadata["narration"]["replayAllCorrectOnCompletion"] is True
        assert metadata["narration"]["newSoloMonologue"] is False
        assert metadata["unlock"]["sources"], "Keep authored chronology provenance"
        assert metadata["unlock"]["mechanicEvidence"], "Solved-count gates require original mechanic evidence"
        assert metadata["retry"]["sameSlotOnly"] and metadata["retry"]["preservePlacedSlots"]
        assert "".join(str(s["answer"])[-1] for s in metadata["slots"]) == expected_order
        with Image.open(ROOT / metadata["board"]["image"]) as page:
            for number, slot in enumerate(metadata["slots"]):
                assert slot["index"] == number
                x, y, w, h = slot["atlasRectPixels"]
                assert w == 1920 and h == 1080 and x + w <= page.width and y + h <= page.height
                correct = next(o for o in slot["options"] if o["id"] == slot["answer"])
                # The full page really contains the current correct image at
                # the specified cell, including padding/subpanels. A manifest
                # entry alone cannot prove this.
                if correct.get('reviewedReplacement'):
                    assert correct['image']!=correct['legacyImage']
                    assert hashlib.sha256((ROOT/correct['image']).read_bytes()).hexdigest()==correct['sha256']
                    revised_images+=1
                else:
                    with Image.open(ROOT / correct["image"]) as candidate:
                        actual = candidate.convert("RGBA").resize((w, h), Image.Resampling.LANCZOS).convert("RGB")
                        tile = page.crop((x, y, x + w, y + h)).convert("RGB")
                        assert ImageChops.difference(actual, tile).getbbox() is None, (ident, number, "wrong page cell pixels")
                        exact_cells+=1
                for option in slot["options"]:
                    assert option["captionRequired"] and option["response"], "Every choice has its actual source response"
                    assert option["source"]["fileSha256"] == metadata["source"]["fileSha256"]
                    speech += sum(r["type"] == "say" for r in option["response"])
                    options += 1
                panels += 1
        if close["owner"] == "story-graph":
            assert close["entry"] == metadata["returnTo"]
            assert len(close["nodeIds"]) == len(set(close["nodeIds"])) == len(close["events"])
        else:
            assert close["events"] == native[ident]["queues"]["success"]
        corrupt = copy.deepcopy(original)
        corrupt["stage"]["slots"][0]["answer"] = "not-the-authored-answer"
        try:
            bind_task(corrupt, index)
        except ValueError:
            pass
        else:
            raise AssertionError("Changed answers must fail closed")
    sentinel = {"taskId": "T1-NS-A01", "stage": {"kind": "nonstop"}}
    assert bind_task(sentinel, index) == sentinel
    assert native_path.read_bytes() == before, "Central output must remain untouched"
    assert all((ROOT / 'docs/design/rewrite_v4' / name).read_bytes() == data
               for name, data in manuscripts.items()), "Authored manuscript bytes must remain untouched"
    assert selection_path.read_bytes() == selection_before, "Reviewed image selection must remain untouched"
    assert panels == stock_pieces == 38
    assert options == 114
    report = {"ok": True, "tasks": 6, "slots": panels, "candidateOptions": options,
              "sourceValidatedChoiceSpeechRows": speech, "exactLegacyAtlasCellsVerified": exact_cells,"reviewedCurrentReplacementImages":revised_images,
              "completionOwners": owners, "sourceTaskSha256": hashlib.sha256(before).hexdigest(),
              "stockPieces": stock_pieces, "allLogicDifficultiesAndInitialSkillReachable": True,
              "allReachableStockStatesChecked": reachable_states, "manuscriptBytesUnchanged": True,
              "pureAndIdempotent": True, "changedAnswerRejected": True,
              "gameBuiltOrExecuted": False, "runtimeVisualAcceptance": False}
    target = ROOT / "tools/v4_comic_presentation_verification.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
