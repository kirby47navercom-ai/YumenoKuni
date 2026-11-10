import hashlib,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1];engine=root.parent/'engineCreate';saved=root/'Game/Saved';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text(encoding='utf8'))
build=read(root/'Game/build-result.json');assert build['id']=='2026-11-01T17-48-58-797Z-a1f98373'
work=saved/'native-ui-wheel-restoration-20261102';work.mkdir(exist_ok=True)
source=saved/'native-ui-frame-candidate/HBNativePlayer.cpp';text=source.read_text(encoding='utf8');working=(engine/'native/desktop/HBNativePlayer.cpp').read_text(encoding='utf8');import re
wheel=re.search(r'case WM_MOUSEWHEEL:.*?return 0;',working,re.S)[0];reader='catch(const std::exception& e){failed=true;log(e.what());}DWORD code=0;';assert text.count(wheel)==1 and text.count(reader)==1
before=text.replace(wheel,'').replace(reader,'catch(const std::exception& e){log(e.what());}DWORD code=0;')
original=read(saved/'native-ui-performance-approved-20261102-024635/receipt.json');assert hashlib.sha256(before.encode()).hexdigest()==original['compiledBaseline']['candidateSHA256'],'Only the two missing approved handlers may change'
(work/'before.cpp').write_text(before,encoding='utf8');shutil.copyfile(source,work/'after.cpp');shutil.copyfile(engine/'dist/HBEngine/HBNativePlayer.exe',work/'before-HBNativePlayer.exe');shutil.copyfile(saved/'native-ui-frame-candidate/HBNativePlayer.exe',engine/'dist/HBEngine/HBNativePlayer.exe')
metadata=saved/'native-ui-baseline-0fce033a'
for name in ['game.hbpack.json','Content/Assets/Blueprints/BP_Yumeno.hbblueprint.json','Content/Assets/Scenes/Main.hbscene.json']:
 destination=metadata/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/'Game/Builds/windows/2026-11-01T13-56-29-441Z-0fce033a'/name,destination)
r={'status':'published-rebuild-required','baselineBuild':build['id'],'originalCoreBaseline':'2026-11-01T13-56-29-441Z-0fce033a','compiledSourceOnlyChanges':['previously approved WM_MOUSEWHEEL handling restored','previously approved reader exception failed flag restored'],'beforeSourceSHA256':hashlib.sha256(before.encode()).hexdigest(),'afterSourceSHA256':sha(source),'beforePlayerSHA256':sha(work/'before-HBNativePlayer.exe'),'afterPlayerSHA256':sha(engine/'dist/HBEngine/HBNativePlayer.exe'),'renderUIAndKeyboardOrButtonBranchesUnchanged':True,'cause':'The first UI candidate compiled the23a3359c base but omitted its two previously approved patches. The shipping working CPP already retained both; source working hunks remain untouched.','sourceBuild':read(saved/'native-ui-frame-candidate/build.json'),'installedVersionsOrUserProfileModified':False}
(work/'receipt.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'restored':True,'work':str(work)}))
