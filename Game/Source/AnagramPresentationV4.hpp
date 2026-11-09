#pragma once

void Yumeno::anagramPresentationStart(){
 anagramIntroV4=2.8f;
 anagramWrongV4=false;
 anagramWrongResponseV4.clear();
 for(auto id:{"AnaIntroEcho","AnaIntroBlur","AnaIntroRays","AnaEndBlack","AnaEndComplete"})svis(id,false);
 for(int i=0;i<48;i++)svis("AnaShard"+std::to_string(i),false);
 for(auto id:{"AnaIntroDim","AnaIntroTitle","AnaIntroLit","AnaIntroSubtitle","AnaFeedback","AnaResultBand","AnaResultFace","AnaResultWord","AnaResultCrack"})svis(id,false);
 for(auto id:{"AnaBackground","AnaSilhouette","AnaLight","AnaSpot","AnaAnswerLabel","AnaTimeLabel","AnaTime","AnaQuestionButton","AnaAim","AnaStatus"})svis(id,false);
 for(int i=0;i<20;i++){
  for(auto prefix:{"AnaBall","Orb","AnaSlot","AnaSlotBack","AnaHeart"})svis(std::string(prefix)+std::to_string(i),false);
  if(i<10)svis("AnaStar"+std::to_string(i),false);
 }
}

void Yumeno::anagramFeedbackStart(bool wrong,bool complete){
 anagramWrongV4=wrong;
 anagramFeedbackV4=complete?6.2f:wrong?.78f:.62f;
 UI::SetTexture(this,"anagramv4","AnaFeedback",wrong?"Assets/Art/ui/anagram_feedback_wrong.svg":"Assets/Art/ui/anagram_feedback_correct.svg");
}

