#pragma once
#include <array>
namespace spotlayoutv4 {
// Below the focus HUD and above the question strip, in logical 1280x720 units.
inline constexpr std::array<float,4> Rect{{192.f,108.666667f,896.f,506.666667f}};
inline std::array<float,4> imageRect(const std::string& taskId){
 static const auto aspects=hb::Data::Get("Assets/Data/v4_story/spot_image_aspects.json");
 const float aspect=aspects.is_object()?aspects.value(taskId,0.f):0.f;
 if(aspect<=0)return Rect;
 const float w=std::min(Rect[2],Rect[3]*aspect),h=std::min(Rect[3],Rect[2]/aspect);
 return {Rect[0]+(Rect[2]-w)*.5f,Rect[1]+(Rect[3]-h)*.5f,w,h};
}
}
