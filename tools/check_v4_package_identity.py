"""Compare the latest packaged sources/data without launching a player."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
result=read(ROOT/'Game/build-result.json');package=Path(result['executable']).parent
assert package.resolve().is_relative_to((ROOT/'Game/Builds').resolve())
blueprint=read(ROOT/'Game/Assets/Blueprints/BP_Yumeno.hbblueprint.json')
for field,name in [('header','Yumeno.h'),('source','Yumeno.cpp')]:
    assert blueprint['native'].pop(field)==(ROOT/'Game/Source'/name).read_bytes().decode('utf-8'),name
assert blueprint==read(package/'Content/Assets/Blueprints/BP_Yumeno.hbblueprint.json')
sources=list((ROOT/'Game/Source').rglob('*'))
sources=[p for p in sources if p.is_file() and p.suffix in ('.h','.hpp','.cpp','.inl','.cc','.cxx')]
for p in sources:assert p.read_bytes()==(package/'Content'/p.relative_to(ROOT/'Game')).read_bytes(),str(p)
data=list((ROOT/'Game/Assets/Data').rglob('*.json'))
for p in data:assert read(p)==read(package/'Content'/p.relative_to(ROOT/'Game')),str(p)
manifest=read(package/'game.hbpack.json')
assert manifest['windowsRuntime']=='native'
assert manifest['windowsRenderer']=='d3d11'
checkpoint=ROOT/'Game/Saved/ui-checkpoints/normal-ch3-latest/savegames.json'
assert hashlib.sha256(checkpoint.read_bytes()).hexdigest()=='d43c126c6df61cb9f96b312cb65fdcf9992605368617f23c572fc5c6e9850fe7'
report={'status':'PASS','build':package.name,'inlineSourceExact':True,'packagedMetadataExactAfterEngineSourceStrip':True,'allSourceFilesExact':len(sources),'allGeneratedDataJSONExact':len(data),'skillsGrowthJSONExact':True,'normalCheckpointUnchanged':True,'sourceSkills':sum('sourceLabel' in row for row in read(ROOT/'data/skills.json')['items']),'playerLaunch':False}
destination=ROOT/'Game/Saved'/('source-identity-'+package.name.rsplit('-',1)[1]+'.json')
destination.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
