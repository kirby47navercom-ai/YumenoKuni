"""Read V3 LLFS/SpFlash UI tables and raw animation operations with offsets.

Reference: CaptainSwag101/DRV3-Sharp Formats/Data/SFL/SflSerializer.cs.
Display tags match Adobe SWF tag identities, but the payloads differ. Native
FUN_1404b7710 (matrix), FUN_1404b74c0 (color), FUN_1404b6d00 (actions) and
FUN_1404b7010 (placement) establish component masks, scale factors and ordering.
Evidence is retained in Downloads/v3_re/native/rea-restored-evidence.json.
No runtime framerate or viewport mapping is guessed.
"""
import argparse
import hashlib
import json
import math
import struct
from pathlib import Path


class _Bits:
    def __init__(self,data,byte=0): self.data,self.bit=data,byte*8
    def get(self,n,signed=False):
        if self.bit+n>len(self.data)*8: raise ValueError('truncated SWF bitfield')
        value=0
        for _ in range(n):
            value=(value<<1)|((self.data[self.bit//8]>>(7-self.bit%8))&1)
            self.bit+=1
        return value-(1<<n) if signed and n and value&(1<<(n-1)) else value
    def byte(self): return (self.bit+7)//8


def _matrix(raw,pos):
    # Native FUN_1404b7710: component mask followed by a shared five-bit width
    # per present group. Not SWF's has-scale/has-rotate MATRIX record.
    if pos>=len(raw):raise ValueError('short SpFlash matrix')
    flags=raw[pos];bits=_Bits(raw,pos+1)
    sx=sy=1.0;rx=ry=0.0
    tx=ty=0.0
    if flags&0x11:
        n=bits.get(5)
        if flags&1:sx=bits.get(n,True)/65536
        if flags&16:sy=bits.get(n,True)/65536
    if flags&0x0a:
        n=bits.get(5)
        if flags&2:rx=bits.get(n,True)/65536
        if flags&8:ry=bits.get(n,True)/65536
    if flags&0x24:
        n=bits.get(5)
        if flags&4:tx=bits.get(n,True)*0.05
        if flags&32:ty=bits.get(n,True)*0.05
    return dict(scale_x=sx,scale_y=sy,rotate_skew0=rx,rotate_skew1=ry,
                translate_x=tx,translate_y=ty,component_mask=flags,
                native_evidence='ev_9727aa40a4dd39983bcac9e37dfdd2fcbb72fba69b0c159f3e46e1df86fe3f97',
                native_translation_scale=0.05),bits.byte()


def decode_operation(opcode,raw):
    if opcode==1: return dict(name='ShowFrame')
    if opcode==28:
        if len(raw)<2: raise ValueError('short RemoveObject2')
        return dict(name='RemoveObject2',depth=struct.unpack_from('<H',raw)[0],trailing_hex=raw[2:].hex())
    if opcode==12:
        pos,actions=0,[]
        while pos<len(raw):
            if pos+4>len(raw):raise ValueError('short SpFlash action header')
            at=pos;code,unknown,size=struct.unpack_from('<BBH',raw,pos);pos+=4
            if pos+size>len(raw):raise ValueError('SpFlash action exceeds tag')
            payload=raw[pos:pos+size]
            action=dict(offset=at,opcode=code,unknown=unknown,name={0:'End',4:'NextFrame',5:'PreviousFrame',6:'Play',7:'Stop',0x81:'GotoFrame',0x83:'ExternalCall',0x8b:'SetTarget',0x8c:'GoToLabel'}.get(code,'unknown'),raw_hex=payload.hex())
            if code==0x81 and len(payload)>=2:action['frame']=struct.unpack_from('<H',payload)[0]
            if code in (0x83,0x8b,0x8c):action['strings']=[x.decode('cp932',errors='replace') for x in payload.split(b'\0') if x]
            actions.append(action)
            pos+=size
            if code==0:break
        return dict(name='DoAction',actions=actions,trailing_hex=raw[pos:].hex())
    if opcode!=26:return dict(name='unknown')
    if len(raw)<3:raise ValueError('short PlaceObject2')
    flags=raw[0];depth=struct.unpack_from('<H',raw,1)[0];pos=3
    result=dict(name='PlaceObject2',flags=flags,depth=depth,move=bool(flags&1))
    if flags&2:
        # SpFlash uses table kind UI8 + entry index UI16, rather than SWF's
        # single UI16 character ID. Retain this observed corpus adaptation.
        if pos+3>len(raw):raise ValueError('short PlaceObject2 character')
        character=int.from_bytes(raw[pos:pos+3],'little');pos+=3
        result['character_id']=character
        result['character_reference']=dict(table=character&255,entry=character>>8)
    if flags&4:
        result['matrix'],pos=_matrix(raw,pos)
    if flags&8:
        if pos>=len(raw):raise ValueError('short SpFlash color')
        component_flags=raw[pos];bits=_Bits(raw,pos+1)
        multiply=[1.0]*4;addition=[0.0]*4
        if component_flags:
            n=bits.get(4)
            for i in range(4):
                if component_flags&(1<<i):multiply[i]=bits.get(n,True)/256
            for i in range(4):
                if component_flags&(16<<i):addition[i]=bits.get(n,True)/256
        result['color_transform']=dict(multiply_rgba=multiply,add_rgba=addition,component_mask=component_flags,
            native_evidence='ev_281438cc2ac8158986ff07dd7b5267901d5e759d25511a208a1dc980cc222d8d')
        pos=bits.byte()
    # Native PlaceObject2 does not consume a SWF Ratio when bit0x10 is set.
    if flags&64:
        if pos+2>len(raw):raise ValueError('short PlaceObject2 clip depth')
        result['clip_depth']=struct.unpack_from('<H',raw,pos)[0];pos+=2
    if flags&32:
        end=raw.find(b'\0',pos)
        if end<0:raise ValueError('unterminated PlaceObject2 name')
        result['instance_name']=raw[pos:end].decode('cp932',errors='replace');pos=end+1
    result['trailing_hex']=raw[pos:].hex()
    return result


def decode_text_header(raw, absolute=0):
    """Native4b3d10 text header; remaining fields deliberately stay raw."""
    if len(raw)<24:raise ValueError('short native SFL text header')
    color,x,y,width,height,alignment,unknown,height_raw=struct.unpack_from('<I4iBBH',raw)
    return dict(offset=absolute,color_u32=color,bounds_xywh=[x,y,width,height],
                alignment_raw=alignment,alignment={1:'right',2:'center'}.get(alignment,'left'),
                unknown_u8_21=unknown,font_height_u16=height_raw,
                native_font_height_design=int(height_raw*0.05),
                remaining_hex=raw[24:].hex(),
                line_gap_u16=struct.unpack_from('<H',raw,30)[0] if len(raw)>=32 else None,
                native_line_gap_design=struct.unpack_from('<H',raw,30)[0]*0.4 if len(raw)>=32 else None,
                native_evidence='ev_ee05dc8da27b4a06ef6697e62024459aa32e501e2916195a54d0933cef09823f',
                limitations=['Design font height precedes hierarchy/viewport/glyph scaling.',
                             'Remaining header fields and runtime style selection are unverified; glyph bearing and line advance have separate consumers.'])


def compose_native_affine(local, parent):
    """4ad070 row-vector order: point * local * parent, excluding state flags."""
    if len(local)!=9 or len(parent)!=9:raise ValueError('native affine matrices need9values')
    return [sum(local[row*3+k]*parent[k*3+column] for k in range(3))
            for row in range(3) for column in range(3)]


def project_design_2d(x, y, viewport):
    """Embedded virtual-screen VS mapping, given an explicit hardware viewport.

    Does not infer letterboxing/window size or apply sprite hierarchy transforms.
    """
    if len(viewport)!=4 or viewport[2]<=0 or viewport[3]<=0:
        raise ValueError('viewport must contain x,y,positive width,height')
    nx,ny=2*x/1920-1,1-2*y/1080
    return dict(ndc=[nx,ny],viewport_xy=[viewport[0]+(nx+1)*viewport[2]/2,
                                      viewport[1]+(1-ny)*viewport[3]/2])


def parse_sfl(data):
    def read(fmt,at,end=None):
        if at<0 or at+struct.calcsize('<'+fmt)>(len(data) if end is None else end):
            raise ValueError(f'SFL out of range at {at:#x}')
        return struct.unpack_from('<'+fmt,data,at)
    if data[:4]!=b'LLFS': raise ValueError('not LLFS')
    patch,minor,major,count=read('HHII',4)
    pos,tables=16,[]
    for _ in range(count):
        table_start=pos
        ident,length,n,unknown1,unknown2=read('IIHHI',pos)
        pos+=16
        end=pos+length
        if end>len(data): raise ValueError('SFL table exceeds file')
        entries=[]
        for _ in range(n):
            entry_start=pos
            eid,size,event,ndata,sequences=read('IIHHI',pos,end)
            pos+=16
            stop=pos+size
            if stop>end: raise ValueError('SFL entry exceeds table')
            raw=data[pos:stop]
            item=dict(id=eid,offset=entry_start,data_offset=pos,length=size,event_number=event,
                      data_count=ndata,uses_sequences=sequences,raw_hex=raw.hex())
            if size%4==0:
                item['int32_interpretation']=list(read('i'*(size//4),pos,stop))
                item['float32_interpretation']=[v if math.isfinite(v) else {'nonfinite':repr(v)} for v in read('f'*(size//4),pos,stop)]
            if ident==2 and size%2==0: item['int16_values']=list(read('h'*(size//2),pos,stop))
            if ident==3 and size==ndata*24:
                item['rect_records']=[dict(image_id=read('I',pos+24*i)[0],unknown_hex=data[pos+24*i+4:pos+24*i+8].hex(),
                                           four_ints=list(read('4i',pos+24*i+8))) for i in range(ndata)]
            if ident==4 and not sequences:
                try:item['text_header']=decode_text_header(raw,pos)
                except ValueError as error:item['text_decode_error']=str(error)
            if sequences:
                cursor,seqs=pos,[]
                try:
                    for _ in range(ndata):
                        seq_start=cursor
                        seq_len,header_len,nops=read('IHH',cursor,stop)
                        name_end=data.find(b'\0',cursor+8,stop)
                        if name_end<0: raise ValueError('sequence name unterminated')
                        name=data[cursor+8:name_end].decode('ascii',errors='replace')
                        cursor=(name_end+4)&~3
                        operations=[]
                        for _ in range(nops):
                            op_at=cursor
                            opcode,opsize=read('HH',cursor,stop)
                            cursor+=4
                            if cursor+opsize>stop: raise ValueError('operation exceeds entry')
                            op=dict(offset=op_at,opcode=opcode,length=opsize,raw_hex=data[cursor:cursor+opsize].hex())
                            try:op['decoded']=decode_operation(opcode,data[cursor:cursor+opsize])
                            except (ValueError,struct.error) as error:op['decode_error']=str(error)
                            if opsize%4==0:
                                op['int32_interpretation']=list(read('i'*(opsize//4),cursor,stop))
                                op['float32_interpretation']=[v if math.isfinite(v) else {'nonfinite':repr(v)} for v in read('f'*(opsize//4),cursor,stop)]
                            operations.append(op)
                            cursor+=opsize
                        seqs.append(dict(offset=seq_start,name=name,declared_length=seq_len,header_length=header_len,operations=operations))
                    item['sequences']=seqs
                    item['sequence_unconsumed_bytes']=stop-cursor
                except ValueError as error: item['sequence_decode_error']=str(error)
            entries.append(item)
            pos=stop
        tables.append(dict(id=ident,offset=table_start,length=length,unknown1=unknown1,unknown2=unknown2,entries=entries,unconsumed_bytes=end-pos))
        pos=end
    return dict(format='V3 SFL',version=f'{major}.{minor}{patch}',sha256=hashlib.sha256(data).hexdigest(),
                size=len(data),tables=tables,trailing_bytes=len(data)-pos,
                limitations=['MATRIX, color and action layouts recovered from native static code; runtime playback has not been observed.',
                             'Screen-pixel mapping, runtime frame rate and easing are unverified.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    result=parse_sfl(args.source.read_bytes())
    result['source']=str(args.source.resolve())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(dict(tables=len(result['tables']),entries=sum(len(t['entries']) for t in result['tables']))))


if __name__=='__main__': main()
