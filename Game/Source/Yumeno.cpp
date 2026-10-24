#include "Yumeno.h"
using namespace hb;

namespace {
const char* UI_ID="main";
const char* SAVE_SLOT="yumeno-progress-v1";
// 화자 이름(괄호 앞) → 스프라이트 폴더
const std::map<std::string,std::string> slugs{{"미오","mio"},{"레이","rei"},{"소라","sora"},{"켄","ken"},{"나나","nana"},{"리쿠","riku"},{"아카리","akari"},{"유우","yuu"},{"코토","koto"},{"사츠키","satsuki"},{"타이가","taiga"},{"린","rin"},{"쇼","sho"},{"아이","ai"},{"하루카","haruka"},{"카에데","kaede"},{"래피","lappy"}};
// emotion.json 의 표정 ID → 공통 포즈 (docs/spec/12 §1)
const std::map<std::string,std::string> poses{{"neutral","C01"},{"smile","C02"},{"surprise","C04"},{"anger","C05"},{"sad","C06"},{"worry","C09"},{"serious","C12"},{"closed","C14"},{"whisper","C10"}};
const std::map<std::string,std::string> lappyPoses{{"neutral","L01"},{"smile","L01"},{"anger","L02"},{"surprise","L03"},{"serious","L04"},{"sad","L05"},{"whisper","L06"},{"worry","L05"},{"closed","L06"}};

int u8len(const std::string& s){int n=0;for(unsigned char c:s)if((c&0xC0)!=0x80)++n;return n;}
std::string u8prefix(const std::string& s,int count){
 int n=0;size_t i=0;
 for(;i<s.size();++i)if((static_cast<unsigned char>(s[i])&0xC0)!=0x80){if(n==count)break;++n;}
 return s.substr(0,i);
}
std::string baseName(const std::string& speaker){auto p=speaker.find('(');return p==std::string::npos?speaker:speaker.substr(0,p);}
}

bool Yumeno::pressed(const std::string& key){bool now=Input::IsKeyDown(key),edge=now&&!held[key];held[key]=now;return edge;}
void Yumeno::text(const std::string& id,const std::string& value){if(texts.count(id)&&texts[id]==value)return;texts[id]=value;UI::SetText(this,UI_ID,id,value);}

void Yumeno::loadFile(int index){
 fileIndex=index;
 file=Data::Get("Assets/Data/scenes/"+story["files"][index].get<std::string>()+".json");
}

void Yumeno::start(int fileAt,int sceneAt,int eventAt){
 loadFile(fileAt);scene=sceneAt;event=eventAt;mode=Mode::Story;portrait.clear();
 UI::SetVisible(this,UI_ID,"Title",false);
 present();
}

void Yumeno::save(){
 try{Save::Write(SAVE_SLOT,Json{{"file",fileIndex},{"scene",scene},{"event",event}});}catch(const std::exception&){}
}

// 현재 이벤트를 화면에 올린다. 표시할 게 없는 이벤트(break 등)는 건너뛴다.
void Yumeno::present(){
 auto& scenes=file["scenes"];
 while(true){
  if(scene>=int(scenes.size())){
   if(fileIndex+1<int(story["files"].size())){loadFile(fileIndex+1);scene=0;event=0;continue;}
   mode=Mode::End;line="— 체험판은 여기까지입니다. —";speaker.clear();break;
  }
  auto& events=scenes[scene]["events"];
  if(event>=int(events.size())){++scene;event=0;portrait.clear();save();continue;}
  auto& e=events[event];
  auto type=e.value("type","");
  if(type=="say"){
   speaker=baseName(e.value("speaker",""));
   bool monologue=e.value("kind","")=="monologue";
   line=e.value("text","");
   auto slug=slugs.count(speaker)?slugs.at(speaker):"";
   if(!slug.empty()&&slug!="mio"){
    auto emo=emotions.value(e.value("emo",""),std::string("neutral"));
    auto& table=slug=="lappy"?lappyPoses:poses;
    auto code=table.count(emo)?table.at(emo):(slug=="lappy"?"L01":"C01");
    portrait="Assets/Art/sprites/"+slug+"/"+slug+"_"+code+".webp";
   }
   UI::SetColor(this,UI_ID,"Body",monologue?Color{.62f,.84f,1,1}:Color{.96f,.94f,.97f,1});
   if(monologue)speaker.clear();
   break;
  }
  if(type=="stage"||type=="ui"||type=="choice"){
   speaker.clear();
   line=type=="ui"?"【안내】 "+e.value("text",""):type=="choice"?"▶ "+e.value("text",""):e.value("text","");
   UI::SetColor(this,UI_ID,"Body",type=="stage"?Color{.8f,.75f,.85f,1}:type=="ui"?Color{1,.86f,.45f,1}:Color{1,.6f,.8f,1});
   break;
  }
  ++event;
 }
 lineLength=u8len(line);shown=0;
 bool named=!speaker.empty();
 UI::SetVisible(this,UI_ID,"Nameplate",named);UI::SetVisible(this,UI_ID,"Name",named);
 text("Name",speaker);
 UI::SetVisible(this,UI_ID,"Portrait",!portrait.empty());
 if(!portrait.empty())UI::SetTexture(this,UI_ID,"Portrait",portrait);
 if(scene<int(file["scenes"].size()))text("SceneTitle",file["scenes"][scene].value("title",""));
 text("Body","");
}

