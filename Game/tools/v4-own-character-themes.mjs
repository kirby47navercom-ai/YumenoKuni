import fs from 'node:fs/promises';
import path from 'node:path';
// Character wallpaper is content, not a license to display the original cast.
// Reuse V3's empty screen-wall theme and put this project's portraits in its wall.
export async function ownCharacterThemes({repo,contract}){
 const bank=contract.provided_bank_check.theme_backgrounds.resources;
 const screen=await fs.readFile(bank.find(r=>r.type_id===22).path);
 const manifest=JSON.parse(await fs.readFile(path.join(repo,'art/character_delivery_v4/manifest.json'),'utf8'));
 const characters=JSON.parse(await fs.readFile(path.join(repo,'data/characters.json'),'utf8'));
 const cast=['mio','rei','sora','ken','nana','riku','akari','yuu','koto','satsuki','taiga','rin','sho','ai','haruka','kaede'],result=new Map();
 if(characters.length<16)throw Error('Expected the existing sixteen own profiles');
 const wrap=ink=>`<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080"><image href="data:image/png;base64,${screen.toString('base64')}" width="1920" height="1088"/>${ink}</svg>`;
 const portrait=async who=>{const file='art/character_delivery_v4/portraits/'+who+'.webp',row=manifest.assets.find(r=>r.file===file);if(!row?.alpha_bbox)throw Error('Missing own portrait bounds '+who);const image=await fs.readFile(path.join(repo,file)),[x,y,right,bottom]=row.alpha_bbox;
  return `<svg x="166" y="116" width="1000" height="350" viewBox="${x} ${y} ${right-x} ${(bottom-y)*.63}" preserveAspectRatio="xMidYMin meet"><image href="data:image/webp;base64,${image.toString('base64')}" width="${row.size[0]}" height="${row.size[1]}"/></svg>`;};
 for(let i=0;i<cast.length;i++)result.set(i+2,{name:characters[i].heading.split(' (')[0].replace(/ —.*/,''),svg:wrap(await portrait(cast[i])),ownActor:cast[i],sourceCarrier:22});
 for(const type of [20,26])result.set(type,{name:type===20?'래피':'래피 · 흑백',svg:wrap(type===26?`<defs><filter id="mono"><feColorMatrix type="saturate" values="0"/></filter></defs><g filter="url(#mono)">${await portrait('lappy')}</g>`:await portrait('lappy')),ownActor:'lappy',sourceCarrier:22});
 const court=await fs.readFile(path.join(repo,'bg/trial_room.webp'));result.set(18,{name:'학급 재판',svg:`<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080"><image href="data:image/webp;base64,${court.toString('base64')}" width="1920" height="1080" preserveAspectRatio="xMidYMid slice"/></svg>`,ownWorld:true});
 return result;
}

export async function emitOwnThemeMasks({repo,write}){
 const contract=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/pad_system_connection_contract.json'),'utf8'));
 const themes=await ownCharacterThemes({repo,contract});
 for(const [type,theme]of themes){
  const image=Buffer.from(theme.svg).toString('base64');
  await write('Assets/Art/ui/v3/map_mask/type_'+String(type).padStart(3,'0')+'.svg',`<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720"><defs><clipPath id="outside"><path fill-rule="evenodd" clip-rule="evenodd" d="M0 0H1280V720H0ZM340 140V660H1220V140Z"/></clipPath></defs><image href="data:image/svg+xml;base64,${image}" width="1280" height="720" preserveAspectRatio="none" clip-path="url(#outside)"/></svg>`);
 }
 return {masks:themes.size,sourceClip:[340,140,880,520],ownCastAndWorld:true};
}
