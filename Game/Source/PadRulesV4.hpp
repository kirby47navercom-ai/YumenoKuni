// Source rule reader: cover first, published table order, bounded W/S pages.
// Own public notices and art replace original prose/illustrations explicitly.
std::vector<std::string> Yumeno::padRuleIds()const{
 std::vector<std::string> out;
 if(v4.active){static const auto layout=Data::Get("Assets/Data/v4_story/rules_layout.json");for(const auto& key:layout["order"]){auto id=key.get<std::string>();if(v4Documents.contains(id)&&!v4Documents[id].value("private",false))out.push_back(id);}}
 else for(const auto& rule:rules["rules"])out.push_back(rule.value("no",std::string()));
 return out;
}
void Yumeno::padRulesDraw(){
 auto ids=padRuleIds();padRow=std::clamp(padRow,0,int(ids.size()));
 if(padRulesVisible)UI::Remove(this,"padrules");UI::Show(this,"Assets/UI/PadRulesV4.hbwidget.json","padrules");padRulesVisible=true;
 for(auto id:{"PdTitle","PdTint","PdSide","PdCoins","PdName","PdSchool","PdHint"})pvis(id,false);
 bool cover=padRow==0;for(auto id:{"KrCover","KrCoverTitleBand","KrCoverTitle"})UI::SetVisible(this,"padrules",id,cover);
 for(auto id:{"KrFigure","KrBodyShade","KrFrame0","KrFrame1","KrFrame2","KrBodyViewport","KrNumberBase","KrSlash"})UI::SetVisible(this,"padrules",id,!cover);
 for(int i=0;i<2;i++){UI::SetVisible(this,"padrules","KrPrev"+std::to_string(i),!cover);UI::SetVisible(this,"padrules","KrNext"+std::to_string(i),padRow<int(ids.size()));}
 if(cover){static const auto arrows=Data::Get("Assets/Data/v4_story/rules_layout.json")["coverNext"];for(int i=0;i<2;i++)UI::SetPosition(this,"padrules","KrNext"+std::to_string(i),{arrows[i][0].get<float>(),arrows[i][1].get<float>()});return;}
 std::string body;auto id=ids[padRow-1];
 if(v4.active){const auto& doc=v4Documents[id];for(const auto& row:doc["rows"]){if(!body.empty())body+="\n";body+=row.get<std::string>();}}
 else body=rules["rules"][padRow-1].value("text",std::string());
 static const auto layout=Data::Get("Assets/Data/v4_story/rules_layout.json");auto key=v4.active?id:"legacy:"+id;float height=73.33333f;
 if(layout["bodies"].contains(key)&&layout["bodies"][key].value("text",std::string())==body){const auto& format=layout["bodies"][key];body=format.value("wrapped",body);height=format.value("height",height);}
 else{std::string wrapped;float width=0;int lines=1;for(const auto& glyph:debate::glyphs(body)){if(glyph=="\n"){wrapped+=glyph;++lines;width=0;continue;}float advance=debate::em(glyph,"Assets/Fonts/pretendard/Pretendard-Medium.otf")*30; /* KrBody 글꼴 실측 폭 */if(width+advance>878){wrapped+="\n";++lines;width=0;}wrapped+=glyph;width+=advance;}body=wrapped;height=std::max(height,lines*39.f);}
 UI::SetText(this,"padrules","KrBody",body);UI::SetSize(this,"padrules","KrBody",{880,height});
 // Left pair=current, right pair=published total is an explicit own pairing;
 // original DAT-to-name association is not recovered by carrier geometry.
 for(int i=0;i<4;i++){int value=i<2?int(ids.size()):padRow,divisor=i%2?10:1;auto key="KrNumber"+std::to_string(i);UI::SetTexture(this,"padrules",key,Data::Get("Assets/Data/v4_story/rules_source_ui.json")["states"]["techou_kousoku_text_digit_"+std::to_string(value/divisor%10)]["asset"].get<std::string>());UI::SetVisible(this,"padrules",key,divisor==1||value>=10);}
}
bool Yumeno::padRulesUpdate(float delta,bool click){
 static const auto layout=Data::Get("Assets/Data/v4_story/rules_layout.json");
 if(padRuleTimer>0){
  padRuleTimer=std::max(0.f,padRuleTimer-delta);float duration=layout.value("transitionSeconds",.24f),phase=1-padRuleTimer/duration;
  // Source direction: next leaves up/enters from below, previous reverses.
  // Time/distance are own transition values, not original clip-duration proof.
  if(phase>=.5f&&!padRuleSwapped){padRow=padRuleTarget;padRulesDraw();padRuleSwapped=true;}
  float displacement=padRuleDirection*(phase<.5f?-phase*2:(1-phase)*2)*64;
  const char* figure=padRow==0?"KrCover":"KrFigure";const auto& r=layout[padRow==0?"cover":"figure"];
  UI::SetPosition(this,"padrules",figure,{r[0].get<float>(),r[1].get<float>()+displacement});
  UI::SetOpacity(this,"padrules",figure,std::abs(phase*2-1));return true;
 }
 Vec2 m;Input::GetCenteredMousePositionForCanvas({1280,720},m);int direction=pressed("w")?-1:pressed("s")?1:0;
 if(click&&m.x>=618.6667f&&m.x<=662.f){if(padRow>0&&m.y>=498.6667f&&m.y<552.f)direction=-1;if(m.y>=(padRow==0?620.6667f:629.3333f)&&m.y<=682.6667f)direction=1;}
 int next=std::clamp(padRow+direction,0,int(padRuleIds().size()));if(next==padRow)return false;
 padRuleTarget=next;padRuleDirection=direction;padRuleSwapped=false;padRuleTimer=layout.value("transitionSeconds",.24f);sfx("ui_select");return true;
}
