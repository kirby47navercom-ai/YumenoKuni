#include "DialoguePortraitV4.hpp"
// Authored V4 graph interpreter. Legacy flow remains a separate save/content format.
namespace {constexpr const char* V4_UI="v4story";constexpr const char* V4_SAVE="yumeno-progress-v4";}
void Yumeno::titleMenu(bool visible){
 if(visible&&mode==Mode::Title){scenesv4::title();releaseGameplay();world.visible=false;world.active=false;world.mesh.clear();world.environmentStamp.clear();}
 if(visible&&mode==Mode::Title&&machineActive){machineActive=false;UI::Remove(this,"machinev4");}
 if(visible){if(!UI::Mounted("titleshellv4"))UI::Show(this,"Assets/UI/TitleShellV4.hbwidget.json","titleshellv4");if(!UI::Mounted("titlemenuv4"))UI::Show(this,"Assets/UI/TitleMenuV4.hbwidget.json","titlemenuv4");}
 else{UI::Remove(this,"titleshellv4");UI::Remove(this,"titlemenuv4");}
 for(auto id:{"New","Load","TitleOption","NewFocus","LoadFocus"})UI::SetVisible(this,V4_UI,id,false);
 UI::SetVisible(this,"titlemenuv4","root",visible);UI::SetVisible(this,"titleshellv4","TitleLogo",visible);UI::SetVisible(this,"titleshellv4","TitleSub",false);
 if(!visible)return;fvis("FHud",false);UI::SetPosition(this,"titleshellv4","TitleLogo",{650,30});UI::SetSize(this,"titleshellv4","TitleLogo",{580,200});
 titleHasContinue=false;try{auto h=Json::parse(Save::ReadText(campaignv4::slot(V4_SAVE)));titleHasContinue=campaignv4::matches(h)&&!h.value("node",std::string()).empty();}catch(const std::exception&){}
 bool chapters=!chapterEntries.empty()||!trialResults.best.empty();int flags=(titleHasContinue?1:0)|(chapters?2:0);
 UI::SetTexture(this,"titlemenuv4","TmArt","Assets/Art/ui/v3/title_chapter/main_"+std::to_string(std::clamp(titleChoice,0,4))+"_"+std::to_string(flags)+".svg");
 UI::SetText(this,"titlemenuv4","TmGuide","W/S 선택 · Enter 결정 · O 설정");
}
int Yumeno::titleMenuHit(float x,float y)const{
 static const auto layout=Data::Get("Assets/Data/v4_story/title_chapter_layout.json");for(int i=4;i>=0;i--){const auto& r=layout["mainRects"][i];if(x>=r[0].get<float>()&&x<=r[0].get<float>()+r[2].get<float>()&&y>=r[1].get<float>()&&y<=r[1].get<float>()+r[3].get<float>())return i;}return -1;
}
void Yumeno::updateTitle(bool click){
 Vec2 mouse;Input::GetMousePositionForCanvas({1280,720},mouse);int old=titleChoice;bool moved=mouse.x!=titleMouseX||mouse.y!=titleMouseY;titleMouseX=mouse.x;titleMouseY=mouse.y;
 int hit=titleMenuHit(mouse.x,mouse.y);if(moved&&hit>=0)titleChoice=hit;
 if(pressed("w")||pressed("ArrowUp"))titleChoice=(titleChoice+4)%5;if(pressed("s")||pressed("ArrowDown"))titleChoice=(titleChoice+1)%5;
 if(old!=titleChoice){sfx("ui_select");titleMenu(true);}int action=-1;if(pressed("o"))action=3;else if(pressed("c"))action=1;else if(enterNow||pressed("Space"))action=titleChoice;else if(click&&hit>=0)action=hit;
 if(action<0)return;if(action==1&&!titleHasContinue){sfx("v3se_000");return;}if(action==2&&chapterEntries.empty()&&trialResults.best.empty()){sfx("v3se_000");return;}sfx("ui_confirm");
 if(action==4){galleryOpen();return;}if(action==3){titleMenu(false);optv4::Open(optionsV4);return;}if(action==2){chapterSelectOpen();return;}
 if(action==1){if(v4Load()){titleMenu(false);UI::SetVisible(this,UI_ID,"Title",false);}else toast("저장을 읽지 못했어요. 시스템의 다른 저장을 확인해 주세요");return;}
 difficultyOpen();
}
void Yumeno::v4Start(const std::string& chapterId,bool reset,bool revisionPreview,const std::string& previewCheckpoint,bool showStartCard){
 auto graph=Data::Get(campaignv4::chapterPath(chapterId,revisionPreview));
 if(!storyv4::valid(graph)||graph.value("campaignRevision",std::string())!=(revisionPreview?campaignv4::Revision:"")){lastError="Invalid authored graph: "+chapterId;return;}
 auto checkpoint=Json::object();
 if(revisionPreview&&!previewCheckpoint.empty()){
  checkpoint=graph.at("qaCheckpoints").at(previewCheckpoint);
  if(!storyv4::has(graph,checkpoint.at("entry").get<std::string>())){lastError="Invalid preview checkpoint: "+previewCheckpoint;return;}
 }
 trialEntryTime=-1.f;UI::Remove(this,"trialentryv4");
 prepareGameplay();
 machineActive=false;UI::Remove(this,"machinev4");
 if(v4TaskActive||v4Court)v4LeaveTrial();
 if(reset||growthV4.contract.empty())growthv4::Init(growthV4,Data::Get(campaignv4::growthPath(revisionPreview)),skillData);
 auto priorFlags=v4.flags;auto priorLog=v4.log;auto priorEvidence=v4.evidence;auto priorRead=v4.read;
 v4PendingTaskResume=Json::object();v4GiftMode=0;v4FreeAccepted=false;v4FreeNode.clear();v4LastOutcome=Json::object();v4HubNode.clear();v4Court=false;v4TaskActive=v4QueueActive=false;v4Task=Json::object();
 v4=storyv4::State{};v4.graph=graph;v4.active=true;storyv4::jump(v4,checkpoint.value("entry",graph.at("entry").get<std::string>()));
 if(!reset){v4.flags=priorFlags;v4.log=priorLog;v4.evidence=priorEvidence;v4.read=priorRead;}
 else{trialResults={};exploreReactions.clear();reactionWorld.clear();reactionAt=-1;coins=10;pulls=0;bonds.clear();gifts.clear();giftKnown.clear();giftNew.clear();cards.clear();flags.clear();seen.clear();notes.clear();playerProgress={};trialAnswerContext.clear();trialAnswerConfirmed.assign(4,false);trialAnswerOn=false;v4Documents=Json::object();world.history.clear();world.active=false;world.id.clear();world.space.clear();pv4::Clear(presentationV4,true,true);}
 for(const auto& card:checkpoint.value("evidence",Json::array())){
  const auto id=card.at("id").get<std::string>();cards.insert(id);v4.evidence[id]={{"name",card.at("name")},{"text",card.at("text")}};
 }
 flowOn=false;after=After::None;ctxPool=ctxSpot=ctxEnding=-1;rooms.clear();hotspots.clear();lastError.clear();
 chapterAt=chapterId=="P"?0:std::stoi(chapterId);chapter=Json{{"chapter",chapterId},{"gone",Json::array()}};
 playerProgress.phase=std::clamp(graph.value("entryHudPhase",0),0,2);playerProgress.context=graph.value("kind",std::string())=="freetime"?"extra":"chapter";
 hideExplore();hideFlow();titleMenu(false);v4Log(false);
 UI::SetVisible(this,UI_ID,"Title",false);UI::SetVisible(this,UI_ID,"Trial",false);UI::SetVisible(this,UI_ID,"CourtDim",false);
 exworld::load(world);
 if(showStartCard&&chapterAt<6){v4ShowChapterCard(ChapterCard::Start);return;}
 auto cue=graph.value("presentation",Json::object()).value("entryMusic",std::string());if(!cue.empty())music(cue);
 v4Enter();
}
static std::string upcomingPanicTask(const hb::Json& graph,const hb::Json& n){
 auto next=n.value("next",std::string());
 for(int beats=0,steps=0;!next.empty()&&beats<3&&steps<12;++steps){
  if(!storyv4::has(graph,next))break;
  const auto& tail=storyv4::lookup(graph,next);
  const auto type=tail.value("type",std::string());
  if(type=="task"){
   const auto task=tail.value("taskId",std::string());
   const auto& tasks=storyv4::bucketData(graph.value("taskBucketPrefix",std::string("Assets/Data/v4_story/native_tasks/")),storyv4::bucket(task,64)).at("tasks");
   if(tasks.contains(task)&&tasks.at(task).at("stage").value("kind",std::string())=="panic")return task;
   break;
  }
  if(type=="say")++beats;
  else if(type!="stage"||tail.value("showRecord",false))break;
  next=tail.value("next",std::string());
 }
 return {};
}
void Yumeno::v4SelectCourtScene(){
 const auto& entry=v4.current();
 const auto type=entry.value("type",std::string());
 scenesv4::courtMode="Court";
 if(type=="task"){
  const auto task=entry.value("taskId",std::string());
  const auto& bundle=storyv4::bucketData(v4.graph.value("taskBucketPrefix",std::string("Assets/Data/v4_story/native_tasks/")),storyv4::bucket(task,64))["tasks"].at(task);
  scenesv4::courtMode=scenesv4::trialMode(bundle.at("stage").value("kind",std::string()));
 }else if(v4Court&&(type=="say"||(type=="stage"&&!entry.value("showRecord",false)))&&!upcomingPanicTask(v4.graph,entry).empty()){
  scenesv4::courtMode="CourtPanic";
 }
}
void Yumeno::v4ShowChapterCard(ChapterCard kind){
 v4CardKind=kind;
 v4CardArmed=false;
 mode=Mode::Card;
 hideFlow();
 hideExplore();
 dialogVisible(false);
 UI::SetVisible(this,UI_ID,"Portrait",false);
 fvis("FHud",false);
 pv4::StopAmbient(presentationV4);
 fvis("FCardBack",true);
 const auto ch=v4.graph.at("chapter").get<std::string>();
 const auto image=artPath("cards","chapter_"+ch,"ui",".webp");
 const bool titleCard=kind==ChapterCard::Start||(kind==ChapterCard::Investigation&&chapterAt==6);
 if(titleCard&&!image.empty()){
  UI::SetTexture(this,flowui::ID,"FCard",image);
  fvis("FCard",true);
 }else{
  ftext("FCardT",chapterAt==0?std::string("프롤로그"):"제"+ch+"장");
  ftext("FCardS",kind==ChapterCard::End?"끝":kind==ChapterCard::Investigation?"수사":"");
  fvis("FCardT",true);
  fvis("FCardS",kind!=ChapterCard::Start);
 }
 // Asset IDs are retained for compatibility. The supplied tracks are A, B and C.
 const char* cue="jingle_chapter";
 if(!titleCard)cue=kind==ChapterCard::Investigation||chapterAt==0?"jingle_chapter_end":"jingle_chapter_p";
 playCue(cue);
}
void Yumeno::v4Enter(bool restoring){
 v4SelectCourtScene();
 if(v4Court&&!scenesv4::courtReady())return;
 if(trialEntryTime>=0){mode=Mode::Story;dialogVisible(false);return;}
 hideMenu();for(auto id:{"DocumentShade","DocumentPaper","DocumentTitle","DocumentBody","DocumentHint"})UI::SetVisible(this,V4_UI,id,false);
 mode=Mode::Story;dialogVisible(true);UI::SetVisible(this,UI_ID,"Backdrop",false);UI::SetVisible(this,UI_ID,"Background",false);
 exworld::visible(world,world.active&&!v4Court);
 fvis("FHud",!v4Court);hud();
 for(int reductions=0;reductions<256;reductions++){
  const auto& n=storyv4::enter(v4);auto kind=n.value("type","");v4PresentScene(n);if(scenesv4::waiting())return;if(kind=="say")galleryRecordNode(n);if(!v4.blocked.empty())break;
  const bool authoredCourt=n.contains("source")&&n["source"].value("file",std::string()).rfind("1"+v4.graph.value("chapter",std::string())+"c",0)==0;
  if(!v4Court&&(authoredCourt||n.value("enterCourt",false))&&v4.graph.contains("trialRoster")){
   trialDead=v4.graph["trialRoster"].value("dead",std::vector<std::string>{});v4BeginCourt();exworld::visible(world,false);setupCourt();fvis("FHud",false);
   if(!restoring){trialEntryTime=0;trialPrepRow=0;dialogVisible(false);return;}
   if(scenesv4::waiting())return;
  }
  if(!restoring&&campaignv4::canSave(v4.graph))chapterArchiveObserve(n);
  if(n.contains("source")){
   auto section=n["source"].value("file","")+":"+n["source"].value("location","");
   if(section!=v4.section){v4.section=section;
    auto p=v4.graph.value("presentation",Json::object());
    if(!restoring&&p.contains("sectionBeds")&&p["sectionBeds"].contains(section))music(p["sectionBeds"][section].value("music",std::string()));
   }
  }
  if(!restoring)pv4::Apply(presentationV4,n,v4.generation);
  if(kind=="branch"||kind=="call"||kind=="return"){
   if(!storyv4::route(v4))break;if(kind=="return")v4ObserveGrowth();continue;
  }
  if(kind=="stage"){
   if(!restoring&&n.value("growthEncounter",false))v4ObserveGrowth();
   v4CaptureRecords(n);if(n.value("showRecord",false)){const auto& record=n["publicRecords"][0];std::string rows;for(const auto& row:record["rows"]){if(!rows.empty())rows+="\n\n";rows+=row.get<std::string>();}v4ShowDocument(record.value("title",std::string()),rows);return;}
   if(n.value("holdSeconds",0.f)>0){
    v4ShotTime=0;dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);
    if(!restoring&&!n.value("shotCue",std::string()).empty())sfx(n.at("shotCue").get<std::string>());
    return;
   }
   // Direction strings are production instructions, never dialogue or answer narration.
   // Explicit scene/action bindings are separate from the authored route graph.
   ++v4.shownStages;
   const auto target=n.value("next",std::string());
   if(n.contains("comicPage")&&!climaxEndDoneV4&&!target.empty()&&!storyv4::lookup(v4.graph,target).contains("comicPage")){climaxEndDoneV4=true;beginModeEnding("climax","story-node",target);return;}
   if(!storyv4::jump(v4,target))break;continue;
  }
  if(kind=="say"){
   speaker=n.value("mono",false)?"":n.value("speaker","");line=n.value("text","");portrait.clear();
   auto slug=n.value("actor","");auto appearance=n.value("appearanceActor",slug);auto pose=n.value("pose","");std::string key=pose.empty()?appearance:pose;
   auto displayed=slug;
   if(!v4Court&&slug=="mio"){displayed=dialogueportraitv4::interlocutor(n);if(!displayed.empty()){appearance=displayed;key=dialogueportraitv4::poseKey(n,displayed);}}
   else if(!v4Court&&pose.empty())key=dialogueportraitv4::poseKey(n,appearance);
   if(displayed!="mio"&&!displayed.empty()){
    if(courtFigures.is_null()||courtFigures.empty())courtFigures=Data::Get("Assets/Data/court.json")["figures"];
    if(courtFigures.contains(key))portrait=courtFigures[key].value("texture",std::string());
    else if(courtFigures.contains(appearance))portrait=courtFigures[appearance].value("texture",std::string());
    else if(slug=="lappy")portrait="Assets/Art/v4/lappy.webp";
   }
   UI::SetColor(this,UI_ID,"Body",n.value("mono",false)?Color{.62f,.84f,1,1}:Color{.96f,.94f,.97f,1});
   showLine();if(n.contains("comicPage"))v4ComicComplete(true);if(!v4RenderedCg.empty())UI::SetVisible(this,UI_ID,"Portrait",false);if(v4Court){UI::SetVisible(this,UI_ID,"Portrait",false);if(!slug.empty()&&!n.value("mono",false))focusSpeaker(slug,key);}
   // 한국어판 V3(Uba6XjXj8OU 2934.6~2938초) : 반론 쇼다운으로 넘어가는 상대의 반론 대사는 그 상대의 「반론」 컷인 → 초록 깨짐 뒤에 나온다
   if(v4Court&&!restoring&&!slug.empty())try{const auto& nx=storyv4::lookup(v4.graph,n.value("next",std::string()));if(nx.value("type",std::string())=="task"){auto task=nx.value("taskId",std::string());const auto& tasks=storyv4::bucketData(v4.graph.value("taskBucketPrefix",std::string("Assets/Data/v4_story/native_tasks/")),storyv4::bucket(task,64))["tasks"];
    if(tasks.contains(task)&&tasks[task]["stage"].value("kind",std::string())=="showdown"&&tasks[task]["stage"].value("showdownV4",Json::object()).value("opponent",std::string())==slug){sdCutinSlug=slug;sdStoryCut=0;sdIntroPrev=-1;UI::Show(this,"Assets/UI/ShowdownV3.hbwidget.json","sdv3");dialogVisible(false);}}}catch(const std::exception&){}
   optv4::BeginLine(optionsV4,v4.node,v4.read.count(v4.node)>0);
   if(!restoring){v4.log.push_back({{"id",v4.node},{"speaker",n.value("speaker","")},{"actor",slug},{"mono",n.value("mono",false)},{"text",line}});if(v4.log.size()>2000)v4.log.erase(v4.log.begin());}
   return;
  }
  if(kind=="menu"){
   v4MenuPage=0;v4Menu();return;
  }
  if(kind=="document"||kind=="evidence"){
   if(kind=="document")v4Documents[v4.node]={{"title",n.value("title",std::string())},{"rows",n.value("rows",Json::array())},{"private",n.value("private",false)},{"image",n.value("image",std::string())}};
   dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);
   std::string rows,title=n.value("title","");
   if(kind=="evidence"){
    auto id=n.value("evidenceId",std::string());if(id.empty()){v4.blocked="Evidence has no authored ID";break;}
    if(n.value("revision",false)&&!v4.evidence.contains(id)){v4.blocked="Cannot revise an unacquired evidence ID: "+id;break;}
    bool fresh=!v4.evidence.contains(id);v4.evidence[id]={{"name",n.value("name",id)},{"text",n.value("text",std::string())}};cards.insert(id);
    title=(n.value("revision",false)?"언령 갱신 · ":"언령 획득 · ")+n.value("name",id);rows=n.value("text",std::string());
    auto action=n.value("revision",false)?"evidence_revised":"evidence_acquired";bool hasAction=false;
    if(n.contains("presentation")&&n["presentation"].contains("actions"))for(auto& a:n["presentation"]["actions"])if(a==action)hasAction=true;
    if(!hasAction&&!restoring&&(fresh||n.value("revision",false)))pv4::Action(presentationV4,action);
   }else for(auto& r:n["rows"]){if(!rows.empty())rows+="\n\n";rows+=r.get<std::string>();}
   v4ShowDocument(title,rows,n.value("image",std::string()));
   return;
  }
  if(kind=="end"){
   if(v4.graph.contains("campaignRevision")&&!campaignv4::canSave(v4.graph)){
    if(n.value("chapterComplete",false)&&n.contains("nextChapter")){v4Start(n["nextChapter"].get<std::string>(),false,true);return;}
    if(v4Court)v4LeaveTrial();toTitle();return;
   }
   if(n.contains("xpReward"))playerClaim(n["xpReward"].value("kind",std::string()),n["xpReward"].value("id",std::string()));
   if(n.value("trialResultAtEnd",false)){
    const auto resultChapter=v4.graph.at("chapter").get<std::string>();
    if(trialResults.current.chapter!=resultChapter)resultv4::begin(trialResults,resultChapter);
    if(!trialResults.current.paid){trialResultStart();return;}
   }
   if(n.value("chapterComplete",false)&&n.contains("nextChapter")){
    if(restoring)v4Start(n["nextChapter"].get<std::string>(),false,v4.graph.contains("campaignRevision"));
    else v4ShowChapterCard(ChapterCard::End);
    return;
   }
   if(n.value("campaignNarrativeEnd",false)){if(restoring)v4Credits();else v4EndingBegin();return;}
   v4.blocked="Authored ending is not connected";break;
  }
  if(kind=="gate"){v4.blocked=n.value("reason","Unresolved authored route");break;}
  if(kind=="investigate"){
   static const std::array<std::string_view,6> investigationEntries{
    "v4:1:investigate:I-02","v4:2:investigate:I2-03","v4:3:investigate:I3-05-rule",
    "v4:4:investigate:I4-02-file","v4:5:investigate:I02-05","v4:6:investigate:I6-01-02"
   };
   const bool firstHub=v4.graph.contains("campaignRevision")
      ? campaignv4::canSave(v4.graph)&&n.value("chapterEntryType",-1)==2
      : chapterAt>=1&&chapterAt<=6&&v4.node==investigationEntries[chapterAt-1];
   if(firstHub&&v4.flags.value("audio:investigation-card",std::string())!=v4.node){
    v4.flags["audio:investigation-card"]=v4.node;
    if(!restoring){v4ShowChapterCard(ChapterCard::Investigation);return;}
   }
   v4Investigate();
   return;
  }
  if(kind=="task"){try{v4TaskStart();return;}catch(const std::exception& e){v4.blocked=e.what();break;}}
  v4.blocked="Unsupported authored node: "+kind;break;
 }
 if(v4.blocked.empty())v4.blocked="Authored routing exceeded 256 automatic nodes";
 lastError="V4 route gate: "+v4.blocked;dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);
}
void Yumeno::v4Update(float delta,bool next,bool click){
 if(mode==Mode::Card){
  if(!v4CardArmed){
   v4CardArmed=!Input::IsKeyDown("Enter")&&!Input::IsKeyDown("Space")&&!Input::IsKeyDown("mouse0");
   return;
  }
  if(jingleTimer>0&&!next)return;
  stopJingle();
  hideFlow();
  mode=Mode::Story;
  if(v4CardKind==ChapterCard::End){
   const auto nextChapter=v4.current().at("nextChapter").get<std::string>();
   v4Start(nextChapter,false,v4.graph.contains("campaignRevision"),"",true);
  }else if(v4CardKind==ChapterCard::Investigation){
   v4Investigate();
  }else{
   const auto cue=v4.graph.value("presentation",Json::object()).value("entryMusic",std::string());
   if(!cue.empty())music(cue);
   v4Enter();
  }
  return;
 }
 if(modeEndingInput(delta))return;
 if(v4Court)updateCamera(delta);
 if(trialEntryTime>=0){
  if(!UI::Mounted("trialentryv4")){
   UI::Show(this,"Assets/UI/TrialEntryV4.hbwidget.json","trialentryv4");
   dialogVisible(false);
   courtWide();
   // V3's six opening scripts request BGM032 immediately before modBriefing.
   music("bgm_elevator");
  }
  if(trialEntryTime>0){
   trialEntryTime=std::max(.001f,trialEntryTime-delta);
   const float opacity=std::clamp(std::min((1.6f-trialEntryTime)*6.f,trialEntryTime*4.f),0.f,1.f);
   UI::SetOpacity(this,"trialentryv4","Opening",opacity);
   if(trialEntryTime<=.001f){trialEntryTime=-1;UI::Remove(this,"trialentryv4");v4Enter();}
   return;
  }
  if(pressed("w")||pressed("ArrowUp")){trialPrepRow=(trialPrepRow+2)%3;sfx("ui_select");}
  if(pressed("s")||pressed("ArrowDown")){trialPrepRow=(trialPrepRow+1)%3;sfx("ui_select");}
  if(click){
   Vec2 cursor;Input::GetMousePositionForCanvas({1280,720},cursor);
   if(cursor.x>=770&&cursor.x<1160&&cursor.y>=285&&cursor.y<477)trialPrepRow=int((cursor.y-285)/64);
   else next=false;
  }
  for(int i=0;i<3;++i)UI::SetOpacity(this,"trialentryv4","PrepChoice"+std::to_string(i),i==trialPrepRow?1.f:.58f);
  if(next){
   if(trialPrepRow==0){
    trialEntryTime=1.6f;
    UI::SetVisible(this,"trialentryv4","Prep",false);
    UI::SetVisible(this,"trialentryv4","Opening",true);
    UI::SetOpacity(this,"trialentryv4","Opening",0.f);
    sfx("v3se_374");
   }else{
    UI::SetVisible(this,"trialentryv4","root",false);
    padToggle();
    padPageAt=trialPrepRow==1?1:3;
    padShowPage();
    if(trialPrepRow==2){UI::Remove(this,"padreport");padReportVisible=false;padSkillRow=0;padSkillDraw();}
   }
  }
  return;
 }
 if(sdStoryCut>=0){sdStoryCut+=std::min(delta,.1f);v4ShowdownIntro(sdStoryCut);if(sdStoryCut<2.6f)return;sdStoryCut=-1;sdFromStory=true;UI::Remove(this,"sdv3");dialogVisible(true);return;} /* 「반론」 컷인이 걷히면 그 반론 대사 */
 if(v4GiftUpdate(delta,next,click))return;
 if(v4LogOpen){v4LogUpdate(click);return;}
 if(pressed("l")){v4Log(true);return;}
 if(!v4.blocked.empty())return;
 const auto& n=v4.current();auto kind=n.value("type","");
 if(kind=="stage"&&n.value("holdSeconds",0.f)>0){
  const float duration=n.at("holdSeconds").get<float>();
  v4ShotTime=std::min(duration,v4ShotTime+delta);
  const float scale=1.f+std::clamp(n.value("shotPush",0.f),0.f,.1f)*court::smooth5(v4ShotTime/duration);
  UI::SetPosition(this,UI_ID,"Background",{640*(1-scale),360*(1-scale)});UI::SetSize(this,UI_ID,"Background",{1280*scale,720*scale});
  if(v4ShotTime>=duration&&storyv4::jump(v4,n.value("next","")))v4Enter();
  return;
 }
 if(kind=="end"&&n.value("campaignNarrativeEnd",false)){v4CreditsTime+=delta;if(next&&v4CreditsTime>=1.5f)toTitle();return;}
 if(kind=="investigate"||v4FreeWorld()){v4WorldUpdate(delta,click);return;}
 if(kind=="menu"){
  if(pressed("g")){v4GiftOpen();return;}if(pressed("c")){v4GiftOpen(true);return;}
  int picked=-1,old=menuHover;Vec2 m;Input::GetMousePositionForCanvas({1280,720},m);
  if(pressed("w")||pressed("ArrowUp"))menuHover=(menuHover+menuCount-1)%menuCount;
  if(pressed("s")||pressed("ArrowDown"))menuHover=(menuHover+1)%menuCount;
  if(menuHover!=old)pv4::Action(presentationV4,"ui_focus");
  for(int i=0;i<menuCount;i++)if(pressed(std::to_string(i+1)))picked=i;
  if(enterNow)picked=menuHover;if(click)picked=menuAt(m.x,m.y);
  if(picked>=0)menuAccept(picked,1);return;
 }
 if(kind=="document"||kind=="evidence"||(kind=="stage"&&n.value("showRecord",false))){
  if(pressed("Backspace")||pressed("ArrowLeft")||pressed("ArrowUp")){if(documentV4.back()){pv4::Action(presentationV4,"page_turn");v4DocumentDraw();}return;}
  bool forward=pressed("ArrowRight")||pressed("ArrowDown");
  if(next||forward){if(documentV4.next()){pv4::Action(presentationV4,"page_turn");v4DocumentDraw();return;}if(!next)return;if(kind=="evidence")playerClaim("GetKotodama","evidence-out:"+v4.node+":"+std::to_string(v4.generation));storyv4::jump(v4,n.value("next",""));v4Enter();}return;
 }
 if(kind!="say")return;
 shown=std::min(float(lineLength),shown+delta*optv4::CharactersPerSecond(optionsV4));text("Body",u8prefix(dialogueText(),int(shown)));
 UI::SetVisible(this,UI_ID,"Next",int(shown)>=lineLength);
 bool skip=optv4::CanSkip(optionsV4,Input::IsKeyDown("Control"));if(skip){skipTimer+=delta;if(skipTimer>.05f){skipTimer=0;next=true;shown=float(lineLength);}}
 if(optv4::ReportRead(optionsV4,int(shown)>=lineLength&&dialogueFinal())){v4.read.insert(v4.node);v4CaptureRecords(n);}
 if(optv4::AutoAdvance(optionsV4,delta,int(shown)>=lineLength))next=true;
 if(next&&dialogueAdvance()){v4CaptureRecords(n);auto target=n.value("next",std::string());if(n.contains("comicPage")&&!climaxEndDoneV4&&!target.empty()&&!storyv4::lookup(v4.graph,target).contains("comicPage")){climaxEndDoneV4=true;beginModeEnding("climax","story-node",target);return;}if(storyv4::jump(v4,target))v4Enter();}
}
void Yumeno::v4Log(bool open){
 if(v4DocumentOpen()){if(open)v4DocumentVisible(false);else if(mode==Mode::Story)v4DocumentDraw();}
 if(open&&comicShown)UI::SetVisible(this,"comicv4","root",false);
 if(!open){if(v4LogOpen)UI::Remove(this,"backlogv4");v4LogOpen=false;if(padSystemLog){padSystemLog=false;padSystemDraw();}if(mode==Mode::Trial&&v4TaskActive){v4CancelInput();v4TaskRoot(!v4QueueActive);if(playingDebate&&!v4QueueActive)debateHud(true);if(v4QueueAfter=="success"&&!v4ComicPage.empty())v4ComicComplete(true);}else if(v4.active&&v4.current().contains("comicPage"))v4ComicComplete(true);return;}
 v4LogOpen=true;v4LogRow=std::max(0,int(v4.log.size())-4);v4LogCursor=std::max(0,int(v4.log.size())-1);pv4::Action(presentationV4,"page_turn");v4LogRender();
}
void Yumeno::v4LogRender(){
 UI::Remove(this,"backlogv4");UI::Show(this,"Assets/UI/BacklogV4.hbwidget.json","backlogv4");
 for(int i=0;i<4;i++){
  int row=v4LogRow+i;bool on=row<int(v4.log.size());auto suffix=std::to_string(i);
  for(auto p:{"BlPlate","BlName","BlViewport","BlFace"})UI::SetVisible(this,"backlogv4",std::string(p)+suffix,on);
  if(!on)continue;
  const auto& r=v4.log[row];auto who=r.value("actor",std::string());UI::SetText(this,"backlogv4","BlName"+suffix,r.value("speaker",std::string())+(r.value("mono",false)?"（독백）":""));
  auto formatted=padsystem::wrap(r.value("text",std::string()));UI::SetText(this,"backlogv4","BlBody"+suffix,formatted.first);UI::SetSize(this,"backlogv4","BlBody"+suffix,{880,std::max(100.f,formatted.second*39.f)});
  bool known=false;for(auto actor:padui::REPORTERS)if(who==actor)known=true;
  UI::SetVisible(this,"backlogv4","BlFace"+suffix,known||who=="lappy");if(known||who=="lappy")UI::SetTexture(this,"backlogv4","BlFace"+suffix,who=="lappy"?"Assets/Art/v4/lappy.webp":"Assets/Art/student_ids/thumb/"+who+".webp");
  for(auto p:{"BlName","BlBody","BlFace"})UI::SetOpacity(this,"backlogv4",std::string(p)+suffix,row==v4LogCursor?1.f:.6015625f);
 }
}
bool Yumeno::v4LogUpdate(bool click){
 if(!v4LogOpen)return false;if(pressed("Backspace")||pressed("mouse1")||pressed("l")||pressed("Escape")){v4Log(false);return true;}
 int old=v4LogCursor,total=int(v4.log.size());if(pressed("w")||pressed("ArrowUp"))--v4LogCursor;if(pressed("s")||pressed("ArrowDown"))++v4LogCursor;if(pressed("q"))v4LogCursor-=4;if(pressed("e"))v4LogCursor+=4;v4LogCursor=std::clamp(v4LogCursor,0,std::max(0,total-1));
 if(click){Vec2 m;Input::GetMousePositionForCanvas({1280,720},m);const auto pages=Data::Get("Assets/Data/v4_story/system_pages_layout.json");for(int i=0;i<4;i++)if(v4LogRow+i<total&&padsystem::hit(m,pages["backlog"]["rows"][i]["body"]))v4LogCursor=v4LogRow+i;}
 if(v4LogCursor<v4LogRow)v4LogRow=v4LogCursor;if(v4LogCursor>=v4LogRow+4)v4LogRow=v4LogCursor-3;if(old!=v4LogCursor)v4LogRender();return true;
}
hb::Json Yumeno::v4Snapshot(){
 auto s=storyv4::save(v4);s["difficulty"]=difficultyv4::save(difficultyV4);s["gallery"]=galleryv4::save(galleryState);if(!galleryRecoveryBank.empty())s["galleryBank"]=galleryRecoveryBank;else if(!galleryProfileHead.empty())s["galleryBank"]=galleryProfileHead;if(machineActive&&!machineFromGallery)s["machine"]=machinev4::save(machineV4);s["coins"]=coins;s["pulls"]=pulls;s["bonds"]=bonds;s["gifts"]=gifts;s["giftKnown"]=giftKnown;s["giftNew"]=giftNew;s["cards"]=cards;s["world"]=exworld::save(world);s["worldId"]=world.id;s["court"]={{"active",v4Court},{"dead",trialDead},{"hearts",debate.hearts},{"hp",v4TaskHp()},{"focus",debate.focus},{"maxHearts",maxHearts},{"retries",retries},{"correct",correctCount},{"reviveUsed",reviveUsed},{"sdGuardUsed",sdGuardUsed},{"missGuardUsed",missGuardUsed}};
 if(v4TaskActive&&v4QueueActive&&v4QueueAfter=="success")s["taskResume"]={{"phase","success"},{"node",v4.node},{"taskId",v4Task.value("taskId",std::string())},{"judgment",v4Judgment}};s["exploreReactions"]=reactionv4::save(exploreReactions);s["trialResults"]=resultv4::save(trialResults);s["trialResultOpen"]=trialResultOn&&!trialResultHistory;s["trialChoice"]={{"context",trialAnswerContext},{"confirmed",trialAnswerConfirmed}};s["playerProgress"]=playerprogress::save(playerProgress);s["documents"]=v4Documents;s["growth"]=growthv4::Save(growthV4);s["presentation"]=pv4::Save(presentationV4,musicCue,jingleTimer>0?jingleNext:"");return s;
}
void Yumeno::v4Credits(){
 scenesv4::title();
 if(musicCue.empty())music("bgm_night");
 hideFlow();hideExplore();fvis("FHud",false);dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);pv4::StopAmbient(presentationV4);mode=Mode::Credits;v4CreditsTime=0;fvis("FShade",true);fvis("FToast",false);ftext("FCredits","유메노쿠니\n\n기획 · 세계관\n주인님\n\n제작\nCodex\n\n엔진\nHBEngine");fvis("FCredits",true);
}
void Yumeno::v4EndingBegin(){
 hideFlow();hideExplore();fvis("FHud",false);dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);pv4::StopAmbient(presentationV4);mode=Mode::Story;fvis("FShade",true);fvis("FCredits",false);toastTimer=0;ftext("FToast","진행을 저장하고 있어요");fvis("FToast",true);
 v4EndingSavePending=savev4::begin(v4EndingWriter,campaignv4::slot(V4_SAVE),v4Snapshot());
 if(!v4EndingSavePending){v4.blocked=lastError="마지막 진행을 저장하지 못했어요. 이전 저장은 유지돼요.";ftext("FToast",lastError);}
}
void Yumeno::v4EndingTick(){
 const int result=savev4::step(v4EndingWriter);if(result==0)return;
 v4EndingSavePending=false;v4EndingWriter={};
 if(result<0){v4.blocked=lastError="마지막 진행을 저장하지 못했어요. 이전 저장은 유지돼요.";ftext("FToast",lastError);return;}
 v4Credits();
}
bool Yumeno::v4Save(){
 if(!v4.active||!v4.blocked.empty()||!campaignv4::canSave(v4.graph))return false;try{return savev4::write(campaignv4::slot(V4_SAVE),v4Snapshot());}catch(const std::exception&){return false;}
}
bool Yumeno::v4Load(const std::string& slot,bool archiveReplay){
 prepareGameplay();
 try{
  auto s=savev4::read(slot.empty()?campaignv4::slot(V4_SAVE):slot);if(!campaignv4::matches(s))return false;
  auto ch=s.value("chapter","");if(ch!="P"&&(ch.size()!=1||ch[0]<'1'||ch[0]>'6'))return false;
  if(archiveReplay){
   // Preserve earned inventory and global read history, never future story flags.
   chapterarchive::mergeReplay(s,chapterReplay);
   auto scores=trialResults;resultv4::begin(scores,ch);s["trialResults"]=resultv4::save(scores);s["trialResultOpen"]=false;s.erase("taskResume");
  }
  auto g=Data::Get(campaignv4::chapterPath(ch,campaignv4::installed()));storyv4::State next;if(!storyv4::restore(next,g,s))return false;
  auto nextBonds=s.value("bonds",std::map<std::string,int>{}),nextGifts=s.value("gifts",std::map<std::string,int>{});int nextCoins=s.value("coins",0);if(nextCoins<0)return false;
  difficultyv4::State nextDifficulty;if(!difficultyv4::restore(nextDifficulty,s.value("difficulty",Json())))return false;if(archiveReplay)nextDifficulty=difficultyV4;
  reactionv4::State nextReactions;if(!reactionv4::restore(nextReactions,s.value("exploreReactions",Json())))return false;
  resultv4::State nextResults;if(!resultv4::restore(nextResults,s.value("trialResults",Json())))return false;bool nextResultOpen=s.value("trialResultOpen",false);if(nextResultOpen&&(!nextResults.current.paid||nextResults.current.chapter!=ch||s.contains("taskResume")))return false;
  playerprogress::State nextPlayer;if(!playerprogress::restore(nextPlayer,s.value("playerProgress",Json())))return false;
  std::string nextChoiceContext;std::vector<bool> nextChoiceConfirmed;if(!trialanswer::restore(s.value("trialChoice",Json::object()),nextChoiceContext,nextChoiceConfirmed))return false;
  auto nextGiftKnown=s.value("giftKnown",std::set<std::string>{}),nextGiftNew=s.value("giftNew",std::set<std::string>{});for(const auto& [id,qty]:nextGifts)nextGiftKnown.insert(id);for(const auto& id:nextGiftNew)if(!nextGiftKnown.count(id))return false;
  auto pending=s.value("taskResume",Json::object());if(!pending.is_object())return false;if(!pending.empty()){auto judgment=pending.value("judgment",std::string());if(pending.value("phase",std::string())!="success"||pending.value("node",std::string())!=next.node||next.current().value("type",std::string())!="task"||pending.value("taskId",std::string())!=next.current().value("taskId",std::string())||(judgment!="refute"&&judgment!="agree"&&judgment!="lie"))return false;}
  auto nextDocuments=s.value("documents",Json::object());if(!nextDocuments.is_object()||nextDocuments.size()>128)return false;for(auto& [id,d]:nextDocuments.items()){if(!d.is_object()||!d.contains("title")||!d["title"].is_string()||!d.contains("rows")||!d["rows"].is_array()||(d.contains("private")&&!d["private"].is_boolean())||(d.contains("image")&&!d["image"].is_string()))return false;for(auto& row:d["rows"])if(!row.is_string())return false;}
  growthv4::State nextGrowth;growthv4::Init(nextGrowth,Data::Get(campaignv4::growthPath(campaignv4::installed())),skillData);if(s.contains("growth")){if(!growthv4::Restore(nextGrowth,s["growth"],playerprogress::level(nextPlayer),ch=="P"?0:std::stoi(ch)))return false;}else growthv4::Observe(nextGrowth,next.flags,nextBonds,nextCoins,false);
  for(const auto& receipt:nextGrowth.giftReceipts)nextGiftKnown.insert(receipt.value("giftId",std::string()));
  galleryv4::State nextGallery;if(!galleryv4::restore(nextGallery,s.value("gallery",Json())))return false;galleryv4::merge(nextGallery,galleryState);
  machinev4::State nextMachine;bool nextMachineActive=s.contains("machine");if(nextMachineActive&&(!machinev4::restore(nextMachine,s["machine"],nextCoins,machinePool())||next.current().value("selectionRole",std::string())!="freetime"))return false;
  auto nextCards=s.value("cards",std::set<std::string>{});for(auto& p:nextBonds)if(p.second<0)return false;for(auto& p:nextGifts)if(p.second<0)return false;
  exworld::State restoredWorld;exworld::load(restoredWorld);exworld::restore(restoredWorld,s.value("world",Json::object()));
  if(next.current().value("type",std::string())=="task"){auto task=next.current().value("taskId",std::string());const auto& bundle=storyv4::bucketData(g.value("taskBucketPrefix",std::string("Assets/Data/v4_story/native_tasks/")),storyv4::bucket(task,64))["tasks"].at(task);taskv4::prepare(bundle,next.evidence);if(!pending.empty())taskv4::success(next.current(),bundle,pending.at("judgment").get<std::string>());}
  auto nextWorldId=s.value("worldId",std::string("plaza"));if(!nextWorldId.empty()&&!restoredWorld.data["instances"].contains(nextWorldId))return false;int nextPulls=std::max(0,s.value("pulls",0));
  auto court=s.value("court",Json::object());if(!court.is_object())return false;bool nextCourt=court.value("active",false);if(!pending.empty()&&!nextCourt)return false;
  auto nextDead=court.value("dead",std::vector<std::string>{});std::set<std::string> uniqueDead;for(const auto& who:nextDead){bool known=false;for(auto seat:court::SEATS)if(who==seat)known=true;if(!known||!uniqueDead.insert(who).second)return false;}
  int nextMaxHearts=archiveReplay?growthv4::MaximumHp(nextGrowth)/2000:std::clamp(court.value("maxHearts",5),1,10),nextHearts=std::clamp(court.value("hearts",nextMaxHearts),1,nextMaxHearts),nextHp=std::clamp(court.value("hp",nextHearts*2000),1,nextMaxHearts*2000),nextRetries=std::max(0,court.value("retries",0)),nextCorrect=std::max(0,court.value("correct",0));float nextFocus=std::clamp(court.value("focus",100.f),0.f,growthv4::MaximumMental(nextGrowth)/100.f);if(!std::isfinite(nextFocus))return false;
  bool nextRevive=court.value("reviveUsed",false),nextSdGuard=court.value("sdGuardUsed",false),nextMissGuard=court.value("missGuardUsed",false);auto nextPresentation=s.value("presentation",Json::object());if(!nextPresentation.is_object())return false;
  if(v4TaskActive||v4Court)v4LeaveTrial();hideExplore();hideFlow();pv4::Clear(presentationV4);v4=std::move(next);difficultyV4=nextDifficulty;exploreReactions=std::move(nextReactions);reactionAt=-1;reactionWorld.clear();trialResults=std::move(nextResults);world=std::move(restoredWorld);coins=nextCoins;bonds=nextBonds;gifts=nextGifts;giftKnown=std::move(nextGiftKnown);giftNew=std::move(nextGiftNew);cards=nextCards;pulls=nextPulls;v4GiftMode=0;v4FreeAccepted=false;growthV4=std::move(nextGrowth);galleryState=std::move(nextGallery);if(galleryRecoveryBank.empty()&&s.contains("galleryBank"))galleryRecoveryBank=s["galleryBank"];machineActive=false;UI::Remove(this,"machinev4");playerProgress=nextPlayer;v4Documents=std::move(nextDocuments);v4PendingTaskResume=std::move(pending);
  // A restored investigation is already inside its hub. Its saved room/pose
  // must survive deferred scene entry instead of re-entering the first spot.
  v4HubNode=v4.current().value("type",std::string())=="investigate"?v4.node:std::string();v4HubPage=0;
  trialAnswerContext=nextChoiceContext;trialAnswerConfirmed=nextChoiceConfirmed;trialAnswerOn=false;UI::SetVisible(this,UI_ID,"Title",false);
  chapterAt=ch=="P"?0:std::stoi(ch);chapter=Json{{"chapter",ch},{"gone",Json::array()}};flowOn=false;lastError.clear();
  if(!nextCourt&&!nextWorldId.empty()){exworld::begin(world,nextWorldId,true,v4FreeWorld()&&v4.graph.contains("campaignRevision"));exworld::camera(world);}else{world.id=nextWorldId;world.visible=false;world.active=false;}v4Court=nextCourt;v4TaskActive=v4QueueActive=false;if(v4Court){v4SelectCourtScene();trialDead=nextDead;maxHearts=nextMaxHearts;debate.hearts=nextHearts;v4TrialHp=nextHp;debate.focus=nextFocus;shownHearts=-1;retries=nextRetries;correctCount=nextCorrect;reviveUsed=nextRevive;sdGuardUsed=nextSdGuard;missGuardUsed=nextMissGuard;setupCourt();}
  // Keep cold court/world construction separate from task/widget entry.
  // All saved data was validated above; only presentation work is deferred.
  v4LoadPresentation=std::move(nextPresentation);v4LoadResult=nextResultOpen;v4LoadMachine=nextMachineActive?machinev4::save(nextMachine):Json();v4LoadPhase=1;mode=Mode::Story;return true;
 }catch(const std::exception&){return false;}
}
void Yumeno::v4LoadTick(){
 if(v4LoadPhase==1){v4Enter(true);if(!scenesv4::waiting()&&!gputrialhudv4::anagramWarming)v4LoadPhase=2;return;}
 if(v4LoadResult)trialResultStart();
 else if(v4TaskActive&&stageKind=="climax"&&v4ComicIntroTime>=0){}
 else if(v4LoadPresentation.contains("bed")||v4LoadPresentation.contains("silent")){
  const auto savedBed=v4LoadPresentation.value("bed",std::string());
  if(v4TaskActive&&stageKind=="vote"&&v4QueueAfter!="success"&&savedBed=="bgm_trial_truth")
   v4LoadPresentation["bed"]="bgm_trial_main_1";
  if(chapterAt==5&&savedBed=="bgm_investigation")
   v4LoadPresentation["bed"]="bgm_investigation_final";
  if(!v4LoadPresentation.value("silent",savedBed.empty())&&mode==Mode::Explore){
   if(v4FreeWorld())v4LoadPresentation["bed"]="bgm_freetime";
   else if(v4.current().value("type",std::string())=="investigate")
    v4LoadPresentation["bed"]=chapterAt>=5?"bgm_investigation_final":"bgm_investigation";
  }
  pv4::Restore(presentationV4,v4LoadPresentation);
 }
 else if(!v4TaskActive&&mode!=Mode::Credits){
  const auto presentation=v4.graph.value("presentation",Json::object());
  const auto beds=presentation.value("sectionBeds",Json::object());
  if(v4Court)music("bgm_trial_main_"+std::to_string(chapterAt));
  else if(v4FreeWorld())music("bgm_freetime");
  else if(v4.current().value("type",std::string())!="investigate")music(beds.value(v4.section,Json::object()).value("music",presentation.value("entryMusic",std::string("bgm_daily_pro"))));
 }
 v4WorldAmbience();pv4::SceneReady(presentationV4,v4Court?"court":world.id,true);v4.restoring=false;
 if(!v4LoadMachine.is_null()){machinev4::State restored; if(!machinev4::restore(restored,v4LoadMachine,coins,machinePool()))throw std::runtime_error("Validated machine restore changed");machineOpen(false);machineV4=std::move(restored);machineTime=0;machineDraw();}
 v4LoadPresentation=v4LoadMachine=Json();v4LoadResult=false;v4LoadPhase=0;
}
hb::Json Yumeno::v4Auto()const{
 if(modeEndTimeV4>=0)return Json{{"kind","wait"}};
 if(v4LoadPhase||trialEntryTime>0)return Json{{"kind","wait"}};
 if(trialEntryTime==0&&mode==Mode::Story)return Json{{"kind","key"},{"key",trialPrepRow==0?"Enter":"w"}};
 if(difficultyOn)return Json{{"kind","key"},{"key",difficultyRow==2?"Enter":"s"}};
 if(mode==Mode::Machine){if(machineHelp)return Json{{"kind","key"},{"key","Escape"}};if(machineV4.phase==machinev4::Phase::Select)return Json{{"kind","key"},{"key",machineV4.selected?"Enter":"w"}};if(machineV4.phase==machinev4::Phase::Prize)return Json{{"kind","key"},{"key","Enter"}};return Json{{"kind","wait"}};}
 if(mode==Mode::Gallery){if(galleryConfirm)return Json{{"kind","key"},{"key",galleryConfirmChoice?"a":"Enter"}};return Json{{"kind","key"},{"key","Escape"}};}

 if(trialResultOn)return Json{{"kind","key"},{"key",trialResultHistory?"Backspace":"Enter"}};
 if(!v4.blocked.empty())return Json{{"kind","gate"}};if(mode==Mode::Menu&&menuPending>=0)return Json{{"kind","wait"}};
 if(v4TaskActive){if(v4QueueActive)return Json{{"kind","key"},{"key","Enter"}};return autoAction();}
 if(v4LogOpen)return Json{{"kind","key"},{"key","Backspace"}};
 if(v4FreeWorld()){
  if(mode==Mode::Menu)return menuAuto(0);
  if(!v4FreeSpots.empty()){
   auto who=v4FreeSpots[0].at("interviewActors")[0].get<std::string>();for(int i=0;i<int(world.targets.size());i++)if(world.targets[i].person&&world.targets[i].slug==who)return exworld::autoTarget(world,i);
   auto path=exworld::route(world,world.id,v4FreeSpots[0].value("space_id",std::string()));
   if(path.size()>1)for(int i=0;i<int(world.targets.size());i++){auto room=world.targets[i].room;if(room>=0&&world.roomIds[room]==path[1])return exworld::autoTarget(world,i);}
  }
  return Json{{"kind","wait"}};
 }
 if(v4.current().value("type","")=="investigate"){
  if(mode==Mode::Explore)return Json{{"kind","key"},{"key","m"}};
  int nextPage=-1;for(int i=0;i<int(v4HubChoices.size());i++){int index=v4HubChoices[i];if(index==-2)nextPage=i;if(index<0)continue;auto id=v4.current()["spots"][index].value("id",std::string());if(!v4.flags.value("spot:"+id+":complete",false))return menuAuto(i);}
  if(nextPage>=0)return menuAuto(nextPage);
  return Json{{"kind","key"},{"key","Backspace"}};
 }
 if(v4.current().value("type","")=="menu")return menuAuto(0);
 if(v4.current().value("holdSeconds",0.f)>0)return Json{{"kind","wait"}};
 return Json{{"kind","key"},{"key","Enter"}};
}
void Yumeno::DebugV4Chapter(int index){
 static const std::array<const char*,7> checkpoints{{"later-trial","door-mine","witness-view","paper-comparison","paper-mine","rescue-hearing","paper-sequence"}};
 if(index>=11&&index<11+int(checkpoints.size()))v4Start("1",true,true,checkpoints[index-11]);
 else if(index==34)v4Start("2",true,true,"theatre-physical");
 else if(index==33)v4Start("2",true,true,"vote-hearing");
 else if(index==32)v4Start("2",true,true,"comic-hearing");
 else if(index==31)v4Start("2",true,true,"theatre-armament");
 else if(index==30)v4Start("2",true,true,"last-sighting");
 else if(index==29)v4Start("1",true,true,"vote-hearing");
 else if(index==28)v4Start("2",true,true,"theatre-ring");
 else if(index==27)v4Start("1",true,true,"phone-evidence");
 else if(index==26)v4Start("1",true,true,"comic-hearing");
 else if(index==25)v4Start("1",true,true,"armament-hearing");
 else if(index==24)v4Start("1",true,true,"signature-hearing");
 else if(index==23)v4Start("1",true,true,"phone-hearing");
 else if(index>=20&&index<=22)v4Start(std::to_string(index-16),true,true);
 else if(index==19)v4Start("3",true,true);
 else if(index==18)v4Start("2",true,true,"sleeve");
 else if(index==10)v4Start("3",true,true,"incident");
 else if(index>=7&&index<=10)v4Start(index==7?"P":std::to_string(index-7),true,true);
 else v4Start(index==0?"P":std::to_string(std::clamp(index,1,6)));
}
void Yumeno::DebugFastRead(){optionsV4.values.readOnlySkip=false;optionsV4.values.autoRead=false;}
void Yumeno::DebugV4ChoiceFixture(int count){
 // Real authored menu/choices, selected directly only for isolated UI QA.
 v4Start("1");std::string selected;
 for(const auto& candidate:flowchoice::layout().at("fixtures")){
  auto id=candidate.get<std::string>();const auto& n=storyv4::lookup(v4.graph,id);int eligible=0;
  for(const auto& o:n["options"])if(storyv4::eligible(v4,o))++eligible;
  if(count<=4?eligible==count:eligible>4){selected=id;break;}
 }
 if(selected.empty()){lastError="No authored menu for isolated choice UI fixture";return;}storyv4::jump(v4,selected);v4Enter();
}
void Yumeno::DebugV4DialogueFixture(int kind){
 // Actual authored lines; direct selection is isolated UI QA, not normal traversal.
 v4Start("1");const auto& targets=dialogueui::layout().at("fixtures");
 if(kind<0||kind>=int(targets.size())){lastError="No authored dialogue UI fixture";return;}
 storyv4::jump(v4,targets[kind].get<std::string>());v4Enter();
}
std::string Yumeno::OptionsStats()const{
 Json db=Json::object();for(auto id:{"Master","Music","SFX","UI","Voice"})db[id]=AudioMixer::GetFloat(const_cast<Yumeno*>(this),optv4::Mixer,id);
 return Json{{"values",optv4::Encode(optionsV4.values)},{"textMultiplier",optv4::TextSpeedFactor(optionsV4.values)},{"reticleScale",optv4::ReticleScale(optionsV4.values)},{"db",db},{"voiceAssets",false},{"visibleKinds",{0,1,2,3,4,5,6,7,8,9,12}}}.dump();
}

