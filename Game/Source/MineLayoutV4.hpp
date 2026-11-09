#pragma once
namespace minelayoutv4 {
// V3's 80-unit squares and centered (-40*w,-20-40*h) board, in 1280x720 UI units.
struct Board {
 float cell=160.f/3,left=0,top=160.f/3,width=0,height=0;
 Board(int columns,int rows=11):left((1280.f-columns*cell)/2),width(columns*cell),height(rows*cell){}
};
}
