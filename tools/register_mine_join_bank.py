"""Keep both source-required joins in one indivisible answer object."""
import json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
BANK=ROOT/'art/v4_production/mine_objects_20261104'
GEN=Path('C:/Users/kirby/.codex/generated_images/01a19fd4-cd3f-7123-91ea-3a9194054780')
def main():
    task='T5-MM-01'
    specs=[
        ('two_join_comparison','exec-c4839057-ca0e-4b44-b1ba-a038c16cd4e6.png','paper-left-edge',.06,.08,8.0),
        ('wrapping_warning_print','exec-9e7b47d4-945a-4dd6-a180-ac1a7d973429.png','whole-paper',.59,.08,6.1),
        ('wrapping_storage_fragment','exec-ad9a5bde-cca2-4a03-9762-6d3bda6710c4.png','right-paper',.06,.35,6.1),
        ('separate_recovered_band','exec-590c0f25-054d-4bdd-8909-8145d22f8e3e.png','cap-strip-other',.59,.55,6.1),
    ]
    objects=[]
    for name,file,region,x,y,size in specs:
        source=GEN/file;w,h=Image.open(source).size
        objects.append({'id':name,'source':str(source),'regionId':region,'rect':[x,y,size/20,size*h/w/11]})
    a=json.loads((BANK/'reviewed-additions.json').read_text(encoding='utf-8'))
    a[task]={'reference':'ui/v4/investigation_diagrams_v4/c5_two_joining_boundaries.webp','objects':objects,'maskFile':'14.json','selectionFile':f'selection_{task}.json',
        'mergeCorrectRegions':['paper-left-edge','paper-right-edge','strip-left-edge','strip-right-edge'],
        'comparisonLabel':'서로 이어지는 두 경계',
        'review':{'directViewed':True,'scope':'Existing paper and recovered cap-band comparison requires both joins together, not either partial join. Top two complementary torn paper edges and bottom separate band plus remaining band gap are a single comparison unit. Exact known warning and R- fragment preserved. Illustrative edge geometry only, no microscopic or measured match. First candidate with uninterrupted cap band rejected; second shows band gap and intact cap. No broken glass, contents, date or new label.'}}
    (BANK/'reviewed-additions.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
