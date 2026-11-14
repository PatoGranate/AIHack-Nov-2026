const fs=require('fs'),vm=require('vm');
const html=fs.readFileSync('C:/Users/pelay/.codex/visualizations/2026/11/14/01a1da50-efb7-7ba0-b530-229f1b9ff62c/poker-comparison.html','utf8');
class El{constructor(){this.children=[];this.style={};this.listeners={};this.value='0';}append(...x){this.children.push(...x)}replaceChildren(...x){this.children=x}setAttribute(){}addEventListener(k,f){this.listeners[k]=f}}
const els={};for(const id of [...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]))els['#'+id]=new El();
for(const m of html.matchAll(/<script[^>]*id="([^"]+)"[^>]*>(.*?)<\/script>/gs))els['#'+m[1]].textContent=m[2];
els['#poker-mode'].value='fast';els['#poker-probe'].value='0';
const root={querySelector:q=>els[q]||(els[q]=new El())},charts=[];
const document={getElementById:()=>root,createElement:()=>new El()};
const script=html.match(/<script type="module">(.*?)<\/script>/s)[1].replace(/^import .*?;\s*/m,'');
vm.runInNewContext(script,{document,mountChart:(el,c)=>{const x={config:c};charts.push(x);return x},console});
if(charts.length!==2||els['#poker-decisions'].children.length!==7)throw Error('Initial view failed');
els['#poker-mode'].value='strict';els['#poker-mode'].listeners.change();
if(!charts[0].config.title.includes('enforced'))throw Error('Mode switch failed');
const before=els['#poker-state'].textContent;els['#poker-probe'].value='1';els['#poker-probe'].listeners.change();
if(els['#poker-state'].textContent===before||els['#poker-decisions'].children.length!==7)throw Error('Probe switch failed');
console.log('Control checks passed: strategy/timing switch and identical-hand selector. Layout was not browser-inspected.');
