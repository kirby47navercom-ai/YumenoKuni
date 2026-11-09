// Authored groups keep dialogue separate from physical cut targets.
// 주인님 지시(2026-11-06) : 모든 진타를 1장 T1-RS-01 짜임(첫 파동 여러 발언 → 발전 → 미오·상대 대화 → 다음 파동 → 약점)으로.
// 대본에 발언이 2개뿐인 과제는 Assets/Data/showdown_extra.json 의 Claude 추가 줄로 채운다(상대의 같은 주장을 되풀이할 뿐 새 사실 없음).
void Yumeno::v4ShowdownExtra(){
 auto& sd=stage["showdownV4"];if(sd.value("_extra",false))return;sd["_extra"]=true;
 const auto& all=Data::Get("Assets/Data/showdown_extra.json");auto id=v4Task.value("taskId",std::string());if(!all.contains(id))return;const auto& x=all[id];
 auto& order=sd["statementOrder"];Json first=sd["statements"].at(order[0].get<std::string>());auto spk=first.value("speaker",std::string()),act=first.value("actor",std::string());int n=0;
 auto add=[&](const Json& text){std::string sid="x:"+id+":"+std::to_string(n++);sd["statements"][sid]=Json{{"id",sid},{"speaker",spk},{"actor",act},{"text",text},{"kind","plain"},{"role","ordinary"},{"requiredHits",2},{"gaugeGain",5},{"gaugeLoss",-5},{"durationFrames",216}};int k=int(order.size());order.push_back(sid);return Json{{"type","statement"},{"lineId",sid},{"statementIndex",k}};};
 auto& groups=sd["groups"];
 if(x.contains("g0")){auto& en=groups[0]["entries"];for(const auto& t:x["g0"])en.push_back(add(t));int c=0;for(const auto& e:en)if(e.value("type",std::string())!="dialogue")++c;groups[0]["advanceThreshold"]=50+5*c;} /* 넘어가는 기준 = 50+발언 수×5(원래 규칙) */
 if(x.contains("talk")){if(!groups[0].contains("afterAdvance")||!groups[0]["afterAdvance"].is_array())groups[0]["afterAdvance"]=Json::array();for(const auto& t:x["talk"]){bool me=t[0].get<std::string>()=="mio";groups[0]["afterAdvance"].push_back(Json{{"type","say"},{"speaker",me?std::string("미오"):spk},{"actor",me?std::string("mio"):act},{"text",t[1]},{"mono",false}});}}
 if(x.contains("last")){auto& en=groups[groups.size()-1]["entries"];Json lead=Json::array();for(const auto& t:x["last"])lead.push_back(add(t));for(const auto& e:en)lead.push_back(e);en=lead;}
 // 주인님 지시 : 난이도 = 노란 약점 후보 수 + 코토다마 칼 수. 1장이 기점(영상), 장마다 늘린다. 수치는 showdown_extra.json "_difficulty"
 const auto& dif=all.value("_difficulty",Json::object());float lv=0;{lv=id.size()>1&&std::isdigit((unsigned char)id[1])?float(id[1]-'1'):0.f;if(id.find("-A02")!=std::string::npos)lv+=.3f;if(id.find("-A03")!=std::string::npos)lv+=.6f;}
 {int want=dif.value("decoyBase",0)+int(lv*dif.value("decoyPerLevel",.5f));auto& en=groups[groups.size()-1]["entries"];
  for(auto& e:en){if(want<=0)break;if(e.value("type",std::string())=="dialogue")continue;auto sid=order.at(e.value("statementIndex",0)).get<std::string>();auto& row=sd["statements"][sid];if(row.value("role",std::string())=="blade")continue;
   auto ch=debate::glyphs(row.value("text",std::string()));int bs=-1,bl=0;for(int i=0;i<int(ch.size());){if(ch[i]==" "){++i;continue;}int j=i;while(j<int(ch.size())&&ch[j]!=" ")++j;int len=j-i;while(len>1&&(ch[i+len-1]=="."||ch[i+len-1]=="?"||ch[i+len-1]=="!"||ch[i+len-1]==","||ch[i+len-1]=="…"))--len;if(len>bl){bl=len;bs=i;}i=j;}
   if(bs<0||bl<2)continue;std::string w;for(int k=bs;k<bs+bl;k++)w+=ch[k];row["decoy"]=true;row["requiredHits"]=1;row["bladeTarget"]=Json{{"start",bs},{"word",w}};--want;}} /* 가짜 약점 : 그 발언의 가장 긴 어절(문장부호 뺌) */
}
void Yumeno::v4ShowdownBlades(){ /* 칼 판 : 정답 + 같은 장 다른 코토다마. 수는 장마다 늘고 목록(6칸)을 넘지 않는다 */
 const auto& dif=Data::Get("Assets/Data/showdown_extra.json").value("_difficulty",Json::object());auto id=v4Task.value("taskId",std::string());auto answer=stage["showdownV4"].value("answerEvidenceId",std::string());
 int want=std::clamp(dif.value("bladeBase",4)+int(sdLevel*dif.value("bladePerLevel",.4f)),1,6);auto& opts=stage["options"];if(!opts.is_array())return;{const auto& all=Data::Get("Assets/Data/showdown_extra.json");if(all.contains(id)&&all[id].contains("blades"))for(const auto& b:all[id]["blades"]){bool have=false;for(const auto& o:opts)have=have||o.value("id",std::string())==b.value("id",std::string());if(!have)opts.push_back(b);}} /* 대본에 정답 칼 하나뿐인 과제(T2-RS-A03)는 같은 장 코토다마로 칼 판을 채운다 */if(int(opts.size())<=want){bladeIds.clear();for(auto& o:opts)bladeIds.push_back(o.value("id",std::string()));bladeList();return;}
 auto h=[&](const std::string& s){unsigned v=2166136261u;for(unsigned char c:id+s){v^=c;v*=16777619u;}return v;};
 Json ans;std::vector<std::pair<unsigned,Json>> rest;for(auto& o:opts){if(o.value("id",std::string())==answer)ans=o;else rest.push_back({h(o.value("id",std::string())),o});}if(ans.is_null())return;
 std::sort(rest.begin(),rest.end(),[](const auto& a,const auto& b){return a.first<b.first;});Json kept=Json::array();int at=int(h("answer")%unsigned(want));for(int i=0,r=0;i<want;i++)kept.push_back(i==at?ans:rest[r++].second);
 opts=kept;bladeIds.clear();for(auto& o:opts)bladeIds.push_back(o.value("id",std::string()));sdBullet=0;bladeList();
}
void Yumeno::v4ShowdownStart(){
 v4ShowdownExtra();const auto& spec=stage.at("showdownV4");std::vector<showdownv4::Statement> statements;std::vector<showdownv4::Group> groups;
 { /* 장이 갈수록 조금씩 어렵게(주인님 지시) : T1=0 … T6=5, 같은 장의 A02 +0.3·A03 +0.6 */
  auto id=v4Task.value("taskId",std::string());sdLevel=id.size()>1&&std::isdigit((unsigned char)id[1])?float(id[1]-'1'):0.f;if(id.find("-A02")!=std::string::npos)sdLevel+=.3f;if(id.find("-A03")!=std::string::npos)sdLevel+=.6f;sdLevel=std::clamp(sdLevel,0.f,6.f);}
 const float lv=sdLevel,durK=1-.03f*lv,gainK=1.f,lossK=1+.05f*lv; /* 주인님 지시 : 1장(영상) 난이도가 기점, 뒤로 갈수록 살짝(6장 발언 시간 ≈0.85배) */ /* 발언 시간 ↓(6장 ≈0.7배), 놓칠 때 깎이는 형세 ↑. 오르는 형세는 그대로(넘어가는 기준 = 50+발언 수×5 라 줄이면 못 넘는다) */
 for(const auto& id:spec["statementOrder"]){const auto& row=spec["statements"].at(id.get<std::string>());showdownv4::Statement s;s.id=id.get<std::string>();s.blade=row.value("role",std::string())=="blade"||row.value("decoy",false);s.decoy=row.value("decoy",false);s.requiredHits=row.value("requiredHits",2);s.durationFrames=row.value("durationFrames",216.f)*durK*(skillOn("showdown_time")?1.3f:1.f);s.gaugeGain=row.value("gaugeGain",5.f)*gainK;s.gaugeLoss=row.value("gaugeLoss",-5.f)*lossK;statements.push_back(s);}
 for(const auto& row:spec["groups"]){showdownv4::Group g;g.threshold=row.value("advanceThreshold",60.f);g.initialGauge=row.value("initialGauge",50.f);g.settleFrames=row.value("gaugeSettleFrames",15);g.dwellFrames=row.value("endDwellFrames",10);g.tugRequired=row.value("tugRequired",8)+int(lv*.5f); /* 힘겨루기 연타 수도 장마다 +1 */g.tugLimit=row.value("tugLimitFrames",180);for(const auto& e:row["entries"])g.entries.push_back({e.value("type",std::string())=="dialogue",e.value("statementIndex",-1)});groups.push_back(g);}
 v4ShowdownBlades();
 showdownV4.reset(statements,groups,v4TaskEntryHp,spec.value("timeFrames",10800.f)*(1-.025f*lv)*trialTimeFactor());showdownV4.wrongBladeDamage=spec.value("wrongBladeDamage",2000);showdownV4.groupFailureDamage=spec.value("groupFailureDamage",1000);if(v4TaskActive){showdownV4.wrongBladeDamage=growthv4::Damage(growthV4,difficultyv4::wakDamage(showdownV4.wrongBladeDamage,difficultyV4.logic));showdownV4.groupFailureDamage=growthv4::Damage(growthV4,difficultyv4::wakDamage(showdownV4.groupFailureDamage,difficultyV4.logic));}showdownV4.halfTug=skillOn("showdown_tug_half");showdownV4.bladeOffset=(skillOn("doutanuki")?32.f:8.f)*(2.f/3);showdownTicks=0;showdownShown=-1;showdownMouseX=aimX;showdownMouseY=aimY;sdBullet=0;
 drawPanicLanes(false);svis("Blade",false);svis("Slash",true);svis("Hint",false);svis("SpkTag",false);svis("StageMsg",false);
 for(auto id:{"SdLeft","SdRight","SdDivider","SdBladeFrame"})svis(id,true);
 UI::SetPosition(this,"stage","SpkName",{45,22});UI::SetFontSize(this,"stage","SpkName",20.f);
 UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);
 for(int i=0;i<48;i++)UI::SetScale(this,"panicv4","P0G"+std::to_string(i),{1.45f,1.45f}); // 논의 시작(startDebate)에서 1 로 되돌린다
 svis("SdFace",false);showdownFaceX=-1; /* 평면 미오 그림은 쓰지 않는다 — 오른쪽도 3D 법정 카메라(updateCamera sdViews) */
 {int me=court::seatOf("mio");if(me>=0)courtPose(me,poseTexture("mio","","mio_C12"));}
 UI::SetTexture(this,"stage","SdLeft","Assets/Art/ui/v3_hr/sd_left_ptn.webp");UI::SetColor(this,"stage","SdLeft",Color{1,1,1,1});UI::SetOpacity(this,"stage","SdLeft",.2f);UI::SetTexture(this,"stage","SdRight","Assets/Art/ui/v3_hr/sd_right_ptn.webp");UI::SetOpacity(this,"stage","SdRight",.2f); /* V3 t_hr_frame_ptn 붉은·푸른 무늬 */
 UI::SetTexture(this,"stage","SdDivider","Assets/Art/ui/v3_hr/sd_divider.webp");UI::SetSize(this,"stage","SdDivider",{40,720}); /* V3 t_hr_line_anm */ /* V3 : 상대 쪽 분홍, 주인공 쪽 파랑으로 물들 뿐 법정은 보인다 */
 UI::SetVisible(this,UI_ID,"Whip",false);bladeList();v4ShowdownDraw();
 UI::Show(this,"Assets/UI/ShowdownV3.hbwidget.json","sdv3");sdLastGroup=-1;sdPhaseFlash=0;sdBy=0;sdDeferred=Json::array();sdIntro=sdFromStory?2.6f:0.f;sdIntroPrev=sdIntro-.01f;sdFromStory=false;sdPreDone=false;sdCutinSlug=spec.value("opponent",std::string()); /* 이야기를 거치지 않고 들어오면(다시 하기·QA) 컷인부터 */sdAdvT=sdSlashT=0;sdBreak=-1; /* 컷인은 이야기 쪽 반론 대사 앞(V4Story) — 여기서는 제목부터 */ /* V3 HUD 는 따로 띄운다(Stage 위젯 노드 한도) */for(auto id:{"SdBladeFrame","BladeName","Slash"})svis(id,false);UI::SetVisible(this,UI_ID,"NamePanel",false);UI::SetVisible(this,UI_ID,"TrialSpeaker",false);sfx("v3se_374");
}
// 한국어판 V3 반론 쇼다운 시작(주인님 제공 영상 유튜브 Uba6XjXj8OU 1장, 2934~3097초 프레임 실측. 좌표는 1280x720 으로 환산)
//  0.0~2.6  상대의 「반론」 컷인 : 왼쪽에서 노란 띠 + 상대 얼굴 + 검은 붓 「반론」(2934.6~2936.2) → 초록 별빛 깨짐(2936.6~2937.8)
//  2.6~     제목 : 주황 수국 왼쪽 위·파랑 수국 오른쪽 아래, 「반론 / 쇼다운 / 진타」 세로 3줄이 빛나며 박힘(3089.2~3090.1) → 푸른 칼선에 베여 사라짐(3090.6)
//           → 칸막이 위 세로 「시작」 + 벚꽃·꽃잎(3091.0~3091.6) → 양쪽 푸른 칼선(3092.4) → 칼날 목록 : 왼쪽 큰 수국 위 칼 판이 하나씩 세로로(3094.2~3097.4)
void Yumeno::v4ShowdownIntro(float t){
 auto vis=[&](const std::string& id,bool v){UI::SetVisible(this,"sdv3",id,v);};auto box=[&](const std::string& id,float cx,float cy,float w,float h){UI::SetSize(this,"sdv3",id,{std::max(1.f,w),std::max(1.f,h)});UI::SetPosition(this,"sdv3",id,{cx-w*.5f,cy-h*.5f});};auto op=[&](const std::string& id,float o){UI::SetOpacity(this,"sdv3",id,std::clamp(o,0.f,1.f));}; /* 크기 0·불투명도 범위 밖은 위젯 검증에 걸린다 */
 auto ease=[](float u){u=std::clamp(u,0.f,1.f);return 1-std::pow(1-u,3);};auto ramp=[](float t,float a,float b){return std::clamp((t-a)/(b-a),0.f,1.f);};
 auto once=[&](float at,const char* se){if(t>=at&&t-sdIntroPrev<1.f&&sdIntroPrev<at)sfx(se);};
 // 상대 「반론」 컷인
 {bool on=t<1.65f;for(auto id:{"SdV3CiBg","SdV3CiEf","SdV3CiPl","SdV3CiFace","SdV3CiTx0","SdV3CiTx1"})vis(id,on);
  if(on){float in=ease(t/.18f),out=ramp(t,1.5f,1.65f),dx=-1100*(1-in)-300*out;
   box("SdV3CiBg",635+dx,360,1368,720);box("SdV3CiEf",635+dx*1.2f,360,1368,720); /* 2935.4초 실측 : 좁은 비스듬한 노란 띠(위 x368~1064, 아래 x192~624) */op("SdV3CiEf",.8f);box("SdV3CiPl",300+dx,520,720,720);
   auto face="Assets/Art/cutin/"+sdCutinSlug+"_1.webp";UI::SetTexture(this,"sdv3","SdV3CiFace",face);box("SdV3CiFace",432+dx*.8f,621,1000,975); /* 2935.4초 : 상대 가슴 위, 얼굴 가운데 ≈(432,300) */
   float s=1.35f-.35f*ease((t-.12f)/.12f);box("SdV3CiTx0",816+dx,112,177*s,190*s);box("SdV3CiTx1",752+dx,296,182*s,190*s); /* 2935.4초 : 「반」(816,112) 「론」(752,296), 띠 오른쪽 기울기 안 */for(auto id:{"SdV3CiTx0","SdV3CiTx1"})op(id,ramp(t,.1f,.16f));}
  once(.02f,"v3se_302");
  bool b=t>=1.75f&&t<2.6f;vis("SdV3CiBurst",b);if(b){float u=ramp(t,1.75f,2.6f);box("SdV3CiBurst",640,360,900+900*u,900+900*u);op("SdV3CiBurst",1-u*u);}once(1.75f,"v3se_376");
  {bool d=t>=2.2f&&t<2.62f;vis("SdV3CutDim",d);if(d){box("SdV3CutDim",640,360,1280,720);UI::SetTexture(this,"sdv3","SdV3CutDim","Assets/Art/ui/v3_hr/black.webp");op("SdV3CutDim",ramp(t,2.2f,2.45f));}}}
 float T=t-2.6f;
 if(T>=0&&T<.4f){vis("SdV3CutDim",true);box("SdV3CutDim",640,360,1280,720);UI::SetTexture(this,"sdv3","SdV3CutDim","Assets/Art/ui/v3_hr/black.webp");op("SdV3CutDim",1-ramp(T,.25f,.4f));}else if(T>=.4f&&T<.5f)vis("SdV3CutDim",false); /* 3087.5~3088.3 : 2분할 대사가 검게 사라지고 지그재그 2분할이 선다 */
 {bool on=T>=0&&T<4.6f;vis("SdV3Dim",on);if(on){box("SdV3Dim",640,360,1280,720);UI::SetTexture(this,"sdv3","SdV3Dim","Assets/Art/ui/v3_hr/black.webp");op("SdV3Dim",.42f*ramp(T,0,.3f)*(1-ramp(T,4.2f,4.6f)));}} /* 3088.6~3093 : 제목 동안 화면이 어둡다 */
 bool title=T>=0&&T<2.35f,start=T>=2.35f&&T<3.4f,list=T>=4.9f; /* 3093.5초 수국, 3093.8초부터 0.3초마다 칼 판 */
 {float u=ease(T/.35f),out=ramp(T,2.4f,2.8f);bool on=T>=0&&T<2.8f;vis("SdV3DecoL",on);vis("SdV3DecoR",on);
  if(on){box("SdV3DecoL",130-260*(1-u),60,560,560);box("SdV3DecoR",1150+260*(1-u),640,560,560);op("SdV3DecoL",(1-out)*.95f);op("SdV3DecoR",(1-out)*.95f);}}
 const float gx[7]{824,848,672,680,672,464,480},gy[7]{120,304,264,432,600,312,496},gt[7]{.55f,.67f,1.15f,1.25f,1.35f,1.45f,1.55f};
 const float gw[7]{265,251,249,253,220,203,243},gh[7]{284,261,208,280,274,270,280},ew[7]{364,352,340,344,316,302,342},eh[7]{380,360,304,384,372,370,380};
 for(int i=0;i<7;i++){auto e="SdV3TitleEf"+std::to_string(i),b="SdV3Title"+std::to_string(i);float a=T-gt[i];bool on=title&&a>=0;vis(b,on);vis(e,on&&a<.5f);if(!on)continue;
  float k=176.f/280*(1.45f-.45f*ease(a/.16f)),out=ramp(T,2.05f,2.3f);box(b,gx[i],gy[i],gw[i]*k,gh[i]*k);op(b,ramp(a,0,.06f)*(1-out));box(e,gx[i],gy[i],ew[i]*k,eh[i]*k);op(e,(1-ramp(a,.12f,.5f))*(1-out));once(T>=0?2.6f+gt[i]:99,"v3se_302");}
 {bool on=T>=2.0f&&T<2.3f;vis("SdV3Line0",on);if(on){float u=ease((T-2.f)/.12f);box("SdV3Line0",650,360,40,1500*u);UI::SetRotation(this,"sdv3","SdV3Line0",58);op("SdV3Line0",1-ramp(T,2.18f,2.3f));}once(4.6f,"sfx_band");}
 for(int i=0;i<2;i++){auto id="SdV3Start"+std::to_string(i);float a=T-2.35f-i*.08f;bool on=start&&a>=0;vis(id,on);if(!on)continue;float s=1.3f-.3f*ease(a/.14f);box(id,i?640.f:630.f,i?490.f:170.f,(i?352.f:308.f)*.66f*s,(i?388.f:384.f)*.66f*s);op(id,ramp(a,0,.06f)*(1-ramp(T,3.05f,3.35f)));}
 once(4.95f,"sfx_band");
 {const float px[8]{420,1140,820,300,980,560,1220,200},py[8]{190,110,650,90,360,600,520,420},ps[8]{120,190,130,40,46,34,40,30};
  for(int i=0;i<8;i++){auto id="SdV3Petal"+std::to_string(i);bool on=T>=2.35f&&T<3.6f;vis(id,on);if(!on)continue;float a=T-2.35f;box(id,px[i]+30*std::sin(a*2+i),py[i]+60*a,ps[i],ps[i]*(i<3?1.f:.84f));UI::SetRotation(this,"sdv3",id,a*90*(i&1?1:-1));op(id,ramp(a,0,.15f)*(1-ramp(T,3.2f,3.6f)));}}
 {const float lx[6]{300,960,420,820,200,1060},ly[6]{330,400,250,520,480,220},lr[6]{52,-62,70,-40,30,-75},ld[6]{0,.04f,.08f,.12f,.16f,.2f}; /* 3092.5~3093초 : 파랑·빨강·분홍·주황·노랑 칼선이 양쪽에 */
  for(int i=0;i<6;i++){auto id="SdV3Line"+std::to_string(i);float a0=3.9f+ld[i];if(T<a0||T>=a0+.45f){if(T>=2.3f&&!(i==0&&T<2.3f))vis(id,false);continue;}vis(id,true);float u=ease((T-a0)/.12f);box(id,lx[i],ly[i],i<2?30.f:20.f,1300*u);UI::SetRotation(this,"sdv3",id,lr[i]);op(id,1-ramp(T,a0+.25f,a0+.45f));}}
 once(6.4f,"sfx_band");
 int n=std::min(6,int(bladeIds.size()));vis("SdV3ListRing",list);if(list){float u=ease((T-4.9f)/.3f);box("SdV3ListRing",150,360,680*u,680*u);op("SdV3ListRing",.9f*u);}
 for(int i=0;i<6;i++){auto k="SdV3Kata"+std::to_string(i),tn="SdV3KataT"+std::to_string(i);float a=T-5.2f-i*.3f;bool on=list&&i<n&&a>=0;vis(k,on);vis(tn,on);if(!on)continue;float u=ease(a/.18f),x=64-120*(1-u),y=214+i*68.f;
  UI::SetTexture(this,"sdv3",k,"Assets/Art/ui/v3_hr/katana_sheathed.webp");UI::SetPosition(this,"sdv3",k,{x,y-32});UI::SetSize(this,"sdv3",k,{430,64});op(k,u);UI::SetPosition(this,"sdv3",tn,{x+30,y-15});UI::SetSize(this,"sdv3",tn,{240,28});op(tn,u);UI::SetText(this,"sdv3",tn,stage["options"][i].value("name",std::string()));once(2.6f+5.2f+i*.3f,"ui_select");}
 sdIntroPrev=t;
}
// V3 마무리(영상 Hs3Y7uyOAQk 194.5~196.6초, 0.15초 간격 캡처) : 칼날이 약점에 맞으면 흰·파란 충돌 빛(t_hr_ef_hit_ok) →
// 판이 어두워지고 초록 원 + 「Cut!」(한국어판 「참격」 t_hr_break_zen_tx) + 초록 원호·사선 → 사라지면 글자 파편 → 반론 컷인
void Yumeno::v4ShowdownBreak(float t){
 auto vis=[&](const char* id,bool v){UI::SetVisible(this,"sdv3",id,v);};auto at=[&](const char* id,float cx,float cy,float w,float h){UI::SetSize(this,"sdv3",id,{std::max(1.f,w),std::max(1.f,h)});UI::SetPosition(this,"sdv3",id,{cx-w*.5f,cy-h*.5f});};auto op=[&](const char* id,float o){UI::SetOpacity(this,"sdv3",id,std::clamp(o,0.f,1.f));};
 auto ramp=[](float t,float a,float b){return std::clamp((t-a)/(b-a),0.f,1.f);};const float cx=sdBreakC[0],cy=sdBreakC[1]; /* 약점 글자 자리 */
 { /* 3160.9초 : 약점 글자가 칼줄기를 따라 두 쪽으로 어긋난다(같은 글자 두 장을 반대로 민다) */
  float a=(sdBreakC[2]+90)*3.14159265f/180,nx=std::cos(a),ny=std::sin(a),d=16*ramp(t,.04f,.16f),o=1-ramp(t,1.5f,1.8f),f=ramp(t,.6f,1.8f);int spare=std::max(sdSplitN,24); /* 3161.5~3162.4초 : 참격 뒤 약점 글자가 제자리에서 주황 조각으로 옆으로 퍼지며 떨어진다 */
  for(size_t q=0;q<sdSplit.size();q++){const auto& w=sdSplit[q];for(int h=0;h<2;h++){int slot=h?spare+int(q):int(w[0]);if(slot>=48)continue;auto id="P0G"+std::to_string(slot);float sg=h?-1.f:1.f;
   UI::SetVisible(this,"panicv4",id,t<1.8f);UI::SetFont(this,"panicv4",id,"Assets/Fonts/gothica1/GothicA1-Bold.ttf");glyphStyle.erase(id);UI::SetText(this,"panicv4",id,sdSplitCh[q]);float side=sg*(50+30*float(q%3)),sc=1.45f*w[3]*(1-.35f*f);UI::SetPosition(this,"panicv4",id,{w[1]+nx*d*sg+side*f,w[2]+ny*d*sg+560*f*f-40*f});UI::SetScale(this,"panicv4",id,{sc,sc});UI::SetRotation(this,"panicv4",id,w[4]+sg*240*f);UI::SetColor(this,"panicv4",id,(h&&t<.6f)?Color{1,1,1,1}:Color{1,.6f,.15f,1});UI::SetOpacity(this,"panicv4",id,o*(h&&t<.6f?.8f:1.f));glyphCache.erase(id);}}}
 {bool on=t<.2f;vis("SdV3Streak",on);if(on){float u=std::clamp(t/.08f,0.f,1.f);at("SdV3Streak",cx,cy,30+60*u,1700);UI::SetRotation(this,"sdv3","SdV3Streak",sdBreakC[2]+90);UI::SetColor(this,"sdv3","SdV3Streak",Color{1,1,1,1});op("SdV3Streak",1-ramp(t,.12f,.2f));}} /* 3160.8~3160.9초 : 흰 칼줄기가 약점을 가른다 */
 {bool on=sdBreakV&&t>=.12f&&t<.75f;vis("SdV3VMark",on);if(on){float s=1.4f-.4f*std::clamp((t-.12f)/.1f,0.f,1.f);at("SdV3VMark",860,150,200*s,300*s);op("SdV3VMark",1-ramp(t,.55f,.75f));}} /* 한국어판 3161.2초 : V 포인트를 베면 주황 「V」(t_ef_ronpa_hit_tx_vpoint) */
 for(auto id:{"SdV3Arc","SdV3Pointer","SdV3Flower","SdV3Band","SdV3SlashN","SdV3SlashT","SdV3Adv"})vis(id,false);
 {bool on=t<.22f;vis("SdV3BrkHit",on);float u=ramp(t,0,.22f);at("SdV3BrkHit",cx,cy,300+500*u,300+500*u);op("SdV3BrkHit",1-u);}
 vis("SdV3BrkDim",true);at("SdV3BrkDim",640,360,1280,720);op("SdV3BrkDim",.6f*ramp(t,.1f,.18f)*(1-ramp(t,.75f,.85f)));
 {bool on=t>=.15f&&t<.75f;float s=1.3f-.3f*ramp(t,.15f,.25f),o=1-ramp(t,.55f,.75f);vis("SdV3BrkCircle",on);vis("SdV3BrkTx",on);at("SdV3BrkCircle",cx,cy,520*s,520*s);op("SdV3BrkCircle",o);float ts=1.4f-.4f*ramp(t,.15f,.24f);at("SdV3BrkTx",cx,cy,520*ts,520*ts);op("SdV3BrkTx",o);}
 {bool on=t>=.15f&&t<.5f;vis("SdV3BrkSlash",on);at("SdV3BrkSlash",cx,cy,560,560);op("SdV3BrkSlash",1-ramp(t,.35f,.5f));}
 {bool on=t>=.2f&&t<.85f;vis("SdV3BrkLine",on);float w=1600*ramp(t,.2f,.3f);at("SdV3BrkLine",cx,cy,w,100);UI::SetRotation(this,"sdv3","SdV3BrkLine",-55);op("SdV3BrkLine",1-ramp(t,.7f,.85f));}
}
// V3(LP 2장 반론 쇼다운 #1, lparchive Update 60) : 상대 발언은 낱말마다 크기가 다르고 세로·가로 낱말이 화면 대각선을 따라 날아든다
// 「the side / of the / tank / being / open…」「I know / she / didn't / do that!」. 칼은 화면 가운데를 지나는 각도 선으로 벤다(Codex RE 3f24f0 angle cursor)
// 한국어 낱말 끝의 조사·어미 글자 수(한국어판 쇼다운은 뜻 낱말 크게, 조사 작게)
int Yumeno::sdTail(const std::vector<std::string>& g)const{static const std::vector<std::string> two{"에서","에게","으로","까지","부터","처럼","보다","이다","라고","하고","이라","한테","마저","조차"},one{"은","는","이","가","을","를","에","엔","의","도","로","와","과","만","고","서","며","면","나","요","야","지","게","죠","네"};
 int m=int(g.size());if(m>=3){auto s=g[m-2]+g[m-1];for(auto& x:two)if(s==x)return 2;}if(m>=2)for(auto& x:one)if(g[m-1]==x)return 1;return 0;}
