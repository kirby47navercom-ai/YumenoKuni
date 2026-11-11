// 논의 스크럼 V3 연출(Claude 2026-11-06, 사양서 27a). 근거 : 주인님 제공 한국어판 영상 HWGF48cBGF0(1장)·AfE70Sp86AQ(2장)·pl_2nfpKd68(4장)·DfHXouauWJU(5장).
// UI id "scv3"(Assets/UI/ScrumV3.hbwidget.json, tools/claude_scrum_nodes.py), 그림 Assets/Art/ui/v3_scrum(tools/v3_scrum_assets.py).
namespace scv3 {
inline float ease(float u){u=std::clamp(u,0.f,1.f);return u*u*(3-2*u);}
inline const char* NODES[]{"ScDim","ScLock","ScLockBg","ScLockPre","ScOp0","ScOp1","ScOp2","ScOp3","ScHibi0","ScHibi1","ScHibi2","ScHibi3","ScTopicBand","ScTopic","ScArrowL","ScArrowTailL","ScArrowTL","ScArrowR","ScArrowTailR","ScArrowTR","ScEmblem","ScEmblemDecoL","ScEmblemDecoR","ScEmblemFrame","ScEmblemT","ScStartEf","ScStart","ScStartLine","ScTimeBase","ScTimeIco","ScHit","ScCheckBg","ScCheck","ScMattaBg","ScMattaEf","ScMattaPl0","ScMattaPl1","ScMattaPl2","ScMattaPl3","ScMattaChara","ScMattaTxEf","ScMattaTx","ScPushPl","ScCrouch","ScBind","ScSetEf","ScSet","ScBtnEf","ScBtnRing","ScBtn","ScPushTx","ScJet"};
}
void Yumeno::scv3Box(const std::string& id,float cx,float cy,float w,float h,float op,float rot){if(!UI::Mounted("scv3"))return;bool on=op>.001f;UI::SetVisible(this,"scv3",id,on);if(!on)return;UI::SetPosition(this,"scv3",id,{cx-w/2,cy-h/2});UI::SetSize(this,"scv3",id,{w,h});UI::SetOpacity(this,"scv3",id,std::min(1.f,op));UI::SetRotation(this,"scv3",id,rot);}
void Yumeno::scv3HideAll(){scv3Speaker("",true);if(!UI::Mounted("scv3"))return;for(auto id:scv3::NODES)UI::SetVisible(this,"scv3",id,false);for(int i=0;i<9;i++)UI::SetVisible(this,"scv3","ScTimeD"+std::to_string(i),false);for(int i=0;i<6;i++)UI::SetVisible(this,"scv3","ScPushLine"+std::to_string(i),false);}
const Json& Yumeno::scv3Task()const{
 if(stage.contains("scrumPresentation"))return stage.at("scrumPresentation");
 static const Json none=Json::object(),all=Data::Get("Assets/Data/scrum_v3.json");
 std::string id=v4Task.is_object()?v4Task.value("taskId",std::string()):std::string();
 if(id.empty()&&stage.is_object())id=stage.value("id",std::string());
 return all.contains(id)?all[id]:none;
}
// 1. 「의견대립」(영상 1번 4.25~7.6초) : 검은 화면 → 왕좌 정면이 밝아짐 → 의·견(1.0초)·대(1.25)·립(1.5) 세로로 박힘 → 번개 금(2.0) → 글자가 흩어짐(2.75~3.2)
bool Yumeno::scv3OpIntro(float t){
 {Vec3 hp{0,4.6f,-(court::RADIUS+2.4f)};if(auto* h=actor("Host"))hp=Scene::GetPosition(h);setCam({hp.x,hp.y-.35f,hp.z+2.3f,0,4,0});} /* 영상 4.5~7.5초 : 왕좌만 정면으로(참가자 없이, 왕좌 바로 앞에서) */
 for(auto id:{"StatusPanel","StatusLabel"})UI::SetVisible(this,UI_ID,id,false);for(int i=0;i<10;i++)UI::SetVisible(this,UI_ID,"Star"+std::to_string(i),false);
 {static const char* hud[]{"ScVStatementP","ScVStatement","ScVClaimInk","StageTimer"};for(auto id:hud)svis(id,false);for(int k=0;k<10;k++)for(auto sd:{"L","R"})for(auto part:{"P","F","T"})svis(std::string("ScV")+sd+part+std::to_string(k),false);UI::SetVisible(this,"trialvitalsv4","root",false);UI::SetVisible(this,"scv3cut","ScClaim",false);}
 float dark=t<.25f?1.f:t<.9f?1-(t-.25f)/.65f:t>3.15f?std::min(1.f,(t-3.15f)/.25f):0.f;scv3Box("ScDim",640,360,1280,720,dark);
 struct Tile{float at,cx,cy,s;};static const Tile tiles[4]{{1.f,616,201,190/.57f},{1.f,648,311,100/.52f},{1.25f,641,396,112/.55f},{1.5f,638,532,165/.76f}}; /* 그림 둘레 빈칸만큼 키운다(내용 57·52·55·76%) */ /* 5.25~5.75초 프레임 실측(1280x720) */
 for(int i=0;i<4;i++){auto id="ScOp"+std::to_string(i);const auto& k=tiles[i];if(t<k.at){UI::SetVisible(this,"scv3",id,false);continue;}
  float pop=t<k.at+.12f?1.5f-.5f*scv3::ease((t-k.at)/.12f):1.f,br=t>2.75f?std::min(1.f,(t-2.75f)/.45f):0.f,side=i%2?1.f:-1.f;
  scv3Box(id,k.cx+side*br*140,k.cy+br*br*300,k.s*pop,k.s*pop,1-br,side*br*30);}
 static const float hx[4]{470,810,470,810},hy[4]{230,230,500,500};
 for(int i=0;i<4;i++){float op=t<2.f?0.f:t<2.15f?(t-2.f)/.15f:t<2.75f?1.f:std::max(0.f,1-(t-2.75f)/.3f);scv3Box("ScHibi"+std::to_string(i),hx[i],hy[i],430,430,op,float(i*90));} /* 6.5초 : 가운데에서 사방으로 번개 금 */
 if(t>=1.f&&t-scv3Prev<.5f&&scv3Prev<1.f)sfx("v3se_363");if(t>=2.f&&scv3Prev<2.f)sfx("v3se_364");scv3Prev=t;
 // 열쇠·원판(영상 1번 10.75~13.25초, V3 의 3D 장면을 블렌더로 비슷하게 만든 78장 : tools/blender_scrum_lock.py) — 래피 앞발이 열쇠를 꽂아 돌리면 원판 타일이 바뀐다
 {float u=t-3.4f;bool on=u>=0&&u<2.6f;UI::SetVisible(this,"scv3","ScLock",on);UI::SetVisible(this,"scv3","ScLockBg",on);if(on){UI::SetPosition(this,"scv3","ScLockBg",{0,0});UI::SetSize(this,"scv3","ScLockBg",{1280,720});UI::SetOpacity(this,"scv3","ScLockBg",1);}
  {int pf=std::clamp(int((t<3.4f?t*78/3.4f:(u+.2f)*30))+2,1,78);char pn[48];std::snprintf(pn,sizeof pn,"Assets/Art/ui/v3_scrum/lock/%04d.webp",pf);UI::SetTexture(this,"scv3","ScLockPre",pn);UI::SetPosition(this,"scv3","ScLockPre",{0,0});UI::SetSize(this,"scv3","ScLockPre",{2,2});UI::SetOpacity(this,"scv3","ScLockPre",.02f);UI::SetVisible(this,"scv3","ScLockPre",t<6.f);} /* 의견대립 동안 78장을 차례로 미리 읽는다 */if(on){int f=std::clamp(int(u*30)+1,1,78);char n[48];std::snprintf(n,sizeof n,"Assets/Art/ui/v3_scrum/lock/%04d.webp",f);UI::SetTexture(this,"scv3","ScLock",n);scv3Box("ScLock",640,360,1280,720,1);
  float d=u<.15f?1-u/.15f:u>2.45f?(u-2.45f)/.15f:0.f;scv3Box("ScDim",640,360,1280,720,d);for(int i=0;i<4;i++){UI::SetVisible(this,"scv3","ScOp"+std::to_string(i),false);UI::SetVisible(this,"scv3","ScHibi"+std::to_string(i),false);}}}
 return t<6.f;
}
// 2. 주제·두 팀(33.5~42.5초) : 어둠에서 밝아짐 → 가운데 주제 글(34.2) → 왼쪽 팀 + 붉은 띠(35.5~37.2) → 오른쪽 팀 + 푸른 띠(38.5) → 두 줄 전체(39.5) → 검은 번쩍(40.3) → 「논의 스크럼 시작」(41.5)
bool Yumeno::scv3TeamIntro(float t){
 const auto& d=scv3Task();auto topic=d.value("topic",std::string()),lt=d.value("them",std::string()),ut=d.value("us",std::string());
 int nThem=0,nUs=0;
 if(stage.contains("scrumSides")){
  const auto& sides=stage.at("scrumSides");
  nThem=int(sides.at("them").size());
  nUs=int(sides.at("us").size());
 }else{
  std::set<std::string> them,us{"미오"};
  for(const auto& pair:stage.at("pairs")){
   them.insert(pair.value("them",""));
   us.insert(pair.value("us",""));
  }
  nThem=int(them.size());
  nUs=int(us.size());
 }
 float zThem=(nThem-1)*.56f,zUs=(nUs-1)*.56f;
 if(t<2.f)setCam({0,1.7f,3.6f,0,6,-7}); /* 솟은 증언대 위에서 통로 너머 왕좌 쪽(34.2초 기울인 화면) */                                                       // 34.2초 : 왕좌를 비스듬히 올려다봄
 else if(t<3.4f){float u=(t-2.f)/1.4f;setCam({.2f+.1f*u,1.8f,zThem+.75f-.25f*u,52,-3,0}); /* 37초 : 맨 앞 사람부터 가슴 위가 크게 줄지어 보인다 */}    // 37초 : 왼쪽(상대) 팀을 앞에서 비스듬히
 else if(t<4.6f){float u=(t-3.4f)/1.2f;setCam({-.2f-.1f*u,1.8f,zUs+.75f-.25f*u,-52,-3,0});}   // 38.5초 : 오른쪽(우리) 팀
 else setCam({0,2.2f,4.4f,0,-5,0}); /* 두 줄 끝에서 왕좌 쪽 */                                                           // 39.5~42초 : 통로 끝에서 왕좌 쪽으로 두 줄 전체
 float dark=t<.5f?1-t/.5f:t>=5.6f&&t<5.9f?1.f:t>=5.9f&&t<6.1f?1-(t-5.9f)/.2f:0.f;scv3Box("ScDim",640,360,1280,720,dark);
 float topOp=t<.5f?0.f:t<.8f?(t-.5f)/.3f:t<1.8f?1.f:std::max(0.f,1-(t-1.8f)/.2f);
 scv3Box("ScTopicBand",640,360,1280,110,topOp*.85f);scv3Box("ScTopic",640,360,1180,70,topOp);UI::SetText(this,"scv3","ScTopic",topic);
 auto arrow=[&](const char* s,bool on,float in,const std::string& label){bool l=s[0]=='L';float u=scv3::ease(in/.25f),dx=(l?-1.f:1.f)*560*(1-u); /* V3 t_scm_team_pl 띠는 화면 끝에서 미끄러져 들어온다(37·38.5초) */
  float cx=(l?188.f:1092.f)+dx,tx=(l?258.f:1022.f)+dx;scv3Box(std::string("ScArrow")+s,cx,624,680,105,on?1.f:0.f);scv3Box(std::string("ScArrowTail")+s,cx,624,680,105,on?1.f:0.f);
  scv3Box(std::string("ScArrowT")+s,tx,622,480,40,on?1.f:0.f);UI::SetText(this,"scv3",std::string("ScArrowT")+s,label);};
 bool lOn=t>=2.f&&t<5.6f||t>=5.9f,rOn=t>=3.4f&&t<5.6f||t>=5.9f;arrow("L",lOn,t>=5.9f?1.f:t-2.f,lt);arrow("R",rOn,t>=5.9f?1.f:t-3.4f,ut);
 scv3Emblem(t>=2.f&&!(t>=5.6f&&t<5.9f),t);
 float s=t-5.9f;float sOp=s<0?0.f:s<.15f?s/.15f:s<1.3f?1.f:std::max(0.f,1-(s-1.3f)/.2f),pop=s<.15f?1.3f-.3f*scv3::ease(s/.15f):1.f;
 scv3Box("ScStartLine",640,360,1280*scv3::ease(s/.2f),16,sOp*.9f);scv3Box("ScStartEf",640,360,640*pop,104*pop,sOp*(.6f+.4f*std::sin(s*20)));scv3Box("ScStart",640,360,590*pop,96*pop,sOp);
 {bool st=t>=5.9f;for(auto id:{"StatusPanel","StatusLabel"})UI::SetVisible(this,UI_ID,id,st);for(int i=0;i<10;i++)UI::SetVisible(this,UI_ID,"Star"+std::to_string(i),st);} /* 41.5초 「논의 스크럼 시작」과 함께 STATUS */
 if(t>=5.9f&&scv3Prev<5.9f)sfx("v3se_356");if(t>=2.f&&scv3Prev<2.f)sfx("v3se_365");scv3Prev=t;
 return t<7.5f;
}
// 가운데 아래 문양(영상 1번 37~140초) : 육각 판 안에 주제 글이 두세 글자씩 흘러간다
void Yumeno::scv3Emblem(bool on,float t,float dx){if(!UI::Mounted("scv3"))return;if(scv3Op>=0||scrumT<1)on=false; /* 의견대립·열쇠·증언대 동안은 없음 */
 scv3Box("ScEmblem",640+dx,626,150,150,on?1.f:0.f);scv3Box("ScEmblemDecoL",590+dx,626,150,150,on?1.f:0.f);scv3Box("ScEmblemDecoR",690+dx,626,150,150,on?1.f:0.f);scv3Box("ScEmblemFrame",640+dx,626,150,150,on?1.f:0.f);scv3Box("ScEmblemT",640+dx,622,130,50,on?1.f:0.f);if(!on)return;
 auto chars=debate::glyphs(scv3Task().value("topic",std::string()));if(chars.empty())return;int n=int(chars.size()),at=int(t/.33f)%(n+2);std::string w;for(int i=at-2;i<=at;i++)if(i>=0&&i<n)w+=chars[i];UI::SetText(this,"scv3","ScEmblemT",w);
}
// 진행 중 시간판(위 가운데, 43초 「04:59:233」)
void Yumeno::scv3Clock(float left){if(!UI::Mounted("scv3"))return;
 if(scv3Op>=0||scv3Team>=0||scv3PushT>=0||scrumT<1||mash>=0){for(int i=0;i<9;i++)UI::SetVisible(this,"scv3","ScTimeD"+std::to_string(i),false);UI::SetVisible(this,"scv3","ScTimeBase",false);UI::SetVisible(this,"scv3","ScTimeIco",false);return;}
 int ms=int(std::max(0.f,left)*1000);char c[16];std::snprintf(c,sizeof c,"%02d:%02d:%03d",ms/60000,ms/1000%60,ms%1000);
 scv3Box("ScTimeBase",640,44,360,62,1);scv3Box("ScTimeIco",478,44,34,34,1);float x=516;
 for(int i=0;i<9;i++){auto id="ScTimeD"+std::to_string(i);bool colon=c[i]==':';UI::SetTexture(this,"scv3",id,"Assets/Art/ui/v3_scrum/t_time_num_0"+std::string(colon?"10":std::string("0")+c[i])+".webp");scv3Box(id,x+(colon?7.f:13.f),44,colon?14.f:26.f,36,1);x+=colon?14.f:26.f;}
}
// 큰 발언 글 : 상대(왼쪽 인물)면 글은 오른쪽, 아군(오른쪽 인물)이면 왼쪽(영상 1번 46초·98.5초)
void Yumeno::scv3Claim(const std::string& text,bool speakerLeft,bool plain){if(!UI::Mounted("scv3cut"))return;
 static const Json bank=Data::Get("Assets/Data/scrum_v3text.json");if(text.empty()||!bank["items"].contains(text)){UI::SetVisible(this,"scv3cut","ScClaim",false);return;}
 const auto& it=bank["items"][text];UI::SetTexture(this,"scv3cut","ScClaim",(plain&&it.contains("plain")?it["plain"]:it["texture"]).get<std::string>());float cx=speakerLeft?960.f:330.f;UI::SetPosition(this,"scv3cut","ScClaim",{cx-310,330-146});UI::SetSize(this,"scv3cut","ScClaim",{620,292});UI::SetOpacity(this,"scv3cut","ScClaim",std::min(1.f,scv3CutT/.3f));UI::SetVisible(this,"scv3cut","ScClaim",true); /* 영상 42.6~44.4초 : 글은 인물 판 뒤에서, 인물이 비켜나며 드러난다 */
}
// 마지막 맞물림 뒤(137.9~141.5초) : 아래 띠에 분홍 번쩍 → 흑백 사선 + 「CROUCH」「BIND」 → 「SET!」 → 밀기
bool Yumeno::scv3PushCutin(float t){
 setCam({0,2.2f,4.4f,0,-5,0}); /* 두 줄 끝에서 왕좌 쪽 */
 scv3Box("ScHit",640,624,1280*scv3::ease(t/.15f),150,t<.45f?1-t/.45f:0.f);
 float c=t-.4f,cOp=c<0?0.f:c<.12f?c/.12f:c<1.4f?1.f:std::max(0.f,1-(c-1.4f)/.15f);
 scv3Box("ScPushPl",640,330,1280,150,cOp*.9f);scv3Box("ScCrouch",470+40*(1-scv3::ease(c/.2f)),330,520,130,cOp);scv3Box("ScBind",830-40*(1-scv3::ease(c/.2f)),330,420,130,cOp);
 float s=t-1.6f,sOp=s<0?0.f:s<.1f?s/.1f:s<.8f?1.f:std::max(0.f,1-(s-.8f)/.15f),pop=s<.12f?1.6f-.6f*scv3::ease(s/.12f):1.f;
 scv3Box("ScSetEf",640,330,640*pop,170*pop,sOp*.8f);scv3Box("ScSet",640,330,560*pop,150*pop,sOp);
 bool arrows=t<2.6f;for(auto s2:{"L","R"}){bool l=s2[0]=='L';scv3Box(std::string("ScArrow")+s2,l?188.f:1092.f,624,680,105,arrows?1.f:0.f);scv3Box(std::string("ScArrowTail")+s2,l?188.f:1092.f,624,680,105,arrows?1.f:0.f);scv3Box(std::string("ScArrowT")+s2,l?258.f:1022.f,622,480,40,arrows?1.f:0.f);}
 UI::SetText(this,"scv3","ScArrowTL",scv3Task().value("them",std::string()));UI::SetText(this,"scv3","ScArrowTR",scv3Task().value("us",std::string()));scv3Emblem(arrows,t);
 if(t>=.4f&&scv3Prev<.4f)sfx("v3se_364");if(t>=1.6f&&scv3Prev<1.6f)sfx("v3se_365");scv3Prev=t;
 return t<2.6f;
}
// 밀기 단추(141.5~146.5초) : 말하는 아군 얼굴 위 둥근 키 단추(PC : 세모 W · 동그라미 D · X S · 네모 A), 바깥 푸른 고리가 조여든다
void Yumeno::scv3PushButton(int direction,float phaseT,bool on){if(!UI::Mounted("scv3"))return;
 static const char* tex[]{"triangle","circle","cross","square"};
 if(!on){for(auto id:{"ScBtn","ScBtnEf","ScBtnRing","ScPushTx"})UI::SetVisible(this,"scv3",id,false);return;}
 UI::SetTexture(this,"scv3","ScBtn",std::string("Assets/Art/ui/v3_scrum/t_scrum_push_button_")+tex[std::clamp(direction,0,3)]+"_win.webp");
 {float j=.75f+.25f*std::sin(phaseT*24);UI::SetTexture(this,"scv3","ScJet","Assets/Art/ui/v3_scrum/t_scm_jet_ef_ray_l_000.webp");scv3Box("ScJet",1180,330,560*j,560*j,.9f,180);}
 float ring=1.8f-.8f*std::fmod(phaseT*2.2f,1.f);scv3Box("ScBtnRing",910,300,170*ring,170*ring,.9f);scv3Box("ScBtnEf",910,300,230,230,.35f+.25f*std::sin(phaseT*18));scv3Box("ScBtn",910,300,112,112,1); /* 141.5초 : 말하는 아군(미오, 화면 오른쪽 x≈910) 얼굴 위 */
}
// 맞는 아군의 응수(3.2초) → 이어지는 대본 줄(2.8초씩)을 같은 큰 글로. 말하는 사람 쪽으로 카메라(scrumFocus)
void Yumeno::scv3Respond(float delta){
 if(scv3Resp<0||scv3Resp>=int(stage["pairs"].size()))return;const auto& p=stage["pairs"][scv3Resp];scv3RespT+=delta;
 auto slugOf=[&](const std::string& n,const std::string& fallback){if(!fallback.empty())return fallback;return slugs.count(n)?slugs.at(n):std::string();};
 std::set<std::string> them;for(auto& q:stage["pairs"])them.insert(slugOf(q.value("them",""),q.value("themActor","")));
 if(scv3RespT<.8f){scv3Speaker("",true);scv3Box("ScHit",640,624,1280*scv3::ease(scv3RespT/.15f),150,scv3RespT<.45f?1-scv3RespT/.45f:0.f);scrumFocus();return;} /* 97.2~98초 : 맞힌 순간 아래 띠 번쩍 + 넓은 화면 */
 if(scv3RespT<4.f){scv3Focus=slugOf(p.value("us",""),p.value("usActor",""));scv3Speaker(scv3Focus,false);scv3Claim(p.value("usText",std::string()),false);scv3Box("ScHit",640,624,1280*scv3::ease(scv3RespT/.15f),150,scv3RespT<.45f?1-scv3RespT/.45f:0.f);}
 else{int i=std::min(int((scv3RespT-4.f)/2.8f),int(scv3Lines.size())-1);if(i<0)return;const auto& r=scv3Lines[i];scv3Focus=r.value("actor",std::string());bool l=them.count(scv3Focus)>0;scv3Speaker(scv3Focus,l);scv3Claim(r.value("text",std::string()),l);}
 scrumFocus();
}
// 말하는 사람(영상 1번 42.3~48.4초·98.4초) : 화자를 증언대 자리에서 잡는 건 scrumFocus. 여기는 발언 글 시간만
void Yumeno::scv3Speaker(const std::string& slug,bool left){
 if(!UI::Mounted("scv3cut"))return;float dt=std::max(0.f,stageTime-scv3CutClock);scv3CutClock=stageTime;
 /* 주인님 지시 2026-11-07 : 2D 컷인을 크게 띄우지 않는다(V3 46초 신구지는 증언대 자리에 선 채 카메라가 다가감). 화자는 scrumFocus 가 잡고, 여기서는 화자가 바뀐 시각만 재서 발언 글이 0.3초에 걸쳐 나타나게 한다 */
 for(auto id:{"ScCut0","ScCut1"})UI::SetVisible(this,"scv3cut",id,false);
 if(slug.empty()){UI::SetVisible(this,"scv3cut","ScBgDim",false);UI::SetVisible(this,"scv3cut","ScClaim",false);scv3CutKey.clear();return;}
 UI::SetPosition(this,"scv3cut","ScBgDim",{0,0});UI::SetSize(this,"scv3cut","ScBgDim",{1280,720});UI::SetOpacity(this,"scv3cut","ScBgDim",.35f);UI::SetVisible(this,"scv3cut","ScBgDim",true); /* V3 46초 : 발언 중 화면 전체가 어둡게 물든다(흰 벽 위 흰 글이 읽히게) */
 std::string key=slug+(left?"_SR":"_SL");if(key!=scv3CutKey){scv3CutKey=key;scv3CutLeft=left;scv3CutT=0;}
 scv3CutT+=dt;
}
// 진행 중 뒤 배경 카메라 : 통로 끝에서 왕좌 쪽(인물 판 뒤로 어둡게 보인다). 맞힌 직후 0.8초는 건너편 줄을 훑는다(97.6초)
void Yumeno::scv3PlayCam(){
 if(scv3Resp>=0&&scv3RespT<.8f){float u=scv3::ease(scv3RespT/.8f);setCam({-.7f+.9f*u,1.85f,3.1f-.4f*u,-18+26*u,2,0});return;}
 float a=std::sin(stageTime*.25f);setCam({.15f*a,2.15f,4.3f,2*a,-4,0});
}
// 밀기 동안 단추가 바뀔 때마다 다음 아군 얼굴(영상 141.5 모모타 → 143.5 키보 → 146.5 카에데)
std::string Yumeno::scv3PushSlug()const{std::vector<std::string> us{"mio"};for(const auto& p:stage["pairs"]){auto s=p.value("usActor",std::string());if(s.empty()&&slugs.count(p.value("us",std::string())))s=slugs.at(p.value("us",std::string()));if(!s.empty()&&std::find(us.begin(),us.end(),s)==us.end())us.push_back(s);}return us[size_t(std::max(0,scrumV4.pattern+scrumV4.phase*3))%us.size()];}
