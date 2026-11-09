"""New explicitly authored optional gift dialogue, independent of FTE prose."""
import copy,hashlib,json,re
from pathlib import Path
from v4_growth_bindings import ROOT,ROUNDS,build_growth_contract
SOURCE=ROOT/'docs/design/rewrite_v4/선물_추가대본_V4.md'


def build_gift_contract():
    from build_v4_story import Source
    source=Source(SOURCE);catalog=ROOT/'art/gifts_v4/delivery/manifest.json';inventory=ROOT/'data/gifts.json'
    delivered=json.loads(catalog.read_text(encoding='utf-8'))['assets'];items=json.loads(inventory.read_text(encoding='utf-8'))['items']
    by_id={x['id']:x for x in delivered};names={x['id']:x['name'] for x in items};assert len(by_id)==len(names)==110 and by_id.keys()==names.keys()
    growth=build_growth_contract();offers={};scenes={}
    def section(token):
        a=source.at('## '+token)
        b=next((i-1 for i in range(a+1,len(source.lines)+1) if source.lines[i-1].startswith('#')),len(source.lines))
        rows=source.paragraphs(a+1,b)
        assert rows and all(e['type']=='say' for e in rows),token
        return rows
    for actor,rounds in ROUNDS.items():
        info=next(l for l in source.lines if l.startswith('> actor='+actor+';'))
        allowed=re.search(r'품목=([A-Za-z0-9,]+)',info)[1].split(',')
        assert len(allowed)==3 and all(g in by_id for g in allowed)
        ident='gift:'+actor
        scenes[ident]={key:section(ident+':'+key) for key in ('intro','willing','accepted','rejected','deferred','withdrawn')}
        scenes[ident]['acceptedByGift']={}
        for gift in allowed:
            base=copy.deepcopy(scenes[ident]['accepted']);extra=section(ident+':item:'+gift)
            scenes[ident]['acceptedByGift'][gift]=base[:1]+extra+base[1:]
        first=growth['entries'][actor+':1']
        offers[ident]={
            'actor':actor,'allowedGifts':allowed,'acceptedNode':ident+':accepted','dialogueKey':ident,
            'dispositions':{g:('accept' if g in allowed else 'reject') for g in by_id},
            'requiresAnyCompletionFlags':first['completionFlags'],'requiresActualOriginalIdentity':True,
            'freeWindowOnly':True,'duringFteForbidden':True,'duringInvestigationForbidden':True,'duringTrialForbidden':True,
            'presenceSource':'Actual current free-time candidate/actor availability, never future graph catalogue membership.',
            'oneAcceptedGiftPerActorPerWindow':True,'bondDelta':3,'coins':0,'trustChange':False,
            'acceptedAfterInventoryCommitOnly':True,'refusedDeferredCancelledConsume':0,
            'newlyAuthored':True,'source':source.ref(source.at('## '+ident+':intro')),
            'voiceReference':growth['entries'][actor+':3']['source'],
        }
    return {'schemaVersion':1,'contentVersion':'v4','source':{'file':SOURCE.relative_to(ROOT).as_posix(),'sha256':source.hash},
      'inventorySource':{'file':inventory.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(inventory.read_bytes()).hexdigest()},
      'artCatalogue':{'file':catalog.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(catalog.read_bytes()).hexdigest()},
      'items':{k:{'name':names[k],'image':by_id[k]['file']} for k in by_id},'offers':offers,'scenes':scenes,
      'policy':{'newOptionalWriting':True,'replaceExistingFte':False,'insertAtExistingNoGiftMoment':False,'automaticStoryFlagMutation':False,'automaticForgiveness':False,'acceptedBondSource':'docs/design/00_시스템_기획서.md:167 (explicit existing project preference reward; not a V3 numeric claim)','refundDecline':False,'declineNeverConsumes':True,'confirmationRequired':True,'modeAndPresenceRecheckBeforeCommit':True}}


def eligible(contract,offer,flags,*,free_window,busy,present,original_identity,window):
    row=contract['offers'].get(offer)
    return bool(row and free_window and not busy and present and original_identity and window and any(flags.get(k) is True for k in row['requiresAnyCompletionFlags']))


if __name__=='__main__':
    p=ROOT/'tools/v4_gift_contract.json';d=build_gift_contract();p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'offers':len(d['offers']),'catalogueItems':len(d['items']),'sourceDialogueSections':135,'centralOutputsWritten':False},ensure_ascii=False))