void Yumeno::dialogVisible(bool visible){
 for(auto id:{"DialogFrame","Nameplate","Name","Body","Hint","SceneTitle"})UI::SetVisible(this,UI_ID,id,visible);
}

void Yumeno::message(const std::string& value,float seconds){text("TrialMsg",value);UI::SetVisible(this,UI_ID,"TrialMsg",true);messageTimer=seconds;}

void Yumeno::showBullet(){
 if(bullets.empty())return;
 auto& b=bullets[bullet];
 text("Bullet","언령  ◀ "+b.second+" ▶   ("+std::to_string(bullet+1)+"/"+std::to_string(bullets.size())+")");
}

void Yumeno::startDebate(int at){
 auto& list=trials["debates"];
 if(at>=int(list.size())){
  mode=Mode::End;UI::SetVisible(this,UI_ID,"Trial",false);dialogVisible(true);UI::SetVisible(this,UI_ID,"Portrait",false);
  speaker.clear();line="— 1장 논스톱 논의 체험 끝. Enter로 타이틀 —";text("Name","");text("Body",line);text("SceneTitle","");
  UI::SetVisible(this,UI_ID,"Nameplate",false);UI::SetVisible(this,UI_ID,"Name",false);
  return;
 }
 debateAt=at;auto& d=list[at];
 int hearts=debate.lines.empty()?5:debate.hearts; // 발언력은 재판 내내 이어짐
 debate=debate::State{};
 for(auto& l:d["lines"]){
  debate::Line x{l.value("speaker",""),l.value("text",""),l.value("kind","plain")};
  if(l.contains("weak")){x.word=l["weak"].value("word","");x.answer=l["weak"].value("answer","");x.start=l["weak"].value("start",0);}
  debate.lines.push_back(x);
 }
 debate.broken.assign(debate.lines.size(),false);debate.hearts=hearts;
 bullets.clear();for(auto& b:d["bullets"])bullets.emplace_back(b.value("id",""),b.value("name",""));
 bullet=0;shownLine=-1;shownHearts=-1;clearTimer=0;
 mode=Mode::Trial;dialogVisible(false);UI::SetVisible(this,UI_ID,"Title",false);UI::SetVisible(this,UI_ID,"Trial",true);
 showBullet();message("논스톱 논의 개시!",1.6f);
}

void Yumeno::updateDebate(float delta){
 // 타이머 : 메시지·컷인·논의 종료
 if(messageTimer>0&&(messageTimer-=delta)<=0)UI::SetVisible(this,UI_ID,"TrialMsg",false);
 if(cutinTimer>0&&(cutinTimer-=delta)<=0)UI::SetVisible(this,UI_ID,"Cutin",false);
 if(clearTimer>0){if((clearTimer-=delta)<=0)startDebate(debateAt+1);return;}
 bool changed=debate.tick(delta)||shownLine!=debate.index;
 auto& l=debate.line();auto o=debate.layout();
 if(changed){
  shownLine=debate.index;
  bool weak=l.kind=="weak";
  text("StmtPre",weak?debate::u8sub(l.text,0,l.start):l.text);
  text("StmtWeak",weak?l.word:"");
  text("StmtPost",weak?debate::u8sub(l.text,l.start+debate::u8len(l.word),1<<20):"");
  for(auto id:{"StmtPre","StmtWeak","StmtPost"})UI::SetFontSize(this,UI_ID,id,o.size);
  UI::SetColor(this,UI_ID,"StmtPre",l.kind=="agree"?Color{.45f,.78f,1,1}:l.kind=="noise"?Color{.75f,.72f,.78f,1}:Color{1,1,1,1});
  UI::SetPosition(this,UI_ID,"StmtPre",{0,0});UI::SetSize(this,UI_ID,"StmtPre",{o.pre+8,o.size*1.4f});
  UI::SetPosition(this,UI_ID,"StmtWeak",{o.pre,0});UI::SetSize(this,UI_ID,"StmtWeak",{o.weak+8,o.size*1.4f});
  UI::SetPosition(this,UI_ID,"StmtPost",{o.pre+o.weak,0});UI::SetSize(this,UI_ID,"StmtPost",{o.post+8,o.size*1.4f});
  text("TrialSpeaker",l.speaker);
  auto slug=slugs.count(l.speaker)?slugs.at(l.speaker):"";
  portrait=slug.empty()||slug=="mio"?"":"Assets/Art/sprites/"+slug+"/"+slug+"_"+(slug=="lappy"?"L01":weak?"T02":l.kind=="agree"?"T03":"C02")+".webp";
  UI::SetVisible(this,UI_ID,"Portrait",!portrait.empty());if(!portrait.empty())UI::SetTexture(this,UI_ID,"Portrait",portrait);
 }
 UI::SetPosition(this,UI_ID,"Stmt",{o.x,o.y});
 if(shownHearts!=debate.hearts){shownHearts=debate.hearts;for(int i=0;i<5;i++)UI::SetTexture(this,UI_ID,"Heart"+std::to_string(i),i<debate.hearts?"Assets/Art/ui/heart_full.png":"Assets/Art/ui/heart_empty.png");}
 // 조준 : 마우스 위치(뷰포트 픽셀). ponytail: 창 크기 1280×720 고정 가정.
 Vec2 m;if(Input::GetMousePosition(m)){aimX=m.x;aimY=m.y;}
 UI::SetPosition(this,UI_ID,"Aim",{aimX-32,aimY-32});
 if(!bullets.empty()){
  if(pressed("q")){bullet=(bullet+int(bullets.size())-1)%int(bullets.size());showBullet();}
  if(pressed("e")){bullet=(bullet+1)%int(bullets.size());showBullet();}
 }
 if(!pressed("mouse0")||bullets.empty())return;
 if(!debate.weakHit(aimX,aimY))return; // 빗나감 : 감점 없음
 if(bullets[bullet].first==l.answer){
  debate.broken[debate.index]=true;
  UI::SetVisible(this,UI_ID,"Cutin",true);cutinTimer=1.1f;
  if(debate.cleared()){message("논파 완료!",2.2f);clearTimer=2.4f;}
  else{message("논파!",1.0f);debate.next();}
 }else{
  if(--debate.hearts<=0){message("발언력이 바닥났어요… 처음부터!",2.f);debate.hearts=5;debate.broken.assign(debate.lines.size(),false);debate.index=0;debate.time=0;}
  else message("아야! 틀렸어요~!",1.2f);
 }
}

