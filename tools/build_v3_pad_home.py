"""Compose supplied menu pixels at their shipped SFL positions.

Reads the already provided Korean UI cache only. No Steam reads, new archive
extraction, target execution, source-pixel edits or invented title typography.
"""
from pathlib import Path
import base64
import copy
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
CACHE=Path('C:/Users/kirby/Downloads/v3_re/ui_authorized_20261029')
NAMES={'map':'map','bullet':'kotodama','gift':'present','card':'tsusinbo','rules':'kousoku','option':'system'}
LABELS=[('fl_map_kotodama','fl_kotodama_wait'),('fl_kotodama_present','fl_present_wait'),('fl_present_tsusinbo','fl_tsusinbo_wait'),('fl_tsusinbo_rule','fl_rule_wait'),('fl_rule_system','fl_system_wait')]

def build():
    inv=json.loads((CACHE/'manifest.json').read_text(encoding='utf8'))
    sfl=json.loads((CACHE/'pad-korean-menu-sfl.json').read_text(encoding='utf8'))
    sequences=next(t for t in sfl['tables'] if t['id']==6)['entries'][0]['sequences']
    labels={s['name']:i for i,s in enumerate(sequences) if s['name']}
    display={}
    def apply(start,end):
        for seq in sequences[start:end+1]:
            for op in seq['operations']:
                d=op.get('decoded',{})
                if d.get('name')=='RemoveObject2':display.pop(d['depth'],None)
                elif d.get('name')=='PlaceObject2':
                    if not d['move']:display[d['depth']]={}
                    display.setdefault(d['depth'],{}).update(d)
    apply(0,labels['fl_map_wait'])
    states=[copy.deepcopy(display)]
    for first,last in LABELS:
        apply(labels[first],labels[last]);states.append(copy.deepcopy(display))
    provenance=[]
    def image(container,resource):
        rows=[r for r in inv['textures'] if r['container'].endswith('/'+container) and r['resource']==resource]
        if len(rows)!=1:raise ValueError((container,resource,len(rows)))
        row=rows[0];raw=Path(row['path']).read_bytes()
        if row not in provenance:provenance.append(row)
        return 'data:image/png;base64,'+base64.b64encode(raw).decode('ascii')
    floor=image('techou_type_000_JP.spc','bg_000_DXT1.png')
    folder=ROOT/'ui/v3_authorized/pad_home';folder.mkdir(exist_ok=True)
    layouts={};files=[]
    for index,(key,original) in enumerate(NAMES.items()):
        state={r.get('instance_name'):r for r in states[index].values() if r.get('instance_name')}
        header_name='i_rule' if key=='rules' else 'i_'+original
        title_name='p_title_tx_rule' if key=='rules' else 'p_title_tx_'+original
        header=state[header_name]['matrix'];title=state[title_name]['matrix'];bubble=state['p_setumei']['matrix']
        if any(abs(m.get('rotate_skew0',0))+abs(m.get('rotate_skew1',0))>0.001 for m in [header,title,bubble]):raise ValueError('Unexpected non-affine menu state')
        if abs(header['scale_x']-1)>.001 or abs(title['scale_x']-1)>.001:raise ValueError('Selected menu did not settle')
        graphic=image('techou_type_000_JP.spc','icon_'+original+'_DXT1.png')
        label=image('techou_type_000_JP.spc','title_tx_'+('rule' if key=='rules' else original)+'_JP.png')
        # Keep original pixels opaque here. Exact original material blending is
        # not inferred from a DXT1 filename. No guessed alpha/key conversion.
        svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="3840" height="2160" viewBox="0 0 1920 1080">'
             f'<image href="{floor}" width="1920" height="1088" preserveAspectRatio="none"/>'
             f'<image href="{graphic}" x="{header["translate_x"]}" y="{header["translate_y"]}" width="1920" height="660" preserveAspectRatio="none"/>'
             f'<image href="{label}" x="{title["translate_x"]}" y="{title["translate_y"]}" width="799" height="128" preserveAspectRatio="none"/></svg>')
        dest=folder/(key+'.svg');dest.write_text(svg,encoding='utf8');files.append({'file':dest.relative_to(ROOT).as_posix(),'runtime':'Assets/Art/ui/v3/pad_home/'+dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
        layouts[key]={'header':header,'title':title,'bubble':bubble,'bubbleLocalBounds':[-58,645,0,256],'descriptionFontHeightDesign':45,'labelResource':'title_tx_'+('rule' if key=='rules' else original)+'_JP.png'}
    # The actual supplied icon pixels remain intact; the observed circular
    # button silhouette clips their square carrier rather than showing a tile.
    for key,original in NAMES.items():
        graphic=image('techou_type_027_JP.spc','icon_'+('rule' if key=='rules' else original)+'_DXT1.png')
        svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="560" height="560" viewBox="0 0 140 140"><defs><clipPath id="button"><circle cx="70" cy="70" r="61"/></clipPath></defs><circle cx="70" cy="70" r="65" fill="#08080d" stroke="#ffffff" stroke-width="3"/>'
             f'<image href="{graphic}" x="9" y="9" width="122" height="122" preserveAspectRatio="xMidYMid meet" clip-path="url(#button)"/></svg>')
        dest=folder/('icon_'+key+'.svg');dest.write_text(svg,encoding='utf8');files.append({'file':dest.relative_to(ROOT).as_posix(),'runtime':'Assets/Art/ui/v3/pad_home/'+dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
    result={'originalInstallationRead':False,'sourcePixelsChanged':False,'targetExecuted':False,'runtimeVerified':False,'sflSha256':sfl['sha256'],'buttonLimitation':'The shared techou_top button raster is absent from the supplied bank. type027 icon pixels remain a provisional supplied-art substitution, not the default type000 common buttons. Do not accept as exact V3 button artwork. Base positions/selection lift follow the confirmed common SFL, without scale enlargement.','materialBlend':'unverified; supplied carrier kept opaque, never represented as exact original additive compositing','provenance':provenance,'layouts':layouts,'files':files}
    (folder/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return result

if __name__=='__main__':
    result=build();print(json.dumps({'files':len(result['files']),'sourceTextures':len(result['provenance']),'originalInstallationRead':False}))
