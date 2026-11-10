#include <windows.h>
#include <dxgi1_6.h>
#include <iostream>
#include <iomanip>
int main(){IDXGIFactory1* factory=nullptr;if(FAILED(CreateDXGIFactory1(__uuidof(IDXGIFactory1),(void**)&factory)))return 1;for(unsigned i=0;;i++){IDXGIAdapter1* a=nullptr;if(factory->EnumAdapters1(i,&a)==DXGI_ERROR_NOT_FOUND)break;DXGI_ADAPTER_DESC1 d{};if(SUCCEEDED(a->GetDesc1(&d)))std::wcout<<L"adapter="<<i<<L" name="<<d.Description<<L" luid=0x"<<std::hex<<std::setfill(L'0')<<std::setw(8)<<unsigned(d.AdapterLuid.HighPart)<<L"_0x"<<std::setw(8)<<d.AdapterLuid.LowPart<<std::dec<<L" videoBytes="<<d.DedicatedVideoMemory<<L" flags="<<d.Flags<<L"\n";a->Release();}factory->Release();}
