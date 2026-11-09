// 장 진행 (docs/spec/09) : Assets/Data/flow/{P,1..6}.json 의 비트를 차례로 실행한다.
// 비트 : card · scene · freetime · investigate · trial · execution · ending · end   (tools/build_flow.py)
// Yumeno.cpp 끝에서 include 한다.
#include <random>
namespace flowui {
const char* ID="flow";
constexpr float OPT_X=730.66667f,OPT_Y=352,OPT_W=586.66667f,OPT_H=50,OPT_STEP=48.66667f; // adv_choices source strips
constexpr float CELL_X=150,CELL_Y=110,CELL_W=236,CELL_H=120,CELL_DX=250,CELL_DY=130; // 인물·선물 칸 4×4
const int LEVELS[]{0,4,10,18,28}; // 인연 Lv1~5 누적 포인트 (00 §5-2)
}
#include "DialogueChoiceV4.hpp"
#include "DialogueWindowV4.hpp"

void Yumeno::ftext(const std::string& id,const std::string& v){if(ftexts.count(id)&&ftexts[id]==v)return;ftexts[id]=v;UI::SetText(this,flowui::ID,id,v);}
void Yumeno::fvis(const std::string& id,bool v){
 if(id=="FHud"){fvis("FHudImg",v);fvis("FHudSub",v);fvis("FHudGauge",v);fvis("FLevelUp",v&&playerProgress.popup>=2);} // Sibling nodes, not label children.
 if(fvisible.count(id)&&fvisible[id]==v)return;fvisible[id]=v;UI::SetVisible(this,flowui::ID,id,v);
}
std::string Yumeno::artPath(const std::string& group,const std::string& name,const std::string& dir,const std::string& ext)const{
 if(!art.contains(group))return "";
 for(auto& n:art[group])if(n.get<std::string>()==name)return "Assets/Art/"+dir+"/"+name+ext;
 return "";
}
// BGM : 엔진은 파일 전체만 반복한다 → 들어가는 부분(<큐>_intro)을 한 번 틀고 끝나기 직전에 반복 부분으로 (tools/import_audio.py)
bool Yumeno::hasAudio(const std::string& cue)const{return art.contains("audio")&&art["audio"].contains(cue);}
float Yumeno::audioLen(const std::string& cue)const{return art.contains("audioLen")&&art["audioLen"].contains(cue)?art["audioLen"][cue].get<float>():0.f;}
void Yumeno::stopJingle(){if(!jingleHandle.empty())Audio::Stop(jingleHandle);jingleHandle.clear();jingleTimer=0;jingleNext.clear();jingleIntro=false;}
void Yumeno::music(const std::string& cue){
 if(cue=="@silence"){stopJingle();Audio::StopMusic(.15f);musicCue.clear();return;}
 if(cue==musicCue)return;
 if(!hasAudio(cue)){lastError="Missing music cue: "+cue;return;}
 stopJingle();musicCue=cue;if(cue.rfind("bgm_",0)==0&&cue.size()<80)galleryGrant("bgm:"+cue);
 if(hasAudio(cue+"_intro")){Audio::StopMusic(.5f);jingleHandle=Audio::Play(art["audio"][cue+"_intro"].get<std::string>(),1.f,1.f,"music");jingleTimer=std::max(.05f,audioLen(cue+"_intro")-.03f);jingleNext=cue;jingleIntro=true;return;}
 Audio::PlayMusic(art["audio"][cue].get<std::string>(),1.f);
}
// 「징글>다음 곡」 : 징글(한 번)이 끝나면 다음 곡. 징글이 아니면 그냥 그 곡
void Yumeno::playCue(const std::string& spec){
 auto gt=spec.find('>');auto first=spec.substr(0,gt),then=gt==std::string::npos?std::string():spec.substr(gt+1);
 if(first.rfind("jingle_",0)!=0){music(first);return;}
 stopJingle();Audio::StopMusic(.3f);musicCue="";
 if(hasAudio(first)){jingleHandle=Audio::Play(art["audio"][first].get<std::string>(),1.f,1.f,"sfx");jingleTimer=std::max(.5f,audioLen(first));jingleNext=then;jingleIntro=false;}
 else if(!then.empty())music(then);
}
void Yumeno::updateMusic(float delta){
 if(jingleTimer<=0||(jingleTimer-=delta)>0)return;
 jingleHandle.clear();jingleTimer=0;if(jingleNext.empty())return;
 if(jingleIntro){auto next=jingleNext;jingleNext.clear();jingleIntro=false;musicCue=next;Audio::PlayMusic(art["audio"][next].get<std::string>(),0.f);}
 else{auto next=jingleNext;jingleNext.clear();music(next);}
}
// 효과음 : audio/cues.json 에 파일이 있는 큐만 (docs/spec/16 §5). ui_* 는 UI 버스
void Yumeno::sfx(const std::string& cue){
 if(mode==Mode::Trial&&(cue=="v3se_316"||cue=="v3se_315")){
  if(trialImpactCooldown>0&&(lastTrialImpactDamage||cue=="v3se_315"))return;
  trialImpact(cue=="v3se_316");
 }
 if(hasAudio(cue))Audio::Play(art["audio"][cue].get<std::string>(),1.f,1.f,cue.rfind("ui_",0)==0?"ui":"sfx");
}
void Yumeno::trialImpact(bool damage){
 trialImpactCooldown=damage?.18f:.09f;lastTrialImpactDamage=damage;
 // The native camera service adds a decaying offset after authored framing.
 // The camera-mounted anagram board uses its own red rejection ring. A world
 // camera offset moves its near-plane sprites outside the viewport.
 if(stageKind!="anagram")if(auto* c=actor("Camera"))Camera::Shake(c,damage?.065f:.018f,damage?.32f:.14f);
 Camera::Flash({.78f,.015f,.04f,damage?.30f:.10f},damage?.28f:.12f);
}
// 대본 이벤트에 붙은 소리 : "music"(징글>곡 가능), "sfx"(하나 또는 여럿). 같은 이벤트는 한 번만
void Yumeno::eventSound(const hb::Json& e){
 if(&e==lastSoundEvent)return;lastSoundEvent=&e;
 if(e.contains("presentation")){pv4::Apply(presentationV4,e,static_cast<std::uint64_t>((chapterAt+1)*1000000+(beat+1)*10000+event));return;}
 if(e.contains("music"))playCue(e["music"].get<std::string>());
 if(e.contains("sfx")){if(e["sfx"].is_array())for(auto& s:e["sfx"])sfx(s.get<std::string>());else sfx(e["sfx"].get<std::string>());}
}
int Yumeno::level(const std::string& slug)const{int p=bonds.count(slug)?bonds.at(slug):0,l=1;for(int i=1;i<5;i++)if(p>=flowui::LEVELS[i])l=i+1;return l;}
void Yumeno::addBond(const std::string& slug,int points){int before=level(slug);if(points>=3)sfx("sfx_correct");if(points<0)sfx("sfx_wrong");bonds[slug]=std::max(0,bonds[slug]+points);if(level(slug)>before){sfx("sfx_bond_up");toast(nameOf(slug)+" 인연 Lv"+std::to_string(level(slug))+"!");}}
void Yumeno::toast(const std::string& v){ftext("FToast",v);fvis("FToast",true);toastTimer=2.2f;}
void Yumeno::hud(){
 std::string ch=chapter.value("chapter","P"),phase=playerProgress.phase==1?"night":playerProgress.phase==2?"close":"day";
 auto header=playerProgress.context=="extra"?"10":playerProgress.context=="epilogue"?"7":playerProgress.context=="trial"?"9":ch=="P"?"0":ch;
 auto key=phase+header;static const auto layout=Data::Get("Assets/Data/v4_story/exploration_hud_layout.json");
 auto image=layout.at("variants").value(key,std::string());if(!image.empty()&&image!=hudImage){hudImage=image;UI::SetTexture(this,flowui::ID,"FHudImg",image);}
 auto gauge="Assets/Art/ui/v3/exploration/gauge_"+std::to_string(playerprogress::fullGauge(playerProgress,playerprogress::level(playerProgress))?100:int(std::round(playerprogress::fraction(playerProgress)*100)))+".svg";
 if(gauge!=hudGauge){hudGauge=gauge;UI::SetTexture(this,flowui::ID,"FHudGauge",gauge);}
 ftext("FHud","");ftext("FHudSub","Level "+std::to_string(playerProgress.displayed));
}
void Yumeno::playerXp(const std::string& kind,int count){
 if(count<=0)return;if(playerprogress::gain(playerProgress,playerprogress::amount(kind)*count)){if(growthV4.legacyBudget<=playerprogress::level(playerProgress))growthV4.legacyBudget=0;hud();}
}
void Yumeno::playerClaim(const std::string& kind,const std::string& id){int amount=playerprogress::amount(kind);if(amount>0&&playerprogress::claim(playerProgress,id,amount)){if(growthV4.legacyBudget<=playerprogress::level(playerProgress))growthV4.legacyBudget=0;hud();}}
void Yumeno::playerWalk(float distance){int count=playerprogress::walk(playerProgress,distance);if(count)playerXp("Walk",count);}
bool Yumeno::exploreConcentration(){
 bool down=Input::IsKeyDown("r");if(!down)exploreFocusReady=true;bool active=down&&world.active&&mode==Mode::Explore;
 if(!active){exploreConcentrationOff();return false;}
 if(!exploreFocusOn&&exploreFocusReady){exploreFocusOn=true;exploreFocusReady=false;playerXp("UseConcentration");pv4::Action(presentationV4,"concentration_on");}
 return exploreFocusOn;
}
void Yumeno::exploreConcentrationOff(){if(!exploreFocusOn)return;exploreFocusOn=false;pv4::Action(presentationV4,"concentration_off");}
void Yumeno::playerTick(float delta){
 if(mode!=Mode::Explore||optionsV4.open)exploreConcentrationOff();
 if(!galleryReplay)exworld::environment(world,playerProgress.skyPhase);
 bool admitted=!optionsV4.open&&mode!=Mode::Pad&&mode!=Mode::Title&&mode!=Mode::Trial&&!v4LogOpen&&fvisible["FHud"];
 if(!admitted){fvis("FLevelUp",false);return;}
 playerProgress.clock+=delta*60;int count=std::min(8,int(playerProgress.clock));playerProgress.clock-=count;
 for(int i=0;i<count;i++){int action=playerprogress::tick(playerProgress,playerprogress::level(playerProgress));if(action==1)sfx("sfx_bond_up");} // Own positive chime; not a claimed V3_SE_048 binding.
 bool visible=playerProgress.popup>=2;fvis("FLevelUp",visible);
 if(visible){static const auto layout=Data::Get("Assets/Data/v4_story/level_up_layout.json");auto key=playerProgress.popup==3?"out":playerProgress.frame<16?"in":"wait";int frame=playerProgress.popup==3?playerProgress.frame:playerProgress.frame<16?playerProgress.frame:playerProgress.child%45;auto image=layout.at(key)[frame].get<std::string>();if(image!=levelUpImage){levelUpImage=image;UI::SetTexture(this,flowui::ID,"FLevelUp",image);}}
 hud();
}
std::string Yumeno::PlayerProgressStats()const{return Json{{"xp",playerProgress.xp},{"level",playerprogress::level(playerProgress)},{"displayed",playerProgress.displayed},{"popup",playerProgress.popup},{"hold",playerProgress.hold},{"frame",playerProgress.frame},{"claims",playerProgress.claims.size()},{"concentration",exploreFocusOn},{"objectReactions",reactionv4::save(exploreReactions)},{"capacity",growthv4::Capacity(growthV4,playerprogress::level(playerProgress))},{"legacyBudget",growthV4.legacyBudget},{"fraction",playerprogress::fraction(playerProgress)},{"walkPhase",playerProgress.walkPhase},{"phase",playerProgress.phase},{"context",playerProgress.context},{"image",hudImage},{"gauge",hudGauge}}.dump();}
void Yumeno::DebugPlayerProgressFixture(int xp){playerProgress={};playerprogress::gain(playerProgress,xp);playerProgress.displayed=playerprogress::level(playerProgress);hud();}

