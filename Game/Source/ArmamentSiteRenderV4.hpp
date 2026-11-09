#pragma once
#include "ArmamentSiteSourceV4.hpp"
// Only presentation. Native chart/input/HP owners decide success and failure.
namespace armsitevisual {
inline constexpr int POOL=12,LEAVES=26;
inline void hide(int pool){for(int i=0;i<LEAVES;i++)gputrialhudv4::setVisible("ArSource"+std::to_string(pool)+"_"+std::to_string(i),false);}
inline void hideAll(){for(int i=0;i<POOL;i++)hide(i);}
inline void render(int pool,int type,float age,float lead,bool done,bool success,float doneAge,bool held,float holdProgress,int mashProgress,int button,bool fever,float x,float y,float rootScale=1,float rootRotation=0,float opacity=1){
 using namespace armamentsource;
 if(pool<0||pool>=POOL)throw std::out_of_range("Original armament UI visual pool");
 if(done&&!success){hide(pool);return;}
 const std::vector<std::vector<Leaf>>* frames=nullptr;int at=0,elapsed=std::max(0,int(age*60));
 if(done){frames=type==1?&hold_out:type==2?&mash_out:&tap_out;at=std::clamp(int(doneAge*60),0,int(frames->size())-1);if(doneAge*60>=frames->size()){hide(pool);return;}}
 else if(elapsed<8){frames=type==1?&hold_in:type==2?&mash_in:&tap_in;at=std::min(elapsed,int(frames->size())-1);}
 else{frames=type==1?&hold_wait:type==2?&mash_wait:&tap_wait;at=(elapsed-8)%int(frames->size());}
 const float angle=rootRotation*3.14159265358979323846f/180.f,co=std::cos(angle),si=std::sin(angle);int used=0;
 const int timer=std::clamp(int(age/std::max(.001f,lead)*60),0,60),holdFill=std::clamp(int(holdProgress*60),0,60);
 for(const auto& leaf:frames->at(at)){
  if((leaf.kind==1&&!fever)||(leaf.kind==2&&!fever)||(leaf.kind==3&&fever)||(leaf.kind==4&&held)||(leaf.kind==5&&!held)||(leaf.kind==6&&!held)||(leaf.kind==7&&leaf.dot>=mashProgress))continue;
  if(used>=LEAVES)throw std::runtime_error("Original armament UI leaf budget exceeded");
  int tex=fever?leaf.feverTexture:leaf.texture;if(leaf.kind==3)tex=keys.at(std::clamp(button,0,3));int clip=fever?leaf.feverClip:leaf.clip;if(clip>=0)tex=clips.at(clip).at(leaf.kind==6?holdFill:timer);
  if(leaf.mirror)tex=mirrorY.at(tex);
  const auto id="ArSource"+std::to_string(pool)+"_"+std::to_string(used++);auto& node=gputrialhudv4::nodes.at(id);const float cx=(leaf.x+leaf.w/2)*rootScale,cy=(leaf.y+leaf.h/2)*rootScale,w=leaf.w*rootScale,h=leaf.h*rootScale;
  gputrialhudv4::setPosition(id,{x+cx*co-cy*si-w/2,y+cx*si+cy*co-h/2});gputrialhudv4::setSize(id,{w,h});gputrialhudv4::setRotation(id,leaf.rotation+rootRotation);gputrialhudv4::setScale(id,{1,1});gputrialhudv4::setOpacity(id,leaf.alpha*opacity);gputrialhudv4::setVisible(id,true);
  if(node.texture!=textures.at(tex))gputrialhudv4::setTexture(id,textures.at(tex));
  const auto mode=leaf.additive?"additive":"translucent";if(armvisualv4::blends[id]!=mode){hb::Components::SetString(node.actor,"SpriteRenderer","blendMode",mode);armvisualv4::blends[id]=mode;}
 }
 for(int i=used;i<LEAVES;i++)gputrialhudv4::setVisible("ArSource"+std::to_string(pool)+"_"+std::to_string(i),false);
}
}
