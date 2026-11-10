"""Register directly reviewed, unscaled storage-boundary recollection sprites."""
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BANK=ROOT/'art/v4_production/mine_objects_20261104'
GENERATED=Path('C:/Users/kirby/.codex/generated_images/01a19fd4-cd3f-7123-91ea-3a9194054780')

def main():
    task='T4-MM-01'
    specs=[
        ('storage_dead_end','exec-8d4a9086-f19c-40b9-b4c8-470e999ce5e0.png','storage-and-wall',.06,.08,6.8),
        ('closed_hatch_leaf','exec-27392c66-f7b5-42f0-bdfc-53de5efeb692.png','hatch',.56,.08,6.5),
        ('front_hall_cutaway','exec-a4f9b9ef-594e-43cd-bc0f-ae0fc7127d9b.png','front-hall',.06,.55,6.5),
        ('storage_inside_door','exec-63cfea3f-84e9-430d-adf8-e862886c7585.png','inside-door',.56,.35,6.5),
    ]
    objects=[]
    for name,file,region,x,y,size in specs:
        source=GENERATED/file
        w,h=Image.open(source).size
        objects.append({'id':name,'source':str(source),'regionId':region,'rect':[x,y,size/20,size*h/w/11]})
    approved=json.loads((BANK/'reviewed-additions.json').read_text(encoding='utf-8'))
    approved[task]={'reference':'ui/v4/investigation_diagrams_v4/c4_storage_boundary.webp','objects':objects,
        'maskFile':'13.json','selectionFile':f'selection_{task}.json',
        'review':{'directViewed':True,'scope':'Unscaled recollection components from the already examined comparison plan. Compact closed storage and existing exterior wall behind it form one comparison unit. Hall, closed inside door and hatch are separate alternatives. No new exit, corridor, window, door-swing direction, measured dimensions or currently accessible location is asserted. Source manuscript14b1:107/121,14b3:195,166:109/114 reviewed.'}}
    (BANK/'reviewed-additions.json').write_text(json.dumps(approved,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
