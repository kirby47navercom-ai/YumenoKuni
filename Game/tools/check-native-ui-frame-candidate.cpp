#define NOMINMAX
#include <windows.h>
#include <vector>
#include <string>
#include <stdexcept>
#include <algorithm>
#include <cstring>
#include <fstream>
#include <iostream>
#include <nlohmann/json.hpp>
#include "NativeWidgetWindow.hpp"
using Microsoft::WRL::ComPtr;
int main(int argc,char**argv){try{
 CoInitializeEx(nullptr,COINIT_MULTITHREADED);unsigned tests=0;
 for(int i=1;i<argc;i++){
  nlohmann::json j;std::ifstream(argv[i])>>j;std::vector<BYTE> actual;NativeWidgetWindow::decodePixels(j.at("pixels"),j.at("width"),j.at("height"),actual);
  std::string encoded=j.at("png");DWORD size=0;CryptStringToBinaryA(encoded.data(),DWORD(encoded.size()),CRYPT_STRING_BASE64,nullptr,&size,nullptr,nullptr);std::vector<BYTE> png(size);CryptStringToBinaryA(encoded.data(),DWORD(encoded.size()),CRYPT_STRING_BASE64,png.data(),&size,nullptr,nullptr);
  auto check=[](HRESULT hr){if(FAILED(hr))throw std::runtime_error("WIC reference failure");};ComPtr<IWICImagingFactory>factory;ComPtr<IWICStream>stream;ComPtr<IWICBitmapDecoder>decoder;ComPtr<IWICBitmapFrameDecode>frame;ComPtr<IWICFormatConverter>converter;
  check(CoCreateInstance(CLSID_WICImagingFactory,nullptr,CLSCTX_INPROC_SERVER,IID_PPV_ARGS(&factory)));check(factory->CreateStream(&stream));check(stream->InitializeFromMemory(png.data(),size));check(factory->CreateDecoderFromStream(stream.Get(),nullptr,WICDecodeMetadataCacheOnLoad,&decoder));check(decoder->GetFrame(0,&frame));unsigned w,h;check(frame->GetSize(&w,&h));check(factory->CreateFormatConverter(&converter));check(converter->Initialize(frame.Get(),GUID_WICPixelFormat32bppPBGRA,WICBitmapDitherTypeNone,nullptr,0,WICBitmapPaletteTypeCustom));std::vector<BYTE>expected(w*h*4);check(converter->CopyPixels(nullptr,w*4,UINT(expected.size()),expected.data()));
  if(actual!=expected)throw std::runtime_error("Native PBGRA differs from old PNG/WIC");tests++;
  for(int bad=0;bad<4;bad++){bool rejected=false;try{std::vector<BYTE>result;NativeWidgetWindow::decodePixels(bad==0?"bad!":j.at("pixels").get<std::string>(),bad==1?0:bad==2?7681:w,bad==3?h+1:h,result);}catch(...){rejected=true;}if(!rejected)throw std::runtime_error("Malformed UI frame accepted");tests++;}
 }
 CoUninitialize();std::cout<<"{\"ok\":true,\"tests\":"<<tests<<",\"exactWICPBGRA\":true}";return 0;
 }catch(const std::exception&e){std::cerr<<e.what();return 1;}}
