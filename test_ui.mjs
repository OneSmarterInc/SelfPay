// Client workflow checks with a stub transport. Real HTTP handlers have separate Python tests.
import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
const entries=JSON.parse(fs.readFileSync('seed/directory.json','utf8'));
const offers=JSON.parse(fs.readFileSync('seed/mappings.json','utf8')).map(o=>({...o,entry:entries.find(e=>e.name===o.entry_name),version:'test-version'}));
let storedUsage={};
let signedIn=false,conversations=[],failSave=false,failCatalog=false,limitReached=false,saveAttempts=0;
const nodes=new Map();const node=id=>{if(!nodes.has(id))nodes.set(id,{setAttribute(k,v){this[k]=v},querySelectorAll(){return []},focus(){},hidden:true,value:'',innerHTML:'',textContent:'',classList:{add(){},remove(){}},showModal(){},close(){},checked:false});return nodes.get(id)};
const fetch=async(url,options={})=>{
  let status=200,body={};const input=JSON.parse(options.body||'{}');
  if(url==='/api/agent'&&limitReached)return {ok:false,status:429,json:async()=>({error:'Guest preview limit reached. Full access is coming with MySelfPay accounts.',code:'guest_preview_limit'})};
  if((failSave&&url==='/api/conversations'&&options.method==='POST')||(failCatalog&&url==='/api/catalog'))return {ok:false,status:503,json:async()=>({error:'Synthetic service failure'})};
  if(url==='/api/guest'){signedIn=true;body={csrf:'demo-test',member:{id:'a',tenant:'guest',name:'Alex',email:'alex.a@example.test'}}}
  else if(!signedIn){status=401;body={error:'Sign in'}}
  else if(url==='/api/catalog')body={entries,offers,version:'test-version'};
  else if(url==='/api/guest-usage')body={usage:storedUsage};
  else if(url==='/api/preferences')body={};
  else if(url==='/api/search'||url==='/api/agent'){
    const raw=input.search||input;const search=Object.fromEntries(['mod','body','contrast','location','budget','type','sort','selected'].map(k=>[k,raw[k]]));
    if(input.message?.includes('without contrast'))search.contrast='without';
    if(input.message?.includes('Boise'))search.location='Boise';
    const matches=offers.filter(o=>o.mod===search.mod&&o.region===search.location&&(search.contrast==='unknown'||o.contrast===search.contrast||o.contrast==='unknown'));
    body={search,offers:matches,count:matches.length,version:'test-version',reply:'Review sourced candidates and confirm scope.',conversation_id:'chat-1',usage:{'chat-1':1}};
  }else if(url==='/api/conversations'){
    if(options.method==='POST'){saveAttempts++;conversations=conversations.filter(c=>c.id!==input.id);conversations.push({...input,title:'MRI · Cincinnati',expires:Date.now()+86400000,version:'test-version'});body={id:input.id}}
    else body={conversations};
  }else if(url==='/api/logout'){signedIn=false;body={ok:true}}
  return {ok:status<400,status,json:async()=>body};
};
const ctx=vm.createContext({console,fetch,crypto:globalThis.crypto,Date,setTimeout(){},document:{getElementById:node,querySelectorAll:()=>[],addEventListener(){}}});
{
  vm.runInContext(fs.readFileSync('static/app.js','utf8'),ctx);
  await vm.runInContext('bootReady',ctx);
  assert.match(node('app').innerHTML,/Find self-pay MRI and CT near you/);
  await vm.runInContext('signInGuest()',ctx);
  assert.equal(node('profile').textContent,'Sign out');
  assert.equal(node('history').hidden,true);
  await vm.runInContext('enterJourney("search")',ctx);
  assert.match(node('app').innerHTML,/Where would you like to search/);
  assert.equal(vm.runInContext('results.length',ctx),0);
  vm.runInContext("state.mod='MRI';state.body='Knee';state.location='Cincinnati';state.budget=500",ctx);
  assert.equal(vm.runInContext('DIRECTORY.length',ctx),74);
  await vm.runInContext('talk("Find knee MRI without contrast near Cincinnati under $500")',ctx);
  assert.equal(vm.runInContext('results.length',ctx),2);
  assert.equal(vm.runInContext('state.messages.length',ctx),2);
  assert.equal(vm.runInContext("price({type:'quote',amount:null})",ctx),'Ask for a price');
  assert.equal(vm.runInContext("typeLabel({type:'quote'})",ctx),'Price on request');
  const saved=await vm.runInContext('api("/conversations")',ctx);assert.equal(saved.conversations.length,0);
  vm.runInContext('detail("aff-mri")',ctx);assert.match(node('app').innerHTML,/Questions to ask the facility/);
  assert.equal(saveAttempts,0);
  assert.equal(vm.runInContext('state.private',ctx),true);
  vm.runInContext('epoch++;state.private=true;state.messages=[];state.savedId=null;',ctx);
  await vm.runInContext('talk("MRI without contrast in Boise")',ctx);
  const after=await vm.runInContext('api("/conversations")',ctx);assert.equal(after.conversations.length,0);
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
  assert.match(vm.runInContext("groupedCards(offers.filter(o=>o.type==='fixed'&&o.amount>500))",ctx),/Above your published-price budget/);
  vm.runInContext("state=defaults();state.mod='MRI';state.body='Knee';state.contrast='without';render()",ctx);
  assert.match(vm.runInContext('chips()',ctx),/Without contrast/);
  assert.doesNotMatch(vm.runInContext('chips()',ctx),/<span[^>]*>\s*<\/span>/);
  vm.runInContext('state.searched=true;render()',ctx);node('location').oninput();
  assert.match(node('searchNotice').textContent,/Search changed/);
  vm.runInContext('state.selected=offers.slice(0,2).map(o=>o.id);compare()',ctx);
  assert.match(node('modal').innerHTML,/comparison-table/);
  assert.equal(vm.runInContext("phoneOf({coverage:'5692 Far Hills Ave, Dayton, OH 45429. 937-438-3384'})",ctx),'937-438-3384');
  assert.equal(vm.runInContext("addressOf({coverage:'5692 Far Hills Ave, Dayton, OH 45429. 937-438-3384'})",ctx),'5692 Far Hills Ave, Dayton, OH 45429');
  assert.equal(vm.runInContext("addressOf({coverage:'Multiple markets'})",ctx),'');
  assert.match(vm.runInContext("contactActions({entry:{name:'PDI — Dayton',coverage:'5692 Far Hills Ave, Dayton, OH 45429. 937-438-3384',source:'https://example.org/mri'}})",ctx),/href="tel:\+19374383384"[\s\S]*Website[\s\S]*Directions/);
  assert.equal(vm.runInContext("contactActions({entry:{name:'X',coverage:'Multiple markets',source:'javascript:alert(1)'}})",ctx),'');
  assert.equal(vm.runInContext("infoPage('for-imaging-centers')",ctx),true);
  assert.match(node('app').innerHTML,/Free during the pilot/);
  assert.match(node('app').innerHTML,/mailto:partners@onesmarter\.com/);
  for(const key of ['contact','privacy','terms'])assert.equal(vm.runInContext(`infoPage('${key}')`,ctx),true);
  assert.equal(vm.runInContext("infoPage('nope')",ctx),false);
  assert.equal(vm.runInContext("JSON.stringify(restrictionsOf({included:'Official site offers self-pay MRI. No dollar amount verified.',entry:{notes:'Official site offers self-pay MRI; No dollar amount verified; Order required'}}))",ctx),'["Order required"]');
  assert.match(vm.runInContext("questions({mod:'MRI',order:'Review the facility restrictions below and confirm the exact order requirement.'})[3]",ctx),/^Do you need a doctor’s order or referral\?$/);
  assert.match(vm.runInContext("questions({mod:'MRI',order:'Physician order required'})[3]",ctx),/The listing says: Physician order required\./);
  vm.runInContext('request(offers[0])',ctx);
  assert.match(node('modal').innerHTML,/Ask for a self-pay price/);
  assert.match(node('modal').innerHTML,/Questions to ask/);
  assert.doesNotMatch(node('modal').innerHTML,/simulat/i);
  assert.match(vm.runInContext('initialSearch()',ctx),/Directory loaded: 74 researched entries/);
  assert.match(vm.runInContext('initialSearch()',ctx),/Try sample: knee MRI/);
  vm.runInContext("state.mode='agent';render()",ctx);
  assert.match(node('app').innerHTML,/Guest preview:/);
  assert.equal((node('app').innerHTML.match(/data-starter=/g)||[]).length,3);
  assert.doesNotMatch(node('app').innerHTML,/id="private"/);
  limitReached=true;
  await vm.runInContext("talk('MRI')",ctx);
  assert.equal(vm.runInContext('chatDisabled()',ctx),true);
  assert.match(node('app').innerHTML,/Guest preview limit reached/);
  assert.match(node('app').innerHTML,/id="message"[^>]*disabled/);
  vm.runInContext("state.mod='MRI';state.body='Knee';state.location='Cincinnati';state.contrast='without'",ctx);
  await vm.runInContext('search()',ctx);
  assert.equal(vm.runInContext('results.length',ctx),2);
  assert.equal(saveAttempts,0);
  limitReached=false;failCatalog=true;
  await vm.runInContext('start().catch(loadFailure)',ctx);
  await vm.runInContext('enterJourney("search")',ctx);
  assert.match(node('app').innerHTML,/Where would you like to search/);
  assert.match(node('app').innerHTML,/full directory is temporarily unavailable/);
  failCatalog=false;
  await vm.runInContext('start()',ctx);
  assert.match(node('app').innerHTML,/How would you like to begin/);
  storedUsage={'chat-a':5,'chat-b':5,'chat-c':5};
  await vm.runInContext('start()',ctx);
  await vm.runInContext('enterJourney("agent")',ctx);
  assert.equal(vm.runInContext('chatDisabled()',ctx),true);
  assert.match(node('app').innerHTML,/id="message"[^>]*disabled/);
  assert.match(node('app').innerHTML,/id="newGuestChat"[^>]*disabled/);
  assert.match(node('app').innerHTML,/id="voice"[^>]*disabled/);
  assert.equal(vm.runInContext('state.messages.length',ctx),0);
  storedUsage={};
  await vm.runInContext('api("/logout",{})',ctx);
  const rejected=await vm.runInContext('api("/catalog").then(()=>false).catch(()=>true)',ctx);assert.equal(rejected,true);
  assert.equal(node('profile').textContent,'Start searching');
  assert.equal(node('history').hidden,true);
  assert.doesNotMatch(node('app').innerHTML,/loginForm|Create an account/);
  await vm.runInContext('signInGuest("agent")',ctx);
  assert.equal(vm.runInContext('state.mode',ctx),'agent');
  await vm.runInContext('signOut()',ctx);
  assert.equal(node('profile').textContent,'Start searching');
  assert.equal(vm.runInContext('account',ctx),null);
  console.log('Client workflow checks, including guest privacy, quotas and catalog failure recovery, passed with stub transport. No browser visual QA.');
}


