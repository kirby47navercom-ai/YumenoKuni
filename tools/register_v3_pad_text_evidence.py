"""Register the authenticated supplementary REA bundle; never changes coverage scores."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = Path("C:/Users/kirby/Downloads/v3_re/native")
SPEC = ROOT / "docs/spec/18_V3_분석"
BUNDLE = EXTERNAL / "rea-pad-text-ui-20261030.json"
TARGET = "1a012357f54076ef7fbe6a63f19f055bbe1ce71792b8c0719e7dc51d2a5affeb"
raw = BUNDLE.read_bytes()
bundle = json.loads(raw)
assert any(a.get("digest", {}).get("sha256") == TARGET for a in bundle["artifacts"])

def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

findings = {
    "scope": "Relative evidence-list/detail text layout and scroll consumer; static V3 evidence, not original runtime observation.",
    "target_sha256": TARGET,
    "bundle": str(BUNDLE),
    "bundle_sha256": hashlib.sha256(raw).hexdigest(),
    "matched_base_cache_sha256": "200f3c4626b1b37e70b891421e664ff9fb1c9641122775682bcb7ee02156f11b",
    "source_sfl_sha256": "eae6e728f4e2679091b2343dac2bb97b87653c0caf836ca2410468c15933d004",
    "evidence": {
        "setter_dossier": "ev_c8e5868529651fd52ab1848453f7ec9a1c1b5b0d957da8aec3d7730e747d5c58",
        "setter_queue": "ev_95ed9de6dc14b7ed0927e0bf0cbdf7e5a82841ba61c2e285c34f2bb7e09d51e9",
        "queue_callbacks": "ev_79e258c94caa2a4d914fa1340b549ca77c58592837d16da9c74addde8115b38e",
        "text_map_and_movie_flags": "ev_f70fc413a31989e332a23a268ad5f309052c1de0c46821aa55ed0ef7fe6a5086",
        "name_parsers": "ev_95ce951d1878bb5722275da8a4a641857cbe36e75791569d41b10312a34958e7",
        "text_vtable": "ev_205f72eedeb82bafbfa77214b987e4bb27dbff3e1d7a21861c18ffd8091671d0",
        "text_draw": "ev_dc4edccf717b1ebe60e0f8a97c3d9e2d097a5d802aa5aadcfe231491fa5d018f",
        "scroll_update_and_affine": "ev_55faa5d7c1fcdf373b668e80aa4c49ecb15745f9b40c060d3806c370c07ff916",
        "text_prepare": "ev_976e0986d0c5e56bb8abb5ebc08fa6d57406421aa4ea5eaddcfd0f9513c0a588",
    },
    "confirmed": [
        "4aaeb0 queues a keyed text value through4b8df0/4bc500/4bd480/4be030; it does not directly add the parent268 as a glyph X coordinate.",
        "4b4440 parses the actual _scroll_s1w990x80 suffix: speed1, repeat gap990, initial X80, default initial wait150 admitted updates.",
        "4b4b80 counts the wait down, then subtracts the speed from the float scroll offset per admitted update and wraps by text-width plus gap. Not a wall-clock measurement.",
        "4b3d10 composes text bounds and affine state, then adds the configured initial/current scroll offset when drawing.",
        "Parent(268,141)+child(-268,2)+text bounds(-2,-2)+initial X80 gives initial relative glyph(78,141), projected own(52,94), before additional root runtime transforms.",
        "The right image carrier is903x512 at scale(.8892822265625,.8886260986328125), not the full PNG size or a guessed440x260 card.",
    ],
    "own_projection": {
        "scale": 2 / 3,
        "visible_rows": 11,
        "row_base_xywh": [2 / 3, 122 * 2 / 3, 850 * 2 / 3, 54],
        "row_step": 52,
        "initial_text_x": 52,
        "text_font": 30,
        "image_xywh": [581.3333, 78.6667, 535.348, 303.318],
        "description_viewport_xywh": [586, 396, 633.3372, 220.0013],
        "description_glyph_relative_xy": [2.0111, 10.6778],
        "description_font": 31.25,
    },
    "limitations": [
        "No original target execution, screenshot rendering of this SFL or fresh original asset extraction.",
        "Root runtime transforms, exact raster/material identity and every selected-row effect are not claimed pixel-identical.",
        "Own long row names may fit a slightly smaller font; this is not a claim that original smooth horizontal marquee is reproduced.",
        "The host ScrollBox uses its own line-height and wheel behavior, recreated per row to reset scroll; not the original150-update marquee or text-control implementation.",
        "Description raw gap65436 must not be used as the previously unsigned26174.4 design line gap. Its final signed/semantic consumer is not accepted here.",
        "Explicit reviewed own-art references now bind15 evidence cards to17 unique images (22 links). Other illustrations remain unbound; never fill them with unrelated art.",
    ],
    "original_runtime_observed": False,
}
write(EXTERNAL / "pad_text_layout_findings.json", findings)
write(ROOT / "docs/analysis/v3_rebuild/pad_text_layout_findings.json", findings)
index_path = SPEC / "evidence_index.json"
index = json.loads(index_path.read_text(encoding="utf-8"))
assert index["target_sha256"] == TARGET
by_id = {row["evidence_id"]: row for row in index["records"]}
old_count = len(by_id)
for record in bundle["records"]:
    if record["evidence_id"] in by_id:
        continue
    by_id[record["evidence_id"]] = {key: record[key] for key in ["evidence_id", "operation", "parameters", "confidence", "authority", "locations"]}
index["records"] = sorted(by_id.values(), key=lambda r: r["evidence_id"])
supplement = {"path": str(BUNDLE), "sha256": findings["bundle_sha256"], "records": len(bundle["records"])}
index["supplementary_bundles"] = [r for r in index.get("supplementary_bundles", []) if r["path"] != str(BUNDLE)] + [supplement]
write(index_path, index)
numbers_path = SPEC / "numbers.json"
numbers = json.loads(numbers_path.read_text(encoding="utf-8"))
numbers["coverage"]["rea_evidence_records"] = len(by_id)
numbers["ui"]["pad_text_layout_followup_20261030"] = {"findings": str(EXTERNAL / "pad_text_layout_findings.json"), "bundle": supplement, "visible_rows": 11, "font_design": 45, "initial_scroll_offset_design": 80, "scroll_speed_per_update": 1, "scroll_wait_updates": 150, "repeat_gap_design": 990, "original_runtime_observed": False, "behavior_progress_changed": False}
write(numbers_path, numbers)
check_path = ROOT / "docs/analysis/v3_rebuild/pad_evidence_text_hierarchy_check.json"
check = json.loads(check_path.read_text(encoding="utf-8"))
check["new_question"]["status"] = "closed_for_setter_and_scroll_fields; root/material exactness remains separate"
check["new_question"]["findings"] = "pad_text_layout_findings.json"
write(check_path, check)
print(json.dumps({"new_evidence_records": len(by_id) - old_count, "indexed_records": len(by_id), "behavior_progress_changed": False}))