// 저장 : 장·비트·이벤트·문맥 + 인연·코인·선물·언령·플래그
bool Yumeno::saveFlow(bool checkpoint){
 if(v4.active)return v4Save();
 if(!flowOn||chapter.is_null())return false;
 auto resume=mode==Mode::Pad?beforePad:mode;
 Json s{{"v",3},{"checkpoint",checkpoint},{"mode",int(resume)},{"chapter",chapterAt},{"beat",beat},{"event",event},{"pool",ctxPool},{"spot",ctxSpot},{"ending",ctxEnding},{"slots",slots},
  {"read",readLegacy},{"world",exworld::save(world)},{"playerProgress",playerprogress::save(playerProgress)},{"exploreReactions",reactionv4::save(exploreReactions)},{"coins",coins},{"pulls",pulls},{"bonds",bonds},{"gifts",gifts},{"giftKnown",giftKnown},{"giftNew",giftNew},{"cards",cards},{"flags",flags},{"seen",seen},{"notes",notes},
  {"room",roomAt},{"mapReturn",mapReturnRoom},{"pan",panX},{"map",mapHover},{"eventEnd",eventEnd},{"segment",segmentKey},{"after",int(after)},
  {"giftTarget",giftTarget},{"background",lastBackground},{"sceneBackground",sceneBackground},{"music",musicCue},
  {"line",line},{"speaker",speaker},{"portrait",portrait},{"trialStage",mode==Mode::Trial?stageAt:-1},
  {"trialHearts",debate.hearts},{"trialRetries",retries},{"trialCorrect",correctCount},{"trialRevived",reviveUsed},{"trialChoice",{{"context",trialAnswerContext},{"confirmed",trialAnswerConfirmed}}}};
 try{Save::Write(SAVE_SLOT,s);return Json::parse(Save::ReadText(SAVE_SLOT))==s;}
 catch(const std::exception&){return false;}
}
bool Yumeno::loadFlow(const std::string& slot){
 try{
  auto s=Json::parse(Save::ReadText(slot.empty()?SAVE_SLOT:slot));int v=s.value("v",0);
  if(!s.is_object()||(v!=2&&v!=3))return false;
  int ch=s.value("chapter",-1),bt=s.value("beat",-1),ev=s.value("event",0);
  if(ch<0||ch>=int(story["chapters"].size()))return false;
  auto restored=Data::Get("Assets/Data/flow/"+story["chapters"][ch].get<std::string>()+".json");
  if(bt<0||bt>=int(restored["beats"].size())||ev<0)return false;
  int pool=s.value("pool",-1),spot=s.value("spot",-1),ending=s.value("ending",-1),savedSlots=s.value("slots",0);
  auto& b=restored["beats"][bt];auto kind=b.value("t","");bool checkpoint=s.value("checkpoint",false);
  if(!checkpoint){
   if(pool>=0&&(kind!="freetime"||pool>=int(b["pool"].size())))return false;
   if(spot>=0&&(kind!="investigate"||spot>=int(b["spots"].size())))return false;
   if(ending>=0&&(kind!="ending"||ending>=int(b["options"].size())))return false;
   if(savedSlots<0||savedSlots>100)return false;
   const auto* events=pool>=0?&b["pool"][pool]["events"]:spot>=0?&b["spots"][spot]["events"]:ending>=0?&b["options"][ending]["beat"]["events"]:b.contains("events")?&b["events"]:nullptr;
   if(events&&ev>int(events->size()))return false;
  }
  // Parse every collection before replacing live progress; damaged saves leave it untouched.
  auto nb=s.value("bonds",std::map<std::string,int>{}),ng=s.value("gifts",std::map<std::string,int>{});
  int nc=s.value("coins",0),np=s.value("pulls",0);
  if(nc<0||np<0)return false;
  reactionv4::State nextReactions;if(!reactionv4::restore(nextReactions,s.value("exploreReactions",Json())))return false;
  playerprogress::State nextPlayer;if(!playerprogress::restore(nextPlayer,s.value("playerProgress",Json())))return false;
  std::string nextChoiceContext;std::vector<bool> nextChoiceConfirmed;if(!trialanswer::restore(s.value("trialChoice",Json::object()),nextChoiceContext,nextChoiceConfirmed))return false;
  for(auto& x:nb)if(x.second<0)return false;
  for(auto& x:ng)if(x.second<0)return false;
  auto setOf=[&](const char* key){auto rows=s.value(key,std::vector<std::string>{});return std::set<std::string>(rows.begin(),rows.end());};
  auto nCards=setOf("cards"),nFlags=setOf("flags"),nSeen=setOf("seen"),nNotes=setOf("notes"),nRead=setOf("read");
  auto nGiftKnown=setOf("giftKnown"),nGiftNew=setOf("giftNew");for(const auto& [id,qty]:ng)nGiftKnown.insert(id);for(const auto& id:nGiftNew)if(!nGiftKnown.count(id))return false;
  int savedMode=s.value("mode",int(Mode::Story)),savedAfter=s.value("after",0);
  if(savedMode<0||savedMode>int(Mode::Popup)||savedAfter<0||savedAfter>int(After::Trial))return false;
  int savedStage=s.value("trialStage",-1);
  int savedHearts=s.value("trialHearts",5),savedRetries=s.value("trialRetries",0),savedCorrect=s.value("trialCorrect",0);
  bool savedRevived=s.value("trialRevived",false);
  if(savedMode==int(Mode::Trial)&&!checkpoint){
   if(kind!="trial"||savedStage<0)return false;
   auto trial=Data::Get("Assets/Data/trials/"+b.value("key",std::string())+".json");
   if(!trial.contains("stages")||savedStage>=int(trial["stages"].size()))return false;
   if(savedHearts<1||savedHearts>6||savedRetries<0||savedCorrect<0)return false;
  }
  v4.active=false;v4Log(false);pv4::Clear(presentationV4);hideExplore();hideFlow();exworld::load(world);world.history.clear();if(s.contains("world"))exworld::restore(world,s["world"]);after=After::None;lastSoundEvent=nullptr;lastError.clear();resultPending=false;elevatorDone=false;
  readLegacy=nRead;coins=nc;pulls=np;bonds=nb;gifts=ng;cards=nCards;flags=nFlags;seen=nSeen;notes=nNotes;playerProgress=nextPlayer;exploreReactions=std::move(nextReactions);reactionWorld.clear();reactionAt=-1;
  giftKnown=std::move(nGiftKnown);giftNew=std::move(nGiftNew);trialAnswerContext=nextChoiceContext;trialAnswerConfirmed=nextChoiceConfirmed;
  chapterAt=ch;chapter=restored;beat=bt;event=ev;ctxPool=pool;ctxSpot=spot;ctxEnding=ending;slots=savedSlots;flowOn=true;
  lastBackground=s.value("background",std::string());sceneBackground=s.value("sceneBackground",std::string());
  if(!lastBackground.empty()){UI::SetTexture(this,UI_ID,"Background",lastBackground);UI::SetVisible(this,UI_ID,"Background",true);}
  auto cue=s.value("music",std::string());if(!cue.empty())music(cue);
  if(checkpoint){ctxPool=ctxSpot=ctxEnding=-1;enterBeat();return true;}
  if(savedMode==int(Mode::Trial)){elevatorDone=true;enterBeat();debate.hearts=std::min(maxHearts,savedHearts);retries=savedRetries;correctCount=savedCorrect;reviveUsed=savedRevived;enterStage(savedStage);return true;}
  if(kind=="freetime"||kind=="investigate"){
   showMap();mapReturnRoom=s.value("mapReturn",-1);if(mapReturnRoom>=int(rooms.size()))mapReturnRoom=-1;int room=s.value("room",0);
   if(!rooms.empty()&&room>=0&&room<int(rooms.size())&&(savedMode==int(Mode::Explore)||spot>=0||pool>=0||savedAfter!=0)){
    enterRoom(room);panX=std::clamp(s.value("pan",0.f),-160.f,160.f);placeRoom();
   }
   ctxPool=pool;ctxSpot=spot;ctxEnding=ending;event=ev;
   eventEnd=s.value("eventEnd",-1);segmentKey=s.value("segment",std::string());
   if(v==2&&spot>=0){for(auto& o:rooms[roomAt].objects)if(ev>=o.from&&ev<o.to){eventEnd=o.to;segmentKey=b["spots"][spot].value("id","")+"#"+std::to_string(o.index);break;}}
   if(savedAfter!=0){giftTarget=s.value("giftTarget",std::string());showStory();speaker=s.value("speaker",std::string());line=s.value("line",std::string());portrait=s.value("portrait",std::string());after=After(savedAfter);showLine();}
   else if(pool>=0||spot>=0){showStory();if(savedMode==int(Mode::Popup)&&event<int(flowEvents().size())&&flowEvents()[event].value("type",std::string())=="card")kotodamaGet(flowEvents()[event].value("id",std::string()));else flowPresent();}
   else if(savedMode==int(Mode::Grid)){giftTarget=s.value("giftTarget",std::string());showGifts();}
   else if(savedMode!=int(Mode::Explore)){mapHover=std::clamp(s.value("map",0),0,std::max(0,int(rooms.size())-1));renderMap();}
  }else if(kind=="scene"||kind=="execution"||ending>=0){showStory();if(savedMode==int(Mode::Popup)&&event<int(flowEvents().size())&&flowEvents()[event].value("type",std::string())=="card")kotodamaGet(flowEvents()[event].value("id",std::string()));else flowPresent();}
  else enterBeat();
  return true;
 }catch(const std::exception&){return false;}
}

