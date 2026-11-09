"""Only bind reviewed own art with explicit evidence IDs in the authoring catalogue.

Broad I3/I5 story references and a name mentioned in prose are deliberately not
converted into evidence IDs. They require a separate semantic binding review.
"""
import json
import re
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def build():
    catalogue = json.loads((ROOT / "art/v4_production/completion/final_catalog.json").read_text(encoding="utf-8"))
    documents = json.loads((ROOT / catalogue["documents"]).read_text(encoding="utf-8"))["assets"]
    evidence = {}
    for path in sorted((ROOT / "data/v4_story/chapters").glob("*.json")):
        evidence.update(json.loads(path.read_text(encoding="utf-8")).get("evidenceCatalog", {}))
    known = set(evidence)
    result, unmatched = {}, []
    def add(row, reference):
        image = row.get("webp", row.get("file", ""))
        assert image and (ROOT / image).is_file(), image
        for match in re.finditer(r"\b(E[1-6]-)(\d{2})((?:/\d{2})*)", reference):
            codes = [match[2]] + match[3].split("/")[1:]
            for code in codes:
                key = "v4:" + match[1] + code
                if key not in known:
                    unmatched.append({"viewId": row["id"], "manuscriptReference": match[1] + code, "reason": "No matching runtime evidence ID; semantic alias requires review"})
                    continue
                entries = result.setdefault(key, [])
                if not any(item["image"] == image for item in entries):
                    entries.append({"image": image, "viewId": row["id"], "binding": "explicit-own-art-evidence-reference"})
    for row in catalogue["inspection_views"]:
        add(row, row.get("story_reference", ""))
    for row in documents:
        add(row, row.get("role", ""))
    reviewed_path = ROOT / "tools/v4_evidence_art_semantic.json"
    reviewed = json.loads(reviewed_path.read_text(encoding="utf-8")) if reviewed_path.exists() else {"bindings": []}
    views = {row["id"]: row for row in catalogue["inspection_views"]}
    illustration_path=ROOT/'tools/v4_evidence_illustration_views.json'
    if illustration_path.exists():
        for row in json.loads(illustration_path.read_text(encoding='utf-8'))['views']:
            assert row['id'] not in views, 'Evidence illustration ID collision'
            assert row['reviewed'] and row['scope'], 'Unreviewed evidence illustration'
            views[row['id']]=row
    # Explicitly reviewed incident art may illustrate the already acquired
    # victim/file context. It does not establish a medical cause, time or actor;
    # those remain the existing evidence text. No automatic chapter aliasing.
    incident_review=json.loads((ROOT/'art/v4_production/death_posture_20261103/review.json').read_text(encoding='utf-8'))
    for row in incident_review['rows']:
        image=row['delivery']
        assert hashlib.sha256((ROOT/image).read_bytes()).hexdigest()==row['sha256'], 'Re-review changed incident context'
        ident='scene_context_'+row['logical']
        views[ident]={'id':ident,'file':image,'scope':'Previously revealed incident context only; no additional medical inference or acquisition.'}
    document_contract = json.loads((ROOT / "ui/v4/documents_case6_runtime_v1/manifest.json").read_text(encoding="utf-8"))
    for key in ("safety", "statement", "topology"):
        row = document_contract[key]
        ident = "case6_document_" + key
        # These are reviewed readable documents/topology, not a guessed image
        # with a similar old evidence number. Validate its own quoted source.
        views[ident] = {"id": ident, "file": row["image"], "documentSources": row["source"], "evidenceId": row["evidenceId"]}
    for binding in reviewed["bindings"]:
        ident = binding["evidenceId"]
        assert ident in evidence, ident
        actual = evidence[ident]
        digest = hashlib.sha256((actual["name"] + "\n" + actual["text"]).encode("utf8")).hexdigest()
        assert digest == binding["evidenceTextSha256"], "Re-review changed evidence semantics: " + ident
        retired = set(binding.get('replaceCatalogueViews', []))
        if retired:
            current = result.get(ident, [])
            assert retired <= {r['viewId'] for r in current}, 'Changed replaced catalogue pictures: ' + ident
            result[ident] = [r for r in current if r['viewId'] not in retired]
        for ref in binding.get('sourceStatements', []):
            text=(ROOT/'docs/design/rewrite_v4'/ref['file']).read_text(encoding='utf-8-sig')
            assert hashlib.sha256(text.encode()).hexdigest()==ref['sha256'], 'Re-review changed statement source'
            assert ref['quote'] in text.splitlines()[ref['line']-1], 'Re-review moved or changed statement'
        for visual in binding["views"]:
            row = views[visual["id"]]
            if "documentSources" in row:
                assert row["evidenceId"] == ident
                for ref in row["documentSources"]:
                    text = (ROOT / "docs/design/rewrite_v4" / ref["file"]).read_text(encoding="utf-8-sig")
                    assert hashlib.sha256(text.encode("utf8")).hexdigest() == ref["sha256"], "Re-review changed document source"
                    assert ref["quote"] in text.splitlines()[ref["line"]-1], "Document quotation moved or changed"
            image = row.get("webp", row.get("file", ""))
            assert hashlib.sha256((ROOT / image).read_bytes()).hexdigest() == visual["sha256"], "Re-review changed clue picture: " + image
            entries = result.setdefault(ident, [])
            if not any(item["image"] == image for item in entries):
                entries.append({"image": image, "viewId": row["id"], "binding": "explicit-reviewed-semantic-reference"})
    return {"schemaVersion": 1, "items": result, "unmatchedReferences": unmatched, "policy": "Explicit catalogue references plus individually reviewed semantic bindings pinned to evidence text and picture SHA. No guessed broad I3/I5/I6 alias, fabricated clue or automatic portrait replacement."}

if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False))
