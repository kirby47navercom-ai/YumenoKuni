"""Attach bounded implementation QA without changing original REA evidence counts."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
NATIVE = Path('C:/Users/kirby/Downloads/v3_re/native')


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    audit_path = ROOT / 'docs/analysis/v3_rebuild/full_completion_audit_20261031.json'
    audit = read(audit_path)
    history = ROOT / 'docs/analysis/v3_rebuild/history/extended_qa_20261031'
    history.mkdir(parents=True, exist_ok=True)
    for source in [audit_path, ROOT / 'CODEX_HANDOFF.md', ROOT / 'DEBUG_HANDOFF.md', ROOT / 'docs/analysis/v3_rebuild/UI_교정_재개점_20261030.md']:
        target = history / source.name
        if not target.exists():
            shutil.copy2(source, target)
    report = {
        'status': 'extended-qa-pass-audio-headroom-repair-in-progress',
        'taskSuccessInjectedOnlyForStructuralTraversal': True,
        'routes': {'report': 'Game/Saved/choice-route-coverage.json', 'savedStateForkRuns': 503,
                   'coveredDecisionEdges': 1106, 'steps': 11492555, 'uncoveredAuthoredMenuOptions': 0,
                   'bothEndingsReachable': True, 'allHistoryCombinationsClaimed': False},
        'wrongCandidates': {'report': 'Game/Saved/wrong-choice-full-regression.json', 'cases': 631,
                            'tasks': 65, 'reasoningLinks': 46, 'comicSlots': 38, 'nativeGameplay': False,
                            'checks': 'Every candidate wrong at these positions, exact runtime-authored feedback, one HP/gaffe event, retained node/link, repeat frames, save roundtrip; correct callback no extra gaffe'},
        'narrativeContracts': {'report': 'Game/Saved/final-narrative-contracts.json', 'checks': 13,
                              'literaryQualityCertificate': False},
        'playableText': {'report': 'Game/Saved/playable-text-route-audit.json',
                         'assumedCharactersPerMinute': [250, 400], 'measuredHumanPlaytime': False,
                         'fiveHourTrialPassed': False, 'unselectedAlternativeDialogueAddedToOneRun': False},
        'alternateEndingNative': {'report': 'Game/Saved/v4-flow-1793453765826/report.json',
                                 'freshContinue': 'Game/Saved/v4-flow-1793454102123/entry-report.json',
                                 'nextExactDecisionSave': 'Game/Saved/v4-flow-1793453765826/ending-decision-savegames.json',
                                 'pixelsReviewed': 'Game/Saved/v4-flow-1793454102123/restored-ending.png',
                                 'fixture': False, 'taskSuccessInjected': False,
                                 'build': '2026-10-31T11-08-00-592Z-df1296fa'},
        'audio': {'decodedBank': 'Game/Saved/audio-full-decode-audit.json', 'files': 229,
                  'wholeBankMixerComparison': 'Game/Saved/v4-audio-bank-headroom-1793455395331/report.json',
                  'comparisonGain': .5, 'comparisonPeakMaximum': 1.1158686876296997,
                  'comparisonFailures': ['S_sfx_explode.hbaudioasset.json'],
                  'repairAssetGain': .4, 'status': 'generation-build-and-focused-native-pending',
                  'source': 'Game/tools/create-project.mjs', 'rawCueFilesModified': False,
                  'compressorOnlyCandidatesRejected': True, 'humanWholeBankListening': False,
                  'allSimultaneousSoundCombinationsBounded': False},
        'newOriginalExtraction': False, 'newREARecords': 0,
        'fixed24x5BehaviorProgressChanged': False,
    }
    final = '--final' in sys.argv
    if final:
        pcm_path = 'Game/Saved/v4-audio-bank-headroom-1793455818783/report.json'
        native_path = 'Game/Saved/v4-audio-headroom-live-1793455872846/report.json'
        delta_path = 'Game/Saved/audio-headroom-package-delta.json'
        assert read(pcm_path)['ok'] and read(native_path)['ok'] and read(delta_path)['ok']
        assert read('Game/Saved/choice-route-coverage.json')['status'] == 'PASS'
        assert read('Game/Saved/wrong-choice-full-regression.json')['ok']
        result = read('Game/build-result.json')
        build = Path(result['executable']).parent.name
        assert build == read(delta_path)['build'] == Path(read(native_path)['executable']).parent.name
        report['status'] = 'authored-choice-edge-and-focused-native-qa-complete'
        report['lastPackagedBuild'] = build
        report['audio'].update({'status': 'PASS-package-focused-offline-and-native',
                                'finalPCM': pcm_path, 'finalNative': native_path, 'packageDelta': delta_path,
                                'finalBuild': build, 'actualFocusedCuePeak': max(r['peak'] for r in read(pcm_path)['rows']),
                                'predictedWholeBankSingleCuePeak': read(delta_path)['maximumPredictedSingleCuePeak']})
        report['audio']['sourceSHA256'] = hashlib.sha256((ROOT / report['audio']['source']).read_bytes()).hexdigest()
        audit['frozenProductionSHA256'][report['audio']['source']] = report['audio']['sourceSHA256']
        audit['productionSourceFilesChangedScope'] = 'Historical initial five repairs; latest audio followup changes one generator only, no gameplay CPP or story/UI delta.'
        audit['latestProductionDelta'] = {'source': ['Game/tools/create-project.mjs'], 'audioDescriptors': 229, 'gameCpp': 0, 'dataJSON': 0, 'uiJSON': 0}
        audit['retention'].update({'buildReceipt': 'Game/Saved/build-retention-20261031-230949-813.json',
                                   'closedCacheReceipt': 'Game/Saved/build-retention-20261031-231434-430.json'})
        pixel = report['alternateEndingNative']['pixelsReviewed']
        if pixel not in audit['nativeVisualReviewed']:
            audit['nativeVisualReviewed'].append(pixel)
        report['sourceOnlyChangesAfterBuild'] = 0
        report['qaHarnessRepairs'] = ['Legacy verify-flow no longer deletes proof; zero-beat title-only exit no longer passes. Its earlier no-op invocation is not campaign proof.']
        audit['repairs']['audioHeadroom'] = report['audio']
        audit['totalTrackedRepairFamilies'] = 9
        audit['lastPackagedBuild'] = build
        audit['executable'] = result['executable']
        audit['packageIdentity'] = 'Game/Saved/source-identity-' + build.rsplit('-', 1)[1] + '.json'
        audit['packageDelta'] = delta_path
        audit['passed']['audioHeadroomFinal'] = {'status': 'PASS', 'report': native_path, 'fixture': False, 'build': build}
        for name, value in [('allAuthoredChoiceEdges', report['routes']), ('allWrongCandidates', report['wrongCandidates']), ('alternateEndingB', report['alternateEndingNative'])]:
            audit['passed'][name] = {'status': 'PASS', **value}
    write(ROOT / 'docs/analysis/v3_rebuild/extended_qa_20261031.json', report)
    write(NATIVE / 'extended_qa_20261031.json', report)
    audit['extendedQA'] = report
    audit['status'] = report['status']
    audit['pending'] = [] if final else ['Audio headroom generated package and focused native/max-volume/mute validation']
    audit['sourceOnlyChangesAfterBuild'] = 0 if final else 1
    audit['remainingKnownFunctionalFailures'] = 0 if final else 1
    write(audit_path, audit)
    write(NATIVE / audit_path.name, audit)
    note = {'report': 'docs/analysis/v3_rebuild/extended_qa_20261031.json', 'status': report['status'],
            'newREARecords': 0, 'originalRuntimeObserved': False, 'fixed24x5BehaviorProgressChanged': False,
            'originalRetainedRecords': 2354, 'sharedIndexRecords': 2553,
            'fiveHourTrialCertificate': False, 'audioPending': not final,
            'lastPackagedBuild': audit['lastPackagedBuild']}
    index_path = ROOT / 'docs/spec/18_V3_분석/evidence_index.json'
    index = read(index_path)
    before = hashlib.sha256(json.dumps(index['records'], sort_keys=True).encode()).hexdigest()
    index.setdefault('implementation_reuse_notes', {})['extended_qa_20261031'] = note
    assert before == hashlib.sha256(json.dumps(index['records'], sort_keys=True).encode()).hexdigest()
    write(index_path, index)
    numbers_path = ROOT / 'docs/spec/18_V3_분석/numbers.json'
    numbers = read(numbers_path)
    numbers.setdefault('fangame_reference_comparison', {})['extended_qa_20261031'] = note
    write(numbers_path, numbers)
    print(json.dumps({'status': report['status'], 'newREARecords': 0, 'originalIndexRecordsUnchanged': True}))


if __name__ == '__main__':
    main()
