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
const ctx=vm.createContext({console,fetch,crypto:globalThis.crypto,Date,setTimeout(){},setInterval(){},clearInterval(){},document:{getElementById:node,querySelectorAll:()=>[],addEventListener(){}}});
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
  assert.doesNotMatch(node('app').innerHTML,/id="scan"|id="explore"|data-journey="scan"/);
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
  assert.equal(node('profile').hidden,true);
  assert.equal(node('history').hidden,true);
  assert.doesNotMatch(node('app').innerHTML,/loginForm|Create an account/);
  await vm.runInContext('signInGuest("agent")',ctx);
  assert.equal(vm.runInContext('state.mode',ctx),'agent');
  await vm.runInContext('signOut()',ctx);
  assert.equal(node('profile').hidden,true);
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


const testCenter={name:'Synthetic & Center',booking_id:'synthetic-clinic'};
ctx.testCenter=testCenter;
assert.doesNotMatch(vm.runInContext("contactActions({entry:{name:'No identity'}})",ctx),/Book appointment/);
assert.match(vm.runInContext('contactActions({entry:testCenter})',ctx),/data-appointment="synthetic-clinic"/);
ctx.bookingTest={clinic_name:'Synthetic <clinic>',location:'Test',service:'MRI',exam:'Knee',contrast:'without',slots:[{date:'2026-11-03',period:'morning'}],timezone:'America/New_York'};
const summary=vm.runInContext('bookingSummary(bookingTest)',ctx);
assert.match(summary,/Synthetic &lt;clinic&gt;/);
assert.match(summary,/Morning/);
assert.match(summary,/Eastern/);
assert.match(summary,/Clinic will confirm/);
assert.doesNotMatch(fs.readFileSync('static/app.js','utf8'),/location.href=draft.uri/);
console.log('Booking identity and escaped review checks passed.');

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

// Public account forms keep guest entry and handle validation/login state.
ctx.location={hash:'#signup',pathname:'/'};
ctx.history={replaceState(){ctx.location.hash=''}};
vm.runInContext('accountPage(true)',ctx);
assert.match(node('app').innerHTML,/Full name/);
assert.match(node('app').innerHTML,/Phone number \(optional\)/);
assert.match(node('app').innerHTML,/Sign in as guest/);
assert.match(node('app').innerHTML,/autocomplete="new-password"/);
node('accountError').isConnected=true;
node('accountPassword').value='Synthetic-passphrase!';
node('accountConfirm').value='does not match';
await node('accountForm').onsubmit({preventDefault(){}});
assert.equal(node('accountError').textContent,'Passwords do not match.');
vm.runInContext('accountPage(false)',ctx);
assert.match(node('app').innerHTML,/href="#signup"/);
ctx.fetch=async(url,options)=>url==='/api/login'
 ? {ok:false,status:401,json:async()=>({error:'Email or password is incorrect.'})}
 : originalFetch(url,options);
await node('accountForm').onsubmit({preventDefault(){}});
assert.equal(node('accountError').textContent,'Email or password is incorrect.');
assert.equal(node('accountSubmit').disabled,false);
node('accountForm').reset=()=>{};
ctx.fetch=async(url,options)=>{
 if(url==='/api/login'){signedIn=true;return {ok:true,status:200,json:async()=>({member:{id:'account-1',tenant:'selfpay',name:'Synthetic'},csrf:'new-csrf'})};}
 return originalFetch(url,options);
};
await node('accountForm').onsubmit({preventDefault(){}});
assert.equal(vm.runInContext('account.tenant',ctx),'selfpay');
assert.equal(node('accountLogin').hidden,true);
assert.equal(node('profile').textContent,'Sign out');
assert.equal(vm.runInContext('state.private',ctx),true);
assert.equal(vm.runInContext('chatDisabled()',ctx),false);
assert.doesNotMatch(vm.runInContext('guestChatControls()',ctx),/Guest preview:/);
ctx.fetch=originalFetch;
await vm.runInContext('signOut()',ctx);
assert.equal(node('accountLogin').hidden,false);
assert.equal(node('profile').hidden,true);
console.log('Account form validation, login/logout, guest entry and private-state checks passed.');

