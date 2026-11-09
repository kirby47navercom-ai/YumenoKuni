#pragma once
#include <cstdint>
#include <algorithm>
#include <iterator>
namespace gputrialatlasv4 {
struct Glyph {std::uint32_t key;std::int16_t ox,oy,w,h;};
inline constexpr Glyph entries[]={
#include "GpuTrialAtlasRows0.inl"
#include "GpuTrialAtlasRows1.inl"
#include "GpuTrialAtlasRows2.inl"
};
inline const Glyph* find(std::uint32_t key){auto p=std::lower_bound(std::begin(entries),std::end(entries),key,[](const Glyph& g,std::uint32_t k){return g.key<k;});return p!=std::end(entries)&&p->key==key?p:nullptr;}
}
