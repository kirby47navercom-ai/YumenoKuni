#pragma once
#include <HBEngine/Game.hpp>
#include "DisplayV4.hpp"
#include "KeyBindingsV4.hpp"
#include <cmath>
#include <stdexcept>
// Keep canvas coordinates normalized even when the pointer is outside or the
// background test window is hidden; callers must not receive raw pixels then.
// Engine input/SDK files stay unchanged; raw mouse and all key APIs are inherited.
namespace gameinputv4 {
struct Input : hb::Input {
 struct PhysicalFrame {std::string pressed;bool held=false;};
 inline static std::map<std::string,bool> physicalHeld;
 static PhysicalFrame PollPhysical(){PhysicalFrame frame;for(const auto& key:keybindv4::Candidates()){bool down=hb::Input::IsKeyDown(key);if(down&&!physicalHeld[key]&&frame.pressed.empty())frame.pressed=key;frame.held|=down;physicalHeld[key]=down;}return frame;}
 static bool IsKeyDown(const std::string& key){return hb::Input::IsKeyDown(keybindv4::Physical(key));}
 static float GetAxis(const std::string& key){return hb::Input::GetAxis(keybindv4::Physical(key));}
 static hb::Vec2 CanvasPosition(hb::Vec2 p,const hb::Vec2& size,const hb::Vec2& reference,bool centered){
  const float fit=std::min(size.x/reference.x,size.y/reference.y);
  p.x/=fit;p.y/=fit;
  if(centered){p.x-=(size.x/fit-reference.x)*.5f;p.y-=(size.y/fit-reference.y)*.5f;}
  return p;
 }
 static bool GetCenteredMousePositionForCanvas(const hb::Vec2& reference,hb::Vec2& position){return CanvasMouse(reference,position,true);}
 static bool GetMousePositionForCanvas(const hb::Vec2& reference,hb::Vec2& position){
  return CanvasMouse(reference,position,false);
 }
 static bool CanvasMouse(const hb::Vec2& reference,hb::Vec2& position,bool centered){
  if(!std::isfinite(reference.x)||!std::isfinite(reference.y)||reference.x<=0||reference.y<=0)throw std::invalid_argument("invalid game canvas size");
#ifdef _WIN32
  const bool available=hb::Input::GetMousePosition(position);
  static HWND ownWindow=nullptr;if(!ownWindow||!IsWindow(ownWindow))ownWindow=displayv4::Window();RECT r{};displayv4::DpiScope dpi;
  if(ownWindow&&GetClientRect(ownWindow,&r)&&r.right>0&&r.bottom>0){position=CanvasPosition(position,{float(r.right),float(r.bottom)},reference,centered);return available;}
#endif
  return hb::Input::GetMousePositionForCanvas(reference,position);
 }
};

}
