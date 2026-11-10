"""Scan installed ACB/AWB metadata using saved CPK/SPC inventories.

Does not export encoded audio, PCM, or audio keys. ACB table blobs are analysis
metadata and should be written outside the source repository.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

from audio import acb, awb, cue_waveforms, json_value
from catalog import read_child


def scan(inventory, output):
    inventory=Path(inventory);output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    report={'acb':[],'awb':[],'errors':[],'complete':False}
    listings=list(sorted(inventory.glob('*.spc.jsonl')))
    deeper=inventory/'nested-deeper.jsonl'
    if deeper.exists(): listings.append(deeper)
    def save(name,result):
        destination=output/name
        destination.write_text(json.dumps(result,ensure_ascii=False,indent=1,default=json_value),encoding='utf-8')
        return str(destination.resolve())
    for listing in listings:
        for line in listing.open(encoding='utf-8'):
            carrier=json.loads(line)
            for child in carrier.get('members',[]):
                if Path(child['name']).suffix.lower()!='.acb':continue
                source={'archive':carrier['archive'],
                        'ancestry':carrier.get('ancestry',[carrier.get('parent',{}).get('path')]),
                        'member':child['name'],'offset':child['offset']}
                try:
                    result=acb(read_child(carrier,child['index'],inventory))
                    result['cue_links']=cue_waveforms(result);result['source']=source
                    name=f"{Path(carrier['archive']).stem}__{len(report['acb']):03d}__{Path(child['name']).name}.json"
                    path=save(name,result)
                    report['acb'].append(dict(source=source,output=path,cues=len(result['cues']),
                        embedded_streams=sum(b['bank']['count'] for b in result['banks']),
                        unresolved_cues=sum(bool(c['unknown']) or not c['waveforms'] for c in result['cue_links'])))
                except (ValueError,OSError,KeyError,UnicodeError) as error:
                    report['errors'].append({'source':source,'error':str(error)})
    for inv_path in sorted(inventory.glob('partition*.json')):
        inv=json.loads(inv_path.read_text(encoding='utf-8'))
        if 'archive' not in inv or 'members' not in inv:continue
        with Path(inv['archive']).open('rb') as handle:
            for member in inv['members']:
                if Path(member['path']).suffix.lower()!='.awb':continue
                try:
                    if member['compression']!='none':
                        raise ValueError('streaming AWB scan requires uncompressed CPK member')
                    result=awb(handle,member['offset'],member['stored_size'])
                    result['source']={'archive':inv['archive'],'member':member['path'],'offset':member['offset']}
                    path=save(f"{inv_path.stem}__{Path(member['path']).name}.json",result)
                    report['awb'].append({'source':result['source'],'output':path,'count':result['count'],
                        'codecs':dict(Counter(r['codec']['format'] for r in result['records']))})
                except (ValueError,OSError,KeyError) as error:
                    report['errors'].append({'source':member['path'],'error':str(error)})
    report['complete']=not report['errors']
    save('summary.json',report)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inventory',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();result=scan(args.inventory,args.output)
    print(json.dumps({'acb':len(result['acb']),'awb':len(result['awb']),
                      'errors':len(result['errors']),'complete':result['complete']}))
    raise SystemExit(bool(result['errors']))