void Yumeno::openChapter(int index){
 chapterAt=index;
 chapter=Data::Get("Assets/Data/flow/"+story["chapters"][index].get<std::string>()+".json");
 beat=0;event=0;ctxPool=ctxSpot=ctxEnding=-1;
}
const Json& Yumeno::currentBeat()const{return chapter["beats"][beat];}
const Json& Yumeno::flowEvents()const{
 auto& b=currentBeat();
 if(ctxPool>=0)return b["pool"][ctxPool]["events"];
 if(ctxSpot>=0)return b["spots"][ctxSpot]["events"];
 if(ctxEnding>=0)return b["options"][ctxEnding]["beat"]["events"];
 return b["events"];
}
bool Yumeno::inPark(const std::string& slug)const{
 for(auto& g:chapter["gone"])if(g.get<std::string>()==slug)return false;
 return true;
}

void Yumeno::newGame(){
 prepareGameplay();
 if(v4TaskActive||v4Court)v4LeaveTrial();
 v4.active=false;v4Log(false);pv4::Clear(presentationV4,true);titleMenu(false);
 world.history.clear();world.id.clear();world.active=false;
 readLegacy.clear();exploreReactions.clear();reactionWorld.clear();reactionAt=-1;coins=10;pulls=0;bonds.clear();gifts.clear();giftKnown.clear();giftNew.clear();cards.clear();flags.clear();seen.clear();notes.clear();playerProgress={};
 trialAnswerContext.clear();trialAnswerConfirmed.assign(4,false);trialAnswerOn=false;
 after=After::None;eventEnd=-1;segmentKey.clear();rooms.clear();hotspots.clear();mapReturnRoom=-1;giftPage=0;lastError.clear();lastSoundEvent=nullptr;elevatorDone=false;resultPending=false;lastBackground.clear();sceneBackground.clear();hideExplore();
 openChapter(0);flowOn=true;
 UI::SetVisible(this,UI_ID,"Title",false);
 enterBeat();
}
void Yumeno::hideFlow(){
 for(auto id:{"FCardBack","FCard","FCardT","FCardS","FShade","FMenuQ","FGridHead","FGridFoot","FCredits","FToast"})fvis(id,false);
 menuPending=-1;for(int i=0;i<9;i++)for(auto p:{"FOptP","FOptA","FOptC","FOptT"})fvis(std::string(p)+std::to_string(i),false);
 for(int i=0;i<16;i++){fvis("FCell"+std::to_string(i),false);fvis("FFace"+std::to_string(i),false);fvis("FName"+std::to_string(i),false);}
}
void Yumeno::showStory(){
 if(mode==Mode::Explore||mode==Mode::Confirm||mode==Mode::Map){hideExplore();if(!lastBackground.empty()){UI::SetTexture(this,UI_ID,"Background",lastBackground);UI::SetVisible(this,UI_ID,"Background",true);}}
 hideFlow();mode=Mode::Story;
 UI::SetVisible(this,UI_ID,"Backdrop",true);dialogVisible(true);hud();fvis("FHud",true);
}
void Yumeno::nextBeat(){++beat;event=0;ctxPool=ctxSpot=ctxEnding=-1;enterBeat();}
void Yumeno::enterBeat(){
 if(beat>=int(chapter["beats"].size())){
  if(chapterAt+1>=int(story["chapters"].size())){toTitle();return;}
  openChapter(chapterAt+1);
 }
 saveFlow(true);hud();
 auto& b=currentBeat();auto t=b.value("t","");
 if(t=="card"){
  hideFlow();dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);mode=Mode::Card;
  auto ch=b.value("chapter","P");auto img=artPath("cards","chapter_"+ch,"ui",".webp");
  fvis("FCardBack",true);fvis("FCard",!img.empty());if(!img.empty())UI::SetTexture(this,flowui::ID,"FCard",img);
  ftext("FCardT",img.empty()?(ch=="P"?std::string("프롤로그"):"제"+ch+"장"):"");ftext("FCardS",img.empty()?b.value("title",""):"");
  fvis("FCardT",img.empty());fvis("FCardS",img.empty());
  if(ch=="P")sfx("sfx_prologue");
  playCue(std::string(ch=="P"?"jingle_chapter_p":"jingle_chapter")+">"+(ch=="P"?"bgm_pro_arrival":ch=="6"?"bgm_core":std::array<const char*,6>{"","bgm_daily_pastel","bgm_daily_summer","bgm_daily_night","bgm_daily_grey","bgm_daily_mono"}[std::stoi(ch)]));
  return;
 }
 if(t=="scene"||t=="execution"){
  if(b.contains("need")&&level(b["need"].value("who",""))<b["need"].value("level",3)){nextBeat();return;} // 유품 : 인연 Lv3 이상
  // 장면 곡 : tools/sound_design.py 가 장면마다 정한 것(bgm). 없으면 처형만 처형 곡
  if(b.contains("bgm"))playCue(b["bgm"].get<std::string>());else if(t=="execution")music("bgm_punishment_time");
  showStory();event=0;flowPresent();return;
 }
 if(t=="freetime"){mapReturnRoom=-1;slots=b.value("slots",2);music("bgm_freetime");mapHover=0;showMap();band("free");return;}
 if(t=="investigate"){mapReturnRoom=-1;auto ch=chapter.value("chapter","1");music(ch=="5"||ch=="6"?"bgm_investigation_final":"bgm_investigation");mapHover=0;showMap();band("inv");return;}
 if(t=="trial"&&!elevatorDone){
  elevatorDone=true;showStory();UI::SetTexture(this,UI_ID,"Background","Assets/Art/bg/trial_elevator.webp");UI::SetVisible(this,UI_ID,"Background",true);
  music("bgm_elevator");sfx("sfx_elevator");sayOnce("mio","(…엘리베이터가 내려간다. 철창 사이로 빛이 하나씩 지나간다. 이 아래에서 — 학급 재판이 기다리고 있다.)","C01",After::Trial);
  speaker.clear();text("Name","");UI::SetVisible(this,UI_ID,"Nameplate",false);UI::SetVisible(this,UI_ID,"Name",false);UI::SetVisible(this,UI_ID,"NameHead",false);UI::SetColor(this,UI_ID,"Body",Color{.62f,.84f,1,1});
  shakeTimer=2.5f;return;
 }
 if(t=="trial"){
  elevatorDone=false;
  trialKey=b.value("key","11c");trialDead.clear();for(auto& d:b["dead"])trialDead.push_back(d.get<std::string>());
  trials=Data::Get("Assets/Data/trials/"+trialKey+".json");hideFlow();fvis("FHud",false);sfx("sfx_elevator_stop");startTrial();return;
 }
 if(t=="ending"){
  showStory();UI::SetVisible(this,UI_ID,"Portrait",false);
  std::vector<std::string> o;for(auto& x:b["options"])o.push_back(x.value("label",""));
  music("bgm_ending_choice");showMenu(b.value("q",""),o,MenuKind::Ending);return;
 }
 if(t=="end"){
  hideFlow();dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);mode=Mode::Credits;music("bgm_ending_a");
  auto bg=artPath("cards","credits_bg","ui",".webp");fvis("FCardBack",true);fvis("FCard",!bg.empty());if(!bg.empty())UI::SetTexture(this,flowui::ID,"FCard",bg);
  ftext("FCredits","『유메노쿠니』\n\n끝까지 함께해 주셔서 고맙습니다.\n\n각본 · 기획 · 연출\n주인님\n\n그림\nNovelAI · Codex\n\n엔진\nHBEngine\n\n글꼴\nSIL Open Font License 글꼴들\n\n— Fin —");fvis("FCredits",true);
  return;
 }
 nextBeat();
}
void Yumeno::toTitle(){
 trialEntryTime=-1.f;UI::Remove(this,"trialentryv4");
 if(v4TaskActive||v4Court)v4LeaveTrial();
 v4Log(false);v4DocumentVisible(false);v4.active=false;pv4::Clear(presentationV4);mode=Mode::Title;titleMenu(true);
 flowOn=false;hideExplore();hideFlow();fvis("FHud",false);dialogVisible(false);mode=Mode::Title;
 UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"Background",false);UI::SetVisible(this,UI_ID,"Title",true);music("bgm_title");
}

