"""Register directly reviewed native comic candidates without changing task facts."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / 'art/v4_production/comic_revisions_20261104'
GENERATED = Path('C:/Users/kirby/.codex/generated_images/01a19fd4-cd3f-7123-91ea-3a9194054780')
CANDIDATES = {
    (6,3): ['e9ccb42b-98bd-42a2-921a-524aa4225155', '94dfe280-7e21-49fc-981f-9849be86fc95', 'c83262ec-e94f-4c5d-8e1a-6896a85ed7ef'],
    (6,7): ['c8c41a42-8bf3-4f54-a02b-fb3ed57db0f0', 'a4f5b063-8785-401e-98d1-a9a59863a947', '814ced6b-7c19-40d3-b4f0-fe159287e15a'],
    (6,8): ['308a4060-6c25-43e6-b8f2-88bf9a341dba', 'fd383703-ddfa-4844-9391-e04b93aa94e5', '36a7fc98-dfb0-41df-a52d-47b87c60c1e6'],
    (5,6): ['d9464c0d-2574-41ba-bf17-6f73d395ca24', 'ef746f76-3b73-4e78-a025-579782e56158', 'd00942e7-5aaf-468f-934b-a555734dc1a5'],
}
BASES = {
    3: 'Three authored hypotheses: missing second contact; distinct partial observations and rail reach; false omniscient witness. Repaired B has continuous worn rail, no invented broken-off gap and no visible attacker identity.',
    7: 'Three authored hypotheses: false original co-arrival; false memory-created person and room; actual separate arrival then creation. Cameras removed from B/C. Closeups do not visually enumerate arrival counts.',
    8: 'Three authored hypotheses: distinct present operator and past shove; false oath puppetry metaphor; false automatic absolution. No support decision is executed, no technical shutdown is shown. Memory insets are reconstruction rather than newly acquired photographs.',
    6: 'Chapter 5: the whole THIRD statement sheet is directly shown, then the new oath line ends, then the later sample retrieval. Not three sheets; not all old oaths ended. B automatic release and C prior ownership/input are explicitly false hypotheses. No added readable document, substance identity or dosage.',
}

def main():
    registry = BANK / 'selection.json'
    selected = json.loads(registry.read_text(encoding='utf-8'))
    tasks = json.loads((ROOT/'data/v4_story/native_tasks.json').read_text(encoding='utf-8-sig'))['tasks']
    added = []
    for (chapter,number), images in CANDIDATES.items():
        ident=f'T{chapter}-MG-01'
        task=tasks[ident]
        source=(ROOT/'docs/design/rewrite_v4'/task['source']['file']).read_text(encoding='utf-8-sig')
        source_sha=hashlib.sha256(source.encode()).hexdigest()
        assert source_sha==task['source']['fileSha256']
        source_lines=source.splitlines()
        slot = task['stage']['slots'][number-1]
        for key, generated in zip('ABC', images):
            option = next(o for o in slot['options'] if str(o['id']).endswith(key))
            expected = f"|{number}{key}|{option['label']}|" + ('정답' if option['id']==slot['answer'] else '오답') + '|'
            assert source_lines[option['source']['line']-1] == expected
            assert option['source']['fileSha256'] == source_sha
            original = GENERATED/f'exec-{generated}.png'
            destination = BANK/f'C{chapter}_S{number:02d}_{key}.png'
            existing=next((r for r in selected['rows'] if r['taskId']==ident and r['slotId']==slot['id'] and r['optionId']==option['id']),None)
            if existing:
                assert existing['sourceSha256']==source_sha
                assert existing['captionSha256']==hashlib.sha256(option['label'].encode()).hexdigest()
                assert hashlib.sha256(original.read_bytes()).hexdigest()==existing.get('originalSha256',existing['sha256'])
                continue
            assert not destination.exists()
            shutil.copyfile(original, destination)
            selected['rows'].append({
                'taskId':ident, 'slotId':slot['id'], 'optionId':option['id'],
                'captionSha256':hashlib.sha256(option['label'].encode()).hexdigest(), 'sourceSha256':source_sha,
                'image':destination.relative_to(ROOT).as_posix(), 'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
                'review':{'directViewed':True,'basis':BASES[number],'captionRequired':True,'sameIllustrationStyleAsOtherTwoOptions':True,
                          'counterfactualAuthoredOption':option['id']!=slot['answer'],'notHistoricalEvidence':True,
                          'limits':'Exact source caption and existing response own the meaning; no new readable document, named attacker identification or additional acquired evidence.'},
                'nativeVisualAcceptance':False,
            })
            added.append(f'C{chapter}_S{number:02d}_{key}')
    registry.write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'added':added,'totalSelected':len(selected['rows']),'storyOrAnswersChanged':False}))

if __name__ == '__main__':
    main()
