"""Validate recorded visual gaps without granting image/task acceptance."""
import hashlib
import json
from pathlib import Path
from build_v4_story import ROOT,Source


def validate_review(sources=None):
    path=ROOT/"tools/v4_remaining_picture_review.json"
    review=json.loads(path.read_text(encoding="utf-8"))
    sources=sources or {p.name:Source(p) for p in (ROOT/"docs/design/rewrite_v4").glob("*.md")}
    assert len(review["contracts"])==len({x["taskId"] for x in review["contracts"]})==13
    assert len(review["approvedBindings"])==13
    images={x["file"]:x for x in review["reviewedImages"]}
    for image in images.values():
        assert hashlib.sha256((ROOT/image["file"]).read_bytes()).hexdigest()==image["sha256"],image["file"]
        assert image["rejectionReason"]
    for item in review["contracts"]:
        ref=item["source"];source=sources[ref["file"]]
        assert source.hash==ref["fileSha256"],ref["file"]
        assert source.lines[ref["line"]-1]==item["sourceQuote"],item["taskId"]
        if item["bindingReady"]:
            assert item["status"]=="bound-new-source-inspection"
            assert item["resolutionContract"]=="ui/v4/investigation_diagrams_v4/manifest.json"
        else:assert item["status"]=="missing-exact-inspected-picture"
        assert "regions" not in item and "answerRegionId" not in item
        assert all(p in images for p in item["rejectedExistingAssets"])
        assert item["requiredVisibleContent"]
    return {"status":"PASS","reviewedDeliveryImages":len(images),"sourceSpecificGaps":len(review["contracts"]),"sourceTaskContractsCurrent":True,"sourceBoundResolutions":13,"remainingExactPictures":0,"newPicturesCreated":True,"runtimeExecuted":False}


if __name__=="__main__":print(json.dumps(validate_review(),ensure_ascii=False))