// 이벤트 하나를 화면에 올린다. 표시할 것이 없는 이벤트(bg·card·goto)는 처리하고 넘어간다.
void Yumeno::flowPresent(){
 while(true){
  auto& evs=flowEvents();
  if(event>=int(evs.size())||(eventEnd>=0&&event>=eventEnd)){eventsDone();return;}
  auto& e=evs[event];auto type=e.value("type","");
  if(type=="goto"){event=e.value("to",event+1);continue;}
  eventSound(e);
  if(type=="bg"){
   auto bg=e.value("bg","");std::string path;
   if(bg.rfind("cg:death",0)==0)band("body");
   if(bg.rfind("cg:",0)==0){auto want=bg.substr(3);if(art.contains("cg"))for(auto& c:art["cg"]){auto n=c.get<std::string>();if(n.rfind(want,0)==0){path="Assets/Art/cg/"+n+".webp";break;}}}
   else if(bg.rfind("ui:",0)==0)path=artPath("cards",bg.substr(3),"ui",".webp");
   else path=artPath("backgrounds",bg,"bg",".webp");
   if(!path.empty()){UI::SetTexture(this,UI_ID,"Background",path);UI::SetVisible(this,UI_ID,"Background",true);UI::SetScale(this,UI_ID,"Background",{1,1});UI::SetPosition(this,UI_ID,"Background",{-40,-24});if(bg.rfind("cg:",0)!=0)lastBackground=path;if(ctxSpot>=0&&bg.rfind("cg:",0)!=0)sceneBackground=path;}
   ++event;continue;
  }
  if(type=="card"){auto id=e.value("id","");if(cards.insert(id).second){showStory();kotodamaGet(id);return;}++event;continue;}
  if(type=="menu"){
   std::vector<std::string> o;for(auto& x:e["options"])o.push_back(x.value("label",""));
   showMenu(e.value("q",""),o,MenuKind::Event);return;
  }
  // 처형 : 키프레임 CG 가 있으면 한 줄마다 다음 장
  if(currentBeat().value("t","")=="execution"&&art.contains("cg")){
   std::vector<std::string> keys;auto pre="exec_"+std::to_string(currentBeat().value("chapter",1))+"_";
   for(auto& c:art["cg"]){auto n=c.get<std::string>();if(n.rfind(pre,0)==0)keys.push_back(n);}
   {auto key="event_"+std::to_string(currentBeat().value("chapter",1))+"_execution_keyart";if(!artPath("cg",key,"cg",".webp").empty())keys.insert(keys.begin(),key);} // 처형 키아트가 첫 장
   if(!keys.empty()){UI::SetTexture(this,UI_ID,"Background","Assets/Art/cg/"+keys[std::min<size_t>(event,keys.size()-1)]+".webp");UI::SetVisible(this,UI_ID,"Background",true);kenTime=0;}
  }
  speaker.clear();portrait.clear();
  if(type=="say"){
   speaker=e.value("speaker","");line=e.value("text","");
   auto slug=slugs.count(speaker)?slugs.at(speaker):"";
   if(!slug.empty()&&slug!="mio"){
    auto emo=emotions.value(e.value("emo",""),std::string("neutral"));
    auto& table=slug=="lappy"?lappyPoses:poses;
    auto code=e.contains("pose")?e["pose"].get<std::string>():table.count(emo)?table.at(emo):(slug=="lappy"?"L01":"C01"); // pose = tools/pose_design.py
    portrait="Assets/Art/sprites/"+slug+"/"+slug+"_"+code+".webp";
   }
   bool mono=e.value("mono",false);
   UI::SetColor(this,UI_ID,"Body",mono?Color{.62f,.84f,1,1}:Color{.96f,.94f,.97f,1});
   if(mono)speaker.clear();
  }else{
   line=type=="ui"?"【안내】 "+e.value("text",""):e.value("text","");
   UI::SetColor(this,UI_ID,"Body",type=="stage"?Color{.8f,.75f,.85f,1}:Color{1,.86f,.45f,1});
  }
  showLine();
  return;
 }
}
void Yumeno::showLine(){
 dialoguePrepare();
 auto readId="legacy:"+std::to_string(chapterAt)+":"+std::to_string(beat)+":"+std::to_string(event)+":"+std::to_string(ctxPool)+":"+std::to_string(ctxSpot)+":"+readSignature(speaker+"|"+line);optv4::BeginLine(optionsV4,readId,readLegacy.count(readId)>0);
 UI::SetVisible(this,UI_ID,"Portrait",!portrait.empty());
 if(!portrait.empty())UI::SetTexture(this,UI_ID,"Portrait",portrait);
 text("Body","");
}
// 대사 한 줄(선물 반응 등) : 다 읽으면 after 로
void Yumeno::sayOnce(const std::string& slug,const std::string& value,const std::string& pose,After then){
 showStory();speaker=nameOf(slug);line=value;portrait=slug.empty()||slug=="mio"?"":"Assets/Art/sprites/"+slug+"/"+slug+"_"+pose+".webp";
 UI::SetColor(this,UI_ID,"Body",Color{.96f,.94f,.97f,1});showLine();after=then;
}
void Yumeno::eventsDone(){
 auto& b=currentBeat();
 if(ctxPool>=0){ // 프리타임 이벤트 끝 : 인연 +2, 코인 +2, 선물 차례
  auto who=b["pool"][ctxPool].value("who","");seen.insert(b["pool"][ctxPool].value("id",""));ctxPool=-1;
  addBond(who,2);coins+=2;giftTarget=who;showGifts();return;
 }
 if(ctxSpot>=0){segmentDone();return;}
 if(ctxEnding>=0){ctxEnding=-1;nextBeat();return;}
 coins+=1;nextBeat();
}
void Yumeno::advanceFlow(){
 if(!dialogueAdvance())return;
 if(after!=After::None){auto a=after;after=After::None;
  if(a==After::Gift)showGifts();else if(a==After::Slot)slotDone();else if(a==After::Explore)enterRoomBack();else if(a==After::Trial)enterBeat();
  return;}
 ++event;flowPresent();
}

