#pragma once
#include "NonstopRefuteSourceV4.hpp"
// Presentation is shared by nonstop and panic; it never decides the answer.
void Yumeno::setupResultPlanes(){
 if(!resultPlanes.empty())return;resultPlaneData=Data::Get("Assets/Data/debate_fx.json");
 for(auto& row:resultPlaneData["planes"]){std::string id=row["id"];auto& n=resultPlanes[id];auto r=row["rect"];n.x=r[0];n.y=r[1];n.w=r[2];n.h=r[3];n.depth=row["depth"];n.texture=row["texture"];}
}
void Yumeno::resultPlanePose(const std::string& id){auto& n=resultPlanes[id];UI::SetPosition(this,"debatefx",id,{n.x,n.y});}
void Yumeno::resultPlaneVisible(const std::string& id,bool on){auto& n=resultPlanes[id];n.requested=on;bool shown=on&&n.alpha>.02f;if(shown==n.shown)return;n.shown=shown;UI::SetVisible(this,"debatefx",id,shown);}
void Yumeno::resultPlaneTexture(const std::string& id,const std::string& texture){auto& n=resultPlanes[id];if(n.texture==texture)return;n.texture=texture;UI::SetTexture(this,"debatefx",id,texture);resultPlaneSize(id,n.w,n.h);}
void Yumeno::resultPlanePosition(const std::string& id,float x,float y){auto& n=resultPlanes[id];if(n.x==x&&n.y==y)return;n.x=x;n.y=y;resultPlanePose(id);}
void Yumeno::resultPlaneSize(const std::string& id,float w,float h){auto& n=resultPlanes[id];if(n.w==w&&n.h==h)return;n.w=w;n.h=h;float fitW=w,fitH=h;
 if((id=="ResultHero"||id=="ResultPartner")&&resultPlaneData["textures"].contains(n.texture)){auto dim=resultPlaneData["textures"][n.texture];float aspect=dim[0].get<float>()/dim[1].get<float>();if(w/h>aspect)fitW=h*aspect;else fitH=w/aspect;}
 UI::SetSize(this,"debatefx",id,{w,h});resultPlanePose(id);
}
void Yumeno::resultPlaneScale(const std::string& id,float x,float y){auto& n=resultPlanes[id];x=std::max(.01f,x);y=std::max(.01f,y);if(n.sx==x&&n.sy==y)return;n.sx=x;n.sy=y;UI::SetScale(this,"debatefx",id,{n.sx,n.sy});}
void Yumeno::resultPlaneRotation(const std::string& id,float angle){if(resultPlanes[id].angle==angle)return;resultPlanes[id].angle=angle;UI::SetRotation(this,"debatefx",id,angle);}
void Yumeno::resultPlaneAlpha(const std::string& id,float alpha){auto& n=resultPlanes[id];if(n.alpha==alpha)return;n.alpha=alpha;UI::SetOpacity(this,"debatefx",id,alpha);resultPlaneVisible(id,n.requested);}
std::string Yumeno::FxStats()const{hb::Json out=hb::Json::object();for(auto& [id,n]:resultPlanes){out[id]={{"visible",n.shown},{"texture",n.texture.substr(n.texture.find_last_of('/')+1)},{"carrier","native-ui"},{"position",{n.x,n.y}}};
 if(id=="ResultHero"||id=="ResultPartner"||id=="ResultWord"||id=="ResultWord2"){float w=n.w*n.sx,h=n.h*n.sy;float r=n.angle*court::PI/180,c=std::abs(std::cos(r)),s=std::abs(std::sin(r)),rw=w*c+h*s,rh=w*s+h*c;float x=n.x+n.w/2,y=n.y+n.h/2;out[id]["bounds"]={x-rw/2,y-rh/2,x+rw/2,y+rh/2};}
 }return out.dump();}
