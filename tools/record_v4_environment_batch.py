"""Record this batch's actual files and manual findings; never approve by generation count."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
reviews={
 'p01_notebook_boundary_v3':('HOLD','Eye colors corrected; bag appears closed despite the scene requiring it open; keychain/acting continuity still pending.'),
 'p02_opened_seal':('REJECT','Thermos-like jug and tissue-like strip do not match the intended tamper ring.'),
 'p03_dust_boundary':('REJECT','An unrequested character portrait appears on the notice board.'),
 'p04_handle_observation':('REJECT','Unrequested pale hair/person and hand introduce identity/action errors.'),
 'p04_unanswered_phone':('REJECT','Receiver remains on the cradle instead of beside the phone.'),
 'p02_opened_seal_v2':('INSERT_CANDIDATE','Separated broken plastic ring/cap present. Match final authored jug design and HD ring detail before final selection.'),
 'p03_dust_boundary_v2':('HOLD','No portrait, but dust/clean patch reads like a grey rectangle rather than subtle rubbed wood.'),
 'p04_handle_observation_v2':('HOLD','Unrequested person removed. Distinct two wear areas and final 3D handle continuity remain unresolved.'),
 'p04_unanswered_phone_v2':('REJECT','Receiver geometry is split/malformed.'),
 'p04_unanswered_phone_v3':('REJECT','A second receiver remains on the phone base.'),
 'p03_dust_boundary_v3':('REJECT','Rubbed dust patch instead reads as peeling paint/bare wood damage.'),
 'p04_unanswered_phone_v4':('HOLD','Own 3D composition guide preserved layout, but the result remains an uninked 3D study, not final anime CG.'),
 'p04_unanswered_phone_v5':('REJECT','Higher img2img strength adds ink but reintroduces an extra receiver on the base.'),
}
rows=[]
for identifier,(verdict,reason) in reviews.items():
    p=ROOT/'art/cg_v4'/f'{identifier}.png';mp=p.with_suffix('.json');meta=json.loads(mp.read_text(encoding='utf8'))
    assert p.exists() and (ROOT/meta['hd_file']).exists()
    meta['visual_review']={'verdict':verdict,'reason':reason,'scope':'source full image inspected; no blanket HD detail approval','runtime_integrated':False}
    mp.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    rows.append({'id':identifier,'source':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),**meta['visual_review']})
cg={'tool':'NovelAI V5, original production only','source_reviewed':len(rows),'final_accepted':0,'entries':rows,
    'failed_attempt':{'id':'p04_unanswered_phone_v6','model':'nai-diffusion-5-full','action':'infill','http_status':400,'message':'Model nai-diffusion-5-full does not support action infill','generated_asset':False,'retry':'disabled in generator; do not silently substitute V4.5'},
    'next_method':'Further CG needs a different V5-supported composition/repair method; no same text-only or infill retries.',
    'official_references':['https://docs.novelai.net/en/image/inpaint/','https://image.novelai.net/docs/doc.json']}
(ROOT/'art/v4_production/cg_environment_review.json').write_text(json.dumps(cg,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
space=json.loads((ROOT/'art/space_v4/detail_v1/manifest.json').read_text(encoding='utf8'))
qa=json.loads((ROOT/'art/space_v4/detail_v1/qa.json').read_text(encoding='utf8'))
assert len(qa['files'])==len(space['models'])+len(space['spaces'])
modes={m:sum(s['mode']==m for s in space['spaces']) for m in ['free_walk','fixed_pan','scripted_court']}
ui=[]
for folder in ['systems_hd','trial_hd']:
    report=json.loads((ROOT/f'ui/v4/{folder}/qa.json').read_text(encoding='utf8'));assert report['status']=='PASS';ui.append({'folder':folder,'count':report['count']})
hd=json.loads((ROOT/'art/v4_production/hd_qa.json').read_text(encoding='utf8'));assert not hd['pending_ids']
record={'date':'2026-10-28','whole_game_art_complete':False,'game_integrated':False,
 'new_ui':ui,'new_ui_total':sum(x['count'] for x in ui),
 'environment':{'folder':'art/space_v4/detail_v1','kit_models':len(space['models']),'new_kit_models':len(space['models'])-31,'spaces':len(space['spaces']),'modes':modes,'GLB_structural_pass':len(qa['files']),'renders':len(list((ROOT/'Game/Saved/v4-space-detail-v1').glob('*.png'))),'manual_view_scope':'14 cutaway +13 inside overview contact images inspected; selected full individual views; not every object/detail','runtime':'not tested'},
 'new_CG_candidates':len(rows),'final_CG_accepted':0,'CG_review':'art/v4_production/cg_environment_review.json',
 'new_fx':[{'id':name,'tool':'built-in image_gen','source_center_alpha':0,'HD':'4x','runtime':'not tested'} for name in ['tension_whip','unease_border']],
 'total_HD_candidates_structural_pass':hd['upscaled_art_checked'],'total_UI_native_4x_checked':hd['vector_ui_4x_checked'],
 'limits':['counts include rejected/superseded candidates; not whole-game completion','CG source geometry/story matching still unresolved','whole park topology and final visual material pass pending','Game high-resolution import, movement/collision, audio/VFX scene integration and runtime QA pending','Game source, old originals and old candidates preserved; no build/staging/commit in this art-only batch']}
(ROOT/'art/v4_production/environment_batch_02.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Recorded',record['new_ui_total'],'new UI;',record['environment']['GLB_structural_pass'],'GLB checks;',len(rows),'CG candidates, zero final acceptance; HD',hd['upscaled_art_checked'])

