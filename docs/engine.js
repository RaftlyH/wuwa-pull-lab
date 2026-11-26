/* Calculation core shared by the browser worker and Node validation. */
function validate(s) {
  for (const [key, min, max] of [['budget',0,1120],['pity',0,79],['copies',1,7],['runs',1,50000],['seed',0,2147483647],['softStart',2,79]]) {
    if (!Number.isInteger(s[key]) || s[key] < min || s[key] > max) throw new Error(`Invalid ${key}.`);
  }
  if (!Number.isFinite(s.step) || s.step < 0 || s.step > 20) throw new Error('Invalid soft-pity increase.');
}
function probabilities(s) {
  return Float64Array.from({length:80}, (_,i) => i===79 ? 1 : Math.min(1,.008+(s.soft ? Math.max(0,i+2-s.softStart)*s.step/100 : 0)));
}
function maximumPulls(s) { return 160*s.copies-s.pity-(s.guaranteed ? 80 : 0); }
function exactCDF(s) {
  const rates=probabilities(s), horizon=maximumPulls(s), cdf=new Float64Array(horizon+1);
  let state=new Float64Array(s.copies*160), completed=0;
  state[(s.guaranteed ? 80 : 0)+s.pity]=1;
  for(let pull=1;pull<=horizon;pull++) {
    const next=new Float64Array(state.length);
    for(let c=0;c<s.copies;c++) for(let g=0;g<2;g++) for(let p=0;p<80;p++) {
      const idx=c*160+g*80+p, mass=state[idx];
      if(!mass) continue;
      if(p<79) next[idx+1]+=mass*(1-rates[p]);
      const hit=mass*rates[p], win=hit*(g ? 1 : .5);
      if(!g) next[c*160+80]+=hit*.5;
      if(c+1===s.copies) completed+=win; else next[(c+1)*160]+=win;
    }
    cdf[pull]=Math.min(1,Math.max(0,completed)); state=next;
  }
  return cdf;
}
function randomGenerator(seed) {
  let a=seed>>>0;
  return () => {a=(a+0x6D2B79F5)>>>0;let t=Math.imul(a^(a>>>15),1|a);t^=t+Math.imul(t^(t>>>7),61|t);return ((t^(t>>>14))>>>0)/4294967296;};
}
function simulate(s) {
  const random=randomGenerator(s.seed), rates=probabilities(s), times=new Uint16Array(s.runs*s.copies);
  for(let trial=0;trial<s.runs;trial++) {
    let pity=s.pity, guaranteed=s.guaranteed, copies=0;
    for(let pull=1;copies<s.copies && pull<=maximumPulls(s);pull++) {
      if(random()<rates[pity]) {
        pity=0;
        if(guaranteed || random()<.5) {times[trial*s.copies+copies++]=pull;guaranteed=false;} else guaranteed=true;
      } else pity++;
    }
    if(!times[(trial+1)*s.copies-1]) throw new Error('A trial exceeded the guarantee bound.');
  }
  return times;
}
function analyze(s) {
  validate(s);
  const exact=exactCDF(s), alternative=exactCDF({...s,guaranteed:!s.guaranteed}), times=simulate(s), horizon=exact.length-1;
  const counts=new Uint32Array(horizon+1), copiesCounts=new Uint32Array(s.copies+1);
  let successes=0;
  for(let t=0;t<s.runs;t++) {
    const final=times[(t+1)*s.copies-1];counts[final]++;if(final<=s.budget) successes++;
    let n=0;for(let c=0;c<s.copies;c++) if(times[t*s.copies+c]<=s.budget) n++;copiesCounts[n]++;
  }
  let cumulative=0,mean=0;const empirical=Float64Array.from(counts,n=>(cumulative+=n)/s.runs);
  for(let i=0;i<horizon;i++) mean+=1-exact[i];
  return {settings:s,exact,alternative,times,horizon,counts,copiesCounts,successes,empirical,mean,rates:probabilities(s)};
}
if(typeof module!=='undefined') module.exports={validate,probabilities,maximumPulls,exactCDF,simulate,analyze};
if(typeof WorkerGlobalScope!=='undefined' && self instanceof WorkerGlobalScope) self.onmessage=({data})=>{
  try {self.postMessage({result:analyze(data)});} catch(error) {self.postMessage({error:error.message});}
};
