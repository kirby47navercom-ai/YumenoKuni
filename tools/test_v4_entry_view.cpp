#include "../Game/Source/ExploreWorld.hpp"
#include <cassert>
#include <fstream>
#include <iostream>
int main(){
 using J=hb::Json;
 J extension;std::ifstream("art/space_v4/dedicated_v1/world_extension.json")>>extension;
 auto original=extension["spaces"]["garden_rest_area"],corrected=original;
 corrected["entry_yaw"]=50;
 auto p=exworld::entryPose(original),q=exworld::entryPose(corrected);
 assert(p.yaw==0&&q.yaw==50&&p.x==q.x&&p.y==q.y&&p.z==q.z&&p.pitch==q.pitch);
 float x,y,depth;auto bench=original["targets"][0]["p"];
 assert(court::screen({p.x,p.y,p.z,p.yaw,p.pitch,0},bench[0],bench[1],bench[2],x,y,depth));
 assert(x<0); // Previously the subject of the drawing was outside the frame.
 assert(court::screen({q.x,q.y,q.z,q.yaw,q.pitch,0},bench[0],bench[1],bench[2],x,y,depth));
 assert(x>250&&x<1000&&y>0&&y<548);
 for(auto& [id,spec]:extension["spaces"].items()){
  auto a=exworld::entryPose(spec);assert(a.yaw==0&&a.pitch==0);
  auto extreme=spec;extreme["entry_yaw"]=999;extreme["entry_pitch"]=-999;
  auto b=exworld::entryPose(extreme);assert(b.yaw==spec["yaw_limits"][1]&&b.pitch==spec["pitch_limits"][0]);
 }
 std::cout<<"Entry yaw defaults preserved, authored yaw/pitch clamped, garden bench visible above dialogue.\n";
}
