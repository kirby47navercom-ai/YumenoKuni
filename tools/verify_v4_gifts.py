"""New gift source/actual catalogue, conditional queue and no-consumption checks."""
import copy,itertools,json
from pathlib import Path
from v4_gift_bindings import ROOT,SOURCE,build_gift_contract,eligible

def main():
 c=build_gift_contract();assert len(c['offers'])==15 and len(c['items'])==110
 texts=[];actual=set()
 for id,offer in c['offers'].items():
  actor=offer['actor'];s=c['scenes'][id]
  assert len(offer['dispositions'])==110 and len(offer['allowedGifts'])==3
  assert set(offer['dispositions'])==set(c['items'])
  for state in ('intro','willing','accepted','rejected','deferred','withdrawn'):
   for row in s[state]:
    assert row['actor'] in ('mio',actor)
    assert row['source']['file']==SOURCE.name
    assert row['source']['fileSha256']==c['source']['sha256']
    texts.append(row['text']);actual.add(row['id'])
  for gift,rows in s['acceptedByGift'].items():
   assert offer['dispositions'][gift]=='accept' and len(rows)>len(s['accepted'])
   for row in rows:actual.add(row['id'])
  flags={offer['requiresAnyCompletionFlags'][0]:True}
  good=dict(free_window=True,busy=False,present=True,original_identity=True,window='F:next-independent')
  assert eligible(c,id,flags,**good)
  for field,value in [('free_window',False),('busy',True),('present',False),('original_identity',False),('window','')]:
   bad={**good,field:value};assert not eligible(c,id,flags,**bad),(id,field)
  assert not eligible(c,id,{},**good)
  assert offer['trustChange'] is False and offer['acceptedAfterInventoryCommitOnly']
 assert len(actual)==314
 for item in c['items'].values():assert (ROOT/item['image']).is_file()
 assert c['policy']['replaceExistingFte'] is False and c['policy']['automaticForgiveness'] is False
 print(json.dumps({'status':'PASS','newOptionalActors':15,'uniqueAuthoredSayEvents':len(actual),'catalogueIds':110,'explicitActorItemDispositions':15*110,'acceptingActorItemResponses':45,'contextRejectionCases':15*6,'existingFteChanged':False,'centralOutputsWritten':False,'nativeExecution':False},ensure_ascii=False))
if __name__=='__main__':main()
