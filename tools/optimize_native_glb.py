"""Lossless runtime-only packaging for the native loader's 64 MiB GLB limit.

Original art is never rewritten. Image dimensions/pixels, geometry buffer views,
scene hierarchy, material assignments and sampler values remain identical.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import tempfile
import time
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 64 * 1024 * 1024
CACHE = ROOT / 'Game/Saved/native-glb-texture-cache'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def atomic(file, data):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=file.parent, prefix=file.name+'.', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
        os.replace(temporary, file)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def encode_png(raw):
    CACHE.mkdir(parents=True, exist_ok=True)
    key = sha(raw)
    file = CACHE / (key+'.webp')
    receipt = CACHE / (key+'.json')
    if file.exists() and receipt.exists():
        proof = json.loads(receipt.read_text(encoding='utf8'))
        encoded = file.read_bytes()
        if proof.get('sourceSHA256') == key and proof.get('encodedSHA256') == sha(encoded) and proof.get('exactPixels') is True:
            return encoded, proof
    image = Image.open(io.BytesIO(raw))
    image.load()
    output = io.BytesIO()
    # exact also preserves RGB values under fully transparent pixels.
    image.save(output, format='WEBP', lossless=True, exact=True, method=4)
    encoded = output.getvalue()
    decoded = Image.open(io.BytesIO(encoded))
    assert decoded.size == image.size
    pixels = image.convert('RGBA').tobytes()
    assert pixels == decoded.convert('RGBA').tobytes(), 'Lossless texture roundtrip changed pixels'
    proof = {'sourceSHA256':key, 'encodedSHA256':sha(encoded), 'size':list(image.size),
             'rgbaSHA256':sha(pixels), 'exactPixels':True, 'before':len(raw), 'after':len(encoded)}
    atomic(file, encoded)
    atomic(receipt, (json.dumps(proof, indent=2)+'\n').encode())
    return encoded, proof


def repack(source):
    assert source[:4] == b'glTF'
    assert struct.unpack_from('<II', source, 4) == (2, len(source))
    json_size, json_type = struct.unpack_from('<II', source, 12)
    assert json_type == 0x4e4f534a
    spec = json.loads(source[20:20+json_size])
    binary_size, binary_type = struct.unpack_from('<II', source, 20+json_size)
    assert binary_type == 0x004e4942 and 28+json_size+binary_size == len(source)
    binary = source[28+json_size:]
    assert len(spec['buffers']) == 1 and 'uri' not in spec['buffers'][0]
    original = json.loads(json.dumps(spec))
    replacements = {}
    proofs = []
    converted = set()
    for index, image in enumerate(spec.get('images', [])):
        if image.get('mimeType') != 'image/png' or 'bufferView' not in image:
            continue
        view_id = image['bufferView']
        view = spec['bufferViews'][view_id]
        start = view.get('byteOffset', 0)
        raw = binary[start:start+view['byteLength']]
        encoded, proof = encode_png(raw)
        if len(encoded) >= len(raw):
            continue
        # Image buffer views cannot simultaneously carry vertex/index data.
        assert not any(a.get('bufferView') == view_id or any(v.get('bufferView') == view_id for v in a.get('sparse', {}).values() if isinstance(v, dict)) for a in spec.get('accessors', []))
        replacements[view_id] = encoded
        image['mimeType'] = 'image/webp'
        converted.add(index)
        proofs.append({'image':index, 'name':image.get('name'), **proof})
    assert replacements, 'Large GLB has no reducible embedded PNGs'
    for texture in spec.get('textures', []):
        if texture.get('source') in converted:
            texture.setdefault('extensions', {})['EXT_texture_webp'] = {'source':texture.pop('source')}
    for key in ('extensionsUsed', 'extensionsRequired'):
        if 'EXT_texture_webp' not in spec.setdefault(key, []):
            spec[key].append('EXT_texture_webp')
    parts = []
    length = 0
    geometry = []
    for index, view in enumerate(spec['bufferViews']):
        assert view['buffer'] == 0
        old = original['bufferViews'][index]
        before = binary[old.get('byteOffset', 0):old.get('byteOffset', 0)+old['byteLength']]
        assert len(before) == old['byteLength']
        data = replacements.get(index, before)
        view['byteOffset'] = length
        view['byteLength'] = len(data)
        parts.extend((data, b'\0' * (-len(data) % 4)))
        length += len(data) + (-len(data) % 4)
        if index not in replacements:
            geometry.append({'bufferView':index, 'bytes':len(data), 'sha256':sha(data)})
    spec['buffers'][0]['byteLength'] = length
    encoded_json = json.dumps(spec, separators=(',', ':'), ensure_ascii=False).encode('utf8')
    encoded_json += b' ' * (-len(encoded_json) % 4)
    output = (struct.pack('<IIIII', 0x46546c67, 2, 28+len(encoded_json)+length, len(encoded_json), 0x4e4f534a)
              + encoded_json + struct.pack('<II', length, 0x004e4942) + b''.join(parts))
    assert len(output) < LIMIT, 'Lossless packaging alone does not meet native GLB limit'
    # Check actual serialized output, not just inputs used to construct it.
    out_binary = output[28+len(encoded_json):]
    for proof in geometry:
        view = spec['bufferViews'][proof['bufferView']]
        assert sha(out_binary[view['byteOffset']:view['byteOffset']+view['byteLength']]) == proof['sha256']
    for key in ('nodes', 'scenes', 'scene', 'meshes', 'accessors', 'materials', 'samplers', 'animations', 'skins'):
        assert spec.get(key) == original.get(key), key+' must not change'
    return output, {'textures':proofs, 'unchangedBufferViews':geometry, 'sceneGeometryMaterialsSamplersUnchanged':True}


def optimize_generated_glbs():
    rows = []
    for file in sorted((ROOT/'Game/Assets/Art').rglob('*.glb')):
        if file.stat().st_size <= LIMIT:
            continue
        source = file.read_bytes()
        output, proof = repack(source)
        atomic(file, output)
        rows.append({'path':file.relative_to(ROOT).as_posix(), 'before':len(source), 'after':len(output),
                     'sourceSHA256':sha(source), 'runtimeSHA256':sha(output), **proof})
    work = ROOT/'Game/Saved'/('native-glb-compat-'+str(time.time_ns()//1000000))
    work.mkdir(parents=True)
    report = work/'report.json'
    report.write_text(json.dumps({'ok':True, 'limit':LIMIT, 'count':len(rows), 'rows':rows,
        'scope':'Generated runtime GLBs only. Original art untouched; same resolution and RGBA pixels, all non-image views and scene/mesh/material/sampler data preserved. Native runtime verification is separate.'}, indent=2)+'\n', encoding='utf8')
    print(json.dumps({'nativeGLBsLosslesslyRepacked':len(rows), 'report':str(report)}), flush=True)
    return report


if __name__ == '__main__':
    optimize_generated_glbs()
