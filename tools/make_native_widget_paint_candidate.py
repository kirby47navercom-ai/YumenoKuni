from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'Game/tools/native-widget-frame.candidate.mjs';s=p.read_text(encoding='utf8')
s=s.replace('update:()=>{this.revision++;this.pruneImages();','update:()=>{this.revision++;')
hook='''const prepare=view.fontsReady;let assetStamp;
view.fontsReady=async()=>{const used=new Set();for(const node of data.nodes){const p=node.properties;for(const name of [p.font,p.texture,p.vectorTexture,p.backgroundTexture,p.fillTexture])if(name)used.add(name);}const stamp=[...used].sort().join('\\0');if(stamp===assetStamp)return;await prepare();assetStamp=stamp;};'''
needle='this.ownedViews.add(view);this.views.add(view);this.revision++;return view;'
assert s.count(needle)==1;s=s.replace(needle,hook+needle)
s=s.replace("const p={...widgetDefaults,...node.properties};if(!p.visible||p.deviceVisibility==='touch')return;", "if(node.properties.visible===false||node.properties.deviceVisibility==='touch')return;const p=node.properties;")
s=s.replace('ctx.rotate(p.rotation*Math.PI/180);ctx.scale(...p.scale);','ctx.rotate((p.rotation??widgetDefaults.rotation)*Math.PI/180);ctx.scale(...(p.scale??widgetDefaults.scale));')
old="ctx.fillStyle=this.down?.node===node?p.pressed:this.hover?.node===node&&node.type==='Button'?p.hover:p.background;ctx.beginPath();ctx.roundRect(0,0,w,h,Math.min(p.radius*scale,w/2,h/2));ctx.fill();if(border)"
new="const fillColor=this.down?.node===node?p.pressed:this.hover?.node===node&&node.type==='Button'?p.hover:p.background;if(fillColor.length!==9||!fillColor.endsWith('00')){ctx.fillStyle=fillColor;ctx.beginPath();ctx.roundRect(0,0,w,h,Math.min(p.radius*scale,w/2,h/2));ctx.fill();}if(border)"
# Canvas fillStyle may normalize transparent hex to rgba(...); preserve the
# original draw in that case. Only an exact zero-alpha hex skips a no-op fill.
assert s.count(old)==1;s=s.replace(old,new)
(root/'Game/tools/native-widget-paint.candidate.mjs').write_text(s,encoding='utf8')
print('Created asset preparation and transparent paint candidate')
