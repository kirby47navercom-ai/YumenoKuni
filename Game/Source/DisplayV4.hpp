#pragma once
#include <algorithm>
#include <array>
#include <string>
#include <vector>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <tlhelp32.h>
// Windows compatibility macros collide with the engine's object API and camera names.
#undef GetObject
#undef near
#undef far
#endif
namespace displayv4 {
struct Size {int width=1280,height=720;bool operator==(const Size& b)const{return width==b.width&&height==b.height;}};
inline std::vector<Size> Resolutions(Size native){
 std::vector<Size> out;for(auto p:std::array<Size,14>{{{960,540},{1280,720},{1600,900},{1920,1080},{2560,1080},{2560,1440},{2560,1600},{3440,1440},{3840,1600},{3840,2160},{5120,1440},{5120,2160},{5120,2880},{7680,4320}}})out.push_back(p);
 if(std::find(out.begin(),out.end(),native)==out.end())out.push_back(native);
 std::sort(out.begin(),out.end(),[](Size a,Size b){return a.width*a.height<b.width*b.height;});return out;
}
#ifdef _WIN32
// Only this module's own process ancestry can supply the packaged game window.
inline HWND Window(){
 DWORD pid=GetCurrentProcessId();std::vector<DWORD> ancestors{pid};HANDLE snapshot=CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS,0);if(snapshot==INVALID_HANDLE_VALUE)return nullptr;
 PROCESSENTRY32W p{};p.dwSize=sizeof(p);std::vector<std::pair<DWORD,DWORD>> parents;if(Process32FirstW(snapshot,&p))do{parents.push_back({p.th32ProcessID,p.th32ParentProcessID});}while(Process32NextW(snapshot,&p));CloseHandle(snapshot);
 for(int i=0;i<4;i++){auto at=std::find_if(parents.begin(),parents.end(),[&](auto q){return q.first==pid;});if(at==parents.end()||!at->second||at->second==pid)break;pid=at->second;ancestors.push_back(pid);}
 // The native renderer may be a sibling of the C++ worker. Choose the
 // nearest shared session ancestor, never an unrelated game/editor window.
 struct Search{std::vector<DWORD>* ids;std::vector<std::pair<DWORD,DWORD>>* parents;HWND window=nullptr;int rank=99;}search{&ancestors,&parents};
 EnumWindows([](HWND w,LPARAM data)->BOOL{auto& s=*reinterpret_cast<Search*>(data);wchar_t name[128]{};GetClassNameW(w,name,128);if(std::wstring(name)!=L"HBEngine.NativeGame")return TRUE;DWORD owner=0;GetWindowThreadProcessId(w,&owner);
  for(int depth=0;owner&&depth<12;depth++){auto same=std::find(s.ids->begin(),s.ids->end(),owner);if(same!=s.ids->end()){int rank=int(same-s.ids->begin());if(rank<=2&&rank<s.rank){s.window=w;s.rank=rank;}break;}auto parent=std::find_if(s.parents->begin(),s.parents->end(),[&](auto p){return p.first==owner;});if(parent==s.parents->end()||parent->second==owner)break;owner=parent->second;}return TRUE;
 },reinterpret_cast<LPARAM>(&search));return search.window;
}
struct DpiScope {
 using Change=HANDLE(WINAPI*)(HANDLE);Change change=nullptr;HANDLE prior=nullptr;
 DpiScope(){change=reinterpret_cast<Change>(GetProcAddress(GetModuleHandleW(L"user32.dll"),"SetThreadDpiAwarenessContext"));if(change)prior=change(reinterpret_cast<HANDLE>(-4));}
 ~DpiScope(){if(change&&prior)change(prior);}
};
struct Snapshot {HWND window=nullptr;LONG_PTR style=0;RECT rect{};bool valid=false;};
inline Snapshot Capture(){DpiScope dpi;Snapshot s;s.window=Window();if(!s.window)return s;s.style=GetWindowLongPtrW(s.window,GWL_STYLE);s.valid=GetWindowRect(s.window,&s.rect);return s;}
inline MONITORINFO Monitor(HWND w){MONITORINFO info{};info.cbSize=sizeof(info);GetMonitorInfoW(MonitorFromWindow(w,MONITOR_DEFAULTTONEAREST),&info);return info;}
inline Size Native(){DpiScope dpi;auto m=Monitor(Window());return {m.rcMonitor.right-m.rcMonitor.left,m.rcMonitor.bottom-m.rcMonitor.top};}
inline bool Style(HWND w,LONG_PTR style){SetLastError(0);auto prior=SetWindowLongPtrW(w,GWL_STYLE,style);return prior!=0||GetLastError()==0;}
inline bool Restore(const Snapshot& s){if(!s.valid||!IsWindow(s.window)||Window()!=s.window)return false;DpiScope dpi;return Style(s.window,s.style)&&SetWindowPos(s.window,nullptr,s.rect.left,s.rect.top,s.rect.right-s.rect.left,s.rect.bottom-s.rect.top,SWP_NOZORDER|SWP_NOACTIVATE|SWP_FRAMECHANGED);}
inline bool Apply(int mode,Size resolution,std::string& error){
 if(mode<0||mode>2||resolution.width<320||resolution.width>7680||resolution.height<240||resolution.height>4320){error="지원하지 않는 화면 설정이에요.";return false;}
 auto before=Capture();if(!before.valid){error="게임 창을 찾지 못했어요.";return false;}DpiScope dpi;auto m=Monitor(before.window);if(m.rcMonitor.right<=m.rcMonitor.left){error="모니터 정보를 읽지 못했어요.";return false;}
 LONG_PTR style=before.style&~(WS_OVERLAPPEDWINDOW|WS_POPUP|WS_MINIMIZE|WS_MAXIMIZE);style|=mode==0?WS_OVERLAPPEDWINDOW:WS_POPUP;
 RECT r{0,0,resolution.width,resolution.height};int x=0,y=0;
 if(mode==2){r=m.rcMonitor;x=r.left;y=r.top;}else{
  if(mode==0){using Adjust=BOOL(WINAPI*)(LPRECT,DWORD,BOOL,DWORD,UINT);using Dpi=UINT(WINAPI*)(HWND);auto adjust=reinterpret_cast<Adjust>(GetProcAddress(GetModuleHandleW(L"user32.dll"),"AdjustWindowRectExForDpi"));auto dpiFor=reinterpret_cast<Dpi>(GetProcAddress(GetModuleHandleW(L"user32.dll"),"GetDpiForWindow"));const auto ex=DWORD(GetWindowLongPtrW(before.window,GWL_EXSTYLE));if(adjust&&dpiFor)adjust(&r,DWORD(style),FALSE,ex,dpiFor(before.window));else AdjustWindowRectEx(&r,DWORD(style),FALSE,ex);}
  const auto area=mode==0?m.rcWork:m.rcMonitor;x=area.left+(area.right-area.left-(r.right-r.left))/2;y=std::max(area.top,area.top+(area.bottom-area.top-(r.bottom-r.top))/2);
 }
 if(!Style(before.window,style)||!SetWindowPos(before.window,nullptr,x,y,r.right-r.left,r.bottom-r.top,SWP_NOZORDER|SWP_NOACTIVATE|SWP_FRAMECHANGED)){Restore(before);error="화면 설정을 적용하지 못했어요.";return false;}
 RECT client{};const auto expected=mode==2?Size{m.rcMonitor.right-m.rcMonitor.left,m.rcMonitor.bottom-m.rcMonitor.top}:resolution;
 if(!GetClientRect(before.window,&client)||client.right!=expected.width||client.bottom!=expected.height){Restore(before);error="현재 화면에서 이 해상도를 적용하지 못했어요.";return false;}error.clear();return true;
}
#else
struct Snapshot{bool valid=false;};inline Snapshot Capture(){return {};}
inline Size Native(){return {1920,1080};}inline bool Restore(const Snapshot&){return false;}
inline bool Apply(int,Size,std::string& error){error="현재 플랫폼에서 창 설정을 지원하지 않아요.";return false;}
#endif
inline std::string Label(Size p){return std::to_string(p.width)+" × "+std::to_string(p.height);}
}
