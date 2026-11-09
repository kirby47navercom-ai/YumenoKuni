$ErrorActionPreference='Stop'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class OwnedNativeWindow {
 public delegate bool Callback(IntPtr h,IntPtr p);
 [DllImport("user32.dll")] static extern bool EnumWindows(Callback c,IntPtr p);
 [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern int GetClassName(IntPtr h,StringBuilder b,int n);
 [DllImport("user32.dll")] static extern bool PostMessage(IntPtr h,uint m,IntPtr w,IntPtr l);
 [StructLayout(LayoutKind.Sequential)] public struct Rect {public int left,top,right,bottom;}
 [DllImport("user32.dll")] static extern bool GetClientRect(IntPtr h,out Rect r);
 [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr h,out Rect r);
 [DllImport("user32.dll")] static extern bool SetWindowPos(IntPtr h,IntPtr after,int x,int y,int w,int height,uint flags);
 [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll")] static extern bool IsIconic(IntPtr h);
 [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] static extern bool ShowWindow(IntPtr h,int command);
 [DllImport("user32.dll")] static extern int GetWindowLongW(IntPtr h,int index);
 [DllImport("user32.dll")] static extern int SetWindowLongW(IntPtr h,int index,int value);
 [DllImport("user32.dll")] static extern IntPtr MonitorFromWindow(IntPtr h,uint flags);
 [StructLayout(LayoutKind.Sequential)] public struct Monitor {public int size;public Rect bounds,work;public uint flags;}
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern bool GetMonitorInfo(IntPtr h,ref Monitor info);
 public static long[] Display(int pid,long handle){Post(pid,handle,0,0,0);var h=new IntPtr(handle);Rect r;if(!GetWindowRect(h,out r))throw new Exception("Window rectangle");var m=new Monitor();m.size=Marshal.SizeOf(m);if(!GetMonitorInfo(MonitorFromWindow(h,2),ref m))throw new Exception("Monitor rectangle");return new long[]{unchecked((uint)GetWindowLongW(h,-16)),r.left,r.top,r.right-r.left,r.bottom-r.top,m.bounds.left,m.bounds.top,m.bounds.right-m.bounds.left,m.bounds.bottom-m.bounds.top};}
 [DllImport("user32.dll")] static extern uint GetGuiResources(IntPtr process,uint flags);
 [StructLayout(LayoutKind.Sequential)] public struct Point {public int x,y;}
 [DllImport("user32.dll")] static extern bool ClientToScreen(IntPtr h,ref Point p);
 public static void Wheel(int pid,long handle,int delta,int x,int y){var p=new Point{x=x,y=y};if(!ClientToScreen(new IntPtr(handle),ref p))throw new Exception("Client conversion failed");Post(pid,handle,0x20A,((long)(delta*120))<<16,((p.y&0xffff)<<16)|(p.x&0xffff));}
 public static int[] Size(long handle){Rect r;if(!GetClientRect(new IntPtr(handle),out r))throw new Exception("Client rectangle unavailable");return new[]{r.right-r.left,r.bottom-r.top};}
 public static void Resize(int pid,long handle,int width,int height){if(width<320||width>7680||height<240||height>4320)throw new Exception("Owned resize bounds");Post(pid,handle,0,0,0);var h=new IntPtr(handle);Rect outer,inner;if(!GetWindowRect(h,out outer)||!GetClientRect(h,out inner))throw new Exception("Owned resize rectangle");if(!SetWindowPos(h,IntPtr.Zero,0,0,width+(outer.right-outer.left)-(inner.right-inner.left),height+(outer.bottom-outer.top)-(inner.bottom-inner.top),0x16))throw new Exception("Owned resize failed");}
 public static int[] Resources(int pid,long handle){Post(pid,handle,0,0,0);using(var p=System.Diagnostics.Process.GetProcessById(pid)){return new[]{(int)GetGuiResources(p.Handle,0),(int)GetGuiResources(p.Handle,1),p.HandleCount};}}
 public static bool[] State(int pid,long handle){Post(pid,handle,0,0,0);var h=new IntPtr(handle);return new[]{IsWindowVisible(h),IsIconic(h),GetForegroundWindow()==h};}
 public static bool Focus(int pid,long handle){Post(pid,handle,0,0,0);var h=new IntPtr(handle);ShowWindow(h,9);SetForegroundWindow(h);return GetForegroundWindow()==h;}
 public static void HiddenBorderless(int pid,long handle){Post(pid,handle,0,0,0);var h=new IntPtr(handle);if(IsWindowVisible(h))throw new Exception("Borderless QA requires hidden owned window");var style=GetWindowLongW(h,-16);SetWindowLongW(h,-16,unchecked((int)((uint)style&~0x00c40000u|0x80000000u)));if(!SetWindowPos(h,IntPtr.Zero,0,0,0,0,0x37))throw new Exception("Hidden borderless QA failed");}
 public static long Find(int pid){long found=0;EnumWindows((h,p)=>{uint owner;GetWindowThreadProcessId(h,out owner);var name=new StringBuilder(128);GetClassName(h,name,128);if(owner==pid && name.ToString()=="HBEngine.NativeGame"){found=h.ToInt64();return false;}return true;},IntPtr.Zero);return found;}
 public static void Post(int pid,long handle,uint message,long w,long l){uint owner;var h=new IntPtr(handle);GetWindowThreadProcessId(h,out owner);var name=new StringBuilder(128);GetClassName(h,name,128);if(owner!=pid||name.ToString()!="HBEngine.NativeGame")throw new Exception("Owned native window mismatch");if(!PostMessage(h,message,new IntPtr(w),new IntPtr(l)))throw new Exception("PostMessage failed");}
}
'@
while($line=[Console]::ReadLine()) {
 try {
  $command=$line|ConvertFrom-Json
  if($command.op -eq 'find'){$result=[OwnedNativeWindow]::Find([int]$command.pid)}
  elseif($command.op -eq 'size'){$result=[OwnedNativeWindow]::Size([long]$command.handle)}
  elseif($command.op -eq 'resize'){[OwnedNativeWindow]::Resize([int]$command.pid,[long]$command.handle,[int]$command.width,[int]$command.height);$result=$true}
  elseif($command.op -eq 'resources'){$result=[OwnedNativeWindow]::Resources([int]$command.pid,[long]$command.handle)}
  elseif($command.op -eq 'state'){$result=[OwnedNativeWindow]::State([int]$command.pid,[long]$command.handle)}
  elseif($command.op -eq 'display'){$result=[OwnedNativeWindow]::Display([int]$command.pid,[long]$command.handle)}
  elseif($command.op -eq 'focus'){$result=[OwnedNativeWindow]::Focus([int]$command.pid,[long]$command.handle)}
  elseif($command.op -eq 'hidden-borderless'){[OwnedNativeWindow]::HiddenBorderless([int]$command.pid,[long]$command.handle);$result=$true}
  elseif($command.op -eq 'wheel'){[OwnedNativeWindow]::Wheel([int]$command.pid,[long]$command.handle,[int]$command.delta,[int]$command.x,[int]$command.y);$result=$true}
  elseif($command.op -eq 'post'){[OwnedNativeWindow]::Post([int]$command.pid,[long]$command.handle,[uint32]$command.message,[long]$command.w,[long]$command.l);$result=$true}
  else{throw 'Unknown owned input operation'}
  @{id=$command.id;ok=$true;value=$result}|ConvertTo-Json -Compress
 }catch{@{id=$command.id;ok=$false;error=$_.Exception.Message}|ConvertTo-Json -Compress}
}
