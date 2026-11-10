// Lossless streaming UI PNG: fixed filter0 and fast native zlib.
import zlib from 'node:zlib';
import {promisify} from 'node:util';
const deflate=promisify(zlib.deflate),signature=Buffer.from([137,80,78,71,13,10,26,10]);
const crcTable=Uint32Array.from({length:256},(_,n)=>{for(let k=0;k<8;k++)n=n&1?0xedb88320^(n>>>1):n>>>1;return n>>>0;});
function crc(bytes){if(typeof zlib.crc32==='function')return zlib.crc32(bytes);let c=0xffffffff;for(const b of bytes)c=crcTable[(c^b)&255]^(c>>>8);return (c^0xffffffff)>>>0;}
function chunk(type,data){const out=Buffer.allocUnsafe(data.length+12);out.writeUInt32BE(data.length);out.write(type,4,4,'ascii');data.copy(out,8);out.writeUInt32BE(crc(out.subarray(4,data.length+8)),data.length+8);return out;}
export async function encodeNativeUIPNG(canvas){
 const width=canvas.width,height=canvas.height;
 // Preserve the established encoder for unusually large canvases rather than
 // allocating an unbounded raw staging buffer.4K is within this64MiB limit.
 if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>16777216)return canvas.encode('png');
 const pixels=canvas.getContext('2d').getImageData(0,0,width,height).data,rgba=Buffer.from(pixels.buffer,pixels.byteOffset,pixels.byteLength),stride=width*4;
 if(rgba.length!==stride*height)throw Error('Invalid native UI RGBA size');
 const rows=Buffer.allocUnsafe((stride+1)*height);for(let y=0;y<height;y++){rows[y*(stride+1)]=0;rgba.copy(rows,y*(stride+1)+1,y*stride,(y+1)*stride);}
 const header=Buffer.alloc(13);header.writeUInt32BE(width);header.writeUInt32BE(height,4);header[8]=8;header[9]=6;
 const compressed=await deflate(rows,{level:1});return Buffer.concat([signature,chunk('IHDR',header),chunk('IDAT',compressed),chunk('IEND',Buffer.alloc(0))]);
}
