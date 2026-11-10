"""The observation-boundary comparison, never an invented attack recording."""
import json
from register_mine_waiting_banks import BANK,object_row
def main():
    task='T3-MM-01'
    specs=[
        ('reflection_direct_overlap','exec-e9ff4505-a566-484c-bacf-a3a0c5420e34.png','overlap',.06,.04,6),
        ('work_niche_recollection','exec-0b7ff67c-0ca5-4010-8a8f-ff9891450cb9.png','work-inside',.60,.04,5),
        ('storage_inside_door','exec-63cfea3f-84e9-430d-adf8-e862886c7585.png','waiting-door',.10,.50,4),
        ('maze_open_entrance','exec-d415fe13-4c98-4bfe-a10f-3387437f85ea.png','entrance',.39,.50,4),
        ('work_niche_back_wall','exec-cc73ccf4-231d-42d1-b262-edc4b90a9c79.png','H-back-wall',.67,.58,4.5),
    ]
    a=json.loads((BANK/'reviewed-additions.json').read_text(encoding='utf-8'))
    a[task]={'reference':'ui/v4/investigation_diagrams_v4/c3_observation_plan.webp','objects':[object_row(*s) for s in specs],'maskFile':'17.json','selectionFile':f'selection_{task}.json',
        'review':{'directViewed':True,'scope':'Source13b1 I3-12:553..595 controlled empty-handed recheck,165 T3-MM-01 and known observation plan directly reviewed. Same approved gray-haired observer-helper head reflected in fixed mirror while actual shoulder emerges at corner. No visible original handle, attack replay, camera-angle identity, secret door, additional person or measured ray geometry. Illustration preserves overlap and occlusion only; mirror dimensions, fixture style and room fragment dimensions are schematic. Door/alcove/entrance/solid wall are recollection alternatives, not new accessed spaces.'}}
    (BANK/'reviewed-additions.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
