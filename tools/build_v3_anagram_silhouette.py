"""Wrap our approved protagonist art for the observed dark anagram silhouette.

The original image bytes are embedded unchanged. SVG crop/tint is presentation,
not a newly generated pose or an original-game asset.
"""
from pathlib import Path
import base64, hashlib, json
root=Path(__file__).resolve().parents[1]
source=root/'art/hd_v4/masters/mio.webp';raw=source.read_bytes()
svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="5120" height="2880" viewBox="0 0 1280 720"><defs><filter id="silhouette"><feColorMatrix type="matrix" values="0 0 0 0 .008 0 0 0 0 .025 0 0 0 0 .055 0 0 0 .94 0"/></filter></defs><image href="data:image/webp;base64,{base64.b64encode(raw).decode()}" x="-368" y="-60" width="1966.08" height="2949.12" filter="url(#silhouette)"/></svg>'''
dest=root/'ui/v4/v3_reference/anagram_silhouette.svg';dest.write_text(svg,encoding='utf8')
print(json.dumps({'source':source.relative_to(root).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'sourcePixelsChanged':False,'originalGameRead':False,'output':dest.relative_to(root).as_posix()}))
