"""Keep generated material originals and full-resolution 4x exports. No raster painting."""
from pathlib import Path
import json,shutil
from PIL import Image
from upscale_v4_assets import run
ROOT=Path(__file__).resolve().parents[1]
GEN=Path('C:/Users/kirby/.codex/generated_images/01a17b90-e079-75f1-95c2-c92b9f7ec03a')
items=[
 ('ivory_plaster','exec-5d12ce11-9461-45a8-8394-57915949449c.png','Flat seamless warm ivory plaster with sparse broken ink scratches and tiny stress cracks; no objects, perspective, text, vignette or directional lighting.'),
 ('walnut_ink','exec-7d9ce488-1e61-4003-8dc4-3412c9be3fd2.png','Flat tileable warm walnut surface, horizontal hand-inked grain, no plank borders, perspective, objects, text, vignette or directional lighting.'),
 ('wine_fabric','exec-069324a3-9e50-4433-8a34-db6e9130ae21.png','Flat tileable muted wine-red/dusty rose woven fabric with fine weave and restrained dark hatching; no objects, emblem, border, text or lighting.')]
folder=ROOT/'art/materials_v4';folder.mkdir(parents=True,exist_ok=True);records=[]
for identifier,filename,brief in items:
    original=GEN/filename;dest=folder/(identifier+'.png')
    if not dest.exists():shutil.copy2(original,dest)
    with Image.open(dest) as im:
        size=list(im.size);im.save(dest.with_suffix('.webp'),'WEBP',lossless=True,exact=True,method=4)
    hd=f'art/hd_v4/materials/{identifier}.png'
    run({'id':'material_'+identifier,'source':dest.relative_to(ROOT).as_posix(),'output':hd,'family':'environment_material'})
    record={'id':identifier,'tool':'built-in image_gen','original':str(original),'source':dest.relative_to(ROOT).as_posix(),'source_size':size,'hd_file':hd,'upscale':'complete','prompt_brief':brief,'tile_extent_m':[2,2],'runtime_integrated':False,'visual_review':'source viewed; 3D UV/seam and runtime sharpness acceptance separate'}
    dest.with_suffix('.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8');records.append(record)
(folder/'manifest.json').write_text(json.dumps({'status':'material sources, not story CG','assets':records},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Preserved',len(records),'material originals and 4x outputs')
