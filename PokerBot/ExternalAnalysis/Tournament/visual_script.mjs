
import {mountChart} from 'https://persistent.oaistatic.com/plugins/visualize/charts/1.6.5/element.js';
const root=document.getElementById('poker-league');
const data=JSON.parse(root.querySelector('#poker-data').textContent);
data.profiles.forEach((text,i)=>{const p=document.createElement('p');p.className='text-small';p.textContent=data.manifest[i].name+' — '+text;root.querySelector('#poker-policies').append(p)});
const configs={fast:JSON.parse(root.querySelector('#poker-fast-config').textContent),strict:JSON.parse(root.querySelector('#poker-strict-config').textContent)};
const chart=mountChart(root.querySelector('#poker-profit [data-viz-container]'),configs.fast);
const styleConfig=JSON.parse(root.querySelector('#poker-style-config').textContent);
mountChart(root.querySelector('#poker-style [data-viz-container]'),styleConfig);
styleConfig.rows.forEach(r=>{const p=document.createElement('p');p.className='text-small';p.textContent=`${r.bot} · ${r.metric}: ${r.events.toLocaleString()} / ${r.opportunities.toLocaleString()}`;root.querySelector('#poker-style-counts').append(p)});
const mode=root.querySelector('#poker-mode');
function showMode(){const d=data[mode.value];chart.config=configs[mode.value];root.querySelector('#poker-context').textContent=mode.value==='fast'?`${d.tableHands.toLocaleString()} table hands · ${d.rows[0].hands.toLocaleString()} hands per bot · external deadlines not enforced`:`${d.tableHands.toLocaleString()} table hands · 10 ms decisions / 10 s bank · local Windows runtime`;
root.querySelector('#poker-timing').replaceChildren(...d.rows.map(r=>{const el=document.createElement('div');el.className='timing-row';const name=document.createElement('span');name.textContent=r.name;const val=document.createElement('span');val.className='tabular-nums';val.textContent=`${r.timeouts} timeouts · ${r.bankOut} bank-outs · ${r.errors} errors · max ${r.maxMs.toFixed(1)} ms`;el.append(name,val);return el}));}
mode.addEventListener('change',showMode);showMode();
const select=root.querySelector('#poker-probe');
data.probes.forEach((p,i)=>{const opt=document.createElement('option');opt.value=i;opt.textContent=`${i+1} · ${p.state.street} · ${p.state.hole_cards.join(' ')} · call ${p.state.to_call}`;select.append(opt)});
function showProbe(){const p=data.probes[Number(select.value)];if(!p)return;const s=p.state;root.querySelector('#poker-state').textContent=`Hero ${s.hole_cards.join(' ')} | Board ${s.board.join(' ')} | Pot ${s.pot} | To call ${s.to_call} | Pot odds ${(s.to_call/(s.pot+s.to_call)*100).toFixed(1)}% | ${s.folded.filter(x=>!x).length} live players`;
root.querySelector('#poker-decisions').replaceChildren(...p.bots.map(b=>{const el=document.createElement('div');el.className='decision-item';const name=document.createElement('div');name.textContent=data.manifest[b.id].name;const action=document.createElement('strong');action.textContent=`${b.action.action}${b.action.amount!=null?' to '+b.action.amount:''}`;const estimate=document.createElement('div');estimate.className='text-small tabular-nums';estimate.textContent=b.equity==null?'Equity unavailable':`Estimated equity ${(b.equity*100).toFixed(1)}%${b.samples?' · '+b.samples+' samples':''}`;el.append(name,action,estimate);if(b.equity!=null){const track=document.createElement('div');track.className='progress';track.setAttribute('role','progressbar');track.setAttribute('aria-label',name.textContent+' estimated equity');track.setAttribute('aria-valuenow',b.equity*100);track.setAttribute('aria-valuemin','0');track.setAttribute('aria-valuemax','100');const bar=document.createElement('div');bar.className='progress-bar';bar.style.width=(b.equity*100)+'%';track.append(bar);el.append(track)}return el}));}
select.addEventListener('change',showProbe);showProbe();