vm.runInContext("results=[];state.searched=true;state.dirty=false;state.unlocatedOfferCount=4;render()",ctx);
assert.match(node('app').innerHTML,/Distance results are incomplete/);
assert.match(node('app').innerHTML,/does not mean no services are available/);

// Opening the arrow ignores the current value; typing filters only suggestions.
vm.runInContext("state.location='Cincinnati, OH';render()",ctx);
node('location').value='Cincinnati, OH';
node('cityChoices').hidden=true;
node('locationToggle').onclick();
assert.equal(node('cityChoices').hidden,false);
assert.ok(node('cityChoices').innerHTML.includes('Boise'));
node('location').oninput();
assert.ok(!node('cityChoices').innerHTML.includes('Boise'));
node('locationToggle').onclick();
node('locationToggle').onclick();
assert.ok(node('cityChoices').innerHTML.includes('Boise'));

// Location clarification must replace the empty-results card, with choices next to the input.
vm.runInContext("state.location='Baltimore';state.locationSuggestions=['Baltimore, MD','Baltimore, OH'];state.locationUnresolved=true;state.searched=true;results=[];render()",ctx);
assert.match(node('app').innerHTML,/Choose your city and state/);
assert.doesNotMatch(node('app').innerHTML,/No reviewed match|0 reviewed offers|Select up to 3 options/);
assert.match(node('locationSuggestions').innerHTML,/Baltimore, MD/);
assert.match(node('locationSuggestions').innerHTML,/Baltimore, OH/);
assert.match(node('locationSuggestions').innerHTML,/type="button"/);
const fieldMarkup=vm.runInContext('searchFields()',ctx);
assert.ok(fieldMarkup.indexOf('id="locationSuggestions"')>fieldMarkup.indexOf('id="location"'));
assert.ok(fieldMarkup.indexOf('id="locationSuggestions"')<fieldMarkup.indexOf('id="budget"'));
vm.runInContext("state.locationSuggestions=[];state.location='unrecognized';render()",ctx);
assert.match(node('app').innerHTML,/Enter a city and state or ZIP code/);
assert.doesNotMatch(node('app').innerHTML,/No reviewed match/);
vm.runInContext("state.locationUnresolved=false;state.location='Baltimore, MD';render()",ctx);
assert.doesNotMatch(node('app').innerHTML,/Choose your city and state/);