void Yumeno::v4Menu(){
 if(v4FreeWorld()){v4FreeBegin();return;}
 const auto& n=v4.current();std::vector<int> available;for(int i=0;i<int(n["options"].size());i++)if(storyv4::eligible(v4,n["options"][i]))available.push_back(i);
 v4MenuChoices.clear();std::vector<std::string> labels;v4MenuPage=std::clamp(v4MenuPage,0,std::max(0,(int(available.size())-1)/7));
 for(int row=v4MenuPage*7;row<std::min((v4MenuPage+1)*7,int(available.size()));row++){int index=available[row];v4MenuChoices.push_back(index);labels.push_back(n["options"][index].value("label",std::string()));}
 if(v4MenuPage>0){v4MenuChoices.push_back(-1);labels.push_back("이전 쪽");}if((v4MenuPage+1)*7<int(available.size())){v4MenuChoices.push_back(-2);labels.push_back("다음 쪽");}
 if(labels.empty()){v4.blocked="Authored menu has no eligible route";lastError="V4: "+v4.blocked;return;}UI::SetFontSize(this,flowui::ID,"FMenuQ",30);showMenu(n.value("q",std::string()),labels,MenuKind::Event);if(n.value("selectionRole",std::string())=="freetime"){UI::SetFontSize(this,flowui::ID,"FMenuQ",24);text("Body",n.value("q",std::string())+"\nG 선물 · C 캡슐");}
 if(!v4Court&&n.contains("dialoguePortrait")){
  auto displayed=dialogueportraitv4::interlocutor(n);portrait.clear();
  if(courtFigures.is_null()||courtFigures.empty())courtFigures=Data::Get("Assets/Data/court.json")["figures"];
  auto key=dialogueportraitv4::poseKey(n,displayed);if(courtFigures.contains(key))portrait=courtFigures[key].value("texture",std::string());
  dialoguePortrait();if(!portrait.empty())UI::SetTexture(this,UI_ID,"Portrait",portrait);
  UI::SetVisible(this,UI_ID,"Portrait",!portrait.empty()&&v4RenderedCg.empty());
 }
}
void Yumeno::v4MenuPick(int index){
 if(index<0||index>=int(v4MenuChoices.size()))return;int choice=v4MenuChoices[index];
 if(choice<0){v4MenuPage+=choice==-1?-1:1;pv4::Action(presentationV4,"page_turn");v4Menu();return;}
 if(storyv4::choose(v4,choice))v4Enter();
}

