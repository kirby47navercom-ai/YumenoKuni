// QA-only capture of the exact owned player HWND; never a monitor/desktop.
// API contract: Microsoft Learn CreateFreeThreaded and CreateForWindow.
#define NOMINMAX
#include <windows.h>
#include <d3d11.h>
#include <dxgi.h>
#include <windows.graphics.capture.interop.h>
#include <windows.graphics.directx.direct3d11.interop.h>
#include <winrt/Windows.Foundation.h>
#include <winrt/Windows.Graphics.Capture.h>
#include <winrt/Windows.Graphics.DirectX.h>
#include <winrt/Windows.Graphics.DirectX.Direct3D11.h>
#include <io.h>
#include <fcntl.h>
#include <cstdio>
#include <atomic>
#include <chrono>
#include <stdexcept>
#include <vector>
using namespace winrt;
using namespace winrt::Windows::Graphics::Capture;
using namespace winrt::Windows::Graphics::DirectX;
using namespace winrt::Windows::Graphics::DirectX::Direct3D11;
static void bytes(const void* p,size_t n){if(fwrite(p,1,n,stdout)!=n)throw std::runtime_error("Encoder pipe closed");}
int wmain(int argc,wchar_t** argv){
 HWND window=nullptr;LONG_PTR oldStyle=0;RECT oldRect{};bool background=false;
 try{
  if(argc<4)throw std::runtime_error("usage: owned-window-wgc PID HWND frames [--background]");
  const DWORD expected=std::stoul(argv[1]);window=reinterpret_cast<HWND>(std::stoull(argv[2]));int limit=std::stoi(argv[3]);
  DWORD actual=0;GetWindowThreadProcessId(window,&actual);wchar_t cls[128]{};GetClassNameW(window,cls,128);
  if(actual!=expected||wcscmp(cls,L"HBEngine.NativeGame")||limit<1||limit>18000)throw std::runtime_error("Exact owned native player required");
  SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2);
  background=argc>4&&wcscmp(argv[4],L"--background")==0;
  if(background){
   if(IsWindowVisible(window))throw std::runtime_error("Background proof starts with hidden owned window");
   oldStyle=GetWindowLongPtrW(window,GWL_EXSTYLE);GetWindowRect(window,&oldRect);
   SetWindowLongPtrW(window,GWL_EXSTYLE,oldStyle|WS_EX_TOOLWINDOW|WS_EX_NOACTIVATE);
   // No activation, no foreground and no desktop pixels. Off-screen own HWND.
   if(!SetWindowPos(window,HWND_BOTTOM,-20000,-20000,0,0,SWP_NOSIZE|SWP_NOACTIVATE|SWP_SHOWWINDOW))throw std::runtime_error("Owned background placement failed");
  }
  init_apartment(apartment_type::multi_threaded);
  if(!GraphicsCaptureSession::IsSupported())throw std::runtime_error("Windows capture unsupported");
  com_ptr<ID3D11Device> d3d;com_ptr<ID3D11DeviceContext> context;
  check_hresult(D3D11CreateDevice(nullptr,D3D_DRIVER_TYPE_HARDWARE,nullptr,D3D11_CREATE_DEVICE_BGRA_SUPPORT,nullptr,0,D3D11_SDK_VERSION,d3d.put(),nullptr,context.put()));
  auto dxgi=d3d.as<IDXGIDevice>();com_ptr<IInspectable> inspectable;
  check_hresult(CreateDirect3D11DeviceFromDXGIDevice(dxgi.get(),inspectable.put()));auto device=inspectable.as<IDirect3DDevice>();
  auto interop=get_activation_factory<GraphicsCaptureItem,IGraphicsCaptureItemInterop>();GraphicsCaptureItem item{nullptr};
  check_hresult(interop->CreateForWindow(window,guid_of<GraphicsCaptureItem>(),put_abi(item)));
  auto size=item.Size();auto pool=Direct3D11CaptureFramePool::CreateFreeThreaded(device,DirectXPixelFormat::B8G8R8A8UIntNormalized,2,size);
  std::atomic<bool> arrived=false;auto token=pool.FrameArrived([&](auto const&,auto const&){arrived=true;});
  auto session=pool.CreateCaptureSession(item);session.IsCursorCaptureEnabled(false);session.StartCapture();
  struct UiSearch{HWND owner,result;DWORD pid;};UiSearch uiSearch{window,nullptr,expected};
  EnumWindows([](HWND h,LPARAM value)->BOOL{auto& search=*reinterpret_cast<UiSearch*>(value);DWORD pid=0;GetWindowThreadProcessId(h,&pid);wchar_t name[64]{};GetClassNameW(h,name,64);if(pid==search.pid&&GetWindow(h,GW_OWNER)==search.owner&&!_wcsicmp(name,L"STATIC")&&(GetWindowLongPtrW(h,GWL_EXSTYLE)&WS_EX_LAYERED)){search.result=h;return FALSE;}return TRUE;},reinterpret_cast<LPARAM>(&uiSearch));
  if(!uiSearch.result)throw std::runtime_error("Exact owned UI overlay not found");
  for(int i=0;i<100&&!IsWindowVisible(uiSearch.result);i++)Sleep(10);
  GraphicsCaptureItem uiItem{nullptr};check_hresult(interop->CreateForWindow(uiSearch.result,guid_of<GraphicsCaptureItem>(),put_abi(uiItem)));
  auto uiPool=Direct3D11CaptureFramePool::CreateFreeThreaded(device,DirectXPixelFormat::B8G8R8A8UIntNormalized,2,uiItem.Size());std::atomic<bool> uiArrived=false;auto uiToken=uiPool.FrameArrived([&](auto const&,auto const&){uiArrived=true;});auto uiSession=uiPool.CreateCaptureSession(uiItem);uiSession.IsCursorCaptureEnabled(false);uiSession.StartCapture();
  com_ptr<ID3D11Texture2D> uiStaging;D3D11_TEXTURE2D_DESC uiDesc{};std::vector<BYTE> uiPixels;int alphaMin=255,alphaMax=0;
  _setmode(_fileno(stdout),_O_BINARY);const auto begin=std::chrono::steady_clock::now();auto lastEmitted=begin-std::chrono::seconds(1);int frames=0;long long firstUnixMS=0,lastUnixMS=0;com_ptr<ID3D11Texture2D> staging;D3D11_TEXTURE2D_DESC cached{};std::vector<BYTE> worldPixels;
  while(frames<limit){
   if(argc>5&&frames>0&&GetFileAttributesW(argv[5])!=INVALID_FILE_ATTRIBUTES)break;
   if(std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count()>10+limit/15.0)break;
   if(uiArrived.exchange(false)){
    auto uf=uiPool.TryGetNextFrame();if(uf){auto access=uf.Surface().as<::Windows::Graphics::DirectX::Direct3D11::IDirect3DDxgiInterfaceAccess>();com_ptr<ID3D11Texture2D> texture;check_hresult(access->GetInterface(__uuidof(ID3D11Texture2D),texture.put_void()));D3D11_TEXTURE2D_DESC desc{};texture->GetDesc(&desc);if(!uiStaging||desc.Width!=uiDesc.Width||desc.Height!=uiDesc.Height){uiDesc=desc;desc.Usage=D3D11_USAGE_STAGING;desc.BindFlags=0;desc.CPUAccessFlags=D3D11_CPU_ACCESS_READ;desc.MiscFlags=0;uiStaging=nullptr;check_hresult(d3d->CreateTexture2D(&desc,nullptr,uiStaging.put()));uiPixels.resize(uiDesc.Width*uiDesc.Height*4);}context->CopyResource(uiStaging.get(),texture.get());D3D11_MAPPED_SUBRESOURCE m{};check_hresult(context->Map(uiStaging.get(),0,D3D11_MAP_READ,0,&m));alphaMin=255;alphaMax=0;for(UINT y=0;y<uiDesc.Height;y++){auto source=static_cast<const BYTE*>(m.pData)+y*m.RowPitch;memcpy(uiPixels.data()+y*uiDesc.Width*4,source,uiDesc.Width*4);for(UINT x=0;x<uiDesc.Width;x++){alphaMin=std::min(alphaMin,int(source[x*4+3]));alphaMax=std::max(alphaMax,int(source[x*4+3]));}}context->Unmap(uiStaging.get(),0);uf.Close();}
   }
   if(arrived.exchange(false)){auto frame=pool.TryGetNextFrame();if(frame){
   auto access=frame.Surface().as<::Windows::Graphics::DirectX::Direct3D11::IDirect3DDxgiInterfaceAccess>();com_ptr<ID3D11Texture2D> source;check_hresult(access->GetInterface(__uuidof(ID3D11Texture2D),source.put_void()));
   D3D11_TEXTURE2D_DESC desc{};source->GetDesc(&desc);
   if(!staging||desc.Width!=cached.Width||desc.Height!=cached.Height){cached=desc;desc.Usage=D3D11_USAGE_STAGING;desc.BindFlags=0;desc.CPUAccessFlags=D3D11_CPU_ACCESS_READ;desc.MiscFlags=0;staging=nullptr;check_hresult(d3d->CreateTexture2D(&desc,nullptr,staging.put()));worldPixels.resize(cached.Width*cached.Height*4);}
   context->CopyResource(staging.get(),source.get());D3D11_MAPPED_SUBRESOURCE mapped{};check_hresult(context->Map(staging.get(),0,D3D11_MAP_READ,0,&mapped));
   for(UINT y=0;y<cached.Height;y++)memcpy(worldPixels.data()+y*cached.Width*4,static_cast<const BYTE*>(mapped.pData)+y*mapped.RowPitch,cached.Width*4);
   context->Unmap(staging.get(),0);frame.Close();}}
   // A still world must not suppress UI-only animation or trim the final hold.
   // Keep the latest exact pixels of both owned windows and sample the visible
   // composition on a wall clock, even when one surface did not change.
   const auto emitted=std::chrono::steady_clock::now();if(uiPixels.empty()||worldPixels.empty()||emitted-lastEmitted<std::chrono::microseconds(33333)){Sleep(1);continue;}lastEmitted=emitted;
   lastUnixMS=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();if(!firstUnixMS)firstUnixMS=lastUnixMS;
   BITMAPFILEHEADER file{};file.bfType=0x4d42;file.bfOffBits=sizeof(file)+sizeof(BITMAPINFOHEADER);file.bfSize=file.bfOffBits+cached.Width*cached.Height*4;
   BITMAPINFOHEADER info{};info.biSize=sizeof(info);info.biWidth=cached.Width;info.biHeight=-LONG(cached.Height);info.biPlanes=1;info.biBitCount=32;info.biCompression=BI_RGB;
   if(uiDesc.Width!=cached.Width||uiDesc.Height!=cached.Height)throw std::runtime_error("Owned UI/world capture dimensions disagree");
   bytes(&file,sizeof(file));bytes(&info,sizeof(info));std::vector<BYTE> pixels(cached.Width*cached.Height*4);for(UINT y=0;y<cached.Height;y++){auto world=worldPixels.data()+y*cached.Width*4;auto ui=uiPixels.data()+y*cached.Width*4;auto row=pixels.data()+y*cached.Width*4;for(UINT x=0;x<cached.Width;x++){const int a=ui[x*4+3];for(int c=0;c<3;c++)row[x*4+c]=BYTE(std::min(255,int(ui[x*4+c])+(int(world[x*4+c])*(255-a)+127)/255));row[x*4+3]=255;}}bytes(pixels.data(),pixels.size());fflush(stdout);++frames;
   if(frames==1){fprintf(stderr,"{\"event\":\"first-frame\",\"unixMS\":%lld}\n",firstUnixMS);fflush(stderr);}
  }
  uiSession.Close();uiPool.FrameArrived(uiToken);uiPool.Close();session.Close();pool.FrameArrived(token);pool.Close();
  fprintf(stderr,"{\"frames\":%d,\"width\":%u,\"height\":%u,\"seconds\":%.3f,\"firstFrameUnixMS\":%lld,\"lastFrameUnixMS\":%lld,\"maximumCaptureFPS\":30,\"background\":%s,\"ownedUiAlphaMin\":%d,\"ownedUiAlphaMax\":%d}\n",frames,cached.Width,cached.Height,std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count(),firstUnixMS,lastUnixMS,background?"true":"false",alphaMin,alphaMax);
  if(background){ShowWindow(window,SW_HIDE);SetWindowLongPtrW(window,GWL_EXSTYLE,oldStyle);SetWindowPos(window,HWND_BOTTOM,oldRect.left,oldRect.top,0,0,SWP_NOSIZE|SWP_NOACTIVATE);}
  return frames==limit||(argc>5&&frames>0&&GetFileAttributesW(argv[5])!=INVALID_FILE_ATTRIBUTES)?0:2;
 }catch(const hresult_error& e){fprintf(stderr,"WGC HRESULT 0x%08x: %s\n",unsigned(e.code().value),to_string(e.message()).c_str());}
 catch(const std::exception& e){fprintf(stderr,"%s\n",e.what());}
 if(background&&window){ShowWindow(window,SW_HIDE);SetWindowLongPtrW(window,GWL_EXSTYLE,oldStyle);SetWindowPos(window,HWND_BOTTOM,oldRect.left,oldRect.top,0,0,SWP_NOSIZE|SWP_NOACTIVATE);}return 1;
}