const testCenter={name:'Synthetic & Center',email:'test@example.test',appointment_email_approved:true,test_only:true};
ctx.testCenter=testCenter;
assert.doesNotMatch(vm.runInContext("contactActions({entry:{name:'No email'}})",ctx),/Book appointment/);
assert.match(vm.runInContext('contactActions({entry:testCenter})',ctx),/Book appointment/);
assert.equal(vm.runInContext("appointmentEmail({email:'billing@example.test',email_scope:'Billing, not scheduling'})",ctx),'');
assert.equal(vm.runInContext("appointmentEmail({email:'x@example.test?bcc=bad@example.test',appointment_email_approved:true})",ctx),'');
ctx.formValues={name:'Test & Name',phone:'5551234567',date:'2099-01-01',time:'10:30',zone:'Eastern',service:'MRI'};
const draft=vm.runInContext('appointmentDraft(testCenter,formValues)',ctx);
assert.match(draft.uri,/^mailto:test%40example.test\?subject=/);
const params=new URLSearchParams(draft.uri.split('?')[1]);
assert.equal(params.get('subject'),'Appointment request — Synthetic & Center');
assert.match(params.get('body'),/Test & Name/);assert.match(params.get('body'),/2099-01-01/);assert.match(params.get('body'),/10:30 \(Eastern time\)/);
assert.equal(params.size,2);
assert.throws(()=>vm.runInContext("appointmentDraft(testCenter,{...formValues,date:'2000-01-01'})",ctx));
vm.runInContext('appointmentForm(testCenter)',ctx);
assert.match(node('modal').innerHTML,/Open email app/);assert.match(node('modal').innerHTML,/No MySelfPay account is needed/);
console.log('Appointment mailto checks passed; no email sent.');

