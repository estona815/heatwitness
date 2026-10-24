const $=id=>document.getElementById(id);
const signed=n=>n>0?`+${n}`:String(n).replace('-','−');
const range=a=>a.hot_days_lower===a.hot_days_upper?`${a.hot_days_lower}`:`${a.hot_days_lower}–${a.hot_days_upper}`;
let current;
function period(target,a){
 const article=$(target);article.replaceChildren();
 for(const [tag,cls,text] of [['h2','',`${a.start.slice(0,4)} · June–August`],['div','count',`${range(a)} ${a.hot_days_lower===1&&a.hot_days_upper===1?'day':'days'}`],['p','coverage',`${a.valid_days} of ${a.calendar_days} observations usable`]]){
  const el=document.createElement(tag);el.className=cls;el.textContent=text;article.append(el);
 }
 const grid=document.createElement('div');grid.className='tiles';grid.setAttribute('role','img');
 grid.setAttribute('aria-label',`${a.hot_days_lower} observed hot days, ${a.valid_days-a.hot_days_lower} observed below, ${a.unknown_days} unknown`);
 for(const d of a.days){const tile=document.createElement('span');tile.className=`tile ${['hot','below'].includes(d.status)?d.status:'unknown'}`;tile.title=`${d.date}: ${d.status}${d.source?.value_tenths_c!=null?`, ${d.source.value_tenths_c/10}°C`:''}`;grid.append(tile)}
 article.append(grid);
}
try{
 const response=await fetch('audits.json');if(!response.ok)throw Error('Cannot read local audit data');
 const data=await response.json();
 for(const id of ['before','after'])for(const year of Object.keys(data.audits['300'])){const option=document.createElement('option');option.value=year;option.textContent=year;$(id).append(option)}
 $('before').value='2014';$('after').value='2024';$('source-hash').textContent=data.source_sha256;
 function render(){
  const before=data.audits[$('threshold').value][$('before').value],after=data.audits[$('threshold').value][$('after').value];
  let lower=after.hot_days_lower-before.hot_days_upper,upper=after.hot_days_upper-before.hot_days_lower;
  // Reusing the exact same period is an identity, not two independent missing datasets.
  if(before.start===after.start){lower=0;upper=0;}
  const title=lower>0?'More hot days':upper<0?'Fewer hot days':lower===0&&upper===0?'Same count':'Unresolved';
  $('conclusion').textContent=title;
  $('explanation').textContent=title==='Unresolved'?'Missing observations could reverse or erase the apparent difference.':title==='Same count'?'These inputs produce the same count.':'The direction holds even under the worst-case completion of missing data.';
  period('period-before',before);period('period-after',after);
  $('difference').textContent=`${signed(lower)} to ${signed(upper)} days`;
  $('evidence').replaceChildren();
  for(const a of [before,after]){const tr=document.createElement('tr');for(const value of [a.start.slice(0,4),a.calendar_days,a.valid_days,a.unknown_days,range(a)]){const td=document.createElement('td');td.textContent=value;tr.append(td)}$('evidence').append(tr)}
  current={schema:'heatwitness-browser/v1',station:data.station,source_sha256:data.source_sha256,provenance:data.provenance,before,after,comparison:{difference_lower:lower,difference_upper:upper,conclusion:title},limitations:'Worst-case bounds, not confidence intervals. No climate-trend or attribution claim.'};
 }
 $('controls').addEventListener('change',render);$('controls').addEventListener('submit',e=>e.preventDefault());
 $('download').disabled=false;$('download').addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(current,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=`heatwitness-${$('before').value}-${$('after').value}-${$('threshold').value}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)});
 render();
}catch(error){$('conclusion').textContent='Source data unavailable';$('explanation').textContent='Serve this folder over localhost and ensure audits.json exists. No result has been inferred.';console.error(error)}
