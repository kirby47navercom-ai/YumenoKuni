// Result ownership is separate from a single-stage refutation/agreement cut-in.
void Yumeno::trialScoreBegin(){
 trialScoreElapsed=0;trialScoreInitial=0;trialScoreVPoints=vBreaks;if(!v4TaskActive)return;
 if(stageKind=="nonstop"||stageKind=="panic")trialScoreInitial=debateTime*60;
 else if(stageKind=="showdown")trialScoreInitial=showdownV4.initialTime;
 else if(stageKind=="mindmine")trialScoreInitial=float(mineV4.time);
 else if(stageKind=="reasoning")trialScoreInitial=300*60*trialTimeFactor(); // Own replacement: five minutes admitted input.
 else if(stageKind=="climax")trialScoreInitial=600*60*trialTimeFactor(); // Own comic placement budget, review is excluded.
 else if(stageKind=="scrum")trialScoreInitial=300*60*trialTimeFactor(); // Own multi-round debate adapter.
 else if(resultv4::type(stageKind)>=0)trialScoreInitial=stageLimit*60;
}
void Yumeno::trialScoreTick(float delta){
 if(!v4TaskActive)return;trialResults.current.retry=std::max(trialResults.current.retry,retries);
 if(v4QueueActive||inScript||debateIntroTime>=0||debateResultTime>0||restartStage||v4ComicReview||(stageKind=="climax"&&v4ComicIntroTime>=0))return;
 if(stageKind=="reasoning"||stageKind=="climax"||stageKind=="scrum"){
  trialScoreElapsed=std::min(trialScoreInitial,trialScoreElapsed+delta*60);
  if(stageKind!="scrum"){int secs=std::max(0,int((trialScoreInitial-trialScoreElapsed)/60));stext("StageTimer",std::to_string(secs/60)+":"+(secs%60<10?"0":"")+std::to_string(secs%60));svis("StageTimer",true);}
  if(trialScoreElapsed>=trialScoreInitial){sfx("sfx_timeup");++retries;v4ResetHearts(maxHearts);restartStage=true;}
 }
}
void Yumeno::trialScoreCapture(){
 if(!v4TaskActive)return;int type=resultv4::type(stageKind);if(type<0)return;
 auto id=v4Task.value("taskId",std::string());for(const auto& row:trialResults.current.records)if(row.id==id)return;
 if(trialResults.current.chapter!=v4.graph.value("chapter",std::string()))resultv4::begin(trialResults,v4.graph.value("chapter",std::string()));
 float remaining=0;bool vp=false;
 if(type==0||type==8){remaining=debateTime*60;vp=vBreaks>trialScoreVPoints;}
 else if(type==1){remaining=showdownV4.remaining;vp=showdownV4.lastVPoint;}
 else if(type==4)remaining=float(mineV4.time);
 else if(type==2||type==6||type==7)remaining=trialScoreInitial-trialScoreElapsed;
 else remaining=(stageLimit-stageTime)*60;
 if(trialScoreInitial<=0)throw std::runtime_error("Scored phase lacks admitted gameplay budget");
 remaining=std::clamp(remaining,0.f,trialScoreInitial);
 resultv4::Record row;row.difficulty0=difficultyV4.logic;row.difficulty1=difficultyV4.action;row.id=id;row.type=type;row.initial=int(trialScoreInitial);row.remaining=int(remaining);row.raw=resultv4::raw(type,remaining,vp);resultv4::capture(trialResults,row);
}
void Yumeno::trialResultClear(){trialResultOn=false;trialResultPaint.clear();UI::Remove(this,"trialresultv4");}
void Yumeno::trialResultStart(bool history,const std::string& chapter){
 if(history)trialResultReturn=mode;trialResultHistory=history;trialResultChapter=chapter.empty()?trialResults.current.chapter:chapter;
 if(history&&!trialResults.best.count(trialResultChapter))return;
 if(!history)resultv4::settle(trialResults,coins,skillOn("financing"));
 // The root is owned only after Show; task teardown must not touch a cold result widget.
 trialResultOn=false;trialResultDetail=false;trialResultArmed=false;trialResultRow=trialResultFirst=0;trialResultTime=0;trialResultPaint.clear();
 if(stageShown){sclear();v4TaskRoot(false);debateHud(false);}dialogVisible(false);hideFlow();hideExplore();exworld::visible(world,false);
 UI::SetVisible(this,UI_ID,"Trial",false);UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);
 UI::Show(this,"Assets/UI/TrialResultV4.hbwidget.json","trialresultv4");trialResultOn=true;mode=Mode::Trial;if(!history)pv4::RequestMusic(presentationV4,"@silence");trialResultDraw();
}
void Yumeno::trialResultDraw(){
 if(!trialResultOn)return;const auto& r=trialResultHistory?trialResults.best.at(trialResultChapter):trialResults.current;
 const float time=trialResultHistory?5.f:trialResultTime;
 const float scoring=std::clamp((time-.25f)/2.f,0.f,1.f);
 const float deduction=std::clamp((time-2.25f)/.8f,0.f,1.f);
 const float medal=std::clamp((time-3.25f)/1.f,0.f,1.f);
 int subtotal=0;
 for(const auto& row:r.records)subtotal+=resultv4::weighted(row.raw,row.difficulty0,row.difficulty1);
 const int shown=int(subtotal*scoring+(r.total-subtotal)*deduction),award=int(r.award*medal);
 const int revealed=int(std::ceil(r.records.size()*scoring));
 const bool graded=time>=3.05f;
 std::string stamp=std::to_string(shown)+":"+std::to_string(award)+":"+std::to_string(revealed)+":"+std::to_string(trialResultRow)+":"+std::to_string(trialResultDetail)+":"+std::to_string(graded)+":"+std::to_string(time>=2.25f)+":"+std::to_string(time>=3.25f);if(stamp==trialResultPaint)return;trialResultPaint=stamp;
 auto tx=[&](const std::string& id,const std::string& value){UI::SetText(this,"trialresultv4",id,value);};
 static const auto resultLayout=Data::Get("Assets/Data/v4_story/trial_result_layout.json");
 static const char* ranks[]{"우","양","가"};static const char* rankFiles[]{"yuu","ryou","ka"};
 tx("RsHeader","학급재판 결과 · 제"+trialResultChapter+"장"+(trialResultHistory?" · 최고 기록":""));
 trialResultFirst=std::clamp(trialResultFirst,0,std::max(0,int(r.records.size())-8));
 for(int i=0;i<8;i++){int index=trialResultFirst+i;bool visible=index<revealed;for(auto p:{"RsStrip","RsNo","RsIcon","RsLabel","RsScore","RsRank"})UI::SetVisible(this,"trialresultv4",std::string(p)+std::to_string(i),visible);if(!visible)continue;
  const auto& row=r.records[index];int score=resultv4::weighted(row.raw,row.difficulty0,row.difficulty1),max=resultv4::raw(row.type,float(row.initial)),rank=resultv4::rank(score,max/2,max/4);
  auto n=std::to_string(i);tx("RsNo"+n,std::to_string(index+1));tx("RsLabel"+n,resultv4::label(row.type));tx("RsScore"+n,std::to_string(score));UI::SetColor(this,"trialresultv4","RsLabel"+n,index==trialResultRow?Color{1,.81f,.08f,1}:Color{1,1,1,1});
  const auto& icons=resultLayout.at("iconNames");
  if(row.type>=0&&row.type<int(icons.size()))UI::SetTexture(this,"trialresultv4","RsIcon"+n,"Assets/Art/ui/v3/trial_result/icon_"+icons[row.type].get<std::string>()+"_JP.png");
  UI::SetTexture(this,"trialresultv4","RsRank"+n,resultLayout["assets"].at(std::string("t_resultt_list_rank_ico_tx_")+rankFiles[rank]+"_JP.png").get<std::string>());
 }
 tx("RsPage",r.records.empty()?"기록된 미니게임이 없어요":std::to_string(trialResultRow+1)+" / "+std::to_string(r.records.size())+"  · W/S 선택 · A/D 쪽 이동");
 tx("RsTotalLabel",graded?"종합 점수":"점수 합산");tx("RsTotal",std::to_string(shown));tx("RsGrade",!graded?"":r.records.empty()?std::string("기록 없음"):std::string("종합 평가  ")+ranks[resultv4::rank(r.total,r.upper,r.middle)]);
 UI::SetVisible(this,"trialresultv4","RsMedal",time>=3.25f);
 UI::SetVisible(this,"trialresultv4","RsPenalties",time>=2.25f);
 tx("RsMedal","획득 메달  "+std::to_string(award)+(r.financing?"  ×2":""));
 tx("RsPenalties","실언  "+std::to_string(r.gaffe)+"    −"+std::to_string(std::min(r.gaffe*100,9999))+"\n재도전  "+std::to_string(r.retry)+"    −"+std::to_string(std::min(r.retry*1000,9999)));
 if(!r.records.empty()){const auto& x=r.records[trialResultRow];std::string detail=resultv4::label(x.type);detail+="\n남은 시간  "+std::to_string(x.remaining/60)+"초 / "+std::to_string(x.initial/60)+"초";
  if(trialResultDetail)detail+="\n기본 "+std::to_string(x.raw)+" × "+std::to_string(int(std::lround(resultv4::coefficient(x.difficulty0)*100)))+"% × "+std::to_string(int(std::lround(resultv4::coefficient(x.difficulty1)*100)))+"% = "+std::to_string(resultv4::weighted(x.raw,x.difficulty0,x.difficulty1));tx("RsSelected",detail);
 }else tx("RsSelected","기록된 평가 항목이 없어요.");
 tx("RsGuide",trialResultHistory?"Q 상세 보기 · Backspace 돌아가기":"Q 상세 보기 · Tab 패드 · Enter 계속");
}
bool Yumeno::trialResultUpdate(float delta){
 if(!trialResultOn)return false;
 const float previous=trialResultTime;
 trialResultTime+=delta;
 auto playReveals=[&](bool skipped){
  if(trialResultHistory)return;
  if(skipped){if(previous<3.25f)sfx("v3se_322");return;}
  if(previous<.25f&&trialResultTime>=.25f)sfx("v3se_321");
  if(previous<2.25f&&trialResultTime>=2.25f)sfx("v3se_321");
  if(previous<3.05f&&trialResultTime>=3.05f)sfx("v3se_320");
  if(previous<3.25f&&trialResultTime>=3.25f)sfx("v3se_322");
 };
 Vec2 mouse;Input::GetMousePositionForCanvas({1280,720},mouse);
 if(!trialResultArmed){if(!Input::IsKeyDown("Enter")&&!Input::IsKeyDown("Space")&&!Input::IsKeyDown("mouse0"))trialResultArmed=true;playReveals(false);trialResultDraw();return true;}
 const auto& r=trialResultHistory?trialResults.best.at(trialResultChapter):trialResults.current;int old=trialResultRow,count=int(r.records.size());
 if(count){if(pressed("w")||pressed("ArrowUp"))trialResultRow=(trialResultRow+count-1)%count;if(pressed("s")||pressed("ArrowDown"))trialResultRow=(trialResultRow+1)%count;if(pressed("a")||pressed("ArrowLeft"))trialResultRow=std::max(0,trialResultRow-8);if(pressed("d")||pressed("ArrowRight"))trialResultRow=std::min(count-1,trialResultRow+8);
  if(pressed("mouse0")&&mouse.x>=64&&mouse.x<=543&&mouse.y>=88&&mouse.y<520){int row=trialResultFirst+int((mouse.y-88)/54);if(row<count)trialResultRow=row;}
  if(trialResultRow<trialResultFirst)trialResultFirst=trialResultRow;if(trialResultRow>=trialResultFirst+8)trialResultFirst=trialResultRow-7;
 }
 if(old!=trialResultRow)sfx("ui_select");if(pressed("q")){trialResultDetail=!trialResultDetail;trialResultPaint.clear();}
 bool skipped=false;
 if(pressed("Enter")||pressed("Space")){
  if(!trialResultHistory&&trialResultTime<4.25f){trialResultTime=4.25f;skipped=true;}
  else if(!trialResultHistory){trialResultFinish();return true;}
 }
 if(trialResultHistory&&(pressed("Backspace")||pressed("Escape")||pressed("mouse1"))){trialResultFinish();return true;}
 playReveals(skipped);trialResultDraw();return true;
}
void Yumeno::trialResultFinish(){bool history=trialResultHistory;trialResultClear();if(history){mode=trialResultReturn;if(mode==Mode::Title){if(chapterSelectOn)chapterSelectDraw();else titleMenu(true);}else if(mode==Mode::Pad)padSystemDraw();return;}mode=Mode::Story;v4Enter();}
std::string Yumeno::TrialResultStats()const{return Json{{"open",trialResultOn},{"history",trialResultHistory},{"row",trialResultRow},{"first",trialResultFirst},{"elapsed",trialResultTime},{"ledger",resultv4::summary(trialResults)}}.dump();}
