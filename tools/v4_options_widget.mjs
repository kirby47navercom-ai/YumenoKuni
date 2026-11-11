import {createAudioMixer,validAudioMixer,mixerDefaults} from '../Game/engineCreate/prototype/audio-mixer.js';
import {emitSourceOptions} from './v4_options_source.mjs';
export async function emitOptionsV4({repo,copy,write}){
 const mixer=createAudioMixer('MX_Yumeno');
 mixer.buses.push({id:'voice',name:'Voice',parent:'master',...mixerDefaults});
 mixer.exposed=[['Master','master'],['Music','music'],['SFX','sfx'],['UI','ui'],['Voice','voice']].map(([name,bus])=>({name,bus,parameter:'volumeDb'}));
 if(!validAudioMixer(mixer))throw Error('V4 mixer contract invalid');
 await write('Assets/Audio/MX_Yumeno.hbaudiomixer.json',mixer);
 const nodes=await emitSourceOptions({repo,write});
 return {widget:'Assets/UI/OptionsV4.hbwidget.json',mixer:'Assets/Audio/MX_Yumeno.hbaudiomixer.json',nodes,rows:8,totalSettings:15};
}
