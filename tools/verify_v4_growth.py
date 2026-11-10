"""Read-only source identities, aliases and truthful source policy checks."""
from v4_growth_bindings import ROOT,ROUNDS,ALIASES,build_growth_contract
import json

def main():
 c=build_growth_contract();assert len(c['entries'])==45 and len(c['flagIndex'])==60
 assert len(ROUNDS)==15 and len(ALIASES)==15
 assert c['flagIndex']['fte:152:complete']==c['flagIndex']['fte:33:complete']
 assert c['flagIndex']['fte:153:complete']==c['flagIndex']['fte:22:complete']
 assert len({k for k in c['flagIndex'].values()})==45
 assert all(not e['trustChange'] and not e['unlocksStoryEvidence'] for e in c['entries'].values())
 skills=json.loads((ROOT/'data/skills.json').read_text(encoding='utf-8'))
 native=''.join(p.read_text(encoding='utf-8') for p in (ROOT/'Game/Source').glob('*.hpp'))+(ROOT/'Game/Source/Yumeno.cpp').read_text(encoding='utf-8')
 assert all(s['effect'] in c['supportedEffects'] and any(call in native for call in ('skillOn("'+s['effect']+'")','Effect(s,"'+s['effect']+'")')) for s in skills['items'])
 assert c['policy']['automaticEquip'] is False and c['policy']['isOriginalV3NumericClaim'] is False
 assert not c['giftOffers']
 print(json.dumps({'status':'PASS','canonicalEncounters':45,'completionAliases':60,'supportedSkillItems':len(skills['items']),'choiceTrustMutation':False,'nativeExecution':False,'fixture':'tools/tests/v4_growth_fixture.cpp'},ensure_ascii=False))
if __name__=='__main__':main()
