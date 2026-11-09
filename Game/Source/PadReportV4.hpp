// Source report/skill separation. Own physical profiles and already-read lines
// are not the original game's character text, unlock bits or numeric growth.
std::string Yumeno::padReportActor()const{return padui::REPORTERS[std::clamp(padRow,0,15)];}
bool Yumeno::padReportAllowed(int index)const{
 if(index<0||index>=16)return false;if(index==0||!v4.active||chapterAt>0)return true;
 for(const auto& row:v4.log)if(row.value("actor",std::string())==padui::REPORTERS[index]&&row.value("speaker",std::string())!="???")return true;
 return false;
}
int Yumeno::padReportPages()const{
 if(padRow==0)return 2;if(!v4.active||growthV4.contract.empty())return 1;
 return 1+int(growthv4::Pages(growthV4,padui::REPORTERS[std::clamp(padRow,0,15)]).size());
}
std::vector<hb::Json> Yumeno::padSkills()const{
 std::vector<Json> out;if(!v4.active||growthV4.contract.empty())return out;
 for(const auto& skill:skillData["items"])if(growthv4::Supported(growthV4,skill)&&(!skill.value("legacyOnly",false)||growthV4.owned.count(skill.value("id",std::string()))))out.push_back(skill);return out;
}
void Yumeno::padReportDraw(){
 auto hint=[&](const std::string& message){UI::SetText(this,"padreport","PrHintShadow",message);UI::SetText(this,"padreport","PrHint",message);};
 if(!padReportAllowed(padRow))padRow=0;padReportPage=std::clamp(padReportPage,0,padReportPages()-1);
 if(padReportVisible)UI::Remove(this,"padreport");UI::Show(this,"Assets/UI/PadReportV4.hbwidget.json","padreport");padReportVisible=true;
 for(auto id:{"PdTitle","PdTint","PdSide","PdCoins","PdName","PdSchool"})pvis(id,false);
 const auto who=std::string(padui::REPORTERS[padRow]);const auto& profiles=Data::Get("Assets/Data/v4_story/report_profiles.json");const auto& profile=profiles["items"][who];
 const auto layout=Data::Get("Assets/Data/v4_story/report_layout.json");
 const auto pageState=padRow==0?(padReportPage==0?"fl_shuzinko_wait_0":"fl_shuzinko_wait_1"):(padReportPage==0?"fl_wait_0":"fl_wait_1");
 const auto panels=layout["bodyPanels"][pageState];
 const auto sourceBody=Data::Get("Assets/Data/v4_story/report_source_ui.json")["states"][padReportPage==0?"report_profile":"report_memo"];UI::SetTexture(this,"padreport","PrSourceBody",sourceBody["asset"].get<std::string>());
 for(int i=0;i<3;i++){auto id="PrBodyPlate"+std::to_string(i);bool on=i<int(panels.size())&&panels[i].value("visible",false);UI::SetVisible(this,"padreport",id,on);if(on){auto r=panels[i]["rect"];UI::SetPosition(this,"padreport",id,{r[0].get<float>(),r[1].get<float>()});UI::SetSize(this,"padreport",id,{r[2].get<float>(),r[3].get<float>()});UI::SetOpacity(this,"padreport",id,panels[i]["alpha"].get<float>());}}
 UI::SetTexture(this,"padreport","PrStanding","Assets/Art/court_figures/"+who+".webp");UI::SetText(this,"padreport","PrName",profile.value("name",nameOf(who)));
 UI::SetTexture(this,"padreport","PrAffinity","Assets/Art/ui/pad_affinity_"+std::to_string(padRow==0?0:std::clamp(level(who),0,5))+".svg");
 for(int i=0;i<16;i++){auto n=std::to_string(i);UI::SetTexture(this,"padreport","PrActor"+n,std::string("Assets/Art/court_figures/")+padui::REPORTERS[i]+".webp");UI::SetOpacity(this,"padreport","PrActor"+n,i==padRow?1.f:padReportAllowed(i)?.16f:.08f);UI::SetVisible(this,"padreport","PrActorLine"+n,false);}
 for(int i=0;i<8;i++){auto n=std::to_string(i);UI::SetVisible(this,"padreport","PrLabel"+n,padReportPage==0);UI::SetVisible(this,"padreport","PrValue"+n,padReportPage==0);if(padReportPage==0){UI::SetText(this,"padreport","PrLabel"+n,profile["labels"][i].get<std::string>());UI::SetText(this,"padreport","PrValue"+n,profile["values"][i].get<std::string>());UI::SetFontSize(this,"padreport","PrValue"+n,profile["fontSizes"][i].get<float>());}}
 bool skillEntry=padRow==0&&padReportPage==1;UI::SetVisible(this,"padreport","PrSkillEntry",skillEntry);
 if(skillEntry){hint("A/D 인물 · W/S 페이지 · Enter 스킬 · Esc 돌아가기");return;}
 bool memo=padReportPage>0;for(auto id:{"PrPageLabel","PrPageValue","PrMemoViewport"})UI::SetVisible(this,"padreport",id,memo);
 if(memo){
  std::string title,body;
  if(padRow==0){title="스킬";body="스킬 목록";hint("A/D 인물 · W/S 페이지 · Enter 스킬 · Esc 돌아가기");}
  else{
   const auto pages=growthv4::Pages(growthV4,who);const auto& page=pages[padReportPage-1];title="함께한 시간";body=page.value("title",std::string());
   // Quote only this player's actual read nodes from this completed encounter,
   // including its delayed-entry alias; never display an unchosen branch.
   std::vector<std::string> prefixes;
   if(v4.graph.contains("campaignRevision"))prefixes.push_back("rev:"+page.at("source").at("location").get<std::string>()+":");
   else for(const auto& f:page["completionFlags"]){auto flag=f.get<std::string>();auto end=flag.find(':',4);if(end!=std::string::npos)prefixes.push_back("v4:"+flag.substr(4,end-4)+":");}
   std::vector<std::pair<int,std::string>> quotes;
   for(const auto& id:v4.read){bool match=false;for(const auto& prefix:prefixes)if(id.rfind(prefix,0)==0)match=true;if(!match)continue;
    const auto prefix=v4.graph.value("bucketPrefix",std::string("Assets/Data/v4_story/nodes/"));
    const auto count=v4.graph.value("bucketCount",128u);
    const auto& nodes=storyv4::bucketData(prefix,storyv4::bucket(id,count)).at("nodes");
    if(!nodes.contains(id))continue;const auto& node=nodes.at(id);
    if(node.value("type",std::string())=="say"&&node.value("actor",std::string())==who&&!node.value("mono",false))quotes.push_back({node.value("source",Json::object()).value("line",0),node.value("text",std::string())});
   }
   std::sort(quotes.begin(),quotes.end());for(int i=0;i<int(quotes.size());i++){if(i>=4&&i<int(quotes.size())-4)continue;body+="\n\n「"+quotes[i].second+"」";}
   hint("A/D 인물 · W/S 페이지 · 휠 기록 · Esc 돌아가기");
  }
  UI::SetText(this,"padreport","PrPageLabel",title);UI::SetText(this,"padreport","PrPageValue",std::to_string(padReportPage)+" / "+std::to_string(padReportPages()-1));UI::SetText(this,"padreport","PrMemo",body);
  int lines=debate::lineCount(body,"Assets/Fonts/pretendard/Pretendard-Medium.otf",30,600);UI::SetSize(this,"padreport","PrMemo",{600,std::max(320.f,(lines+1)*39.f)});
 }else hint("A/D 인물 · W/S 페이지 · Esc 돌아가기");
}
void Yumeno::padSkillDraw(){
 auto skills=padSkills();padSkillRow=std::clamp(padSkillRow,0,std::max(0,int(skills.size())-1));
 if(!padSkillVisible){UI::Show(this,"Assets/UI/PadSkillV4.hbwidget.json","padskill");padSkillVisible=true;}
 std::vector<Json> equipped;for(const auto& row:skills)if(growthV4.equipped.count(row.value("id",std::string())))equipped.push_back(row);
 int equippedFirst=0;if(!skills.empty())for(int i=0;i<int(equipped.size());i++)if(equipped[i].value("id",std::string())==skills[padSkillRow].value("id",std::string()))equippedFirst=std::max(0,i-6);
 int first=std::max(0,padSkillRow-6);
 static const auto sourceFocus=Data::Get("Assets/Data/v4_story/skill_source_ui.json")["states"];
 auto sourceDigit=[&](const std::string& id,int value,bool black=false){UI::SetTexture(this,"padskill",id,sourceFocus["techou_skill_list_US_digit_"+std::to_string(std::clamp(value,0,9))+(black?"_black":"")]["asset"].get<std::string>());};
 auto focus=[&](const std::string& side,int row){auto id="PsSourceFocus"+side;UI::SetVisible(this,"padskill",id,row>=0);if(row<0)return;const auto& f=sourceFocus["skill_"+side+"_"+std::to_string(row)];const auto& r=f["rect"];UI::SetTexture(this,"padskill",id,f["asset"].get<std::string>());UI::SetPosition(this,"padskill",id,{r[0].get<float>(),r[1].get<float>()});UI::SetSize(this,"padskill",id,{r[2].get<float>(),r[3].get<float>()});};
 focus("catalog",skills.empty()?-1:padSkillRow-first);focus("equipped",-1);
 for(int i=0;i<7;i++){
  int index=first+i;bool exists=index<int(skills.size()),on=index==padSkillRow;auto n=std::to_string(i);UI::SetVisible(this,"padskill","PsRow"+n,exists);
  if(exists){const auto& row=skills[index];bool owned=growthV4.owned.count(row.value("id",std::string()));UI::SetText(this,"padskill","PsRow"+n,row.value("name",std::string()));UI::SetOpacity(this,"padskill","PsRow"+n,on?1.f:.699219f*(owned?1.f:.5f));UI::SetColor(this,"padskill","PsRow"+n,on?Color{0,0,0,1}:Color{1,1,1,1});}
  bool eq=equippedFirst+i<int(equipped.size());UI::SetVisible(this,"padskill","PsEquipped"+n,eq);if(eq)UI::SetText(this,"padskill","PsEquipped"+n,equipped[equippedFirst+i].value("name",std::string()));
  for(int d=0;d<2;d++)for(int side=0;side<2;side++){
   bool active=side?eq:exists;auto id=std::string(side?"PsEquippedCost":"PsCost")+n+"_"+std::to_string(d);int cost=active?(side?equipped[equippedFirst+i].value("sp",0):skills[index].value(growthV4.owned.count(skills[index].value("id",std::string()))?"sp":"fp",0)):0;
   UI::SetVisible(this,"padskill",id,active&&(d==0||cost>=10));sourceDigit(id,(cost/(d==0?1:10))%10,!side&&on);UI::SetOpacity(this,"padskill",id,side||on?1.f:.699219f);UI::SetColor(this,"padskill",id,!side&&on?Color{0,0,0,1}:Color{1,1,1,1});
  }
 }
 int used=growthv4::Used(growthV4),capacity=growthv4::Capacity(growthV4,playerprogress::level(playerProgress));
 // Retained total carrier: catalog shows FP purchase price until owned, then SP.
 for(int d=0;d<4;d++){int value=d>=2?used:capacity,divisor=d%2==0?1:10;auto id="PsTotal"+std::to_string(d);sourceDigit(id,(value/divisor)%10);UI::SetVisible(this,"padskill",id,divisor==1||value>=10);}
 for(int d=0,divisor=100;d<3;d++,divisor/=10){auto id="PsFp"+std::to_string(d);sourceDigit(id,(growthV4.fp/divisor)%10);UI::SetVisible(this,"padskill",id,growthV4.fp>=divisor||d==2);}
 std::string status;if(!skills.empty()){const auto& row=skills[padSkillRow];bool owned=growthV4.owned.count(row.value("id",std::string()));status=owned?(growthV4.equipped.count(row.value("id",std::string()))?"장착 중 · ":"보유 · ")+std::to_string(row.value("sp",0))+" SP":row.value("fp",0)>0?"구입 · "+std::to_string(row.value("fp",0))+" FP":"자유행동 기록으로 획득";status+="\n"+row.value("text",std::string());}
 UI::SetText(this,"padskill","PsBody",status);
 auto hint="W/S 고르기 · Q/E 페이지 · Enter 구입/장착/해제 · Backspace 통신부";UI::SetText(this,"padskill","PsHint",hint);UI::SetText(this,"padskill","PsHintShadow",hint);
}
void Yumeno::padSkillConfirmDraw(){
 auto row=growthv4::Skill(growthV4,padSkillPurchase);if(!row)return;UI::Show(this,"Assets/UI/CommonConfirmV4.hbwidget.json","skillconfirm");
 UI::SetText(this,"skillconfirm","CwBody",row->value("name",std::string())+"\n"+std::to_string(row->value("fp",0))+" FP로 구입할까요?\n보유 FP "+std::to_string(growthV4.fp));
 for(int i=0;i<2;i++){UI::SetTexture(this,"skillconfirm","CwChoice"+std::to_string(i),std::string("Assets/Art/ui/pad_choice_")+(i==padSkillConfirm?"on":"off")+".svg");UI::SetOpacity(this,"skillconfirm",i==0?"CwYes":"CwNo",i==padSkillConfirm?1.f:.6f);}
}
bool Yumeno::padSkillConfirmUpdate(bool click){
 if(padSkillPurchase.empty())return false;
 auto close=[&](){padSkillPurchase.clear();UI::Remove(this,"skillconfirm");padSkillDraw();};
 if(!padSkillConfirmArmed){if(!Input::IsKeyDown("Enter")&&!Input::IsKeyDown("mouse0"))padSkillConfirmArmed=true;return true;}
 if(pressed("Backspace")||pressed("mouse1")||pressed("Escape")){close();sfx("ui_cancel");return true;}
 int before=padSkillConfirm;if(pressed("a")||pressed("ArrowLeft"))padSkillConfirm=0;if(pressed("d")||pressed("ArrowRight"))padSkillConfirm=1;bool select=pressed("Enter");
 if(click){Vec2 m;Input::GetMousePositionForCanvas({1280,720},m);static const auto layout=Data::Get("Assets/Data/v4_story/system_pages_layout.json");for(int i=0;i<2;i++){const auto& r=layout["confirm"][i==0?"yes":"no"];if(m.x>=r[0].get<float>()&&m.x<r[0].get<float>()+r[2].get<float>()&&m.y>=r[1].get<float>()&&m.y<r[1].get<float>()+r[3].get<float>()){padSkillConfirm=i;select=true;}}}
 if(before!=padSkillConfirm){padSkillConfirmDraw();sfx("ui_select");}if(!select)return true;
 if(padSkillConfirm==0){auto result=growthv4::Purchase(growthV4,padSkillPurchase,true,v4.active&&!v4Court&&!(machineActive&&machineFromGallery)&&v4.current().value("type",std::string())!="investigate");sfx(result.changed?"ui_confirm":"ui_cancel");if(!result.changed)toast(result.reason=="insufficient-fp"?"FP가 부족해요":"지금은 구입할 수 없어요");}else sfx("ui_cancel");close();return true;
}
