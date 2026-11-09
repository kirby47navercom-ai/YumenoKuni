"""Decode the user-authorized, already-provided Korean UI bank, never game executables."""
from pathlib import Path
import argparse,hashlib,json,sys

sys.path.insert(0,str(Path(__file__).resolve().parent/'re'))
import spc,srd

def sha(b):return hashlib.sha256(b).hexdigest()

def run(source:Path,output:Path):
    source=source.resolve();output=output.resolve()
    if not source.is_dir():raise ValueError('Provided UI bank missing')
    if source==output or source in output.parents:raise ValueError('Keep decoded results outside the source bank')
    output.mkdir(parents=True,exist_ok=True)
    report={'authorization':'User 2026-10-29 explicitly permits supplied V3/Korean UI reuse and adaptation.',
            'source_bank':str(source),'original_installation_read':False,'executable_launched':False,
            'containers':[],'textures':[],'errors':[]}
    for f in sorted(source.rglob('*.spc')):
        raw=f.read_bytes();digest=sha(raw);rel=f.relative_to(source).as_posix()
        row={'path':rel,'sha256':digest,'textures':0};report['containers'].append(row)
        cache=output/digest[:16];cache.mkdir(exist_ok=True)
        try:
            members={e['name']:spc.payload(raw,e) for e in spc.entries(raw)}
            for name,data in members.items():
                if not name.lower().endswith('.srd'):continue
                stem=name.rsplit('.',1)[0]
                companions={ext:members[stem+'.'+ext] for ext in ('srdi','srdv') if stem+'.'+ext in members}
                parsed=srd.parse_srd(data,companions)
                for block in srd.walk(parsed['blocks']):
                    if block['type']!='$TXR' or 'decoded' not in block:continue
                    rsi=next((c.get('decoded') for c in block['children'] if c['type']=='$RSI'),None)
                    if not rsi:continue
                    label=rsi['strings'][0] if rsi['strings'] else f'tex_{block["offset"]:x}'
                    try:
                        payload=srd.external_bytes(srd.texture_resource(block['decoded'],rsi),companions)
                        im=srd.texture_image(block['decoded'],payload)
                        pixel_sha=sha(im.tobytes());dest=cache/(pixel_sha[:20]+'.png')
                        if not dest.exists():im.save(dest)
                        report['textures'].append({'container':rel,'container_sha256':digest,'member':name,
                            'resource':label,'block_offset':block['offset'],'size':list(im.size),
                            'pixel_sha256':pixel_sha,'path':str(dest),'reviewed':False,'runtime_selected':False})
                        row['textures']+=1
                    except (ValueError,KeyError,OSError) as err:
                        report['errors'].append({'container':rel,'resource':label,'error':str(err)})
        except (ValueError,KeyError,OSError) as err:report['errors'].append({'container':rel,'error':str(err)})
    (output/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'containers':len(report['containers']),'textures':len(report['textures']),
        'errors':len(report['errors']),'manifest':str(output/'manifest.json')},ensure_ascii=False))
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path('C:/Users/kirby/Downloads/v3_re/ui_import_20261029/ui-containers'))
    parser.add_argument('--output',type=Path,default=Path('C:/Users/kirby/Downloads/v3_re/ui_authorized_20261029'))
    a=parser.parse_args();run(a.source,a.output)
