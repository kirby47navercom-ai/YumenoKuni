"""Losslessly package fresh Blender exports without rewriting original sources."""
from pathlib import Path
import sys
from optimize_native_glb import repack,atomic,LIMIT
file=Path(sys.argv[1])
if file.stat().st_size>=LIMIT:
    before=file.read_bytes();data,proof=repack(before);atomic(file,data)
    print('SCULPTED_LOSSLESS_PACK',file.name,len(before),len(data),flush=True)
assert file.stat().st_size<LIMIT
