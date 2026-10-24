#pragma once
#include <HBEngine/Game.hpp>
#include <map>
HB_CLASS(Blueprintable)
class Yumeno : public hb::Actor {
public:
 HB_FUNCTION(BlueprintCallable) void Update(float delta);
 HB_FUNCTION(BlueprintPure) std::string Stats() const;
private:
 enum class Mode{Title,Story,Pad,End};
 Mode mode=Mode::Title;
 bool ready=false;
 hb::Json story,emotions,rules,file;
 int fileIndex=0,scene=0,event=0;
 std::string line,speaker,portrait;
 int lineLength=0;
 float shown=0,skipTimer=0;
 std::map<std::string,bool> held;
 std::map<std::string,std::string> texts;
 bool pressed(const std::string& key);
 void text(const std::string& id,const std::string& value);
 void loadFile(int index);
 void start(int fileAt,int sceneAt,int eventAt);
 void present();
 void advance();
 void save();
};
