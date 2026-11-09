#pragma once
void Yumeno::drawNonstopSourceHud(float delta){
 const bool panic=stageKind=="panic"&&debate.panic();
 const bool owns=v4TaskActive&&(stageKind=="nonstop"||panic)&&mode==Mode::Trial&&playingDebate;
 if(!owns){if(UI::Mounted("nonstophud"))UI::Remove(this,"nonstophud");return;}
 if(!UI::Mounted("nonstophud")){UI::Show(this,"Assets/UI/NonstopSourceHud.hbwidget.json","nonstophud");nonstopHudLayout=Data::Get("Assets/Data/nonstop_source_hud.json");nonstopCylinderAngle=float(bullet*60);}
 const bool on=debateIntroTime<0&&!inScript&&!v4QueueActive&&clearTimer<=0&&debateResultTime<=0;
 UI::SetVisible(this,"nonstophud","root",on);
 for(auto id:{"NamePanel","TrialSpeaker","StatusPanel","StatusLabel","Cylinder","BulletPlate","Bullet","BulletLabel","TimerPanel","Timer"})UI::SetVisible(this,UI_ID,id,false);
 for(int i=0;i<10;i++)UI::SetVisible(this,UI_ID,"Star"+std::to_string(i),false);
 UI::SetVisible(this,"trialvitalsv4","root",false);
 const float ammoBlend=debateIntroTime<0?1.f:court::smooth5((debateIntroTime-court::nonstopFocusStart(int(bullets.size())))/court::NONSTOP_FOCUS);
 const bool preview=!on&&debateIntroTime>=0&&ammoBlend>0;
 UI::SetVisible(this,"nonstophud","root",on||preview);
 UI::SetOpacity(this,"nonstophud","Ammo",ammoBlend);
 for(auto id:{"Status","Hearts","Stars","Name","Speaker","Clock","DotActive"})UI::SetVisible(this,"nonstophud",id,on);
 for(int i=0;i<9;i++)UI::SetVisible(this,"nonstophud","Clock"+std::to_string(i),on);
 if(!on)for(int i=0;i<20;i++)UI::SetVisible(this,"nonstophud","Dot"+std::to_string(i),false);
 if(!on&&!preview)return;
 const bool inverted=lie||(!flyingEvidence.empty()&&shotLie);
 auto image=[&](const char* id,const std::string& file){
  const std::string node=id;
  const bool warm=panic&&!inverted&&(node=="Cylinder"||node=="AmmoFrame"||node=="BulletPlate"||node=="PlateMiddle"||node=="PlateTip");
  UI::SetTexture(this,"nonstophud",id,"Assets/Art/ui/nonstop_source/"+std::string(warm?"panic_":"")+file);
 };
 const std::string label=!flyingEvidence.empty()?flyingLabel:texts.count("Bullet")?texts.at("Bullet"):std::string();
 float labelEm=0;for(const auto& g:debate::glyphs(label))labelEm+=glyphmetrics::advance(g,"pretendard/Pretendard-Medium.otf");
 const float cap=42.666667f,font=std::min(20.f,320.f/std::max(.1f,labelEm)),width=std::max(139.3333f,font*labelEm+62.f);
 UI::SetFontSize(this,"nonstophud","Bullet",font);
 UI::SetSize(this,"nonstophud","Cartridge",{width,85.333333f});
 UI::SetSize(this,"nonstophud","PlateMiddle",{width-cap*2,85.333333f});UI::SetPosition(this,"nonstophud","PlateTip",{width-cap,0});
 UI::SetSize(this,"nonstophud","Bullet",{width-54,30});UI::SetText(this,"nonstophud","Bullet",label);
 for(const auto& part:std::vector<std::pair<std::string,std::string>>{{"BulletPlate","Left"},{"PlateMiddle","Middle"},{"PlateTip","Tip"}})image(part.first.c_str(),"ammoPlate"+std::string(inverted?"Lie":"")+part.second+".png");
 UI::SetColor(this,"nonstophud","Bullet",inverted?Color{.23f,.08f,.37f,1}:Color{.06f,.17f,.27f,1});
 for(int i=0;i<9;i++){const auto id="AmmoStock"+std::to_string(i);UI::SetVisible(this,"nonstophud",id,i<int(bullets.size())-1);if(i<int(bullets.size())-1)image(id.c_str(),std::string(i==bullet?"ammoSelected":"ammoStock")+std::to_string(i)+".png");}
 const float firingAge=flyingEvidence.empty()?-1.f:shotDuration-shotTimeLeft;
 UI::SetVisible(this,"nonstophud","Bullet",true);
 float difference=std::remainder(float(bullet*60)-nonstopCylinderAngle,360.f);nonstopCylinderAngle+=difference*std::min(1.f,std::max(0.f,delta)*24);
 int frame=(int(std::round(nonstopCylinderAngle/10))%36+36)%36;
 const std::string palette=inverted?"Lie":"";
 image("Cylinder","ammoCylinder"+palette+std::to_string(frame)+".png");
 image("AmmoFrame",firingAge>=0&&firingAge<23.f/60?"ammoFrame"+palette+"Shot"+std::to_string(std::min(22,int(firingAge*60)))+".png":"ammoFrame"+palette+".png");
 if(!on)return;
 UI::SetTexture(this,UI_ID,"Aim",held.at("Shift")&&!focusExhausted&&debate.focus>0?"Assets/Art/ui/nonstop_source/aim_focus.svg":nonstopHudLayout["idleAim"].get<std::string>());
 image("Status",inverted?"statusLie.png":"status.png");
 image("Clock",inverted?"clockLie.png":"clock.png");
 const int ms=std::max(0,int(debateTime*1000));char time[16];std::snprintf(time,sizeof time,"%02d:%02d:%03d",ms/60000,ms/1000%60,ms%1000);
 for(int i=0;i<9;i++){int digit=time[i]==':'?10:time[i]-'0';image(("Clock"+std::to_string(i)).c_str(),std::string("digit")+(inverted?"Lie":"")+std::to_string(digit)+".png");}
 auto rect=[&](const char* id,const Json& r){UI::SetPosition(this,"nonstophud",id,{r[0].get<float>()-1280,r[1].get<float>()});UI::SetSize(this,"nonstophud",id,{r[2],r[3]});};
 const int bank=maxHearts<=5?5:maxHearts<=7?7:10;
 const int hp=std::clamp(int(std::ceil(float(v4TaskHp())/(maxHearts*2000)*bank*2)),0,bank*2);
 image("Hearts","heart"+std::to_string(bank)+(inverted?"Lie_":"_")+std::to_string(hp)+".png");rect("Hearts",nonstopHudLayout["hearts"][std::to_string(bank)]);
 const int focus=std::clamp(int(std::ceil(debate.focus/maximumFocus()*bank*2)),0,bank*2);
 image("Stars","star"+std::to_string(bank)+(inverted?"Lie_":"_")+std::to_string(focus)+".png");rect("Stars",nonstopHudLayout["stars"][std::to_string(bank)]);
 const int lane=debate.panicDisplayLane;
 const auto& l=panic?debate.lines[debate.laneLine(lane)]:debate.line();
 UI::SetText(this,"nonstophud","Speaker",l.speaker.empty()?nameOf(l.actor):l.speaker);
 image("Name",inverted?"nameLie.png":"name.png");
 UI::SetColor(this,"nonstophud","Speaker",inverted?Color{.035f,.045f,.065f,1}:Color{.886f,.906f,.945f,1});
 int count=0,index=0;
 const int activeLine=panic?debate.laneLine(lane):debate.index;
 for(int i=0;i<int(debate.lines.size());++i)if(debate.lines[i].kind!="noise"&&(!panic||debate.laneOf(i)>=0)){
  if(i==activeLine)index=count;
  ++count;
 }
 count=std::clamp(count,1,20);index=std::clamp(index,0,count-1);
 for(int i=0;i<20;i++){UI::SetVisible(this,"nonstophud","Dot"+std::to_string(i),i<count);if(i<count)image(("Dot"+std::to_string(i)).c_str(),inverted?"dotLie.png":"dot.png");}
 image("DotActive",inverted?"dotActiveLie.png":"dotActive.png");
 const auto& marker=nonstopHudLayout["speakerMarkerPositions"][index];UI::SetPosition(this,"nonstophud","DotActive",{marker[0],marker[1]});
}
