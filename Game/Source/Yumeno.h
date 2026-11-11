#pragma once
#include "MineLayoutV4.hpp"
#include "DialogueTextV4.hpp"
#include "DocumentV4.hpp"
#include <HBEngine/Game.hpp>
#include "WidgetOwnersV4.hpp"
#include "RuntimeScenesV4.hpp"
#include "Debate.hpp"
#include "NonstopLoopHintsV4.hpp"
#include "GlyphDisplayV4.hpp"
#include "Courtroom.hpp"
#include "ExploreWorld.hpp"
#include "StoryGraphV4.hpp"
#include "PresentationV4.hpp"
#include "TrialRulesV4.hpp"
#include "ArmamentRhythmV4.hpp"
#include "OptionsV4.hpp"
#include "SaveV4.hpp"
#include "TaskGraphV4.hpp"
#include "GrowthV4.hpp"
#include "PlayerProgressV4.hpp"
#include "TrialResultV4.hpp"
#include "ExploreReactionsV4.hpp"
#include "ChapterArchiveV4.hpp"
#include "MachineV4.hpp"
#include "GalleryV4.hpp"
#include "DifficultyV4.hpp"
#include "LieV4.hpp"
#include "ComicProgressV4.hpp"
#include "AimSkillsV4.hpp"
#include "ShotRecoveryV4.hpp"
#include "KotodamaFlightV4.hpp"
#include "MineOpeningV4.hpp"
#include "SilencerV4.hpp"
#include "EvidenceHintV4.hpp"
#include "TrialInputMotionV4.hpp"
#include <deque>
#include "ShowdownV4.hpp"
#include <map>
#include <array>
#include <set>
HB_CLASS(Blueprintable)
class Yumeno : public hb::GameInstance {
public:
 void Init() override;void Shutdown() override;
 HB_FUNCTION(BlueprintCallable) void Update(float delta);
 HB_FUNCTION(BlueprintPure) std::string Stats() const;
 HB_FUNCTION(BlueprintPure) std::string CourtStats() const;
 HB_FUNCTION(BlueprintPure) std::string GrowthStats() const;
 HB_FUNCTION(BlueprintPure) std::string MachineStats() const;
 HB_FUNCTION(BlueprintPure) std::string FxStats() const;
 HB_FUNCTION(BlueprintPure) std::string MapStats() const;
 HB_FUNCTION(BlueprintPure) std::string OptionsStats() const;
 HB_FUNCTION(BlueprintPure) std::string ChoiceStats() const;
 HB_FUNCTION(BlueprintPure) std::string PlayerProgressStats() const;
 HB_FUNCTION(BlueprintPure) std::string TrialAnswerStats() const;
 HB_FUNCTION(BlueprintPure) std::string TrialPickerStats() const;
 HB_FUNCTION(BlueprintPure) std::string EnvironmentStats() const;
 HB_FUNCTION(BlueprintPure) std::string TrialResultStats() const;
 HB_FUNCTION(BlueprintPure) std::string AimStats() const;
 HB_FUNCTION(BlueprintPure) std::string RhythmStats() const;
 HB_FUNCTION(BlueprintPure) std::string DocumentStats() const;
 HB_FUNCTION(BlueprintCallable) void DebugV4OutdoorFixture(int index,int phase);
 HB_FUNCTION(BlueprintCallable) void DebugPlayerProgressFixture(int xp);
 HB_FUNCTION(BlueprintCallable) void DebugJump(int index);
 HB_FUNCTION(BlueprintCallable) void DebugCourtSeat(int index);
 HB_FUNCTION(BlueprintCallable) void DebugChapter(int index);
 HB_FUNCTION(BlueprintCallable) void DebugV4Chapter(int index);
 HB_FUNCTION(BlueprintCallable) void DebugV4Task(const std::string& taskId);
 HB_FUNCTION(BlueprintCallable) void DebugV4GiftFixture();
 HB_FUNCTION(BlueprintCallable) void DebugV4ReportFixture();
 HB_FUNCTION(BlueprintCallable) void DebugV4RulesFixture();
 HB_FUNCTION(BlueprintCallable) void DebugV4CompletionFixture();
 HB_FUNCTION(BlueprintCallable) void DebugV4MapFixture();
 HB_FUNCTION(BlueprintCallable) void DebugFastRead();
 HB_FUNCTION(BlueprintCallable) void DebugV4ChoiceFixture(int count);
 HB_FUNCTION(BlueprintCallable) void DebugV4DialogueFixture(int kind);
 HB_FUNCTION(BlueprintPure) std::string DialogueStats()const;
 HB_FUNCTION(BlueprintCallable) void DebugDebateFixture(int outcome);
private:
 using UI=widgetownersv4::UI;
 using Input=gameinputv4::Input;
 enum class Mode{Title,Story,Pad,End,Trial,Menu,Grid,Card,Credits,Explore,Map,Confirm,Popup,Machine,Gallery};
 Mode mode=Mode::Title,beforePad=Mode::Story;
 machinev4::State machineV4;bool machineActive=false,machineFromGallery=false,machineArmed=false,machineHelp=false;float machineTime=0,machineRepeatTime=0;int machineRepeatCount=0,machineDirection=0;std::string machinePriorMusic;
 std::vector<std::string> machinePool()const;void machineOpen(bool fromGallery=false);void machineClose();void machineDraw();void machineUpdate(float delta);
 galleryv4::State galleryState;hb::Json galleryHead=hb::Json::object(),galleryProfileHead=hb::Json::object(),galleryRecoveryBank=hb::Json::object();galleryv4::ReadJob galleryReadJob;galleryv4::SaveJob gallerySaveJob;int gallerySavePhase=0;bool gallerySaving=false;std::set<std::string> galleryRead;std::string gallerySelected,galleryPlaying,galleryReplaySpace;std::vector<std::string> galleryReplayNodes;exworld::State galleryReplayWorld;
 bool galleryDirty=false,galleryArmed=false,galleryConfirm=false,galleryClosing=false,galleryViewer=false,galleryReplay=false,galleryPriorCourt=false,galleryReading=false;
 int galleryDepth=0,galleryTop=0,galleryRow=0,galleryFirst=0,galleryConfirmChoice=1,galleryReplayAt=0;
 void galleryInit();void galleryOpen();void galleryClose();void galleryDraw();void galleryUpdate(float delta);void galleryReadTick();void galleryGrant(const std::string& id);void galleryRecordNode(const hb::Json& node);const hb::Json& galleryRecord(const std::string& id)const;std::vector<std::string> galleryRows()const;
 void galleryConfirmDraw();int galleryCommit();void galleryView(const std::string& id);void galleryViewerClose();void galleryReplayShow();

