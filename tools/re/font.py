"""Read V3 SRD-backed STX SpFt font metrics; never export font images.

Primary layout source read: Harmony-Tools FontBlock.cs/Utils.cs at
82ff93c1f181f30e403440be5b91303db32d72f2. Actual bitmap/index cardinality
and every glyph range are checked, including Unicode values above0xD800.
"""
import argparse
import json
from pathlib import Path
import struct

from srd import parse_srd, walk


def spft(data):
    if len(data)<44 or data[:4]!=b'SpFt':
        raise ValueError('SpFt header missing')
    version,bits,name_length,name_at,count,box_at,flags_at,index_at,scale,pointers_at=struct.unpack_from('<10I',data,4)
    def bounded(start,size):
        if start<44 or size<0 or start+size>len(data):
            raise ValueError('SpFt range outside table')
        return data[start:start+size]
    flags=bounded(flags_at,(bits+7)//8)
    boxes=bounded(box_at,count*8)
    name=bounded(name_at,(name_length+1)*2)
    if name[-2:]!=b'\0\0':raise ValueError('SpFt font name terminator')
    glyphs=[];group_counts={}
    for codepoint in range(bits):
        if not flags[codepoint//8]>>(codepoint%8)&1:continue
        group=codepoint//32
        index=struct.unpack('<I',bounded(index_at+group*4,4))[0]+group_counts.get(group,0)
        group_counts[group]=group_counts.get(group,0)+1
        if index>=count:raise ValueError('SpFt glyph index out of range')
        a,b,c,width,height,k0,k1,k2=struct.unpack_from('<5B3b',boxes,index*8)
        glyphs.append({'codepoint':codepoint,'index':index,'record_offset':box_at+index*8,
            'atlas_x':a+((b&15)<<8),'atlas_y':(b>>4)+(c<<4),
            'width':width,'height':height,'kerning_raw':[k0,k1,k2]})
    if len(glyphs)!=count or len({g['index'] for g in glyphs})!=count:
        raise ValueError('SpFt bitmap/index/glyph count disagreement')
    pointers=struct.unpack('<4I',bounded(pointers_at,16))
    if any(p!=name_at for p in pointers):raise ValueError('SpFt font name pointer mismatch')
    return {'format':'SpFt','version':version,'font_name':name[:-2].decode('utf-16le'),
        'glyph_count':count,'bit_count':bits,'scale_flag_raw':scale,
        'bitmap_offset':flags_at,'index_offset':index_at,'glyph_offset':box_at,
        'name_offset':name_at,'glyphs':glyphs,
        'limitations':['Metrics describe an atlas; final font scaling, outline and baseline need native consumers.']}


def parse(data):
    resource=parse_srd(data);fonts=[]
    for block in walk(resource['blocks']):
        if block['type']!='$TXR':continue
        atlas=block['decoded']
        for child in block['children']:
            if child['type']!='$RSI':continue
            for local in child['decoded']['local']:
                if local['name']!='font_table':continue
                start=local['offset'];end=start+local['length']
                result=spft(data[start:end]);result['table_file_offset']=start
                result['atlas']={k:atlas[k] for k in ['width','height','format','format_id','swizzle']}
                for glyph in result['glyphs']:
                    if glyph['atlas_x']+glyph['width']>atlas['width'] or glyph['atlas_y']+glyph['height']>atlas['height']:
                        raise ValueError('SpFt glyph rectangle outside atlas')
                fonts.append(result)
    if not fonts:raise ValueError('SRD contains no font_table resource')
    return {'format':'V3_FONT_STX','sha256':resource['sha256'],'size':len(data),'fonts':fonts}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();result=parse(args.source.read_bytes())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=1),encoding='utf-8')
    print(json.dumps({'fonts':len(result['fonts']),'glyphs':sum(f['glyph_count'] for f in result['fonts'])}))
