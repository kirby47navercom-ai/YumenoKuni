#pragma once
#include <HBEngine/Game.hpp>
#include "DisplayV4.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <functional>
#include <map>
#include <string>

namespace optv4 {
inline const char* Widget="optionsv4";
inline const char* Slot="YumenoKuni-options-v4";
inline const char* Mixer="Assets/Audio/MX_Yumeno.hbaudiomixer.json";
inline constexpr int Rows=14,VisibleRows=8;
inline constexpr float X=63.33333f,Y=79.33333f,Width=1153.34147f,Step=51.333333f,Height=51.333333f;
struct Values {
    int windowMode=0,width=1280,height=720;
    int frameRate=120,textSpeed=8;bool autoRead=false;float autoWait=1.5f;
    bool readOnlySkip=true;float cameraSensitivity=1.f;bool reducedEffects=false;
    int master=10,music=6,sfx=6,ui=10,voice=6,reticleSpeed=3;
    bool movementBob=false,invertY=false,invertX=false,mapRotate=true,vibration=true;int controls=1,voiceLanguage=0;
};
struct Edges {
    bool up=false,down=false,left=false,right=false,confirm=false,cancel=false,click=false;
    bool mouseMoved=false;float mouseX=0,mouseY=0,wheel=0;
};
struct LineState {std::string id;bool readAtEntry=false,readReported=false;float fullSeconds=0;bool fullSeen=false;};
struct State {
    hb::Actor* owner=nullptr;Values values;LineState line;
    std::function<void(const std::string&)> feedback;
    bool initialized=false,open=false,dirty=false,loaded=false,saveFailed=false;
    bool mixerEnabled=false,fresh=false;int row=0,first=0;float saveDelay=0;
    std::array<float,5> appliedDb{{999,999,999,999,999}};
    std::map<std::string,std::string> textCache,textureCache;
    std::map<std::string,bool> visibleCache;
    std::string error;
    std::string previewText;float previewShown=0;int previewLevel=-1;
    Values displayBefore;displayv4::Snapshot windowBefore;
    bool displayPending=false,keepDisplay=true;float displaySeconds=0;
    std::string displayError;
};
inline void Clamp(Values& v){
    v.windowMode=std::clamp(v.windowMode,0,2);if(v.width<320||v.width>7680||v.height<240||v.height>4320){v.width=1280;v.height=720;}
    if(v.frameRate!=30&&v.frameRate!=60&&v.frameRate!=120)v.frameRate=120;
    v.textSpeed=std::clamp(v.textSpeed,1,10);v.reticleSpeed=std::clamp(v.reticleSpeed,1,5);v.controls=std::clamp(v.controls,0,1);v.voiceLanguage=std::clamp(v.voiceLanguage,0,1);
    if(!std::isfinite(v.autoWait))v.autoWait=1.5f;
    v.autoWait=std::clamp(v.autoWait,.5f,5.f);
    if(!std::isfinite(v.cameraSensitivity))v.cameraSensitivity=1.f;
    v.cameraSensitivity=std::clamp(v.cameraSensitivity,.25f,2.f);
    for(auto p:{&v.master,&v.music,&v.sfx,&v.ui,&v.voice})*p=std::clamp(*p,0,10);
}
inline hb::Json Encode(const Values& v){return {{"version",2},{"windowMode",v.windowMode},{"width",v.width},{"height",v.height},{"frameRate",v.frameRate},{"textSpeed",v.textSpeed},{"autoRead",v.autoRead},
    {"autoWait",v.autoWait},{"readOnlySkip",v.readOnlySkip},{"cameraSensitivity",v.cameraSensitivity},
    {"reducedEffects",v.reducedEffects},{"master",v.master},{"music",v.music},{"sfx",v.sfx},{"ui",v.ui},{"voice",v.voice},{"reticleSpeed",v.reticleSpeed},{"movementBobV2",v.movementBob},{"invertY",v.invertY},{"invertX",v.invertX},{"controls",v.controls},{"mapRotate",v.mapRotate},{"vibration",v.vibration},{"voiceLanguage",v.voiceLanguage}};}
inline bool Decode(const hb::Json& j,Values& result){
    if(!j.is_object()||!j.contains("version")||!j["version"].is_number_integer()||(j["version"].get<int>()!=1&&j["version"].get<int>()!=2))return false;
    Values v;
    auto i=[&](const char* k,int& dst){if(j.contains(k)&&j[k].is_number_integer())dst=j[k].get<int>();};
    auto f=[&](const char* k,float& dst){if(j.contains(k)&&j[k].is_number())dst=j[k].get<float>();};
    auto b=[&](const char* k,bool& dst){if(j.contains(k)&&j[k].is_boolean())dst=j[k].get<bool>();};
    i("frameRate",v.frameRate);i("textSpeed",v.textSpeed);b("autoRead",v.autoRead);f("autoWait",v.autoWait);
    i("windowMode",v.windowMode);i("width",v.width);i("height",v.height);
    b("readOnlySkip",v.readOnlySkip);f("cameraSensitivity",v.cameraSensitivity);b("reducedEffects",v.reducedEffects);
    i("master",v.master);i("music",v.music);i("sfx",v.sfx);i("ui",v.ui);
    i("voice",v.voice);i("reticleSpeed",v.reticleSpeed);b("movementBobV2",v.movementBob); /* 주인님 지시 : 걸을 때 위아래 흔들림 없이. 예전 저장 키(켜짐)는 읽지 않는다 */b("invertY",v.invertY);b("invertX",v.invertX);i("controls",v.controls);b("mapRotate",v.mapRotate);b("vibration",v.vibration);i("voiceLanguage",v.voiceLanguage);
    if(j["version"].get<int>()==1)v.textSpeed=j.contains("textSpeed")?std::array<int,3>{{7,8,9}}[std::clamp(v.textSpeed,0,2)]:8;
    Clamp(v);result=v;return true;
}
inline float VolumeDb(int level){return level<=0?-80.f:20.f*std::log10(std::clamp(level,1,10)/10.f);}
inline void ApplyMixer(State& s){
    if(!s.owner||!s.mixerEnabled)return;
    const std::array<int,5> values{{s.values.master,s.values.music,s.values.sfx,s.values.ui,s.values.voice}};
    const std::array<const char*,5> names{{"Master","Music","SFX","UI","Voice"}};
    for(int i=0;i<5;i++){float db=VolumeDb(values[i]);if(i==3)db=std::max(-80.f,db+VolumeDb(s.values.sfx));if(s.appliedDb[i]!=db){
        hb::AudioMixer::SetFloat(s.owner,Mixer,names[i],db);s.appliedDb[i]=db;}}
}
inline void Text(State& s,const std::string& id,const std::string& text){
    if(!s.owner)return;
    auto it=s.textCache.find(id);if(it!=s.textCache.end()&&it->second==text)return;
    hb::UI::SetText(s.owner,Widget,id,text);s.textCache[id]=text;
}
inline void Visible(State& s,const std::string& id,bool value){
    if(!s.owner)return;
    auto it=s.visibleCache.find(id);if(it!=s.visibleCache.end()&&it->second==value)return;
    hb::UI::SetVisible(s.owner,Widget,id,value);s.visibleCache[id]=value;
}
inline void Texture(State& s,const std::string& id,const std::string& texture){
    if(!s.owner)return;
    auto it=s.textureCache.find(id);if(it!=s.textureCache.end()&&it->second==texture)return;
    hb::UI::SetTexture(s.owner,Widget,id,texture);s.textureCache[id]=texture;
}
inline std::string Decimal(float value){
    int n=int(std::round(value*100));std::string r=std::to_string(n/100)+".";
    if(n%100<10)r+="0";
    r+=std::to_string(n%100);return r;
}
inline float TextSpeedFactor(const Values& v){return std::array<float,10>{{.3f,.4f,.5f,.6f,.8f,1,2,4,8,20}}[std::clamp(v.textSpeed,1,10)-1];}
inline float ReticleScale(const Values& v){return std::array<float,5>{{.5f,.75f,1,1.5f,2}}[std::clamp(v.reticleSpeed,1,5)-1];}
inline std::string ExploreHint(const Values& v,bool free){return (free?(v.controls==1?std::string("WASD 이동 · Shift 달리기 · "):std::string("W/S 이동 · A/D 회전 · Shift 달리기 · ")):std::string())+"방향키 / 우클릭 시선 · E / 클릭 조사 · M 조사 목록 · Tab 패드";}
inline int RowValue(const Values& v,int row){switch(row){case 0:return v.music;case 1:return v.sfx;case 2:return v.voice;case 3:return v.textSpeed;case 4:return v.reticleSpeed;case 5:return v.movementBob;case 6:return v.invertY;case 7:return v.invertX;case 8:return v.controls;case 9:return v.mapRotate;case 10:return v.frameRate==30?0:v.frameRate==60?1:2;case 11:return v.windowMode;default:return 0;}}
inline void RestoreSourceDefaults(Values& v){v.windowMode=0;v.width=1280;v.height=720;v.frameRate=120;v.music=v.sfx=v.voice=6;v.textSpeed=8;v.reticleSpeed=3;v.mapRotate=v.vibration=true;v.movementBob=false;v.invertX=v.invertY=false;v.controls=1;}
inline void Render(State& s){
    if(!s.open)return;
    if(s.row<s.first)s.first=s.row;if(s.row>=s.first+VisibleRows)s.first=s.row-VisibleRows+1;s.first=std::clamp(s.first,0,Rows-VisibleRows);
    const std::array<const char*,Rows> labels{{"BGM 음량","효과음 음량","음성 음량","글자 표시 속도","조사 조준점 속도","이동 시점 흔들림","시선의 상하 조작","시선의 좌우 조작","이동 조작","지도 표시","프레임 제한","화면 모드","해상도","기본값 복원"}};
    for(int i=0;i<VisibleRows;i++){
        auto n=std::to_string(i);int row=s.first+i,value=RowValue(s.values,row);std::string style="guage";
        if(row==4){style="slowfast";--value;}else if(row>=5&&row<=9){style=row==6||row==7?"two_invert":row==8?"two_controls":row==9?"two_map":"two";if(row==6||row==7)value=1-value;}else if(row==10||row==11)style="fps";else if(row==12)style="value";else if(row==13)style="one";
        Texture(s,"Row"+n,std::string("Assets/Art/ui/options/v3row/")+style+"_"+(row==s.row?"on":"off")+"_"+std::to_string(value)+".svg");
        for(int f=0;f<3;f++){auto id="FPS"+n+"_"+std::to_string(f);Visible(s,id,row==10||row==11);if(row==10||row==11){Text(s,id,row==10?std::to_string(std::array<int,3>{{30,60,120}}[f]):std::array<const char*,3>{{"창 모드","테두리 없음","전체화면"}}[f]);}if(row==10||row==11)hb::UI::SetColor(s.owner,Widget,id,row==s.row?hb::Color{0,0,0,1}:hb::Color{1,1,1,1});}
        Visible(s,"Value"+n,row==12);if(row==12){auto size=s.values.windowMode==2?displayv4::Native():displayv4::Size{s.values.width,s.values.height};auto label=displayv4::Label(size);Text(s,"Value"+n,s.values.windowMode==2?label:"◀ "+label+" ▶");hb::UI::SetColor(s.owner,Widget,"Value"+n,row==s.row?hb::Color{0,0,0,1}:hb::Color{1,1,1,1});}
        Text(s,"Label"+n,labels[row]);hb::UI::SetColor(s.owner,Widget,"Label"+n,row==s.row?hb::Color{0,0,0,1}:hb::Color{1,1,1,1});hb::UI::SetOpacity(s.owner,Widget,"Label"+n,row==s.row?1.f:.5f);
    }
    const std::array<const char*,Rows> desc{{
        "배경 음악의 음량을 조절해요.","효과음·징글·결정·취소 소리의 음량을 조절해요.",
        "대사 음성의 음량을 조절해요.","글자가 표시되는 속도를 조절해요.","조사할 때 조준점이 움직이는 속도를 조절해요.",
        "걸어갈 때 시점이 위아래로 흔들리는 효과를 켜거나 꺼요.","시선의 상하 조작을 일반 / 반전 중에서 골라요.","시선의 좌우 조작을 일반 / 반전 중에서 골라요.",
        "슈터식: A/D 옆 이동 · 단간론파식: A/D 회전. W/S 이동·방향키 시선·우클릭 둘러보기·Shift 달리기·E 조사는 공통이에요.",
        "회전은 바라보는 방향을 지도 위쪽에 맞추고, 고정은 지도의 방향을 유지해요.","30 · 60 · 120 FPS 중에서 골라요. 설정은 바로 적용되고 저장돼요.","창 모드 · 테두리 없는 창 · 전체화면을 골라요. 변경 후15초 안에 유지 여부를 결정해요.","창 모드와 테두리 없는 창의 실제 해상도를 골라요. 전체화면은 현재 모니터의 기본 해상도를 사용해요.","환경설정을 기본값으로 되돌려요."}};
    std::string description=desc[s.row];if(s.row<=4)description+="\n"+std::to_string(RowValue(s.values,s.row))+" / "+std::to_string(s.row==4?5:10);
    // This project has no recorded actor voices/JP+EN packs. Never fake a
    // preview with an unrelated cue or expose a language reload button.
    if(s.row==2)description+="\n현재 대사 음성 파일이 없어요.";
    if(s.row==3){if(s.previewText!=description||s.previewLevel!=s.values.textSpeed){s.previewText=description;s.previewShown=0;s.previewLevel=s.values.textSpeed;Text(s,"Description","");}}
    else{s.previewText.clear();s.previewLevel=-1;Text(s,"Description",description);}
    if(!s.displayError.empty())Text(s,"Description",s.displayError);
    if(s.saveFailed)Text(s,"Description","설정을 저장하지 못했어요. 다시 시도해 주세요.");
    Visible(s,"DisplayConfirm",s.displayPending);if(s.displayPending){Text(s,"DisplayQuestion","이 화면 설정을 유지할까요?\n"+std::to_string(int(std::ceil(s.displaySeconds)))+"초 후 이전 설정으로 돌아가요.");for(int i=0;i<2;i++){auto id=i?"DisplayRevert":"DisplayKeep";bool selected=(i==0)==s.keepDisplay;Texture(s,id,std::string("Assets/Art/ui/v3/choice_")+(selected?"on":"off")+".svg");hb::UI::SetColor(s.owner,Widget,std::string(id)+"Label",selected?hb::Color{0,0,0,1}:hb::Color{1,1,1,1});}}
    const auto layout=hb::Data::Get("Assets/Data/options_layout.json");auto r=layout["scroll"];
    float height=r[3].get<float>()*VisibleRows/Rows,travel=r[3].get<float>()-height;
    hb::UI::SetPosition(s.owner,Widget,"OptionsScroll",{r[0].get<float>(),r[1].get<float>()+travel*s.first/(Rows-VisibleRows)});hb::UI::SetSize(s.owner,Widget,"OptionsScroll",{r[2].get<float>(),height});
}
inline bool Save(State& s){
    try{hb::Save::Write(Slot,Encode(s.values));s.dirty=false;s.saveFailed=false;s.saveDelay=0;s.error.clear();return true;}
    catch(const std::exception& e){s.saveFailed=true;s.error=e.what();s.saveDelay=0;return false;}
}
inline void ApplyFrameRate(const State& s){auto state=hb::Json::parse(hb::Game::GetStateText());state["runtimeSettings"]["frameRate"]=s.values.frameRate;hb::Game::SetStateText(state.dump());}
inline void Changed(State& s);
inline void FinishDisplay(State& s,bool keep){
    if(!s.displayPending)return;
    if(!keep){if(!displayv4::Restore(s.windowBefore))s.displayError="이전 창 설정을 복원하지 못했어요.";else s.displayError="화면 설정을 이전 값으로 되돌렸어요.";s.values=s.displayBefore;}
    s.displayPending=false;s.displaySeconds=0;Changed(s);
}
inline bool PreviewDisplay(State& s,const Values& previous){
    if(!s.owner){Changed(s);return true;}
    s.windowBefore=displayv4::Capture();s.displayError.clear();
    if(!displayv4::Apply(s.values.windowMode,{s.values.width,s.values.height},s.displayError)){s.values=previous;Render(s);return false;}
    s.displayBefore=previous;s.displayPending=true;s.displaySeconds=15;s.keepDisplay=true;s.saveDelay=0;Render(s);return true;
}
inline void Init(State& s,hb::Actor* owner,std::function<void(const std::string&)> feedback,bool mixerReady=true){
    s.owner=owner;s.feedback=std::move(feedback);s.mixerEnabled=mixerReady;
    try{auto raw=hb::Save::ReadText(Slot);if(!raw.empty())s.loaded=Decode(hb::Json::parse(raw),s.values);}
    catch(const std::exception& e){s.error=e.what();s.loaded=false;}
    Clamp(s.values);s.initialized=true;s.open=false;s.textCache.clear();s.textureCache.clear();s.visibleCache.clear();
    s.appliedDb={{999,999,999,999,999}};
    ApplyMixer(s);ApplyFrameRate(s);
    if(s.owner){auto sizes=displayv4::Resolutions(displayv4::Native());if(std::find(sizes.begin(),sizes.end(),displayv4::Size{s.values.width,s.values.height})==sizes.end()){auto safe=std::find(sizes.begin(),sizes.end(),displayv4::Size{1280,720});auto size=safe==sizes.end()?sizes.front():*safe;s.values.width=size.width;s.values.height=size.height;}if(!displayv4::Apply(s.values.windowMode,{s.values.width,s.values.height},s.displayError)){s.values.windowMode=0;s.values.width=960;s.values.height=540;displayv4::Apply(0,{960,540},s.displayError);}}
}
inline void Open(State& s){if(!s.initialized)return;s.open=true;s.fresh=true;s.row=s.first=0;s.textCache.clear();s.textureCache.clear();s.visibleCache.clear();hb::UI::Show(s.owner,"Assets/UI/OptionsV4.hbwidget.json",Widget);Visible(s,"OptionsRoot",true);Render(s);}
inline void Close(State& s){if(s.displayPending)FinishDisplay(s,false);if(s.dirty)Save(s);s.open=false;hb::UI::Remove(s.owner,Widget);s.textCache.clear();s.textureCache.clear();s.visibleCache.clear();}
inline void Changed(State& s){Clamp(s.values);s.dirty=true;s.saveDelay=.5f;s.line.fullSeconds=0;ApplyMixer(s);ApplyFrameRate(s);Render(s);}
inline bool Adjust(State& s,int row,int direction){
    if(direction==0)return false;
    if(row<=2&&!s.mixerEnabled)return false;
    const auto previous=s.values;const auto old=Encode(s.values);direction=direction>0?1:-1;
    auto cycle=[&](int value,int low,int high){int count=high-low+1;return low+(value-low+direction+count)%count;};
    switch(row){
    case 0:s.values.music=cycle(s.values.music,0,10);break;
    case 1:s.values.sfx=cycle(s.values.sfx,0,10);break;
    case 2:s.values.voice=cycle(s.values.voice,0,10);break;
    case 3:s.values.textSpeed=cycle(s.values.textSpeed,1,10);break;
    case 4:s.values.reticleSpeed=cycle(s.values.reticleSpeed,1,5);break;
    case 5:s.values.movementBob=!s.values.movementBob;break;
    case 6:s.values.invertY=!s.values.invertY;break;
    case 7:s.values.invertX=!s.values.invertX;break;
    case 8:s.values.controls=1-s.values.controls;break;
    case 9:s.values.mapRotate=!s.values.mapRotate;break;
    case 10:s.values.frameRate=std::array<int,3>{{30,60,120}}[cycle(RowValue(s.values,10),0,2)];break;
    case 11:s.values.windowMode=cycle(s.values.windowMode,0,2);break;
    case 12:{if(s.values.windowMode==2)return false;auto sizes=displayv4::Resolutions(displayv4::Native());auto at=std::find(sizes.begin(),sizes.end(),displayv4::Size{s.values.width,s.values.height});int current=at==sizes.end()?0:int(at-sizes.begin());auto size=sizes[cycle(current,0,int(sizes.size())-1)];s.values.width=size.width;s.values.height=size.height;break;}
    case 13:RestoreSourceDefaults(s.values);break;
    default:return false;}
    Clamp(s.values);if(Encode(s.values)==old)return false;
    if(s.values.windowMode!=previous.windowMode||s.values.width!=previous.width||s.values.height!=previous.height)return PreviewDisplay(s,previous);
    Changed(s);return true;
}
inline int HitRow(float x,float y){
    if(!std::isfinite(x)||!std::isfinite(y)||x<X||x>X+Width||y<Y||y>Y+(VisibleRows-1)*Step+Height)return -1;
    int row=int((y-Y)/Step);
    if(row<0||row>=VisibleRows||y>Y+row*Step+Height)return -1;
    return row;
}
inline bool Handle(State& s,const Edges& e){
    if(!s.open)return false;
    auto feedback=[&](const std::string& id){if(s.feedback)s.feedback(id);};
    if(s.displayPending){if(e.cancel){FinishDisplay(s,false);feedback("ui_cancel");return true;}if(e.left||e.right||e.up||e.down){s.keepDisplay=!s.keepDisplay;Render(s);}if(e.mouseMoved&&e.mouseY>=370&&e.mouseY<420){if(e.mouseX>=380&&e.mouseX<620)s.keepDisplay=true;else if(e.mouseX>=660&&e.mouseX<900)s.keepDisplay=false;Render(s);}if(e.confirm||(e.click&&e.mouseY>=370&&e.mouseY<420&&((e.mouseX>=380&&e.mouseX<620)||(e.mouseX>=660&&e.mouseX<900)))){if(e.click)s.keepDisplay=e.mouseX<620;FinishDisplay(s,s.keepDisplay);feedback("ui_confirm");}return true;}
    if(e.cancel){feedback("ui_cancel");Close(s);return true;}
    int old=s.row,oldFirst=s.first;
    if(e.wheel!=0){s.first=std::clamp(s.first+(e.wheel>0?-3:3),0,Rows-VisibleRows);s.row=std::clamp(s.row,s.first,s.first+VisibleRows-1);}
    if(e.up)s.row=(s.row+Rows-1)%Rows;
    if(e.down)s.row=(s.row+1)%Rows;
    int hovered=HitRow(e.mouseX,e.mouseY);
    if((!s.fresh&&e.mouseMoved||e.click)&&hovered>=0)s.row=s.first+hovered;s.fresh=false;
    if(old!=s.row||oldFirst!=s.first){feedback("ui_focus");Render(s);}
    int direction=e.left?-1:e.right?1:0;
    if(e.click&&hovered>=0){
        if(e.mouseX>=686.66667f&&e.mouseX<736)direction=-1;
        else if(e.mouseX>=1159.33333f&&e.mouseX<1208)direction=1;
        if(s.row>=5&&s.row<=9){int current=RowValue(s.values,s.row),left=s.row==6||s.row==7?0:1;if(e.mouseX>=688.66667f&&e.mouseX<942.f)direction=current==left?0:1;else if(e.mouseX>=954&&e.mouseX<1208)direction=current==1-left?0:1;}
        if(s.row==12&&e.mouseX>=688.66667f&&e.mouseX<1208)direction=e.mouseX<948.33333f?-1:1;
        if(s.row==13&&e.mouseX>=688.66667f)direction=1;
    }
    if(e.click&&hovered>=0&&s.row==10&&e.mouseX>=688.66667f&&e.mouseX<1208){const auto oldRate=s.values.frameRate;s.values.frameRate=std::array<int,3>{{30,60,120}}[std::clamp(int((e.mouseX-688.66667f)/173.11111f),0,2)];if(s.values.frameRate!=oldRate){Changed(s);feedback("ui_confirm");}return true;}
    if(e.click&&hovered>=0&&s.row==11&&e.mouseX>=688.66667f&&e.mouseX<1208){const auto previous=s.values;s.values.windowMode=std::clamp(int((e.mouseX-688.66667f)/173.11111f),0,2);if(s.values.windowMode!=previous.windowMode)feedback(PreviewDisplay(s,previous)?"ui_confirm":"ui_reject");return true;}
    if(e.confirm)direction=1;if(s.row==13&&!e.confirm&&!e.click)direction=0;
    if(direction){
        const bool reset=s.row==13;
        feedback(Adjust(s,s.row,direction)?(reset?"ui_confirm":"ui_focus"):"ui_reject");
    }
    return true; // Consume the entire modal input; never pass clicks to a map.
}
inline void Tick(State& s,float delta){
    if(!std::isfinite(delta)||delta<0)return;
    if(s.displayPending){int old=int(std::ceil(s.displaySeconds));s.displaySeconds-=delta;if(s.displaySeconds<=0)FinishDisplay(s,false);else if(int(std::ceil(s.displaySeconds))!=old)Render(s);return;}
    if(s.open&&s.row==3&&!s.previewText.empty()&&!s.saveFailed){int old=int(s.previewShown);s.previewShown+=delta*2.f*TextSpeedFactor(s.values);if(int(s.previewShown)!=old){size_t end=0;int count=0;while(end<s.previewText.size()&&count<int(s.previewShown)){unsigned char c=s.previewText[end];end+=c<128?1:(c&0xe0)==0xc0?2:(c&0xf0)==0xe0?3:4;++count;}Text(s,"Description",s.previewText.substr(0,end));}}
    if(s.dirty&&s.saveDelay>0){s.saveDelay-=delta;if(s.saveDelay<=0){Save(s);Render(s);}}
}
inline float CharactersPerSecond(const State& s){return 10.f*TextSpeedFactor(s.values);}
inline void BeginLine(State& s,const std::string& id,bool wasReadBeforeEntry){s.line={id,wasReadBeforeEntry,false,0};}
inline bool CanSkip(const State& s,bool controlHeld){return controlHeld&&(!s.values.readOnlySkip||s.line.readAtEntry);}
inline bool ReportRead(State& s,bool fullyShown){
    if(!fullyShown||s.line.readReported||s.line.id.empty())return false;
    s.line.readReported=true;return true;
}
inline bool AutoAdvance(State& s,float delta,bool fullyShown,bool blocked=false){
    if(!s.values.autoRead||!fullyShown||blocked){s.line.fullSeconds=0;s.line.fullSeen=false;return false;}
    if(!s.line.fullSeen){s.line.fullSeen=true;s.line.fullSeconds=0;return false;}
    if(std::isfinite(delta)&&delta>0)s.line.fullSeconds+=delta;
    return s.line.fullSeconds>=s.values.autoWait;
}
inline hb::Json Stats(const State& s){auto result=hb::Json{{"open",s.open},{"row",s.row},{"values",Encode(s.values)},
    {"displayPending",s.displayPending},{"displaySeconds",s.displaySeconds},{"displayError",s.displayError},
    {"loaded",s.loaded},{"saveFailed",s.saveFailed},{"dirty",s.dirty},{"mixerEnabled",s.mixerEnabled},
    {"lineReadAtEntry",s.line.readAtEntry}};if(s.open){result["first"]=s.first;result["visibleRows"]=VisibleRows;result["totalRows"]=Rows;}return result;}
} // namespace optv4