// Browser-history adapter: exercise refresh, Back/Forward and private snapshots.
const navigationEntries=[];let navigationIndex=-1;
ctx.history={state:null,pushState(value,unused,url){navigationEntries.splice(navigationIndex+1);navigationEntries.push({value:structuredClone(value),url});navigationIndex++;this.state=structuredClone(value);ctx.location.hash=url.includes('#')?url.slice(url.indexOf('#')):'';},replaceState(value,unused,url){this.state=structuredClone(value);if(navigationIndex<0){navigationEntries.push({value:structuredClone(value),url});navigationIndex=0;}else navigationEntries[navigationIndex]={value:structuredClone(value),url};ctx.location.hash=url.includes('#')?url.slice(url.indexOf('#')):'';}};
ctx.location={hash:'',pathname:'/'};
await vm.runInContext('signInGuest()',ctx);
vm.runInContext("Object.assign(state,{location:'Cincinnati',mod:'MRI',body:'Knee',contrast:'without',selected:['aff-mri'],messages:[{text:'PRIVATE CHAT'}]})",ctx);
await vm.runInContext('search()',ctx);
assert.equal(ctx.location.hash,'#search');
const searchIndex=navigationIndex;
assert.doesNotMatch(JSON.stringify(ctx.history.state),/PRIVATE CHAT|csrf|password|token/);
assert.doesNotMatch(navigationEntries[navigationIndex].url,/Cincinnati|Knee/);
vm.runInContext('detail("aff-mri")',ctx);
assert.equal(ctx.location.hash,'#facility/aff-mri');
const detailIndex=navigationIndex;
// Refresh resets in-memory search state; history state restores it using fresh data.
vm.runInContext('state=defaults();results=[]',ctx);
await vm.runInContext('restoreNavigation()',ctx);
assert.match(node('app').innerHTML,/Questions to ask the facility/);
assert.equal(vm.runInContext('state.location',ctx),'Cincinnati');
assert.equal(vm.runInContext('state.messages.length',ctx),0);
assert.equal(navigationIndex,detailIndex,'Restoration must not push history entries');
function travel(index){navigationIndex=index;ctx.history.state=structuredClone(navigationEntries[index].value);const url=navigationEntries[index].url;ctx.location.hash=url.includes('#')?url.slice(url.indexOf('#')):'';}
travel(searchIndex);await vm.runInContext('restoreNavigation()',ctx);
assert.match(node('app').innerHTML,/Find and compare imaging options/);
assert.equal(vm.runInContext('state.selected[0]',ctx),'aff-mri');
travel(detailIndex);await vm.runInContext('restoreNavigation()',ctx);
assert.match(node('app').innerHTML,/Questions to ask the facility/);
vm.runInContext('compare()',ctx);
assert.equal(ctx.location.hash,'#compare');
await vm.runInContext('restoreNavigation()',ctx);
assert.match(node('modal').innerHTML,/Compare selected options/);
vm.runInContext('closeDialog()',ctx);assert.equal(ctx.location.hash,'#search');
vm.runInContext('directory()',ctx);node('dirSearch').value='Dayton';node('dirSearch').oninput();
assert.equal(ctx.history.state.query.directoryQuery,'Dayton');
vm.runInContext('state=defaults()',ctx);await vm.runInContext('restoreNavigation()',ctx);
assert.equal(node('dirSearch').value,'Dayton');
assert.equal(ctx.location.hash,'#directory');
vm.runInContext('closeDialog();welcome()',ctx);
assert.doesNotMatch(node('app').innerHTML,/doctor.?s order|sample order|data-journey="scan"|welcomeExplore/i);
await vm.runInContext('signOut()',ctx);
travel(detailIndex);await vm.runInContext('restoreNavigation()',ctx);
assert.match(node('app').innerHTML,/Find self-pay MRI and CT near you/);
console.log('Refresh, Back/Forward, facility, compare, directory and logout navigation checks passed.');
