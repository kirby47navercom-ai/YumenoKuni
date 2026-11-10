"""Explicit widescreen built-in CG jobs; no paid API or credentials."""
from pathlib import Path
import ast,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
tree=ast.parse((ROOT/'tools/plan_v4_story_cg.py').read_text(encoding='utf8'))
actors={}
for n in tree.body:
    if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and getattr(n.value.func,'id','')=='add':
        args=n.value.args;actors[ast.literal_eval(args[0])]=ast.literal_eval(args[3]) if len(args)>3 else []
derived=json.loads((ROOT/'art/v4_production/derived_jobs.json').read_text(encoding='utf8'))['jobs']
refs={}
for j in derived:refs.setdefault(j['character'],j['reference'])
refs.update(mio='art/standing_v4/mio_color_v2.webp',haruka='art/masters_clean_v4/haruka_r2.webp',yuu='art/masters_clean_v4/yuu.webp',taiga='art/masters_clean_v4/taiga.webp',nana='art/standing_v4/nana_fullbody.webp',lappy='art/sprites_nai_v4/lappy/lappy_L01.webp')
base=('Use case: illustration-story / identity-preserve. ONE finished original mystery visual-novel story CG. FULL-BLEED 16:9 WIDESCREEN, target1920x1080. '
      'Each attached image is an exact CHARACTER IDENTITY and STYLE reference, not a composition to paste. Preserve exact faces, eye colors, hair/accessories, costume cuts, hems and small legitimate motifs. '
      'Match reference angular ink contour variation, intricate thin hair strands, precise hard cel shadows, restrained texture and expressive sharp faces. New natural narrative poses, no generic soft anime redesign, no glossy airbrush. '
      'ENVIRONMENT: authored theme park interiors have warm distressed ivory plaster above muted deep-violet wainscoting with thin brass rail, walnut wood, dusty wine upholstery, brass lamps. '
      'Compose faces and ALL essential hands/objects inside x5..95%, y6..69%; reserve bottom25% for dialogue overlay but draw continuous environment there, NO UI. '
      'Leave room above all hair; no head crop. Correct hand anatomy and physical object support. Distinct character heights and attitudes. '
      'Only characters explicitly named; no extra spectators/reflections unless requested. No readable text, captions, watermark, logos, UI, magical effects or invented clue. Fully clothed nonsexual characters. ')
out=ROOT/'art/v4_production/full/builtin_jobs';out.mkdir(parents=True,exist_ok=True);jobs=[]
for j in json.loads((ROOT/'art/v4_production/full/story_cg_jobs.json').read_text(encoding='utf8'))['jobs']:
    cast=actors[j['id']]
    mapping=' '.join(f'Image{i+1}: {slug}, {action}.' for i,(slug,action) in enumerate(cast))
    references=[refs[s] for s,_ in cast] or [refs['mio']]
    if not cast:mapping='Image1 supplies ink/cel DRAWING STYLE ONLY. Do not include this character in the scene.'
    scene=j['scene']
    for old,new in [('green-haired','lavender-bob cat-mask'),('lavender-haired','dusty-pink short-haired'),('silver-haired','blond orange-jacketed'),('brown-haired','burgundy-haired'),('red-haired student organizer','long-blonde-haired student organizer'),('coral-haired','auburn-haired')]:scene=scene.replace(old,new)
    prompt=base+mapping+' STORY MOMENT: '+scene+' AVOID: '+j.get('negative','')
    job={'id':j['id']+'_builtin_r1','source':j['source'],'source_sha256':j['source_sha256'],'references':references,'characters':[s for s,_ in cast],'prompt':prompt,'visual_status':'not generated','scope':'event CG; not whole-project completion'}
    (out/(job['id']+'.json')).write_text(json.dumps(job,ensure_ascii=False,indent=2)+'\n',encoding='utf8');jobs.append(job)
(ROOT/'art/v4_production/full/builtin_jobs.json').write_text(json.dumps({'tool':'built-in image_gen ONLY','jobs':jobs},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Prepared',len(jobs),'source-linked reference CG briefs; not generated')
