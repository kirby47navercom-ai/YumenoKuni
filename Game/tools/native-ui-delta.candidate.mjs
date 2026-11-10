// Native Skia data is premultiplied RGBA8. Retain those exact bytes across
// the process boundary; the older PNG path remains a bounded fallback.
import * as zlib from 'node:zlib';
import {promisify} from 'node:util';
const compress=typeof zlib.zstdCompress==='function'?promisify(zlib.zstdCompress):null;
const frames=new WeakMap();
export async function encodeNativeUIFrame(canvas){
 const width=canvas.width,height=canvas.height;
 if(width>7680||height>4320||width<1||height<1)throw Error('Native UI dimensions invalid');
 if(!compress)return {png:(await canvas.encode('png')).toString('base64')};const bytes=canvas.data();
 if(bytes.length!==width*height*4){frames.delete(canvas);return {png:(await canvas.encode('png')).toString('base64')};}
 const prior=frames.get(canvas),sequence=prior&&prior.sequence<Number.MAX_SAFE_INTEGER?prior.sequence+1:1;
 let input=bytes,delta=false,buffer;
 if(prior&&sequence>1&&prior.width===width&&prior.height===height&&prior.bytes.length===bytes.length){
  // Scene changes use a full frame. Sparse moving text/reticles keep exact
  // pixels but send only their XOR against the acknowledged previous frame.
  let changes=0,samples=0;for(let i=0;i<bytes.length;i+=4096){samples++;if(bytes.readUInt32LE(i)!==prior.bytes.readUInt32LE(i))changes++;}
  if(changes/samples<.25){buffer=prior.buffer?.length===bytes.length?prior.buffer:Buffer.allocUnsafe(bytes.length);if(bytes.byteOffset%4===0&&prior.bytes.byteOffset%4===0&&buffer.byteOffset%4===0){const a=new Uint32Array(bytes.buffer,bytes.byteOffset,bytes.length/4),b=new Uint32Array(prior.bytes.buffer,prior.bytes.byteOffset,bytes.length/4),out=new Uint32Array(buffer.buffer,buffer.byteOffset,buffer.length/4);for(let i=0;i<out.length;i++)out[i]=a[i]^b[i];}else for(let i=0;i<bytes.length;i++)buffer[i]=bytes[i]^prior.bytes[i];input=buffer;delta=true;}
 }
 const options={params:{[zlib.constants.ZSTD_c_compressionLevel]:1}};
 const packed=input.length<=4*1024*1024&&typeof zlib.zstdCompressSync==='function'?zlib.zstdCompressSync(input,options):await compress(input,options);
 // NativeWidgetLayer serially awaits each UI acknowledgment before encoding again.
 frames.set(canvas,{width,height,bytes,sequence,buffer:buffer||prior?.buffer});
 return {encoding:delta?'zstd-rgba8-premultiplied-xor':'zstd-rgba8-premultiplied',width,height,sequence,...delta?{baseSequence:prior.sequence}:{},pixels:packed.toString('base64')};
}
