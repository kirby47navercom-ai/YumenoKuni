"""Source/release-boundary checks for Pad records; no native/game execution."""
import json
from copy import deepcopy
from pathlib import Path
import shutil
import tempfile
from build_v4_story import Source,SAY,clean
from v4_public_records import ROOT,RULES,REVIEWED_HASHES,build_records
from verify_v4_story import walk


def main():
    result=build_records();records=result['records'];checks=0
    assert not result['startingInventory'] and len(records)==29
    all_nodes={}
    for p in (ROOT/'data/v4_story/chapters').glob('*.json'):
        all_nodes.update(json.loads(p.read_text(encoding='utf-8'))['nodes'])
    for key,file,line,row_lines,title,category,reveal in RULES:
        source=Source(ROOT/'docs/design/rewrite_v4'/file)
        ident='v4:public-record:'+key;record=records[ident]
        event=record['acquireEventId']
        assert event in all_nodes and all_nodes[event]['source']['file']==file
        assert all_nodes[event]['source']['line']==line
        assert result['eventById'][event]==[ident]
        boundary=next(r for r in result['sourceRanges'] if r['eventId']==event)
        assert boundary['firstLine']==boundary['lastLine']==line and boundary['exactEventOnly']
        assert not record['private'] and not record['grantsEvidence'] and not record['grantsAbility'] and not record['changesStoryFlags']
        for row,n in zip(record['rows'],row_lines):
            raw=source.lines[n-1].strip();match=SAY.fullmatch(raw)
            expected=clean(match[2]) if match else clean(raw[2:]) if raw.startswith('- ') else raw[1:-1]
            assert row==expected and record['sourceRefs'][list(row_lines).index(n)]['line']==n
            assert n<=line or (key=='6-five-votes' and n in range(33,38))
        assert record['showOnAcquire']==reveal
        checks+=1+len(row_lines)
    assert sum(bool(r['showOnAcquire']) for r in records.values())==1
    final=records['v4:public-record:6-five-votes']
    assert final['showOnAcquire'] and len(final['rows'])==5
    assert '세 표 이상' in final['rows'][2] and '재논의' in final['rows'][2]
    assert '모든 쟁점' in final['rows'][4] and '새 살인' in final['rows'][4]
    assert '중간 사실 확인' in final['rows'][1] and '새 처형' in final['rows'][3]
    # Catalog availability must never be confused with owning a later record.
    prologue=json.loads((ROOT/'data/v4_story/chapters/P.json').read_text(encoding='utf-8'))
    selected={n['id']:n['options'][0]['id'] for n in prologue['nodes'].values() if n['type']=='menu'}
    trace,flags=walk(prologue,selected);owned={}
    for event in trace:
        for ident in result['eventById'].get(event['id'],[]):owned[ident]=deepcopy(records[ident])
    assert set(owned)=={'v4:public-record:P-graduation','v4:public-record:P-no-deadline','v4:public-record:P-disclosure'}
    assert 'v4:public-record:6-five-votes' not in owned
    assert all('살의 조건' not in row for record in owned.values() for row in record['rows'])
    # The original private page remains governed by actual document capture;
    # neither the visible rows nor that private event are relabelled public.
    assert 'v4:10:P-06a:document' not in result['eventById']
    assert all('원장' not in r['sourceRefs'][0]['file'] and '자유시간' not in r['sourceRefs'][0]['file'] for r in records.values())
    # Reject changed source rather than rebinding an old line number silently.
    with tempfile.TemporaryDirectory(prefix='v4-public-records-') as folder:
        target=Path(folder)/'docs/design/rewrite_v4';target.mkdir(parents=True)
        for file in REVIEWED_HASHES:shutil.copyfile(ROOT/'docs/design/rewrite_v4'/file,target/file)
        changed=target/next(iter(REVIEWED_HASHES));changed.write_text(changed.read_text(encoding='utf-8')+'\nChanged for guard test.\n',encoding='utf-8')
        try:build_records(folder)
        except ValueError as error:assert 're-read' in str(error)
        else:raise AssertionError('Changed public record source was silently accepted')
    print(json.dumps({'passed':True,'records':len(records),'exactEvents':len(result['eventById']),'checks':checks+9,'prologueAcquired':len(owned),'futurePreload':False,'privatePagePublished':False,'sourceMutationRejected':True,'runtimeExecuted':False}))


if __name__=='__main__':main()
