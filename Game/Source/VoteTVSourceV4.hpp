#pragma once
// Presentation only. Does not depend on the unpublished TrialInputMotion state,
// change vote selection, delay optionPicked, or alter timeout/count/outcomes.
namespace votetvui {
using UI=widgetownersv4::UI;
inline const hb::Json& b(){static const auto data=hb::Data::Get("Assets/Data/v4_story/vote_tv_source.json");return data;}
inline const hb::Json& assets(){return b().at("presentation");}
struct State{std::string digits,resultName;bool manualPose=false,verdictVisible=false,monitorSpace=false,returnDialogueOpened=false;std::array<bool,16> dead{};};
inline std::map<const void*,State> states;
template<class T>void reset(T* owner){states[owner]=State{};}
inline float x(float value){return(value-b().at("screen")[0].get<float>())/b().at("scale")[0].get<float>();}
inline float y(float value){return(value-b().at("screen")[1].get<float>())/b().at("scale")[1].get<float>();}
template<class T>void rect(T* owner,const std::string& id,float x,float y,float w,float h){if(states[owner].monitorSpace){x=129+x*(1022.f/1280.f);y=143+y*(575.f/720.f);w*=1022.f/1280.f;h*=575.f/720.f;}const auto& s=b().at("screen");const auto& a=b().at("scale");UI::SetPosition(owner,"vote",id,{s[0].get<float>()+x*a[0].get<float>(),s[1].get<float>()+y*a[1].get<float>()});UI::SetSize(owner,"vote",id,{w*a[0].get<float>(),h*a[1].get<float>()});}
template<class T>void rect(T* owner,const std::string& id,const hb::Json& r){rect(owner,id,r[0].get<float>(),r[1].get<float>(),r[2].get<float>(),r[3].get<float>());}
inline bool commit(float px,float py){const auto&r=b().at("commit");float u=x(px),v=y(py);return u>=r[0].get<float>()&&u<=r[0].get<float>()+r[2].get<float>()&&v>=r[1].get<float>()&&v<=r[1].get<float>()+r[3].get<float>();}
inline std::string portrait(const std::string& who,const std::string& fallback){const auto&p=b().at("portraits");return p.contains(who)?p.at(who).get<std::string>():fallback;}
inline std::string digits(float seconds){int ms=std::max(0,int(seconds*1000)),min=std::min(99,ms/60000),sec=(ms/1000)%60,milli=ms%1000;std::string s;for(int v:{min/10,min%10,10,sec/10,sec%10,10,milli/100,(milli/10)%10,milli%10})s+=char('0'+v);return s;}
template<class T>void pose(T* owner,const std::string& track,int index,bool manual=true,float opacity=1.f){if(manual)states[owner].manualPose=true;const auto& meta=assets().at("tracks").at(track);const hb::Json empty=hb::Json::array();const hb::Json* ptr=&empty;if(index>=0&&index<meta.at("frames").get<int>()){static std::map<std::string,hb::Json> chunks;auto file=meta.at("chunks")[index/24].get<std::string>();if(!chunks.count(file))chunks[file]=hb::Data::Get(file);ptr=&chunks.at(file).at("frames")[index%24];}const auto& rows=*ptr;for(int i=0;i<25;i++){auto id="VoteAnimation"+std::to_string(i);UI::SetVisible(owner,"vote",id,i<int(rows.size()));if(i>=int(rows.size()))continue;const auto&r=rows[i];UI::SetTexture(owner,"vote",id,r[0].get<std::string>());rect(owner,id,r[1].get<float>(),r[2].get<float>(),r[3].get<float>(),r[4].get<float>());UI::SetRotation(owner,"vote",id,r[5].get<float>());UI::SetOpacity(owner,"vote",id,r[6].get<float>()*opacity);}}
template<class T>void clock(T* owner,float remaining,float duration){auto& state=states[owner];bool on=duration>0;for(auto id:{"VoteTimeArt","VoteTimerObi"})UI::SetVisible(owner,"vote",id,on);const auto value=digits(remaining);const auto& glyphs=assets().at("clocks").at("vote").at("digits");for(int i=0;i<9;i++){auto id="VoteDigit"+std::to_string(i);UI::SetVisible(owner,"vote",id,on);if(on&&(state.digits.size()!=9||state.digits[i]!=value[i]))UI::SetTexture(owner,"vote",id,glyphs.at(std::to_string(value[i]-'0')).get<std::string>());}state.digits=value;if(!state.manualPose){int frame=int(std::max(0.f,duration-remaining)*60);pose(owner,"intro",frame<98?frame:-1,false);}}
template<class T>void shutters(T* owner,int at,int count,int selected){
 const auto& motion=b().at("shutters");
 const int frame=std::clamp(at,0,motion.at("frames").get<int>()-1);
 static std::map<std::string,hb::Json> chunks;
 const auto file=motion.at("tracks")[frame/12].get<std::string>();
 if(!chunks.count(file))chunks[file]=hb::Data::Get(file);
 const auto& row=chunks.at(file)[frame%12];
 for(int i=0;i<16;i++){
  const auto id=std::to_string(i);
  const auto& card=row.at("cards")[i][0];const auto& cover=row.at("cards")[i][1];
  const bool faceVisible=i<count&&card[4].get<float>()>0;
  UI::SetVisible(owner,"vote","VoteD"+id,faceVisible&&states[owner].dead[i]);
  UI::SetVisible(owner,"vote","VoteP"+id,i<count&&i==selected&&frame<4);
  UI::SetVisible(owner,"vote","VoteF"+id,faceVisible);
  UI::SetVisible(owner,"vote","VoteShutter"+id,cover[4].get<float>()>0);
  rect(owner,"VoteF"+id,card);rect(owner,"VoteD"+id,card);rect(owner,"VoteShutter"+id,cover);
  UI::SetOpacity(owner,"vote","VoteShutter"+id,cover[4]);
 }
 UI::SetVisible(owner,"vote","VoteWait",row["wait"].get<float>()>0);
 UI::SetOpacity(owner,"vote","VoteWait",row["wait"]);
}
template<class T>void confetti(T* owner,float elapsed){
 const std::string award="VoteAnimation24";
 UI::SetVisible(owner,"vote",award,true);
 UI::SetTexture(owner,"vote",award,"Assets/Art/ui/vote_verdict/tally_award.svg");
 rect(owner,award,696.f,22.f,544.f,548.f);
 UI::SetRotation(owner,"vote",award,0.f);
 UI::SetOpacity(owner,"vote",award,1.f);
 const std::array<const char*,3> colors{"or","pk","ye"};
 for(int i=0;i<24;i++){
  const auto id="VoteAnimation"+std::to_string(i);
  const float age=elapsed-.028f*((i*11)%24);
  const float speed=216.f+float((i*29)%76);
  const float y=-32.f+age*speed+10.f*age*age;
  const bool visible=age>=0.f&&y>=0.f&&y<=697.f;
  UI::SetVisible(owner,"vote",id,visible);
  if(!visible)continue;
  const float x=672.f+float((i*137)%515)+20.f*std::sin(age*3.2f+i);
  const float size=14.f+float((i*7)%13);
  rect(owner,id,x,y,size,size*(.28f+.72f*std::abs(std::cos(age*6.f+i))));
  UI::SetTexture(owner,"vote",id,std::string("Assets/Art/ui/vote_tv_source/result_t_tohyo_chara_kamihubuki_")+colors[i%3]+".png");
  UI::SetRotation(owner,"vote",id,40.f*std::sin(age*4.f+i));
  UI::SetOpacity(owner,"vote",id,1.f);
 }
}
inline constexpr float monitorIntro=3.3f,monitorOutro=1.65f;
template<class T>void monitor(T* owner,float offset,bool black,bool slate,float slateAlpha=1){
 UI::SetVisible(owner,"vote","VoteFullMatte",false);
 for(auto id:{"VoteTVBezel","VoteMonitorBlack","VoteMonitorSlate"}){
  const bool bezel=std::string_view(id)=="VoteTVBezel";
  UI::SetPosition(owner,"vote",id,{bezel?0.f:129.f,(bezel?0.f:143.f)+offset});
  UI::SetVisible(owner,"vote",id,bezel||(std::string_view(id)=="VoteMonitorBlack"?black:slate));
 }
 UI::SetOpacity(owner,"vote","VoteMonitorSlate",slateAlpha);
}
template<class T>void monitorClear(T* owner,bool matte=true){
 for(auto id:{"VoteTVBezel","VoteMonitorBlack","VoteMonitorSlate"})UI::SetVisible(owner,"vote",id,false);
 UI::SetVisible(owner,"vote","VoteFullMatte",matte);states[owner].monitorSpace=false;
}
inline constexpr float tallySpan=3.6f;
inline constexpr float verdictHold=4.f, wheelReveal=2.5f, wheelWide=4.5f;
inline constexpr float coinStart=verdictHold+wheelWide+3.f, closeStart=coinStart+2.35f, verdictEnd=closeStart+1.65f;
template<class T>void verdict(T* owner,float time,const std::vector<std::string>& people,const std::string& winner,const std::string& label){
 const auto key=[](const std::string& name){return "VoteVerdict"+name;};
 const auto visible=[&](const std::string& name,bool on){UI::SetVisible(owner,"vote",key(name),on);};
 const auto place=[&](const std::string& name,float x,float y,float w,float h,float rotation=0.f){
  rect(owner,key(name),x,y,w,h);UI::SetRotation(owner,"vote",key(name),rotation);
 };
 const float phase=time-verdictHold;
 if(phase<0)return;
 states[owner].verdictVisible=true;
 if(time>=closeStart){
  for(const auto* name:{"Room","SideL","SideR","Dial","Focus","Seal","Name"})visible(name,false);
  for(int i=0;i<16;i++)visible("Dot"+std::to_string(i),false);
  for(int i=0;i<34;i++)visible("Coin"+std::to_string(i),false);
  visible("Dark",true);UI::SetOpacity(owner,"vote",key("Dark"),1.f);
  const auto& close=assets().at("tracks").at("close");
  pose(owner,"close",std::min(close.at("frames").get<int>()-2,int((time-closeStart)*48)));
  return;
 }
 const int count=std::min(16,int(people.size()));
 const auto selected=std::find(people.begin(),people.begin()+count,winner);
 const int winning=selected==people.begin()+count?0:int(selected-people.begin());
 const bool revealed=phase>=wheelReveal;
 const bool angled=phase>=wheelWide;
 const auto ease=[](float t){t=std::clamp(t,0.f,1.f);return t*t*(3-2*t);};
 // The reveal holds on the face, then cuts to a wider, elevated cabinet angle.
 const float zoom=angled?.91f:1.03f+.29f*ease(phase/1.05f);
 const float left=640-305*zoom,top=angled?40.f:438.f-373.f*zoom;
 const auto machine=[&](const std::string& name,float x,float y,float w,float h,float rotation=0.f){
  if(angled){y=61.f+y*.82f;h*=.82f;}
  place(name,left+x*zoom,top+y*zoom,w*zoom,h*zoom,rotation);
 };
 visible("Room",true);
 for(const auto& [name,x]:std::array<std::pair<const char*,float>,2>{{{"SideL",85.f},{"SideR",870.f}}}){
  visible(name,angled);place(name,x,281,322,370);UI::SetTexture(owner,"vote",key(name),"Assets/Art/ui/vote_verdict/cabinet_angle.svg");UI::SetOpacity(owner,"vote",key(name),.36f);
 }
 visible("Dial",true);place("Dial",left,top,610*zoom,700*zoom);
 UI::SetTexture(owner,"vote",key("Dial"),angled?"Assets/Art/ui/vote_verdict/cabinet_angle.svg":"Assets/Art/ui/vote_verdict/cabinet.svg");
 const int active=revealed?winning:(winning+1+int(phase*phase*14))%16;
 for(int i=0;i<16;i++){
  const float angle=float(i)*.39269908f,dx=std::sin(angle),dy=-std::cos(angle);
  const float x=305+183*dx,y=373+183*dy;
  const auto dot="Dot"+std::to_string(i);
  visible(dot,i<count);
  if(i<count){machine(dot,x-28,y-28,56,56);UI::SetTexture(owner,"vote",key(dot),"Assets/Art/ui/vote_verdict/dot_"+people[i]+".png");}
  if(i<count)UI::SetOpacity(owner,"vote",key(dot),revealed&&i!=winning?.31f:1.f);
  if(i==active)machine("Focus",x-46,y-38,92,75,float(i)*22.5f);
 }
 visible("Focus",true);UI::SetOpacity(owner,"vote",key("Focus"),revealed?.62f+.38f*std::sin(phase*26.f):1.f);visible("Seal",revealed);visible("Name",revealed);
 if(revealed){
  const float scale=.72f+.28f*ease((phase-wheelReveal)/.18f);
  const float radius=95*scale;
  machine("Seal",305-radius,373-radius,2*radius,2*radius);
  if(winning<count)UI::SetTexture(owner,"vote",key("Seal"),"Assets/Art/ui/vote_verdict/led_"+people[winning]+".png");
  machine("Name",147,116,316,34);
  UI::SetFontSize(owner,"vote",key("Name"),(label.size()>22?22.f:29.f)*zoom);
  UI::SetText(owner,"vote",key("Name"),label);
 }
 if(time<coinStart)return;
 const float elapsed=time-coinStart;
 for(int i=0;i<34;i++){
  const auto name="Coin"+std::to_string(i);
  const float launch=i<3?.14f*i:.43f+.034f*(i-3);
  const float age=elapsed-launch;
  visible(name,age>=0.f);
  if(age<0.f)continue;
  const float flight=std::clamp(age/(i<3?1.45f:.87f),0.f,1.f);
  const float spread=ease(flight);
  const float jitter=float((i*31+11)%67)-33.f;
  const int slot=(i*13)%34;
  const float endX=40.f+(slot%7)*200.f+jitter;
  const float endY=650.f-(slot/7)*156.f+jitter;
  const float size=24.f+(250.f+float((i*47)%76))*spread;
  const float originX=640.f+float(i%5-2)*63.f;
  const float x=originX+(endX-originX)*spread;
  const float y=590.f+(endY-590.f)*spread-150.f*std::sin(flight*3.14159265f);
  place(name,x-size*.5f,y-size*.5f,size,size,float((i*47)%360)+270.f*flight);
 }
 const float fade=ease((elapsed-1.91f)/.4f);
 visible("Dark",fade>0.f);
 UI::SetOpacity(owner,"vote",key("Dark"),fade);
}

template<class T>void clearVerdict(T* owner){
 auto it=states.find(owner);
 if(it==states.end()||!it->second.verdictVisible)return;
 for(const auto* name:{"Room","SideL","SideR","Dial","Focus","Seal","Name","Dark"})
  UI::SetVisible(owner,"vote",std::string("VoteVerdict")+name,false);
 for(int i=0;i<16;i++)UI::SetVisible(owner,"vote","VoteVerdictDot"+std::to_string(i),false);
 for(int i=0;i<34;i++)UI::SetVisible(owner,"vote","VoteVerdictCoin"+std::to_string(i),false);
 pose(owner,"close",-1);it->second.verdictVisible=false;
}

}