void Yumeno::resetDebateFx(){
 if(UI::Mounted("nonstophud"))UI::Remove(this,"nonstophud");
 endingSourceClear();
 if(debateCastTinted){for(int seat=0;seat<16;++seat)for(auto prefix:{"Seat","SeatRear"})if(auto* figure=actor(prefix+std::to_string(seat)))Sprites::SetColor(figure,{1,1,1,1});debateCastTinted=false;}
 if(auto* grade=actor("LieWorldGrade"))Components::SetFloat(grade,"PostProcessVolume","weight",0);
 if(debateResultTime>0){setCam(debateResultCam);UI::SetVisible(this,UI_ID,"Trial",true);UI::SetVisible(this,UI_ID,"CourtDim",mode==Mode::Trial);}
 debateResultTime=shotTimeLeft=0;debateResult.clear();flyingEvidence.clear();flyingMeshes.clear();flyingImpact=false;
 debateResultPhase=-1;
 debateFxValues.clear();
 if(!chargeSe.empty()){Audio::Stop(chargeSe);chargeSe.clear();}chargeSeOn=false;
 if(!stageShown)return;
 for(auto id:{"FocusVeil","ChargeRing","ChargeState","LieEyeL","LieEyeR","ShotTrail","ShotImpact","ResultRoot"})UI::SetVisible(this,"debatefx",id,false);
 UI::SetOpacity(this,UI_ID,"BulletPlate",1);UI::SetOpacity(this,UI_ID,"Bullet",1);
 for(auto& [id,n]:resultPlanes)resultPlaneVisible(id,false);
}
void Yumeno::debateSuccess(const std::string& result){
 if(v4TaskActive)v4NoiseReset();
 setupResultPlanes();
 debateResult=result;debateResultTime=DEBATE_RESULT_SECONDS;debateResultPhase=-1;debateResultCam=cam;
 debateFxValues.clear();
 const bool showdown=stageKind=="showdown"&&stage.contains("showdownV4"); /* 쇼다운은 논스톱 줄이 없다 : 상대와 벤 발언을 쓴다 */
 auto slug=stageKind=="lie"?stage.at("targetActor").get<std::string>():showdown?stage["showdownV4"].value("opponent",std::string()):!debate.line().actor.empty()?debate.line().actor:slugs.count(debate.line().speaker)?slugs.at(debate.line().speaker):"";debateResultSeat=court::seatOf(slug);
 UI::SetVisible(this,UI_ID,"Cutin",false);UI::SetVisible(this,UI_ID,"TrialMsg",false);messageTimer=0;
 // V3 LP Ch1 : 맞은 발언의 글자가 커졌다가 흰 섬광 속에 산산이 깨진 뒤 컷인. 그동안 글자 층(Trial 아래 MF)만 남기고 HUD 는 감춘다
 shatterGlyphs.clear();shatterUsed=false;
 if(!showdown&&stageKind!="lie"&&!debate.lines.empty()&&!debate.panic()){shatterGlyphs=debate.current();shatterUsed=!shatterGlyphs.empty();}
 if(shatterUsed){for(auto id:{"NamePanel","TrialSpeaker","StatusPanel","StatusLabel","Cylinder","BulletPlate","Bullet","BulletLabel","TimerPanel","Timer","Aim","VPoint","VPoint1","VPoint2","Lens"})UI::SetVisible(this,UI_ID,id,false);for(int k=0;k<10;k++)UI::SetVisible(this,UI_ID,"Star"+std::to_string(k),false);for(int k=0;k<20;k++)UI::SetVisible(this,"trialvitalsv4","Heart"+std::to_string(k),false);drawGlyphs("N",26,{});}
 else UI::SetVisible(this,UI_ID,"Trial",false);
 UI::SetVisible(this,UI_ID,"CourtDim",false);
 if(debate.panic())drawPanicLanes(false);
 for(int i=0;i<3;i++)for(auto id:{"PanicFig","PanicFrame","PanicName"})svis(id+std::to_string(i),false);
 UI::SetVisible(this,"debatefx","FocusVeil",false);
 UI::SetVisible(this,"debatefx","ChargeRing",false);UI::SetVisible(this,"debatefx","ChargeState",false);
 UI::SetVisible(this,"debatefx","LieEyeL",false);UI::SetVisible(this,"debatefx","LieEyeR",false);
 UI::SetVisible(this,"debatefx","ResultRoot",true);
 UI::SetOpacity(this,"debatefx","ResultRoot",1);
 const std::string resultFolder=(stageKind=="nonstop"||showdown)&&result!="lie"?"Assets/Art/ui/nonstop_":"Assets/Art/ui/";
 resultPlaneTexture("ResultBand",resultFolder+"result_scene_"+result+".svg");
 resultPlaneTexture("ResultWord","Assets/Art/ui/result_"+result+"_glyph0.svg");resultPlaneTexture("ResultWord2","Assets/Art/ui/result_"+result+"_glyph1.svg");
 const auto heroStem=std::string("Assets/Art/ui/")+(result=="lie"?"hero_lie_deduction.":"hero_"+result+".");std::string heroTexture;
 for(auto it=resultPlaneData.at("textures").begin();it!=resultPlaneData.at("textures").end();++it)if(it.key().rfind(heroStem,0)==0){heroTexture=it.key();break;}
 if(heroTexture.empty())throw std::runtime_error("Result hero missing from generated texture metadata: "+result);
 resultPlaneTexture("ResultCrack",resultFolder+"result_crack_"+result+".svg");resultPlaneTexture("ResultHero",heroTexture);
 if(debateResultSeat>=0)resultPlaneTexture("ResultPartner","Assets/Art/ui/"+std::string(result=="lie"?"negative_":"partner_")+slug+".webp");
 for(int i=0;i<5;i++)resultPlaneTexture("ResultBreak"+std::to_string(i),resultFolder+"result_"+result+"_break"+std::to_string(i)+".svg");
 UI::SetText(this,"debatefx","ResultClaim",stageKind=="lie"?stage.value("lie",std::string()):showdown?stage.value("blade",Json::object()).value("word",std::string()):debate.line().word.empty()?debate.line().text:debate.line().word);
 UI::SetColor(this,"debatefx","ResultClaim",result=="agree"?Color{.35f,.85f,1,1}:Color{1,.65f,.06f,1});
 UI::SetVisible(this,"debatefx","ResultClaim",false);UI::SetOpacity(this,"debatefx","ResultClaim",1);
 for(auto& [id,n]:resultPlanes)resultPlaneVisible(id,false);
 resultPlaneVisible("ResultCourtDim",true);
 // V3 3f0500 명중 : 논파 SE309(Ronpa) / 동의 SE310 / 위증 SE308
 sfx(result=="agree"?"v3se_310":result=="lie"?"v3se_308":"v3se_309");
 drawGlyphs("M",48,{});drawGlyphs("N",26,{});
}
void Yumeno::updateDebateFx(float delta){
 drawNonstopSourceHud(delta);
 bool negative=(holdTime>=0&&lie)||(debateResultTime>0&&debateResult=="lie"&&DEBATE_RESULT_SECONDS-debateResultTime<3.9f);auto gradeState=debateFxValues.find("worldNegative");if(gradeState==debateFxValues.end()||gradeState->second[0]!=(negative?1.f:0.f)){if(auto* grade=actor("LieWorldGrade"))Components::SetFloat(grade,"PostProcessVolume","weight",negative?1.f:0.f);debateFxValues["worldNegative"]={negative?1.f:0.f,0};}
 bool charging=holdTime>=0&&debateResultTime<=0&&(!v4TaskActive||stageKind=="lie"||lieV4.charge>0||lieV4.transformed);
 if(debateResultTime<=0){UI::SetVisible(this,"debatefx","ChargeRing",charging);UI::SetVisible(this,"debatefx","ChargeState",charging);}
 for(auto id:{"LieEyeL","LieEyeR"})UI::SetVisible(this,"debatefx",id,charging&&lie);
 // V3 3f0500 : 누르기 시작(case 19) SE341 + 반복 SE342, 떼면 342 를 멈추고 발사(case 10, SE305)
 if(charging!=chargeSeOn){chargeSeOn=charging;
  if(charging){sfx("v3se_341");if(hasAudio("v3se_342"))chargeSe=Audio::Play(art["audio"]["v3se_342"].get<std::string>(),1.f,1.f,"sfx");}
  else if(!chargeSe.empty()){Audio::Stop(chargeSe);chargeSe.clear();}}
 if(charging){
  float p=v4TaskActive&&stageKind!="lie"?std::clamp(lieV4.charge/60.f,0.f,1.f):std::clamp(holdTime/.45f,0.f,1.f);
  UI::SetPosition(this,"debatefx","ChargeRing",{aimX,aimY});
  UI::SetScale(this,"debatefx","ChargeRing",{1.25f-.4f*p,1.25f-.4f*p});
  UI::SetRotation(this,"debatefx","ChargeRing",holdTime*150);
  UI::SetVisible(this,"debatefx","ChargeState",false);
  for(auto id:{"LieEyeL","LieEyeR"})UI::SetScale(this,"debatefx",id,{.85f+.15f*p,.85f+.15f*p});
 }
 if(!flyingEvidence.empty()){
  const bool wasFlying=shotTimeLeft>NONSTOP_IMPACT;
  shotTimeLeft=std::max(0.f,shotTimeLeft-delta);
  const float elapsed=shotDuration-shotTimeLeft;
  const bool windup=elapsed<flyingWord.prepare;
  const bool inFlight=!windup&&elapsed<flyingWord.prepare+flyingWord.duration;
  const bool impact=!windup&&!inFlight&&flyingImpact&&shotTimeLeft>0.f;
  UI::SetVisible(this,"debatefx","ShotTrail",false);
  UI::SetOpacity(this,UI_ID,"Bullet",1.f);
  flyingMeshes.draw(std::clamp((elapsed-flyingWord.prepare)/flyingWord.duration,0.f,1.f),shotX,shotY,flyingWord.originY,inFlight);
  UI::SetVisible(this,"debatefx","ShotImpact",impact);
  if(impact){
   if(wasFlying)if(auto* camera=actor("Camera"))Camera::Shake(camera,.028f,.11f);
   const float burst=1.f-std::clamp(shotTimeLeft/NONSTOP_IMPACT,0.f,1.f);
   const float scale=.45f+burst*1.05f;
   UI::SetPosition(this,"debatefx","ShotImpact",{shotX,shotY});
   UI::SetScale(this,"debatefx","ShotImpact",{scale,scale});
   UI::SetOpacity(this,"debatefx","ShotImpact",1.f-burst);
  }
 }else if(shotTimeLeft>0){
  UI::SetSize(this,"debatefx","ShotTrail",{280,18});
  shotTimeLeft=std::max(0.f,shotTimeLeft-delta);
  float visualRate=.22f/shotDuration,t=(shotDuration-shotTimeLeft)*visualRate,p=std::clamp(t/.12f,0.f,1.f);
  UI::SetVisible(this,"debatefx","ShotTrail",t<.15f&&shotTimeLeft>0);
  UI::SetPosition(this,"debatefx","ShotTrail",{130+(shotX-130)*p,590+(shotY-590)*p});
  UI::SetRotation(this,"debatefx","ShotTrail",std::atan2(shotY-590,shotX-130)*180/court::PI);
  UI::SetOpacity(this,"debatefx","ShotTrail",std::clamp(shotTimeLeft*visualRate/.08f,0.f,1.f));
  UI::SetVisible(this,"debatefx","ShotImpact",t>=.10f&&shotTimeLeft>0);
  UI::SetPosition(this,"debatefx","ShotImpact",{shotX,shotY});
  float scale=.2f+.9f*std::clamp((t-.1f)/.12f,0.f,1.f);
  UI::SetScale(this,"debatefx","ShotImpact",{scale,scale});
  UI::SetOpacity(this,"debatefx","ShotImpact",std::clamp(shotTimeLeft*visualRate/.1f,0.f,1.f));
 }
 if(debateResultTime>0){
  debateResultTime=std::max(0.f,debateResultTime-delta);
  float t=DEBATE_RESULT_SECONDS-debateResultTime;
  bool lying=debateResult=="lie",agreeing=debateResult=="agree";
  // Avoid serial native/UI work for unchanged or hidden presentation properties.
  auto changed=[&](const std::string& key,float x,float y,float epsilon){auto it=debateFxValues.find(key);if(it!=debateFxValues.end()&&std::abs(it->second[0]-x)<epsilon&&std::abs(it->second[1]-y)<epsilon)return false;debateFxValues[key]={x,y};return true;};
  auto pos=[&](const std::string& id,float x,float y){if(changed("p"+id,x,y,.15f))resultPlanePosition(id,x,y);};
  auto size=[&](const std::string& id,float x,float y){if(changed("s"+id,x,y,.01f))resultPlaneSize(id,x,y);};
  auto scale=[&](const std::string& id,float x,float y){if(changed("z"+id,x,y,.001f))resultPlaneScale(id,x,y);};
  auto opacity=[&](const std::string& id,float v){if(changed("a"+id,v,0,.004f))resultPlaneAlpha(id,v);};
  auto rotation=[&](const std::string& id,float v){if(changed("r"+id,v,0,.1f))resultPlaneRotation(id,v);};
  const std::string sourceCutin=lying?"lieCutin":agreeing?"agreeCutin":stageKind=="panic"?"panicCutin":"";
  const float cutEnd=v4TaskActive?1.35f+(sourceCutin.empty()?nonstoprefutev4::frames.size():endingsourcev4::frames.at(sourceCutin).size())/60.f:3.05f;
  const float breakBegin=v4TaskActive?cutEnd+(lying?43.f/60.f:.4f):3.9f;
  int phase=t<1.35f?0:t<cutEnd?1:t<breakBegin?2:t<5.65f?3:4;
  const bool sourceRefute=v4TaskActive&&stageKind!="panic"&&debateResult=="refute";
  if(sourceRefute&&phase==2&&debateResultPhase==1){
   // Restore the shared crack/Break carriers after the source cut-in owns them.
   for(const auto& row:resultPlaneData["planes"]){auto id=row["id"].get<std::string>();auto r=row["rect"];resultPlaneSize(id,r[2],r[3]);resultPlanePosition(id,r[0],r[1]);resultPlaneScale(id,1,1);resultPlaneRotation(id,0);resultPlaneAlpha(id,1);resultPlaneVisible(id,false);}
   resultPlaneTexture("ResultCrack","Assets/Art/ui/nonstop_result_crack_refute.svg");
   for(int i=0;i<5;++i)resultPlaneTexture("ResultBreak"+std::to_string(i),"Assets/Art/ui/nonstop_result_refute_break"+std::to_string(i)+".svg");
   resultPlaneTexture("ResultShard0","Assets/Art/ui/result_shatter.svg");resultPlaneTexture("ResultInk","Assets/Art/ui/result_ink.svg");debateFxValues.clear();
  }
  if(phase!=debateResultPhase){debateResultPhase=phase;
   // V3 3ee7b0 : 준비 뒤 컷인 SE330(논파)/331(동의), 이어 파괴 단계 SE327. 위증 3ef2f0 은 SE346 → 349
   if(phase==1)sfx(agreeing?"v3se_331":lying?"v3se_346":"v3se_330");
   if(phase==2)sfx(lying?"v3se_349":stageKind=="panic"?"v3se_348":"v3se_327");
  }
  auto vis=[&](const std::string& id,bool v){if(changed("v"+id,v?1.f:0.f,0,.1f)){if(id=="ResultClaim")UI::SetVisible(this,"debatefx",id,v);else resultPlaneVisible(id,v);}};
  // Push toward the actual struck seat, then restore the pre-hit camera after the wipe.
  if(debateResultSeat>=0&&phase==0){auto target=court::frame(court::seatAngle(debateResultSeat),-7+10*std::min(t/3.f,1.f),1.95f,1.78f,0,lying?-4.f:4.f);float p=court::smooth5(t/.65f);
   setCam({debateResultCam.x+(target.x-debateResultCam.x)*p,debateResultCam.y+(target.y-debateResultCam.y)*p,debateResultCam.z+(target.z-debateResultCam.z)*p,court::turn(debateResultCam.yaw,target.yaw,p),debateResultCam.pitch*(1-p),debateResultCam.roll+(target.roll-debateResultCam.roll)*p});}
  const bool gpuShatter=v4TaskActive&&fractureSupportedV4&&t>=breakBegin&&t<breakBegin+1.2f;
  vis("ResultWash",(lying&&phase==0&&t<.34f)||(phase>=3&&!gpuShatter));
  if(changed("washColor",phase>=3?1.f:0.f,0,.1f))resultPlaneTexture("ResultWash",phase>=3?"Assets/Art/ui/result_black.svg":"Assets/Art/ui/result_white.svg");
  opacity("ResultWash",phase>=3?1:lying?1-court::smooth5((t-.10f)/.24f):0);
  vis("ResultClaim",phase==0&&t<.8f&&!shatterUsed);
  if(shatterUsed&&!shatterGlyphs.empty()){
   if(t<.9f){float cx=0,cy=0;int nw=0;for(const auto& g:shatterGlyphs)if(g.weak){cx+=g.x;cy+=g.y;++nw;}if(nw){cx/=nw;cy/=nw;}else{cx=640;cy=360;}
    std::vector<debate::Glyph> out;out.reserve(shatterGlyphs.size());int k=0;
    for(auto g:shatterGlyphs){++k;float h1=debate::hash(k,7)-.5f,h2=debate::hash(k,8)-.5f,h3=debate::hash(k,9);
     if(g.weak){float pop=court::smooth5(t/.16f),br=std::clamp((t-.16f)/.7f,0.f,1.f),e=1-std::pow(1-br,2);
      float dx=g.x-cx,dy=g.y-cy;g.x=cx+dx*(1+.35f*pop)+(dx*2.2f+h1*900)*e;g.y=cy+dy*(1+.35f*pop)+(dy*2.2f+h2*700-120)*e+380*br*br;
      g.scale*=1+.55f*pop+.8f*e;g.rotation+=(h1>0?1:-1)*(120+h3*260)*e;g.opacity*=1-std::pow(br,1.6f);g.front=true;}
     else{float f=std::clamp(t/.22f,0.f,1.f);g.x+=h1*260*f;g.y+=h2*140*f;g.rotation+=h1*40*f;g.opacity*=1-f;}
     out.push_back(g);}
    drawGlyphs("M",48,out);}
   else{drawGlyphs("M",48,{});UI::SetVisible(this,UI_ID,"Trial",false);shatterGlyphs.clear();}
  }
  float enter=court::smooth5((t-1.35f)/.18f),exit=court::smooth5((t-2.85f)/.20f);
  bool cut=phase==1;vis("ResultBand",cut);vis("ResultBolt",cut);vis("ResultHero",cut);vis("ResultWord",cut);vis("ResultWord2",cut&&t>1.48f);
  if(cut){pos("ResultBand",(lying?-1.f:1.f)*850*(1-enter)-850*exit,0);scale("ResultBand",1,enter);opacity("ResultBolt",std::clamp(enter-exit,0.f,1.f));}
  // Dk_JjYZEzdg03:13: deliberate face close-up cropped at the lower/right
  // viewport. Perjury10:24 uses a separate calculating upper-body pose.
  float hx=agreeing?775.f:lying?200.f:400.f,hy=agreeing?30.f:lying?-80.f:-100.f;
  if(cut){size("ResultHero",agreeing?450.f:lying?900.f:1400.f,agreeing?660.f:lying?1148.f:2456.f);pos("ResultHero",hx+180*(1-enter)-150*exit,hy+30*(1-enter)+35*exit);scale("ResultHero",.96f+.04f*enter-.03f*exit,.96f+.04f*enter-.03f*exit);}
  vis("ResultPartner",debateResultSeat>=0&&agreeing&&cut);
  if(agreeing&&cut){size("ResultPartner",450.f,650.f);pos("ResultPartner",40.f-16*(1-enter),35.f+8*(1-enter));scale("ResultPartner",.92f+.08f*enter-.04f*exit,.92f+.08f*enter-.04f*exit);}
  if(cut)for(int i=0;i<2;i++){
   std::string id=i?"ResultWord2":"ResultWord";
   float x=agreeing?475.f:lying?(i?930.f:40.f):(i?280.f:60.f);
   float y=agreeing?(i?345.f:75.f):lying?(i?340.f:20.f):(i?275.f:65.f);
   float p=court::smooth5((t-1.35f-i*.13f)/.14f),s=1.20f-.20f*p,angle=agreeing?0.f:lying?14.f:16.f;
   float extent=180*s*(std::abs(std::cos(angle*court::PI/180))+std::abs(std::sin(angle*court::PI/180)));
   float cx=std::clamp(x+180+80*(1-p),12+extent,1268-extent),cy=std::clamp(y+180,12+extent,708-extent);
   pos(id,cx-180,cy-180);scale(id,s,s);rotation(id,angle);
  }
  vis("ResultCrack",phase==2&&!lying);if(phase==2&&!lying)opacity("ResultCrack",court::smooth5((t-3.05f)/.12f));
  vis("ResultInk",lying&&phase>=2);float ink=court::smooth5((t-3.05f)/.7f)*4;
  if(lying&&phase>=2){scale("ResultInk",ink,ink);pos("ResultInk",0,0);}
  {std::string id="ResultShard0";bool early=phase==0;vis(id,!lying&&(early||phase==2));
   if(!lying&&(early||phase==2)){
    float p=early?std::clamp((t-.12f)/1.1f,0.f,1.f):std::clamp((t-3.05f)/.85f,0.f,1.f);
    float s=.05f+p*(early?2.8f:4.3f);scale(id,s,s);rotation(id,p*(early?35.f:-28.f));opacity(id,early?1-p:1);
   }
  }
  for(int i=0;i<5;i++){auto id="ResultBreak"+std::to_string(i);float p=court::smooth5((t-3.95f-i*.075f)/.14f);vis(id,phase>=3&&p>0);if(phase>=3){opacity(id,p);scale(id,.7f+.3f*p,.7f+.3f*p);}}
  vis("ResultExit",phase==4&&!gpuShatter);if(phase==4)opacity("ResultExit",court::smooth5((t-5.35f)/.3f));
  if(sourceRefute&&cut){
   for(auto id:{"ResultHero","ResultPartner","ResultWord","ResultWord2"})resultPlaneVisible(id,false);
   static const char* layers[]{"ResultBand","ResultBolt","ResultCrack","ResultShard0","ResultInk","ResultBreak0","ResultBreak1","ResultBreak2","ResultBreak3"};
   const auto& rows=nonstoprefutev4::frames[std::clamp(int((t-1.35f)*60),0,int(nonstoprefutev4::frames.size())-1)];
   for(int i=0;i<9;++i){auto id=std::string(layers[i]);if(i>=int(rows.size())){resultPlaneVisible(id,false);continue;}const auto& r=rows[i];resultPlaneTexture(id,nonstoprefutev4::textures[r.texture]);resultPlanePosition(id,r.x,r.y);resultPlaneSize(id,r.w,r.h);resultPlaneScale(id,1,1);resultPlaneRotation(id,r.rotation);resultPlaneAlpha(id,r.alpha);resultPlaneVisible(id,true);}
  }
  if(v4TaskActive){
   fractureControl(t<cutEnd+.12f?"off":t<breakBegin?"capture":t<breakBegin+1.2f?"animate":"off",t-breakBegin);
   const bool showdown=stageKind=="showdown",panic=stageKind=="panic";
   const std::string crack=lying?"lieInk":agreeing?"agreeCrack":showdown?"showdownCrack":panic?"panicCrack":"crack";
   const std::string finish=lying?"lieBreak":agreeing?"agreeBreak":panic?"panicBreak":"refuteBreak";
   if(phase>=2){for(auto id:{"ResultCrack","ResultInk","ResultShard0"})resultPlaneVisible(id,false);for(int i=0;i<5;i++)resultPlaneVisible("ResultBreak"+std::to_string(i),false);}
   if(!sourceCutin.empty()&&phase==1){
    for(auto id:{"ResultBand","ResultBolt","ResultHero","ResultPartner","ResultWord","ResultWord2","ResultCrack","ResultInk","ResultShard0"})resultPlaneVisible(id,false);
    for(int i=0;i<5;i++)resultPlaneVisible("ResultBreak"+std::to_string(i),false);
    endingSourceFrame(sourceCutin,int((t-1.35f)*60));
   }else endingSourceFrame(crack,phase==2?int((t-cutEnd)*60):-1);
   const float finishEnd=breakBegin+endingsourcev4::frames.at(finish).size()/60.f;
   endingSourceFrame(finish,!showdown&&t>=breakBegin&&t<finishEnd?int((t-breakBegin)*60):-1,24);
   endingSourceBlack(phase>=3?1.f:0.f);
  }
  if(debateResultTime<=0){endingSourceClear();UI::SetVisible(this,"debatefx","ResultRoot",false);setCam(debateResultCam);const bool doneNonstop=v4TaskActive&&stageKind=="nonstop"&&clearTimer>0;UI::SetVisible(this,UI_ID,"Trial",!doneNonstop);UI::SetVisible(this,UI_ID,"CourtDim",!doneNonstop);if(!doneNonstop)debateHud(true);
   for(auto& [id,n]:resultPlanes)resultPlaneVisible(id,false);
   // A completed Nonstop proceeds to authored dialogue, without resurrecting
   // its aim/timer or adding an invented success announcement.
   if(doneNonstop){clearTimer=.001f;lieView(false);UI::SetVisible(this,UI_ID,"TrialMsg",false);messageTimer=0;}
  }
 }
}