 storyv4::State v4;
 int v4LoadPhase=0;hb::Json v4LoadPresentation,v4LoadMachine;bool v4LoadResult=false;void v4LoadTick();
 pv4::State presentationV4;
 optv4::State optionsV4;std::set<std::string> readLegacy;
 growthv4::State growthV4;hb::Json v4Documents=hb::Json::object();int padSkillRow=0,padReportPage=0,padSkillConfirm=1;std::string padSkillPurchase;bool padSkillConfirmArmed=false;void padSkillConfirmDraw();bool padSkillConfirmUpdate(bool click);bool padReportVisible=false,padSkillVisible=false;void v4ObserveGrowth();void v4SelectCourtScene();void v4PresentScene(const hb::Json& node);std::string v4RenderedCg;float v4ShotTime=0;
 bool padRulesVisible=false,padRuleSwapped=false;int padRuleTarget=0,padRuleDirection=0;float padRuleTimer=0;std::vector<std::string> padRuleIds()const;void padRulesDraw();bool padRulesUpdate(float delta,bool click);
 documentv4::State documentV4;bool v4DocumentOpen()const;void v4DocumentVisible(bool visible);void v4DocumentDraw();void v4CaptureRecords(const hb::Json& node);void v4ShowDocument(const std::string& title,const std::string& rows,const std::string& image="");
 hb::Json v4GiftCatalog,v4GiftQueue;int v4GiftMode=0,v4GiftPage=0,v4GiftQueueAt=-1;std::string v4GiftActor,v4GiftItem,v4GiftAfter;std::vector<std::string> v4GiftChoices;
 std::vector<std::string> v4FreeActors()const;growthv4::GiftContext v4GiftContext(const std::string& who)const;
 void v4GiftOpen(bool capsule=false);void v4GiftMenu(int kind);void v4GiftPick(int index);void v4GiftSay(const hb::Json& rows,const std::string& after);void v4GiftNext();void v4GiftClose();bool v4GiftUpdate(float delta,bool next,bool click);
 float optionsMouseX=-1,optionsMouseY=-1,padHintTime=0;int padHintRow=-1;
 int titleChoice=0,v4LogRow=0,v4LogCursor=0;bool v4LogOpen=false;float titleMouseX=-1,titleMouseY=-1;
 int padSystemView=0,padSystemColumn=0,padStorageRow=0,padThemeRow=0,padThemeFirst=0,padThemeSaveNo=0,padConfirmChoice=1;
 bool padSystemVisible=false,padSystemLog=false,padStorageBusy=false;float padStorageDelay=0;hb::Json padManualSlots=hb::Json::object();
 savev4::Writer padSaveWriter;hb::Json padSaveSnapshot;int padSavePhase=0;int padManualSaveStep();
 void padSystemClear();void padSystemDraw();void padSystemUpdate(float delta,bool click);void padThemeApply();void padSystemInit();
 bool padManualSave();bool padManualLoad();std::string padManualSlot()const;bool v4LogUpdate(bool click);
 int padMapMode=0,padMapGroup=0,padMapFirst=0,padMapCharacter=0;bool padMapVisible=false,padMapDragging=false;
 float padMapPanX=0,padMapPanY=0,padMapDragX=0,padMapDragY=0;std::string padMapSelected;
 void padMapClear();void padMapDraw();void padMapPaintAtlas();void padMapUpdate(float delta,bool click);void padMapTravel();void padMapFocus(const std::string& id);
 bool padMapCanTravel(const std::string& id)const;std::vector<std::string> padMapCandidates()const;hb::Json padMapPeople()const;
 bool v4SpotEligible(const hb::Json& spot)const;
 std::string v4HubNode;int v4HubPage=0;std::vector<int> v4HubChoices;
 std::string v4FreeNode,v4FreeActor;hb::Json v4FreeSpots=hb::Json::array();int v4FreeChoice=-1,v4FreeRest=-1;bool v4FreeCanGift=false,v4FreeAccepted=false;void v4FreeBegin();void v4FreeContinue();void v4FreePick(int index);bool v4FreeWorld()const;
 void v4Investigate();void v4HubMenu();void v4HubPick(int index,int clickedPerson=-1);void v4WorldUpdate(float delta,bool click);void v4WorldPlace();void v4WorldMarkers();void v4WorldAmbience();
 struct ChapterJob {chapterarchive::Entry entry;hb::Json snapshot;};chapterarchive::Index chapterEntries;std::set<std::string> chapterArchiveClaims;std::deque<ChapterJob> chapterArchiveQueue;savev4::Writer chapterArchiveWriter;
 bool chapterSelectWidgetShown=false,chapterSelectOn=false,chapterSelectArmed=false,titleHasContinue=false;int chapterSelectDepth=0,chapterSelectChapter=0,chapterSelectRow=0;std::vector<int> chapterSelectTypes;
 void chapterArchiveInit();void chapterArchiveObserve(const hb::Json& node);void chapterArchiveTick();void chapterSelectOpen();void chapterSelectClose();void chapterSelectOptions();void chapterSelectDraw();bool chapterSelectUpdate(float delta);int chapterSelectHit(float x,float y)const;int chapterSelectPartHit(float x,float y)const;int titleMenuHit(float x,float y)const;
 void titleMenu(bool visible);void updateTitle(bool click);
 difficultyv4::State difficultyV4;bool difficultyOn=false,difficultyArmed=false,difficultyLoading=false;int difficultyRow=0;std::string difficultySlot;chapterarchive::Replay chapterReplay;
 void difficultyOpen(const std::string& slot="");void difficultyDraw();void difficultyUpdate();int v4Damage(int raw);
 float v4CreditsTime=0;int v4MenuPage=0;std::vector<int> v4MenuChoices;void v4Menu();void v4MenuPick(int index);
 bool v4EndingSavePending=false;savev4::Writer v4EndingWriter;void v4EndingBegin();void v4EndingTick();void v4Credits();
 float trialEntryTime=-1.f;int trialPrepRow=0;
 void v4Start(const std::string& chapterId,bool reset=true,bool revisionPreview=false,const std::string& previewCheckpoint="",bool showStartCard=false);
 enum class ChapterCard { Start, Investigation, End };
 ChapterCard v4CardKind=ChapterCard::Start;
 bool v4CardArmed=false;
 void v4ShowChapterCard(ChapterCard kind);
 void v4Enter(bool restore=false);void v4Update(float delta,bool next,bool click);
 hb::Json v4Snapshot();bool v4Save();bool v4Load(const std::string& slot="",bool archiveReplay=false);void v4Log(bool open);void v4LogRender();hb::Json v4Auto()const;
 float skillMentalTicks=0;float maximumFocus()const;bool skillFocusTick(bool held,float delta);float trialTimeFactor()const;
 struct MineTileMotion { int oldColor=-1; float elapsed=0; };
 mineopeningv4::State mineOpeningV4;std::vector<float> mineTileAlphaV4;std::vector<int> mineTileStyleV4;std::vector<MineTileMotion> mineTileMotionV4;std::vector<int> mineBurstCellsV4;std::string mineClockV4;bool mineFocusActiveV4=false;float mineIntroV4=0,mineBurstTimeV4=0;int mineBurstColorV4=0;float mineFocusPulseV4=0,minePenaltyV4=0,mineTimeoutV4=0;int mineCursorStateV4=-1;bool mineQuestionVisibleV4=true;int minePaintAt=0;float mineSuccessTimeV4=-1;int mineSuccessPhaseV4=-1;int v4TrialHp=10000,v4TaskEntryHearts=5,v4TaskEntryHp=10000;int v4TaskHp()const;void v4ResetHearts(int hearts);
 bool v4Court=false,v4TaskActive=false,v4QueueActive=false;int v4QueueAt=-1,v4TaskLinks=0;std::uint64_t v4QueueGeneration=0;std::string v4QueueAfter,v4Judgment="refute";
 hb::Json v4Task,v4LastOutcome=hb::Json::object(),v4Queue=hb::Json::array(),v4PendingTaskResume=hb::Json::object();
 void v4TaskStart();void v4TaskPlay();void v4TaskEnd();void v4TaskRoute();
 Mode trialResultReturn=Mode::Title;
 resultv4::State trialResults;bool trialResultOn=false,trialResultHistory=false,trialResultDetail=false,trialResultArmed=false;int trialResultRow=0,trialResultFirst=0,trialScoreVPoints=0;float trialResultTime=0,trialScoreInitial=0,trialScoreElapsed=0;std::string trialResultChapter,trialResultPaint;
 void trialScoreBegin();void trialScoreCapture();void trialScoreTick(float delta);
 void trialResultStart(bool history=false,const std::string& chapter="");void trialResultDraw();void trialResultClear();bool trialResultUpdate(float delta);void trialResultFinish();
 void v4TaskQueue(const hb::Json& rows,const std::string& after);void v4TaskQueueNext();bool v4TaskQueueUpdate(float delta);
 int v4AppliedDebateMode=-1;void v4DebateMode(bool transformed);void v4TaskWrong(int variant=-1);void v4NonstopRestart();void v4TaskRoot(bool visible);void v4Reasoning();
 std::vector<std::string> v4ArmChoices;void v4ArmFinalShow();void v4ArmResponse(int index);bool v4ArmRetry();
 hb::Json armFigureStates,armDefeatFigure,armStreamBank;int armArmorPhase=-1;float armVisualTime=0,armArmorTransition=0,armVisualHit=0,armIntro=0,armFinish=0,armRatingTime=0,armFeverTicks=0,armLastIntro=0;hb::Vec2 armHitPoint{640,360};void armamentVisualStart();void armamentVisualUpdate(float delta);void armamentVisualHide();bool armamentPresentationInput(float delta);void armamentRating(trialv4::Rating rating);void armamentSites();int solutionFrameV4=-1;float solutionPendingV4=0;bool solutionConsumedV4=false;void solutionCutinFrame(int frame);bool solutionCutinInput(float delta);
 armrhythm::State armRhythmV4;void armamentRhythmStart();void armamentRhythmTick(float delta);hb::Json armamentRhythmAuto()const;
 static constexpr float ARM_FINISH_SECONDS=7.7f;void endingSourceFrame(const std::string& name,int frame,int first=0,int count=24);void endingSourceBlack(float alpha);void endingSourceClear();
 float modeEndTimeV4=-1;std::string modeEndKindV4,modeEndAfterV4,modeEndNextV4;bool climaxEndDoneV4=false;void beginModeEnding(const std::string& kind,const std::string& after,const std::string& next="");bool modeEndingInput(float delta);
 std::string fracturePhaseV4;int fractureSerialV4=0,fractureFrameV4=-1;bool fractureSupportedV4=false;void fractureControl(const std::string& phase,float time=0,float duration=1.2f);
 bool v4TrialInputArmed=false;void v4CancelInput();void v4LeaveTrial();void v4BeginCourt();
 float v4LieHeld=0;void v4LieStart();bool v4LieUpdate(float delta,bool click);
 void v4MineStart();bool v4MineUpdate(float delta,bool click);void v4ComicStart();void v4ComicShow();void v4ComicPick(int index);
 comicprogressv4::State comicProgressV4;
 hb::Json v4ComicStock=hb::Json::array();int v4ComicStockPage=0,v4ComicPlaceSlot=-1;
 hb::Json v4ComicBankV3;float v4ComicClockV3=0,v4ComicFeedbackV3=-1,v4ComicIntroTime=-1;bool v4ComicCorrectV3=false;int v4ComicFeedbackTargetV3=-1;
 void v4ComicHudV3();void v4ComicReplayDrawV3(bool dialogue=false);void v4ComicTileV3(const std::string&,const hb::Json&,bool visible);void v4ComicUnlockDrawV3();
 float v4ComicPageTurnV4=1;int v4ComicPageDirectionV4=1;void v4ComicPagePoseV4();
 hb::Json v4ComicStockAnimationV4;float v4ComicStockAnimationTimeV4=-1;
 bool v4ComicReview=false,comicShown=false,v4ComicZoom=false,v4ComicExpanded=false,v4ComicReplay=false;int v4ComicReplayAt=0;float v4ComicReplayTime=0;int v4ComicSpread=0,v4ComicCursor=0,v4ComicPlacing=-1;float v4ComicPlaceTicks=0;std::string v4ComicPage;
 void v4ComicDraw();hb::Json v4ComicAuto()const;
 void v4ComicClear();void v4ComicComplete(bool dialogue=false);bool v4ComicUpdate(float delta,bool click);void v4ComicHighlight();
 showdownv4::State showdownV4;float showdownTicks=0,showdownMouseX=0,showdownMouseY=0;int showdownShown=-1;
 void v4ShowdownExtra();void v4ShowdownBlades();void v4ShowdownStart();bool v4ShowdownUpdate(float delta,bool click,bool released);void v4ShowdownDraw();std::vector<showdownv4::Glyph> v4ShowdownGlyphs()const;hb::Json v4ShowdownAuto()const;
 reactionv4::State exploreReactions;std::string reactionWorld;int reactionAt=-1;float reactionTime=0;bool reactionCommitted=false;void exploreReactionPlace(bool targets);bool exploreReactionUpdate(float delta,int over);
 bool exploreFocusOn=false,exploreFocusReady=true;bool exploreConcentration();void exploreConcentrationOff();
 bool ready=false,gameplayReady=false,gameplayDataReady=false;
 void prepareGameplay();void releaseGameplay();void mountTrialUi(const std::string& kind);void releaseTrialUi();
 hb::Json story,emotions,rules,trials,chapter,art,giftData,kotodama,reactions,hotspotData;
 int event=0;
 std::string line,speaker,portrait;
 int lineLength=0;
 float shown=0,skipTimer=0;
 // 논스톱 논의
 debate::State debate;
 std::vector<std::pair<std::string,std::string>> bullets;
 int debateAt=0,bullet=0,shownLine=-1,shownHearts=-1,shownHeartMax=-1,shownNoise=-1,vBreaks=0;
 float messageTimer=0,cutinTimer=0,clearTimer=0,holdTime=-1,cameraFrom=0,cameraTo=0,cameraAngle=0,cameraTime=1;
 bool chargeSeOn=false;std::string chargeSe; // 누르고 있는 동안의 V3 장전음(SE341 → 반복 SE342)
 bool tugSeOn=false;std::string tugSe; // 반론 힘겨루기 반복음(SE378)
 mutable std::vector<std::array<float,2>> sdLook; /* 쇼다운 글자마다 (회전, 크기) — v4ShowdownGlyphs 가 채운다 */int sdCombo=0;bool sdAlert=false;float sdDraw=-1; /* 진실의 칼날 뽑는 중(초), -1 = 아님 */float sdIntro=-1,sdAdvT=0,sdSlashT=0,sdBreak=-1; /* 마무리 「참격」 연출 중(초) */int sdTail(const std::vector<std::string>& g)const;std::vector<std::array<std::string,2>> sdTalkWords;float sdTalkT=0;std::set<int> sdCut;std::string sdCutId;std::vector<std::array<float,8>> sdShards;std::vector<std::string> sdShardCh;std::array<float,3> sdHit{0,0,-1};float sdGap=0,sdFlash=0;std::array<float,3> sdBreakC{520,400,0};std::vector<std::array<float,5>> sdSplit;std::vector<std::string> sdSplitCh;int sdSplitN=0,sdLastGroup=-1;float sdLevel=0,sdPhaseFlash=0,sdBy=0,sdCutFx=0,sdCutAng=0;hb::Json sdDeferred=hb::Json::array(); /* 베인 글자·파편(슬롯,x,y,vx,vy,t,크기,회전)·맞은 자리 */bool sdFromStory=false,sdPreDone=false;float sdIntroPrev=-1,sdStoryCut=-1;std::string sdCutinSlug;bool sdBreakV=false;std::array<std::array<float,3>,4> sdBonus{};int sdBonusAt=0; /* 「+0.2 sec.」 (x,y,남은 초) */bool sdTalkOn=false;float sdPick=0; /* 칼날 바꾸는 중 목록 표시(초) */ /* 쇼다운 중 주인공 발언 : 화면 가득 주인공 + 하늘색 글(V3 175초) */void v4ShowdownIntro(float t);void v4ShowdownBreak(float t);
 float showdownFaceX=-1; // 쇼다운 오른쪽 주인공 위치(바뀔 때만 보낸다)
 float debateSwirl=0,debatePunch=0;int debatePunchSeat=-1;bool debateSwirlOn=false; // 다이내믹 논스톱 : 외침 뒤 소용돌이 남은 시간, 화자 튀어나옴
 std::set<int> scrumSideSeats; // 스크럼 옆모습(_SR/_SL) 입상으로 바꾼 자리 : 끝나면 되돌린다
 float cameraPitch=0,pitchFrom=0;
 float debateIntroTime=-1;int debateIntroSeat=0,debateIntroLoaded=0;bool debateInputArmed=true;
 float debateResultTime=0,shotTimeLeft=0,shotDuration=.22f,shotX=0,shotY=0;bool focusExhausted=false,shotLie=false;
 shotv4::State shotRecoveryV4;silencerv4::State silencerV4;float noiseGainTimeV4=0,noiseSeTimeV4=0;std::string noiseSeV4;int noiseBlockedShotsV4=0;
 bool v4NoiseInput(float delta);bool v4NoiseBreak(int at,int power=1);void v4NoiseReset();void v4MineHints();
 int shotsFired=0;std::string debateResult;
 static constexpr float DEBATE_RESULT_SECONDS=7.f;
 int debateResultPhase=-1,debateResultSeat=-1;court::Cam debateResultCam{};
 std::map<std::string,std::array<float,2>> debateFxValues;
 struct ResultPlane{float x=0,y=0,w=1280,h=720,depth=.18f,sx=1,sy=1,angle=0,alpha=1;bool requested=false,shown=false;std::string texture;};
 std::map<std::string,ResultPlane> resultPlanes;
 hb::Json resultPlaneData;
 void setupResultPlanes();void resultPlanePose(const std::string& id);void resultPlaneVisible(const std::string& id,bool on);
 void resultPlaneTexture(const std::string& id,const std::string& texture);void resultPlanePosition(const std::string& id,float x,float y);void resultPlaneSize(const std::string& id,float w,float h);void resultPlaneScale(const std::string& id,float x,float y);void resultPlaneRotation(const std::string& id,float angle);void resultPlaneAlpha(const std::string& id,float alpha);
 void resetDebateFx();void updateDebateFx(float delta);void debateSuccess(const std::string& result);
 hb::Json courtFigures;std::map<int,std::string> seatShownTexture;
 void courtPose(int seat,const std::string& texture);
 std::array<float,16> debateSeatOffsets{};
 void applyDebateSeats(float seconds);
 void beginDebateIntro();bool updateDebateIntro(float delta);void cancelDebateIntro();
 int speakerSeat=-1,retries=0,shownStars=-1;
 float debateTime=180;
 std::map<std::string,hb::Actor*> actors;
 float aimX=640,aimY=360;
 bool lie=false,lieCost=false,enterPressed=false,spacePressed=false;
 liev4::State lieV4;float lieV4Ticks=0;bool v4LieCommit(bool correct);
 aimskillsv4::Result aimAssistV4;aimskillsv4::Pointer aimPointerV4;aimskillsv4::Sway aimSwayV4;void v4AimAssist(bool focused);
 struct GlyphCache{int visible=0;std::string text;float rotation=1e9f,opacity=-1,x=-1e9f,y=-1e9f,s=-1;int lastLayer=0;};
 std::map<std::string,GlyphCache> glyphCache;
 glyphdisplayv4::Batch glyphDisplay;
 glyphdisplayv4::Batch panicGlyphDisplay;
 struct GlyphStyle{std::string font;float size=0,r=-1,g=-1,b=-1;};
 std::map<std::string,GlyphStyle> glyphStyle;bool noiseStyled=false;
 std::map<std::string,bool> held,keyEdges;float mouseWheelV4=0;
 void sampleInput();
 std::map<std::string,std::string> texts;
 bool pressed(const std::string& key);
 void text(const std::string& id,const std::string& value);
 // 장 진행 (Flow.hpp)
 enum class MenuKind{Event,Ending,Gift};enum class After{None,Gift,Slot,Explore,Trial};
 MenuKind menuKind=MenuKind::Event;After after=After::None;
 bool flowOn=false;int chapterAt=0,beat=0,ctxPool=-1,ctxSpot=-1,ctxEnding=-1,slots=0,coins=0,pulls=0,menuCount=0;float toastTimer=0,blink=0,kenTime=0,shakeTimer=0;bool elevatorDone=false;bool nextShown=false;
 std::map<std::string,int> bonds,gifts;std::set<std::string> cards,flags,seen,notes,giftKnown,giftNew;std::vector<std::string> gridSlugs,giftOrder,trialDead;int giftPage=0,giftHover=0,menuHover=0;
 std::string jingleHandle,jingleNext;float jingleTimer=0;bool jingleIntro=false,trialVoted=false;const hb::Json* lastSoundEvent=nullptr;
 bool hasAudio(const std::string& cue)const;float audioLen(const std::string& cue)const;void stopJingle();void playCue(const std::string& spec);void updateMusic(float delta);void eventSound(const hb::Json& e);
 std::string giftTarget,musicCue,lastBackground,sceneBackground;std::map<std::string,std::string> ftexts;std::map<std::string,bool> fvisible;
 void ftext(const std::string& id,const std::string& v);void fvis(const std::string& id,bool v);
 std::string artPath(const std::string& group,const std::string& name,const std::string& dir,const std::string& ext)const;
 void music(const std::string& cue);void sfx(const std::string& cue);int level(const std::string& slug)const;void addBond(const std::string& slug,int points);void toast(const std::string& v);void hud();
 playerprogress::State playerProgress;std::string hudImage,hudGauge,levelUpImage;void playerXp(const std::string& kind,int count=1);void playerClaim(const std::string& kind,const std::string& id);void playerWalk(float distance);void playerTick(float delta);
 trialinputmotion::ClockState trialInputClock;
 float voteIntroTicks=0,voteCommitTicks=-1,voteHostTime=0,voteMonitorTime=-1;court::Cam voteHostCamera{};int votePending=-1;
 court::Cam pickerCameraFrom{};
 int culpritDirection=0;
 int spotPending=-1;float spotLockTicks=-1,spotLockX=0,spotLockY=0;bool spotQuestion=false;
 bool trialAnswerOn=false;int trialAnswerHover=-1,trialAnswerPending=-1;float trialAnswerTicks=0,trialAnswerMarquee=0;std::string trialAnswerStamp,trialAnswerContext;
 std::vector<bool> trialAnswerConfirmed=std::vector<bool>(4,false);
 bool trialPickerShown=false,trialPickerOn=false,trialPickerQuestion=false;int trialPickerFirst=0,trialPickerPending=-1,trialPickerImage=0,trialPickerImages=0;float trialPickerTicks=0,trialPickerMarquee=0;std::string trialPickerStamp,trialPickerPrompt;
 void trialPickerStart(const std::string& question);void trialPickerDraw();void trialPickerClear();bool trialPickerInput(float delta,bool click);void trialPickerCamera();
 void trialAnswerStart(const std::string& question);void trialAnswerDraw(float delta);bool trialAnswerInput(float delta,bool click);
 bool saveFlow(bool checkpoint=false);bool loadFlow(const std::string& slot="");void openChapter(int index);const hb::Json& currentBeat()const;const hb::Json& flowEvents()const;bool inPark(const std::string& slug)const;
 void newGame();void hideFlow();void showStory();void nextBeat();void enterBeat();void toTitle();void flowPresent();void showLine();
 void sayOnce(const std::string& slug,const std::string& value,const std::string& pose,After then);void eventsDone();void advanceFlow();
 void showMenu(const std::string& q,const std::vector<std::string>& o,MenuKind kind);void hideMenu();int menuAt(float x,float y)const;void menuPicked(int i);
 void menuDraw(float delta=0);bool menuVisualUpdate(float delta);void menuAccept(int index,int route);float menuRowY(int index)const;hb::Json menuAuto(int index)const;
 int menuFirst=0,menuPending=-1,menuRoute=0,menuShownHover=-1,menuCommits=0;float menuFocusTicks=0,menuMarqueeTicks=0,menuConfirmTicks=0;std::string menuRenderStamp;std::vector<std::string> menuLabels;
 int poolOf(const std::string& slug)const;int gridAt(float x,float y)const;std::array<float,2> cellAt(int i)const;void gridPicked(int i);void pullCapsule();
 std::string giftName(const std::string& id)const;hb::Color nameColor(const std::string& slug)const;std::string reaction(const std::string& slug,const std::string& kind)const;std::string kotodamaName(const std::string& id)const;std::string kotodamaText(const std::string& id)const;void showGifts();void giveGift(int i);void slotDone();void trialDone();
 void updateFlow(float delta,bool next,bool click);hb::Json autoFlow()const;
 // 탐색 (Explore.hpp)
 exworld::State world;
 struct Obj{std::string name;int from=0,to=0;std::string who;int index=0;};
 struct Room{int spot=-1;std::string name,bg;std::vector<std::string> people;std::vector<Obj> objects;bool done=false;};
 struct Hot{float u=0,v=0;bool person=false;int object=-1;std::string who;};
 std::vector<Room> rooms;std::vector<Hot> hotspots;int roomAt=0,mapHover=0,mapReturnRoom=-1,crossOver=-1,eventEnd=-1;float panX=0,bandTimer=0,flashTimer=0,kspin=0;
 float mapMouseX=-1,mapMouseY=-1;
 std::string segmentKey,confirmWho;bool confirmYes=true;Mode popupFrom=Mode::Story;std::map<std::string,std::string> etexts;std::map<std::string,bool> evisible;
 void etext(const std::string& id,const std::string& v);void evis(const std::string& id,bool v);void hideExplore();void showMap();void renderMap();void mapPreview();bool roomDone(const Room& r)const;int mapAt(float x,float y)const;
 void enterRoom(int i);void placeRoom();int hotspotAt(float x,float y)const;std::string hotspotLabel(int i)const;void playSegment(int spot,int from,int to);void interact(int i);
 void showConfirm(const std::string& q);void confirmPicked(bool yes);void segmentDone();void enterRoomBack();void band(const std::string& kind);void kotodamaGet(const std::string& id);
 void updateExplore(float delta,bool click);hb::Json autoExplore()const;
 // 래피 패드 (Pad.hpp)
 int padIcon=0,padPageAt=-1,padRow=0,padListFirst=0,padEvidenceImage=0,padEvidenceImages=0;bool enterNow=false,padEvidenceVisible=false,padGiftVisible=false;float padMouseX=-1,padMouseY=-1;std::map<std::string,std::string> ptexts;std::map<std::string,bool> pvisible;
 void ptext(const std::string& id,const std::string& v);void pvis(const std::string& id,bool v);void padToggle(bool playCloseSound=true);void padMenu();void padHidePage();
 std::vector<std::pair<std::string,std::string>> padRows()const;void padShowPage();void padEvidenceImageDraw();void padGiftDraw();void padGiftLeave();std::string padReportActor()const;bool padReportAllowed(int index)const;int padReportPages()const;void padReportDraw();void padSkillDraw();std::vector<hb::Json> padSkills()const;void updatePad(float delta,bool click);void armNoteDraw();
 void dialogVisible(bool visible);
 void dialogueSurface(bool trial);void dialogueName();void dialoguePortrait();void dialoguePrepare();const std::string& dialogueText()const;bool dialogueFinal()const;bool dialogueAdvance();
 void dialogueCue(const std::string& delivery,bool replay);void dialogueCueTick(float delta);
 std::vector<dialoguetext::Page> dialoguePages;int dialoguePage=0;bool dialogueTrial=false,dialogueHero=false;
 float dialogueCueTime=0;
 void startDebate(const hb::Json& d);
 void updateDebate(float delta);
 void resolveDebateShot(float x,float y,const std::string& evidence,bool lieShot);
 std::string flyingEvidence,flyingLabel;
 shotv4::WordFlight flyingWord;kotodamaflightv4::Flight flyingMeshes;
 hb::Json nonstopHudLayout;float nonstopCylinderAngle=0;void drawNonstopSourceHud(float delta);
 bool flyingImpact=false;
 static constexpr float NONSTOP_FLIGHT=.24f,NONSTOP_IMPACT=.10f;
 void message(const std::string& value,float seconds);
 void showBullet();
 float trialImpactCooldown=0;bool lastTrialImpactDamage=false;void trialImpact(bool damage=true);
 std::string lastDebateWash;
 int lastDebateWashStep=16;
 bool debateFollowPosePlayed=false;
 bool debateCastTinted=false;
 void styleLine();
 hb::Actor* actor(const std::string& id);
 void seatVisible(int seat,bool visible);
 void placeCamera(float angle);void setCam(const court::Cam& c);void courtWide();bool overlayStage()const;court::Cam shotCam(int seat,float u)const;
 court::Cam cam{},whipFrom{};int shotKind=0,shotCount=0;float shotTime=0,idleYaw=0;bool courtIdle=false;
 void setupCourt();
 // 재판 단계 (TrialRunner.hpp)
 trialv4::Mine mineV4;trialv4::Scrum scrumV4;trialv4::Anagram anagramV4;trialv4::AnagramLight anagramLightV4;trialv4::Arming armingV4;trialv4::FourPieces armPiecesV4;
 std::array<int,3> armHudShown{{-1,-1,-1}};int armHudTension=-1;
 void armHudDraw();
 float minigameTicksV4=0,anagramFeedbackV4=0,anagramIntroV4=0,scrumPairElapsedV4=0;int scrumHpV4=10000;
 bool anagramWrongV4=false;
 std::string anagramWrongResponseV4;
 void anagramPresentationStart();bool anagramPresentationTick(float delta);void anagramFeedbackStart(bool wrong,bool complete);
 std::vector<bool> scrumConfirmedV4;std::vector<int> scrumChosenV4;
 std::string scrumPortraitTextureV4;int scrumPortraitSeatV4=-1;std::array<float,4> scrumPortraitRectV4{{0,0,0,0}};
 bool anagramQuestionV4=false;int anagramFocusDrawnV4=-1;std::array<int,20> anagramLitV4{};std::array<float,20> anagramScaleV4{};
 struct Orb{std::string ch;float x=0,y=0,vx=0,vy=0;bool taken=false;};
 std::string trialKey="11c",lastError;hb::Json stages,stage;std::string stageKind;int stageAt=-1;bool inScript=false,playingDebate=false,restartStage=false,stageShown=false,mouseWasDown=false;
 std::vector<hb::Json> scriptLines;int scriptAt=0;
 std::vector<std::string> opts,bladeIds,personIds,pieceIds,usedPieces,anaChars;std::vector<int> scrumIds,cells,loneHits,armOrder;std::vector<bool> filledPanel;std::vector<Orb> orbs;
 hb::Json rhythmRecent=hb::Json::array();int rhythmUpdates=0,rhythmPresses=0,rhythmJudge=0,rhythmInput=-1;
 int optAnswer=-1,optHover=0,optPage=0,optStep=0,climaxBlank=-1,sdLine=0,sdBullet=0,scPair=0,mash=-1,armLine=0,armHits=0,armFinal=-1,armQuestionPhase=0,taxiQ=0,taxiLane=1,anaFilled=0,mineAnswer=0;
 float optY=118,optStepPx=64,optH=56,stageTime=0,stageLimit=999,stageMsgTimer=0,sdTime=0,armBeat=0,taxiDist=0,lightX=-300,spot=0,dragX=0,dragY=0;
 std::map<std::string,std::string> stexts;std::map<int,std::string> seatTexture;std::map<std::string,bool> svisible;
 void stext(const std::string& id,const std::string& v);void svis(const std::string& id,bool v);void sclear();void smsg(const std::string& v,float seconds);
 std::string nameOf(const std::string& slug)const;std::string poseTexture(const std::string& slug,const std::string& emo,const std::string& pose)const;
 void debateHud(bool on);void lieView(bool on);bool lieViewOn=false;std::vector<debate::Glyph> shatterGlyphs;bool shatterUsed=false;void drawHearts();void hurt();void heal();void focusSpeaker(const std::string& slug,const std::string& texture);void updateCamera(float delta);
 void startTrial();void endTrial();void enterStage(int i);void finishStage();void beginScript();void nextScriptLine();void updateScript(float delta,bool next);
 void showOptions(const std::string& question,const std::vector<std::string>& o);int optionAt(float x,float y)const;std::vector<std::string> alive(bool withMio)const;
 std::vector<std::string> trialCgs()const;void showTrialCg(int i);std::vector<std::string> scriptCgs;void climaxOptions();void bladeList();void optionHighlight();void personShow();void voteShow();void hideVote();void spotShow();void setupPlay();void optionPicked(int i);void scrumNext();void scrumPick(int i);void anaSlots();std::vector<int> mineGroup(int start)const;bool itemOpen(int item)const;void mineClick(int c);void taxiShow();
 void updateTrial(float delta);hb::Json autoAction(int mineTarget=-1)const;
 void scrumFormation(float t,float rise=-1);void scrumDraw();void scrumFocus();void anagramOrbDraw(int i,float x,float y,float scale,bool lit);void taxiQText();void updateTaxi(float delta);
 std::vector<std::array<float,4>> optRects;std::vector<std::string> taxiChars;
 bool voteGridVisible=false;float optionMouseX=-1,optionMouseY=-1;
 bool panicViewsPublished=false;
 std::string panicLeadTask;
 std::vector<std::string> panicStorySpeakers;
 float panicLeadSplit=0;
 int panicLeadCount=0;
 std::vector<std::string> panicWho;hb::Json skillData;int correctCount=0,maxHearts=5;bool reviveUsed=false,sdGuardUsed=false,missGuardUsed=false,resultPending=false;
 std::vector<hb::Json> equippedSkills()const;bool skillOn(const std::string& effect)const;void onCorrect();void showResult();std::string slotWho;float slotTimer=0,slotHold=0;int voteResultTick=-1;void voteResultShow();void voteResultUpdate(float progress);
 float scv3Op=-1,scv3Team=-1,scv3PushT=-1,scv3Prev=0,scv3RespT=0;int scv3Resp=-1;std::string scv3Focus;hb::Json scv3Lines=hb::Json::array(); /* 논의 스크럼 V3(V4ScrumV3.hpp) */
 void scv3Box(const std::string& id,float cx,float cy,float w,float h,float op,float rot=0);void scv3HideAll();const hb::Json& scv3Task()const;bool scv3OpIntro(float t);bool scv3TeamIntro(float t);void scv3Emblem(bool on,float t,float dx=0);void scv3Clock(float left);void scv3Claim(const std::string& text,bool speakerLeft,bool plain=false);std::vector<bool> scv3Revealed;bool scv3PushCutin(float t);void scv3PushButton(int direction,float phaseT,bool on);void scv3Respond(float delta);void scv3Speaker(const std::string& slug,bool left);void scv3PlayCam();std::string scv3PushSlug()const;std::string scv3CutKey,scv3PrevKey;bool scv3CutLeft=true,scv3PrevLeft=true;float scv3CutT=0,scv3PrevT=0,scv3CutClock=0;
 float scrumT=1,scrumWait=0,cubeD=-1,rivalD=-1,paxD=-1,carX=640,roadT=0;int taxiGot=0,taxiPhase=0,cubeLane=1,rivalLane=0;
 void drawGlyphs(const std::string& prefix,int capacity,const std::vector<debate::Glyph>& glyphs);
 void drawPanicLanes(bool visible);
};