// 보기 목록 (선택지 · 수사 현장 · 엔딩 · 선물)
void Yumeno::showMenu(const std::string& q,const std::vector<std::string>& o,MenuKind kind){
 menuHover=menuFirst=0;menuPending=-1;menuKind=kind;menuCount=std::min(9,int(o.size()));menuLabels.assign(o.begin(),o.begin()+menuCount);mode=Mode::Menu;
 menuShownHover=-1;menuRenderStamp.clear();menuFocusTicks=menuMarqueeTicks=menuConfirmTicks=0;
 fvis("FShade",false);fvis("FMenuQ",false);if(!q.empty()){
  dialogueSurface(v4Court);dialogVisible(true);for(auto id:{"Nameplate","Name","NameHead","Next"})UI::SetVisible(this,UI_ID,id,false);
  text("Name","");text("NameHead","");UI::SetColor(this,UI_ID,"Body",Color{.96f,.94f,.97f,1});text("Body",q);
 }menuDraw();
}
void Yumeno::hideMenu(){menuPending=-1;menuRenderStamp.clear();fvis("FShade",false);fvis("FMenuQ",false);for(int i=0;i<9;i++)for(auto p:{"FOptP","FOptA","FOptC","FOptT"})fvis(std::string(p)+std::to_string(i),false);}
int Yumeno::menuAt(float x,float y)const{
 for(int i=menuFirst;i<std::min(menuFirst+4,menuCount);i++){float left=flowui::OPT_X-(i==menuHover?37.33333f:0),top=menuRowY(i);if(x>=left&&x<left+flowui::OPT_W&&y>=top&&y<top+flowui::OPT_H)return i;}return -1;
}
void Yumeno::menuPicked(int i){
 hideMenu();sfx("ui_confirm");auto& b=currentBeat();
 if(menuKind==MenuKind::Event){
  auto& o=flowEvents()[event]["options"][i];
  flags.insert(o.value("flag",""));
  {auto label=o.value("label","");if(label.rfind("적는다",0)==0||label.find("노트")!=std::string::npos){sfx("sfx_note");toast("노트에 적었다");
   auto at=label.find("(N");if(at!=std::string::npos){auto end=label.find_first_of(" )/",at+1);auto id=label.substr(at+1,end-at-1);cards.insert(id);notes.insert(id);}}}
  event=o.value("to",event+1);showStory();flowPresent();return;
 }
 if(menuKind==MenuKind::Ending){ctxEnding=i;event=0;showStory();flowPresent();return;}
 if(menuKind==MenuKind::Gift){giveGift(i);return;}
}
void Yumeno::giveGift(int i){
 dialoguePortrait();
 {
  hideFlow();
  if(i>=int(gridSlugs.size())||gridSlugs[i].empty()){slotDone();return;}
  if(gridSlugs[i]=="#next"){++giftPage;sfx("ui_page");showGifts();return;}
  auto id=gridSlugs[i];giftKnown.insert(id);if(--gifts[id]<=0)gifts.erase(id);giftPage=0;
  int delta=1;std::string pose="C02",kind="normal";
  if(giftData["likes"].contains(giftTarget)){
   for(auto& g:giftData["likes"][giftTarget].value("like",hb::Json::array()))if(g.get<std::string>()==id){delta=2;pose="C02";kind="like";}
   for(auto& g:giftData["likes"][giftTarget]["love"])if(g.get<std::string>()==id){delta=3;pose="T03";kind="love";}
   for(auto& g:giftData["likes"][giftTarget]["hate"])if(g.get<std::string>()==id){delta=-1;pose="C09";kind="hate";}
  }
  addBond(giftTarget,delta);sayOnce(giftTarget,reaction(giftTarget,kind),pose,After::Slot);return;
 }
}

