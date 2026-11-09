export function verdictMachine(svg,angled){
 const palette=['#b83961','#5484b7','#c98840','#d1aa49','#5d578d','#398887'];
 const ring=Array.from({length:16},(_,i)=>`<path d="M-29-148L-42-220Q0-228 42-220L29-148Z" transform="rotate(${22.5*i})" fill="${palette[i%palette.length]}" stroke="#242033" stroke-width="4"/>`).join('');
 const bulbs=Array.from({length:40},(_,i)=>{
  const a=i*Math.PI/20;return `<circle cx="${Math.cos(a)*240}" cy="${Math.sin(a)*240}" r="4.8" fill="#fff9ce"/>`;
 }).join('');
 const rails=Array.from({length:32},(_,i)=>[33,577].map(x=>`<rect x="${x-7}" y="${119+i*14}" width="14" height="10" rx="5" fill="url(#lamp)"/>`).join('')).join('');
 const trim=angled?'translate(0 61) scale(1 .82)':'';
 const tray=Array.from({length:5},(_,i)=>`<ellipse cx="${94+i*106}" cy="${angled?585:649}" rx="44" ry="${angled?17:10}" fill="#170e1f" stroke="url(#brass)" stroke-width="4"/>`).join('');
 return svg(610,700,`<defs>
 <linearGradient id="red" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#ee614b"/><stop offset=".22" stop-color="#9b2436"/><stop offset=".62" stop-color="#501630"/><stop offset="1" stop-color="#22142d"/></linearGradient>
 <linearGradient id="brass" x2="0" y2="1"><stop stop-color="#fff6b9"/><stop offset=".21" stop-color="#d19237"/><stop offset=".43" stop-color="#98501a"/><stop offset=".65" stop-color="#fbd47a"/><stop offset=".89" stop-color="#86541f"/><stop offset="1" stop-color="#ebbd62"/></linearGradient>
 <linearGradient id="deck" x2="0" y2="1"><stop stop-color="#b43846"/><stop offset="1" stop-color="#321323"/></linearGradient>
 <radialGradient id="lamp"><stop stop-color="#fffce0"/><stop offset=".55" stop-color="#fff1bc"/><stop offset="1" stop-color="#f8a24e"/></radialGradient>
 <radialGradient id="glass"><stop stop-color="#302744"/><stop offset="1" stop-color="#111524"/></radialGradient>
 <pattern id="grid" width="5" height="5" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r=".8" fill="#bd9138" opacity=".38"/></pattern>
 </defs>
 <path d="${angled?'M11 141H599L610 625 579 682H31L0 625Z':'M19 44H592L605 630 581 678H34L5 630Z'}" fill="#211322" stroke="#281721" stroke-width="12"/>
 <path d="M35 615H575L588 662 542 691H68L22 662Z" fill="url(#red)" stroke="#361728" stroke-width="6"/>
 <path d="M57 632H553L536 675H73Z" fill="#321527" stroke="#682a33" stroke-width="4"/>
 <g ${trim?`transform="${trim}"`:""}>
 <path d="M63 29H547L587 73 600 575 562 627H48L10 575 23 73Z" fill="url(#red)" stroke="url(#brass)" stroke-width="6"/>
 <path d="M79 47H531L554 76H56Z" fill="#5d1629" stroke="#de6c47" stroke-width="3"/>
 <path d="M56 87H554L575 597H35Z" fill="#381a34" stroke="#d1833d" stroke-width="5"/>
 <path d="M70 102H540L556 570H54Z" fill="url(#glass)"/>
 <text x="305" y="83" font-family="Arial" font-weight="900" font-size="50" letter-spacing="9" text-anchor="middle" fill="#ffd99c" stroke="#671d2b" stroke-width="2">VERDICT</text>
 <path d="M126 104H484L468 155H142Z" fill="#11111d" stroke="url(#brass)" stroke-width="5"/>
 <path d="M134 111H476L463 149H147Z" fill="url(#grid)"/>
 <path d="M21 108H46V568H21Z M564 108H589V568H564Z" fill="#8a482d" stroke="url(#brass)" stroke-width="3"/>${rails}
 <g transform="translate(305 373)">
 <circle r="252" fill="#472333" stroke="#c48638" stroke-width="5"/>
 <circle r="241" fill="url(#brass)" stroke="#f5cc79" stroke-width="5"/>${bulbs}
 <circle r="226" fill="#1e192b" stroke="#261323" stroke-width="5"/>${ring}
 <circle r="148" fill="url(#glass)" stroke="url(#brass)" stroke-width="8"/>
 <circle r="136" fill="url(#grid)" opacity=".34"/>
 </g>
 </g>
 <path d="${angled?'M24 555H586L608 604 573 635H37L2 604Z':'M45 630H565L586 653 561 676H49L24 653Z'}" fill="url(#deck)" stroke="url(#brass)" stroke-width="6"/>
 ${tray}
 <path d="${angled?'M32 615H578':'M49 663H561'}" stroke="#fff0a0" stroke-width="4" stroke-dasharray="4 5"/>
 `);
}

