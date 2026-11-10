#pragma once
#include <wincodec.h>
#include <wrl/client.h>
#include <wincrypt.h>
#include <zstd.h>
#include <chrono>
#include <array>
// A transparent owned Win32 surface. It never takes focus or input from the game.
class NativeWidgetWindow {
    HWND window=nullptr;std::vector<BYTE> pixels;unsigned width=0,height=0;
    HDC memory=nullptr;HBITMAP image=nullptr;HGDIOBJ previous=nullptr;void* bits=nullptr;unsigned bitmapWidth=0,bitmapHeight=0;
    static std::vector<BYTE> base64(const std::string& encoded){
        DWORD size=0;if(encoded.size()>180*1024*1024||!CryptStringToBinaryA(encoded.data(),DWORD(encoded.size()),CRYPT_STRING_BASE64,nullptr,&size,nullptr,nullptr)||size>128*1024*1024)throw std::runtime_error("UI frame invalid");std::vector<BYTE> bytes(size);if(!CryptStringToBinaryA(encoded.data(),DWORD(encoded.size()),CRYPT_STRING_BASE64,bytes.data(),&size,nullptr,nullptr))throw std::runtime_error("UI frame decode");return bytes;
    }
    static std::vector<BYTE> frameBytes(const std::string& text){
        if(text.empty()||text.size()%4||text.size()>180*1024*1024)throw std::runtime_error("UI pixel base64 size invalid");
        static const auto digit=[](){std::array<int,256> result{};result.fill(-1);const std::string alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";for(unsigned i=0;i<alphabet.size();i++)result[BYTE(alphabet[i])]=int(i);return result;}();
        const auto size=text.size()/4*3-(text.back()=='=')-(text[text.size()-2]=='=');if(size>128*1024*1024)throw std::runtime_error("UI pixel bytes invalid");std::vector<BYTE> bytes(size);std::size_t at=0;
        for(std::size_t i=0;i<text.size();i+=4){const int a=digit[BYTE(text[i])],b=digit[BYTE(text[i+1])],c=digit[BYTE(text[i+2])],d=digit[BYTE(text[i+3])];const bool padC=text[i+2]=='=',padD=text[i+3]=='=';
            if(a<0||b<0||(!padC&&c<0)||(!padD&&d<0)||(padC&&!padD)||((padC||padD)&&i+4!=text.size())||(padC&&(b&15))||(padD&&!padC&&(c&3)))throw std::runtime_error("UI pixel base64 encoding invalid");
            bytes[at++]=BYTE((a<<2)|(b>>4));if(!padC)bytes[at++]=BYTE((b<<4)|(c>>2));if(!padD)bytes[at++]=BYTE((c<<6)|d);
        }return bytes;
    }
    void resetBitmap(){if(image){SelectObject(memory,previous);DeleteObject(image);image=nullptr;bits=nullptr;}if(memory){DeleteDC(memory);memory=nullptr;}bitmapWidth=bitmapHeight=0;}
    void present(HWND owner){
        if(!window){window=CreateWindowExW(WS_EX_LAYERED|WS_EX_TRANSPARENT|WS_EX_NOACTIVATE|WS_EX_TOOLWINDOW,L"STATIC",L"",WS_POPUP,0,0,width,height,owner,nullptr,GetModuleHandleW(nullptr),nullptr);if(!window)throw std::runtime_error("Native UI window");}
        if(!image||bitmapWidth!=width||bitmapHeight!=height){resetBitmap();memory=CreateCompatibleDC(nullptr);if(!memory)throw std::runtime_error("Native UI device context");BITMAPINFO bitmap{};bitmap.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);bitmap.bmiHeader.biWidth=width;bitmap.bmiHeader.biHeight=-LONG(height);bitmap.bmiHeader.biPlanes=1;bitmap.bmiHeader.biBitCount=32;bitmap.bmiHeader.biCompression=BI_RGB;image=CreateDIBSection(memory,&bitmap,DIB_RGB_COLORS,&bits,nullptr,0);if(!image){resetBitmap();throw std::runtime_error("Native UI bitmap");}previous=SelectObject(memory,image);bitmapWidth=width;bitmapHeight=height;}
        std::memcpy(bits,pixels.data(),pixels.size());HDC screen=GetDC(nullptr);POINT origin{},position{};ClientToScreen(owner,&position);SIZE extent{LONG(width),LONG(height)};BLENDFUNCTION blend{AC_SRC_OVER,0,255,AC_SRC_ALPHA};const bool ok=UpdateLayeredWindow(window,screen,&position,&extent,memory,&origin,0,&blend,ULW_ALPHA);ReleaseDC(nullptr,screen);if(!ok)throw std::runtime_error("Native UI surface update");place(owner);
    }
public:
    double decodeMS=0,presentMS=0;
    void place(HWND owner){if(!window)return;POINT point{};ClientToScreen(owner,&point);const bool visible=IsWindowVisible(owner)&&!IsIconic(owner);auto previousWindow=GetWindow(owner,GW_HWNDPREV);UINT flags=SWP_NOSIZE|SWP_NOACTIVATE;if(previousWindow==window)flags|=SWP_NOZORDER;if(bool(IsWindowVisible(window))!=visible)flags|=visible?SWP_SHOWWINDOW:SWP_HIDEWINDOW;SetWindowPos(window,previousWindow?previousWindow:HWND_TOP,point.x,point.y,0,0,flags);}
    static void decodePixels(const std::string& encoded,unsigned width,unsigned height,std::vector<BYTE>& pixels){
        if(!width||!height||width>7680||height>4320)throw std::runtime_error("UI dimensions invalid");auto compressed=frameBytes(encoded);pixels.resize(std::size_t(width)*height*4);const auto length=ZSTD_decompress(pixels.data(),pixels.size(),compressed.data(),compressed.size());if(ZSTD_isError(length)||length!=pixels.size())throw std::runtime_error("Native UI pixel decode");for(std::size_t at=0;at<pixels.size();at+=4)std::swap(pixels[at],pixels[at+2]);
    }
    void updatePixels(HWND owner,const std::string& encoded,unsigned nextWidth,unsigned nextHeight){const auto start=std::chrono::steady_clock::now();decodePixels(encoded,nextWidth,nextHeight,pixels);width=nextWidth;height=nextHeight;const auto decoded=std::chrono::steady_clock::now();present(owner);decodeMS=std::chrono::duration<double,std::milli>(decoded-start).count();presentMS=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-decoded).count();}
    void update(HWND owner,const std::string& encoded){
        using Microsoft::WRL::ComPtr;auto png=base64(encoded);ComPtr<IWICImagingFactory> factory;ComPtr<IWICStream> stream;ComPtr<IWICBitmapDecoder> decoder;ComPtr<IWICBitmapFrameDecode> frame;ComPtr<IWICFormatConverter> converter;
        auto check=[](HRESULT hr){if(FAILED(hr))throw std::runtime_error("Native UI image conversion");};check(CoCreateInstance(CLSID_WICImagingFactory,nullptr,CLSCTX_INPROC_SERVER,IID_PPV_ARGS(&factory)));check(factory->CreateStream(&stream));check(stream->InitializeFromMemory(png.data(),DWORD(png.size())));check(factory->CreateDecoderFromStream(stream.Get(),nullptr,WICDecodeMetadataCacheOnLoad,&decoder));check(decoder->GetFrame(0,&frame));check(frame->GetSize(&width,&height));if(!width||!height||width>7680||height>4320)throw std::runtime_error("UI dimensions invalid");check(factory->CreateFormatConverter(&converter));check(converter->Initialize(frame.Get(),GUID_WICPixelFormat32bppPBGRA,WICBitmapDitherTypeNone,nullptr,0,WICBitmapPaletteTypeCustom));pixels.resize(std::size_t(width)*height*4);check(converter->CopyPixels(nullptr,width*4,UINT(pixels.size()),pixels.data()));present(owner);
    }
    ~NativeWidgetWindow(){resetBitmap();if(window)DestroyWindow(window);}
};