void Yumeno::advance(){
 if(mode!=Mode::Story)return;
 if(int(shown)<lineLength){shown=float(lineLength);text("Body",line);return;}
 ++event;present();
}

void Yumeno::Update(float delta){
 if(!ready){
  ready=true;
  story=Data::Get("Assets/Data/story.json");
  emotions=Data::Get("Assets/Data/emotion.json");
  rules=Data::Get("Assets/Data/rules.json");
  trials=Data::Get("Assets/Data/trials/"+story["trials"][0].get<std::string>()+".json");
  std::string pad;
  for(auto& r:rules["rules"])pad+=r.value("no","")+"   "+r.value("text","")+"\n";
  UI::Show(this,"Assets/UI/Main.hbwidget.json",UI_ID);
  text("PadBody",pad);
  return;
 }
 if(mode==Mode::Trial){updateDebate(delta);return;}
 bool next=pressed("Enter")|pressed("Space")|pressed("mouse0");
 if(pressed("Tab")&&(mode==Mode::Story||mode==Mode::Pad)){
  mode=mode==Mode::Pad?Mode::Story:Mode::Pad;
  UI::SetVisible(this,UI_ID,"Pad",mode==Mode::Pad);
  return;
 }
 if(mode==Mode::Title){
  if(pressed("c")){
   try{auto s=Json::parse(Save::ReadText(SAVE_SLOT));if(s.is_object()){start(s.value("file",0),s.value("scene",0),s.value("event",0));return;}}catch(const std::exception&){}
  }
  if(pressed("t")){startDebate(0);return;}
  if(next)start(0,0,0);
  return;
 }
 if(mode==Mode::Pad)return;
 if(mode==Mode::Story){
  // 타이핑 : 초당 40자. Ctrl 을 누르고 있으면 0.05초마다 넘김.
  if(int(shown)<lineLength){shown=std::min(float(lineLength),shown+delta*40);text("Body",u8prefix(line,int(shown)));}
  if(Input::IsKeyDown("Control")){skipTimer+=delta;if(skipTimer>.05f){skipTimer=0;shown=float(lineLength);advance();}}
  if(next)advance();
 }
 if(mode==Mode::End){
  text("Body",line);UI::SetVisible(this,UI_ID,"Portrait",false);
  if(next){mode=Mode::Title;debate=debate::State{};UI::SetVisible(this,UI_ID,"Title",true);}
 }
}

std::string Yumeno::Stats()const{
 const char* names[]{"title","story","pad","end","trial"};
 Json s{{"mode",names[int(mode)]},{"file",fileIndex},{"scene",scene},{"event",event},{"speaker",speaker},{"portrait",portrait},{"line",line},{"shown",int(shown)},{"length",lineLength}};
 if(mode==Mode::Trial&&!debate.lines.empty()){
  auto o=debate.layout();auto& l=debate.line();int broken=0;for(bool b:debate.broken)broken+=b;
  s["trial"]={{"debate",debateAt},{"index",debate.index},{"kind",l.kind},{"answer",l.answer},{"hearts",debate.hearts},{"broken",broken},{"bullet",bullets.empty()?"":bullets[bullet].first},{"aim",{aimX,aimY}},{"weakRect",{o.x+o.pre,o.y,o.weak,o.size*1.4f}},{"clearing",clearTimer>0}};
 }
 return s.dump();
}
