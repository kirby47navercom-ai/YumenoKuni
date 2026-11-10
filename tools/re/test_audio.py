import io
import struct
import unittest

from audio import awb, hca_header, cue_waveforms


class AudioMetadataTest(unittest.TestCase):
    def test_cue_graph_uses_references_not_row_order(self):
        def table(rows): return {'rows':rows}
        data={'cues':[{'name':'test','cue_index':0,'cue':{'ReferenceType':3,'ReferenceIndex':0}}],
              'tables':{'SequenceTable':table([{'NumTracks':1,'TrackIndex':b'\0\1'}]),
                        'TrackTable':table([{'EventIndex':99},{'EventIndex':0}]),
                        'CommandTable':table([{'Command':bytes.fromhex('07d00400020001000000')}]),
                        'SynthTable':table([{'ReferenceItems':b''},{'ReferenceItems':b'\0\1\0\1'}]),
                        'WaveformTable':table([{'MemoryAwbId':99},{'MemoryAwbId':7}])}}
        links=cue_waveforms(data)
        self.assertEqual(links[0]['waveforms'][0]['waveform']['MemoryAwbId'],7)
        data['tables']['SynthTable']['rows'][1]['ReferenceItems']=b'\0\2\0\1'
        with self.assertRaisesRegex(ValueError,'cycle'):
            cue_waveforms(data)

    def test_hca_samples_and_loop(self):
        data=bytearray(64)
        data[:12]=b'HCA\0'+struct.pack('>HH',0x200,64)+b'fmt\0'
        data[12]=2;data[13:16]=(48000).to_bytes(3,'big')
        struct.pack_into('>IHH',data,16,100,128,256)
        data[24:28]=b'loop';struct.pack_into('>IIHH',data,28,10,90,16,32)
        data[40:44]=b'ciph';struct.pack_into('>H',data,44,0)
        data[46:50]=b'pad\0'
        result=hca_header(data)
        self.assertEqual(result['samples'],102016)
        self.assertEqual(result['loop']['start_sample'],10128)
        self.assertEqual(result['loop']['end_sample'],93024)

    def test_awb_alignment_ids_and_corruption(self):
        data=bytearray(96)
        data[:16]=b'AFS2'+bytes([1,4,2,0])+struct.pack('<IHH',1,32,0)
        struct.pack_into('<HII',data,16,7,26,96)
        data[32:36]=b'RIFF'
        result=awb(io.BytesIO(data))
        self.assertEqual(result['records'][0]['id'],7)
        self.assertEqual(result['records'][0]['offset'],32)
        struct.pack_into('<I',data,22,1000)
        with self.assertRaises(ValueError):
            awb(io.BytesIO(data))


if __name__=='__main__':
    unittest.main()
