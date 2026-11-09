#pragma once
#include <map>
#include <string>
#include <vector>

namespace glyphdisplayv4 {
inline bool hasInk(const std::string& text){return text.find_first_not_of(" \t\r\n")!=std::string::npos;}
enum Field:unsigned {Visible=1,Text=2,Position=4,Scale=8,Rotation=16,Opacity=32};
struct Point {float x=0,y=0;bool operator==(const Point& p)const{return x==p.x&&y==p.y;}};
struct Values {bool visible=false;std::string text;Point position,scale{1,1};float rotation=0,opacity=1;};
class Batch {
 struct Node {Values desired,applied;unsigned known=0,sent=0;bool queued=false;};
 std::map<std::string,Node> nodes;std::vector<std::string> dirty;
 Node& edit(const std::string& id,unsigned field){auto& n=nodes[id];n.known|=field;if(!n.queued){n.queued=true;dirty.push_back(id);}return n;}
public:
 // External font/text handoffs invalidate only their owned glyph family.
 void invalidatePrefix(const std::string& prefix){for(auto& [id,node]:nodes)if(id.rfind(prefix,0)==0)node.sent=0;}
 void visible(const std::string& id,bool v){edit(id,Visible).desired.visible=v;}
 void text(const std::string& id,const std::string& v){edit(id,Text).desired.text=v;}
 void position(const std::string& id,Point v){edit(id,Position).desired.position=v;}
 void scale(const std::string& id,Point v){edit(id,Scale).desired.scale=v;}
 void rotation(const std::string& id,float v){edit(id,Rotation).desired.rotation=v;}
 void opacity(const std::string& id,float v){edit(id,Opacity).desired.opacity=v;}
 template<class Emit> void flush(Emit emit){
  for(const auto& id:dirty){auto& n=nodes.at(id);auto& d=n.desired;auto& a=n.applied;unsigned changed=0;
   // These leaf Text nodes have no background, decorations, bindings or input.
   // Spaces still occupy their original logical positions and hit-test indices.
   const bool shown=d.visible&&d.opacity!=0&&hasInk(d.text);
   if((n.known&Visible)&&(!(n.sent&Visible)||shown!=a.visible))changed|=Visible;
   // Keep the original logical pose while transparent. Send its latest values
   // before it becomes visible, without changing the game's glyph/timing caches.
   if(shown){
    if((n.known&Opacity)&&(!(n.sent&Opacity)||d.opacity!=a.opacity))changed|=Opacity;
    if(d.opacity!=0){
     if((n.known&Text)&&(!(n.sent&Text)||d.text!=a.text))changed|=Text;
     if((n.known&Position)&&(!(n.sent&Position)||!(d.position==a.position)))changed|=Position;
     if((n.known&Scale)&&(!(n.sent&Scale)||!(d.scale==a.scale)))changed|=Scale;
     if((n.known&Rotation)&&(!(n.sent&Rotation)||d.rotation!=a.rotation))changed|=Rotation;
    }
   }
   if(changed){auto rendered=d;rendered.visible=shown;emit(id,rendered,changed);if(changed&Visible)a.visible=shown;if(changed&Text)a.text=d.text;if(changed&Position)a.position=d.position;if(changed&Scale)a.scale=d.scale;if(changed&Rotation)a.rotation=d.rotation;if(changed&Opacity)a.opacity=d.opacity;n.sent|=changed;}
   n.queued=false;
  }
  dirty.clear();
 }
};
}
