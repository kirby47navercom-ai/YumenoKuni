"""Apply only the reviewed, lossless native UI performance delta."""
import hashlib,json,shutil,sys
from pathlib import Path
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1];engine=root.parent/'engineCreate';saved=root/'Game/Saved';read=lambda p:json.loads(p.read_text(encoding='utf8'));sha=lambda b:hashlib.sha256(b).hexdigest()
proof=read(Path(sys.argv[1]));assert proof['ok'] and proof['case']=='active-nonstop' and proof['seconds']>=58 and proof['fps']>=30,'Candidate must first meet the reviewed30FPS scene floor'
assert proof['runtime']['webview'] is False and not proof['runtime']['audio']['errors']
work=saved/('native-ui-performance-approved-'+datetime.now().strftime('%Y%m%d-%H%M%S'));work.mkdir();rows=[]
def apply(name,after,expected=None):
 p=engine/name;before=p.read_bytes() if p.exists() else None
 if expected:assert before is not None and sha(before)==expected,name+' changed since review'
 if before is not None:
  backup=work/'before'/name;backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(before)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(after)
 rows.append({'owner':name,'beforeSHA256':sha(before) if before else None,'afterSHA256':sha(after),'bytes':len(after)})
apply('prototype/ui-runtime.js',(root/'Game/tools/ui-runtime-snapshot.candidate.mjs').read_bytes(),'be90c61690f5cd6acb7aeac2710ec8df666bf052b021704ddc8bdfa1eaeab491')
apply('tools/native-widget-layer.mjs',(root/'Game/tools/native-widget-paint.candidate.mjs').read_bytes(),'36a8ed22535bd2687ddec5d852cc37645cc5b7a4cd4b23a440c7eeb45df1fa5f')
apply('tools/native-ui-frame.mjs',(root/'Game/tools/native-ui-frame.candidate.mjs').read_bytes())
apply('native/desktop/NativeWidgetWindow.hpp',(root/'Game/tools/NativeWidgetWindow.candidate.hpp').read_bytes(),'4e274be2f78e00b09a9b5104bf18a17d9953139bcf77dae367679a3e12856fea')
cpp=engine/'native/desktop/HBNativePlayer.cpp';old=cpp.read_text(encoding='utf8');needle='ui.update(window,message.at("data").at("png").get<std::string>());';replacement='const auto& frame=message.at("data");if(frame.value("encoding",std::string())=="zstd-rgba8-premultiplied")ui.updatePixels(window,frame.at("pixels").get<std::string>(),frame.at("width").get<unsigned>(),frame.at("height").get<unsigned>());else ui.update(window,frame.at("png").get<std::string>());'
assert old.count(needle)==1;new=old.replace(needle,replacement).replace('value={{"ok",true}};}else if(op=="capture")','value={{"ok",true},{"nativeUiDecodeMS",ui.decodeMS},{"nativeUiPresentMS",ui.presentMS}};}else if(op=="capture")')
apply('native/desktop/HBNativePlayer.cpp',new.encode(),'c1965853ca2ad76f6305880c9fb8214f8c41df707887850f653dea7f7f7d5774')
builder=engine/'tools/build-native-player.mjs';old=builder.read_text(encoding='utf8');assert old.count("'-ladvapi32']")==1
new=old.replace("'-ladvapi32']","'-ladvapi32','-lzstd']").replace("const shaders=path.join(path.dirname(output),'Shaders');","const licenseDirectory=path.join(path.dirname(output),'licenses');await fs.mkdir(licenseDirectory,{recursive:true});await fs.copyFile(path.join(root,'native/licenses/zstd-LICENSE.txt'),path.join(licenseDirectory,'native-ui-zstd-LICENSE.txt'));const shaders=path.join(path.dirname(output),'Shaders');")
apply('tools/build-native-player.mjs',new.encode())
license=Path('C:/msys64/ucrt64/share/licenses/zstd/LICENSE').read_bytes()
apply('native/licenses/zstd-LICENSE.txt',license);apply('dist/HBEngine/licenses/native-ui-zstd-LICENSE.txt',license)
apply('dist/HBEngine/HBNativePlayer.exe',(saved/'native-ui-frame-candidate/HBNativePlayer.exe').read_bytes(),'1b4611d3b54b29643fd700b6996199191cbbfd8bf9a1458c5d4c7d1ffffff8c8')
report={'authorization':'Human: 확인된 호환성 결함 수정 허용. Measured actual nonlinear trial UI10.73FPS; no logic/art/resolution/timer reduction.','status':'applied-awaiting-shipping-regression','proof':str(Path(sys.argv[1]).resolve().relative_to(root)),'rows':rows,'compiledBaseline':read(saved/'native-ui-frame-candidate/build.json'),'workingCppForeignHunksPreserved':True,'pixelReference':'Actual C++/WIC PBGRA equality20cases; repeated state snapshots162cases and raster4frames.','installedVersionsAndUserProfileModified':False,'stagingCommitPush':False}
(work/'receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(saved/'native-ui-performance-approved-latest.json').write_text(json.dumps({'work':work.relative_to(root).as_posix(),'receipt':(work/'receipt.json').relative_to(root).as_posix()},ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'work':str(work),'files':len(rows)}))
