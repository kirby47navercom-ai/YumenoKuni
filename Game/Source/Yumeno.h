#pragma once
#include <HBEngine/Game.hpp>
#include "Debate.hpp"
#include <map>
#include <array>
#include <set>
HB_CLASS(Blueprintable)
class Yumeno : public hb::Actor {
public:
 HB_FUNCTION(BlueprintCallable) void Update(float delta);
 HB_FUNCTION(BlueprintPure) std::string Stats() const;
 HB_FUNCTION(BlueprintCallable) void DebugJump(int index);
 HB_FUNCTION(BlueprintCallable) void DebugChapter(int index);
private:
 enum class Mode{Title,Story,Pad,End,Trial,Menu,Grid,Card,Credits};
 Mode mode=Mode::Title,beforePad=Mode::Story;
 bool ready=false;
 hb::Json story,emotions,rules,trials,chapter,art,giftData,kotodama,reactions;
 int event=0;
 std::string line,speaker,portrait;
 int lineLength=0;
 float shown=0,skipTimer=0;
 // 논스톱 논의
 debate::State debate;
 std::vector<std::pair<std::string,std::string>> bullets;
 int debateAt=0,bullet=0,shownLine=-1,shownHearts=-1,shownNoise=-1,vBreaks=0;
 float messageTimer=0,cutinTimer=0,clearTimer=0,holdTime=-1,cameraFrom=0,cameraTo=0,cameraAngle=0,cameraTime=1;
 float cameraPitch=0,pitchFrom=0;
 int speakerSeat=-1,retries=0,shownStars=-1;
 float debateTime=180;
 std::map<std::string,hb::Actor*> actors;
 float aimX=640,aimY=360;
 bool lie=false,lieCost=false,enterPressed=false,spacePressed=false;
 struct GlyphCache{int visible=0;std::string text;float rotation=1e9f,opacity=-1;};
 std::map<std::string,GlyphCache> glyphCache;
 struct GlyphStyle{std::string font;float size=0,r=-1,g=-1,b=-1;};
 std::map<std::string,GlyphStyle> glyphStyle;bool noiseStyled=false;
 std::map<std::string,bool> held;
 std::map<std::string,std::string> texts;
 bool pressed(const std::string& key);
 void text(const std::string& id,const std::string& value);
 // 장 진행 (Flow.hpp)
 enum class MenuKind{Event,Investigate,Ending,Gift};enum class GridKind{Free,Gift};enum class After{None,Gift,Slot};
 MenuKind menuKind=MenuKind::Event;GridKind gridKind=GridKind::Free;After after=After::None;
 bool flowOn=false;int chapterAt=0,beat=0,ctxPool=-1,ctxSpot=-1,ctxEnding=-1,slots=0,coins=0,pulls=0,menuCount=0,padTab=0;float toastTimer=0;
 std::map<std::string,int> bonds,gifts;std::set<std::string> cards,flags,seen;std::vector<std::string> gridSlugs,giftOrder,trialDead;std::vector<int> spotOrder;
 std::string giftTarget,musicCue;std::map<std::string,std::string> ftexts;std::map<std::string,bool> fvisible;
 void ftext(const std::string& id,const std::string& v);void fvis(const std::string& id,bool v);
 std::string artPath(const std::string& group,const std::string& name,const std::string& dir,const std::string& ext)const;
 void music(const std::string& cue);int level(const std::string& slug)const;void addBond(const std::string& slug,int points);void toast(const std::string& v);void hud();
 void saveFlow();bool loadFlow();void openChapter(int index);const hb::Json& currentBeat()const;const hb::Json& flowEvents()const;bool inPark(const std::string& slug)const;
 void newGame();void hideFlow();void showStory();void nextBeat();void enterBeat();void toTitle();void flowPresent();void showLine();
 void sayOnce(const std::string& slug,const std::string& value,const std::string& pose,After then);void eventsDone();void advanceFlow();
 void showMenu(const std::string& q,const std::vector<std::string>& o,MenuKind kind);void hideMenu();int menuAt(float x,float y)const;void menuPicked(int i);
 void showFreeSelect();int poolOf(const std::string& slug)const;int gridAt(float x,float y)const;void gridPicked(int i);void pullCapsule();
 std::string giftName(const std::string& id)const;std::string reaction(const std::string& slug,const std::string& kind)const;std::string kotodamaName(const std::string& id)const;void showGifts();void giveGift(int i);void slotDone();void showInvestigate();void trialDone();void padPage();
 void updateFlow(float delta,bool next,bool click);hb::Json autoFlow()const;
 void dialogVisible(bool visible);
 void startDebate(const hb::Json& d);
 void updateDebate(float delta);
 void message(const std::string& value,float seconds);
 void showBullet();
 void styleLine();
 hb::Actor* actor(const std::string& id);
 void seatVisible(int seat,bool visible);
 void placeCamera(float angle);
 void setupCourt();
 // 재판 단계 (TrialRunner.hpp)
 struct Orb{std::string ch;float x=0,y=0,vx=0,vy=0;bool taken=false;};
 std::string trialKey="11c",lastError;hb::Json stages,stage;std::string stageKind;int stageAt=-1;bool inScript=false,playingDebate=false,restartStage=false,stageShown=false,mouseWasDown=false;
 std::vector<hb::Json> scriptLines;int scriptAt=0;
 std::vector<std::string> opts,bladeIds,personIds,pieceIds,usedPieces,anaChars;std::vector<int> scrumIds,cells,loneHits,armOrder;std::vector<bool> filledPanel;std::vector<Orb> orbs;
 int optAnswer=-1,optHover=0,optStep=0,climaxBlank=-1,sdLine=0,sdBullet=0,scPair=0,mash=-1,armLine=0,armHits=0,armFinal=-1,taxiQ=0,taxiLane=1,anaFilled=0,mineAnswer=0;
 float optY=118,optStepPx=64,optH=56,stageTime=0,stageLimit=999,stageMsgTimer=0,sdTime=0,armBeat=0,taxiDist=0,lightX=-300,spot=0,dragX=0,dragY=0;
 std::map<std::string,std::string> stexts;std::map<int,std::string> seatTexture;std::map<std::string,bool> svisible;
 void stext(const std::string& id,const std::string& v);void svis(const std::string& id,bool v);void sclear();void smsg(const std::string& v,float seconds);
 std::string nameOf(const std::string& slug)const;std::string poseTexture(const std::string& slug,const std::string& emo,const std::string& pose)const;
 void debateHud(bool on);void drawHearts();void hurt();void heal();void focusSpeaker(const std::string& slug,const std::string& texture);void updateCamera(float delta);
 void startTrial();void endTrial();void enterStage(int i);void finishStage();void beginScript();void nextScriptLine();void updateScript(float delta,bool next);
 void showOptions(const std::string& question,const std::vector<std::string>& o);int optionAt(float x,float y)const;std::vector<std::string> alive(bool withMio)const;
 void climaxOptions();void setupPlay();void optionPicked(int i);void scrumNext();void scrumPick(int i);void anaSlots();std::vector<int> mineGroup(int start)const;bool itemOpen(int item)const;void mineClick(int c);void taxiShow();
 void updateTrial(float delta);hb::Json autoAction()const;
 void scrumFormation(float t);void taxiQText();void updateTaxi(float delta);
 std::vector<std::array<float,4>> optRects;std::vector<std::string> taxiChars;
 float scrumT=1,scrumWait=0,cubeD=-1,rivalD=-1,paxD=-1,carX=640,roadT=0;int taxiGot=0,taxiPhase=0,cubeLane=1,rivalLane=0;
 void drawGlyphs(const std::string& prefix,int capacity,const std::vector<debate::Glyph>& glyphs);
};
