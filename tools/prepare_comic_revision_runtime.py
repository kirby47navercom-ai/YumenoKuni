"""Metadata-only runtime PNG copies; preserve original and compressed pixels."""
import hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BANK=ROOT/'art/v4_production/comic_revisions_20261104'
def chunks(data):
 assert data[:8]==b'\x89PNG\r\n\x1a\n';offset=8
 while offset<len(data):
  size=struct.unpack_from('>I',data,offset)[0];end=offset+size+12;assert end<=len(data)
  yield data[offset+4:offset+8],data[offset:end];offset=end
 assert offset==len(data)
def main():
 p=BANK/'selection.json';m=json.loads(p.read_text(encoding='utf-8'));receipts=[]
 for row in m['rows']:
  original=row.get('original',row['image']);data=(ROOT/original).read_bytes();source_hash=hashlib.sha256(data).hexdigest();assert source_hash==row.get('originalSha256',row['sha256'])
  runtime=b'\x89PNG\r\n\x1a\n'+b''.join(raw for kind,raw in chunks(data) if kind!=b'caBX')
  assert [raw for kind,raw in chunks(runtime) if kind in (b'IHDR',b'IDAT',b'PLTE',b'tRNS')]==[raw for kind,raw in chunks(data) if kind in (b'IHDR',b'IDAT',b'PLTE',b'tRNS')]
  assert not re.search(br'<svg(?:\s|>)',runtime[:4096],re.I)
  destination=BANK/'runtime'/Path(original).name;destination.parent.mkdir(exist_ok=True);destination.write_bytes(runtime)
  row.update(original=original,originalSha256=source_hash,image=destination.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(runtime).hexdigest())
  receipts.append({'id':row['slotId']+row['optionId'],'originalSha256':source_hash,'runtimeSha256':row['sha256'],'compressedPixelsByteIdentical':True,'onlyCaBXRemoved':True})
 p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(BANK/'runtime-receipt.json').write_text(json.dumps(receipts,indent=2)+'\n',encoding='utf-8');print(json.dumps({'runtimeCopies':len(receipts),'pixelBytesPreserved':True,'engineModified':False}))
if __name__=='__main__':main()
