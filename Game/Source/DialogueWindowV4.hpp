#include "DialogueTextV4.hpp"
namespace dialogueui {
inline std::string piece(const std::string& file,const char* part){
 const auto dot=file.find_last_of('.'),slash=file.find_last_of("/\\");
 if(dot==std::string::npos||(slash!=std::string::npos&&dot<slash))return file+"_"+part+".png";
 return file.substr(0,dot)+"_"+part+file.substr(dot);
}
inline const hb::Json& layout(){static const hb::Json value=hb::Data::Get("Assets/Data/v4_story/dialogue_layout.json");return value;}
}
void Yumeno::dialogueSurface(bool trial){
 dialogueTrial=trial;const auto& l=dialogueui::layout();
 auto rect=[&](const char* id,float x,float y,float w,float h){if(std::string(id)=="Body"){x-=640;y-=720;}else if(std::string(id)=="Next"){x-=1280;y-=720;}UI::SetPosition(this,UI_ID,id,{x,y});UI::SetSize(this,UI_ID,id,{w,h});};
 if(trial){
  UI::SetFont(this,UI_ID,"Body","Assets/Fonts/pretendard/Pretendard-Regular.otf");
  UI::SetTexture(this,UI_ID,"DialogueOrnament",l["trial"]["frameAssets"][std::to_string(std::clamp(chapterAt,1,6))].get<std::string>());
  // Own absent-WIN policy is explicit Normal/Down/Center/in, not a native default claim.
  rect("DialogFrame",0,0,340,720);
  const auto& b=l["trial"]["body"];rect("Body",b[0],b[1],b[2],b[3]);UI::SetFontSize(this,UI_ID,"Body",l["trial"]["font"].get<float>());const auto& n=l["trial"][optionsV4.values.autoRead?"autoRect":"next"];rect("Next",n[0],n[1],n[2],n[3]);UI::SetTexture(this,UI_ID,"Next",l["trial"][optionsV4.values.autoRead?"autoAsset":"nextAsset"].get<std::string>());
 }else{
  UI::SetFont(this,UI_ID,"Body","Assets/Fonts/pretendard/Pretendard-Medium.otf");
  rect("DialogFrame",0,0,1280,720);
  const auto& b=l["body"];rect("Body",b[0],b[1],b[2],b[3]);UI::SetFontSize(this,UI_ID,"Body",l["font"].get<float>());
  const char* phase=playerProgress.phase==1?"night":playerProgress.phase==2?"close":"day";const auto& palette=l["advSource"]["palettes"][phase];
  const auto& n=palette[optionsV4.values.autoRead?"autoRect":"next"];rect("Next",n[0],n[1],n[2],n[3]);
  UI::SetTexture(this,UI_ID,"Next",palette[optionsV4.values.autoRead?"autoAsset":"nextAsset"].get<std::string>());
 }
}
void Yumeno::dialogueName(){
 const auto& l=dialogueui::layout();const auto& assets=dialogueTrial?l["trial"]["nameAssets"]:l["nameAssets"];std::string display=speaker,appearance;
 if(dialogueTrial&&v4.active){const auto& cue=v4QueueActive&&v4QueueAt>=0&&v4QueueAt<int(v4Queue.size())?v4Queue[v4QueueAt]:v4.current();appearance=cue.value("appearanceActor",cue.value("actor",std::string()));if(display.empty()&&cue.value("mono",false)&&!appearance.empty())display=nameOf(appearance);}
 const bool named=!display.empty()&&assets.contains(display);if(appearance.empty()&&slugs.count(baseName(display)))appearance=slugs.at(baseName(display));
 dialogueHero=!dialogueTrial&&speaker==l["ownPlayer"]["displayName"].get<std::string>();const auto branch=dialogueHero?"hero":"normal";
 UI::SetVisible(this,UI_ID,"DialogueOrnament",dialogueTrial); if(dialogueTrial){auto ch=std::to_string(std::clamp(chapterAt,1,6));bool card=named&&l["trial"]["iconAssets"].contains(appearance);auto frame=card?l["trial"]["frameAssets"][ch].get<std::string>():l["trial"]["framePlainAsset"].get<std::string>();auto body=l["trial"][card?"bodyAsset":"bodyPlainAsset"].get<std::string>();
  UI::SetSize(this,UI_ID,"DialogueOrnament",{340,720});
  for(auto part:{"left","middle","right"}){auto suffix=std::string(part)=="left"?std::string():std::string(part)=="middle"?std::string("Middle"):std::string("Right");UI::SetTexture(this,UI_ID,"DialogueOrnament"+suffix,dialogueui::piece(frame,part));UI::SetTexture(this,UI_ID,"DialogFrame"+suffix,dialogueui::piece(body,part));}}
 for(auto id:{"DialogFrameMiddle","DialogFrameRight","DialogueOrnamentMiddle","DialogueOrnamentRight"})UI::SetVisible(this,UI_ID,id,dialogueTrial);
 if(!dialogueTrial){const char* phase=playerProgress.phase==1?"night":playerProgress.phase==2?"close":"day";UI::SetTexture(this,UI_ID,"DialogFrame",l["advSource"]["palettes"][phase]["branches"][named?branch:"nameless"].get<std::string>());}
 for(auto id:{"Nameplate","Name"})UI::SetVisible(this,UI_ID,id,named);UI::SetVisible(this,UI_ID,"NameHead",false);
 if(!named)return;const auto& b=dialogueTrial?l["trial"]["icon"]:l["namebase"][branch];const auto& n=dialogueTrial?l["trial"]["name"]:l["names"][branch];
 auto slug=dialogueTrial?appearance:slugs.count(speaker)?slugs.at(speaker):std::string();bool icon=!dialogueTrial||l["trial"]["iconAssets"].contains(slug);UI::SetVisible(this,UI_ID,"Nameplate",icon);
 if(icon)UI::SetTexture(this,UI_ID,"Nameplate",dialogueTrial?l["trial"]["iconAssets"][slug].get<std::string>():"Assets/Art/ui/v3/dialogue/namebase.svg");
 UI::SetPosition(this,UI_ID,"Nameplate",{b[0],b[1]});UI::SetSize(this,UI_ID,"Nameplate",{b[2],b[3]});
 UI::SetPosition(this,UI_ID,"Name",{n[0],n[1]});UI::SetSize(this,UI_ID,"Name",{n[2],n[3]});UI::SetTexture(this,UI_ID,"Name",assets[display].get<std::string>());
}
void Yumeno::dialoguePortrait(){
 if(dialogueTrial)return;const auto& p=dialogueui::layout().at("portrait");auto actorName=baseName(speaker);
 auto file=portrait.substr(portrait.find_last_of('/')+1),key=file.substr(0,file.find_first_of("_."));
 for(const auto& [display,slug]:slugs)if(slug==key)actorName=display;
 const auto& heights=p.at("heightCmByName");float cm=heights.contains(actorName)?heights.at(actorName).get<float>():160.f;
 float h=p.at("referenceImageHeight").get<float>()*cm/p.at("referenceHeightCm").get<float>();
 if(key=="lappy"){UI::SetPosition(this,UI_ID,"Portrait",{290,0});UI::SetSize(this,UI_ID,"Portrait",{700,700});return;}
 UI::SetPosition(this,UI_ID,"Portrait",{0,p.at("top").get<float>()});UI::SetSize(this,UI_ID,"Portrait",{1280,h});
}
void Yumeno::dialoguePrepare(){
 dialogueSurface(mode==Mode::Trial||v4Court||inScript);dialogueName();const auto& l=dialogueui::layout();
 dialoguePortrait();
 float size=dialogueTrial?l["trial"]["font"].get<float>():l["font"].get<float>(),width=dialogueTrial?l["trial"]["body"][2].get<float>()-8:l["ownWrap"]["width"].get<float>();int rows=dialogueTrial?2:3;
 dialoguePages=dialoguetext::pages(line,width,rows,[&](const std::string& g){return flowchoice::width(g)*size/26.6666667f;},true);dialoguePage=0;
 lineLength=u8len(dialogueText());shown=0;blink=0;nextShown=false;UI::SetVisible(this,UI_ID,"Next",false);text("Body","");
}
const std::string& Yumeno::dialogueText()const{return dialoguePages.empty()?line:dialoguePages[dialoguePage].text;}
bool Yumeno::dialogueFinal()const{return dialoguePage+1>=int(dialoguePages.size());}
bool Yumeno::dialogueAdvance(){
 if(int(shown)<lineLength){shown=float(lineLength);text("Body",dialogueText());return false;}
 if(!Input::IsKeyDown("Control"))sfx("v3se_003"); // V3 BTN confirmation, after the text finishes.
 if(!dialogueFinal()){
  ++dialoguePage;lineLength=u8len(dialogueText());shown=0;blink=0;nextShown=false;UI::SetVisible(this,UI_ID,"Next",false);text("Body","");
  optionsV4.line.fullSeconds=0;optionsV4.line.fullSeen=false;return false;
 }return true;
}
std::string Yumeno::DialogueStats()const{return Json{{"page",dialoguePage},{"pages",dialoguePages.size()},{"final",dialogueFinal()},{"shown",shown},{"length",lineLength},{"hero",dialogueHero},{"trial",dialogueTrial},{"raw",line},{"text",dialogueText()},{"speaker",speaker}}.dump();}
