void Yumeno::chapterArchiveInit(){
 try{chapterarchive::restore(chapterEntries,Json::parse(Save::ReadText(campaignv4::slot("yumeno-v4-chapter-index"))));}catch(const std::exception&){}
 // Result history is in the small head; reading it does not restore story/world/log parts.
 try{auto head=Json::parse(Save::ReadText(campaignv4::slot("yumeno-progress-v4")));if(campaignv4::matches(head)){difficultyv4::restore(difficultyV4,head.value("difficulty",Json()));resultv4::State result;if(resultv4::restore(result,head.value("trialResults",Json())))trialResults=std::move(result);}}catch(const std::exception&){}
}
void Yumeno::chapterArchiveObserve(const Json& node){
 if(!v4.active||v4.restoring||!node.contains("chapterEntryType"))return;auto chapter=v4.graph.value("chapter",std::string());int type=node["chapterEntryType"].get<int>();auto key=chapterarchive::key(chapter,type);
 if(chapterEntries.count(key)||chapterArchiveClaims.count(key))return;
 auto snapshot=v4Snapshot();chapterArchiveClaims.insert(key);chapterArchiveQueue.push_back({{chapter,v4.node,chapterarchive::slot(chapter,type),type},std::move(snapshot)});
}
void Yumeno::chapterArchiveTick(){
 if(chapterArchiveQueue.empty()||padStorageBusy)return;auto& job=chapterArchiveQueue.front();
 if(chapterArchiveWriter.slot.empty()){if(!savev4::begin(chapterArchiveWriter,job.entry.slot,job.snapshot)){chapterArchiveClaims.erase(chapterarchive::key(job.entry.chapter,job.entry.type));chapterArchiveQueue.pop_front();chapterArchiveWriter={};toast("구간 기록을 저장하지 못했어요");}return;}
 int result=savev4::step(chapterArchiveWriter);if(result==0)return;
 if(result>0){try{auto next=chapterEntries;next[chapterarchive::key(job.entry.chapter,job.entry.type)]=job.entry;auto index=chapterarchive::save(next);Save::Write(campaignv4::slot("yumeno-v4-chapter-index"),index);if(Json::parse(Save::ReadText(campaignv4::slot("yumeno-v4-chapter-index")))!=index)throw std::runtime_error("Chapter index readback");chapterEntries=std::move(next);if(chapterSelectOn&&mode==Mode::Title)chapterSelectDraw();}catch(const std::exception&){result=-1;}}
 if(result<0){chapterArchiveClaims.erase(chapterarchive::key(job.entry.chapter,job.entry.type));toast("구간 기록을 저장하지 못했어요");}chapterArchiveQueue.pop_front();chapterArchiveWriter={};
}
void Yumeno::chapterSelectOpen(){
 titleMenu(false);chapterSelectOn=true;chapterSelectDepth=0;chapterSelectChapter=std::clamp(chapterSelectChapter,0,6);chapterSelectRow=0;chapterSelectArmed=false;chapterSelectDraw();
}
void Yumeno::chapterSelectClose(){chapterSelectOn=false;chapterSelectWidgetShown=false;UI::Remove(this,"chapterselectv4");titleMenu(true);}
void Yumeno::chapterSelectOptions(){
 chapterSelectTypes.clear();auto ch=chapterSelectChapter==0?std::string("P"):std::to_string(chapterSelectChapter);
 for(int type=0;type<4;type++)if(chapterEntries.count(chapterarchive::key(ch,type)))chapterSelectTypes.push_back(type);
 if(trialResults.best.count(ch))chapterSelectTypes.push_back(4);chapterSelectRow=std::clamp(chapterSelectRow,0,std::max(0,int(chapterSelectTypes.size())-1));
}
bool Yumeno::chapterSelectUpdate(float delta){
 if(!chapterSelectOn)return false;if(!chapterSelectArmed){if(!Input::IsKeyDown("Enter")&&!Input::IsKeyDown("mouse0"))chapterSelectArmed=true;return true;}
 bool back=pressed("Backspace")||pressed("Escape")||pressed("mouse1");if(back){if(chapterSelectDepth){chapterSelectDepth=0;chapterSelectRow=0;chapterSelectDraw();}else chapterSelectClose();return true;}
 Vec2 mouse;Input::GetMousePositionForCanvas({1280,720},mouse);bool confirm=pressed("Enter");int old=chapterSelectDepth?chapterSelectRow:chapterSelectChapter;
 if(chapterSelectDepth==0){if(pressed("a")||pressed("ArrowLeft"))chapterSelectChapter=(chapterSelectChapter+6)%7;if(pressed("d")||pressed("ArrowRight"))chapterSelectChapter=(chapterSelectChapter+1)%7;
  if(pressed("mouse0")){int hit=chapterSelectHit(mouse.x,mouse.y);if(hit>=0){chapterSelectChapter=hit;confirm=true;}}
  if(old!=chapterSelectChapter){sfx("ui_select");chapterSelectDraw();}if(confirm){chapterSelectOptions();if(chapterSelectTypes.empty()){sfx("ui_cancel");return true;}chapterSelectDepth=1;chapterSelectRow=0;chapterSelectArmed=false;chapterSelectDraw();}return true;
 }
 int count=int(chapterSelectTypes.size());if(count==0)return true;if(pressed("w")||pressed("ArrowUp"))chapterSelectRow=(chapterSelectRow+count-1)%count;if(pressed("s")||pressed("ArrowDown"))chapterSelectRow=(chapterSelectRow+1)%count;
 if(pressed("mouse0")){int hit=chapterSelectPartHit(mouse.x,mouse.y);if(hit>=0&&hit<count){chapterSelectRow=hit;confirm=true;}}
 if(old!=chapterSelectRow){sfx("ui_select");chapterSelectDraw();}if(!confirm)return true;
 auto ch=chapterSelectChapter==0?std::string("P"):std::to_string(chapterSelectChapter);int type=chapterSelectTypes[chapterSelectRow];
 if(type==4){UI::SetVisible(this,"chapterselectv4","root",false);trialResultStart(true,ch);return true;}
 const auto& entry=chapterEntries.at(chapterarchive::key(ch,type));UI::SetVisible(this,"chapterselectv4","root",false);difficultyOpen(entry.slot);return true;
}

