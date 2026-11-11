#include "DialoguePortraitV4.hpp"
const hb::Json& Yumeno::galleryRecord(const std::string& id)const{return storyv4::bucketData("Assets/Data/v4_story/gallery_records/",storyv4::bucket(id,64)).at("records").at(id);}
void Yumeno::galleryGrant(const std::string& id){if(mode==Mode::Gallery||mode==Mode::Machine||galleryReplay)return;if(galleryv4::grant(galleryState,id))galleryDirty=true;}
void Yumeno::galleryRecordNode(const Json& n){
 if(galleryReplay||mode==Mode::Gallery||mode==Mode::Machine)return;auto id=n.value("id",std::string());if(id.empty())return;
 const auto& map=storyv4::bucketData("Assets/Data/v4_story/gallery_map/",storyv4::bucket(id,128)).at("nodes");if(map.contains(id))for(const auto& item:map.at(id))galleryGrant(item.get<std::string>());
}
void Yumeno::galleryInit(){
 galleryv4::State saved;try{auto profile=Json::parse(Save::ReadText(campaignv4::slot("yumeno-v4-gallery")));if(galleryv4::restore(saved,profile)){galleryProfileHead=profile;galleryv4::merge(galleryState,saved);}}catch(const std::exception&){}
 try{auto head=Json::parse(Save::ReadText(campaignv4::slot("yumeno-progress-v4")));if(galleryv4::restore(saved,head.value("gallery",Json())))galleryv4::merge(galleryState,saved);if(head.contains("galleryBank")){galleryRecoveryBank=head["galleryBank"];if(galleryv4::restore(saved,galleryRecoveryBank))galleryv4::merge(galleryState,saved);}}catch(const std::exception&){}
}
void Yumeno::galleryOpen(){
 prepareGameplay();
 auto liveRead=v4.active?v4.read:std::set<std::string>{};galleryInit();galleryHead=Json::object();try{auto head=Json::parse(Save::ReadText(campaignv4::slot("yumeno-progress-v4")));if(campaignv4::matches(head))galleryHead=std::move(head);}catch(const std::exception&){}
 try{if(!galleryHead.empty()){
  coins=std::clamp(galleryHead.value("coins",0),0,999);gifts=galleryHead.value("gifts",std::map<std::string,int>{});giftKnown=galleryHead.value("giftKnown",std::set<std::string>{});giftNew=galleryHead.value("giftNew",std::set<std::string>{});pulls=galleryHead.value("pulls",0);
  galleryv4::State saved;if(galleryv4::restore(saved,galleryHead.value("gallery",Json())))galleryv4::merge(galleryState,saved);
  auto ch=galleryHead.value("chapter",std::string());storyv4::State context;
  if(ch!="P"&&(ch.size()!=1||ch[0]<'1'||ch[0]>'6'))throw std::runtime_error("Gallery chapter context");
  if(!storyv4::restore(context,Data::Get(campaignv4::chapterPath(ch,campaignv4::installed())),galleryHead))throw std::runtime_error("Gallery saved context");
  playerprogress::State player;if(!playerprogress::restore(player,galleryHead.value("playerProgress",Json())))throw std::runtime_error("Gallery saved level");growthv4::State skills;growthv4::Init(skills,Data::Get(campaignv4::growthPath(campaignv4::installed())),skillData);if(galleryHead.contains("growth")&&!growthv4::Restore(skills,galleryHead["growth"],playerprogress::level(player),ch=="P"?0:std::stoi(ch)))throw std::runtime_error("Gallery saved skills");
  if(v4TaskActive||v4Court)v4LeaveTrial();v4=std::move(context);v4.restoring=false;v4Court=v4TaskActive=v4QueueActive=false;chapterAt=ch=="P"?0:std::stoi(ch);chapter=Json{{"chapter",ch}};growthV4=std::move(skills);playerProgress=player;cards=galleryHead.value("cards",std::set<std::string>{});bonds=galleryHead.value("bonds",std::map<std::string,int>{});v4Documents=galleryHead.value("documents",Json::object());exworld::restore(world,galleryHead.value("world",Json::object()));world.id=galleryHead.value("worldId",std::string("plaza"));world.active=false;
  if(!campaignv4::installed())for(const auto& key:galleryHead.value("growth",Json::object()).value("completed",Json::array()))if(galleryv4::grant(galleryState,"fte:"+key.get<std::string>()))galleryDirty=true;
 }
 }catch(const std::exception&){toast("갤러리에서 저장 기록을 읽지 못했어요");return;}
 exworld::load(world);
 galleryRead.clear();galleryReadJob={};galleryReadJob.rows=Json(liveRead);
 std::set<std::string> snapshots;for(const auto& candidate:std::vector<Json>{galleryHead,galleryHead.value("galleryBank",Json::object()),galleryRecoveryBank,galleryProfileHead}){if(candidate.empty())continue;auto snapshot=candidate.value("snapshot",std::string());if(!snapshot.empty()&&!snapshots.insert(snapshot).second)continue;galleryv4::enqueue(galleryReadJob,candidate);}
 galleryReading=true;gallerySavePhase=0;gallerySaving=false;gallerySaveJob={};
 galleryDepth=galleryTop=galleryRow=galleryFirst=0;galleryViewer=galleryReplay=galleryConfirm=false;galleryPlaying.clear();galleryArmed=false;galleryConfirmChoice=1;
 titleMenu(false);hideFlow();hideExplore();dialogVisible(false);exworld::visible(world,false);for(auto id:{"Title","Backdrop","Background","Portrait"})UI::SetVisible(this,UI_ID,id,false);
 UI::Show(this,"Assets/UI/GalleryV4.hbwidget.json","galleryv4");mode=Mode::Gallery;music("bgm_title");galleryDraw();
}
void Yumeno::galleryReadTick(){
 if(!galleryReading)return;
 auto added=galleryv4::readStep(galleryReadJob,[](const std::string& slot){return Json::parse(Save::ReadText(slot));});
 for(const auto& id:added){if(!galleryRead.insert(id).second)continue;const auto& map=storyv4::bucketData("Assets/Data/v4_story/gallery_map/",storyv4::bucket(id,128)).at("nodes");if(map.contains(id))for(const auto& item:map[id])if(galleryv4::grant(galleryState,item.get<std::string>()))galleryDirty=true;}
 if(galleryReadJob.done){galleryReading=false;v4.read=galleryRead;if(!galleryv4::readable(galleryReadJob))toast("지난 회상 원장을 읽지 못했어요. 구입과 저장을 보류해요");galleryDraw();}
}
std::vector<std::string> Yumeno::galleryRows()const{
 static const auto catalog=Data::Get("Assets/Data/v4_story/gallery_catalog.json");static const char* keys[]{"event","movie","artwork","bgm","monomono","intimacy","return_title"};auto key=keys[std::clamp(galleryTop,0,6)];if(!catalog["order"].contains(key))return {};return catalog["order"][key].get<std::vector<std::string>>();
}
void Yumeno::galleryDraw(){
 if(mode!=Mode::Gallery)return;static const auto layout=Data::Get("Assets/Data/v4_story/gallery_layout.json");static const char* names[]{"이벤트 기록","영상 기록","일러스트","음악","모노모노머신","자유행동 기록","타이틀로 돌아가기"};
 UI::SetVisible(this,"galleryv4","root",true);for(auto id:{"GaShade","GaTitle"})UI::SetVisible(this,"galleryv4",id,!galleryViewer);UI::SetVisible(this,"galleryv4","GaViewer",galleryViewer&&!galleryReplay);UI::SetVisible(this,"galleryv4","GaPreview",false);
 UI::SetTexture(this,"galleryv4","GaShade",layout["material"]["backgrounds"][galleryDepth?"list":"top"].get<std::string>());
 static const auto catalog=Data::Get("Assets/Data/v4_story/gallery_catalog.json");static const char* keys[]{"event","movie","artwork","bgm","monomono","intimacy","return_title"};
 for(int i=0;i<7;i++){auto id="GaTop"+std::to_string(i);bool enabled=i!=4||galleryState.machine;UI::SetVisible(this,"galleryv4",id,galleryDepth==0&&!galleryViewer);UI::SetText(this,"galleryv4",id,names[i]);UI::SetColor(this,"galleryv4",id,i==galleryTop&&enabled?Color{0,0,0,1}:Color{1,1,1,1});bool fresh=false;if(catalog["order"].contains(keys[i]))for(const auto& item:catalog["order"][keys[i]])if(galleryv4::fresh(galleryState,item.get<std::string>())){fresh=true;break;}UI::SetVisible(this,"galleryv4","GaTopNew"+std::to_string(i),galleryDepth==0&&!galleryViewer&&fresh);}
 auto rows=galleryRows();galleryRow=std::clamp(galleryRow,0,std::max(0,int(rows.size())-1));if(galleryRow<galleryFirst)galleryFirst=galleryRow;if(galleryRow>=galleryFirst+11)galleryFirst=galleryRow-10;
 int cursor=galleryDepth?galleryRow-galleryFirst:layout["categories"][galleryTop]["native_top_index"].get<int>();UI::SetVisible(this,"galleryv4","GaCursor",!galleryViewer&&(!galleryDepth||!rows.empty()));UI::SetTexture(this,"galleryv4","GaCursor",layout["material"]["cursors"][galleryDepth?"list":"top"][cursor].get<std::string>());
 for(int i=0;i<11;i++){int at=galleryFirst+i;bool show=galleryDepth==1&&!galleryViewer&&at<int(rows.size());auto id="GaRow"+std::to_string(i),cost="GaPrice"+std::to_string(i);UI::SetVisible(this,"galleryv4",id,show);UI::SetVisible(this,"galleryv4",cost,show);UI::SetVisible(this,"galleryv4","GaRowNew"+std::to_string(i),show&&galleryv4::fresh(galleryState,rows[at]));UI::SetVisible(this,"galleryv4","GaPlaying"+std::to_string(i),show&&rows[at]==galleryPlaying);if(!show)continue;
  const auto& row=galleryRecord(rows[at]);int status=galleryv4::status(galleryState,rows[at]);std::string label=status?row.value("label",rows[at]):"？？？？？？";if(status&&row.value("category",std::string())=="intimacy")label=nameOf(row.value("actor",std::string()))+" · "+std::to_string(row.value("episode",1))+"번째 기록";
  UI::SetText(this,"galleryv4",id,label);auto ink=at==galleryRow&&status?Color{0,0,0,1}:Color{1,1,1,1};UI::SetColor(this,"galleryv4",id,ink);UI::SetColor(this,"galleryv4",cost,ink);UI::SetText(this,"galleryv4",cost,status==2?"보유":status==1&&row.value("price",0)>0?std::to_string(row.value("price",0)):std::string());
 }
 for(int i=0,divisor=1;i<3;i++,divisor*=10){auto id="GaCoin"+std::to_string(i);bool show=galleryDepth==1&&!galleryViewer&&(i==0||coins>=divisor);UI::SetVisible(this,"galleryv4",id,show);if(show)UI::SetTexture(this,"galleryv4",id,layout["material"]["coinDigits"][i][std::clamp(coins/divisor%10,0,9)].get<std::string>());}
 std::string status;if(galleryReading)status="지난 진행 기록 준비 중…";else if(galleryDepth&&rows.empty())status="아직 준비된 기록이 없어요";UI::SetText(this,"galleryv4","GaStatus",galleryViewer?std::string():status);

 if(galleryDepth==1&&!galleryViewer&&!rows.empty()){const auto& row=galleryRecord(rows[galleryRow]);if(galleryState.available.count(rows[galleryRow])&&row.contains("image")){UI::SetTexture(this,"galleryv4","GaPreview",row["image"].get<std::string>());UI::SetVisible(this,"galleryv4","GaPreview",true);}}
 UI::SetVisible(this,"galleryv4","GaHint",!galleryReplay);UI::SetColor(this,"galleryv4","GaHint",Color{1,1,1,1});UI::SetText(this,"galleryv4","GaHint",galleryViewer?"Enter 다음 · Esc 목록으로":galleryDepth?"W/S 선택 · Q/E 페이지 · Enter 구입/열람 · Esc 뒤로":"W/S 선택 · Enter 결정 · Esc 타이틀");
}
void Yumeno::galleryConfirmDraw(){
 UI::Show(this,"Assets/UI/CommonConfirmV4.hbwidget.json","galleryconfirm");std::string message;
 if(galleryClosing)message="갤러리의 변경 내용을 저장하고\n타이틀로 돌아갈까요?";else{const auto& row=galleryRecord(gallerySelected);message=row.value("label",std::string())+"\n"+std::to_string(row.value("price",0))+" 코인으로 구입할까요?";}
 UI::SetText(this,"galleryconfirm","CwBody",message);for(int i=0;i<2;i++){UI::SetTexture(this,"galleryconfirm","CwChoice"+std::to_string(i),std::string("Assets/Art/ui/pad_choice_")+(i==galleryConfirmChoice?"on":"off")+".svg");UI::SetOpacity(this,"galleryconfirm",i==0?"CwYes":"CwNo",i==galleryConfirmChoice?1.f:.6f);}
}
int Yumeno::galleryCommit(){
 if(galleryReading)return 0;if(!galleryv4::readable(galleryReadJob))return -1;
 if(gallerySavePhase==0){auto common=galleryHead;if(!common.empty()){common["coins"]=coins;common["gifts"]=gifts;common["giftKnown"]=giftKnown;common["giftNew"]=giftNew;common["pulls"]=pulls;}if(!galleryv4::beginSave(gallerySaveJob,galleryState,galleryRead,std::move(common)))return -1;gallerySavePhase=1;return 0;}
 int result=galleryv4::saveStep(gallerySaveJob);if(gallerySaveJob.phase>=2){galleryHead=gallerySaveJob.canonical;galleryRecoveryBank=gallerySaveJob.writer.package.head;}if(gallerySaveJob.phase>=3)galleryProfileHead=gallerySaveJob.writer.package.head;
 if(result==1){galleryDirty=false;gallerySavePhase=0;gallerySaveJob={};}return result;
}
void Yumeno::galleryClose(){
 if(galleryDirty){galleryClosing=galleryConfirm=true;galleryConfirmChoice=1;galleryArmed=false;galleryConfirmDraw();return;}
 galleryPlaying.clear();UI::Remove(this,"galleryv4");UI::Remove(this,"galleryconfirm");mode=Mode::Title;UI::SetVisible(this,UI_ID,"Title",true);music("bgm_title");titleMenu(true);
}
void Yumeno::galleryView(const std::string& id){
 gallerySelected=id;const auto& row=galleryRecord(id);auto category=row.value("category",std::string());
 if(category=="bgm"){if(galleryv4::view(galleryState,id))galleryDirty=true;if(galleryPlaying==id){galleryPlaying.clear();music("bgm_title");}else{galleryPlaying=id;music(row.at("cue").get<std::string>());}galleryDraw();return;}
 if(category=="artwork"){if(galleryv4::view(galleryState,id))galleryDirty=true;galleryViewer=true;galleryReplay=false;UI::SetTexture(this,"galleryv4","GaViewer",row.at("image").get<std::string>());galleryArmed=false;galleryDraw();return;}
 if(category=="event"||category=="intimacy"){
  if(galleryReading){toast("지난 기록을 준비하고 있어요");return;}
  galleryReplayNodes.clear();for(const auto& node:row.value("nodes",Json::array()))if(galleryRead.count(node.get<std::string>()))galleryReplayNodes.push_back(node.get<std::string>());
  if(galleryReplayNodes.empty()){toast("저장된 열람 기록이 없어요");return;}
  if(galleryv4::view(galleryState,id))galleryDirty=true;galleryReplaySpace=row.value("space",std::string("plaza"));galleryViewer=galleryReplay=true;galleryReplayAt=0;galleryPriorCourt=v4Court;v4Court=false;galleryArmed=false;galleryReplayWorld=world;galleryDraw();galleryReplayShow();return;
 }
}
void Yumeno::galleryReplayShow(){
 if(galleryReplayAt>=int(galleryReplayNodes.size())){galleryViewerClose();return;}
 const auto& node=storyv4::bucketData("Assets/Data/v4_story/nodes/",storyv4::bucket(galleryReplayNodes[galleryReplayAt],128)).at("nodes").at(galleryReplayNodes[galleryReplayAt]);
 auto scene=galleryv4::replayScene(node,v4.flags);auto space=scene.value("space",galleryReplaySpace);if(space=="guest_room")space="story_guest_room";if(galleryReplayWorld.data.contains("instances")&&galleryReplayWorld.data["instances"].contains(space)){if(!galleryReplayWorld.active||galleryReplayWorld.id!=space){galleryReplayWorld.id.clear();exworld::begin(galleryReplayWorld,space,false);}exworld::camera(galleryReplayWorld);exworld::visible(galleryReplayWorld,true);galleryReplaySpace=space;}
 if(node.contains("timeOfDay")){auto phase=node.at("timeOfDay").get<std::string>();exworld::environment(galleryReplayWorld,phase=="night"?1:phase=="evening"?2:0);}
 auto image=node.value("shot",Json::object()).value("image",std::string());UI::SetVisible(this,"galleryv4","GaViewer",!image.empty());if(!image.empty()){UI::SetTexture(this,"galleryv4","GaViewer",image);exworld::visible(galleryReplayWorld,false);}
 if(courtFigures.is_null()||courtFigures.empty())courtFigures=Data::Get("Assets/Data/court.json")["figures"];
 line=node.value("text",std::string());speaker=node.value("mono",false)?std::string():node.value("speaker",std::string());auto actor=node.value("actor",std::string());portrait.clear();auto appearance=node.value("appearanceActor",actor);auto pose=node.value("pose",std::string());auto key=actor=="mio"?dialogueportraitv4::interlocutor(node):(pose.empty()?appearance:pose);if(!key.empty()&&courtFigures.contains(key))portrait=courtFigures[key].value("texture",std::string());else if(actor!="mio"&&courtFigures.contains(appearance))portrait=courtFigures[appearance].value("texture",std::string());else if(actor=="lappy")portrait="Assets/Art/v4/lappy.webp";showLine();if(!image.empty())UI::SetVisible(this,UI_ID,"Portrait",false);shown=float(lineLength);text("Body",dialogueText());UI::SetColor(this,UI_ID,"Body",node.value("mono",false)?Color{.62f,.84f,1,1}:Color{.96f,.94f,.97f,1});dialogVisible(true);
 auto bed=galleryv4::replayMusic(node,Json::object());
 static std::map<int,Json> chapters;int scope=node.value("scope",0);
 for(int ch=0;!bed.first&&ch<=6;ch++)if(scope&(1<<ch)){auto found=chapters.find(ch);if(found==chapters.end())found=chapters.emplace(ch,Data::Get("Assets/Data/v4_story/chapters/"+(ch?std::to_string(ch):std::string("P"))+".json")).first;bed=galleryv4::replayMusic(node,found->second);}
 if(bed.first)music(bed.second.empty()?"@silence":bed.second);
 else if(galleryReplayAt==0&&galleryRecord(gallerySelected).value("category",std::string())=="intimacy")music("bgm_freetime");
 pv4::WorldAmbience(presentationV4,galleryReplayWorld.active&&image.empty(),galleryReplayWorld.active&&galleryReplayWorld.spec().value("outdoor",false));
}
void Yumeno::galleryViewerClose(){
 galleryViewer=false;if(galleryReplay){galleryReplay=false;v4Court=galleryPriorCourt;scenesv4::title();exworld::visible(galleryReplayWorld,false);world.mesh.clear();world.environmentStamp.clear();pv4::StopAmbient(presentationV4);dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);}galleryArmed=false;music("bgm_title");galleryPlaying.clear();galleryDraw();
}
void Yumeno::galleryUpdate(float delta){
 galleryReadTick();if(gallerySaving){int result=galleryCommit();if(result==0)return;gallerySaving=false;if(result<0){gallerySavePhase=0;gallerySaveJob={};toast("저장하지 못했어요. 다시 시도해 주세요");galleryConfirmDraw();return;}galleryConfirm=false;UI::Remove(this,"galleryconfirm");galleryClose();return;}if(!galleryArmed){if(!Input::IsKeyDown("Enter")&&!Input::IsKeyDown("mouse0"))galleryArmed=true;return;}
 bool click=pressed("mouse0"),enter=pressed("Enter"),back=pressed("Escape")||pressed("Backspace")||pressed("mouse1");Vec2 m;Input::GetCenteredMousePositionForCanvas({1280,720},m);static const auto layout=Data::Get("Assets/Data/v4_story/gallery_layout.json");
 auto hit=[&](const Json& r){return m.x>=r[0].get<float>()&&m.x<r[0].get<float>()+r[2].get<float>()&&m.y>=r[1].get<float>()&&m.y<r[1].get<float>()+r[3].get<float>();};
 if(galleryConfirm){
  if(back){galleryConfirm=false;UI::Remove(this,"galleryconfirm");return;}int old=galleryConfirmChoice;if(pressed("a")||pressed("ArrowLeft"))galleryConfirmChoice=0;if(pressed("d")||pressed("ArrowRight"))galleryConfirmChoice=1;
  if(click){static const auto p=Data::Get("Assets/Data/v4_story/system_pages_layout.json");for(int i=0;i<2;i++)if(hit(p["confirm"][i==0?"yes":"no"])){galleryConfirmChoice=i;enter=true;}}
  if(old!=galleryConfirmChoice)galleryConfirmDraw();if(!enter)return;if(galleryConfirmChoice){galleryConfirm=false;UI::Remove(this,"galleryconfirm");return;}
  if(galleryClosing){if(!galleryv4::readable(galleryReadJob)&&!galleryReading){galleryReadJob={};for(const auto& h:std::vector<Json>{galleryHead,galleryHead.value("galleryBank",Json::object()),galleryRecoveryBank,galleryProfileHead})galleryv4::enqueue(galleryReadJob,h);galleryReading=true;}gallerySaving=true;gallerySavePhase=0;gallerySaveJob={};UI::SetText(this,"galleryconfirm","CwBody","갤러리 변경을 저장하고 있어요…");return;}
  const auto& row=galleryRecord(gallerySelected);if(!galleryv4::buy(galleryState,gallerySelected,row.value("price",0),coins,true)){toast("구입할 수 없어요");sfx("ui_cancel");}else{galleryDirty=true;sfx("ui_confirm");}galleryConfirm=false;UI::Remove(this,"galleryconfirm");galleryDraw();return;
 }
 if(galleryViewer){if(back){galleryViewerClose();return;}if(galleryReplay&&(enter||pressed("Space")||click)){if(dialogueAdvance()){++galleryReplayAt;galleryReplayShow();}else{shown=float(lineLength);text("Body",dialogueText());}}else if(!galleryReplay&&(enter||click))galleryViewerClose();return;}
 if(back){sfx("ui_cancel");if(galleryDepth){galleryDepth=0;galleryRow=galleryFirst=0;galleryDraw();}else galleryClose();return;}
 if(galleryDepth==0){int old=galleryTop;if(pressed("w"))galleryTop=(galleryTop+6)%7;if(pressed("s"))galleryTop=(galleryTop+1)%7;if(click)for(int i=0;i<7;i++)if(hit(layout["top"][i])){galleryTop=i;enter=true;}if(old!=galleryTop){sfx("ui_select");galleryDraw();}if(!enter)return;if(galleryTop==6){galleryClose();return;}if(galleryTop==4){if(galleryReading||!galleryv4::readable(galleryReadJob)){toast("지난 기록을 먼저 준비해야 해요");return;}if(!galleryState.machine||galleryHead.empty()){sfx("ui_cancel");toast("본편에서 머신을 확인하고 저장한 뒤 이용할 수 있어요");return;}machineOpen(true);return;}galleryDepth=1;galleryRow=galleryFirst=0;galleryArmed=false;galleryDraw();return;}
 auto rows=galleryRows();if(rows.empty())return;int old=galleryRow;if(pressed("w"))galleryRow=(galleryRow+int(rows.size())-1)%int(rows.size());if(pressed("s"))galleryRow=(galleryRow+1)%int(rows.size());if(pressed("q"))galleryRow=std::max(0,galleryRow-11);if(pressed("e"))galleryRow=std::min(int(rows.size())-1,galleryRow+11);if(click)for(int i=0;i<11;i++)if(hit(layout["rows"][i])&&galleryFirst+i<int(rows.size())){galleryRow=galleryFirst+i;enter=true;}
 if(old!=galleryRow){sfx("ui_select");galleryDraw();}if(!enter)return;auto id=rows[galleryRow];int status=galleryv4::status(galleryState,id);if(!status){sfx("v3se_000");return;}if(status==2){sfx("ui_confirm");galleryView(id);return;}if(galleryReading||!galleryv4::readable(galleryReadJob)){toast("지난 기록을 먼저 준비해야 해요");return;}const auto& row=galleryRecord(id);auto category=row.value("category",std::string());if(category=="event"||category=="intimacy"){if(galleryReading){toast("지난 기록을 준비하고 있어요");return;}bool readable=false;for(const auto& node:row.value("nodes",Json::array()))if(galleryRead.count(node.get<std::string>())){readable=true;break;}if(!readable){toast("열람할 대화 기록이 없어요");return;}}int price=row.value("price",0);if(coins<price){toast("코인이 "+std::to_string(price-coins)+"개 부족해요");sfx("v3se_000");return;}if(price==0){if(galleryv4::buy(galleryState,id,0,coins,true)){galleryDirty=true;galleryView(id);}return;}gallerySelected=id;galleryConfirm=true;galleryClosing=false;galleryConfirmChoice=1;galleryArmed=false;galleryConfirmDraw();
}
