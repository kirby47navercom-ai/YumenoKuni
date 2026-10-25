// 장 진행 (docs/spec/09) : Assets/Data/flow/{P,1..6}.json 의 비트를 차례로 실행한다.
// 비트 : card · scene · freetime · investigate · trial · execution · ending · end   (tools/build_flow.py)
// Yumeno.cpp 끝에서 include 한다.
#include <random>
namespace flowui {
const char* ID="flow";
constexpr float OPT_X=340,OPT_Y=200,OPT_W=600,OPT_H=50,OPT_STEP=58; // 보기 목록
constexpr float CELL_X=150,CELL_Y=110,CELL_W=236,CELL_H=120,CELL_DX=250,CELL_DY=130; // 인물·선물 칸 4×4
const int LEVELS[]{0,4,10,18,28}; // 인연 Lv1~5 누적 포인트 (00 §5-2)
}

void Yumeno::ftext(const std::string& id,const std::string& v){if(ftexts.count(id)&&ftexts[id]==v)return;ftexts[id]=v;UI::SetText(this,flowui::ID,id,v);}
void Yumeno::fvis(const std::string& id,bool v){if(fvisible.count(id)&&fvisible[id]==v)return;fvisible[id]=v;UI::SetVisible(this,flowui::ID,id,v);}
std::string Yumeno::artPath(const std::string& group,const std::string& name,const std::string& dir,const std::string& ext)const{
 if(!art.contains(group))return "";
 for(auto& n:art[group])if(n.get<std::string>()==name)return "Assets/Art/"+dir+"/"+name+ext;
 return "";
}
void Yumeno::music(const std::string& cue){
 if(cue==musicCue)return;musicCue=cue;
 if(art.contains("audio")&&art["audio"].contains(cue))Audio::PlayMusic(art["audio"][cue].get<std::string>(),1.f);
}
int Yumeno::level(const std::string& slug)const{int p=bonds.count(slug)?bonds.at(slug):0,l=1;for(int i=1;i<5;i++)if(p>=flowui::LEVELS[i])l=i+1;return l;}
void Yumeno::addBond(const std::string& slug,int points){int before=level(slug);bonds[slug]=std::max(0,bonds[slug]+points);if(level(slug)>before)toast(nameOf(slug)+" 인연 Lv"+std::to_string(level(slug))+"!");}
void Yumeno::toast(const std::string& v){ftext("FToast",v);fvis("FToast",true);toastTimer=2.2f;}
void Yumeno::hud(){
 std::string ch=chapter.value("chapter","P");
 ftext("FHud",ch=="P"?std::string("프롤로그"):"제"+ch+"장");
 int total=0;for(auto& [k,v]:bonds)total+=v;
 ftext("FHudSub","Lv "+std::to_string(1+total/12)+"     ◎ "+std::to_string(coins));
}

