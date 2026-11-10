"""Replace rejected explanatory plates with inspected physical clue illustrations."""
import hashlib
import json
import shutil
from pathlib import Path
from prepare_comic_revision_runtime import chunks

ROOT = Path(__file__).resolve().parents[1]
GEN = Path('C:/Users/kirby/.codex/generated_images/01a19fd4-cd3f-7123-91ea-3a9194054780')
OUT = ROOT / 'art/inspection_v4/physical_clues_20261104'
SPECS = [
    ('private_notebook', 'v4:3:knowledge:private-notebook', 'b97f6a29-d946-4cc2-86ce-07c465acedd3'),
    ('recent_conditions', 'v4:E5-03', 'd3eda848-8338-4734-9621-18e11865dd83'),
    ('third_statement', 'v4:E5-04', 'f6d5461d-0bd8-4abe-b86d-52c8e333b1eb'),
    ('ordinary_protected', 'v4:E5-05', 'd6ea6494-5bf5-4635-a14c-f78113a42806'),
    ('old_note', 'v4:E6-04', '3f39a7f9-04ec-48a7-bceb-120aac1270dc'),
    ('closed_dry_camera_bag', 'v4:3:knowledge:camera-preparation', 'bc12cd8e-86c7-400e-8117-c5d725a324c8'),
    ('rabbit_inner_tag', 'v4:E6-13', '939fc769-f450-4328-bb0e-93ea6cca5bdb'),
    ('archive_index', 'v4:3:knowledge:riku-index', '756b165e-6d3b-4b55-9065-3c7cb6e49aa7'),
    ('rescue_record_viewer', 'v4:3:knowledge:father-record', 'e4c04403-ab09-4bda-943a-03224fded812'),
    ('pipe_boundary', 'v4:4:knowledge:pipe-boundary', '8d5b0c61-c2e5-4e25-aa81-e7da062d9297'),
    ('arrival_register', 'v4:E6-03', 'a62f0252-044e-4fc4-92da-03e9fc9513a7'),
    ('current_record_page', 'v4:E6-14', '78a04c94-5fc1-4bb2-9c11-46120c89f6e5'),
    ('old_oath_copies', 'v4:E6-06', 'bf09ee53-f5bd-46bf-a38d-f4c4450c1186'),
    ('safety_records', 'v4:E6-10', '9072508f-0289-4e62-ad69-4a3c394aa6e2'),
    ('preserved_records', 'v4:E6-16', '133c19d9-d4aa-48e7-a6d5-2b6556e19172'),
]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def proof(file, line, quote):
    text = (ROOT / 'docs/design/rewrite_v4' / file).read_text(encoding='utf-8-sig')
    assert quote in text.splitlines()[line-1]
    return {'file': file, 'line': line, 'quote': quote, 'sha256': sha(text.encode())}

