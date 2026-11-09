"""Exact, directly inspected existing-art bindings for chapters two and six.

This module creates no assets and publishes no output. Unseen clues and blank
document interiors remain real gates; catalog completion is not clue proof.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = "art/v4_production/completion/final_catalog.json"
PICTURES = {
    "T2-SPOT-A01": {
        "file": "art/inspection_v4/delivery/chest_exterior.webp",
        "sha256": "4c4d4352fda01db25cabbf1ea0992c035f35e32d2f8ffea092fb46ee50901ea5",
        "catalogId": "chest_exterior", "answerRegionId": "external-latch-left",
        "evidenceId": "v4:E2-02", "title": "장비 함의 바깥 구조",
        "proof": [("182", 573, "영역A=바깥 걸쇠"), ("182", 574, "바깥 걸쇠 영역"), ("12b1", 148, "걸쇠는 출발할 때 닫혀 있었어요")],
        "regions": [
            {"id": "external-latch-left", "label": "바깥 걸쇠", "correct": True, "polygon": [[.363,.360],[.402,.350],[.402,.481],[.365,.496]]},
            {"id": "external-latch-right", "label": "반대쪽 바깥 걸쇠", "correct": True, "polygon": [[.731,.294],[.765,.285],[.766,.416],[.733,.424]]},
            {"id": "front-wheel", "label": "앞 바퀴", "correct": False, "wrongVariant": "wheel", "polygon": [[.272,.770],[.331,.744],[.350,.837],[.301,.883],[.267,.844]]},
            {"id": "right-wheel", "label": "오른쪽 바퀴", "correct": False, "wrongVariant": "wheel", "polygon": [[.756,.649],[.786,.625],[.821,.679],[.815,.724],[.782,.744],[.756,.706]]},
            {"id": "rear-wheel", "label": "뒤 바퀴", "correct": False, "wrongVariant": "wheel", "polygon": [[.156,.615],[.183,.605],[.205,.658],[.190,.714],[.162,.710],[.153,.671]]},
        ],
        "visualReview": "Direct full-image inspection: two closed external metal latches and three actual visible wheels. The image does not show inside cloth; no invisible cloth region is manufactured. Both actual latches satisfy the same source question.",
    },
    "T2-MM-A02": {
        "file": "art/inspection_v4/delivery/microphone_base_forensic_r2.webp",
        "sha256": "ccf99c365b57f207f33f8cadfa74ee9016bae5316d2fe96d02fef6fc0d27a973",
        "catalogId": "microphone_base", "answerRegionId": "heavy-detached-base",
        "evidenceId": "v4:E2-04", "title": "직원용 통로의 분리된 받침대",
        "proof": [("182", 759, "마이크 스탠드/통로 도구 사진"), ("182", 762, "무거운 받침 밑판"), ("12b2", 75, "봉은 빠져 있고"), ("12b2", 91, "모서리 한쪽은 찌그러져 있다")],
        "regions": [
            {"id": "heavy-detached-base", "label": "무거운 금속 받침 밑판", "correct": True, "polygon": [[.431,.491],[.443,.419],[.489,.404],[.529,.447],[.533,.488],[.611,.505],[.671,.548],[.697,.596],[.704,.651],[.690,.731],[.649,.793],[.561,.825],[.460,.826],[.359,.790],[.305,.733],[.291,.652],[.342,.571]]},
            {"id": "covering-cloth", "label": "덮인 천", "correct": False, "polygon": [[.240,.400],[.310,.330],[.390,.310],[.410,.380],[.340,.440],[.280,.600],[.235,.700]]},
        ],
        "visualReview": "Direct inspection of full 3840x2160 delivery and literal forensic crop: the broad detached metal base, threaded socket, partly covering cloth and edge are visible. The rod and chest wheels are absent. No dimensions or unique injury/weapon attribution is inferred from drawn residue.",
    },
}

DOCUMENT_CONTRACT = "ui/v4/documents_case6_runtime_v1/manifest.json"
REVIEWED_DOCUMENT_CONTRACT = "f6d8cc7a4fe262ab051d621bcab91eccd4c0b71d878dffa28414cefbef6ebf87"
CONNECTION_CONTRACT = "ui/v4/documents_case2_connection_v1/manifest.json"
REVIEWED_CONNECTION_CONTRACT = "3b066c27fcb4d72b431eb1cdd3e1c7bc97684aff8b73451f53515cc68d829015"


def _documents():
    path = ROOT / DOCUMENT_CONTRACT
    if hashlib.sha256(path.read_bytes()).hexdigest() != REVIEWED_DOCUMENT_CONTRACT:
        raise ValueError("Chapter-six document contract changed; re-inspect source fields and UV masks")
    contract = json.loads(path.read_text(encoding="utf-8"))
    result = {}
    for ident, key in (("T6-MM-A02", "safety"), ("T6-MM-A03", "statement"), ("T6-SPOT-A01", "topology")):
        picture = contract[key]
        result[ident] = {**deepcopy(picture), "file": picture["image"], "catalogId": None, "proofRecords": deepcopy(picture["source"]), "contract": DOCUMENT_CONTRACT}
    path = ROOT / CONNECTION_CONTRACT
    if hashlib.sha256(path.read_bytes()).hexdigest() != REVIEWED_CONNECTION_CONTRACT:
        raise ValueError("Chapter-two connection contract changed; re-inspect source topology and UV masks")
    picture = json.loads(path.read_text(encoding="utf-8"))
    result["T2-MM-01"] = {**deepcopy(picture), "file": picture["image"], "catalogId": None, "proofRecords": deepcopy(picture["source"]), "contract": CONNECTION_CONTRACT}
    return result


PICTURES.update(_documents())

PICTURES.update({
    "T2-MM-A03": {
        "file": "art/inspection_v4/delivery/plastic_loop_join_builtin_r1.webp",
        "sha256": "05ac8abb9053cd670d3aace3e4f4d2615a6b14a6a62314e2a3c48d52e5836a60",
        "catalogId": None, "artMetadata": "art/inspection_v4/generated/plastic_loop_join_builtin_r1.json", "artId": "plastic_loop_join_builtin_r1",
        "answerRegionId": "two-fracture-boundaries", "evidenceId": "v4:E2-08", "title": "회수 조각과 개인 재생기 끈의 파단면",
        "proof": [("182", 787, "파단면 대조 그림"), ("182", 790, "이어지는 파단면"), ("12b1", 180, "개인 재생기를 꺼낸다"), ("12b1", 262, "부러진 부분을 가볍게 맞춘다")],
        "regions": [{"id": "two-fracture-boundaries", "label": "두 실물의 이어지는 파단면", "correct": True, "polygon": [[.401,.559],[.452,.540],[.486,.513],[.531,.493],[.558,.542],[.554,.643],[.533,.701],[.490,.710],[.454,.738],[.403,.721]]}, {"id": "intact-fabric-strap", "label": "남아 있는 끈", "correct": False, "polygon": [[.630,.464],[.706,.432],[.768,.358],[.792,.343],[.807,.389],[.764,.506],[.694,.567],[.645,.586]]}, {"id": "player-housing", "label": "개인 재생기 본체", "correct": False, "polygon": [[.640,.080],[.928,.080],[.928,.267],[.853,.300],[.790,.254]]}],
        "visualReview": "Directly viewed full6688x3764 delivery: left recovered dark plastic fragment and right strap-attached remainder have facing irregular break surfaces, with a visible gap; intact braid and separate player housing remain distinguishable. The image is an object comparison, not a new cutting/timing/identity proof. A separate short cord on the recovered fragment is outside the depicted detail, so the artwork does not replace the earlier hand/cord record.",
    },
    "T6-MM-01": {
        "file": "art/inspection_v4/delivery/historical_entrance_builtin_r1.webp",
        "sha256": "853874ca429f8d927029473cee6bd8462bdef0284e595907243bfd9635be53aa",
        "catalogId": None, "artMetadata": "art/inspection_v4/generated/historical_entrance_builtin_r1.json", "artId": "historical_entrance_builtin_r1",
        "answerRegionId": "two-faces-clothing-common-heading", "evidenceId": "v4:E6-03", "title": "옛 행사일의 주 통로 입구 자료",
        "proof": [("16b1", 201, "어린 코토와 하루카가 함께 안쪽으로 가는 장면"), ("16b1", 211, "현장 장치 시각"), ("186", 389, "수사 때의 옛 행사일 사진/날짜")],
        "regions": [{"id": "two-faces-clothing-common-heading", "label": "두 얼굴·복장과 함께 향한 몸", "correct": True, "polygon": [[.245,.180],[.430,.130],[.506,.245],[.533,.377],[.557,.254],[.680,.213],[.743,.322],[.762,.649],[.710,.930],[.245,.930],[.185,.725]]}],
        "visualReview": "Directly viewed full6688x3764 delivery: two distinct child identities at one threshold, long light-brown-haired Koto left and pink-bob Haruka right, both faces and forward-oriented clothing/upper bodies visible. The still frame does not establish continuous movement, exact foot positions, an inner-hall act, clock offset or a later push. No timestamp/date text, memorial cross, new witness or injury is painted.",
    },
})

UNBOUND = {}


def _validate(sources):
    docs = {s.prefix: s for s in sources.values()}
    from v4_story_case2 import REVIEWED_HASHES as CASE2
    from v4_story_case6 import REVIEWED_HASHES as CASE6
    reviewed = {**CASE2, **CASE6}
    _documents()  # Recheck the reviewed text/layout/mask contract each call.
    catalog = json.loads((ROOT / CATALOG).read_text(encoding="utf-8-sig"))
    indexed = {x["id"]: x for x in catalog["inspection_views"]}
    proofs = {}
    for ident, p in PICTURES.items():
        if hashlib.sha256((ROOT / p["file"]).read_bytes()).hexdigest() != p["sha256"]:
            raise ValueError("Inspected clue picture changed; re-inspect visible regions: " + p["file"])
        if p.get("catalogId"):
            entry = indexed[p["catalogId"]]
            if entry["file"].replace("\\", "/") != p["file"] or entry["size"] != [3840, 2160]:
                raise ValueError("Reviewed catalog image identity/size changed: " + ident)
        if p.get("artMetadata"):
            metadata = json.loads((ROOT/p["artMetadata"]).read_text(encoding="utf-8-sig"))
            if metadata.get("id") != p["artId"] or metadata.get("tool") != "built-in image_gen":
                raise ValueError("Reviewed original-art identity changed: " + ident)
        proofs[ident] = []
        rows = p.get("proof", [(q["file"].split("_", 1)[0], q["line"], q["quote"]) for q in p.get("proofRecords", [])])
        for prefix, line, quote in rows:
            source = docs[prefix]
            if source.hash != reviewed[prefix] or quote not in source.lines[line - 1]:
                raise ValueError("Picture source changed; re-read source proof: " + source.name)
            proofs[ident].append({**source.ref(line), "quote": quote})
    return proofs


def bind_pictures(g, sources, tasks):
    """Apply to Graph or exported graph before scoring; no filesystem writes."""
    chapter = str(g["chapter"] if isinstance(g, dict) else g.chapter)
    nodes = g["nodes"] if isinstance(g, dict) else g.nodes
    if chapter not in ("2", "6"):
        return
    proofs = _validate(sources)
    for ident, p in PICTURES.items():
        if not ident.startswith("T" + chapter + "-"):
            continue
        task = tasks["tasks"][ident]
        task.update(image=p["file"], coordinateSystem="normalized-image-uv", answerRegionId=p["answerRegionId"], regions=deepcopy(p["regions"]))
        task["requiresEvidence"] = list(dict.fromkeys([*task.get("requiresEvidence", []), p["evidenceId"]]))
        if p.get("presentationPrompt"):
            task.setdefault("sourcePromptBeforeTopologyClarification", task["prompt"])
            task["prompt"] = p["presentationPrompt"]
            task["spatialProofScope"] = p["layoutRole"]
        task["bindings"] = [b for b in task.get("bindings", []) if b["kind"] != "forensicImageRegions"]
        task["runtimeReady"] = not any(b.get("required") for b in task["bindings"])
        task["pictureProvenance"] = {"catalog": CATALOG if p.get("catalogId") else None, "catalogEntry": p.get("catalogId"), "contract": p.get("contract"), "artMetadata": p.get("artMetadata"), "sha256": p["sha256"], "sourceProof": proofs[ident], "visualReview": p["visualReview"], "newEvidence": False, "unseenDistractorsCreated": False}
        # A wheel-specific original line is played only for an actual wheel.
        # A picture with no thin rod cannot claim the player picked that rod.
        if "sourceWrongBeforePictureBinding" not in task:
            task["sourceWrongBeforePictureBinding"] = deepcopy(task.get("wrong", []))
            task["sourceWrongVariantsBeforePictureBinding"] = deepcopy(task.get("wrongVariants", []))
        original = task["sourceWrongBeforePictureBinding"]
        if ident == "T2-SPOT-A01":
            task["wrongVariants"] = [{"cause": "wheel", "script": original}]
            task["wrong"] = [x for x in original if x["source"]["line"] == 580]
        elif ident == "T6-SPOT-A01":
            task["wrongVariants"] = [{"cause": "floor", "script": original}]
            task["wrong"] = [x for x in original if x["source"]["line"] == 512]
        elif ident == "T2-MM-01":
            # The source already provides three explicit, actually pictured
            # wrong causes. Keep them and dispatch by region cause, not index.
            task["wrong"] = original
        else:
            cause = {"T2-MM-A02": "thin-rod-not-shown", "T2-MM-A03": "unprovided-public-card-not-selected", "T6-MM-A02": "unprovided-signature-not-selected", "T6-MM-A03": "unprovided-reception-number-not-selected", "T6-MM-01": "unprovided-clock-signature-or-inner-hall-region"}[ident]
            task["unavailableSourceWrongVariants"] = [{"cause": cause, "script": original, "dispatch": False}] + [{**deepcopy(v), "dispatch": False} for v in task["sourceWrongVariantsBeforePictureBinding"]]
            task["wrong"], task["wrongVariants"] = [], []
        task["wrongPolicy"] = "Use only the selected visible-region cause. An unmasked miss retries without inventing an absent object or granting a new clue."
        for node in nodes.values():
            if node.get("taskId") == ident:
                node["runtimeReady"] = task["runtimeReady"]
        grants = [n for n in nodes.values() if n.get("type") == "evidence" and n.get("evidenceId") == p["evidenceId"] and not n.get("revision")]
        if len(grants) != 1:
            raise ValueError("Exact first acquisition missing/ambiguous: " + p["evidenceId"])
        evidence = grants[0]
        docid = evidence["id"] + ":inspected-existing-picture"
        if docid in nodes:
            if nodes[docid]["image"] != p["file"] or nodes[docid]["next"] != evidence["id"]:
                raise ValueError("Inspection acquisition contract changed: " + docid)
            continue
        before = [n for n in nodes.values() if n.get("next") == evidence["id"]]
        if len(before) != 1:
            raise ValueError("Inspection picture predecessor missing/ambiguous: " + p["evidenceId"])
        before[0]["next"] = docid
        document = {"id": docid, "type": "document", "title": p["title"], "rows": [], "image": p["file"], "private": False, "source": evidence["source"], "next": evidence["id"], "inspectionOnly": True, "grantsEvidence": False, "pictureSha256": p["sha256"]}
        if isinstance(g, dict):
            nodes[docid] = document
        else:
            g.add(docid, document)
    if chapter == "6":
        picture = PICTURES["T6-MM-01"]
        task = tasks["tasks"]["T6-PERSON-A02"]
        override = task["candidateOverrides"]["haruka"]
        override.update(image=picture["file"], caption="오른쪽 인물 · 옛 행사일(5년 전)", layout="landscape-photo", identityScope="actual-past-victim-not-current-created-body", pictureSha256=picture["sha256"])
        task["requiresEvidence"] = list(dict.fromkeys([*task.get("requiresEvidence", []), "v4:E6-03"]))
        task["bindings"] = [b for b in task.get("bindings", []) if b["kind"] != "historicalVictimPortrait"]
        task["runtimeReady"] = not any(b.get("required") for b in task["bindings"])
        task["historicalPictureProvenance"] = deepcopy(tasks["tasks"]["T6-MM-01"]["pictureProvenance"])
        for node in nodes.values():
            if node.get("taskId") == "T6-PERSON-A02":
                node["runtimeReady"] = task["runtimeReady"]
    # Explicit graph metadata records rejected matches without changing the
    # actual unresolved task, its source, required binding or readiness.
    review = {k: deepcopy(v) for k, v in UNBOUND.items() if k.startswith("T" + chapter + "-")}
    if isinstance(g, dict):
        g["pictureBindingReview"] = review
    else:
        g.pictureBindingReview = review
    return review

