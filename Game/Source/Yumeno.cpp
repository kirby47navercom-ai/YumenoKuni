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
  std::string pad;
  for(auto& r:rules["rules"])pad+=r.value("no","")+"   "+r.value("text","")+"\n";
  UI::Show(this,"Assets/UI/Main.hbwidget.json",UI_ID);
  text("PadBody",pad);
  return;
 }
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
 if(mode==Mode::End){text("Body",line);UI::SetVisible(this,UI_ID,"Portrait",false);}
}

std::string Yumeno::Stats()const{
 const char* names[]{"title","story","pad","end"};
 return Json{{"mode",names[int(mode)]},{"file",fileIndex},{"scene",scene},{"event",event},{"speaker",speaker},{"portrait",portrait},{"line",line},{"shown",int(shown)},{"length",lineLength}}.dump();
}
