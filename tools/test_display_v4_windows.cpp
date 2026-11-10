#include "../Game/Source/DisplayV4.hpp"
#include <iostream>
#include <stdexcept>
int main(){
#ifdef _WIN32
 HWND w=nullptr;auto check=[](bool b,const char* why){if(!b)throw std::runtime_error(why);};
 try{displayv4::DpiScope dpi;WNDCLASSW c{};c.lpfnWndProc=DefWindowProcW;c.hInstance=GetModuleHandleW(nullptr);c.lpszClassName=L"HBEngine.NativeGame";RegisterClassW(&c);w=CreateWindowExW(0,c.lpszClassName,L"Hidden own display test",WS_OVERLAPPEDWINDOW,0,0,640,480,nullptr,nullptr,c.hInstance,nullptr);check(w,"Own hidden window");check(displayv4::Window()==w,"Window must belong to test process");auto focus=GetForegroundWindow();std::string error;
 check(displayv4::Apply(0,{960,540},error),error.c_str());RECT r{};GetClientRect(w,&r);check(r.right==960&&r.bottom==540,"Windowed client pixels");check(GetWindowLongPtrW(w,GWL_STYLE)&WS_CAPTION,"Windowed caption");
 check(displayv4::Apply(1,{1280,720},error),error.c_str());GetClientRect(w,&r);check(r.right==1280&&r.bottom==720,"Borderless client pixels");check(!(GetWindowLongPtrW(w,GWL_STYLE)&WS_CAPTION),"Borderless has no caption");check(displayv4::Apply(1,{3840,2160},error),error.c_str());GetClientRect(w,&r);check(r.right==3840&&r.bottom==2160,"Borderless4K pixels");check(displayv4::Apply(1,{1280,720},error),error.c_str());auto before=displayv4::Capture();
 check(displayv4::Apply(2,{1280,720},error),error.c_str());GetClientRect(w,&r);auto native=displayv4::Native();check(r.right==native.width&&r.bottom==native.height,"Fullscreen covers native monitor pixels");check(displayv4::Restore(before),"Restore prior window");GetClientRect(w,&r);check(r.right==1280&&r.bottom==720,"Rollback restores previous client pixels");check(!IsWindowVisible(w),"Hidden test must stay hidden");check(GetForegroundWindow()==focus,"Must never steal focus");
 check(!displayv4::Apply(1,{99999,720},error),"Reject invalid size");GetClientRect(w,&r);check(r.right==1280&&r.bottom==720,"Rejected size preserves window");
 auto sizes=displayv4::Resolutions(native);check(!sizes.empty(),"Resolution list");for(auto size:sizes)check(size.width<=7680&&size.height<=4320,"Supported bounded resolutions");auto small=displayv4::Resolutions({1920,1080});for(auto size:std::array<displayv4::Size,3>{{{3840,2160},{3440,1440},{7680,4320}}})check(std::find(small.begin(),small.end(),size)!=small.end(),"High resolutions must not be filtered by the current monitor");check(std::find(sizes.begin(),sizes.end(),native)!=sizes.end(),"Native resolution included");DestroyWindow(w);std::cout<<"PASS hidden own Win32: windowed/borderless/fullscreen, exact pixels, rollback, size validation, no focus/visibility changes\n";return 0;
 }catch(const std::exception& e){if(w)DestroyWindow(w);std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}
#else
 std::cout<<"Windows only\n";return 1;
#endif
}
