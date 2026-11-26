const $=id=>document.getElementById(id), form=$('settings');
let result;
const percent=x=>(x*100).toFixed(2)+'%';
const line=(x1,y1,x2,y2,color,dash='')=>`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" ${dash ? `stroke-dasharray="${dash}"` : ''}/>`;
function chart(series,maxX,{bars=false,maxY=1,budget=null,xLabel='Additional pulls'}={}) {
  const w=760,h=300,l=52,r=16,t=16,b=46,pw=w-l-r,ph=h-t-b;
  const x=v=>l+(bars ? (v+.5)/(maxX+1) : v/Math.max(1,maxX))*pw,y=v=>t+(1-v/maxY)*ph;
  let svg=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${xLabel} chart"><title>${series.map(s=>s.name).join(', ')} by ${xLabel.toLowerCase()}</title>`;
  for(let i=0;i<=4;i++){const v=i*maxY/4;svg+=line(l,y(v),w-r,y(v),'#263943')+`<text x="${l-8}" y="${y(v)+4}" text-anchor="end">${Math.round(v*100)}%</text>`;}
  const ticks=Math.min(4,maxX);
  for(let i=0;i<=ticks;i++){const v=Math.round(i*maxX/Math.max(1,ticks));svg+=`<text x="${x(v)}" y="${h-25}" text-anchor="middle">${v}</text>`;}
  svg+=`<text x="${l+pw/2}" y="${h-5}" text-anchor="middle">${xLabel}</text>`;
  for(const s of series) {
    if(bars) {
      for(const [v,n] of s.values) svg+=`<rect x="${x(v)-pw/(maxX+1)*.35}" y="${y(n)}" width="${pw/(maxX+1)*.7}" height="${ph*n/maxY}" rx="2" fill="${s.color}"><title>${v}: ${percent(n)}</title></rect>`;
    } else {
      svg+=`<polyline fill="none" stroke="${s.color}" stroke-width="2.5" ${s.dash ? 'stroke-dasharray="6 5"' : ''} points="${s.values.map(([v,n])=>`${x(v)},${y(n)}`).join(' ')}"/>`;
    }
  }
  if(budget!==null && budget<=maxX) svg+=line(x(budget),t,x(budget),h-b,'#d7bf83','4 5')+`<text x="${Math.max(l+38,Math.min(w-r-40,x(budget)))}" y="${t+11}" text-anchor="middle">Budget: ${budget}</text>`;
  return svg+'</svg>';
}
function render(r) {
  const s=r.settings, probability=r.exact[Math.min(s.budget,r.horizon)], p=r.successes/s.runs,z=1.96,den=1+z*z/s.runs;
  const center=(p+z*z/(2*s.runs))/den, margin=z*Math.sqrt(p*(1-p)/s.runs+z*z/(4*s.runs*s.runs))/den;
  $('metrics').innerHTML=[['Success · exact model',percent(probability)],['Success · simulation',percent(p)],['Mean pulls · exact model',r.mean.toFixed(1)],['Hard guarantee',r.horizon+' pulls']].map(([label,value])=>`<div><span>${label}</span><strong>${value}</strong></div>`).join('');
  $('interval').textContent=`Simulation 95% Wilson interval: ${percent(Math.max(0,center-margin))}–${percent(Math.min(1,center+margin))}. Mean pulls includes complete trials beyond the budget.`;
  const points=values=>Array.from(values,(v,i)=>[i,v]);
  $('curve').innerHTML=chart([{name:'Exact model',values:points(r.exact),color:'#7ce6cf'},{name:'Simulation',values:points(r.empirical),color:'#b6a2ff',dash:true},{name:'Opposite guarantee',values:Array.from(r.exact,(_,i)=>[i,r.alternative[Math.min(i,r.alternative.length-1)]]),color:'#8195a2',dash:true}],r.horizon,{budget:s.budget});
  $('thresholds').innerHTML=[.5,.9,.95,.99].map(q=>`<div><span>${q*100}% chance</span><strong>${r.exact.findIndex(v=>v>=q-1e-12)}</strong><span>additional pulls</span></div>`).join('');
  const binWidth=Math.max(1,Math.ceil(r.horizon/40)),bins=[];
  for(let start=1;start<=r.horizon;start+=binWidth){let n=0;for(let i=start;i<Math.min(start+binWidth,r.counts.length);i++) n+=r.counts[i];bins.push([start+(Math.min(binWidth,r.horizon-start+1)-1)/2,n/s.runs]);}
  // Draw histogram bins as adjacent wide rectangles on a bin-number axis.
  $('histogram').innerHTML=histogram(bins,binWidth,r.horizon,s.budget);
  $('copies-chart').innerHTML=chart([{name:'Copies obtained',values:Array.from(r.copiesCounts,(n,i)=>[i,n/s.runs]),color:'#7ce6cf'}],s.copies,{bars:true,xLabel:'Featured copies'});
  $('rates-chart').innerHTML=chart([{name:'Assumed five-star probability',values:Array.from(r.rates,(v,i)=>[i+1,v]),color:'#7ce6cf'}],80,{xLabel:'Pull since last five-star'});
  $('preview').innerHTML='<table><thead><tr><th>Trial</th>'+Array.from({length:s.copies},(_,i)=>`<th>Pull for copy ${i+1}</th>`).join('')+'<th>Within budget</th></tr></thead><tbody>'+Array.from({length:Math.min(100,s.runs)},(_,i)=>'<tr><td>'+(i+1)+'</td>'+Array.from(r.times.slice(i*s.copies,(i+1)*s.copies),v=>`<td>${v}</td>`).join('')+`<td>${r.times[(i+1)*s.copies-1]<=s.budget ? 'Yes' : 'No'}</td></tr>`).join('')+'</tbody></table>';
  $('output').hidden=false;
  $('status').textContent=`${s.budget} pulls · ${s.pity} pity · ${s.copies} additional ${s.copies===1?'copy':'copies'} · ${s.guaranteed?'Guaranteed':'50/50'} · ${s.runs.toLocaleString()} trials · ${s.soft?'Illustrative soft pity':'Simplified model'}`;
}
function histogram(bins,width,horizon,budget) {
  const maxY=Math.max(.05,...bins.map(v=>v[1]))*1.15;
  let svg=chart([],horizon,{maxY,budget});
  const rects=bins.map(([pull,value])=>`<rect x="${52+(pull-width/2)/horizon*692}" y="${16+(1-value/maxY)*238}" width="${Math.max(1,width/horizon*692-1)}" height="${value/maxY*238}" fill="#7ce6cf" opacity=".8"><title>Pulls ${Math.ceil(pull-(width-1)/2)}–${Math.min(horizon,Math.floor(pull+(width-1)/2))}: ${percent(value)}</title></rect>`).join('');
  return svg.replace('</svg>',rects+'</svg>');
}
form.addEventListener('submit',event=>{
  event.preventDefault();if(!form.reportValidity()) return;
  const fields=new FormData(form),s={};
  for(const key of ['budget','pity','copies','runs','seed','softStart','step']) s[key]=Number(fields.get(key));
  s.guaranteed=fields.has('guaranteed');s.soft=fields.has('soft');
  $('run').disabled=true;$('run').textContent='Calculating…';$('status').textContent='Simulating pulls and calculating probabilities…';document.querySelector('.results').setAttribute('aria-busy','true');
  const worker=new Worker('engine.js');
  const finish=()=>{worker.terminate();$('run').disabled=false;$('run').textContent='Run analysis →';document.querySelector('.results').setAttribute('aria-busy','false');};
  worker.onmessage=({data})=>{try{if(data.error) throw new Error(data.error);result=data.result;render(result);}catch(error){$('status').textContent='Analysis failed: '+error.message;}finally{finish();}};
  worker.onerror=()=>{$('status').textContent='Could not load the calculator. Refresh the page and try again.';finish();};
  worker.postMessage(s);
});
document.querySelectorAll('[data-panel]').forEach(button=>button.addEventListener('click',()=>{
  document.querySelectorAll('[data-panel]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
  document.querySelectorAll('.panel').forEach(p=>p.hidden=p.id!==button.dataset.panel);
}));
document.querySelectorAll('[data-download]').forEach(button=>button.addEventListener('click',()=>{
  if(!result) return;const r=result,s=r.settings,type=button.dataset.download;let content,mime,extension;
  if(type==='settings'){content=JSON.stringify(s,null,2);mime='application/json';extension='json';}
  else {
    mime='text/csv';extension='csv';
    if(type==='curve') content='additional_pulls,exact_model_probability,simulated_probability\n'+Array.from(r.exact,(v,i)=>`${i},${v},${r.empirical[i]}`).join('\n');
    else content='trial,'+Array.from({length:s.copies},(_,i)=>'pull_for_copy_'+(i+1)).join(',')+',goal_reached_within_budget,copies_within_budget_capped_at_goal\n'+Array.from({length:s.runs},(_,i)=>{const times=Array.from(r.times.slice(i*s.copies,(i+1)*s.copies));return [i+1,...times,times[s.copies-1]<=s.budget,times.filter(t=>t<=s.budget).length].join(',');}).join('\n');
  }
  const url=URL.createObjectURL(new Blob([content],{type:mime})),a=document.createElement('a');a.href=url;a.download=`wuwa_${type}.${extension}`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}));
form.requestSubmit();
