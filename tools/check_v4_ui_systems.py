"""Validate native 4x vector exports, exact PNG/WebP pixels and declared text bounds."""
from pathlib import Path
import json, hashlib, xml.etree.ElementTree as ET,os
from PIL import Image

root=Path(__file__).resolve().parents[1];folder=root/os.environ.get('V4_UI_CHECK','ui/v4/systems_hd')
manifest=json.loads((folder/'manifest.json').read_text(encoding='utf8'))
seen=set();results=[]
for a in manifest['assets']:
    assert a['id'] not in seen;seen.add(a['id'])
    w,h=a['logical_size'];expected=(w*4,h*4)
    svg=root/a['source'];xml=ET.fromstring(svg.read_text(encoding='utf8'))
    assert xml.attrib['viewBox']==f'0 0 {w} {h}'
    assert (int(xml.attrib['width']),int(xml.attrib['height']))==expected
    assert not any(el.tag.endswith('text') for el in xml.iter()),a['id']
    png=folder/(a['id']+'.png');webp=root/a['file']
    with Image.open(png) as f:im=f.convert('RGBA')
    with Image.open(webp) as f:other=f.convert('RGBA')
    assert im.size==other.size==expected
    assert im.tobytes()==other.tobytes(),a['id']
    assert im.getchannel('A').getextrema()==(0,255)
    if a['text_rect']:
        x,y,tw,th=a['text_rect'];assert 0<=x<x+tw<=w and 0<=y<y+th<=h
    results.append({'id':a['id'],'native_scale':4,'pixel_equality':True,'alpha':'PASS','svg_sha256':hashlib.sha256(svg.read_bytes()).hexdigest(),'runtime_integrated':False})
(folder/'qa.json').write_text(json.dumps({'status':'PASS','count':len(results),'checks':results,'visual_review':'contact sheet and populated save composition inspected separately; no runtime claim'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('PASS',len(results),'native 4x components, exact RGBA exports, SVG and text bounds')
