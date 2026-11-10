// Native Skia data is premultiplied RGBA8. Retain those exact bytes across
// the process boundary; the older PNG path remains a bounded fallback.
import * as zlib from 'node:zlib';
import {promisify} from 'node:util';
const compress=typeof zlib.zstdCompress==='function'?promisify(zlib.zstdCompress):null;
export async function encodeNativeUIFrame(canvas){
 const width=canvas.width,height=canvas.height;
 if(width>7680||height>4320||width<1||height<1)throw Error('Native UI dimensions invalid');
 if(!compress)return {png:(await canvas.encode('png')).toString('base64')};const bytes=canvas.data();
 if(bytes.length!==width*height*4)return {png:(await canvas.encode('png')).toString('base64')};
 const options={params:{[zlib.constants.ZSTD_c_compressionLevel]:1}};
 // A720p frame is a short native call; avoid a worker-pool round trip. Larger
 // canvases retain asynchronous compression so input I/O stays responsive.
 const packed=bytes.length<=4*1024*1024&&typeof zlib.zstdCompressSync==='function'?zlib.zstdCompressSync(bytes,options):await compress(bytes,options);
 return {encoding:'zstd-rgba8-premultiplied',width,height,pixels:packed.toString('base64')};
}
