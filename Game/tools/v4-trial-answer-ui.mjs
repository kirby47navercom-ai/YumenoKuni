import fs from 'node:fs/promises';
import path from 'node:path';

// One source family: trial multiple-choice answers. ADV/person/evidence UIs are separate.
export async function emitTrialAnswerUI({repo,write}){
 const c=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/trial_answer_choice_ui_contract.json'),'utf8'));
 const svg=s=>`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" preserveAspectRatio="none">${s}</svg>`;
 const source=JSON.parse(await fs.readFile(path.join(repo,'ui/v4/trial_inputs_source/manifest.json'),'utf8'));
 const image=async name=>'data:image/png;base64,'+(await fs.readFile(path.join(repo,source.records[name].file))).toString('base64');
 const rowImages={middle:await image('choice_middle'),edge:await image('choice_edge'),gray:await image('choice_gray')};
 const suffix=i=>String(i).padStart(3,'0');
 const color=l=>{const a=l.composed_color_add_rgba||[0,0,0,0],m=l.composed_color_multiply_rgba||[1,1,1,1];return `rgb(${[0,1,2].map(i=>Math.round(Math.min(1,Math.max(0,m[i]+a[i]))*255)).join(',')})`;};
 const frame=async(leaves,asset,count)=>{
  const rows=[];let ink='';
  for(const l of leaves){const r=l.own_projection_rect_1280,a=l.composed_alpha_from_identity??1;if(!r||a<=0)continue;
   // Missing texture alpha leaves dormant template cursors opaque; only paint admitted answer rows.
   const decor=l.path.match(/^i_(?:t_choice_cursor_(?:naka|hashi)|gray)_(\d+)\//);if(decor&&Number(decor[1])>=count)continue;
   const [x,y,w,h]=r;
   const key=l.path.startsWith('i_t_choice_cursor_naka_')?'middle':l.path.startsWith('i_gray_')?'gray':l.path.startsWith('i_t_choice_cursor_hashi_')?'edge':null;
   if(key){const id='r'+rows.length+'_'+ink.length,m=l.composed_color_multiply_rgba||[1,1,1,1],c=l.composed_color_add_rgba||[0,0,0,0];ink+=`<defs><filter id="${id}" color-interpolation-filters="sRGB"><feColorMatrix values="${m[0]} 0 0 0 ${c[0]} 0 ${m[1]} 0 0 ${c[1]} 0 0 ${m[2]} 0 ${c[2]} 0 0 0 1 0"/></filter></defs><image href="${rowImages[key]}" x="${x}" y="${y}" width="${w}" height="${h}" opacity="${a}" preserveAspectRatio="none" filter="url(#${id})"/>`;}

  }
  for(let i=0;i<count;i++){
   const text=leaves.find(l=>l.path===`p_t_choice_${suffix(i)}/p_t_choice_${suffix(i)}`),check=leaves.find(l=>l.path===`p_t_choice_check_${suffix(i)}/depth1`),number=leaves.find(l=>l.path===`p_t_choice_num_${suffix(i)}/depth1`);
   rows.push({text:text?.own_projection_rect_1280||c.answer_geometry_summary.wait_text_own[i],showText:!!text&&(text.composed_alpha_from_identity??1)>0,textColor:text?color(text):'#fff',check:check?.own_projection_rect_1280||[0,0,0,0],showCheck:!!check&&(check.composed_alpha_from_identity??1)>0,number:number?.own_projection_rect_1280||[0,0,0,0],showNumber:!!number&&(number.composed_alpha_from_identity??1)>0});
  }
  await write(asset,svg(ink));return {asset,rows};
 };
 const layout={font:c.answer_geometry_summary.nominal_own_font,counts:[2,3,4],wait:{},tracks:{},question:[227.333333,610,813.33374,100],title:[272.266667,186.666667,341.333333,85.333333],frame:[-6.666667,162.666667,1293.333333,341.333333],scope:'Source trial2/3/4 positions, nine distinct actual6selection+19confirmation record geometries/color chains. Original t_choice cursor/number/check rasters and t_choice_frame_US frame are now connected. Actual retained source geometry/color chains and60Hz record admission remain; own localized text preserves authored meaning, source runtime timing is not observed. Checks mean confirmed indices, not correctness. Prompt remains in separate dialogue position.'};
 for(const count of layout.counts)layout.wait[count]=await frame(c.families.answers.snapshots['fl_wait_'+count],`Assets/Art/ui/v3/trial_answer/wait_${count}.svg`,count);
 for(const track of c.selection_and_confirmation.tracks){
  const key=track.choice_count+'_'+track.zero_based_index,out={select:[],confirm:[]};
  for(const record of track.actual_record_leaf_colors){const phase=record.phase==='selection'?'select':'confirm';const asset=`Assets/Art/ui/v3/trial_answer/${key}_${phase}_${out[phase].length}.svg`;out[phase].push(await frame(record.leaves,asset,track.choice_count));}
  const file=`Assets/Data/v4_story/trial_answer_${key}.json`;await write(file,out);layout.tracks[key]=file;
 }
 await write('Assets/Art/ui/v3/trial_answer/frame.svg',svg(`<image href="${await image('choice_frame')}" width="1280" height="720"/>`));
 await write('Assets/Art/ui/v3/trial_answer/check.svg',`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><image href="${await image('choice_check')}" width="64" height="64"/></svg>`);
 for(let i=0;i<4;i++)await write(`Assets/Art/ui/v3/trial_answer/number_${i}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><image href="${await image('choice_number_'+i)}" width="64" height="64"/></svg>`);
 await write('Assets/Data/v4_story/trial_answer_layout.json',layout);return layout;
}
