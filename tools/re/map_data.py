"""V3 stage, escape, map-state, effect and climax DAT structural readers.

Stage chunk layout is independently inferred and bounds validated across all
105 installed RpgStage/SuccessStage carriers. Escape record widths and map-jump
conditions are corroborated by native 0x140148e00 and 0x140478c90. Runtime
meaning of stage property/object fields remains explicit unknown. Native-proven
fixed state rows and climax groups retain raw lanes; animation tail stays partial.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct


def _read(data, fmt, at):
    if at < 0 or at+struct.calcsize('<'+fmt)>len(data):
        raise ValueError(f'binary DAT bounds at {at:#x}')
    return struct.unpack_from('<'+fmt,data,at)


def _sized_records(data,start,end,count):
    cursor=start;records=[]
    for _ in range(count):
        size,=_read(data,'I',cursor)
        if size<4 or cursor+size>end:raise ValueError('invalid sized stage record')
        raw=data[cursor:cursor+size]
        records.append(dict(offset=cursor,size=size,raw_hex=raw.hex(),
                            u16=list(_read(raw,'H'*(size//2),0))))
        cursor+=size
    if cursor!=end:raise ValueError('unconsumed stage record bytes')
    return records


def parse_stage(data):
    size,start,unknown8,sets,layers,objects,width,height,tilew,tileh=_read(data,'II8H',0)
    if size!=len(data) or start!=24 or unknown8 not in (9,11):
        raise ValueError('unsupported stage header')
    if max(sets,layers,objects)>256 or not width or not height:
        raise ValueError('invalid stage counts')
    at=start;tilesets=[];layer_data=[];object_groups=[]
    for _ in range(sets):
        length,offset,count,index,first_gid,count2,tw,th,imagew,imageh=_read(data,'II8H',at)
        end=at+length
        if end>len(data) or offset<26 or offset>length:raise ValueError('invalid tileset chunk')
        name_end=data.find(b'\0',at+26,at+offset)
        if name_end<0:raise ValueError('unterminated tileset texture path')
        name=data[at+26:name_end].decode('cp932')
        records=_sized_records(data,at+offset,end,count)
        tilesets.append(dict(offset=at,length=length,records_offset=at+offset,
                             tile_count=count,index=index,first_gid=first_gid,
                             repeated_count=count2,tile_width=tw,tile_height=th,
                             image_width=imagew,image_height=imageh,texture_path=name,
                             unknown_u16_24=_read(data,'H',at+24)[0],records=records))
        at=end
    for _ in range(layers):
        length,offset,unknown,index,w,h=_read(data,'II4H',at)
        end=at+length;grid_end=at+16+w*h*2
        if end>len(data) or grid_end>end:raise ValueError('invalid stage tile layer')
        values=list(_read(data,'H'*(w*h),at+16))
        layer_data.append(dict(offset=at,length=length,secondary_offset=at+offset,
                               unknown_u16_8=unknown,index=index,width=w,height=h,
                               tile_indices=values,remaining_hex=data[grid_end:end].hex()))
        at=end
    for _ in range(objects):
        length,offset,count,count2=_read(data,'IIII',at);end=at+length
        if end>len(data) or offset<16 or offset>length:raise ValueError('invalid stage object group')
        records=_sized_records(data,at+offset,end,count)
        object_groups.append(dict(offset=at,length=length,repeated_count=count2,records=records))
        at=end
    if at!=len(data):raise ValueError('unconsumed stage bytes')
    return dict(format='V3_STAGE_CHUNKS',header=dict(size=size,offset=start,unknown_u16_8=unknown8,
                tileset_count=sets,layer_count=layers,object_group_count=objects,
                width=width,height=height,tile_width=tilew,tile_height=tileh),
                tilesets=tilesets,layers=layer_data,object_groups=object_groups,
                native=dict(procedure='0x140241520',evidence_id='ev_80e17b973ca818dbce90d7e193826dc3c4afb3f275b0698e32ff0abbc28482f6'),
                limitations=['Header/tileset/grid roles corroborated by native parser; header+8 meaning remains unknown.',
                             'Tile property lanes, object kinds, triggers and runtime generation remain unknown.'])


def parse_escape(data, filename):
    match=re.fullmatch(r'escape_(head|back|center|front|eline)([012])\.dat',filename.lower())
    if not match:raise ValueError('unsupported escape DAT name')
    kind,index=match.groups();start=8 if kind=='head' else 0;stride=4 if kind=='head' else 8
    if len(data)<start or (len(data)-start)%stride:raise ValueError('invalid escape record extent')
    records=[dict(offset=at,values_s16=list(_read(data,'h'*(stride//2),at))) for at in range(start,len(data),stride)]
    return dict(format='V3_ESCAPE_TRACK',kind=kind,layer=int(index),stride=stride,
                header_s16=list(_read(data,'4h',0)) if start else [],records=records,
                native=dict(procedure='0x140148e00',evidence_id='ev_3a53c46f2093ea9322db4113372eebf43cb982a91613f55357de5124fb9cd280',
                            observed_coordinate_factor=32),
                limitations=['Coordinate factor32 is observed in consumers; lane-specific object/interaction meanings remain partial.'])


def parse(data,filename):
    if re.fullmatch(r'(RpgStage\d\d_\d\d|SuccessStage\d\d)\.dat',filename,re.I):result=parse_stage(data)
    elif filename.lower().startswith('escape_'):result=parse_escape(data,filename)
    elif filename.lower()=='mapjump_data.dat':
        if len(data)%12:raise ValueError('map-jump records must be12bytes')
        result=dict(format='V3_MAP_JUMP',stride=12,records=[dict(offset=at,
                    minimum_state_16a0=values[0],minimum_state_1704=values[1],
                    selected_map=values[2],selected_position=values[3],
                    destination_map=values[4],destination_position=values[5])
                    for at in range(0,len(data),12) for values in [_read(data,'6h',at)]],
                    native=dict(procedure='0x140478c90',evidence_id='ev_1e2569f99e90edbee790599afc84e8e6de22010a350f79d0c1963cc3cd1d09ea'),
                    limitations=['Threshold state enum names and complete pad/map input policy not yet resolved.'])
    elif filename.lower().startswith('climax_data_'):
        header=list(_read(data,'6h',0));at=12;groups=[]
        for index,stride in ((3,28),(4,20),(2,8)):
            count=header[index]
            if count<0 or at+count*stride>len(data):raise ValueError('invalid climax group extent')
            groups.append(dict(count=count,stride=stride,records=[dict(offset=p,values_s16=list(_read(data,'h'*(stride//2),p))) for p in range(at,at+count*stride,stride)]))
            at+=count*stride
        if at!=len(data):raise ValueError('unconsumed climax bytes')
        result=dict(format='V3_CLIMAX_GROUPS',header_s16=header,groups=groups,
                    native=dict(procedure='0x14038f8f0',evidence_id='ev_75f82d42253a89281f3d68c575b61595a43db3266a43314172e32307ebc5e429'),
                    limitations=['Group widths/counts are native-proven; panel placement and gameplay lane meanings remain unverified.'])
    elif filename.lower() in ('mpf_setting.dat','mpf_map.dat','mpf_cursol.dat','chareffectanim.dat','map_reaction_medal.dat'):
        name=filename.lower()
        stride={'mpf_setting.dat':78,'mpf_map.dat':10,'mpf_cursol.dat':40,'chareffectanim.dat':48,'map_reaction_medal.dat':16}[name]
        if len(data)%stride:raise ValueError('invalid fixed DAT extent')
        rows=[]
        for at in range(0,len(data),stride):
            row=dict(offset=at,values_s16=list(_read(data,'h'*(stride//2),at)))
            if name=='chareffectanim.dat':
                row.update(match_keys=row['values_s16'][:2],position_s32=list(_read(data,'2i',at+4)),slot_policy_s16=row['values_s16'][6:8],flash_name=data[at+16:at+48].split(b'\0',1)[0].decode('cp932'))
            elif name=='map_reaction_medal.dat':
                row.update(state_filter_bytes=list(data[at+3:at+5]),raw_bytes=list(data[at:at+16]))
            elif name=='mpf_setting.dat':
                values=row['values_s16']
                row.update(state_key=values[:3],bit_0_to_15_indices=values[3:19],
                           bit_28_indices=values[19:22],special_bit_30_enabled=values[22:39])
            elif name=='mpf_map.dat':
                values=row['values_s16']
                row.update(state_key=values[:3],flag_index=values[3],bit_or_special_flag=values[4],
                           native_tail_eight=at>=len(data)-80)
            elif name=='mpf_cursol.dat':
                values=row['values_s16']
                row.update(state_key=values[:3],bit_29_mutation_codes=values[3:20])
            rows.append(row)
        result=dict(format='V3_FIXED_STATE_DAT',variant=name,stride=stride,records=rows,
                    native=dict(procedure={'mpf_setting.dat':'0x140472650','mpf_map.dat':'0x140472650','mpf_cursol.dat':'0x140472650','chareffectanim.dat':'0x140476c20','map_reaction_medal.dat':'0x140458450'}[name]),
                    limitations=['Native-proven row widths; raw signed lanes retained where enum/bit semantics remain partial.'])
    elif filename.lower()=='monokumaz_anim.dat':
        if len(data)<180:raise ValueError('truncated native animation block')
        count=len(data)//180
        result=dict(format='V3_NATIVE_ANIMATION_BLOCKS_PARTIAL',stride=180,
                    blocks=[dict(offset=base,characters=[dict(offset=base+j*36,
                        state_values=list(_read(data,'6h',base+j*36)),
                        motion_indices=list(_read(data,'6h',base+j*36+12)),
                        countdown_values=list(_read(data,'6h',base+j*36+24))) for j in range(5)]) for base in range(0,count*180,180)],
                    unknown_tail_offset=count*180,unknown_tail_hex=data[count*180:].hex(),
                    native=dict(loader='0x140478150',consumer='0x14048ade0'),
                    limitations=['Native accesses five 36-byte character groups per 180-byte selected block, six steps each.',
                                 'Installed payload has 80 trailing bytes after six complete blocks; their runtime role/index domain is unresolved.'])
    else:raise ValueError('unsupported binary map DAT variant')
    result.update(size=len(data),sha256=hashlib.sha256(data).hexdigest())
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
    result=parse(args.source.read_bytes(),args.source.name)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(format=result['format'],size=result['size'])))


if __name__=='__main__':main()