void Yumeno::v4ObserveGrowth(){
 if(growthV4.contract.empty())return;auto result=growthv4::Observe(growthV4,v4.flags,bonds,coins);if(result.changed)hud();
 for(const auto& id:result.encounters){if(!v4.graph.contains("campaignRevision"))galleryGrant("fte:"+id);auto reward=growthV4.contract.at("entries").at(id).value("xpReward",std::string());if(!reward.empty())playerClaim(reward,"authored-fte-reward:"+id);}
 if(!result.unlocked.empty()){sfx("sfx_bond_up");toast("새 스킬을 익혔어요 · 통신부에서 장착할 수 있어요");}
}
void Yumeno::v4PresentScene(const Json& n){
 auto parkChapter=v4.graph.value("chapter",std::string("P"));world.accessChapter=parkChapter.size()==1&&parkChapter[0]>='1'&&parkChapter[0]<='6'?parkChapter[0]-'0':0;
 if(n.contains("timeOfDay")){auto time=n.at("timeOfDay").get<std::string>();playerProgress.skyPhase=time=="night"?1:time=="evening"?2:0;playerProgress.phase=time=="night"?1:0;}
 if(n.contains("hudPhase")){auto phase=n.at("hudPhase").get<std::string>();if(phase=="day"||phase=="night"||phase=="close")playerProgress.phase=phase=="night"?1:phase=="close"?2:0;}
 playerProgress.context=n.value("hudContext",v4.graph.value("kind",std::string())=="freetime"?std::string("extra"):std::string("chapter"));
 if(n.contains("comicPage")){v4ComicPage=n["comicPage"].get<std::string>();v4ComicComplete(true);}else if(!v4TaskActive&&!v4ComicPage.empty()){v4ComicClear();v4ComicPage.clear();}
 auto scene=n.value("scene",Json::object());
 if(n.contains("sceneVariants")){bool matched=false;for(const auto& candidate:n["sceneVariants"]){bool eligible=true;for(const auto& condition:candidate["when"]){auto key=condition.at("flag").get<std::string>();if(!v4.flags.contains(key)||v4.flags[key]!=condition["equals"])eligible=false;}if(eligible){if(matched){v4.blocked="Multiple current scene variants";return;}scene=candidate;matched=true;}}if(!matched){v4.blocked="Current scene requires its actual preceding choice";return;}}
 if(!scene.empty()){
  if(v4Court&&scene.value("leaveCourt",false)){v4LeaveTrial();dialogVisible(true);}
  if(!v4Court){auto space=scene.value("space",std::string());auto id=space=="guest_room"?std::string("story_guest_room"):space;
   const bool existingHub=n.value("type",std::string())=="investigate"&&v4HubNode==v4.node&&world.active;
   if(!existingHub&&!id.empty()&&(world.id!=id||!world.active)){exworld::begin(world,id,false);exworld::camera(world);}
  }
 }
 auto image=n.value("shot",Json::object()).value("image",std::string());
 if(!image.empty()&&n.value("type",std::string())!="say"&&n.value("type",std::string())!="stage")image.clear();
 if(image!=v4RenderedCg){v4RenderedCg=image;if(!image.empty())UI::SetTexture(this,UI_ID,"Background",image);}
 UI::SetVisible(this,UI_ID,"Background",!image.empty());UI::SetVisible(this,UI_ID,"CourtDim",v4Court&&image.empty());
 if(!image.empty()){UI::SetPosition(this,UI_ID,"Background",{0,0});UI::SetSize(this,UI_ID,"Background",{1280,720});}
 exworld::visible(world,world.active&&!v4Court&&image.empty());
 v4WorldAmbience();
 bool authored=!n.value("presentation",Json::object()).value("actions",Json::array()).empty();
 pv4::SceneReady(presentationV4,v4Court?"court":world.id,v4.restoring||v4Court||authored);
}
void Yumeno::v4WorldAmbience(){
 bool active=v4.active&&world.active&&!v4Court&&mode!=Mode::Title&&mode!=Mode::Credits;
 pv4::WorldAmbience(presentationV4,active,active&&world.spec().value("outdoor",false));
}

void Yumeno::v4CaptureRecords(const Json& n){
 for(const auto& record:n.value("publicRecords",Json::array()))v4Documents[record.at("id").get<std::string>()]={{"title",record.at("title")},{"rows",record.at("rows")},{"category",record.value("category",std::string())},{"private",false},{"image",""}};
}
void Yumeno::v4ShowDocument(const std::string& title,const std::string& rows,const std::string& image){
 dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);
 documentV4.prepare(title,rows,image,[](const std::string& glyph){return flowchoice::width(glyph)*24.f/26.6666667f;});v4DocumentDraw();
}