int Yumeno::poolOf(const std::string& slug)const{
 auto& b=currentBeat();if(!b.contains("pool"))return -1;
 for(int i=0;i<int(b["pool"].size());i++){auto& p=b["pool"][i];if(p.value("who","")==slug&&!seen.count(p.value("id","")))return i;}
 return -1;
}
// 칸 자리 : 선물은 V3 선물 화면처럼 오른쪽 3열(왼쪽은 받는 사람), 나머지는 4열
std::array<float,2> Yumeno::cellAt(int i)const{
 return {560+(i%3)*220.f,flowui::CELL_Y+(i/3)*flowui::CELL_DY};
}
int Yumeno::gridAt(float x,float y)const{
 for(int i=0;i<int(gridSlugs.size())&&i<16;i++){auto c=cellAt(i);if(x>=c[0]&&x<=c[0]+212.f&&y>=c[1]&&y<=c[1]+flowui::CELL_H)return i;}
 return -1;
}
void Yumeno::gridPicked(int i){giveGift(i);}
void Yumeno::pullCapsule(){
 if(coins<3){toast("코인이 모자라요");return;}
 coins-=3;++pulls;sfx("sfx_capsule");
 static std::mt19937 rng{std::random_device{}()};
 int roll=int(rng()%100);std::string tier=roll<1?"장미":roll<10?"희귀":roll<40?"좋은":"일반";
 if(pulls%15==0&&(tier=="일반"||tier=="좋은"))tier="희귀"; // 15회마다 희귀 이상 보증
 std::vector<std::string> pick;for(auto& g:giftData["items"])if(g.value("tier","")==tier)pick.push_back(g.value("id",""));
 if(pick.empty())for(auto& g:giftData["items"])pick.push_back(g.value("id",""));
 for(const auto& [owned,qty]:gifts)if(qty>0)giftKnown.insert(owned);
 auto id=pick[rng()%pick.size()];if(giftKnown.insert(id).second)giftNew.insert(id);++gifts[id];
 sfx("sfx_capsule_open");toast("캡슐 : "+giftName(id)+" 획득!");
}
std::string Yumeno::reaction(const std::string& slug,const std::string& kind)const{
 if(!reactions.contains(slug))return "…고마워.";
 auto& r=reactions[slug];if(r.contains(kind))return r[kind].get<std::string>();
 return kind=="normal"&&r.contains("like")?r["like"].get<std::string>():kind=="like"&&r.contains("love")?r["love"].get<std::string>():std::string("…고마워.");
}
// 이름표 첫 글자 색 : 인물 머리색 (docs/spec/06 §1-2)
Color Yumeno::nameColor(const std::string& slug)const{
 static const std::map<std::string,Color> c{{"rei",{.85f,.88f,.95f,1}},{"sora",{1,.8f,.2f,1}},{"ken",{.75f,.15f,.3f,1}},{"nana",{.78f,.65f,1,1}},{"riku",{1,.55f,.15f,1}},
  {"akari",{.6f,.35f,.2f,1}},{"yuu",{.2f,.8f,.8f,1}},{"koto",{.95f,.75f,.4f,1}},{"satsuki",{.45f,.6f,.3f,1}},{"taiga",{.6f,.6f,.65f,1}},{"rin",{.55f,.3f,.85f,1}},
  {"sho",{.65f,.55f,.45f,1}},{"ai",{.5f,1,.8f,1}},{"haruka",{1,.5f,.7f,1}},{"kaede",{.35f,.45f,.85f,1}},{"lappy",{1,.45f,.7f,1}}};
 auto it=c.find(slug);return it==c.end()?Color{1,1,1,1}:it->second;
}
std::string Yumeno::giftName(const std::string& id)const{for(auto& g:giftData["items"])if(g.value("id","")==id)return g.value("name",id);return id;}
std::string Yumeno::kotodamaName(const std::string& id)const{if(v4.active&&v4.evidence.contains(id))return v4.evidence[id].value("name",id);return kotodama.contains(id)?kotodama[id].value("name",id):id;}
std::string Yumeno::kotodamaText(const std::string& id)const{if(v4.active&&v4.evidence.contains(id))return v4.evidence[id].value("text",std::string());return kotodama.contains(id)?kotodama[id].value("text",""):"";}
// 선물 : 화면 안의 페이지별 선택지 + 「주지 않는다」
void Yumeno::showGifts(){
 giftOrder.clear();for(auto& [id,n]:gifts)if(n>0)giftOrder.push_back(id);
 if(giftOrder.empty()){slotDone();return;}
 // 3열×4행: 10종 + 다음 쪽 + 주지 않는다. 마지막 조작도 화면 안에 남긴다.
 giftHover=0;gridSlugs.clear();
 if(giftOrder.size()>11){int pages=int((giftOrder.size()+9)/10);giftPage%=pages;
  for(int k=giftPage*10;k<std::min<int>(giftOrder.size(),giftPage*10+10);k++)gridSlugs.push_back(giftOrder[k]);gridSlugs.push_back("#next");}
 else gridSlugs=giftOrder;
 gridSlugs.push_back("");
 hideExplore();hideFlow();dialogVisible(false);mode=Mode::Grid;
 if(!lastBackground.empty()){UI::SetTexture(this,UI_ID,"Background",lastBackground);UI::SetVisible(this,UI_ID,"Background",true);}
 // 받는 사람 : 왼쪽 큰 입상(V3)
 UI::SetTexture(this,UI_ID,"Portrait","Assets/Art/sprites/"+giftTarget+"/"+giftTarget+"_C01.webp");UI::SetPosition(this,UI_ID,"Portrait",{-40,40});UI::SetSize(this,UI_ID,"Portrait",{620,680});UI::SetVisible(this,UI_ID,"Portrait",true);
 fvis("FShade",true);ftext("FGridHead",nameOf(giftTarget)+"에게 선물을 줄까?");fvis("FGridHead",true);
 for(int i=0;i<16;i++){
  bool on=i<int(gridSlugs.size());auto n=std::to_string(i);
  fvis("FCell"+n,on);UI::SetColor(this,flowui::ID,"FCell"+n,i==giftHover?Color{.1f,.32f,.55f,.95f}:Color{.04f,.06f,.1f,.9f});fvis("FName"+n,on);if(!on){fvis("FFace"+n,false);continue;}
  {auto c=cellAt(i);UI::SetPosition(this,flowui::ID,"FCell"+n,{c[0],c[1]});UI::SetSize(this,flowui::ID,"FCell"+n,{212,120});UI::SetPosition(this,flowui::ID,"FFace"+n,{c[0]+6,c[1]+6});UI::SetPosition(this,flowui::ID,"FName"+n,{c[0]+102,c[1]+14});UI::SetSize(this,flowui::ID,"FName"+n,{104,94});UI::SetSize(this,flowui::ID,"FFace"+n,{90,108});}
  auto& id=gridSlugs[i];auto icon=id.empty()?"":artPath("gifts",id,"gift",".webp");
  fvis("FFace"+n,!icon.empty());if(!icon.empty())UI::SetTexture(this,flowui::ID,"FFace"+n,icon);
  ftext("FName"+n,id.empty()?std::string("주지 않는다"):id=="#next"?"다음 쪽 ▶\n("+std::to_string(giftPage+1)+"/"+std::to_string((giftOrder.size()+9)/10)+")":giftName(id)+"\n×"+std::to_string(gifts[id]));
 }
 ftext("FGridFoot","좋아하는 선물이면 인연이 크게 오른다");fvis("FGridFoot",true);
}
void Yumeno::slotDone(){
 if(--slots>0){showMap();saveFlow();return;}
 nextBeat();
}

