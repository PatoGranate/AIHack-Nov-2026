
import {mountChart} from 'https://persistent.oaistatic.com/plugins/visualize/charts/1.6.5/element.js';
const root=document.getElementById('v7-review');
const read=id=>JSON.parse(root.querySelector(id).textContent);
const data=read('#v7-data');
mountChart(root.querySelector('#v7-league [data-viz-container]'),read('#v7-league-config'));
const configs={F:read('#v7-f-config'),E:read('#v7-e-config')};
const chart=mountChart(root.querySelector('#v7-fields [data-viz-container]'),configs.F);
const select=root.querySelector('#v7-baseline');select.addEventListener('change',()=>{chart.config=configs[select.value]});
root.querySelector('#v7-status').textContent=`Independent league: ${data.rounds} rounds complete · ${data.allSeatErrors} errors reported across all seats`;
data.pairedLeagueDifferences.forEach(r=>{const el=document.createElement('div');el.className='difference-row';const label=document.createElement('span');label.textContent=r.comparison;const value=document.createElement('span');value.className='tabular-nums';const f=n=>(n>=0?'+':'')+n.toFixed(1);value.textContent=`${f(r.difference)} bb/100 · 95% CI ${f(r.ci95[0])} to ${f(r.ci95[1])}`;el.append(label,value);root.querySelector('#v7-differences').append(el)});