bool Yumeno::anagramPresentationTick(float delta){
 auto alpha=[&](const char* id,float value){
  svis(id,value>.005f);
  if(value>.005f)UI::SetOpacity(this,"anagramv4",id,value);
 };
 if(anagramIntroV4>0){
  stageTime-=delta;
  const float previous=2.8f-anagramIntroV4;
  anagramIntroV4=std::max(0.f,anagramIntroV4-delta);
  const float t=2.8f-anagramIntroV4;
  if(previous<1.25f&&t>=1.25f){
   for(auto id:{"AnaBackground","AnaSilhouette","AnaAnswerLabel","AnaTimeLabel","AnaTime","AnaQuestionButton","AnaStatus"})svis(id,true);
   svis("AnaQuestionButton",!stage.value("question",std::string()).empty());
   for(int i=0;i<20;i++){svis("AnaBall"+std::to_string(i),true);svis("AnaHeart"+std::to_string(i),i<maxHearts*2);if(i<10)svis("AnaStar"+std::to_string(i),true);}
   anaSlots();
  }
  const float in=court::smooth5(t/.16f),out=court::smooth5((t-1.7f)/.65f),lit=court::smooth5((t-1.3f)/.16f);
  // Keep the title over the court, close to black, then reveal the puzzle behind its flash.
  alpha("AnaIntroDim",court::smooth5((t-.5f)/.65f)*(1-court::smooth5((t-1.25f)/.18f)));
  alpha("AnaIntroTitle",in*(1-lit));
  alpha("AnaIntroLit",lit*(1-out));
  alpha("AnaIntroSubtitle",in*(1-out));
  alpha("AnaIntroBlur",lit*(1-out)*.8f);
  alpha("AnaIntroEcho",lit*(1-out)*.65f);
  alpha("AnaIntroRays",court::smooth5((t-1.25f)/.16f)*(1-court::smooth5((t-1.75f)/.4f)));
  const float entry=1+.35f*(1-in),scale=entry+.48f*out;
  UI::SetPosition(this,"anagramv4","AnaIntroTitle",{640-652*entry,368-404*entry});
  UI::SetSize(this,"anagramv4","AnaIntroTitle",{1304*entry,808*entry});
  UI::SetPosition(this,"anagramv4","AnaIntroLit",{640-652*scale,368-404*scale});
  UI::SetSize(this,"anagramv4","AnaIntroLit",{1304*scale,808*scale});
  for(auto id:{"AnaIntroBlur","AnaIntroEcho"}){const float k=scale+(id==std::string("AnaIntroEcho")?.28f:.1f)*out;UI::SetPosition(this,"anagramv4",id,{640-652*k,368-404*k});UI::SetSize(this,"anagramv4",id,{1304*k,808*k});}
  if(anagramIntroV4==0){svis("AnaLight",true);svis("AnaAim",true);}
  return true;
 }
 if(anagramFeedbackV4<=0)return false;
 stageTime-=delta;
 const bool complete=anagramV4.state==trialv4::Result::Complete;
 const float duration=complete?6.2f:anagramWrongV4?.78f:.62f;
 const float previous=duration-anagramFeedbackV4;
 anagramFeedbackV4=std::max(0.f,anagramFeedbackV4-delta);
 const float t=duration-anagramFeedbackV4;
 const float pulse=court::smooth5(t/.09f)*(1-court::smooth5((t-.35f)/.25f));
 alpha("AnaFeedback",pulse);
 if(complete){
  fractureControl(t<3.f?"off":t<3.31f?"capture":t<4.51f?"animate":"off",t-3.31f);
  for(auto id:{"AnaResultBand","AnaResultFace","AnaResultWord"})alpha(id,0);
  const float solutionBegin=.35f,solutionEnd=solutionBegin+armingfinish::frames.size()/60.f;
  solutionCutinFrame(t>=solutionBegin&&t<solutionEnd?int((t-solutionBegin)*60):-1);
  alpha("AnaResultCrack",0);endingSourceFrame("crack",t>=3.13f&&t<3.53f?int((t-3.13f)*60):-1);
  if(previous<3.13f&&t>=3.13f)sfx("sfx_glass");
  if(previous<3.31f&&t>=3.31f){
   for(auto id:{"AnaBackground","AnaSilhouette","AnaLight","AnaSpot","AnaAim","AnaAnswerLabel","AnaTimeLabel","AnaTime","AnaQuestionButton","AnaQuestion","AnaStatus"})svis(id,false);
   for(int i=0;i<20;i++){for(auto prefix:{"AnaBall","Orb","AnaSlot","AnaSlotBack","AnaHeart"})svis(std::string(prefix)+std::to_string(i),false);if(i<10)svis("AnaStar"+std::to_string(i),false);}
   sfx("sfx_break");
  }
  alpha("AnaEndBlack",0);endingSourceBlack(t>=3.31f?1.f:0.f);
  const float shatter=std::clamp((t-3.31f)/.9f,0.f,1.f);
  if(t>=3.31f&&t<4.33f&&!fractureSupportedV4){
   static const auto layout=Data::Get("Assets/Data/gpu_anagram_layout.json").at("shards");
   int i=0;for(const auto& shard:layout){auto id=shard.at("id").get<std::string>();const auto& r=shard.at("rect");float x=r[0],y=r[1],w=r[2],h=r[3],dx=x+w*.5f-640,dy=y+h*.5f-360;const float flight=shatter*shatter*(1.7f+(i%5)*.12f);svis(id,true);UI::SetPosition(this,"anagramv4",id,{x+dx*flight,y+dy*flight+160*shatter*shatter});UI::SetRotation(this,"anagramv4",id,((i%2)?1.f:-1.f)*(25+(i%7)*13)*shatter);UI::SetOpacity(this,"anagramv4",id,1-court::smooth5((shatter-.65f)/.35f));i++;}
  }else for(int i=0;i<48;i++)svis("AnaShard"+std::to_string(i),false);
  alpha("AnaEndComplete",0);endingSourceFrame("complete",t>=3.31f&&t<4.38f?int((t-3.31f)*60):-1,24);
 }
 if(anagramFeedbackV4==0){
  solutionCutinFrame(-1);endingSourceClear();
  for(auto id:{"AnaFeedback","AnaResultBand","AnaResultFace","AnaResultWord","AnaResultCrack","AnaEndBlack","AnaEndComplete"})svis(id,false);
  if(complete){debate.hearts=std::max(1,(anagramV4.hp+1999)/2000);beginScript();}
  else if(!anagramWrongResponseV4.empty()){
   auto response=anagramWrongResponseV4;anagramWrongResponseV4.clear();
   v4TaskQueue(Json::array({Json{{"text",response},{"actor","mio"},{"speaker","미오"},{"mono",true},{"id",v4Task.value("taskId",std::string())+":wrong-anagram"}}}),"resume");
  }
 }
 return true;
}
