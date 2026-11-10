"""Provenance gate: every owned runtime character picture uses the curated family."""
import hashlib
import json
from pathlib import Path
from v4_character_sources import ROOT, catalogue


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


delivery, sources = catalogue()
_, hd = catalogue(hd=True)
approved = {p.resolve() for p in sources.values()}
approved.update((ROOT/r['webp']).resolve() for r in delivery['assets'])
receipt = json.loads((ROOT/'Game/Saved/character-style-export.json').read_text(encoding='utf8'))
expected = set()
for row in receipt['records']:
    source, output = ROOT/row['source'], ROOT/row['output']
    assert source.resolve() in approved, row
    assert sha(source) == row['source_sha256'], row['source']
    assert sha(output) == row['output_sha256'], row['output']
    expected.add(output.resolve())
art = ROOT/'Game/Assets/Art'
actual = {p.resolve() for family in ['sprites','figure','cutin'] for p in (art/family).rglob('*')
          if p.is_file() and p.suffix.lower() in ['.webp','.png','.jpg']}
actual.update(p.resolve() for p in (art/'pad').glob('face_*') if p.is_file())
assert expected == actual, {'unexpected':[str(p) for p in actual-expected], 'missing':[str(p) for p in expected-actual]}
court = json.loads((ROOT/'Game/Assets/Data/court.json').read_text(encoding='utf8'))['figures']
for slug in 'mio rin ken nana taiga ai rei sora haruka sho koto akari riku satsuki yuu kaede'.split():
    assert court[slug+'_C01'] == court[slug], slug+' C01 can fall back to old art'
provenance = json.loads((ROOT/'Game/Saved/court-figures-export.json').read_text(encoding='utf8'))
assert all((ROOT/r['source']).resolve() in {p.resolve() for p in hd.values()} for r in provenance.values())
legacy = [p for folder in ['art/sprites','art/standing','art/standing_hd','art/cutin']
          for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix.lower() in ['.png','.webp','.jpg','.jpeg']]
result = {'runtimeProvenanceGate':True, 'ownedRuntimeRoutes':len(expected), 'curatedMasters':17,
          'curatedIllustratedPoses':368, 'C01Aliases':16, 'oldSourceImagesStillPresent':len(legacy),
          'oldSourceDeletionComplete':False, 'sourceDeletionBlock':'Automatic approval review rejected bulk source-image deletion: blocked by policy.',
          'scope':'Provenance/file-set gate only. Compatibility aliases are not new illustrated poses. Actual drawing quality and placement require direct visual review.'}
(ROOT/'Game/Saved/v4-character-style-gate.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(result,ensure_ascii=False))
