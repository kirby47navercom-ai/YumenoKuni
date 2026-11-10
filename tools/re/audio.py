"""Read-only ACB/AFS2/HCA metadata, without exporting or playing audio.

Primary format sources read: vgmstream/src/meta/{awb,acb,hca}.c,
src/coding/libs/clhca.c. Reference sources stay outside the repository.
HCA sample counts follow clhca's 1024-sample block arithmetic. An ACB cue's
reference graph is preserved; a cue index is NOT assumed to be an AWB ID.
"""
import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import struct

from cpk import utf_table


def hca_header(data):
    tag = lambda b: bytes(x & 127 for x in b)
    if len(data) < 24 or tag(data[:4]) != b'HCA\0':
        return {'format': 'unknown', 'header_hex': data[:16].hex()}
    version, header_size = struct.unpack_from('>HH', data, 4)
    if header_size > len(data) or tag(data[8:12]) != b'fmt\0':
        raise ValueError('HCA header truncated or unsupported fmt layout')
    rate = int.from_bytes(data[13:16], 'big')
    blocks, delay, padding = struct.unpack_from('>IHH', data, 16)
    if not rate:
        raise ValueError('HCA zero sample rate')
    result = dict(format='HCA', version=version, header_size=header_size,
                  channels=data[12], sample_rate=rate, blocks=blocks,
                  encoder_delay=delay, encoder_padding=padding,
                  samples=blocks*1024-delay-padding,
                  seconds=(blocks*1024-delay-padding)/rate, loop=None)
    cursor = 24
    lengths = {b'comp':16, b'dec\0':12, b'vbr\0':8, b'ath\0':6,
               b'loop':16, b'ciph':6, b'rva\0':8}
    chunks = []
    while cursor + 4 <= header_size - 2:
        name = tag(data[cursor:cursor+4])
        if name == b'pad\0':
            break
        size = lengths.get(name)
        if name == b'comm' and cursor+5 <= header_size:
            size = 5+data[cursor+4]
        if size is None or cursor+size > header_size-2:
            result['unknown_chunk_offset'] = cursor
            break
        chunks.append({'offset':cursor, 'tag':name.rstrip(b'\0').decode('ascii')})
        if name == b'loop':
            start, end, first_delay, last_padding = struct.unpack_from('>IIHH',data,cursor+4)
            result['loop'] = dict(start_block=start,end_block=end,
                start_sample=start*1024-delay+first_delay,
                end_sample=end*1024-delay+1024-last_padding)
        if name == b'ciph':
            result['encryption_type'] = struct.unpack_from('>H',data,cursor+4)[0]
        cursor += size
    result['chunks'] = chunks
    return result


def awb(stream, base=0, size=None):
    if size is None:
        pos=stream.tell();stream.seek(0,2);size=stream.tell()-base;stream.seek(pos)
    stream.seek(base);head=stream.read(16)
    if len(head)!=16 or head[:4]!=b'AFS2':
        raise ValueError('Invalid AFS2 signature/header')
    width, id_width = head[5],int.from_bytes(head[6:8],'little')
    count=struct.unpack_from('<I',head,8)[0]
    alignment=struct.unpack_from('<H',head,12)[0]
    if width not in (2,4,8) or id_width not in (2,4) or not alignment:
        raise ValueError('Unsupported AFS2 table widths/alignment')
    table_size=count*id_width+(count+1)*width
    if 16+table_size>size:
        raise ValueError('AFS2 tables exceed bank')
    tables=stream.read(table_size)
    ids=[int.from_bytes(tables[i*id_width:(i+1)*id_width],'little')for i in range(count)]
    pos=count*id_width
    offsets=[int.from_bytes(tables[pos+i*width:pos+(i+1)*width],'little')for i in range(count+1)]
    records=[]
    for i in range(count):
        start=(offsets[i]+alignment-1)//alignment*alignment
        end=(offsets[i+1]+alignment-1)//alignment*alignment if offsets[i+1]<size else offsets[i+1]
        if not 16+table_size<=start<=end<=size:
            raise ValueError('AFS2 payload range invalid')
        stream.seek(base+start);prefix=stream.read(min(end-start,4096))
        records.append(dict(index=i,id=ids[i],offset=start,size=end-start,
                            codec=hca_header(prefix)if prefix else {'format':'missing'}))
    return dict(format='AFS2',version=head[4],count=count,alignment=alignment,
                bytes=size,records=records)


