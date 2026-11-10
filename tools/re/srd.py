"""Read-only V3 SRD block/resource inventory, texture and static geometry export.

Reference: CaptainSwag101/DRV3-Sharp, Formats/Data/SRD/{Blocks,Resources}.
Block headers are big endian; payload fields are little endian. Unknown fields
remain named unknown. Mesh export is raw local geometry, not a rigged scene.
"""
import argparse
import hashlib
import io
import json
import math
import re
import struct
from collections import Counter
from pathlib import Path

TEXTURE_FORMATS = {1:'ARGB8888', 2:'BGR565', 5:'BGRA4444', 15:'DXT1',
                   17:'DXT5', 20:'BC5', 22:'BC4', 26:'Indexed8', 28:'BC7'}


def _read(data, fmt, at):
    if at < 0 or at + struct.calcsize('<'+fmt) > len(data):
        raise ValueError(f'payload range outside block: {at:#x}, {fmt}')
    return struct.unpack_from('<'+fmt, data, at)


def _string(data, at, encoding='cp932'):
    if at < 0 or at >= len(data):
        raise ValueError(f'string pointer outside block: {at:#x}')
    end = data.find(b'\0', at)
    if end < 0:
        raise ValueError(f'unterminated string at {at:#x}')
    return data[at:end].decode(encoding, errors='replace')


def _slice(data, start, length):
    if start < 0 or length < 0 or start+length > len(data):
        raise ValueError('resource range outside payload')
    return data[start:start+length]


