// Trial t_choice only. Existing ADV choice font measurements are shared, not its layout.
namespace flowchoice {inline std::pair<std::string,int> window(const std::string&,float,float);}
namespace trialanswer {
inline const hb::Json& layout(){static const auto value=hb::Data::Get("Assets/Data/v4_story/trial_answer_layout.json");return value;}
inline const hb::Json& track(int count,int selected){static std::map<std::string,hb::Json> values;auto key=std::to_string(count)+"_"+std::to_string(selected);if(!values.count(key))values[key]=hb::Data::Get(layout().at("tracks").at(key).get<std::string>());return values.at(key);}
inline bool restore(const hb::Json& value,std::string& context,std::vector<bool>& confirmed){
 if(!value.is_object())return false;auto name=value.value("context",std::string());auto rows=value.value("confirmed",std::vector<bool>(4,false));if(name.size()>256||rows.size()!=4)return false;context=name;confirmed=rows;return true;
}
}
void Yumeno::trialAnswerStart(const std::string& question){
 trialAnswerOn=true;trialAnswerHover=-1;trialAnswerPending=-1;trialAnswerTicks=trialAnswerMarquee=0;trialAnswerStamp.clear();
 auto context=v4.active?v4.node:trialKey+":"+std::to_string(stageAt);if(context!=trialAnswerContext){trialAnswerContext=context;trialAnswerConfirmed.assign(4,false);}
 for(auto id:{"TaQuestionPlate","TaQuestion","TaFrame","TaRows"})svis(id,true);stext("TaQuestion",question);svis("TaTitle",false);
 trialinputmotion::show(this,"choice",trialInputClock);
 for(int i=0;i<8;i++){svis("OptP"+std::to_string(i),false);svis("OptT"+std::to_string(i),false);}
 const auto& wait=trialanswer::layout().at("wait").at(std::to_string(opts.size()));
 for(int i=0;i<int(opts.size());i++){const auto& r=wait.at("rows")[i].at("text");optRects[i]={365.333333f,r[1].get<float>()-9.333334f,914.666667f,43.333333f};}
 for(int i=0;i<int(opts.size());i++)UI::SetFont(this,trialui::ID,"OptT"+std::to_string(i),"Assets/Fonts/pretendard/Pretendard-Regular.otf");
 UI::SetVisible(this,UI_ID,"Aim",false);
 if(trialinputmotion::bank().contains("choiceOpening")){
  stageTime=-float(trialinputmotion::bank().at("choiceOpening").at("frames").size())/60;
  svis("TaRows",false);trialinputmotion::choiceOpening(this,0,false);
 }else trialAnswerDraw(0);
}
void Yumeno::trialAnswerDraw(float delta){
 if(!trialAnswerOn||stageTime<0)return;if(trialAnswerHover!=optHover){trialAnswerHover=optHover;trialAnswerTicks=trialAnswerMarquee=0;}
 trialAnswerTicks+=delta*60;trialAnswerMarquee+=delta;
 const auto& track=trialanswer::track(int(opts.size()),optHover);const auto& frames=track.at(trialAnswerPending>=0?"confirm":"select");int frame=std::min(int(trialAnswerTicks),int(frames.size())-1);const auto& current=frames[frame];
 auto caption=flowchoice::window(opts[optHover],trialAnswerMarquee,600);std::string stamp=std::to_string(optHover)+":"+std::to_string(trialAnswerPending)+":"+std::to_string(frame)+":"+std::to_string(caption.second);for(bool v:trialAnswerConfirmed)stamp+=v?'1':'0';if(stamp==trialAnswerStamp)return;trialAnswerStamp=stamp;
 UI::SetTexture(this,trialui::ID,"TaRows",current.at("asset").get<std::string>());
 for(int i=0;i<4;i++){
  auto n=std::to_string(i);bool on=i<int(opts.size())&&current.at("rows")[i].at("showText").get<bool>();svis("OptT"+n,on);if(i>=int(opts.size())){svis("TaCheck"+n,false);svis("TaNumber"+n,false);continue;}const auto& row=current.at("rows")[i];
  if(on){const auto& r=row.at("text");UI::SetPosition(this,trialui::ID,"OptT"+n,{r[0],r[1]});UI::SetSize(this,trialui::ID,"OptT"+n,{r[2],r[3]});UI::SetFontSize(this,trialui::ID,"OptT"+n,26.666667f);UI::SetColor(this,trialui::ID,"OptT"+n,Color{1,1,1,1});stext("OptT"+n,i==optHover?caption.first:flowchoice::window(opts[i],0,600).first);}
  bool check=trialAnswerConfirmed[i]&&row.at("showCheck").get<bool>();svis("TaCheck"+n,check);if(check){const auto& r=row.at("check");UI::SetPosition(this,trialui::ID,"TaCheck"+n,{r[0],r[1]});UI::SetSize(this,trialui::ID,"TaCheck"+n,{r[2],r[3]});}
  bool number=!check&&row.at("showNumber").get<bool>();svis("TaNumber"+n,number);if(number){const auto& r=row.at("number");UI::SetPosition(this,trialui::ID,"TaNumber"+n,{r[0],r[1]});UI::SetSize(this,trialui::ID,"TaNumber"+n,{r[2],r[3]});}
 }
}
bool Yumeno::trialAnswerInput(float delta,bool click){
 if(!trialAnswerOn||stageKind!="choice")return false;
 if(stageTime<0){
  stageTime=std::min(0.f,stageTime+delta);
  const float elapsed=stageTime+float(trialinputmotion::bank().at("choiceOpening").at("frames").size())/60;
  trialinputmotion::choiceOpening(this,elapsed,stageTime>=0);
  if(stageTime>=0){svis("TaRows",true);trialAnswerDraw(0);}
  return true;
 }
 if(trialAnswerPending>=0){trialAnswerDraw(delta);const auto& frames=trialanswer::track(int(opts.size()),optHover).at("confirm");if(trialAnswerTicks>=frames.size()){int selected=trialAnswerPending;trialAnswerPending=-1;trialAnswerTicks=6;trialAnswerStamp.clear();optionPicked(selected);}return true;}
 stageTime+=delta;const float duration=stage.value("duration",20.f)*trialTimeFactor();trialinputmotion::clock(this,"choice",std::max(0.f,duration-stageTime),duration,trialInputClock);
 if(duration>0&&stageTime>=duration){hurt();restartStage=true;return true;}
 trialAnswerDraw(delta);if(trialAnswerTicks<6)return true;
 int before=optHover;bool moved=std::abs(aimX-optionMouseX)>.5f||std::abs(aimY-optionMouseY)>.5f;optionMouseX=aimX;optionMouseY=aimY;
 if(pressed("w")||pressed("ArrowUp"))optHover=(optHover+int(opts.size())-1)%int(opts.size());if(pressed("s")||pressed("ArrowDown"))optHover=(optHover+1)%int(opts.size());int hit=optionAt(aimX,aimY);if((moved||click)&&hit>=0)optHover=hit;
 if(before!=optHover){pv4::Action(presentationV4,"ui_focus");trialAnswerDraw(0);}
 if((click&&hit>=0)||pressed("Enter")){trialAnswerConfirmed[optHover]=true;trialAnswerPending=optHover;trialAnswerTicks=0;trialAnswerStamp.clear();pv4::Action(presentationV4,"ui_confirm");trialAnswerDraw(0);}return true;
}
std::string Yumeno::TrialAnswerStats()const{return Json{{"visible",trialAnswerOn},{"context",trialAnswerContext},{"confirmed",trialAnswerConfirmed},{"hover",optHover},{"pending",trialAnswerPending},{"ticks",trialAnswerTicks},{"labels",opts}}.dump();}