assert.equal(vm.runInContext("appointmentEmail({email:'appointments@example.test',email_scope:'Shared clinical/scheduling contact; not branch-specific. For scheduling questions.'})",ctx),'appointments@example.test');

// Startup must request usage while the catalog is still pending.
const originalFetch=ctx.fetch;
let releaseCatalog;
const requested=[];
ctx.fetch=async(url,options)=>{
  requested.push(url);
  if(url==='/api/catalog')await new Promise(resolve=>{releaseCatalog=resolve});
  return originalFetch(url,options);
};
const signingIn=vm.runInContext('signInGuest("agent")',ctx);
assert.match(node('app').innerHTML,/Starting your guest session/);
assert.equal(node('profile').disabled,true);
await vm.runInContext('signInGuest()',ctx);
for(let i=0;i<20;i++)await Promise.resolve();
assert.ok(requested.includes('/api/catalog'));
assert.ok(requested.includes('/api/guest-usage'),'Usage must not wait for catalog completion');
assert.equal(requested.filter(url=>url==='/api/guest').length,1);
await signingIn;
assert.equal(vm.runInContext('catalogReady',ctx),false);
assert.match(node('app').innerHTML,/You can search now/);
vm.runInContext("state.mod='MRI';state.body='Knee';state.location='Cincinnati';state.contrast='without'",ctx);
await vm.runInContext('search()',ctx);
assert.equal(vm.runInContext('results.length',ctx),2);
vm.runInContext('detail(results[0].id)',ctx);
assert.match(node('app').innerHTML,/Questions to ask the facility/);
const screenBeforeCatalog=node('app').innerHTML;
node('location').value='Unsaved typed location';
releaseCatalog();
await vm.runInContext('catalogTask.promise',ctx);
assert.equal(node('app').innerHTML,screenBeforeCatalog);
assert.equal(node('location').value,'Unsaved typed location');
assert.equal(node('profile').disabled,false);
assert.equal(vm.runInContext('state.mode',ctx),'agent');
ctx.fetch=async(url,options)=>url==='/api/guest'
  ? {ok:false,status:503,json:async()=>({error:'Temporarily unavailable'})}
  : originalFetch(url,options);
await assert.rejects(vm.runInContext('signInGuest()',ctx),/Temporarily unavailable/);
assert.equal(node('profile').disabled,false);
assert.match(node('app').innerHTML,/Find self-pay MRI and CT near you/);
ctx.fetch=originalFetch;
console.log('Concurrent guest startup, progress, duplicate-click and failure checks passed.');

ctx.fetch=async(url,options)=>{
  if(url==='/api/catalog'){
    await new Promise(resolve=>{releaseCatalog=resolve});
    return {ok:true,status:200,json:async()=>({entries,offers,version:'old-session'})};
  }
  return originalFetch(url,options);
};
await vm.runInContext('start()',ctx);
const oldCatalog=vm.runInContext('catalogTask.promise',ctx);
assert.equal(vm.runInContext('loadCatalog()',ctx),oldCatalog,'Concurrent catalog consumers share one request');
await vm.runInContext('signOut()',ctx);
releaseCatalog();
await oldCatalog;
assert.equal(vm.runInContext('catalogReady',ctx),false);
assert.equal(vm.runInContext('DIRECTORY.length',ctx),0);
assert.equal(vm.runInContext('offers.length',ctx),0);
ctx.fetch=originalFetch;
console.log('Late catalog responses cannot repopulate a signed-out session.');