def _float_values(data):
    return [value if math.isfinite(value) else {'nonfinite':repr(value)}
            for value in _read(data, 'f'*(len(data)//4), 0)]


def _payload(kind, data, absolute, companions):
    u = lambda fmt, at: _read(data, fmt, at)
    strings = lambda at, count: [_string(data, u('H', at+2*i)[0]) for i in range(count)]
    if kind == '$RSI':
        a,b,c,external_count,local_count,unknown06,local_at,ints_at,strings_at = u('BBbBhhhhI',0)
        external = []
        for i in range(external_count):
            pointer,length,unknown1,unknown2 = u('IIii',16+16*i)
            # Native54f200: three source bits, then a 29-bit byte offset.
            location = {0:'inline_payload',1:'srdi',2:'srdv'}.get(pointer >> 29,'unknown')
            offset = pointer & 0x1fffffff
            companion = data if location=='inline_payload' else companions.get(location)
            external.append(dict(descriptor_offset=absolute+16+16*i,location=location,
                                 offset=offset,length=length,unknown1=unknown1,unknown2=unknown2,
                                 available=companion is not None,
                                 range_valid=companion is not None and offset+length <= len(companion)))
            if location=='inline_payload':external[-1]['absolute_offset']=absolute+offset
        local = []
        for i in range(local_count):
            name_at,offset,length,unknown = u('IIII', local_at+16*i)
            raw = _slice(data, offset, length)
            item = dict(name=_string(data,name_at), descriptor_offset=absolute+local_at+16*i,
                        offset=absolute+offset,length=length,unknown=unknown,raw_hex=raw.hex())
            if length % 4 == 0:
                item['float32_interpretation'] = _float_values(raw)
                item['uint32_interpretation'] = list(_read(raw,'I'*(length//4),0))
            local.append(item)
        resource_strings=[]
        pos=strings_at
        while pos < len(data):
            end=data.find(b'\0',pos)
            if end<0: raise ValueError('unterminated RSI resource string')
            resource_strings.append(data[pos:end].decode('cp932',errors='replace'))
            pos=end+1
        return dict(unknown00=a,unknown01=b,unknown02=c,unknown06=unknown06,
                    external=external,local=local,strings=resource_strings,
                    unknown_ints=list(u('i'*((strings_at-ints_at)//4),ints_at)) if ints_at else [])
    if kind == '$TXR':
        a,swizzle,width,height,scanline,fmt,b,palette,palette_id=u('IHHHHBBBB',0)
        # Native5977d0 splits legacy ushort+4 into flags:u8 and first RSI
        # external-resource index:u8; +0xd is mip count, not a swizzle enum.
        return dict(unknown00=a,swizzle=swizzle,width=width,height=height,scanline=scanline,
                    format_id=fmt,format=TEXTURE_FORMATS.get(fmt,'unknown'),unknown0d=b,
                    palette=palette,palette_id=palette_id,flags_byte=swizzle&255,
                    first_external_index=swizzle>>8,mip_count=b,is_cubemap=bool(swizzle&8))
    if kind == '$VTX':
        vector_count,unknown04,mesh_type,vertex_count,unknown0c,unknown0e,sections=u('IhhIhBB',0)
        root_at,sections_at,vectors_at,bones_at,unknown18,unknown1c=u('HHHHII',16)
        # Native 0x1405bc160: this is a count/flags byte pair, not one mesh enum.
        attribute_count,buffer_flags=u('BB',6)
        attributes=[]
        for i in range(attribute_count):
            at=u('H',4)[0]+i*8
            name_at,offset,stream,semantic,index,fmt,flags=u('H6B',at)
            attributes.append(dict(descriptor_offset=absolute+at,
                name=_string(data,name_at) if name_at else '',offset=offset,stream=stream,
                semantic_id=semantic,semantic_index=index,format_id=fmt,flags=flags))
        return dict(vector_count=vector_count,unknown04=unknown04,mesh_type=mesh_type,
                    attribute_count=attribute_count,buffer_flags=buffer_flags,attributes=attributes,
                    index_width=4 if buffer_flags&1 else 2,primitive_id=u('B',13)[0],
                    vertex_count=vertex_count,unknown0c=unknown0c,unknown0e=unknown0e,
                    root_pointer=root_at,root_id=u('h',root_at)[0],
                    sections=[dict(start=u('II',sections_at+8*i)[0],stride=u('II',sections_at+8*i)[1]) for i in range(sections)],
                    vectors_pointer=vectors_at,bones_pointer=bones_at,unknown18=unknown18,unknown1c=unknown1c)
    if kind == '$SCN':
        unknown,roots_at,root_count,strings_at,string_count=u('IHHHH',0)
        return dict(unknown00=unknown,roots=strings(roots_at,root_count),unknown_strings=strings(strings_at,string_count))
    if kind == '$TRE':
        depth,unknown04,count,unknown08,leaf_count,matrix_at=u('IHHHHI',0)
        branches=[]
        for i in range(count):
            at=16+i*16
            name_at,leaf_at,n,level,unknown0a,unknown0b,unknown0c=u('IIBBBBI',at)
            leaves=[]
            for j in range(n if leaf_at else 0):
                leaf_name,leaf_unknown=u('II',leaf_at+j*8)
                leaves.append(dict(name=_string(data,leaf_name),unknown04=leaf_unknown))
            branches.append(dict(name=_string(data,name_at),depth=level,leaves=leaves,
                                 descriptor_offset=absolute+at,unknown0a=unknown0a,
                                 unknown0b=unknown0b,unknown0c=unknown0c,
                                 flags=unknown0b,matrix_index=unknown0c))
        return dict(max_depth=depth,unknown04=unknown04,unknown08=unknown08,leaf_count=leaf_count,
                    branches=branches,matrix_offset=absolute+matrix_at,
                    unknown_matrix=list(u('16f',matrix_at)),
                    matrix_semantics='native row-vector local @ parent_world; external root, animation and pointer-sharing flags require runtime context',
                    shared_matrix_candidates=_tre_matrices(data,matrix_at,branches,absolute))
    if kind == '$MSH':
        unknown,vertex_at,material_at,flag_at,strings_at,nodes_at,mapping_at,n,nodes,children,unknown13=u('IHHHHHHBBBB',0)
        return dict(unknown00=unknown,vertex=_string(data,vertex_at),material=_string(data,material_at),
                    special_flag=_string(data,flag_at),strings=strings(strings_at,n),nodes=strings(nodes_at,nodes),
                    mapped_nodes=[dict(child=_string(data,u('HH',mapping_at+i*4)[0]),
                                       parent=_string(data,u('HH',mapping_at+i*4)[1])) for i in range(children)],unknown13=unknown13)
    if kind == '$MAT':
        unknown,a,b,c,x,y,at,n=u('IfffHHHH',0)
        return dict(unknown00=unknown,unknown_floats=[a,b,c],unknown10=x,unknown12=y,
                    maps=[dict(texture=_string(data,u('HH',at+i*4)[0]),map=_string(data,u('HH',at+i*4)[1])) for i in range(n)])
    if kind == '$TXI':
        return dict(linked_texture=_string(data,20),unknown_header_hex=data[:20].hex())
    if kind == '$COL':
        # Independently inferred from the installed PC corpus, not the public
        # SRD parser (which leaves COL opaque). Strict ranges and end coverage
        # distinguish this supported layout from unknown variants.
        version,unknown02,nodes_at,node_count,leaf_count,unknown0c,unknown10,unknown14=u('HHIHHIII',0)
        nodes=[]
        for i in range(node_count):
            at=nodes_at+32*i
            nodes.append(dict(offset=absolute+at,bounds_min=list(u('3f',at)),
                              bounds_max=list(u('3f',at+12)),link_words=list(u('II',at+24))))
        cursor=nodes_at+node_count*32
        leaves=[]
        for i in range(leaf_count):
            vertices_at,indices_at,nvertices,nindices=u('IIHH',cursor)
            if vertices_at < cursor+12 or indices_at != vertices_at+nvertices*16:
                raise ValueError('unrecognized COL leaf layout')
            vertices=[list(u('4f',vertices_at+j*16)) for j in range(nvertices)]
            indices=list(u('H'*nindices,indices_at))
            if any(index!=65535 and index>=nvertices for index in indices):
                raise ValueError('COL index exceeds leaf vertex count')
            if not all(math.isfinite(value) for vertex in vertices for value in vertex):
                raise ValueError('COL nonfinite vertex')
            # 0xffff delimits triangle strips, observed consistently in corpus.
            strips=[[]]
            for index in indices:
                if index==65535: strips.append([])
                else: strips[-1].append(index)
            leaves.append(dict(header_offset=absolute+cursor,vertex_offset=absolute+vertices_at,
                               index_offset=absolute+indices_at,vertices_xyzw=vertices,
                               indices=indices,strips=strips))
            cursor=indices_at+nindices*2
        if cursor!=len(data): raise ValueError('COL unconsumed bytes; unsupported variant')
        return dict(version=version,unknown02=unknown02,node_array_offset=absolute+nodes_at,
                    unknown0c=unknown0c,unknown10=unknown10,unknown14=unknown14,
                    nodes=nodes,leaves=leaves,
                    interpretation='inferred local collision geometry: vec4 vertices, u16 restart strips; tree link bitfields and runtime response unknown')
    if kind == '$RSF':
        return dict(unknown_ints=list(u('4i',0)),folder=_string(data,16))
    return dict(raw_hex=data.hex())


def _tre_matrices(data,matrix_at,branches,absolute=0):
    """Infer shared matrix array up to first name; validate every index.

    The public parser only reads one matrix. Installed files consistently
    have multiple matrices and branch unknown0c values indexing this array.
    """
    if not branches:return dict(status='no branches')
    first_name=_read(data,'I',16)[0]
    length=first_name-matrix_at
    if length<64 or length%64:return dict(status='unsupported array boundary')
    count=length//64
    if any(branch['unknown0c']>=count for branch in branches):
        return dict(status='unsupported matrix index',count=count)
    matrices=[list(_read(data,'16f',matrix_at+64*i)) for i in range(count)]
    if not all(math.isfinite(v) for matrix in matrices for v in matrix):
        return dict(status='nonfinite candidate matrix')
    return dict(status='inferred and bounds validated',offsets=[absolute+matrix_at+64*i for i in range(count)],
                matrices=matrices,branch_matrix_index_field='unknown0c',
                translations_candidate=[matrix[12:15] for matrix in matrices])


def parse_srd(data, companions=None):
    companions = companions or {}
    def blocks(start,end):
        result=[]
        at=start
        while at < end:
            if at+16>end: raise ValueError(f'truncated SRD block header at {at:#x}')
            magic,main_len,sub_len,unknown=struct.unpack_from('>4sIII',data,at)
            if not magic.startswith(b'$'): raise ValueError(f'invalid SRD block magic at {at:#x}')
            kind=magic.decode('ascii')
            main=at+16
            sub=(main+main_len+15)&~15
            next_at=(sub+sub_len+15)&~15
            if main+main_len>end or sub+sub_len>end or next_at>end:
                raise ValueError(f'SRD block overruns container at {at:#x}')
            item=dict(type=kind,offset=at,main_offset=main,main_length=main_len,
                      sub_offset=sub,sub_length=sub_len,unknown=unknown)
            try: item['decoded']=_payload(kind,data[main:main+main_len],main,companions)
            except (ValueError,struct.error,UnicodeError) as error: item['decode_error']=str(error)
            item['children']=blocks(sub,sub+sub_len) if sub_len else []
            result.append(item)
            at=next_at
        return result
    result=blocks(0,len(data))
    counts=Counter(block['type'] for block in walk(result))
    return dict(format='V3 SRD',size=len(data),sha256=hashlib.sha256(data).hexdigest(),
                block_counts=dict(counts),blocks=result,
                limitations=['Local resource float interpretations are not automatically transforms.',
                             'TRE matrices have native local @ parent order; external model/root transforms and collision runtime semantics require context.',
                             'OBJ export has no rig, materials, or scene transform application.'])


def walk(blocks):
    for block in blocks:
        yield block
        yield from walk(block['children'])


def external_bytes(resource, companions):
    if not resource['range_valid']: raise ValueError('external companion missing or range invalid')
    return _slice(companions[resource['location']],resource['offset'],resource['length'])


def texture_image(info, raw):
    """Decode linear PC textures via Pillow's audited DDS BC decoder."""
    from PIL import Image
    width,height,fmt=info['width'],info['height'],info['format_id']
    # Preserve existing PC profiles. Native5977d0/597b40/5c0e50/5a7d30 also
    # prove flags7, format15, ordinary2D mip1 passes original BC1 blocks and
    # ceil(width/4)*8 row pitch to CreateTexture2D without pixel rearrangement.
    # UI audit20261107 extends this same mip1 path to BC7: native28->internal29,
    # DXGI98/99, bpp8/block4 =>16-byte blocks (all-ui-source BC7 proof).
    flags=info.get('flags_byte',info.get('swizzle',0)&255)
    native_bc_7=(flags==7 and fmt in (15,28) and not info.get('is_cubemap',False)
                  and info.get('mip_count',info.get('unknown0d',1))==1)
    if flags not in (1,3,65,67,71) and not native_bc_7:
        raise ValueError('unverified texture layout flag')
    if info['palette']: raise ValueError('palette texture unsupported')
    if fmt==1:
        if len(raw)<width*height*4: raise ValueError('short BGRA texture')
        return Image.frombytes('RGBA',(width,height),raw[:width*height*4],'raw','BGRA')
    fourcc={15:b'DXT1',17:b'DXT5',20:b'ATI2',22:b'ATI1',28:b'DX10'}.get(fmt)
    if fourcc is None: raise ValueError(f'texture format {fmt} unsupported')
    header=bytearray(128)
    header[:4]=b'DDS '
    struct.pack_into('<7I',header,4,124,0x81007,height,width,len(raw),0,0)
    struct.pack_into('<II4s',header,76,32,4,fourcc)
    struct.pack_into('<I',header,108,0x1000)
    extension=struct.pack('<5I',98,3,0,1,0) if fmt==28 else b''
    image=Image.open(io.BytesIO(header+extension+raw))
    image.load()
    return image.convert('RGBA')


def texture_resource(info, resource_info):
    """Select the declared base mip by native TXR+5, with strict RSI bounds."""
    index=info.get('first_external_index',info.get('swizzle',0)>>8)
    resources=resource_info['external']
    if index<0 or index>=len(resources):
        raise ValueError('texture external index outside RSI resources')
    return resources[index]


def export_assets(parsed, companions, output):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    exports=[]
    for block in walk(parsed['blocks']):
        if block['type'] not in ('$TXR','$VTX','$COL') or 'decoded' not in block: continue
        rsi=next((child.get('decoded') for child in block['children'] if child['type']=='$RSI'),None)
        if not rsi: continue
        info=block['decoded']
        name=rsi['strings'][0] if rsi['strings'] else f"resource_{block['offset']:x}"
        safe=re.sub(r'[^\w.-]+','_',name)
        entry=dict(type=block['type'],name=name,block_offset=block['offset'])
        try:
            if block['type']=='$TXR':
                raw=external_bytes(texture_resource(info,rsi),companions)
                image=texture_image(info,raw)
                target=output/(safe+'.png')
                image.save(target)
                entry.update(output=str(target),width=image.width,height=image.height)
            elif block['type']=='$COL':
                target=output/(safe+'.collision.obj')
                vertex_base=1
                triangles=0
                with target.open('w',encoding='utf-8') as stream:
                    stream.write('# Inferred COL geometry, local units; strip winding unverified\n')
                    for i,leaf in enumerate(info['leaves']):
                        stream.write(f'g leaf_{i}\n')
                        for vertex in leaf['vertices_xyzw']:
                            stream.write('v '+' '.join(format(v,'.9g') for v in vertex[:3])+'\n')
                        for strip in leaf['strips']:
                            for j in range(len(strip)-2):
                                triangle=strip[j:j+3]
                                if j%2: triangle[0],triangle[1]=triangle[1],triangle[0]
                                if len(set(triangle))<3: continue
                                stream.write('f '+' '.join(str(v+vertex_base) for v in triangle)+'\n')
                                triangles+=1
                        vertex_base+=len(leaf['vertices_xyzw'])
                entry.update(output=str(target),vertices=vertex_base-1,triangles=triangles,
                             inference='geometry reconstructed from bounds-checked vec4/u16-strip layout; collision response unverified')
            else:
                n=info['vertex_count']
                sections=info['sections']
                if not sections or sections[0]['stride']<12: raise ValueError('unrecognized vertex section layout')
                geometry=external_bytes(rsi['external'][0],companions)
                indices=external_bytes(rsi['external'][1],companions)
                if len(indices)%6: raise ValueError('index stream is not u16 triangle list')
                positions=[_read(geometry,'3f',sections[0]['start']+i*sections[0]['stride']) for i in range(n)]
                if not all(math.isfinite(v) for p in positions for v in p): raise ValueError('nonfinite positions')
                triangles=list(struct.iter_unpack('<3H',indices))
                if any(v>=n for t in triangles for v in t): raise ValueError('vertex index outside vertex array')
                target=output/(safe+'.obj')
                with target.open('w',encoding='utf-8') as stream:
                    stream.write('# SRD local geometry; original coordinate axes; no world transforms\n')
                    for p in positions: stream.write('v '+' '.join(format(v,'.9g') for v in p)+'\n')
                    for t in triangles: stream.write('f '+' '.join(str(v+1) for v in t)+'\n')
                entry.update(output=str(target),vertices=n,triangles=len(triangles),
                             bounds_min=[min(p[i] for p in positions) for i in range(3)] if positions else [],
                             bounds_max=[max(p[i] for p in positions) for i in range(3)] if positions else [])
        except (ValueError,IndexError,KeyError,struct.error,OSError,NotImplementedError) as error:
            entry['error']=str(error)
        exports.append(entry)
    return exports


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--export',type=Path)
    args=parser.parse_args()
    companions={ext:args.source.with_suffix('.'+ext).read_bytes() for ext in ('srdi','srdv') if args.source.with_suffix('.'+ext).exists()}
    result=parse_srd(args.source.read_bytes(),companions)
    result['source']=str(args.source.resolve())
    if args.export: result['exports']=export_assets(result,companions,args.export)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(dict(block_counts=result['block_counts'],exports=len(result.get('exports',[])),output=str(args.output))))


if __name__=='__main__': main()