std::vector<showdownv4::Glyph> Yumeno::v4ShowdownGlyphs()const{
 std::vector<showdownv4::Glyph> out;sdLook.clear();auto* current=showdownV4.current();if(showdownV4.phase!=showdownv4::Phase::Active||!current)return out;
 const auto& row=stage["showdownV4"]["statements"].at(current->id);auto text=row.value("text",std::string());auto chars=debate::glyphs(text);auto target=row.value("bladeTarget",Json::object());int first=target.value("start",0),count=u8len(target.value("word",std::string()));
 std::string font="Assets/Fonts/gothica1/GothicA1-Bold.ttf";int n=std::min(48,int(chars.size())); /* 한국어판 3097초 : 쇼다운 발언은 굵은 고딕 하나(v4-gpu-showdown-assets.mjs 가 굽는다) */
 std::vector<int> word(n);int nw=0;{int w=0;for(int i=0;i<n;i++){word[i]=w;if(chars[i]==" ")++w;}nw=w+1;}
 unsigned hv=2166136261u;for(unsigned char c:text){hv^=c;hv*=16777619u;}
 float progress=std::clamp(showdownV4.entryTime/current->durationFrames,0.f,1.f);
 // V3 실측(영상 Hs3Y7uyOAQk 155~194초) : 구절마다 줄을 바꿔 계단처럼 쌓은 굵은 글(「Even if we rule out / the hidden door...」)이
 // 상대 쪽 왼끝에서 나와 칸막이 너머 주인공 쪽으로 오른쪽으로 흐른다. 약점 낱말은 크게. 가끔 구절 전체가 세로로 기운다(194초 「and we'd be none the wiser.」)
 struct Word{std::vector<int> idx;bool weak=false;float size=1,step=0,total=0;std::vector<float> at,gs;int order=0;};std::vector<Word> words;
 // 한국어판(Uba6XjXj8OU 3097~3110초) : 「숨겨진 문 안이」「도서관엔」「범인은」「카메라가」— 뜻 낱말은 크고 조사·어미는 작게 붙는다
 auto tail=[&](const std::vector<int>& idx){static const std::vector<std::string> two{"에서","에게","으로","까지","부터","처럼","보다","이다","라고","하고","이라","한테","마저","조차"},one{"은","는","이","가","을","를","에","엔","의","도","로","와","과","만","고","서","며","면","나","요","야","지","게","죠","네"};
  int m=int(idx.size());if(m>=3){auto s=chars[idx[m-2]]+chars[idx[m-1]];for(auto& x:two)if(s==x)return 2;}if(m>=2)for(auto& x:one)if(chars[idx[m-1]]==x)return 1;return 0;};
 for(int k=0;k<nw;k++){Word w;for(int i=0;i<n;i++)if(word[i]==k&&chars[i]!=" ")w.idx.push_back(i);if(w.idx.empty())continue;
  for(int i:w.idx)w.weak=w.weak||(current->blade&&i>=first&&i<first+count);
  w.size=(w.weak?1.9f:1.55f)*1.1f; /* 한국어판 : 뜻 낱말 높이 ≈ 화면 9% */w.step=36*1.45f*w.size;int tl=tail(w.idx);w.order=int(words.size());
  for(size_t j=0;j<w.idx.size();j++){float s=int(j)>=int(w.idx.size())-tl?.5f:1.f,a=debate::em(chars[w.idx[j]],font)*w.step*s;w.gs.push_back(s);w.at.push_back(w.total+a*.5f);w.total+=a;}words.push_back(w);}
 struct Line{std::vector<int> words;float width=0,height=0,x=0,y=0,rot=0;};std::vector<Line> lines;{int cnt=0; /* 덩어리는 많아도 4줄까지 — 줄이 화면 아래로 밀려 약점 글자가 안 보이면 벨 수 없다 */for(int k=0;k<int(words.size());k++){int c=int(words[k].idx.size());if(lines.empty()||(cnt+c>std::max(7,(n+3)/4)&&!lines.back().words.empty())){lines.push_back({});cnt=0;}auto& l=lines.back();if(!l.words.empty())l.width+=18;l.width+=words[k].total;l.height=std::max(l.height,words[k].step);l.words.push_back(k);cnt+=c;}}
 bool tilt=nw>2&&(hv%8u)==0u; /* 주인님 지시 : 글자 모양은 1장(영상) 그대로 — 장마다 바꾸지 않는다 */ /* 세로로 기운 구절 */float W=0,H=0;
 {int nl=int(lines.size());float gap=nl>1?std::min(std::clamp(420.f/(nl-1),120.f,260.f),380.f/(nl-1)):0; /* 덩어리 전체가 STATUS 밑~시간판 위(150~640)에 들어오게 */ /* 3100.6·3106.9초 : 구절 덩어리는 위·가운데·아래로 130~270px 떨어져 놓이고 */
  for(size_t k=0;k<lines.size();k++){auto& l=lines[k];l.x=k*70.f+float(int(hv>>(k*2%20)&3u))*30;l.y=k*gap+l.height*.5f;H=l.y+l.height*.5f;W=std::max(W,l.x+l.width);l.rot=tilt?-68.f:(float(int(hv>>(k*3%24)&7u))-4.f);}} /* 줄마다 오른쪽으로 비켜 선다 */
 float boundary=std::clamp(640+(50-showdownV4.gauge)*5,200.f,1080.f);
 float ox=-W*.35f+progress*(boundary+340)+float(int(hv>>9&3u))*20, /* 주인님 지시·Hs3Y7uyOAQk 155~161초 : 왼쪽 밖에서 나와 멈추지 않고 칸막이를 넘어 주인공 쪽으로 밀려온다 */oy=std::clamp(360-H*.5f+float(int(hv>>5&3u))*40-60,150.f,std::max(150.f,640-H)); /* 오른쪽 위 STATUS 밑으로 */ /* 3098~3099초 : 전체가 초당 약 80px 오른쪽으로 흐른다 */(void)boundary; /* V3(Hs3Y7uyOAQk 155~161초) : 문장은 상대 쪽 왼끝에서 나와 시간 동안 오른쪽(주인공 쪽)으로 흘러간다. 높이는 발언마다 다르다 */ /* 한국어판 3097.3~3098.8초 : 덩어리는 제자리(흐르지 않는다), 상대 쪽에서 칸막이 언저리까지 */(void)boundary;
 float bcx=ox+W*.5f,bcy=oy+H*.5f,tr=tilt?-68*3.14159265f/180:0;int style=int((hv>>12)%8u);bool vert=!tilt&&style==1&&words.size()<=5;float el=progress*current->durationFrames/60,zoom=style==2?std::clamp(el/.3f,0.f,1.f):1.f;zoom=1-std::pow(1-zoom,2); /* 발언마다 들어오는 모양 : 보통(왼쪽에서), 세로 기둥, 크게→작게 */
 for(size_t k=0;k<lines.size();k++){auto& l=lines[k];float enter=std::clamp((progress-k*.05f)/.06f,0.f,1.f),e=1-std::pow(1-enter,3),leave=std::clamp((progress-.93f)/.07f,0.f,1.f);
  float r=l.rot*3.14159265f/180,cur=0;
  for(int wk:l.words){auto& w=words[wk];
   float st=w.order*(.4f/std::max(1,int(words.size()))),we=std::clamp((progress-st)/.035f,0.f,1.f),sl=std::clamp((progress-st)*current->durationFrames/60/.4f,0.f,1.f),slide=-150*std::pow(1-sl,3); /* 한국어판 3105.6~3106.2초 : 낱말이 하나씩 왼쪽에서 150px 미끄러져 들어와 멈춘다 */
   for(size_t j=0;j<w.idx.size();j++){int i=w.idx[j];float lx=ox+l.x+cur+w.at[j]+slide,ly=oy+l.y+(l.height-w.step)*.3f+(1-w.gs[j])*w.step*.22f;
    if(!tilt){float dx=lx-(ox+l.x),dy=ly-(oy+l.y);lx=ox+l.x+dx*std::cos(r)-dy*std::sin(r);ly=oy+l.y+dx*std::sin(r)+dy*std::cos(r);}
    else{float dx=lx-bcx,dy=ly-bcy;lx=bcx+dx*std::cos(tr)-dy*std::sin(tr);ly=bcy+dx*std::sin(tr)+dy*std::cos(tr);}
    if(vert){lx=ox+40+k*170.f;ly=110+float(int(hv>>14&3u))*30+cur+w.at[j]+slide;} /* 3103.5~3104 : 세로 구절 기둥, 위에서 아래로 붙는다 */
    if(zoom<1){float z=1+3.f*(1-zoom);lx=bcx+(lx-bcx)*z;ly=bcy+(ly-bcy)*z;} /* 3127.1~3127.4 : 화면을 덮을 만큼 크게 나타나 0.3초 만에 제 크기로 */
    showdownv4::Glyph g;g.center={lx,ly};g.radius=26*w.size*w.gs[j];g.index=i;g.visible=we>0&&leave<1&&lx>10&&lx<1270&&ly>60&&ly<700&&sdGap<=0&&!(sdCutId==current->id&&sdCut.count(i)); /* 3129.1초 : 칼선이 지난 글자는 깨져 사라지고 나머지만 남는다 */(void)e;
    g.weak=current->blade&&i>=first&&i<first+count;g.vpoint=row.contains("vpoint")&&i==row["vpoint"].value("glyphIndex",-1);out.push_back(g);sdLook.push_back({vert?0.f:l.rot,w.size*w.gs[j]*(zoom<1?1+3.f*(1-zoom):1.f)});}
   cur+=w.total+18;}
 }
 return out;
}
void Yumeno::v4ShowdownDraw(){
 auto gs=v4ShowdownGlyphs();auto* current=showdownV4.current();std::vector<std::string> chars;std::string font="Assets/Fonts/pretendard/Pretendard-Medium.otf";
 if(current){const auto& row=stage["showdownV4"]["statements"].at(current->id);chars=debate::glyphs(row.value("text",std::string()));font="Assets/Fonts/gothica1/GothicA1-Bold.ttf";}
 for(auto& d:sdShards)d[5]+=1.f/60;for(size_t s=sdShards.size();s-->0;)if(sdShards[s][5]>.28f){sdShards.erase(sdShards.begin()+s);sdShardCh.erase(sdShardCh.begin()+s);}if(sdGap>0)sdGap-=1.f/60;
 for(int i=0;i<48;i++){auto id="P0G"+std::to_string(i);auto& c=glyphCache[id];
  {int sh=-1;for(size_t s=0;s<sdShards.size();s++)if(int(sdShards[s][0])==i)sh=int(s); /* 깨진 글자 : 튀어 나가며 돌고 옅어진다 */
   if(sh>=0){const auto& d=sdShards[sh];float t=d[5],u=t/.28f;float x=d[1]+d[3]*1.6f*t,y=d[2]+d[4]*1.6f*t+600*t*t,rot=d[7]+(i&1?1:-1)*540*u,sc=1.45f*d[6]*(1-.65f*u); /* 3099.3초 : 잘게 깨져 빠르게 튄다 */
    if(!c.visible){UI::SetVisible(this,"panicv4",id,true);c.visible=1;}if(c.text!=sdShardCh[sh]){UI::SetText(this,"panicv4",id,sdShardCh[sh]);c.text=sdShardCh[sh];}UI::SetColor(this,"panicv4",id,Color{1,1,1,1});glyphStyle[id].r=glyphStyle[id].g=glyphStyle[id].b=1;
    UI::SetPosition(this,"panicv4",id,{x,y});c.x=x;c.y=y;UI::SetRotation(this,"panicv4",id,rot);c.rotation=rot;UI::SetScale(this,"panicv4",id,{sc,sc});c.s=-1;UI::SetOpacity(this,"panicv4",id,1-u);c.opacity=1-u;continue;}}
  bool on=i<int(gs.size())&&gs[i].visible;float lookRot=i<int(sdLook.size())?sdLook[i][0]:-14,lookScale=i<int(sdLook.size())?sdLook[i][1]:1;if(!on){if(c.visible){UI::SetVisible(this,"panicv4",id,false);c.visible=0;}continue;}const auto& g=gs[i];auto& st=glyphStyle[id];Color color=g.weak?Color{1,.6f,.15f,1}:Color{1,1,1,1};
  if(st.font!=font){UI::SetFont(this,"panicv4",id,font);st.font=font;}if(st.r!=color.r||st.g!=color.g||st.b!=color.b){UI::SetColor(this,"panicv4",id,color);st.r=color.r;st.g=color.g;st.b=color.b;}if(!c.visible){UI::SetVisible(this,"panicv4",id,true);c.visible=1;}{const auto& ch=chars[g.index];if(c.text!=ch){UI::SetText(this,"panicv4",id,ch);c.text=ch;}}if(std::abs(c.s-lookScale)>.01f){UI::SetScale(this,"panicv4",id,{1.45f*lookScale,1.45f*lookScale});c.s=lookScale;}if(std::abs(c.x-g.center.x)>.6f||std::abs(c.y-g.center.y)>.6f){UI::SetPosition(this,"panicv4",id,{g.center.x,g.center.y});c.x=g.center.x;c.y=g.center.y;}if(c.rotation!=lookRot){UI::SetRotation(this,"panicv4",id,lookRot);c.rotation=lookRot;}if(c.opacity!=1){UI::SetOpacity(this,"panicv4",id,1);c.opacity=1;}
 }
 UI::SetTexture(this,"stage","Slash",sdAlert?"Assets/Art/ui/showdown_line_blade.svg":"Assets/Art/ui/showdown_line.svg");UI::SetPosition(this,"stage","Slash",{640,370}); /* 노드 위치는 가운데 기준 */UI::SetSize(this,"stage","Slash",{1700,36});UI::SetRotation(this,"stage","Slash",showdownV4.angle); /* V3 : 화면 가운데를 지나는 점선 + 노란 칼 표시가 각도로만 돈다 */
 float boundary=std::clamp(640+(50-showdownV4.gauge)*5,200.f,1080.f);
 if(sdIntro<0){ // V3 칼 커서(t_hr_zan_pointer) : 가운데 둘레 원호 위 노란 칼 아이콘이 각도로 돈다. 형세 띠(t_hr_line) : 밀리면 칸막이 옆 「DANGER」, 앞서면 「ADVANTAGE」
  float a=showdownV4.angle*3.14159265f/180,R=560; /* V3 영상(Hs3Y7uyOAQk 194초) 실측 : 커서 원은 화면 가운데 반지름 ≈560 */UI::SetVisible(this,"sdv3","SdV3Arc",false); /* 주인님 지시 : 파란 둥근 선은 뺀다 */UI::SetRotation(this,"sdv3","SdV3Arc",showdownV4.angle);
  UI::SetVisible(this,"sdv3","SdV3Flower",true);UI::SetPosition(this,"sdv3","SdV3Flower",{640+(R+40)*std::cos(a)-48,370+(R+40)*std::sin(a)-48});UI::SetVisible(this,"sdv3","SdV3Pointer",true); /* 한국어판 3097.6초 : 오른쪽 끝 파란 꽃 + 주황 칼 */UI::SetPosition(this,"sdv3","SdV3Pointer",{640+R*std::cos(a)-78,370+R*std::sin(a)-24});UI::SetRotation(this,"sdv3","SdV3Pointer",showdownV4.angle);
  bool danger=showdownV4.gauge<45,adv=showdownV4.gauge>55;UI::SetVisible(this,"sdv3","SdV3Band",danger||adv);
  if(danger||adv){UI::SetTexture(this,"sdv3","SdV3Band",danger?"Assets/Art/ui/v3_hr/band_danger.webp":"Assets/Art/ui/v3_hr/band_advantage.webp");UI::SetPosition(this,"sdv3","SdV3Band",{danger?boundary+22:4.f,0});UI::SetSize(this,"sdv3","SdV3Band",{40,720});}
  if(sdAdvT>0&&(sdAdvT-=1.f/60)<=0){UI::SetVisible(this,"sdv3","SdV3Adv",false);UI::SetVisible(this,"sdv3","SdV3AdvLine",false);}
  { // V3 영상 192초 : 칼날을 바꾸면 왼쪽 위에 칼 판 목록이 세로로 서고 고른 것만 밝다
   bool pick=sdPick>0&&(sdPick-=1.f/60)>0;int n=std::min(6,int(bladeIds.size()));
   for(int i=0;i<6;i++){auto k="SdV3Kata"+std::to_string(i),tn="SdV3KataT"+std::to_string(i);bool on=pick&&i<n;UI::SetVisible(this,"sdv3",k,on);UI::SetVisible(this,"sdv3",tn,on);if(!on)continue;float x=14+i*8.f,y=104+i*60.f;
    UI::SetTexture(this,"sdv3",k,i==sdBullet?"Assets/Art/ui/v3_hr/katana_sheathed.webp":"Assets/Art/ui/v3_hr/katana_sheathed_off.webp");UI::SetPosition(this,"sdv3",k,{x,y+10});UI::SetSize(this,"sdv3",k,{430,64});UI::SetOpacity(this,"sdv3",k,1);UI::SetPosition(this,"sdv3",tn,{x+30,y+27});UI::SetSize(this,"sdv3",tn,{220,26});UI::SetOpacity(this,"sdv3",tn,i==sdBullet?1.f:.6f);UI::SetText(this,"sdv3",tn,stage["options"][i].value("name",std::string()));}
  }
  {bool found=false;showdownv4::Point c{};if(sdAlert)for(const auto& g:gs)if(g.visible&&g.weak){c=g.center;found=true;break;} /* 3159.8초 : 칼을 뽑으면 약점 첫 글자에 붉은 X */
  for(int i=0;i<2;i++){auto id="SdV3X"+std::to_string(i);UI::SetVisible(this,"sdv3",id,found);if(found){UI::SetTexture(this,"sdv3",id,"Assets/Art/ui/v3_hr/red.webp");UI::SetSize(this,"sdv3",id,{5,980});UI::SetPosition(this,"sdv3",id,{c.x-2.5f,c.y-490});UI::SetRotation(this,"sdv3",id,i?-52.f:52.f);UI::SetOpacity(this,"sdv3",id,.85f); /* 3159.9초 : 약점 글자에서 교차하는 길고 가는 붉은 선 두 줄 */}}}
 if(sdBreak<0){bool h=sdHit[2]>=0&&(sdHit[2]+=1.f/60)<.35f;UI::SetVisible(this,"sdv3","SdV3BrkHit",h&&sdHit[2]<.2f);UI::SetVisible(this,"sdv3","SdV3HitRing",h); /* 3099.1~3099.3초 : 흰·파란 별빛 → 파란 원 */
  if(h){float u=sdHit[2]/.2f,v=sdHit[2]/.35f;UI::SetSize(this,"sdv3","SdV3BrkHit",{200+220*u,200+220*u});UI::SetPosition(this,"sdv3","SdV3BrkHit",{sdHit[0]-100-110*u,sdHit[1]-100-110*u});UI::SetOpacity(this,"sdv3","SdV3BrkHit",std::clamp(1-u,0.f,1.f));
   UI::SetSize(this,"sdv3","SdV3HitRing",{160+900*v,160+900*v});UI::SetPosition(this,"sdv3","SdV3HitRing",{sdHit[0]-80-450*v,sdHit[1]-80-450*v}); /* 3099.2초 : 왼쪽 반을 덮는 큰 원 */UI::SetOpacity(this,"sdv3","SdV3HitRing",std::clamp(1-v,0.f,1.f));}else sdHit[2]=-1;
  if(sdPhaseFlash>0){sdPhaseFlash-=1.f/60;float r=std::clamp(sdPhaseFlash/.45f,0.f,1.f);UI::SetColor(this,"stage","SdLeft",Color{1,1-.75f*r,1-.8f*r,1});UI::SetOpacity(this,"stage","SdLeft",.2f+.6f*r);}
  if(sdFlash>0){sdFlash-=1.f/60;UI::SetOpacity(this,"stage","SdRight",.2f+.45f*std::max(0.f,sdFlash)/.2f);} /* 3099.3초 : 오른쪽 화면이 번쩍 */}
 if(sdBreak<0){bool on=sdCutFx>0&&(sdCutFx-=1.f/60)>0;UI::SetVisible(this,"sdv3","SdV3Streak",on);if(on){float u=1-sdCutFx/.14f;UI::SetTexture(this,"sdv3","SdV3Streak","Assets/Art/ui/v3_hr/st_line.webp");UI::SetSize(this,"sdv3","SdV3Streak",{14+10*u,1800});UI::SetPosition(this,"sdv3","SdV3Streak",{640-7-5*u,370-900});UI::SetRotation(this,"sdv3","SdV3Streak",sdCutAng+90);UI::SetOpacity(this,"sdv3","SdV3Streak",1-u);}}
 bool sl=sdSlashT>0&&(sdSlashT-=1.f/60)>0;UI::SetVisible(this,"sdv3","SdV3SlashN",sl);UI::SetVisible(this,"sdv3","SdV3SlashT",sl);if(sl){float u=1-sdSlashT/.8f,sc=1+.25f*(1-std::min(1.f,u*5));UI::SetPosition(this,"sdv3","SdV3SlashN",{1095,180}); /* 한국어판 3126.8초 : 오른쪽 위 STATUS 아래 */UI::SetSize(this,"sdv3","SdV3SlashN",{std::max(1.f,90*sc),std::max(1.f,128*sc)});UI::SetPosition(this,"sdv3","SdV3SlashT",{1105,300});UI::SetSize(this,"sdv3","SdV3SlashT",{150*sc,77*sc});}
  for(int k=0;k<4;k++){auto& b=sdBonus[k];bool on=b[2]>0&&(b[2]-=1.f/60)>0;auto id="SdV3Bonus"+std::to_string(k);UI::SetVisible(this,"sdv3",id,on);if(on){UI::SetPosition(this,"sdv3",id,{b[0]-40,b[1]-40-40*(.9f-b[2])});UI::SetOpacity(this,"sdv3",id,std::clamp(b[2]/.3f,0.f,1.f));}}
 }
 UI::SetSize(this,"stage","SdLeft",{boundary,720});UI::SetPosition(this,"stage","SdRight",{boundary,0});UI::SetSize(this,"stage","SdRight",{1280-boundary,720});UI::SetPosition(this,"stage","SdDivider",{boundary-20,0});
 int ms=std::max(0,int(showdownV4.remaining*1000/60));char clock[20];std::snprintf(clock,sizeof clock,"%02d:%02d:%03d",ms/60000,ms/1000%60,ms%1000);svis("StageTimer",false);{float x=990;for(int i=0;i<9;i++){auto id="SdV3TimeD"+std::to_string(i);char c=clock[i];bool colon=c==':';UI::SetTexture(this,"sdv3",id,"Assets/Art/ui/v3_hr/time_"+std::to_string(colon?10:c-'0')+".webp");UI::SetPosition(this,"sdv3",id,{x-(colon?12.f:0.f),654});UI::SetSize(this,"sdv3",id,{38,38});UI::SetVisible(this,"sdv3",id,sdIntro<0);x+=colon?14.f:26.f;}UI::SetVisible(this,"sdv3","SdV3TimeBase",sdIntro<0);} /* 한국어판 : V3 시간판 숫자 그림 */
 bool tug=showdownV4.phase==showdownv4::Phase::Tug;svis("StageMsg",tug);if(tug)stext("StageMsg","힘겨루기");
}
bool Yumeno::v4ShowdownUpdate(float delta,bool click,bool released){
 if(!v4TaskActive||stageKind!="showdown"||!stage.contains("showdownV4"))return false;
 using P=showdownv4::Phase;using E=showdownv4::Event;auto& state=showdownV4;const auto& spec=stage["showdownV4"];
 if(debateResultTime>0){updateDebateFx(delta);if(debateResultTime<=0)beginScript();return true;} /* 논파 연출이 끝난 뒤 다음 대본 */
 if(sdBreak>=0){sdBreak+=std::min(delta,.1f);v4ShowdownBreak(sdBreak);if(sdBreak<1.8f)return true;sdBreak=-1; /* 「참격」이 걷히면 글자 파편 + 반론 컷인(debateSuccess) */
  drawPanicLanes(false);for(int i=0;i<48;i++)UI::SetVisible(this,"panicv4","P0G"+std::to_string(i),false);for(auto id:{"SdBladeFrame","BladeName","Slash","StageTimer"})svis(id,false);UI::SetVisible(this,UI_ID,"NamePanel",false);UI::SetVisible(this,UI_ID,"TrialSpeaker",false);UI::Remove(this,"sdv3");debateSuccess("refute");debateResultTime=std::max(0.f,debateResultTime-1.35f);return true;} /* 3162.1초 : 참격 뒤엔 HUD 없음. 3162.5 곧바로 「논파」 컷인 — 논스톱의 가운데 글자 깨기(1.35초)는 건너뛴다 */
 if(state.phase==P::Dialogue){auto rows=spec["groups"][state.group]["entries"][state.entry]["events"];v4TaskQueue(rows,"showdown-dialogue");return true;}
 if(state.phase==P::AdvanceFeedback){auto all=spec["groups"][state.group].value("afterAdvance",Json::array()),rows=Json::array();auto opp=spec.value("opponent",std::string()); /* V3 반론 쇼다운엔 상대와 주인공 둘만 나온다 : 다른 사람 대사는 쇼다운이 끝난 뒤로 */
  for(const auto& r:all){auto a=r.value("actor",std::string());if(a.empty()||a=="mio"||a==opp||r.value("type",std::string("say"))!="say")rows.push_back(r);else sdDeferred.push_back(r);}UI::SetTexture(this,"sdv3","SdV3Adv","Assets/Art/ui/v3_hr/advance_kr.webp");UI::SetPosition(this,"sdv3","SdV3Adv",{525,288});UI::SetSize(this,"sdv3","SdV3Adv",{270,143});UI::SetVisible(this,"sdv3","SdV3Adv",true);UI::SetTexture(this,"sdv3","SdV3AdvLine","Assets/Art/ui/v3_hr/advance_line.webp");UI::SetPosition(this,"sdv3","SdV3AdvLine",{-60,315});UI::SetSize(this,"sdv3","SdV3AdvLine",{1400,90});UI::SetVisible(this,"sdv3","SdV3AdvLine",true);sdAdvT=2.f;UI::SetVisible(this,"sdv3","SdV3Adv",false);UI::SetVisible(this,"sdv3","SdV3AdvLine",false); /* 한국어판 3111.6~3112.4초 : 마지막 베기 충격파·파편(0.4초) → 왼쪽 붉은 번쩍 → 3112.4 「발전!」 */ /* 한국어판 3112.6초 : 가운데 가로 푸른 빛줄 + 작은 「발전!」 */sdCombo=0; /* V3 t_hr_hatten 「Advance!」 */ /* V3 : 형세가 넘어오면 「Advance!」 + 가장자리 「ADVANTAGE!!」 */v4TaskQueue(rows,"showdown-advance");return true;}
 if(state.phase==P::RetreatFeedback){UI::SetTexture(this,"sdv3","SdV3Adv","Assets/Art/ui/v3_hr/retreat_kr.webp");UI::SetPosition(this,"sdv3","SdV3Adv",{510,312});UI::SetSize(this,"sdv3","SdV3Adv",{260,100}); /* 한국어판 t_hr_gyaku_hatten 「역발전!」 */UI::SetVisible(this,"sdv3","SdV3Adv",true);sdAdvT=1.4f;} /* V3 t_hr_gyaku_hatten 「Retreat!」 */
 if(state.phase==P::RepeatFeedback||state.phase==P::RetreatFeedback||state.phase==P::WrongFeedback){state.acknowledge();showdownShown=-1;}
 if(state.phase==P::Failed||state.phase==P::TimedOut){++retries;v4ResetHearts(maxHearts);restartStage=true;return true;}
 if(sdIntro>=2.6f&&!sdPreDone){sdPreDone=true;const auto& pre=Data::Get("Assets/Data/showdown_pre.json");auto id=v4Task.value("taskId",std::string()); /* 한국어판 2959~2975초 : 제목 전에 두 사람 얼굴 2분할 대사(칸막이 무늬 없음) */
  if(pre.contains(id)){for(auto k:{"SdLeft","SdRight","SdDivider"})svis(k,false);v4ShowdownIntro(2.59f);for(auto k:{"SdV3CutDim","SdV3CiBurst"})UI::SetVisible(this,"sdv3",k,false);sdIntro=2.6f;sdIntroPrev=2.59f;v4TaskQueue(pre[id],"showdown-pre");return true;}} /* 제목 장식은 대사가 끝난 뒤 */
 if(sdIntro>=0){sdIntro+=std::min(delta,.2f); /* 로딩 끊김(큰 delta)에 연출이 한 번에 지나가지 않게 */v4ShowdownIntro(sdIntro);if(sdIntro<11.5f)return true;sdIntro=-1; /* 한국어판 영상 : 컷인 2.6초 + 제목·장전 8.9초(3088.6~3097.5) */
  for(auto id:{"SdV3DecoL","SdV3DecoR","SdV3Sakura","SdV3Start0","SdV3Start1","SdV3ListRing","SdV3Line0","SdV3Line1","SdV3CiBurst"})UI::SetVisible(this,"sdv3",id,false);for(int i=0;i<8;i++)UI::SetVisible(this,"sdv3","SdV3Petal"+std::to_string(i),false);for(int i=0;i<6;i++){UI::SetVisible(this,"sdv3","SdV3Kata"+std::to_string(i),false);UI::SetVisible(this,"sdv3","SdV3KataT"+std::to_string(i),false);}for(int i=0;i<7;i++){UI::SetVisible(this,"sdv3","SdV3Title"+std::to_string(i),false);UI::SetVisible(this,"sdv3","SdV3TitleEf"+std::to_string(i),false);}
  for(auto id:{"SdBladeFrame","BladeName","Slash"})svis(id,true);showdownShown=-1;}
 if(state.phase==P::Active){if(sdLastGroup>=0&&state.group!=sdLastGroup)sdPhaseFlash=.45f;sdLastGroup=state.group;sdBy+=delta;} /* 3119.6초 : 새 단계는 왼쪽 끝이 붉게 번쩍 · 3105/3122.4초 : 왼쪽 카메라가 가끔 방청 학생 */
 if(state.phase==P::Tug&&pressed("mouse0"))state.tugPress(); /* V3 RE 3f7e10 : 힘겨루기는 일반 베기 입력(좌클릭) 연타 */
 float axisX=float(Input::IsKeyDown("d"))-float(Input::IsKeyDown("a")),axisY=float(Input::IsKeyDown("s"))-float(Input::IsKeyDown("w"));float arc=90+state.gauge*.9f;
 if(std::abs(aimX-showdownMouseX)+std::abs(aimY-showdownMouseY)>.5f&&std::hypot(aimX-640,aimY-370)>24){float d=std::atan2(aimY-370,aimX-640)*180/3.14159265f;if(d>90)d-=180;if(d<=-90)d+=180;state.angle=d;} /* 커서는 늘 오른쪽 반 원호(같은 선의 반대쪽) — V3 PC : 마우스가 가리키는 쪽으로 칼 커서(가운데를 지나는 선)가 향한다 */
 else state.angle=showdownv4::inputAngle(state.angle,axisX,axisY,0,0,state.angle-arc*.5f,state.angle+arc*.5f,skillOn("swap_limit"));showdownMouseX=aimX;showdownMouseY=aimY;
 if(pressed("e")||pressed("mouse2")){sdBullet=(sdBullet+1)%std::max(1,int(bladeIds.size()));bladeList();sfx("v3se_302");sdPick=1.4f;}if(pressed("q")){sdBullet=(sdBullet+int(bladeIds.size())-1)%std::max(1,int(bladeIds.size()));bladeList();sfx("v3se_302");sdPick=1.4f;} /* V3 PC : 가운데 클릭 = 칼날 바꾸기(StrategyWiki) */
 auto* current=state.current();if(current&&state.currentIndex()!=showdownShown){showdownShown=state.currentIndex();const auto& row=spec["statements"].at(current->id);stext("SpkName","");svis("SpkName",false);{auto who=row.value("actor",spec.value("opponent",std::string()));if(!who.empty())who[0]=char(std::toupper((unsigned char)who[0]));std::string spaced;for(char c:who){if(!spaced.empty())spaced+="  ";spaced+=c;} /* 한국어판 3105.6초 : 이름 띠는 로마자 「H o s h i」 */
   UI::SetVisible(this,UI_ID,"NamePanel",true);UI::SetVisible(this,UI_ID,"TrialSpeaker",true);UI::SetPosition(this,UI_ID,"NamePanel",{14,10});UI::SetSize(this,UI_ID,"NamePanel",{360,84});UI::SetPosition(this,UI_ID,"TrialSpeaker",{44,18});UI::SetFont(this,UI_ID,"TrialSpeaker","Assets/Fonts/gothica1/GothicA1-Light.ttf");UI::SetFontSize(this,UI_ID,"TrialSpeaker",22); /* V3 : 얇고 넓은 자간 */text("TrialSpeaker",spaced);
   int total=0,at=0;for(const auto& e:spec["groups"][state.group]["entries"])if(e.value("type",std::string())!="dialogue"){if(e.value("statementIndex",-1)==state.currentIndex())at=total;++total;}total=std::clamp(total,1,14);at=std::clamp(at,0,total-1);UI::SetTexture(this,UI_ID,"NamePanel","Assets/Art/ui/hud_name_dots/n"+std::to_string(total)+"_"+std::to_string(at)+".svg");} /* V3 : 왼쪽 위 이름 탭 + 발언 순서 점 */auto pose=row.value("pose",row.value("actor",std::string()));int seat=court::seatOf(row.value("actor",spec.value("opponent",std::string())));if(seat>=0)courtPose(seat,pose);}
 // V3 PC : 우클릭 = 진실의 칼날 발사(StrategyWiki 「Fire blade」, RE 3c4b70 은 일반 베기 3c4c10 과 다른 입력). 칼을 뽑는 동안(.32초) 화면이 초록 ALERT, 그 뒤 지금 각도로 내리친다
 if(pressed("mouse1")&&sdDraw<0&&!bladeIds.empty()&&state.phase==P::Active){sdDraw=0;sfx("v3se_302");}
 bool strike=false;if(sdDraw>=0){sdDraw+=delta;UI::SetTexture(this,"stage","SdBladeFrame",sdDraw<.16f?"Assets/Art/ui/v3_hr/hud_katana_drawn_glow.webp":"Assets/Art/ui/v3_hr/hud_katana_drawn.webp"); /* V3 : 칼집에서 칼날이 빛나며 나온다(kotodama_toushin ef→on) */
  if(click&&sdDraw>.1f){strike=true;click=false; /* 한국어판 3158.7~3160.8초 : 우클릭으로 뽑은 채 겨누다가 좌클릭으로 내리친다 */sdDraw=-1;UI::SetTexture(this,"stage","SdBladeFrame","Assets/Art/ui/v3_hr/hud_katana_sheathed.webp");}}
 {bool alert=sdDraw>=0&&state.phase==P::Active;
  if(alert!=sdAlert){sdAlert=alert;Color c=alert?Color{.35f,1,.55f,1}:Color{1,1,1,1};UI::SetColor(this,"stage","SdLeft",c);UI::SetColor(this,"stage","SdRight",c);UI::SetOpacity(this,"stage","SdLeft",alert?.5f:.2f);UI::SetOpacity(this,"stage","SdRight",alert?.5f:.2f);UI::SetVisible(this,"sdv3","SdV3Dim",alert);for(int z=0;z<10;z++){auto id="SdV3Zen"+std::to_string(z);UI::SetVisible(this,"sdv3",id,alert);if(alert){UI::SetFont(this,"sdv3",id,"Assets/Fonts/gothica1/GothicA1-Bold.ttf");UI::SetText(this,"sdv3",id,"정신집중");UI::SetPosition(this,"sdv3",id,{float(z%2*380+(z/2%2)*190-120),float(z/2*150-10)});UI::SetOpacity(this,"sdv3",id,.22f);}}if(alert)sdPick=0; /* 칼 뽑은 동안 칼날 목록 없음 */
  if(alert){UI::SetPosition(this,"sdv3","SdV3Dim",{0,0});UI::SetSize(this,"sdv3","SdV3Dim",{1280,720});UI::SetTexture(this,"sdv3","SdV3Dim","Assets/Art/ui/v3_hr/teal.webp");UI::SetOpacity(this,"sdv3","SdV3Dim",.45f);} /* 3158.7초 : 화면 전체 청록 */ /* V3 194.5초 : 칼을 뽑으면 화면 전체가 초록으로 물든다 */if(alert)sfx("v3se_302");}}
 if(click||strike)state.beginStroke();
 if((click||strike)&&state.strokeActive&&current){auto glyphs=v4ShowdownGlyphs();auto segment=showdownv4::angleSegment({640,370},state.angle,1400); /* V3 : 누르면 가운데를 지나는 각도 선 전체로 벤다(드래그 아님) */E event=E::Air;int hp=state.hp;
  if(strike&&!bladeIds.empty()){event=state.blade(current->id,bladeIds[sdBullet],spec.value("answerEvidenceId",std::string()),segment.first,segment.second,glyphs);state.strokeActive=false;}else event=state.resolveStroke(current->id,segment.first,segment.second,glyphs);
  if(event==E::CorrectBlade){if(state.lastVPoint)++vBreaks;sdAlert=false;UI::SetColor(this,"stage","SdLeft",Color{1,1,1,1});UI::SetColor(this,"stage","SdRight",Color{1,1,1,1});UI::SetTexture(this,"stage","SdFace","Assets/Art/sprites/mio/mio_T01.webp");sfx("v3se_376"); /* V3 Hanron_Finish */ {float sx=0,sy=0;int k=0;sdSplit.clear();sdSplitCh.clear();{const auto& srow=spec["statements"].at(current->id);auto sch=debate::glyphs(srow.value("text",std::string()));for(size_t q=0;q<glyphs.size();q++){const auto& g=glyphs[q];if(g.visible&&g.weak)sdSplit.push_back({float(q),g.center.x,g.center.y,q<sdLook.size()?sdLook[q][1]:1.f,q<sdLook.size()?sdLook[q][0]:0.f});if(g.visible&&g.weak)sdSplitCh.push_back(g.index<int(sch.size())?sch[g.index]:std::string());}sdSplitN=int(glyphs.size());}
  for(const auto& g:glyphs)if(g.visible&&g.weak){sx+=g.center.x;sy+=g.center.y;++k;}sdBreakC=k?std::array<float,3>{sx/k,sy/k,state.angle}:std::array<float,3>{520,400,state.angle};}UI::SetVisible(this,"sdv3","SdV3Dim",false);sdBreak=0;sdBreakV=state.lastVPoint;v4ShowdownBreak(0);return true;} /* 베고 나서 논스톱과 같은 논파 컷인·파괴(추정 : V3 쇼다운 마무리도 論破 컷인) */
  if(event==E::WrongBlade){if(skillOn("showdown_guard")&&!sdGuardUsed){sdGuardUsed=true;state.hp=hp;}debate.hearts=(state.hp+1999)/2000;sfx("v3se_311");v4TaskWrong();return true;}
  if(event==E::PartialCut&&!current->blade){bool left=false;for(const auto& g:glyphs)if(g.visible&&!g.weak&&!showdownv4::intersects(segment.first,segment.second,g.center,g.radius)&&!(sdCutId==current->id&&sdCut.count(g.index)))left=true;if(!left)event=state.completeStatement();}
  if(event==E::StatementCut||event==E::PartialCut){sdCutFx=.14f;sdCutAng=state.angle; /* 3099.0초 : 칼선 자리에 흰 섬광 선(남의 연출 효과는 쓰지 않는다) */
   { /* 한국어판 3099.0~3099.8·3129~3130초 : 칼선이 지난 글자마다 흰 파편으로 깨진다. 발언을 다 베면 남은 글자도 깨지고 0.35초 뒤 다음 발언 */
    const auto& srow=spec["statements"].at(current->id);auto sch=debate::glyphs(srow.value("text",std::string()));if(sdCutId!=current->id){sdCutId=current->id;sdCut.clear();}
    bool first=true;for(size_t k=0;k<glyphs.size();k++){const auto& g=glyphs[k];if(!g.visible)continue;bool hit=showdownv4::intersects(segment.first,segment.second,g.center,g.radius);if(!hit&&event!=E::StatementCut)continue;if(g.weak&&event!=E::StatementCut)continue;
     sdCut.insert(g.index);float a=float((g.index*73)%360)*3.14159265f/180;sdShards.push_back({float(k),g.center.x,g.center.y,std::cos(a)*260,std::sin(a)*200-120,0,k<sdLook.size()?sdLook[k][1]:1.f,k<sdLook.size()?sdLook[k][0]:0.f});sdShardCh.push_back(g.index<int(sch.size())?sch[g.index]:std::string());
     if(hit&&first){first=false;sdHit={g.center.x,g.center.y,0};}}
    if(event==E::StatementCut)sdGap=.35f;sdFlash=.2f;}++sdCombo;if(sdCombo>=2){UI::SetTexture(this,"sdv3","SdV3SlashN","Assets/Art/ui/v3_hr/slash_"+std::to_string(std::min(9,sdCombo))+".webp");sdSlashT=.8f;}
   state.remaining+=12; /* 한국어판 3126.8초 : 벨 때마다 「+0.2 sec.」 */for(const auto& g:glyphs)if(g.visible&&showdownv4::intersects(segment.first,segment.second,g.center,g.radius)){int k=sdBonusAt++%4;sdBonus[k]={g.center.x,g.center.y,.9f};UI::SetText(this,"sdv3","SdV3Bonus"+std::to_string(k),"+0.2 sec.");break;}} /* V3 t_hr_slash 숫자 + SLASH */ /* V3 「4 SLASH」 연속 베기 */
  else if(event==E::Air){sfx("v3se_315");sdCombo=0;} // V3 Hanron_Miss
 }
 if(state.phase==P::Active&&skillFocusTick(Input::IsKeyDown("Shift"),delta))delta*=.35f;
 // V3 3f7e10 힘겨루기(Hanron_Tsuba) : 시작 SE318 + 반복 SE378, 끝나면 멈춘다
 {bool tug=state.phase==P::Tug;if(tug!=tugSeOn){tugSeOn=tug;if(tug){sfx("v3se_318");if(hasAudio("v3se_378"))tugSe=Audio::Play(art["audio"]["v3se_378"].get<std::string>(),1.f,1.f,"sfx");}else if(!tugSe.empty()){Audio::Stop(tugSe);tugSe.clear();}}}
 int beforeTickHp=state.hp;showdownTicks+=delta*60;int frames=int(showdownTicks);showdownTicks-=frames;for(int n=0;n<frames;n++){auto e=state.tick();if(e!=E::None)break;}if(state.hp<beforeTickHp)sfx("v3se_316");
 debate.hearts=std::max(1,(state.hp+1999)/2000);v4ShowdownDraw();return true;
}
hb::Json Yumeno::v4ShowdownAuto()const{
 using P=showdownv4::Phase;if(showdownV4.phase==P::Tug)return {{"kind","rapid-key"},{"key","mouse0"}};auto* current=showdownV4.current();if(!current||showdownV4.phase!=P::Active||current->decoy)return {{"kind","wait"}}; /* 가짜 약점은 베지 않고 흘려보낸다 */
 auto answer=stage["showdownV4"].value("answerEvidenceId",std::string());if(current->blade&&!bladeIds.empty()&&bladeIds[sdBullet]!=answer){int n=int(bladeIds.size()),at=int(std::find(bladeIds.begin(),bladeIds.end(),answer)-bladeIds.begin());int forward=(at-sdBullet+n)%n;return {{"kind","key"},{"key",at<n&&forward>n/2?"q":"e"}};} /* 가까운 쪽으로 돌린다 */
 for(const auto& g:v4ShowdownGlyphs())if(g.visible&&(current->blade?g.weak:!g.weak)&&std::hypot(g.center.x-640,g.center.y-370)>40)return {{"kind","sd-slash"},{"blade",current->blade},{"x",g.center.x},{"y",g.center.y},{"keys",""}}; /* 마우스로 글자를 겨눠 벤다 */
 return {{"kind","wait"}};
}