// 저장 : 장·비트·이벤트·문맥 + 인연·코인·선물·언령·플래그
void Yumeno::saveFlow(){
 Json s{{"v",2},{"chapter",chapterAt},{"beat",beat},{"event",event},{"pool",ctxPool},{"spot",ctxSpot},{"ending",ctxEnding},{"slots",slots},
  {"coins",coins},{"pulls",pulls},{"bonds",bonds},{"gifts",gifts},{"cards",std::vector<std::string>(cards.begin(),cards.end())},{"flags",std::vector<std::string>(flags.begin(),flags.end())},{"seen",std::vector<std::string>(seen.begin(),seen.end())}};
 try{Save::Write(SAVE_SLOT,s);}catch(const std::exception&){}
}
bool Yumeno::loadFlow(){
 try{
  auto s=Json::parse(Save::ReadText(SAVE_SLOT));
  if(!s.is_object()||s.value("v",0)!=2)return false;
  coins=s.value("coins",0);pulls=s.value("pulls",0);bonds=s.value("bonds",std::map<std::string,int>{});gifts=s.value("gifts",std::map<std::string,int>{});
  cards.clear();for(auto& c:s["cards"])cards.insert(c.get<std::string>());
  flags.clear();for(auto& c:s["flags"])flags.insert(c.get<std::string>());
  seen.clear();for(auto& c:s["seen"])seen.insert(c.get<std::string>());
  openChapter(s.value("chapter",0));beat=s.value("beat",0);
  ctxPool=s.value("pool",-1);ctxSpot=s.value("spot",-1);ctxEnding=s.value("ending",-1);slots=s.value("slots",0);
  auto t=currentBeat().value("t","");
  if(t=="scene"||t=="execution"||ctxEnding>=0){event=s.value("event",0);showStory();flowPresent();}
  else{ctxPool=ctxSpot=-1;enterBeat();}
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
 coins=10;pulls=0;bonds.clear();gifts.clear();cards.clear();flags.clear();seen.clear();
 openChapter(0);flowOn=true;
 UI::SetVisible(this,UI_ID,"Title",false);
 enterBeat();
}
void Yumeno::hideFlow(){
 for(auto id:{"FCardBack","FCard","FCardT","FCardS","FShade","FMenuQ","FGridHead","FGridFoot","FCredits"})fvis(id,false);
 for(int i=0;i<9;i++){fvis("FOptP"+std::to_string(i),false);fvis("FOptT"+std::to_string(i),false);}
 for(int i=0;i<16;i++){fvis("FCell"+std::to_string(i),false);fvis("FFace"+std::to_string(i),false);fvis("FName"+std::to_string(i),false);}
}
void Yumeno::showStory(){
 hideFlow();mode=Mode::Story;
 UI::SetVisible(this,UI_ID,"Backdrop",true);dialogVisible(true);hud();fvis("FHud",true);
}
void Yumeno::nextBeat(){++beat;event=0;ctxPool=ctxSpot=ctxEnding=-1;enterBeat();}
void Yumeno::enterBeat(){
 if(beat>=int(chapter["beats"].size())){
  if(chapterAt+1>=int(story["chapters"].size())){toTitle();return;}
  openChapter(chapterAt+1);
 }
 saveFlow();hud();
 auto& b=currentBeat();auto t=b.value("t","");
 if(t=="card"){
  hideFlow();dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);mode=Mode::Card;
  auto ch=b.value("chapter","P");auto img=artPath("cards","chapter_"+ch,"ui",".png");
  fvis("FCardBack",true);fvis("FCard",!img.empty());if(!img.empty())UI::SetTexture(this,flowui::ID,"FCard",img);
  ftext("FCardT",img.empty()?(ch=="P"?std::string("프롤로그"):"제"+ch+"장"):"");ftext("FCardS",img.empty()?b.value("title",""):"");
  fvis("FCardT",img.empty());fvis("FCardS",img.empty());
  music(ch=="P"?"bgm_pro_arrival":ch=="6"?"bgm_core":std::array<const char*,6>{"","bgm_daily_pastel","bgm_daily_summer","bgm_daily_night","bgm_daily_grey","bgm_daily_mono"}[std::stoi(ch)]);
  return;
 }
 if(t=="scene"||t=="execution"){
  if(b.contains("need")&&level(b["need"].value("who",""))<b["need"].value("level",3)){nextBeat();return;} // 유품 : 인연 Lv3 이상
  auto id=b.value("id","");
  if(id.find(":B-")!=std::string::npos&&id.find("b:")!=std::string::npos)music("bgm_discovery");
  else if(id.rfind("17:",0)==0)music("bgm_interlude");
  else if(t=="execution")music("bgm_punishment_time");
  else if(id.find("-M-")!=std::string::npos)music("bgm_motive");
  else if(id.find("-E-")!=std::string::npos)music("bgm_epilogue");
  showStory();event=0;flowPresent();return;
 }
 if(t=="freetime"){slots=b.value("slots",2);music("bgm_freetime");mapHover=0;showMap();band("free");return;}
 if(t=="investigate"){music("bgm_investigation");mapHover=0;showMap();band("inv");return;}
 if(t=="trial"){
  trialKey=b.value("key","11c");trialDead.clear();for(auto& d:b["dead"])trialDead.push_back(d.get<std::string>());
  trials=Data::Get("Assets/Data/trials/"+trialKey+".json");hideFlow();fvis("FHud",false);music("bgm_trial_main");startTrial();return;
 }
 if(t=="ending"){
  showStory();UI::SetVisible(this,UI_ID,"Portrait",false);
  std::vector<std::string> o;for(auto& x:b["options"])o.push_back(x.value("label",""));
  showMenu(b.value("q",""),o,MenuKind::Ending);return;
 }
 if(t=="end"){
  hideFlow();dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);mode=Mode::Credits;music("bgm_ending_a");
  auto bg=artPath("cards","credits_bg","ui",".png");fvis("FCardBack",true);fvis("FCard",!bg.empty());if(!bg.empty())UI::SetTexture(this,flowui::ID,"FCard",bg);
  ftext("FCredits","『유메노쿠니』\n\n끝까지 함께해 주셔서 고맙습니다.\n\n각본 · 기획 · 연출\n주인님\n\n그림\nNovelAI · Codex\n\n엔진\nHBEngine\n\n글꼴\nSIL Open Font License 글꼴들\n\n— Fin —");fvis("FCredits",true);
  return;
 }
 nextBeat();
}
void Yumeno::toTitle(){
 flowOn=false;hideFlow();fvis("FHud",false);dialogVisible(false);mode=Mode::Title;
 UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"Background",false);UI::SetVisible(this,UI_ID,"Title",true);music("bgm_title");
}

