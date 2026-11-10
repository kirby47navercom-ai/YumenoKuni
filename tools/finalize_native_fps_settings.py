"""Record the verified FPS option and frozen native package evidence, without relaunching."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / 'Game/Saved/native-engine-perf-20261102'

def read(relative):
    return json.loads((ROOT / relative).read_text(encoding='utf-8-sig'))

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def main():
    build = Path(read('Game/build-result.json')['executable']).parent.name
    assert build == '2026-11-01T20-34-21-051Z-9e3bf267'
    refs = {
        'trial': 'Game/Saved/native-performance-1793563484142/report.json',
        'world': 'Game/Saved/native-performance-1793563953600/report.json',
        'cap30': 'Game/Saved/native-performance-1793564408407/report.json',
        'cap60': 'Game/Saved/native-performance-1793564475543/report.json',
        'settings': 'Game/Saved/native-fps-settings-1793563709838/report.json',
        'canvasAim': 'Game/Saved/native-canvas-aim-1793563780342/report.json',
        'canonicalTrial': 'Game/Saved/native-all-tasks-1793563823892/report.json',
        'currentCanvasClicks': 'Game/Saved/native-canvas-input-1793565375837/report.json',
        'titleDelta': 'Game/Saved/native-engine-perf-20261102/title-background-delta.json',
        'canvasDelta': 'Game/Saved/native-engine-perf-20261102/canvas-fix/package-delta.json',
        'runtimeDelta': 'Game/Saved/native-engine-perf-20261102/package-delta.json',
        'sourceIdentity': 'Game/Saved/source-identity-9e3bf267.json',
        'cleanup': 'Game/Saved/native-qa-retention-20261102-053900-021.json',
        'focusedUI': 'Game/Saved/native-ui-focused-1793561555973/report.json',
    }
    proofs = {key: read(path) for key, path in refs.items()}
    for key in ['trial', 'world', 'cap30', 'cap60', 'settings', 'canvasAim',
                'canonicalTrial', 'currentCanvasClicks', 'titleDelta', 'canvasDelta', 'focusedUI']:
        assert proofs[key]['ok'], key
    assert proofs['sourceIdentity']['status'] == 'PASS'
    assert proofs['titleDelta']['allOtherPackageBytesExact']
    assert proofs['titleDelta']['samePlayerAndGameNativeBinaries']
    assert proofs['settings']['canonicalSaveUnchanged']
    assert proofs['canvasAim']['canonicalSaveUnchanged']
    checkpoint = ROOT / 'Game/Saved/ui-checkpoints/normal-ch3-latest/savegames.json'
    checkpoint_sha = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    assert checkpoint_sha == 'd43c126c6df61cb9f96b312cb65fdcf9992605368617f23c572fc5c6e9850fe7'
    env = dict(os.environ)
    env['PATH'] = 'C:/msys64/ucrt64/bin;' + env['PATH']
    units = []
    for exe, args in [
        ('ui-dirty-test.exe', []), ('fps-options-test.exe', []),
        ('canvas-fix/test.exe', []),
        ('check-delta.exe', [str(RECEIPT / 'delta-test/frames.json')]),
    ]:
        result = subprocess.run([str(RECEIPT / exe), *args], env=env,
                                capture_output=True, text=True, check=True)
        units.append({'executable': exe, 'exitCode': result.returncode,
                      'stdout': result.stdout.strip()})
    for name in ['image-cache', 'text-cache', 'visible-render']:
        assert read(f'Game/Saved/native-engine-perf-20261102/rendering-units/{name}.json')['passed']
    write(RECEIPT / 'native-unit-results.json', {'ok': True, 'units': units})
    result = {
        'status': 'fps-settings-and-reproduced-compatibility-fixes-verified',
        'build': build, 'fpsSettingsAcceptance': True,
        'performanceDiagnosisVerified': True, 'wholeGamePerformanceAcceptance': False,
        'highestSettingReachedInTrial': False,
        'fpsOptions': {'choices': [30, 60, 120], 'default': 120,
                       'immediateApply': True, 'savedAndColdRestartVerified': True,
                       'oldPreferenceMigration': 'Missing frameRate defaults to120',
                       'unlimitedOption': False, 'activeTrialTimerPausedInOptions': True},
        'measurements': {key: {'fps': proofs[key]['fps'], 'seconds': proofs[key]['seconds'],
                               'build': proofs[key]['build'], 'report': refs[key]}
                         for key in ['trial', 'world', 'cap30', 'cap60']},
        'measurementScope': 'This PC, hidden owned native Win32 player. Ordinary execution profiling disabled; read-only1Hz telemetry. Not foreground/all-PC proof.',
        'packageInheritance': 'Measurements/settings/aim/canonical success belong to3c09. Current9e changes only Title/TitleBg viewport anchors; all other package bytes exact. Current9e canvas clicks at3 sizes separately passed. Full focused UI suite belongs to177 and is retained with explicit delta receipts, not relabelled as a9e rerun.',
        'cause': 'Engine UI state copying, serialization/restore and UI raster/transport dominate. Measured C++ gameplay invocation0.425ms within31.161ms original frame. RTX4070SUPER adapter identity verified; no WARP claim.',
        'fixes': ['Exact leaf UI restore and immutable descriptor references',
                  'Bounded exact-pixel raster/text caching and visible asset preparation in frozen engine package',
                  'Guarded lossless RGBA XOR transport; original full frame/PNG fallback preserved',
                  'Phase-based selected FPS scheduling and independent render overlap',
                  'Explicit fit-canvas mouse coordinates in22 calls across17 game source files',
                  'Title background fills viewport at4:3'],
        'remaining': 'Trial measured55.436FPS with120 selected;120trial is not achieved or accepted. Continue at same normal3 save for any future performance work; never repeat completed campaign by default.',
        'preserved': {'normalSaveSHA256': checkpoint_sha,
                      'installedEngineReadOnly': True, 'foreignDpiEditsPreservedAndExcludedFromPlayer': True,
                      'noOriginalV3ExecutionOrExtraction': True, 'noCommitOrAutomation': True},
        'sourceSdkLimit': 'C++ fit-canvas helper exists in authorized engineCreate source. Installed SDK unchanged. Frozen packaged executable verified; source compilation needs the matching source SDK.',
        'cleanup': {'moved': len(proofs['cleanup']['records']),
                    'deleted': 0, 'physicalBytesReclaimed': 0, 'receipt': refs['cleanup']},
        'evidence': refs,
    }
    write(ROOT / 'Game/Saved/native-performance-settings-final-20261102.json', result)
    write(ROOT / 'docs/analysis/v3_rebuild/native_performance_settings_audit_20261102.json', result)
    write(RECEIPT / 'status.json', {key: result[key] for key in ['status', 'build',
          'fpsSettingsAcceptance', 'wholeGamePerformanceAcceptance', 'highestSettingReachedInTrial']})
    print(json.dumps({'status': result['status'], 'build': build, 'nativeUnits': len(units),
                      'trialFPS': result['measurements']['trial']['fps'],
                      'worldFPS': result['measurements']['world']['fps']}))

if __name__ == '__main__':
    main()
