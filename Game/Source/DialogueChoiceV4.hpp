// adv_choices source carriers/focus tracks. The original three rasters are
// recovered bitmap strips/check now retain the source selection/confirmation frames.
namespace flowchoice {
inline const hb::Json& layout(){static const hb::Json value=hb::Data::Get("Assets/Data/v4_story/choice_layout.json");return value;}
inline float width(const std::string& glyph){static const std::map<std::string,float> values=[](){std::map<std::string,float> out;for(const auto& bucket:layout()["advances"])for(const auto& [key,value]:bucket.items())out[key]=value.get<float>();return out;}();auto it=values.find(glyph);return it==values.end()?26.66667f:it->second;}
inline std::pair<std::string,int> window(const std::string& text,float time,float limit=390){
 auto glyphs=debate::glyphs(text);float total=0;for(const auto& g:glyphs)total+=width(g);if(total<=limit)return{text,0};
 float tail=0;int last=int(glyphs.size());while(last>0&&tail+width(glyphs[last-1])<=limit){tail+=width(glyphs[last-1]);--last;}
 float period=2.f+last*.12f,t=std::fmod(time,period);int start=t<=1?0:std::min(last,int((t-1)/.12f));std::string out;float used=0;
 for(int i=start;i<int(glyphs.size());i++){float w=width(glyphs[i]);if(used+w>limit)break;out+=glyphs[i];used+=w;}return{out,start};
}
}
float Yumeno::menuRowY(int index)const{return flowui::OPT_Y+(std::max(0,4-std::min(4,menuCount))+index-menuFirst)*flowui::OPT_STEP;}
hb::Json Yumeno::menuAuto(int index)const{
 if(index<menuFirst)return Json{{"kind","key"},{"key","w"}};if(index>=menuFirst+4)return Json{{"kind","key"},{"key","s"}};
 return Json{{"kind","click"},{"x",flowui::OPT_X+60},{"y",menuRowY(index)+flowui::OPT_H/2}};
}
void Yumeno::menuDraw(float delta){
 if(mode!=Mode::Menu||menuCount<=0)return;const auto& layout=flowchoice::layout();const auto& source=layout["source"];
 if(menuShownHover!=menuHover){menuShownHover=menuHover;menuFocusTicks=menuMarqueeTicks=0;}
 menuFocusTicks+=delta*60;menuMarqueeTicks+=delta;
 if(menuHover<menuFirst)menuFirst=menuHover;if(menuHover>=menuFirst+4)menuFirst=menuHover-3;menuFirst=std::clamp(menuFirst,0,std::max(0,menuCount-4));
 int count=std::min(4,menuCount),local=menuHover-menuFirst,frame=int(menuFocusTicks);const Json* track=nullptr;
 for(const auto& t:layout["tracks"])if(t["count"]==(count==1?2:count)&&t["index"]==(count==1?1:local)){track=&t;break;}
 if(track)frame=std::min(frame,int((*track)["frames"].size())-1);else frame=0;
 auto caption=flowchoice::window(menuLabels[menuHover],menuMarqueeTicks);int flash=menuPending>=0?std::clamp(int(menuConfirmTicks),0,11):-1;
 auto stamp=std::to_string(menuCount)+":"+std::to_string(menuHover)+":"+std::to_string(menuFirst)+":"+std::to_string(frame)+":"+std::to_string(caption.second)+":"+std::to_string(flash);
 if(stamp==menuRenderStamp)return;menuRenderStamp=stamp;
 for(int i=0;i<9;i++){bool visible=i<menuCount&&i>=menuFirst&&i<menuFirst+4,selected=i==menuHover;auto n=std::to_string(i);
  fvis("FOptP"+n,visible);fvis("FOptT"+n,visible);fvis("FOptA"+n,visible&&selected);fvis("FOptC"+n,visible&&selected&&menuPending>=0);if(!visible)continue;
  int slot=4-count+i-menuFirst;float bx=source["base_x"].get<float>(),tx=source["text_x"].get<float>(),ax=bx,y=source["base_y"][slot].get<float>(),ty=source["text_y"][slot].get<float>();
  if(selected&&track){const auto& f=(*track)["frames"][frame];bx=f["base"][0].get<float>();tx=f["text"][0].get<float>();ax=f["active"][0].get<float>();}
  UI::SetPosition(this,flowui::ID,"FOptP"+n,{bx,y});UI::SetPosition(this,flowui::ID,"FOptA"+n,{ax,y});UI::SetPosition(this,flowui::ID,"FOptC"+n,{bx+14.f*2/3,y+10.f*2/3});UI::SetPosition(this,flowui::ID,"FOptT"+n,{tx,ty});
  UI::SetColor(this,flowui::ID,"FOptT"+n,selected?Color{0,0,0,1}:Color{1,1,1,1});UI::SetTexture(this,flowui::ID,"FOptA"+n,flash>=0&&track&&track->contains("confirmationAssets")?(*track)["confirmationAssets"][flash].get<std::string>():std::string("Assets/Art/ui/v3/choice_on.svg"));
  ftext("FOptT"+n,selected?caption.first:flowchoice::window(menuLabels[i],0).first);
 }
}
void Yumeno::menuAccept(int index,int route){
 if(menuPending>=0||index<0||index>=menuCount)return;
 if((route==1&&index<int(v4MenuChoices.size())&&v4MenuChoices[index]>=0)||route==4)
  pv4::Action(presentationV4,"ui_confirm");
 menuHover=index;menuShownHover=index;menuFocusTicks=1000;menuPending=index;menuRoute=route;menuConfirmTicks=0;menuRenderStamp.clear();menuDraw();
}
bool Yumeno::menuVisualUpdate(float delta){
 bool pending=menuPending>=0;if(pending)menuConfirmTicks+=delta*60;menuDraw(delta);
 if(pending&&menuConfirmTicks>=12){int index=menuPending,route=menuRoute;menuPending=-1;menuConfirmTicks=0;++menuCommits;
  if(route==1)v4MenuPick(index);else if(route==2)v4HubPick(index);else if(route==3)v4GiftPick(index);else if(route==4)v4FreePick(index);else menuPicked(index);
 }
 return pending;
}
std::string Yumeno::ChoiceStats()const{return Json{{"count",menuCount},{"hover",menuHover},{"first",menuFirst},{"pending",menuPending},{"commits",menuCommits},{"labels",menuLabels},{"focusTicks",menuFocusTicks},{"confirmTicks",menuConfirmTicks},{"marqueeSeconds",menuMarqueeTicks}}.dump();}
