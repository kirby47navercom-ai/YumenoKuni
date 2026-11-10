"""Check the package delta and the linear bound of the previously rendered cue bank."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
load = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
package = Path(load(ROOT / 'Game/build-result.json')['executable']).parent
previous = ROOT / 'Game/Builds/windows/2026-10-31T11-08-00-592Z-df1296fa'
current_audio = package / 'Content/Assets/Audio'
previous_audio = previous / 'Content/Assets/Audio'
assert current_audio.is_dir() and previous_audio.is_dir()
source_audio = ROOT / 'Game/Assets/Audio'
rows = []
for file in sorted(current_audio.glob('S_*.hbaudioasset.json')):
    current = load(file)
    old = load(previous_audio / file.name)
    assert current == load(source_audio / file.name)
    assert current.pop('volume') == .4 and old.pop('volume') == 1
    assert current == old, file.name
    clip = package / 'Content' / current['clip']
    old_clip = previous / 'Content' / current['clip']
    assert sha(clip) == sha(old_clip) == sha(ROOT / 'Game' / current['clip'])
    rows.append({'asset': file.name, 'clipSHA256': sha(clip), 'gainBefore': 1, 'gainAfter': .4})
assert len(rows) == 229
mixer = load(current_audio / 'MX_Yumeno.hbaudiomixer.json')
assert mixer == load(previous_audio / 'MX_Yumeno.hbaudiomixer.json')
assert all(not b['compressor'] and not b.get('effects') and not b.get('sends') and not b.get('ducking') for b in mixer['buses'])
unchanged = {}
for group in ['Data', 'UI']:
    files = list((package / 'Content/Assets' / group).rglob('*.json'))
    for file in files:
        assert file.read_bytes() == (previous / file.relative_to(package)).read_bytes(), str(file)
    unchanged[group] = len(files)
for file in (ROOT / 'Game/Source').glob('*'):
    if file.is_file():
        assert file.read_bytes() == (previous / 'Content/Source' / file.name).read_bytes(), file.name
baseline = load(ROOT / 'Game/Saved/v4-audio-bank-headroom-1793455395331/report.json')
assert {r['asset'] for r in baseline['rows']} == {r['asset'] for r in rows}
predictions = [{'asset': r['asset'], 'predictedPeak': r['peak'] * (.4 / r['gain'])} for r in baseline['rows']]
assert all(r['predictedPeak'] < 1 for r in predictions)
checkpoint = ROOT / 'Game/Saved/ui-checkpoints/normal-ch3-latest/savegames.json'
assert sha(checkpoint) == 'd43c126c6df61cb9f96b312cb65fdcf9992605368617f23c572fc5c6e9850fe7'
report = {'ok': True, 'build': package.name, 'previous': previous.name, 'audioAssets': rows,
          'unchangedJSON': unchanged, 'gameCppUnchanged': True, 'mixerUnchanged': True,
          'normalCheckpointUnchanged': True, 'allApprovedRawCueBytesUnchanged': True,
          'linearPredictionsFromEarlierFullBankRender': predictions,
          'maximumPredictedSingleCuePeak': max(r['predictedPeak'] for r in predictions),
          'scope': 'Package changes only asset gain1→.4 in229 descriptors. Raw audio, CPP, Data, UI and mixer unchanged. All single-cue bounds are linear scaled predictions from full WebView PCM baseline, not second complete rendering, simultaneous mix guarantees or listening.'}
(ROOT / 'Game/Saved/audio-headroom-package-delta.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'ok': True, 'build': package.name, 'gainChanges': len(rows), 'maximumPredictedSingleCuePeak': report['maximumPredictedSingleCuePeak'], 'unchangedJSON': unchanged}))
