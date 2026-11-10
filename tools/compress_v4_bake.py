"""Run in the existing project Python, which owns Pillow (Blender does not)."""
from pathlib import Path
import sys
from v4_lowpoly_glb import read
from optimize_native_glb import repack,atomic
file=Path(sys.argv[1]);j,b=read(file)
if any(i.get('mimeType')=='image/png' for i in j.get('images',[])):
 data,proof=repack(file.read_bytes());atomic(file,data)
assert file.stat().st_size<64*1024*1024
print('LP_LOSSLESS',file.name,file.stat().st_size,flush=True)