// 재판이 끝나면 (TrialRunner.hpp endTrial)
void Yumeno::trialDone(){
 UI::SetVisible(this,UI_ID,"Backdrop",true);fvis("FHud",true);showResult();
}
// 재판 결과 : 남은 발언력·재도전 횟수로 평가, 코인 보상
void Yumeno::showResult(){
 int h=debate.hearts;const char* grade=retries==0&&h>=4?"S":retries<=1&&h>=3?"A":retries<=3?"B":"C";
 int reward=grade[0]=='S'?30:grade[0]=='A'?20:grade[0]=='B'?15:10;coins+=reward;
 hideFlow();dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);mode=Mode::Card;resultPending=true;
 music("bgm_trial_end");
 fvis("FCardBack",true);fvis("FCard",false);ftext("FCardT",std::string("학급 재판 종료  ·  평가 ")+grade);fvis("FCardT",true);
 ftext("FCardS","남은 발언력 "+std::to_string(h)+"   다시 한 횟수 "+std::to_string(retries)+"   래피 코인 +"+std::to_string(reward));fvis("FCardS",true);
 sfx("sfx_coin");
}

void Yumeno::updateFlow(float delta,bool next,bool click){
 Vec2 m{0,0};Input::GetMousePositionForCanvas({1280,720},m);
 if(mode==Mode::Card){if(next){resultPending=false;nextBeat();}return;}
 if(mode==Mode::Credits){if(next){saveFlow();toTitle();}return;}
 if(mode==Mode::Menu){
  int pick=-1;
  if(menuCount>0){if(pressed("w")||pressed("ArrowUp"))menuHover=(menuHover+menuCount-1)%menuCount;if(pressed("s")||pressed("ArrowDown"))menuHover=(menuHover+1)%menuCount;
   if(enterNow)pick=menuHover;}
  for(int k=0;k<menuCount;k++)if(pressed(std::to_string(k+1)))pick=k;
  if(click)pick=menuAt(m.x,m.y);
  if(pick>=0)menuAccept(pick,0);
  return;
 }
 if(mode==Mode::Grid){
  int before=giftHover,n=int(gridSlugs.size());
  if(n>0){if(pressed("a"))giftHover=(giftHover+n-1)%n;if(pressed("d"))giftHover=(giftHover+1)%n;if(pressed("w"))giftHover=std::max(0,giftHover-3);if(pressed("s"))giftHover=std::min(n-1,giftHover+3);}
  if(before!=giftHover)for(int i=0;i<n;i++)UI::SetColor(this,flowui::ID,"FCell"+std::to_string(i),i==giftHover?Color{.1f,.32f,.55f,.95f}:Color{.04f,.06f,.1f,.9f});
  if(enterNow&&n>0){gridPicked(giftHover);return;}
  if(click){int i=gridAt(m.x,m.y);if(i>=0)gridPicked(i);}
  return;
 }
 if(currentBeat().value("t","")=="execution"||shakeTimer>0){ // 처형 키프레임은 천천히 다가가고, 엘리베이터는 흔들린다
  kenTime+=delta;float z=1+.06f*std::min(1.f,kenTime/6),sx=shakeTimer>0?std::sin(kenTime*40)*3:0;if(shakeTimer>0)shakeTimer-=delta;
  UI::SetScale(this,UI_ID,"Background",{z,z});UI::SetPosition(this,UI_ID,"Background",{-40-12*std::min(1.f,kenTime/6)+sx,-24});
 }
 if(mode==Mode::Story){
  if(int(shown)<lineLength){shown=std::min(float(lineLength),shown+delta*optv4::CharactersPerSecond(optionsV4));text("Body",u8prefix(dialogueText(),int(shown)));}
  else{blink+=delta;bool on=std::fmod(blink,.8f)<.5f;if(on!=nextShown){nextShown=on;UI::SetVisible(this,UI_ID,"Next",on);}}
  if(optv4::ReportRead(optionsV4,int(shown)>=lineLength&&dialogueFinal()))readLegacy.insert(optionsV4.line.id);
   if(optv4::AutoAdvance(optionsV4,delta,int(shown)>=lineLength))next=true;
   if(optv4::CanSkip(optionsV4,Input::IsKeyDown("Control"))){skipTimer+=delta;if(skipTimer>.05f){skipTimer=0;shown=float(lineLength);next=true;}}
  if(next)advanceFlow();
 }
}

// 자동 진행 검증용 : 지금 넣어야 할 입력 (tools/verify-flow.mjs)
Json Yumeno::autoFlow()const{
 if(mode==Mode::Explore||mode==Mode::Map||mode==Mode::Confirm||mode==Mode::Popup)return autoExplore();
 if(mode==Mode::Menu){
  int i=0;
  if(menuKind==MenuKind::Gift)i=0;
  return menuPending>=0?Json{{"kind","wait"}}:menuAuto(i);
 }
 if(mode==Mode::Grid){
  int i=0; // 선물 칸 : 첫 선물
  auto c=cellAt(i);return Json{{"kind","click"},{"x",c[0]+60},{"y",c[1]+60}};
 }
 return Json{{"kind","key"},{"key","Enter"}};
}
