"""Author one printed vector strip, then split it with ONE shared mathematical tear."""
from pathlib import Path
import json,hashlib,html
from PIL import Image,ImageDraw,ImageFont,ImageChops
R=Path(__file__).resolve().parents[1];O=R/'ui/v4/documents_hd';S=4;W,H=1280,720
paper=[(40,80),(775,80),(775,655),(40,655)]
tear=[(40,220),(356,220),(341,239),(367,254),(349,275),(370,292),(352,310),(40,310)]
base=Image.new('RGBA',(W*S,H*S));d=ImageDraw.Draw(base);d.polygon([(x*S,y*S) for x,y in paper],fill='#f3ead9');font=ImageFont.truetype(str(R/'fonts/pretendard/Pretendard-Regular.otf'),42*S)
d.text((88*S,243*S),'17',font=font,fill='#29232e');d.text((270*S,243*S),'작동 확인 불가',font=font,fill='#29232e')
mask=Image.new('L',base.size);ImageDraw.Draw(mask).polygon([(x*S,y*S) for x,y in tear],fill=255)
piece=base.copy();piece.putalpha(ImageChops.multiply(base.getchannel('A'),mask));body=base.copy();body.putalpha(ImageChops.subtract(base.getchannel('A'),mask))
combined=body.copy();piece_bbox=piece.getbbox();part=piece.crop(piece_bbox);combined.alpha_composite(part,(865*S,385*S));p=O/'report17_matching_fragment.png';combined.save(p);combined.save(p.with_suffix('.webp'),'WEBP',lossless=True,exact=True,method=4)
polygon=' '.join(f'{x},{y}' for x,y in tear);points=' '.join(f'{x},{y}' for x,y in paper)
contents=f'<polygon points="{points}" fill="#f3ead9"/><text x="88" y="280" font-family="Pretendard" font-size="42" fill="#29232e">17</text><text x="270" y="280" font-family="Pretendard" font-size="42" fill="#29232e">작동 확인 불가</text>'
outer='M0 0H1280V720H0Z';hole='M'+'L'.join(f'{x} {y}' for x,y in tear)+'Z';dx=865-piece_bbox[0]/S;dy=385-piece_bbox[1]/S
svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="5120" height="2880" viewBox="0 0 1280 720"><style>@font-face{{font-family:Pretendard;src:url(../../../fonts/pretendard/Pretendard-Regular.otf)}}</style><defs><clipPath id="piece"><polygon points="{polygon}"/></clipPath><clipPath id="body"><path d="{outer}{hole}" clip-rule="evenodd"/></clipPath></defs><g clip-path="url(#body)">{contents}</g><g transform="translate({dx} {dy})"><g clip-path="url(#piece)">{contents}</g></g></svg>'
p.with_suffix('.svg').write_text(svg+'\n',encoding='utf8');source=R/'docs/design/rewrite_v4/11b_1장_수사_초고.md';text=source.read_text(encoding='utf8');assert '작동 확인 불가' in text
meta={'id':'report17_matching_fragment','source':p.with_suffix('.svg').relative_to(R).as_posix(),'file':p.with_suffix('.webp').relative_to(R).as_posix(),'logical_size':[W,H],'texture_size':list(combined.size),'native_scale':4,'role':'E1-05/06 exact printed-body/tear match detail; not all report wording','source_document':source.relative_to(R).as_posix(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'printed_fields':['17','작동 확인 불가'],'shared_tear_polygon':tear,'fragment_translation_logical':[dx,dy],'proof':'Both image regions are cut from identical original print coordinates by complementary masks; glyph positions and tear line match exactly after reversing translation. No generated pseudo-text used as forensic proof.','runtime_integrated':False}
p.with_suffix('.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('Created exact mathematical paper/glyph match, native5120x2880')
