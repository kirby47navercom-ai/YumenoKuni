"""Validate supplied SFL projections and index the retained static UI follow-up."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE = Path("C:/Users/kirby/Downloads/v3_re/native")
SPEC = ROOT / "docs/spec/18_V3_분석"
DOC = ROOT / "docs/analysis/v3_rebuild"
TARGET = "1a012357f54076ef7fbe6a63f19f055bbe1ce71792b8c0719e7dc51d2a5affeb"

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

reference = read(DOC / "trial_ui_reference_remaining.json")
widget = read(ROOT / "Game/Assets/UI/Stage.hbwidget.json")
nodes = {n["id"]: n for n in widget["nodes"]}
projection = []
for slot, index in enumerate([10, 7, 8, 9]):
    carrier = reference["cached_sfl_resources"][index]
    root = next(t for t in carrier["timelines"] if t["table"] == 6)
    state = next(s for s in root["root_label_states"] if s["label"] == "fl_wait")["state"]
    plate = next(p["matrix"] for p in state if p.get("instance_name", "").startswith("i_todome_pl_"))
    text = next(p["matrix"] for p in state if p.get("instance_name", "").startswith("p_todome_"))
    icon = next(p["matrix"] for p in state if p.get("instance_name") in ["p_triangle", "p_circle", "p_cross", "p_square"])
    child = carrier["timelines"][0]["named_placements"][0]["matrix"]
    bx, by, bw, bh = carrier["text_headers"][0]["header"]["bounds_xywh"]
    scale = 2 / 3
    expected = {
        "ArmPieceBand": [plate["translate_x"] * scale, plate["translate_y"] * scale, 512 * plate["scale_x"] * scale, 64 * plate["scale_y"] * scale],
        "ArmPieceKey": [icon["translate_x"] * scale, icon["translate_y"] * scale, 256 * icon["scale_x"] * scale, 256 * icon["scale_y"] * scale],
        "Piece": [(text["translate_x"] + (child["translate_x"] + bx) * text["scale_x"]) * scale, (text["translate_y"] + (child["translate_y"] + by) * text["scale_y"]) * scale, bw * text["scale_x"] * scale, bh * text["scale_y"] * scale],
    }
    for key, rect in expected.items():
        actual = nodes[key + str(slot)]["slot"]["offset"]
        assert all(abs(a - b) < .002 for a, b in zip(actual, rect)), (slot, key, actual, rect)
    projection.append({"slot": slot, "source": carrier["ancestry"], "sfl_sha256": carrier["sha256"], "rectangles": expected})

hud_reference = read(DOC / "armament_rhythm_hud_followup.json")
for name, key in [("Hp", "health"), ("Mental", "mental"), ("Boss", "boss")]:
    rect = hud_reference[key]["parts"]["fill"]["first_local_frame_leaves"][0]["own1280_rect_xywh"]
    for suffix in ["", "Track"]:
        node = nodes["ArmHud" + name + suffix]
        assert all(abs(a - b) < .002 for a, b in zip(node["slot"]["offset"], rect))
        assert node["slot"]["zIndex"] > nodes["ArmFace"]["slot"]["zIndex"]
for i, part in enumerate(hud_reference["tension"]["nodes"]):
    rect = part["first_local_frame_leaves"][0]["own1280_rect_xywh"]
    assert all(abs(a - b) < .002 for a, b in zip(nodes["ArmHudTension" + str(i)]["slot"]["offset"], rect))

bundle_path = NATIVE / "rea-pad-followup-ui-20261030.json"
bundle = read(bundle_path)
assert any(a.get("digest", {}).get("sha256") == TARGET for a in bundle["artifacts"])
old_bundle = read(NATIVE / "rea-pad-text-ui-20261030.json")
assert {r["evidence_id"] for r in old_bundle["records"]} <= {r["evidence_id"] for r in bundle["records"]}
findings = {
    "scope": "Static follow-up: gift rendering/availability and final four-piece transition; own native verification is separate.",
    "target_sha256": TARGET,
    "bundle": {"path": str(bundle_path), "sha256": hashlib.sha256(bundle_path.read_bytes()).hexdigest(), "records": len(bundle["records"])},
    "new_functions": {r["parameters"]["procedure"]: r["evidence_id"] for r in bundle["records"] if r["evidence_id"] not in {p["evidence_id"] for p in old_bundle["records"]} and r["operation"] == "analyze_function"},
    "gift_contract": [
        "41cae0 waits for both language resource handles; 41ca30 separately creates and waits for27 icon instances.",
        "41cd70 copies actual parent placeholder positions into the27 icons, uses absolute index=scrollRow*9+slot, and hides slots beyond the static item table.",
        "41cd70 keeps discovery/availability separate from quantity: unknown records use icon999 and omit count; discovered zero-quantity records remain catalogue entries.",
        "41dfd0 clears the selected discovered item's new flag on leaving it; 41e180 applies the present theme to actual bases/numbers, not to arbitrary generic cards.",
        "The gift page now uses27 source-positioned clones; root scale and exact child quads are supplemented by pad_gift_icon_scale_followup.json. Own native acceptance is recorded separately in pad_gift_ui_findings.json.",
    ],
    "four_piece_contract": [
        "337ba0 accepts only unselected logical pieces, records their order, and builds the concatenated actual strings through338500; no regenerated distractor rounds.",
        "3439d0/3408f0 call338280 after four selections and wait for+0x248 to clear before337b40 judges the complete order.",
        "338280 sets timer+0x244=-15.338b00 clamps timer/(618af0()*0.5), interpolates position/rotation/scale, then hides the text and clears readiness at fraction1.",
        "At the own game's admitted60Hz projection, the consumer takes46 updates including its initial negative wait. Native source XYZ/rotation do not directly equal2D screen coordinates.",
    ],
    "four_piece_projection": projection,
    "own_limits": [
        "Supplied SFL geometry is checked against the generated widget within0.002px. This is not original runtime pixel/material acceptance.",
        "Controller shapes are local editable vectors; original source raster, full press/out clips and3D selected-text projection are not reproduced exactly.",
        "The joined-text placement and2D scale adaptation are separate from the verified source temporal gate. Source chart stationary anchors are explicitly bound via phase-a/cyclic own note policy. The retained256-unit p_base container is not proof of a256-unit opaque circle: own visible timing glyph uses the source p_bt89.5996-unit button carrier, projected2/3. Exact source note raster/material, simultaneous30-slot admission and original HUD gauges remain separate, unaccepted work.",
        "Fixed subject and four authored answer fragments remain; old distractor-specific wrong variants are not triggered by a different, partial fragment selection.",
    ],
    "own_armament_hud": {
        "source_contract": "docs/analysis/v3_rebuild/armament_rhythm_hud_followup.json",
        "source_contract_sha256": hashlib.sha256((DOC / "armament_rhythm_hud_followup.json").read_bytes()).hexdigest(),
        "emitter": "Game/tools/v4-armament-hud.mjs",
        "gauge_quads": {key: hud_reference[key]["parts"]["fill"]["first_local_frame_leaves"][0]["own1280_rect_xywh"] for key in ["health", "mental", "boss"]},
        "native_mask_travel_in_source_units": {"health": 438, "mental": 332, "boss": -888},
        "generated_source_quads_checked": 26,
        "tension_layout": "20 separate source quads, ten half/full pairs; odd j<T plus j=T-1 when T odd",
        "adaptations": [
            "Editable vector art follows observed V3 placement. Original source raster alpha, exact decorative silhouette, glow, style-family and fever art are not recovered.",
            "Vector visible spans are explicitly inferred from full-to-empty mask travel; do not describe them as measured original alpha bounds.",
            "Percent texture variants clip a fixed shape, never scale its entire artwork; cosmetic quantization1percent does not change any gameplay resource or damage.",
            "Source HP/mental/boss quads are preserved. Lower-left clock placement and name text are observed-layout own font adaptations.",
            "Long own Korean claims wrap at26px rather than shrinking to single-digit sizes. This is not original word-renderer glyph placement.",
        ],
        "native_status": "d4cb2b62 own native v4-tasks-1793299668007 verifies T3 and common HUD restoration; separate v4-tasks-1793300104184 verifies actual new exhausted-HP retry after3 wrong whole orders, HP500→10000 and retries3→4, clean final widget removal and authored success. hud-layer-pixels.json records original screenshot ROI yellow0→174 after z correction. Earlier c901 functional4-fixture PASS is not its rejected tension visibility acceptance. No original raster identity claim.",
    },
    "original_runtime_observed": False,
    "behavior_progress_changed": False,
}
write(DOC / "pad_and_four_piece_followup_findings.json", findings)
write(NATIVE / "pad_and_four_piece_followup_findings.json", findings)
index_path = SPEC / "evidence_index.json"
index = read(index_path)
by_id = {r["evidence_id"]: r for r in index["records"]}
before = len(by_id)
for row in bundle["records"]:
    if row["evidence_id"] not in by_id:
        by_id[row["evidence_id"]] = {key: row[key] for key in ["evidence_id", "operation", "parameters", "confidence", "authority", "locations"]}
index["records"] = sorted(by_id.values(), key=lambda r: r["evidence_id"])
index["supplementary_bundles"] = [r for r in index.get("supplementary_bundles", []) if r["path"] != str(bundle_path)] + [findings["bundle"]]
write(index_path, index)
numbers_path = SPEC / "numbers.json"
numbers = read(numbers_path)
numbers["coverage"]["rea_evidence_records"] = len(by_id)
numbers["ui"]["pad_four_piece_followup_20261030"] = {"findings": str(NATIVE / "pad_and_four_piece_followup_findings.json"), "bundle": findings["bundle"], "four_piece_source_rectangles_checked": 12, "own_hud_source_quads_checked": 26, "own_transition_consumer_updates_at60Hz": 46, "behavior_progress_changed": False}
write(numbers_path, numbers)
print(json.dumps({"ok": True, "rectangles": 12, "new_records": len(by_id) - before, "indexed_records": len(by_id), "behavior_progress_changed": False}))
