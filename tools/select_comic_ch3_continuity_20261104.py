"""Source-pinned, directly reviewed comic continuity repairs; no story edits."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BANK=ROOT/'art/v4_production/comic_revisions_20261104'
GENERATED=Path('C:/Users/kirby/.codex/generated_images/01a19fd4-cd3f-7123-91ea-3a9194054780')
ROWS={
 (3,'B'):('d2b51c2c-00af-4a60-9456-d47e671ed299','Three times separated: observer and occluded reflected grip; fallen first victim; awake body outside. No invented CCTV or clear first grip. Costume ribbon restored.'),
 (4,'A'):('d1388ae9-4dd4-4847-8f91-af142d593ba8','Separate work-niche investigation with Mio/Sho versus living original body with Nana and awake speaking host at doorway. No second corpse or early knife storage.'),
 (5,'C'):('a8fd405b-d408-4f19-ab02-0e18c33a5b85','Rescue by Sho/Nana; interrupted movement/contact occluded; unresponsive body and still-awake restrained host. Pre-incident shirt clean; purple stain only after. No additional wounds, strike count, host or resurrection.'),
}
def main():
 p=BANK/'selection.json';selected=json.loads(p.read_text(encoding='utf8'))
 task=json.loads((ROOT/'data/v4_story/native_tasks.json').read_text(encoding='utf-8-sig'))['tasks']['T3-MG-01']
 source=(ROOT/'docs/design/rewrite_v4'/task['source']['file']).read_text(encoding='utf-8-sig')
 sha=hashlib.sha256(source.encode()).hexdigest();assert sha==task['source']['fileSha256']
 assert sha=='2ade130b821867bfa7c7edf4347e42a9d3ab78bbaba6faaac10a2e3c2ff360e6'
 for (number,letter),(generated,basis) in ROWS.items():
  slot=task['stage']['slots'][number-1];option=next(o for o in slot['options'] if o['id'].endswith(letter))
  assert slot['answer']==option['id']
  assert source.splitlines()[option['source']['line']-1]==f"|{number}{letter}|{option['label']}|정답|"
  original=GENERATED/f'exec-{generated}.png';digest=hashlib.sha256(original.read_bytes()).hexdigest()
  old=next((r for r in selected['rows'] if (r['taskId'],r['slotId'],r['optionId'])==('T3-MG-01',slot['id'],option['id'])),None)
  if old:
   assert old.get('originalSha256',old['sha256'])==digest;continue
  destination=BANK/f'C3_S{number:02d}_{letter}_continuity.png';assert not destination.exists();shutil.copyfile(original,destination)
  selected['rows'].append({'taskId':'T3-MG-01','slotId':slot['id'],'optionId':option['id'],'captionSha256':hashlib.sha256(option['label'].encode()).hexdigest(),'sourceSha256':sha,'image':destination.relative_to(ROOT).as_posix(),'sha256':digest,'review':{'directViewed':True,'basis':basis,'captionRequired':True,'notHistoricalEvidence':True,'limits':'Illustrated sequence supporting exact authored caption, not a new photograph, witness or measurement. Cropped restraining hands carry no additional identity claim.'},'nativeVisualAcceptance':False})
 p.write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'selectedTotal':len(selected['rows']),'newSourcePinnedRepairs':3,'storyAnswersOrQueuesChanged':False}))
if __name__=='__main__':main()
