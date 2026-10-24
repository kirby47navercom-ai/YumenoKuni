#pragma once
#include <HBEngine/Game.hpp>
#include "Debate.hpp"
#include <map>
HB_CLASS(Blueprintable)
class Yumeno : public hb::Actor {
public:
 HB_FUNCTION(BlueprintCallable) void Update(float delta);
 HB_FUNCTION(BlueprintPure) std::string Stats() const;
private:
 enum class Mode{Title,Story,Pad,End,Trial};
 Mode mode=Mode::Title,beforePad=Mode::Story;
 bool ready=false;
 hb::Json story,emotions,rules,file,trials;
 int fileIndex=0,scene=0,event=0;
 std::string line,speaker,portrait;
 int lineLength=0;
 float shown=0,skipTimer=0;
 // 논스톱 논의
 debate::State debate;
 std::vector<std::pair<std::string,std::string>> bullets;
 int debateAt=0,bullet=0,shownLine=-1,shownHearts=-1,shownNoise=-1,vBreaks=0;
 float messageTimer=0,cutinTimer=0,clearTimer=0,holdTime=-1,cameraFrom=0,cameraTo=0,cameraAngle=0,cameraTime=1;
 int speakerSeat=-1,retries=0,shownStars=-1;
 float debateTime=180;
 std::map<std::string,hb::Actor*> actors;
 float aimX=640,aimY=360;
 bool lie=false;
 struct GlyphCache{int visible=0;std::string text;float rotation=1e9f,opacity=-1;};
 std::map<std::string,GlyphCache> glyphCache;
 std::map<std::string,bool> held;
 std::map<std::string,std::string> texts;
 bool pressed(const std::string& key);
 void text(const std::string& id,const std::string& value);
 void loadFile(int index);
 void start(int fileAt,int sceneAt,int eventAt);
 void present();
 void advance();
 void save();
 void dialogVisible(bool visible);
 void startDebate(int at);
 void updateDebate(float delta);
 void message(const std::string& value,float seconds);
 void showBullet();
 void styleLine();
 hb::Actor* actor(const std::string& id);
 void seatVisible(int seat,bool visible);
 void placeCamera(float angle);
 void setupCourt();
 void drawGlyphs(const std::string& prefix,int capacity,const std::vector<debate::Glyph>& glyphs);
};
