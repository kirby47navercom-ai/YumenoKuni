#pragma once
#include <HBEngine/Game.hpp>
#include "DisplayV4.hpp"
#include <cmath>
#include <stdexcept>
// Keep canvas coordinates normalized even when the pointer is outside or the
// background test window is hidden; callers must not receive raw pixels then.
// Engine input/SDK files stay unchanged; raw mouse and all key APIs are inherited.
namespace gameinputv4 {
struct Input : hb::Input {
 inline static bool centeredCanvas=false;
 static bool GetMousePositionForCanvas(const hb::Vec2& reference,hb::Vec2& position){
  if(!std::isfinite(reference.x)||!std::isfinite(reference.y)||reference.x<=0||reference.y<=0)throw std::invalid_argument("invalid game canvas size");
#ifdef _WIN32
  const bool available=hb::Input::GetMousePosition(position);
  static HWND ownWindow=nullptr;if(!ownWindow||!IsWindow(ownWindow))ownWindow=displayv4::Window();RECT r{};displayv4::DpiScope dpi;
  if(ownWindow&&GetClientRect(ownWindow,&r)&&r.right>0&&r.bottom>0){float fit=std::min(float(r.right)/reference.x,float(r.bottom)/reference.y);position.x/=fit;position.y/=fit;if(centeredCanvas){position.x-=(float(r.right)/fit-reference.x)*.5f;position.y-=(float(r.bottom)/fit-reference.y)*.5f;}return available;}
#endif
  return hb::Input::GetMousePositionForCanvas(reference,position);
 }
};

}
