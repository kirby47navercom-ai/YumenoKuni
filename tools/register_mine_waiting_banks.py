"""Reviewed physical recollection units; no new incident photograph or timeline."""
import json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
BANK=ROOT/'art/v4_production/mine_objects_20261104'
GEN=Path('C:/Users/kirby/.codex/generated_images/01a19fd4-cd3f-7123-91ea-3a9194054780')

def object_row(name,file,region,x,y,size):
    p=GEN/file;w,h=Image.open(p).size
    return {'id':name,'source':str(p),'regionId':region,'rect':[x,y,size/20,size*h/w/11]}

def main():
    body=('waiting_bench_prior_body','exec-5cf43cf0-b6da-4a76-b934-acca27b2d1a3.png')
    empty=('waiting_empty_bench','exec-329c05c5-1385-41f3-bcac-aa37d86bbcde.png')
    aisle=('waiting_middle_aisle','exec-12907417-fcac-4bc7-a1dd-c2802dc413eb.png')
    shelf=('secured_knife_shelf','exec-6d43db4c-a2dc-45a0-89e6-8e80df962537.png')
    a=json.loads((BANK/'reviewed-additions.json').read_text(encoding='utf-8'))
    for task,number,reference,rows,scope in [
        ('T3-MM-A02',15,'c3_waiting_position.webp',[
            object_row(*body,'left-body',.06,.08,7),object_row(*empty,'right-empty',.58,.08,6),object_row(*aisle,'middle',.20,.55,8)],
            'Prior alive-asleep body on left bench: head inward, feet toward entrance, same approved character identity/clothes and wooden bench. Not the later death observation. Right bench empty, central aisle unobstructed. Physical recollection fragments do not establish metric distances or new photographs. Source13b2:95 and183 T3-MM-A02 directly reviewed.'),
        ('T3-MM-A03',16,'c3_knife_custody.webp',[
            object_row(*shelf,'outside-shelf',.06,.08,8),object_row(*empty,'left-head',.58,.08,6),object_row(*aisle,'middle',.20,.55,8)],
            'Existing yellow-black utility knife lies separately on exterior shelf after medical confirmation, not while pressure is being applied. Empty bench denotes head-end location alternative, not a newly missing patient. Central aisle is another location alternative. No new bag/knife/blood pattern, exact blade setting or measured shelf size inferred. Source13b2:129/203 and183 T3-MM-A03 directly reviewed.'),
    ]:
        a[task]={'reference':'ui/v4/investigation_diagrams_v4/'+reference,'objects':rows,'maskFile':f'{number}.json','selectionFile':f'selection_{task}.json','review':{'directViewed':True,'scope':scope}}
    (BANK/'reviewed-additions.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
