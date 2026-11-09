#pragma once
namespace trialinputmotion {
inline hb::Vec2 inset(){
 int w=gputrialhudv4::width>0?gputrialhudv4::width:1280,h=gputrialhudv4::height>0?gputrialhudv4::height:720;
#ifdef _WIN32
 static HWND own=nullptr;if(!own||!IsWindow(own))own=displayv4::Window();RECT r{};if(own&&GetClientRect(own,&r)&&r.right>0&&r.bottom>0){w=r.right;h=r.bottom;}
#endif
 float fit=std::min(w/1280.f,h/720.f);return {(w/fit-1280)*.5f,(h/fit-720)*.5f};
}
inline std::map<const void*,hb::Vec2> statusOffsets;
template<class T>hb::Vec2 stageFrame(T* owner,bool active){auto p=active?inset():hb::Vec2{0,0};widgetownersv4::UI::SetPosition(owner,"stage","InputSourceFrame",p);auto previous=statusOffsets.find(owner);if(previous==statusOffsets.end()||previous->second.x!=p.x||previous->second.y!=p.y){statusOffsets[owner]=p;auto move=[&](const char* id,float x,float y){widgetownersv4::UI::SetPosition(owner,"main",id,{x+p.x,y+p.y});};move("StatusPanel",936,18);move("StatusLabel",972,26);for(int i=0;i<10;i++)widgetownersv4::UI::SetPosition(owner,"main","Star"+std::to_string(i),{972+i*22.5f+p.x,94+p.y});}if(widgetownersv4::UI::Mounted("trialvitalsv4"))widgetownersv4::UI::SetPosition(owner,"trialvitalsv4","InputSourceFrame",p);return p;}
inline const hb::Json& bank(){static const auto b=hb::Data::Get("Assets/Data/v4_story/trial_input_motion.json");return b;}
inline std::string widget(const std::string& kind){return "trialinputmotion_"+kind;}
struct QuestionMotion{bool open=false;float frame=0,width=0;};
inline std::map<const void*,QuestionMotion> questionMotions;
template<class T>void questionPose(T* owner,bool spot,bool open,float delta){
 auto& state=questionMotions[owner];
 const auto& bankData=bank();if(!bankData.contains("questionMotion"))return;
 const auto& frames=bankData.at("questionMotion").at(open?"open":"close");
 if(state.open!=open){
  state.open=open;state.frame=0;
  float distance=std::abs(state.width-frames[0].get<float>());
  for(int i=1;i<int(frames.size());++i){
   const float next=std::abs(state.width-frames[i].get<float>());
   if(next<distance){state.frame=float(i);distance=next;}
  }
 }
 const int frame=std::min(int(state.frame),int(frames.size()));
 const float width=!open&&frame==int(frames.size())?0:frames[std::min(frame,int(frames.size())-1)].get<float>();
 state.width=width;
 state.frame=std::min(state.frame+delta*60,float(frames.size()));
 using UI=widgetownersv4::UI;
 const char* instance=spot?"stage":"trialpickerv4";
 const char* plate=spot?"QBand":"PkQuestionBack";
 const char* label=spot?"QText":"PkQuestion";
 UI::SetVisible(owner,instance,plate,width>1);
 UI::SetVisible(owner,instance,label,open&&frame==int(frames.size()));
 UI::SetPosition(owner,instance,plate,{0,spot?616.f:606.f});UI::SetSize(owner,instance,plate,{width,spot?30.f:40.f});
 UI::SetPosition(owner,instance,label,{26,spot?617.f:610.f});UI::SetSize(owner,instance,label,{750,30});
 if(spot)UI::SetFontSize(owner,instance,label,20);
}
template<class T>void resetQuestion(T* owner){questionMotions[owner]={false,1000};}
template<class T>bool spotExit(T* owner,float ticks,const std::array<float,4>& image){
 const auto& frames=bank().at("spotExit");
 const int frame=std::min(int(ticks),int(frames.size())-1);
 const auto& row=frames[frame];
 const float w=image[2]*row[0].get<float>(),h=image[3]*row[1].get<float>();
 using UI=widgetownersv4::UI;
 UI::SetPosition(owner,"stage","SpotImg",{image[0]+(image[2]-w)*.5f,image[1]+(image[3]-h)*.5f});
 UI::SetSize(owner,"stage","SpotImg",{w,h});
 UI::SetOpacity(owner,"stage","SpotImg",row[2]);
 for(auto id:{"SpotTitle","SpotFrame","SpotModeFrame","CrossH","CrossV"})
  UI::SetOpacity(owner,"stage",id,row[2]);
 for(auto id:{"DecisionGuide","DecisionLabel","DecisionQuestion","PromptIcon0","PromptIcon1"})
  UI::SetOpacity(owner,widget("spot"),id,row[2]);
 return ticks>=frames.size();
}
inline bool usesSourceStatus(const std::string& kind){return kind=="person"||kind=="spot"||kind=="bullet"||kind=="choice";}
template<class T>void sourceStatus(T* owner,bool enabled,int maximum,int hp,float focus,float focusMax){
 using UI=widgetownersv4::UI;
 const std::string ui="trialvitalsv4";
 for(auto id:{"SelectorStatus","SelectorHearts","SelectorStars"})UI::SetVisible(owner,ui,id,enabled);
 if(!enabled)return;
 for(auto id:{"StatusPanel","StatusLabel"})UI::SetVisible(owner,"main",id,false);
 for(int i=0;i<10;i++)UI::SetVisible(owner,"main","Star"+std::to_string(i),false);
 for(int i=0;i<20;i++)UI::SetVisible(owner,ui,"Heart"+std::to_string(i),false);
 static const auto layout=hb::Data::Get("Assets/Data/nonstop_source_hud.json");
 const int count=maximum<=5?5:maximum<=7?7:10;
 auto meter=[&](const char* id,const char* group,const char* prefix,float value){
  const auto& r=layout.at(group).at(std::to_string(count));
  const int step=std::clamp(int(std::ceil(value*count*2)),0,count*2);
  UI::SetPosition(owner,ui,id,{r[0],r[1]});UI::SetSize(owner,ui,id,{r[2],r[3]});
  UI::SetTexture(owner,ui,id,"Assets/Art/ui/nonstop_source/"+std::string(prefix)+std::to_string(count)+"_"+std::to_string(step)+".png");
 };
 meter("SelectorHearts","hearts","heart",float(hp)/std::max(1,maximum*2000));
 meter("SelectorStars","stars","star",focus/std::max(1.f,focusMax));
}
inline int voteAt(float x,float y){
 for(int i=0;i<16;i++){const auto& rect=bank().at("voteCards")[i];float u=(x-rect[0].get<float>())/rect[2].get<float>(),v=(y-rect[1].get<float>())/rect[3].get<float>();const auto& p=bank().at("cardPolygons")[i];bool inside=false;for(int a=0,b=3;a<4;b=a++){float ax=p[a][0],ay=p[a][1],bx=p[b][0],by=p[b][1];if((ay>v)!=(by>v)&&u<(bx-ax)*(v-ay)/(by-ay)+ax)inside=!inside;}if(inside)return i;}return -1;
}
template<class T>void votePose(T* owner,const std::string& track,int index){
 const auto id=widget("vote");const auto& meta=bank().at("tracks").at(track);const hb::Json empty=hb::Json::array();const hb::Json* rowsPtr=&empty;
 if(index>=0&&index<meta.at("frames").get<int>()){static std::map<std::string,hb::Json> chunks;const auto file=meta.at("chunks")[index/24].get<std::string>();if(!chunks.count(file))chunks[file]=hb::Data::Get(file);rowsPtr=&chunks.at(file).at("frames")[index%24];}const auto& rows=*rowsPtr;
 for(int i=0;i<25;i++){const auto n="Leaf"+std::to_string(i);widgetownersv4::UI::SetVisible(owner,id,n,i<int(rows.size()));if(i>=int(rows.size()))continue;const auto& r=rows[i];widgetownersv4::UI::SetTexture(owner,id,n,r[0].template get<std::string>());widgetownersv4::UI::SetPosition(owner,id,n,{r[1],r[2]});widgetownersv4::UI::SetSize(owner,id,n,{r[3],r[4]});widgetownersv4::UI::SetRotation(owner,id,n,r[5]);widgetownersv4::UI::SetOpacity(owner,id,n,r[6]);}
}
struct ClockState{std::string digits;int glass=-1;};
inline std::string digits(float seconds){
 int ms=std::max(0,int(std::ceil(seconds*1000)));int min=std::min(99,ms/60000),sec=(ms/1000)%60,milli=ms%1000;
 std::string s;for(int v:{min/10,min%10,10,sec/10,sec%10,10,milli/100,(milli/10)%10,milli%10})s+=char('0'+v);return s;
}
template<class T>void clear(T* owner){statusOffsets.erase(owner);questionMotions.erase(owner);for(auto id:{"QBand","QText"})widgetownersv4::UI::SetVisible(owner,"stage",id,false);for(auto kind:{"choice","bullet","vote","spot"})widgetownersv4::UI::Remove(owner,widget(kind));}
template<class T>void visibility(T* owner,bool visible){for(auto kind:{"choice","bullet","vote","spot"}){auto id=widget(kind);if(widgetownersv4::UI::Mounted(id))widgetownersv4::UI::SetVisible(owner,id,"root",visible);}}
template<class T>void spotPose(T* owner,int frame,float x,float y){const auto& frames=bank().at("spotLock");const auto& row=frames[std::clamp(frame,0,int(frames.size())-1)];const auto& r=row.at("rect");const auto id=widget("spot");widgetownersv4::UI::SetVisible(owner,id,"Lock",true);widgetownersv4::UI::SetTexture(owner,id,"Lock",row.at("asset").template get<std::string>());widgetownersv4::UI::SetPosition(owner,id,"Lock",{r[0].template get<float>()-640+x,r[1].template get<float>()-360+y});widgetownersv4::UI::SetSize(owner,id,"Lock",{r[2],r[3]});}
template<class T>bool spotOpening(T* owner,float elapsed){
 const auto& data=bank();if(!data.contains("spotOpening"))return false;
 const auto& frames=data.at("spotOpening");
 const auto& row=frames[std::clamp(int(elapsed*60),0,int(frames.size())-1)];
 const float frame=row[0],photo=row[1];
 auto alpha=[&](const char* node,float value){widgetownersv4::UI::SetOpacity(owner,"stage",node,value);};
 alpha("SpotFrame",frame);alpha("SpotModeFrame",frame);alpha("SpotTitle",frame);
 for(auto id:{"SpotImg","Mark0","CrossH","CrossV"})alpha(id,photo);
 for(auto id:{"DecisionGuide","DecisionLabel","DecisionQuestion","PromptIcon0","PromptIcon1"})
  widgetownersv4::UI::SetOpacity(owner,widget("spot"),id,photo);
 return photo<1;
}
template<class T>void choiceOpening(T* owner,float elapsed,bool finished){
 const auto& motion=bank().at("choiceOpening");
 const auto& frames=motion.at("frames");
 const auto& r=frames[std::clamp(int(elapsed*60),0,int(frames.size())-1)];
 using UI=widgetownersv4::UI;
 UI::SetTexture(owner,"stage","TaFrame",motion.at(finished?"rest":"texture").template get<std::string>());
 if(finished){UI::SetPosition(owner,"stage","TaFrame",{0,0});UI::SetSize(owner,"stage","TaFrame",{1280,720});}
 else {UI::SetPosition(owner,"stage","TaFrame",{r[0],r[1]});UI::SetSize(owner,"stage","TaFrame",{r[2],r[3]});}
 for(auto id:{"DecisionGuide","DecisionLabel","PromptIcon0"})UI::SetVisible(owner,widget("choice"),id,finished);
}
template<class T>void show(T* owner,const std::string& kind,ClockState& cache){
 stageFrame(owner,true);
 const auto id=widget(kind);if(!widgetownersv4::UI::Mounted(id))widgetownersv4::UI::Show(owner,bank().at("widgets").at(kind).template get<std::string>(),id);cache={};
}
template<class T>void clock(T* owner,const std::string& kind,float remaining,float duration,ClockState& cache){
 const auto id=widget(kind);bool on=duration>0;widgetownersv4::UI::SetVisible(owner,id,"ClockBase",on&&kind!="choice");
 const std::string value=digits(remaining);const auto& d=bank().at("clocks").at(kind).at("digits");
 for(int i=0;i<9;i++){const auto n="Clock"+std::to_string(i);widgetownersv4::UI::SetVisible(owner,id,n,on);if(on&&(cache.digits.size()!=9||cache.digits[i]!=value[i]))widgetownersv4::UI::SetTexture(owner,id,n,d.at(std::to_string(value[i]-'0')).template get<std::string>());}
 cache.digits=value;
 if(kind=="choice"){
  widgetownersv4::UI::SetVisible(owner,id,"Glass",on);int frame=duration>0?std::clamp(int((1-remaining/duration)*60),0,60):0;
  if(on&&frame!=cache.glass){const auto& g=bank().at("glass")[frame];const auto& r=g.at("rect");widgetownersv4::UI::SetTexture(owner,id,"Glass",g.at("asset").template get<std::string>());widgetownersv4::UI::SetPosition(owner,id,"Glass",{r[0],r[1]});widgetownersv4::UI::SetSize(owner,id,"Glass",{r[2],r[3]});cache.glass=frame;}
 }
}
}