def acb(data):
    header=utf_table(data)
    if len(header['rows'])!=1:
        raise ValueError('Expected one ACB header record')
    tables={};blobs={};scalars={};banks=[]
    for key,value in header['rows'][0].items():
        if not isinstance(value,bytes):
            scalars[key]=value
        elif value.startswith(b'@UTF'):
            tables[key]=utf_table(value)
        elif value.startswith(b'AFS2'):
            banks.append(dict(field=key,bank=awb(io.BytesIO(value))))
        else:
            blobs[key]={'bytes':len(value),'sha256':hashlib.sha256(value).hexdigest()}
    names=tables.get('CueNameTable',{}).get('rows',[])
    cues=tables.get('CueTable',{}).get('rows',[])
    named=[]
    for item in names:
        index=item['CueIndex']
        if not 0<=index<len(cues):
            raise ValueError('ACB cue name points outside CueTable')
        named.append({'name':item['CueName'],'cue_index':index,'cue':cues[index]})
    return dict(format='ACB',sha256=hashlib.sha256(data).hexdigest(),
                header=scalars,tables=tables,blobs=blobs,banks=banks,cues=named,
                limitations=['Cue reference/sequence graph retained, not interpreted as playback timing.',
                             'No audio decoding, playback, key recovery or audio file export.'])


def json_value(value):
    if isinstance(value,bytes):
        return {'bytes_hex':value.hex()}
    raise TypeError(type(value).__name__)


def cue_waveforms(document):
    """Resolve structural references; retain alternatives, never guess playback order.

    Supports the sequence -> command noteOn -> synth -> waveform graph present
    in this installation. Unhandled references are explicit, not silently skipped.
    Input can be parsed metadata or its JSON serialization.
    """
    tables = document['tables']
    def blob(value):
        return bytes.fromhex(value['bytes_hex']) if isinstance(value,dict) else value
    def row(table,index):
        rows=tables.get(table,{}).get('rows',[])
        if not 0 <= index < len(rows):
            raise ValueError(f'ACB {table} reference out of bounds: {index}')
        return rows[index]
    def visit(kind,index,stack):
        key=(kind,index)
        if key in stack:
            raise ValueError('ACB reference cycle')
        stack=stack+(key,)
        if kind==1:
            return {index},[]
        edges=[]; unknown=[]
        if kind==2:
            data=blob(row('SynthTable',index)['ReferenceItems'])
            if len(data)%4:
                raise ValueError('ACB synth reference alignment')
            edges=list(struct.iter_unpack('>HH',data))
        elif kind==3:
            sequence=row('SequenceTable',index)
            data=blob(sequence['TrackIndex'])
            count=sequence['NumTracks']
            if count*2>len(data):
                raise ValueError('ACB sequence track list truncated')
            for (track,) in struct.iter_unpack('>H',data[:count*2]):
                event=row('TrackTable',track)['EventIndex']
                command=blob(row('CommandTable',event)['Command'])
                cursor=0
                while cursor<len(command):
                    if cursor+3>len(command):
                        raise ValueError('ACB command header truncated')
                    code,size=struct.unpack_from('>HB',command,cursor);cursor+=3
                    if cursor+size>len(command):
                        raise ValueError('ACB command value truncated')
                    if code in (2000,2003):
                        if size<4:
                            raise ValueError('ACB noteOn reference truncated')
                        edges.append(struct.unpack_from('>HH',command,cursor))
                    elif code==2004:
                        unknown.append({'code':code,'reason':'duration noteOn unsupported'})
                    cursor+=size
        else:
            return set(),[{'type':kind,'index':index,'reason':'reference type unsupported'}]
        found=set()
        for target_kind,target_index in edges:
            values,residual=visit(target_kind,target_index,stack)
            found.update(values);unknown.extend(residual)
        return found,unknown
    output=[]
    for cue in document['cues']:
        values,unknown=visit(cue['cue']['ReferenceType'],cue['cue']['ReferenceIndex'],())
        waveforms=[]
        for index in sorted(values):
            wave=row('WaveformTable',index)
            extension=wave.get('ExtensionData',65535)
            loop=row('WaveformExtensionDataTable',extension) if extension!=65535 else None
            waveforms.append({'waveform_index':index,'waveform':wave,'loop_extension':loop})
        output.append({'name':cue['name'],'cue_index':cue['cue_index'],
                       'waveforms':waveforms,'unknown':unknown})
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.source.suffix.lower()=='.acb':
        result=acb(args.source.read_bytes())
        result['cue_links']=cue_waveforms(result)
    else:
        with args.source.open('rb')as handle:
            result=awb(handle)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=1,default=json_value),encoding='utf-8')
    print(json.dumps({'format':result['format'],'output':str(args.output),
                      'entries':result.get('count',len(result.get('cues',[])))}))
