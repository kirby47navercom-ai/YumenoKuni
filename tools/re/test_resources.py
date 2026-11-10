"""Format regression tests with independently constructed small byte fixtures."""
import struct
import unittest

import dat
import srd
import sfl
import map_data


def block(kind, main=b'', children=b''):
    result = kind + struct.pack('>III', len(main), len(children), 0) + main
    result += bytes(-len(result) % 16)
    result += children
    return result + bytes(-len(result) % 16)


class ResourceTests(unittest.TestCase):
    def test_dat_array_and_index_pools(self):
        source = struct.pack('<III', 1, 12, 3)
        source += b'position\0f32\0' + struct.pack('<H', 2)
        source += b'label\0label\0' + struct.pack('<H', 1)
        source += b'text\0utf16\0' + struct.pack('<H', 1)
        source += bytes(-len(source) % 16)
        source += struct.pack('<2f2H2H', 1.25, -9, 0, 0, 1, 1)
        source += b'camera\0'
        source += bytes(-len(source) % 2)
        source += 'test\0'.encode('utf-16-le')
        parsed = dat.parse_dat(source)
        self.assertEqual(parsed['rows'], [[[1.25, -9.0], 'camera', 'test']])
        self.assertEqual(parsed['trailing_bytes'], 0)
        self.assertEqual(parsed['unknown_row_bytes'], 0)
        with self.assertRaises(ValueError):
            dat.parse_dat(source[:-1])

    def test_dat_rejects_unknown_type(self):
        with self.assertRaises(ValueError):
            dat.parse_dat(struct.pack('<III', 1, 4, 1) + b'x\0bad\0\x01\0')

    def test_srd_nested_offsets(self):
        texture = struct.pack('<IHHHHBBBB', 8, 1, 32, 16, 1024, 28, 0, 0, 0)
        source = block(b'$CFH', b'', block(b'$TXR', texture))
        result = srd.parse_srd(source)
        nested = result['blocks'][0]['children'][0]
        self.assertEqual(nested['offset'], 16)
        self.assertEqual(nested['main_offset'], 32)
        self.assertEqual(nested['decoded']['width'], 32)
        self.assertEqual(nested['decoded']['format'], 'BC7')
        with self.assertRaises(ValueError):
            srd.parse_srd(source[:-1])

    def test_rsi_external_mask_and_bounds(self):
        payload = struct.pack('<BBbBhhhhI', 6, 5, 4, 1, 0, -1, 32, 0, 32)
        payload += struct.pack('<IIii', 0x40000004, 8, 0, -1) + b'name\0'
        result = srd.parse_srd(block(b'$RSI', payload), {'srdv':bytes(12)})
        external = result['blocks'][0]['decoded']['external'][0]
        self.assertEqual(external['offset'], 4)
        self.assertTrue(external['range_valid'])
        result = srd.parse_srd(block(b'$RSI', payload), {'srdv':bytes(11)})
        self.assertFalse(result['blocks'][0]['decoded']['external'][0]['range_valid'])
        high_offset = payload[:16]+struct.pack('<IIii',0x50000004,8,0,-1)+payload[32:]
        external=srd.parse_srd(block(b'$RSI',high_offset))['blocks'][0]['decoded']['external'][0]
        self.assertEqual(external['location'],'srdv')
        self.assertEqual(external['offset'],0x10000004)
        self.assertFalse(external['range_valid'])

    def test_vtx_native_attribute_byte_fields(self):
        payload=bytearray(96)
        struct.pack_into('<IHHIhBB',payload,0,10,28,0x203,3,1024,1,1)
        struct.pack_into('<4HII',payload,16,60,52,64,0,0,0)
        # Name pointer and stream are independent of byte offset and semantic index.
        struct.pack_into('<H6B',payload,28,80,24,1,4,2,2,1)
        struct.pack_into('<H6B',payload,36,0,0,0,1,0,3,0)
        struct.pack_into('<H6B',payload,44,0,12,0,2,0,3,0)
        struct.pack_into('<II',payload,52,0,32)
        payload[80:85]=b'map2\0'
        decoded=srd.parse_srd(block(b'$VTX',payload))['blocks'][0]['decoded']
        attribute=decoded['attributes'][0]
        self.assertEqual((attribute['name'],attribute['offset'],attribute['stream']),('map2',24,1))
        self.assertEqual((attribute['semantic_id'],attribute['semantic_index'],attribute['format_id']),(4,2,2))
        self.assertEqual(decoded['attribute_count'],3)
        self.assertEqual(decoded['index_width'],2)
        self.assertEqual(decoded['primitive_id'],4)
        payload[7]=3
        self.assertEqual(srd.parse_srd(block(b'$VTX',payload))['blocks'][0]['decoded']['index_width'],4)
        struct.pack_into('<H',payload,28,len(payload))
        malformed=srd.parse_srd(block(b'$VTX',payload))['blocks'][0]
        self.assertIn('string pointer outside block',malformed['decode_error'])

    def test_bgra_texture_channels(self):
        image = srd.texture_image(dict(width=1,height=1,format_id=1,swizzle=1,palette=0), bytes([9,8,7,6]))
        self.assertEqual(image.getpixel((0,0)), (7,8,9,6))

    def test_txr_native_flags_and_external_index_are_separate_bytes(self):
        payload=struct.pack('<IBBHHHBBBB',1,7,2,8,4,16,15,2,0,0)
        info=srd.parse_srd(block(b'$TXR',payload))['blocks'][0]['decoded']
        self.assertEqual(info['swizzle'],0x0207)  # Compatibility with old combined field.
        self.assertEqual((info['flags_byte'],info['first_external_index'],info['mip_count']),(7,2,2))
        self.assertFalse(info['is_cubemap'])
        resources={'external':[{'offset':11},{'offset':22},{'offset':33}]}
        self.assertEqual(srd.texture_resource(info,resources),{'offset':33})
        with self.assertRaises(ValueError):srd.texture_resource(info,{'external':[{},{}]})
        malformed=srd.parse_srd(block(b'$TXR',payload[:-1]))['blocks'][0]
        self.assertIn('decode_error',malformed)

    def test_native_flags7_linear_bc1_block_rows_and_rejection_scope(self):
        # Two independently constructed4x4 BC1 blocks: red left, green right.
        raw=struct.pack('<HHI',0xf800,0,0)+struct.pack('<HHI',0x07e0,0,0)
        info=dict(width=8,height=4,format_id=15,swizzle=7,palette=0,mip_count=1)
        image=srd.texture_image(info,raw)
        self.assertEqual(image.getpixel((0,0)),(255,0,0,255))
        self.assertEqual(image.getpixel((3,3)),(255,0,0,255))
        self.assertEqual(image.getpixel((4,0)),(0,255,0,255))
        self.assertEqual(image.getpixel((7,3)),(0,255,0,255))
        for changed in [dict(format_id=17),dict(is_cubemap=True),dict(mip_count=2),dict(palette=1)]:
            with self.assertRaises(ValueError):srd.texture_image(info|changed,raw)

    def test_sfl_numeric_sequence_and_truncated_table(self):
        # One sequence, 12-byte header (empty name + padding), one operation.
        sequence = struct.pack('<IHH', 8, 12, 1) + bytes(4)
        sequence += struct.pack('<HHI', 28, 4, 3)
        entry = struct.pack('<IIHHI', 9, len(sequence), 7, 1, 1) + sequence
        source = b'LLFS' + struct.pack('<HHII', 1, 1, 7, 1)
        source += struct.pack('<IIHHI', 5, len(entry), 1, 0, 0) + entry
        parsed = sfl.parse_sfl(source)
        decoded = parsed['tables'][0]['entries'][0]
        self.assertEqual(decoded['event_number'], 7)
        self.assertEqual(decoded['sequences'][0]['operations'][0]['opcode'], 28)
        self.assertEqual(decoded['sequence_unconsumed_bytes'], 0)
        with self.assertRaises(ValueError):
            sfl.parse_sfl(source[:-1])

    def test_sfl_spflash_character_reference_and_name(self):
        # Installed SFL uses table-kind:u8 + entry:u16, then custom SpFlash matrix.
        raw = bytes.fromhex('26010005000000695f69636f6e000000')
        decoded = sfl.decode_operation(26, raw)
        self.assertEqual(decoded['instance_name'], 'i_icon')
        self.assertEqual(decoded['character_reference'], dict(table=5,entry=0))
        self.assertEqual(decoded['matrix']['scale_x'], 1.0)

    def test_collision_vec4_strip_bounds(self):
        payload = struct.pack('<HHIHHIII',5,1,24,1,1,1,0,0)
        payload += struct.pack('<6fII',0,0,0,1,1,0,0,0)
        payload += struct.pack('<IIHH',80,128,3,3)
        payload += bytes(80-len(payload))
        payload += struct.pack('<12f',0,0,0,1,1,0,0,1,0,1,0,1)
        payload += struct.pack('<3H',0,1,2)
        decoded = srd.parse_srd(block(b'$COL',payload))['blocks'][0]['decoded']
        self.assertEqual(decoded['leaves'][0]['indices'],[0,1,2])
        invalid = payload[:-2]+struct.pack('<H',3)
        result = srd.parse_srd(block(b'$COL',invalid))
        self.assertIn('decode_error',result['blocks'][0])

    def test_native_matrix_color_and_action_layout(self):
        # Measured adv_camera frame: native component masks, signed bitfields.
        decoded = sfl.decode_operation(26,bytes.fromhex('0d0100242d9408a3e4000000'))
        self.assertEqual(decoded['matrix']['translate_x'],-0.5)
        self.assertEqual(decoded['matrix']['translate_y'],0.5)
        self.assertEqual(decoded['color_transform']['multiply_rgba'][3],249/256)
        actions = sfl.decode_operation(12,bytes.fromhex('0700000000000000'))
        self.assertEqual([a['name'] for a in actions['actions']],['Stop','End'])

    def test_binary_map_jump_thresholds_and_extent(self):
        data=struct.pack('<6h',1,2,3,4,5,-1)
        decoded=map_data.parse(data,'mapjump_data.dat')
        self.assertEqual(decoded['records'][0]['minimum_state_1704'],2)
        self.assertEqual(decoded['records'][0]['destination_position'],-1)
        with self.assertRaises(ValueError):map_data.parse(data[:-1],'mapjump_data.dat')

    def test_stage_layer_grid_boundary(self):
        data=struct.pack('<II8H',42,24,9,0,1,0,1,1,32,32)
        data+=struct.pack('<II4HH',18,18,0,0,1,1,17)
        decoded=map_data.parse_stage(data)
        self.assertEqual(decoded['layers'][0]['tile_indices'],[17])
        with self.assertRaises(ValueError):map_data.parse_stage(data[:-1])

    def test_climax_native_three_group_boundaries(self):
        data=struct.pack('<6h',420,10,1,2,3,0)+bytes(2*28+3*20+8)
        decoded=map_data.parse(data,'climax_data_1.dat')
        self.assertEqual([g['count'] for g in decoded['groups']],[2,3,1])
        self.assertEqual(decoded['groups'][2]['records'][0]['offset'],128)
        with self.assertRaises(ValueError):map_data.parse(data[:-1],'climax_data_1.dat')

    def test_fixed_effect_and_partial_animation_tail(self):
        data=struct.pack('<2h2i2h',20,20,123,456,-1,0)+b'effect\0'+bytes(25)
        decoded=map_data.parse(data,'chareffectanim.dat')['records'][0]
        self.assertEqual(decoded['flash_name'],'effect')
        self.assertEqual(decoded['position_s32'],[123,456])
        partial=map_data.parse(bytes(1160),'monokumaz_anim.dat')
        self.assertEqual(len(partial['blocks']),6)
        self.assertEqual(len(partial['unknown_tail_hex']),160)

    def test_sfl_native_text_design_height_is_not_timeline_speed(self):
        raw=struct.pack('<I4iBBH',0xffffffff,-2,-2,1404,194,2,0,900)+bytes(6)+struct.pack('<H',40)+bytes(8)
        decoded=sfl.decode_text_header(raw,100)
        self.assertEqual(decoded['bounds_xywh'],[-2,-2,1404,194])
        self.assertEqual(decoded['alignment'],'center')
        self.assertEqual(decoded['native_font_height_design'],45)
        self.assertEqual(decoded['offset'],100)
        self.assertEqual(decoded['native_line_gap_design'],16)
        unusual=raw[:30]+struct.pack('<H',65436)+raw[32:]
        self.assertEqual(sfl.decode_text_header(unusual)['line_gap_u16'],65436)
        self.assertAlmostEqual(sfl.decode_text_header(unusual)['native_line_gap_design'],26174.4)
        with self.assertRaises(ValueError):sfl.decode_text_header(raw[:23])

    def test_sfl_native_parent_scale_changes_child_translation(self):
        local=[1,0,0,0,1,0,10,20,1]
        parent=[2,0,0,0,2,0,100,50,1]
        combined=sfl.compose_native_affine(local,parent)
        self.assertEqual(combined,[2,0,0,0,2,0,120,90,1])
        self.assertNotEqual(combined,sfl.compose_native_affine(parent,local))

    def test_sfl_design_projection_requires_explicit_viewport(self):
        self.assertEqual(sfl.project_design_2d(0,0,[0,0,1920,1080])['ndc'],[-1,1])
        self.assertEqual(sfl.project_design_2d(960,540,[0,0,1920,1080])['ndc'],[0,0])
        actual=sfl.project_design_2d(396,873,[100,50,1280,720])['viewport_xy']
        self.assertAlmostEqual(actual[0],364)
        self.assertAlmostEqual(actual[1],632)


if __name__ == '__main__': unittest.main()
