"""Explicit reviewed associations, never filename-based evidence auto-aliasing."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    evidence={}
    for p in (ROOT/'data/v4_story/chapters').glob('*.json'):
        evidence.update(json.loads(p.read_text(encoding='utf-8')).get('evidenceCatalog',{}))
    rows=[
        ('v4:3:knowledge:alive-confirmation',['waiting_bench_prior_body'],'Previously observed asleep body and bench orientation only; an illustration does not itself measure pulse or prove death. Prior observation is explicitly before later injury.'),
        ('v4:3:knowledge:camera-timing',['reflection_direct_overlap'],'Controlled empty-handed recheck after the attack, not the attack itself or a newly acquired historical recording. Observed overlap/occlusion only.'),
        ('v4:4:knowledge:external-fastening',['outside_fastening_detail'],'Existing exterior fastening structure, not proof of who operated it or at what time. Generic hardware silhouette is illustrative.'),
        ('v4:4:knowledge:no-rear-exit',['storage_dead_end','storage_inside_door'],'Known blocked storage and inside-door recollection. No new accessible exit, measured room geometry or hidden route.'),
        ('v4:4:knowledge:closed-photo',['closed_hatch_leaf'],'Illustration of the previously photographed closed lid, not a new first-hand discovery photograph and no hand or storage interior shown.'),
        ('v4:E5-14',['recovered_cap_broken_band'],'Already recovered intact container with opened band. No invented contents, amount, exact code lettering, glass fracture or earlier perpetrator inferred.'),
        ('v4:E5-17',['recovered_cap_broken_band','separate_recovered_band'],'Existing cap-band gap and separately recovered strip. Two views of the compared parts, not duplicate containers or invented manufacturing measurements.'),
        ('v4:E5-16',['wrapping_warning_print','wrapping_storage_fragment'],'Existing warning and R- fragment, only the known print shown. Image alone does not supply the earlier unread text to the observer.'),
        ('v4:E5-10',['wrapping_storage_fragment'],'Existing recovered partial inventory wrapper, not a newly intact label or new contents. R- is known partial print; precise custody remains evidence text.'),
    ]
    p=ROOT/'tools/v4_evidence_art_semantic.json';semantic=json.loads(p.read_text(encoding='utf-8'))
    vp=ROOT/'tools/v4_evidence_illustration_views.json'
    views=json.loads(vp.read_text(encoding='utf-8')) if vp.exists() else {'schemaVersion':1,'views':[]}
    by_id={r['id']:r for r in views['views']}
    for ident,names,basis in rows:
        entries=[]
        for name in names:
            image='art/v4_production/mine_objects_20261104/'+name+'.png';assert (ROOT/image).is_file()
            view='reviewed_object_'+name
            by_id[view]={'id':view,'file':image,'reviewed':True,'scope':'Already known object/recollection illustration. No new acquisition, photograph, date, medical/forensic conclusion or story fact. See per-evidence binding limits.'}
            entries.append({'id':view,'sha256':sha(ROOT/image)})
        ev=evidence[ident]
        binding={'evidenceId':ident,'evidenceTextSha256':hashlib.sha256((ev['name']+'\n'+ev['text']).encode()).hexdigest(),'views':entries,'reviewBasis':basis,'pixelReview':'2026-11-04 direct full original sprite and native correct-object view inspection','grantPolicy':'Existing owned evidence only; illustrative scope, no grants/answers/queues changed.'}
        assert not any(r['evidenceId']==ident for r in semantic['bindings']),ident
        semantic['bindings'].append(binding)
    views['views']=list(by_id.values())
    vp.write_text(json.dumps(views,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    p.write_text(json.dumps(semantic,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'explicitNewEvidenceBindings':len(rows),'newStoryFacts':False}))
if __name__=='__main__':main()