def main():
    OUT.mkdir(exist_ok=True)
    old_manifest = json.loads((ROOT / 'ui/v4/evidence_documents_20261104/manifest.json').read_text(encoding='utf8'))
    prior = {row['id']: row for row in old_manifest['rows']}
    vp = ROOT / 'tools/v4_evidence_illustration_views.json'
    sp = ROOT / 'tools/v4_evidence_art_semantic.json'
    views = json.loads(vp.read_text(encoding='utf8'))
    semantic = json.loads(sp.read_text(encoding='utf8'))
    vm = {row['id']: row for row in views['views']}
    evidence = {}
    for p in (ROOT / 'data/v4_story/chapters').glob('*.json'):
        evidence.update(json.loads(p.read_text(encoding='utf8')).get('evidenceCatalog', {}))
    receipts = []
    for name, ident, generated in SPECS:
        data = (GEN / ('exec-' + generated + '.png')).read_bytes()
        original = OUT / (name + '_original.png')
        shutil.copyfile(GEN / ('exec-' + generated + '.png'), original)
        runtime = b'\x89PNG\r\n\x1a\n' + b''.join(raw for kind, raw in chunks(data) if kind != b'caBX')
        assert [raw for kind, raw in chunks(data) if kind in (b'IHDR', b'IDAT')] == [raw for kind, raw in chunks(runtime) if kind in (b'IHDR', b'IDAT')]
        target = OUT / (name + '.png')
        target.write_bytes(runtime)
        if ident in prior:
            refs = prior[ident]['source']
        elif name == 'rabbit_inner_tag':
            refs = [proof('16a3_6장_지금_쓰는_문장_초고.md', 191, '래피는 귀를 뒤로 젖혀 봉제 안쪽 표지를 보인다.'), proof('16a3_6장_지금_쓰는_문장_초고.md', 201, '장기간 휴면 뒤 잔류 계통에서 깨어난 항목')]
        elif name == 'archive_index':
            refs = [proof('13b4_3장_아침에_쓴_기회_초고.md', 21, '다음 조각은 직원 동선 묶음에 들어가 있다.')]
        elif name == 'rescue_record_viewer':
            refs = [proof('13b4_3장_아침에_쓴_기회_초고.md', 53, '소방복의 남자가 다른 통로로 이동하는 모습'), proof('13b4_3장_아침에_쓴_기회_초고.md', 55, '소라가 화면 밖으로 사라진 뒤에도 아버지는 살아 움직인다.'), proof('13b4_3장_아침에_쓴_기회_초고.md', 61, '그 남자의 마지막 순간을 보여 주지는 않는다.')]
        elif name == 'pipe_boundary':
            refs = [proof('14b2_4장_입구와_햇빛_초고.md', 143, '도면에 있는 연결을 현재 보이는 부속과 맞춘다.'), proof('14b2_4장_입구와_햇빛_초고.md', 149, '표시된 망/배관 결합과 외벽')]
        elif name == 'arrival_register':
            refs = [proof('16a_6장_내려가는_다섯_초고.md', 267, '19:55~20:05 사이 열네 명'), proof('16a_6장_내려가는_다섯_초고.md', 279, '코토20:50.')]
        elif name == 'current_record_page':
            refs = [proof('16a5_6장_발에서_떨어진_그림자_초고.md', 21, '사츠키의 그림자는 그녀의 발에 붙어 있다.'), proof('16a5_6장_발에서_떨어진_그림자_초고.md', 103, '나나는 지금 스스로 숨을 쉬고 있다.')]
        elif name == 'old_oath_copies':
            refs = [proof('16b1_6장_전실과_통로의_수사_초고.md', n, quote) for n, quote in [(416, '레이는 당시 점검 보고의 허위/은폐 과정'), (417, '코토는 레이가 위험 경고 문서를 보고도'), (418, '레이의 위반 대가는 오른팔의 강한 통증과 움직임 제약,코토는 손목의 고통')]]
        elif name == 'safety_records':
            refs = [proof('16b1_6장_전실과_통로의_수사_초고.md', n, quote) for n, quote in [(369, '살의 입력 제한 확인:미완료.해당 항목 인계 유보.'), (370, '동일 안전 항목을 완료로 수정.'), (371, '살의 입력 제한 확인:정상.'), (372, '동일 안전 항목:미해결.')]]
            refs.append(proof('16b2_6장_손을_놓은_뒤의_수사_초고.md', 127, '현재처럼 제한/완충이 유지됐던 상태가 아니라'))
        elif name == 'preserved_records':
            refs = [proof('16b2_6장_손을_놓은_뒤의_수사_초고.md', 417, '미오는 원문과 자기 필기를 나누어 둔다.'), proof('16b2_6장_손을_놓은_뒤의_수사_초고.md', 423, '같은 미래나 같은 공개에 합의하지 않았다.')]
        elif name == 'closed_dry_camera_bag':
            refs = [proof('13a12_3장_끝났다는_말_초고.md', 16, '카메라는 덮개가 닫힌 가방 안에 있다.')]
        else:
            raise ValueError('Unreviewed physical clue source: ' + name)
        if name == 'ordinary_protected':
            refs += [proof('15a10_5장_없는_오후를_바라는_말_초고.md', 297, '코토/차/아카리'), proof('15a11_5장_남아있는_두장_초고.md', 17, '사츠키/빈잔'), proof('15a11_5장_남아있는_두장_초고.md', 19, '「회수」칸은 비어 있다.')]
        if name == 'old_note':
            refs += [proof('16b1_6장_전실과_통로의_수사_초고.md', n, quote) for n, quote in [(349, '하루카가 서류를 들고 코토한테 간다고 했다.'), (351, '둘이 통로 쪽으로 갔다.')]]
        for ref in refs:
            assert proof(ref['file'], ref['line'], ref['quote']) == ref
        viewid = 'physical_clue_' + name
        vm[viewid] = {'id': viewid, 'file': target.relative_to(ROOT).as_posix(), 'reviewed': True, 'scope': 'Individually source-reviewed physical belonging illustration. Object construction/desk placement is illustrative; no newly discovered photograph, exact measurements, extra signature, private text, trace or historical action.'}
        ev = evidence[ident]
        digest = sha((ev['name'] + '\n' + ev['text']).encode())
        old = next((r for r in semantic['bindings'] if r['evidenceId'] == ident), None)
        if old:
            assert old['evidenceTextSha256'] == digest
            assert all(v['id'].startswith(('reading_aid_', 'physical_clue_')) for v in old['views'])
        binding = {'evidenceId': ident, 'evidenceTextSha256': digest, 'views': [{'id': viewid, 'sha256': sha(runtime)}], 'sourceStatements': refs, 'reviewBasis': 'User rejected flat paper exposition. Replaced with an individually inspected physical object, actual sparse source content and relevant material/state contrast. Full evidence details remain the existing acquired text; not a forged full original.', 'pixelReview': 'Generated original directly viewed 2026-11-04. Notebook page/loose memo distinction, intact empty recovery field, exact old three lines, one third-statement sheet, closed dry bag checked. Native acceptance pending.', 'grantPolicy': 'No new acquisition, stains, erasure, tear, blood, signature identity, date, conditions or answers.'}
        if old:
            old.clear()
            old.update(binding)
        else:
            semantic['bindings'].append(binding)
        receipts.append({'id': ident, 'original': original.relative_to(ROOT).as_posix(), 'originalSha256': sha(data), 'runtime': target.relative_to(ROOT).as_posix(), 'runtimeSha256': sha(runtime), 'source': refs, 'compressedPixelsPreserved': True, 'directViewed': True, 'nativeAccepted': False})
    # Reuse the same physical four-record comparison for its original acquisition.
    ident = 'v4:E6-05'
    safety = next(b for b in semantic['bindings'] if b['evidenceId'] == 'v4:E6-10')
    old = next(b for b in semantic['bindings'] if b['evidenceId'] == ident)
    ev = evidence[ident]
    assert old['evidenceTextSha256'] == sha((ev['name'] + '\n' + ev['text']).encode())
    assert all(v['id'] in ('case6_document_safety', 'physical_clue_safety_records') for v in old['views'])
    old['views'] = [v.copy() for v in safety['views']]
    old['sourceStatements'] = safety['sourceStatements'][:4]
    old['reviewBasis'] = 'The four previously acquired old safety states, now shown as inspected physical record copies. No later buffer-condition information is added to the old acquisition.'
    old['pixelReview'] = 'Physical original individually viewed; native selection pending. Old flat four-box comparison is no longer the evidence-card picture.'
    # Differentiate the actual speaker's admission from the physical arrival log.
    ident = 'v4:E6-11'
    arrival = next(b for b in semantic['bindings'] if b['evidenceId'] == 'v4:E6-03')
    portrait = vm['testimony_portrait_nana']
    ev = evidence[ident]
    refs = [proof('16a_6장_내려가는_다섯_초고.md', 239, '전실에서 차례로 아이들의 손을 잡았다고 말한다.'), proof('16a5_6장_발에서_떨어진_그림자_초고.md', 179, '손을 잡으면 조용해졌어요.')]
    binding = {'evidenceId': ident, 'evidenceTextSha256': sha((ev['name'] + '\n' + ev['text']).encode()), 'views': [{'id': 'testimony_portrait_nana', 'sha256': sha((ROOT / portrait['file']).read_bytes())}] + arrival['views'], 'sourceStatements': refs, 'reviewBasis': 'Nana is the actual source of her admission; separate second page shows only the acquired arrival log. The register does not photograph or independently prove memory intervention.', 'pixelReview': 'Approved portrait and arrival image individually viewed; new two-page native selection pending.', 'grantPolicy': 'No new acquisition, memory recovery, consent or third-person reenactment.'}
    old = next((b for b in semantic['bindings'] if b['evidenceId'] == ident), None)
    if old:
        assert old == binding
    else:
        semantic['bindings'].append(binding)
    views['views'] = list(vm.values())
    vp.write_text(json.dumps(views, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    sp.write_text(json.dumps(semantic, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    (OUT / 'manifest.json').write_text(json.dumps({'rows': receipts, 'supersedes': 'ui/v4/evidence_documents_20261104', 'userCorrection': 'Physical clues rather than flat explanatory paper', 'tool': 'builtin image_gen', 'runtimeAdapter': 'caBX-only removal; original pixels preserved'}, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'physicalClues': len(receipts), 'rejectedFlatPlatesReplaced': 5, 'newCameraContext': 1, 'sourceFactsChanged': False}))

if __name__ == '__main__':
    main()