void Yumeno::chapterSelectDraw(){
 if(!chapterSelectOn)return;if(!chapterSelectWidgetShown){UI::Show(this,"Assets/UI/ChapterSelectV4.hbwidget.json","chapterselectv4");chapterSelectWidgetShown=true;}UI::SetVisible(this,"chapterselectv4","root",true);chapterSelectOptions();
 for(int i=0;i<7;i++){auto ch=i==0?std::string("P"):std::to_string(i);bool enabled=trialResults.best.count(ch)>0;for(int t=0;t<4;t++)enabled=enabled||chapterEntries.count(chapterarchive::key(ch,t));auto name="CsPlate"+std::to_string(i);UI::SetTexture(this,"chapterselectv4",name,"Assets/Art/ui/v3/title_chapter/plate_"+std::to_string(i)+(i==chapterSelectChapter?"_on.svg":"_off.svg"));UI::SetOpacity(this,"chapterselectv4",name,enabled?1.f:.28f);}
 auto ch=chapterSelectChapter==0?std::string("P"):std::to_string(chapterSelectChapter);UI::SetText(this,"chapterselectv4","CsStatus",(chapterSelectChapter==0?std::string("프롤로그"):"제"+ch+"장")+" · "+(chapterSelectTypes.empty()?"아직 도달하지 않았어요":"진행한 구간을 선택할 수 있어요"));
 bool parts=chapterSelectDepth!=0;UI::SetVisible(this,"chapterselectv4","CsParts",parts);if(parts)UI::SetTexture(this,"chapterselectv4","CsParts","Assets/Art/ui/v3/title_chapter/parts_"+std::to_string(chapterSelectTypes.size())+"_"+std::to_string(chapterSelectRow)+".svg");
 for(int i=0;i<5;i++){auto name="CsPart"+std::to_string(i);bool show=parts&&i<int(chapterSelectTypes.size());UI::SetVisible(this,"chapterselectv4",name,show);if(show){UI::SetText(this,"chapterselectv4",name,chapterarchive::label(chapterSelectTypes[i]));UI::SetColor(this,"chapterselectv4",name,i==chapterSelectRow?Color{1,.83f,.1f,1}:Color{.94f,.92f,.9f,1});}}
 UI::SetText(this,"chapterselectv4","CsGuide",parts?"W/S 구간 선택 · Enter 결정 · Backspace 장 선택":"A/D 장 선택 · Enter 결정 · Backspace 타이틀");
}
int Yumeno::chapterSelectHit(float x,float y)const{static const auto layout=Data::Get("Assets/Data/v4_story/title_chapter_layout.json");for(int i=6;i>=0;i--){const auto& r=layout["chapterRects"][i];if(x>=r[0].get<float>()&&x<=r[0].get<float>()+r[2].get<float>()&&y>=r[1].get<float>()&&y<=r[1].get<float>()+r[3].get<float>())return i;}return -1;}
int Yumeno::chapterSelectPartHit(float x,float y)const{static const auto layout=Data::Get("Assets/Data/v4_story/title_chapter_layout.json");for(int i=0;i<5;i++){const auto& r=layout["parts"][i];if(x>=r[0].get<float>()&&x<=r[0].get<float>()+r[2].get<float>()&&y>=r[1].get<float>()&&y<=r[1].get<float>()+r[3].get<float>())return i;}return -1;}
