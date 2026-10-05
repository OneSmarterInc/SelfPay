// Client workflow checks with a stub transport. Real HTTP handlers have separate Python tests.
import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
const entries=JSON.parse(fs.readFileSync('seed/directory.json','utf8'));
const offers=JSON.parse(fs.readFileSync('seed/mappings.json','utf8')).map(o=>({...o,entry:entries.find(e=>e.name===o.entry_name),version:'test-version'}));
let signedIn=false,conversations=[];
const nodes=new Map();const node=id=>{if(!nodes.has(id))nodes.set(id,{value:'',innerHTML:'',textContent:'',classList:{add(){},remove(){}},showModal(){},close(){},checked:false});return nodes.get(id)};
const fetch=async(url,options={})=>{
  let status=200,body={};const input=JSON.parse(options.body||'{}');
  if(url==='/api/login'){signedIn=true;body={csrf:'demo-test',member:{id:'a',tenant:'plan-a',name:'Alex',email:'alex.a@example.test'}}}
  else if(!signedIn){status=401;body={error:'Sign in'}}
  else if(url==='/api/catalog')body={entries,offers,version:'test-version'};
  else if(url==='/api/preferences')body={};
  else if(url==='/api/search'||url==='/api/agent'){
    const raw=input.search||input;const search=Object.fromEntries(['mod','body','contrast','location','budget','type','sort','selected'].map(k=>[k,raw[k]]));
    if(input.message?.includes('without contrast'))search.contrast='without';
    if(input.message?.includes('Boise'))search.location='Boise';
    const matches=offers.filter(o=>o.mod===search.mod&&o.region===search.location&&(search.contrast==='unknown'||o.contrast===search.contrast||o.contrast==='unknown'));
    body={search,offers:matches,count:matches.length,version:'test-version',reply:'Review sourced candidates and confirm scope.'};
  }else if(url==='/api/conversations'){
    if(options.method==='POST'){conversations=conversations.filter(c=>c.id!==input.id);conversations.push({...input,title:'MRI · Cincinnati',expires:Date.now()+86400000,version:'test-version'});body={id:input.id}}
    else body={conversations};
  }else if(url==='/api/logout'){signedIn=false;body={ok:true}}
  return {ok:status<400,status,json:async()=>body};
};
const ctx=vm.createContext({console,fetch,crypto:globalThis.crypto,Date,setTimeout(){},document:{getElementById:node,querySelectorAll:()=>[]}});
{
  vm.runInContext(fs.readFileSync('static/app.js','utf8'),ctx);
  vm.runInContext(fs.readFileSync('static/functional.js','utf8'),ctx);
  await vm.runInContext('bootReady',ctx);
  assert.match(node('app').innerHTML,/Understand your self-pay imaging options/);
  await vm.runInContext('(async()=>{const r=await api("/login",{email:"alex.a@example.test",password:"DemoOnly-2026!"});account=r.member;csrf=r.csrf;await start()})()',ctx);
  assert.match(node('app').innerHTML,/How would you like to begin/);
  await vm.runInContext('enterJourney("search")',ctx);
  assert.match(node('app').innerHTML,/Where would you like to search/);
  assert.equal(vm.runInContext('results.length',ctx),0);
  vm.runInContext("state.mod='MRI';state.body='Knee';state.location='Cincinnati';state.budget=500",ctx);
  assert.equal(vm.runInContext('DIRECTORY.length',ctx),44);
  await vm.runInContext('talk("Find knee MRI without contrast near Cincinnati under $500")',ctx);
  assert.equal(vm.runInContext('results.length',ctx),2);
  assert.equal(vm.runInContext('state.messages.length',ctx),2);
  const saved=await vm.runInContext('api("/conversations")',ctx);assert.equal(saved.conversations.length,1);
  vm.runInContext('detail("aff-mri")',ctx);assert.match(node('app').innerHTML,/Questions to ask the facility/);
  await vm.runInContext('history()',ctx);assert.match(node('modal').innerHTML,/Saved conversations/);
  vm.runInContext('epoch++;state.private=true;state.messages=[];state.savedId=null;',ctx);
  await vm.runInContext('talk("MRI without contrast in Boise")',ctx);
  const after=await vm.runInContext('api("/conversations")',ctx);assert.equal(after.conversations.length,1);
  vm.runInContext('scan()',ctx);
  assert.match(node('modal').innerHTML,/Add your doctor’s order/);
  assert.match(node('modal').innerHTML,/No real upload or OCR/);
  node('badOrder').onclick();
  assert.match(node('orderPreview').innerHTML,/We will not guess/);
  assert.match(node('orderPreview').innerHTML,/orderSide/);
  vm.runInContext('explore()',ctx);
  assert.match(node('modal').innerHTML,/Planned · not available yet/);
  vm.runInContext("state=defaults();state.location='Cincinnati';render()",ctx);
  assert.doesNotMatch(node('app').innerHTML,/reviewed offers/);
  assert.match(node('app').innerHTML,/Directory locations in your search area/);
  vm.runInContext("state.budget=500;render()",ctx);
  assert.match(vm.runInContext("groupedCards(offers.filter(o=>o.type==='fixed'&&o.amount>500))",ctx),/Above your budget/);
  vm.runInContext("state=defaults();state.mod='MRI';state.body='Knee';state.contrast='without';render()",ctx);
  assert.match(vm.runInContext('chips()',ctx),/Without contrast/);
  assert.doesNotMatch(vm.runInContext('chips()',ctx),/<span[^>]*>\s*<\/span>/);
  vm.runInContext('state.searched=true;render()',ctx);node('location').oninput();
  assert.match(node('searchNotice').textContent,/Search changed/);
  vm.runInContext('state.selected=offers.slice(0,2).map(o=>o.id);compare()',ctx);
  assert.match(node('modal').innerHTML,/comparison-table/);
  vm.runInContext('request(offers[0])',ctx);node('simulateRequest').onclick();
  assert.match(node('requestStatus').innerHTML,/Sent \(simulated\)/);
  await vm.runInContext('api("/logout",{})',ctx);
  const rejected=await vm.runInContext('api("/catalog").then(()=>false).catch(()=>true)',ctx);assert.equal(rejected,true);
  console.log('24 client workflow checks passed with stub transport. No browser visual QA.');
}