// 이벤트 하나를 화면에 올린다. 표시할 것이 없는 이벤트(bg·card·goto)는 처리하고 넘어간다.
void Yumeno::flowPresent(){
 while(true){
  auto& evs=flowEvents();
  if(event>=int(evs.size())||(eventEnd>=0&&event>=eventEnd)){eventsDone();return;}
  auto& e=evs[event];auto type=e.value("type","");
  if(type=="goto"){event=e.value("to",event+1);continue;}
  if(type=="bg"){
   auto bg=e.value("bg","");std::string path;
   if(bg.rfind("cg:death",0)==0)band("body");
   if(bg.rfind("cg:",0)==0){auto want=bg.substr(3);if(art.contains("cg"))for(auto& c:art["cg"]){auto n=c.get<std::string>();if(n.rfind(want,0)==0){path="Assets/Art/cg/"+n+".webp";break;}}}
   else path=artPath("backgrounds",bg,"bg",".webp");
   if(!path.empty()){UI::SetTexture(this,UI_ID,"Background",path);UI::SetVisible(this,UI_ID,"Background",true);if(bg.rfind("cg:",0)!=0)lastBackground=path;if(ctxSpot>=0&&bg.rfind("cg:",0)!=0)sceneBackground=path;}
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
   if(!keys.empty()){UI::SetTexture(this,UI_ID,"Background","Assets/Art/cg/"+keys[std::min<size_t>(event,keys.size()-1)]+".webp");UI::SetVisible(this,UI_ID,"Background",true);}
  }
  speaker.clear();portrait.clear();
  if(type=="say"){
   speaker=e.value("speaker","");line=e.value("text","");
   auto slug=slugs.count(speaker)?slugs.at(speaker):"";
   if(!slug.empty()&&slug!="mio"){
    auto emo=emotions.value(e.value("emo",""),std::string("neutral"));
    auto& table=slug=="lappy"?lappyPoses:poses;
    auto code=table.count(emo)?table.at(emo):(slug=="lappy"?"L01":"C01");
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
 lineLength=u8len(line);shown=0;
 bool named=!speaker.empty();
 UI::SetVisible(this,UI_ID,"Nameplate",named);UI::SetVisible(this,UI_ID,"Name",named);UI::SetVisible(this,UI_ID,"NameHead",named);UI::SetVisible(this,UI_ID,"Next",false);
 text("Name",speaker);text("NameHead",u8prefix(speaker,1));
 {auto slug=slugs.count(speaker)?slugs.at(speaker):"";UI::SetColor(this,UI_ID,"NameHead",nameColor(slug));}
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
 if(int(shown)<lineLength){shown=float(lineLength);text("Body",line);return;}
 if(after!=After::None){auto a=after;after=After::None;
  if(a==After::Gift)showGifts();else if(a==After::Slot)slotDone();else if(a==After::Explore)enterRoomBack();
  return;}
 ++event;flowPresent();
}

// 보기 목록 (선택지 · 수사 현장 · 엔딩 · 선물)
void Yumeno::showMenu(const std::string& q,const std::vector<std::string>& o,MenuKind kind){
 menuKind=kind;menuCount=std::min(9,int(o.size()));mode=Mode::Menu;
 fvis("FShade",true);ftext("FMenuQ",q);fvis("FMenuQ",!q.empty());
 for(int i=0;i<9;i++){bool on=i<menuCount;fvis("FOptP"+std::to_string(i),on);fvis("FOptT"+std::to_string(i),on);if(on)ftext("FOptT"+std::to_string(i),std::to_string(i+1)+".  "+o[i]);}
}
void Yumeno::hideMenu(){fvis("FShade",false);fvis("FMenuQ",false);for(int i=0;i<9;i++){fvis("FOptP"+std::to_string(i),false);fvis("FOptT"+std::to_string(i),false);}}
int Yumeno::menuAt(float x,float y)const{
 if(x<flowui::OPT_X||x>flowui::OPT_X+flowui::OPT_W||y<flowui::OPT_Y)return -1;
 int i=int((y-flowui::OPT_Y)/flowui::OPT_STEP);
 return i<menuCount&&y-flowui::OPT_Y-i*flowui::OPT_STEP<=flowui::OPT_H?i:-1;
}
void Yumeno::menuPicked(int i){
 hideMenu();auto& b=currentBeat();
 if(menuKind==MenuKind::Event){
  auto& o=flowEvents()[event]["options"][i];
  flags.insert(o.value("flag",""));event=o.value("to",event+1);showStory();flowPresent();return;
 }
 if(menuKind==MenuKind::Ending){ctxEnding=i;event=0;showStory();flowPresent();return;}
 if(menuKind==MenuKind::Investigate){
  if(i<int(spotOrder.size())){ctxSpot=spotOrder[i];event=0;showStory();flowPresent();return;}
  // 수사 종료 : 그 장의 언령을 모두 정리(증언 표·메모 포함)
  auto ch=chapter.value("chapter","1");int added=0;
  if(kotodama.is_object())for(auto& [id,name]:kotodama.items())if(id.size()>2&&id[1]==ch[0]&&cards.insert(id).second)++added;
  if(added)toast("언령 "+std::to_string(added)+"장을 수첩에 정리했다");
  nextBeat();return;
 }
 if(menuKind==MenuKind::Gift){giveGift(i);return;}
}
void Yumeno::giveGift(int i){
 {
  hideFlow();
  if(i>=int(giftOrder.size())){slotDone();return;}
  auto id=giftOrder[i];if(--gifts[id]<=0)gifts.erase(id);
  int delta=1;std::string pose="C02",kind="like";
  if(giftData["likes"].contains(giftTarget)){
   for(auto& g:giftData["likes"][giftTarget]["love"])if(g.get<std::string>()==id){delta=3;pose="T03";kind="love";}
   for(auto& g:giftData["likes"][giftTarget]["hate"])if(g.get<std::string>()==id){delta=-1;pose="C09";kind="hate";}
  }
  addBond(giftTarget,delta);sayOnce(giftTarget,reaction(giftTarget,kind),pose,After::Slot);return;
 }
}

// 프리타임 : 인물 칸 (이벤트가 남은 인물은 밝게)
void Yumeno::showFreeSelect(){
 hideFlow();dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);mode=Mode::Grid;gridKind=GridKind::Free;
 for(int i=0;i<16;i++)fvis("FFace"+std::to_string(i),false); // 선물 칸에서 쓰던 그림
 fvis("FShade",true);ftext("FGridHead","자유시간 — 남은 시간 "+std::to_string(slots)+"번");fvis("FGridHead",true);
 gridSlugs.clear();
 for(auto s:{"rei","sora","ken","nana","riku","akari","yuu","koto","satsuki","taiga","rin","sho","ai","haruka","kaede"})if(inPark(s))gridSlugs.push_back(s);
 for(int i=0;i<16;i++){
  bool on=i<int(gridSlugs.size());auto n=std::to_string(i);
  fvis("FCell"+n,on);fvis("FFace"+n,on);fvis("FName"+n,on);if(!on)continue;
  auto& s=gridSlugs[i];auto face=artPath("pad","face_"+s,"pad",".png");
  UI::SetTexture(this,flowui::ID,"FFace"+n,face.empty()?"Assets/Art/sprites/"+s+"/"+s+"_C02.webp":face);
  ftext("FName"+n,nameOf(s)+"\nLv"+std::to_string(level(s))+(poolOf(s)>=0?"  ★":""));
 }
 ftext("FGridFoot","◎ "+std::to_string(coins)+"     G  캡슐 머신(3코인)     ★ 새 이야기");fvis("FGridFoot",true);
}
int Yumeno::poolOf(const std::string& slug)const{
 auto& b=currentBeat();if(!b.contains("pool"))return -1;
 for(int i=0;i<int(b["pool"].size());i++){auto& p=b["pool"][i];if(p.value("who","")==slug&&!seen.count(p.value("id","")))return i;}
 return -1;
}
int Yumeno::gridAt(float x,float y)const{
 int c=int((x-flowui::CELL_X)/flowui::CELL_DX),r=int((y-flowui::CELL_Y)/flowui::CELL_DY);
 if(x<flowui::CELL_X||y<flowui::CELL_Y||c>3||r>3)return -1;
 if(x-flowui::CELL_X-c*flowui::CELL_DX>flowui::CELL_W||y-flowui::CELL_Y-r*flowui::CELL_DY>flowui::CELL_H)return -1;
 int i=r*4+c;return i<int(gridSlugs.size())?i:-1;
}
void Yumeno::gridPicked(int i){
 if(gridKind==GridKind::Gift){giveGift(i);return;}
 auto slug=gridSlugs[i];int p=poolOf(slug);
 if(p>=0){ctxPool=p;event=0;showStory();flowPresent();return;}
 addBond(slug,1);coins+=1;giftTarget=slug; // 이벤트를 다 본 인물 : 짧은 잡담
 sayOnce(slug,reaction(slug,"chat"),"C02",After::Gift);
}
void Yumeno::pullCapsule(){
 if(coins<3){toast("코인이 모자라요");return;}
 coins-=3;++pulls;
 static std::mt19937 rng{std::random_device{}()};
 int roll=int(rng()%100);std::string tier=roll<1?"장미":roll<10?"희귀":roll<40?"좋은":"일반";
 if(pulls%15==0&&(tier=="일반"||tier=="좋은"))tier="희귀"; // 15회마다 희귀 이상 보증
 std::vector<std::string> pick;for(auto& g:giftData["items"])if(g.value("tier","")==tier)pick.push_back(g.value("id",""));
 if(pick.empty())for(auto& g:giftData["items"])pick.push_back(g.value("id",""));
 auto id=pick[rng()%pick.size()];++gifts[id];
 toast("캡슐 : "+giftName(id)+" 획득!");
 if(gridKind==GridKind::Free&&mode==Mode::Grid)ftext("FGridFoot","◎ "+std::to_string(coins)+"     G  캡슐 머신(3코인)     ★ 새 이야기");
}
std::string Yumeno::reaction(const std::string& slug,const std::string& kind)const{
 return reactions.contains(slug)?reactions[slug].value(kind,std::string("…고마워.")):std::string("…고마워.");
}
// 이름표 첫 글자 색 : 인물 머리색 (docs/spec/06 §1-2)
Color Yumeno::nameColor(const std::string& slug)const{
 static const std::map<std::string,Color> c{{"rei",{.85f,.88f,.95f,1}},{"sora",{1,.8f,.2f,1}},{"ken",{.75f,.15f,.3f,1}},{"nana",{.78f,.65f,1,1}},{"riku",{1,.55f,.15f,1}},
  {"akari",{.6f,.35f,.2f,1}},{"yuu",{.2f,.8f,.8f,1}},{"koto",{.95f,.75f,.4f,1}},{"satsuki",{.45f,.6f,.3f,1}},{"taiga",{.6f,.6f,.65f,1}},{"rin",{.55f,.3f,.85f,1}},
  {"sho",{.65f,.55f,.45f,1}},{"ai",{.5f,1,.8f,1}},{"haruka",{1,.5f,.7f,1}},{"kaede",{.35f,.45f,.85f,1}},{"lappy",{1,.45f,.7f,1}}};
 auto it=c.find(slug);return it==c.end()?Color{1,1,1,1}:it->second;
}
std::string Yumeno::giftName(const std::string& id)const{for(auto& g:giftData["items"])if(g.value("id","")==id)return g.value("name",id);return id;}
std::string Yumeno::kotodamaName(const std::string& id)const{return kotodama.contains(id)?kotodama[id].value("name",id):id;}
std::string Yumeno::kotodamaText(const std::string& id)const{return kotodama.contains(id)?kotodama[id].value("text",""):"";}
// 선물 : 아이콘 칸 15 + 「주지 않는다」
void Yumeno::showGifts(){
 giftOrder.clear();for(auto& [id,n]:gifts)if(n>0)giftOrder.push_back(id);
 if(giftOrder.empty()){slotDone();return;}
 if(giftOrder.size()>15)giftOrder.resize(15);
 hideFlow();dialogVisible(false);mode=Mode::Grid;gridKind=GridKind::Gift;gridSlugs=giftOrder;gridSlugs.push_back("");
 fvis("FShade",true);ftext("FGridHead",nameOf(giftTarget)+"에게 선물을 줄까?");fvis("FGridHead",true);
 for(int i=0;i<16;i++){
  bool on=i<int(gridSlugs.size());auto n=std::to_string(i);
  fvis("FCell"+n,on);fvis("FName"+n,on);if(!on){fvis("FFace"+n,false);continue;}
  auto& id=gridSlugs[i];auto icon=id.empty()?"":artPath("gifts",id,"gift",".png");
  fvis("FFace"+n,!icon.empty());if(!icon.empty())UI::SetTexture(this,flowui::ID,"FFace"+n,icon);
  ftext("FName"+n,id.empty()?std::string("주지 않는다"):giftName(id)+"\n×"+std::to_string(gifts[id]));
 }
 ftext("FGridFoot","좋아하는 선물이면 인연이 크게 오른다");fvis("FGridFoot",true);
}
void Yumeno::slotDone(){
 if(--slots>0){saveFlow();showMap();return;}
 nextBeat();
}

// 수사 : 현장 목록. 모두 보면 「수사 종료」
void Yumeno::showInvestigate(){
 showStory();dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);
 auto& b=currentBeat();spotOrder.clear();std::vector<std::string> o;bool all=true;
 for(int i=0;i<int(b["spots"].size());i++){auto& s=b["spots"][i];bool done=seen.count(s.value("id",""))>0;all=all&&done;spotOrder.push_back(i);o.push_back((done?"✓ ":"")+s.value("spot",""));}
 if(spotOrder.size()>8){spotOrder.resize(8);o.resize(8);}
 if(all)o.push_back("수사 종료 — 재판장으로");
 showMenu(all?"충분히 조사한 것 같아.":"수사 — 어디를 조사할까?",o,MenuKind::Investigate);
}

// 재판이 끝나면 (TrialRunner.hpp endTrial)
void Yumeno::trialDone(){
 coins+=20;UI::SetVisible(this,UI_ID,"Backdrop",true);fvis("FHud",true);nextBeat();
}

// 패드 : 교칙 · 언령 · 선물 · 인연
void Yumeno::padPage(){
 static const char* tabs[]{"교칙","언령","선물","인연"};
 std::string head="래피 패드   ";for(int i=0;i<4;i++)head+=(i==padTab?std::string("【")+tabs[i]+"】 ":std::string(tabs[i])+"  ");
 text("PadHead",head);
 std::string body;
 if(padTab==0){for(auto& r:rules["rules"])body+=r.value("no","")+"   "+r.value("text","")+"\n";}
 if(padTab==1){if(cards.empty())body="아직 언령이 없다.";for(auto& c:cards)body+=c+"   "+kotodamaName(c)+"\n";}
 if(padTab==2){body="래피 코인 ◎ "+std::to_string(coins)+"\n\n";if(gifts.empty())body+="선물이 없다. 프리타임에 G 로 캡슐 머신을 돌릴 수 있다.";for(auto& [id,n]:gifts)body+=giftName(id)+"  ×"+std::to_string(n)+"\n";}
 if(padTab==3){for(auto s:{"rei","sora","ken","nana","riku","akari","yuu","koto","satsuki","taiga","rin","sho","ai","haruka","kaede"})body+=nameOf(s)+(flowOn&&!inPark(s)?"   (퇴장)":"")+"   Lv"+std::to_string(level(s))+"   "+std::string(level(s),'*')+"\n";}
 text("PadBody",body);
}

void Yumeno::updateFlow(float delta,bool next,bool click){
 if(toastTimer>0&&(toastTimer-=delta)<=0)fvis("FToast",false);
 Vec2 m{0,0};Input::GetMousePosition(m);
 if(mode==Mode::Card){if(next)nextBeat();return;}
 if(mode==Mode::Credits){if(next){saveFlow();toTitle();}return;}
 if(mode==Mode::Menu){
  int pick=-1;
  for(int k=0;k<menuCount;k++)if(pressed(std::to_string(k+1)))pick=k;
  if(click)pick=menuAt(m.x,m.y);
  if(pick>=0)menuPicked(pick);
  return;
 }
 if(mode==Mode::Grid){
  if(gridKind==GridKind::Free&&pressed("g"))pullCapsule();
  if(click){int i=gridAt(m.x,m.y);if(i>=0)gridPicked(i);}
  return;
 }
 if(mode==Mode::Story){
  if(int(shown)<lineLength){shown=std::min(float(lineLength),shown+delta*40);text("Body",u8prefix(line,int(shown)));}
  else{blink+=delta;bool on=std::fmod(blink,.8f)<.5f;if(on!=nextShown){nextShown=on;UI::SetVisible(this,UI_ID,"Next",on);}}
  if(Input::IsKeyDown("Control")){skipTimer+=delta;if(skipTimer>.05f){skipTimer=0;shown=float(lineLength);advanceFlow();}}
  if(next)advanceFlow();
 }
}

// 자동 진행 검증용 : 지금 넣어야 할 입력 (tools/verify-flow.mjs)
Json Yumeno::autoFlow()const{
 if(mode==Mode::Explore||mode==Mode::Map||mode==Mode::Confirm||mode==Mode::Popup)return autoExplore();
 if(mode==Mode::Menu){
  int i=0;
  if(menuKind==MenuKind::Investigate){auto& b=currentBeat();i=menuCount-1;for(int k=0;k<int(spotOrder.size());k++)if(!seen.count(b["spots"][spotOrder[k]].value("id",""))){i=k;break;}}
  if(menuKind==MenuKind::Gift)i=0;
  return Json{{"kind","click"},{"x",flowui::OPT_X+60},{"y",flowui::OPT_Y+i*flowui::OPT_STEP+flowui::OPT_H/2}};
 }
 if(mode==Mode::Grid){
  int i=0;for(int k=0;k<int(gridSlugs.size());k++)if(poolOf(gridSlugs[k])>=0){i=k;break;}
  if(gridKind==GridKind::Gift)i=0;
  else if(coins>=3&&gifts.empty())return Json{{"kind","key"},{"key","g"}};
  return Json{{"kind","click"},{"x",flowui::CELL_X+(i%4)*flowui::CELL_DX+60},{"y",flowui::CELL_Y+(i/4)*flowui::CELL_DY+60}};
 }
 return Json{{"kind","key"},{"key","Enter"}};
}
