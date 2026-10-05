const cityLabels=['Cincinnati, OH','Louisville, KY','Lexington, KY','Philadelphia, PA','Boise, ID','Lawrenceville, GA','Auburn, WA','Spanish Fork, UT','South Burlington, VT','Wisconsin','National'];
/* Shared server-backed search and account-scoped persistence. No browser storage. */
let csrf='',account=null,currentVersion='',busy=false,saveQueue=Promise.resolve(),epoch=0,catalogReady=false;
const defaults=()=>({mod:'',body:'',contrast:'unknown',location:'',budget:0,type:'all',mode:'classic',selected:[],private:false,messages:[],member:'',savedId:null,sort:'price'});
async function api(path,data,method){
  const options={method:method||(data?'POST':'GET'),credentials:'same-origin',headers:{}};
  if(options.method!=='GET')options.headers['X-CSRF-Token']=csrf;
  if(data!==undefined){options.headers['Content-Type']='application/json';options.body=JSON.stringify(data)}
  const response=await fetch('/api'+path,options);const body=await response.json();
  if(!response.ok){if(response.status===401&&path!=='/login'){account=null;epoch++;loginScreen()}throw new Error(body.error||'Request failed')}
  return body;
}
function safe(fn){return (...args)=>Promise.resolve().then(()=>fn(...args)).catch(e=>toast(e.message))}
async function loadCatalog(){catalogReady=false;const data=await api('/catalog');if(!Array.isArray(data.entries)||!Array.isArray(data.offers)||!data.version)throw new Error('Provider directory is not published yet. Contact the review administrator.');DIRECTORY=data.entries;offers=data.offers;currentVersion=data.version;catalogReady=true}
function loadFailure(error){pageTop('load-error');$('app').innerHTML=`<section class="panel"><h1>Unable to load your review session</h1><p role="alert">${esc(error.message)}</p><p>Your search history has not been deleted. Retry to load the provider directory from the database.</p><button id="retrySession" class="primary">Retry loading</button></section>`;$('retrySession').onclick=()=>start().catch(loadFailure)}

async function loadResults(){const started=epoch;const data=await api('/search',state);if(started!==epoch)return null;results=data.offers;state.locationSuggestions=data.location_suggestions||[];state.dirty=false;currentVersion=data.version;Object.assign(state,data.search);const byId=new Map(offers.map(o=>[o.id,o]));results.forEach(o=>byId.set(o.id,o));offers=[...byId.values()];return data}
async function search(){state.searched=!!(state.mod&&state.body.trim()&&state.location.trim());if(!state.searched){results=[];state.detailsOpen=true;render();$('searchNotice').textContent=!state.location?'Enter your city or state to continue.':'Choose an exam and body part to see prices.';return}if(!await loadResults())return;try{await save()}finally{render()}}
function save(){
  if(state.private||(!state.messages.length&&!state.searched)||!account)return Promise.resolve();
  state.saveStatus='saving';const started=epoch;const id=state.savedId||crypto.randomUUID();state.savedId=id;
  const payload=JSON.parse(JSON.stringify({id,private:false,messages:state.messages,search:state}));
  saveQueue=saveQueue.catch(()=>{}).then(async()=>{if(started!==epoch)return;await api('/conversations',payload)});
  return saveQueue.then(()=>{if(started===epoch)state.saveStatus='saved'}).catch(e=>{if(started===epoch)state.saveStatus='failed';toast('Conversation not saved: '+e.message);throw e});
}
const originalBind=bind;
bind=function(){
  originalBind();
  const showDirty=()=>{if($('searchNotice'))$('searchNotice').textContent=state.dirty?'Search changed—click Find options to update results. Displayed results belong to your previous search.':'';document.querySelectorAll('[data-select],[data-detail],#compare').forEach(b=>b.disabled=!!state.dirty)};
  showDirty();
  for(const id of ['mod','body','contrast','location','budget','type'])$(id).oninput=()=>{if(state.searched)state.dirty=true;showDirty()};
  if($('locationSuggestions')){$('locationSuggestions').innerHTML=(state.locationSuggestions||[]).length?'<p>Did you mean one of these locations? Choose to update your search.</p>'+state.locationSuggestions.map(label=>`<button data-city="${esc(label)}">${esc(label)}</button>`).join(''):'';document.querySelectorAll('[data-city]').forEach(b=>b.onclick=safe(async()=>{state.location=b.dataset.city;await search()}))}

  // preventDefault must happen during dispatch, not in the asynchronous safe wrapper.
  $('searchForm').onsubmit=e=>{e.preventDefault();safe(async()=>{readFields();await search()})()};
  $('classic').onclick=safe(async()=>{readFields();state.mode='classic';render()});
  $('agent').onclick=safe(async()=>{readFields();state.mode='agent';render()});
  if($('sort'))$('sort').onchange=safe(async e=>{readFields();state.sort=e.target.value;await search()});
  $('private').onchange=safe(async e=>{
    const isPrivate=e.target.checked;epoch++;const member=state.member;
    state={...defaults(),member,private:isPrivate,mode:state.mode};
    await loadResults();render();
    toast(isPrivate?'Private mode: fresh search, no saved preferences or history.':'New normal session. Private content discarded.');
  });
  $('remember').onclick=safe(async()=>{if(state.private)return toast('Preferences are not saved in private mode.');readFields();await api('/preferences',{location:state.location});toast('Location saved to this account.')});
  document.querySelectorAll('[data-select]').forEach(b=>b.onchange=safe(async()=>{if(b.checked&&state.selected.length>=3){b.checked=false;return toast('Compare up to three options.')}state.selected=b.checked?[...state.selected,b.dataset.select]:state.selected.filter(x=>x!==b.dataset.select);try{await save()}finally{render()}}));
  if($('sampleSearch'))$('sampleSearch').onclick=safe(async()=>{Object.assign(state,{mod:'MRI',body:'Knee',contrast:'without',location:'Cincinnati, OH',budget:500,type:'all'});await search()});
  if($('browseDirectory'))$('browseDirectory').onclick=safe(async()=>{await loadCatalog();directory()});
  if($('widen'))$('widen').onclick=safe(async()=>{state.location='National';await search()});
  if($('chatForm')){
    $('chatForm').onsubmit=e=>{e.preventDefault();safe(async()=>{readFields();await talk($('message').value)})()};
    if($('resumeSave'))$('resumeSave').onclick=safe(async()=>{await save();toast(state.private?'Private conversation is not saved.':'Conversation saved to this account.')});
  }
};
async function talk(text){
  if(busy)return;busy=true;const started=epoch;
  try{
    const data=await api('/agent',{message:text,search:state,private:state.private});
    if(started!==epoch)return;
    state.messages.push({role:'user',text},{role:'assistant',text:data.reply});
    Object.assign(state,data.search);state.searched=!!(state.mod&&state.body.trim()&&state.location.trim());results=data.offers;state.locationSuggestions=data.location_suggestions||[];state.dirty=false;currentVersion=data.version;
    const byId=new Map(offers.map(o=>[o.id,o]));results.forEach(o=>byId.set(o.id,o));offers=[...byId.values()];
    try{await save()}finally{render()};
  }finally{busy=false}
}
function voice(){modal('<h2>Voice conversation preview</h2><p>No microphone or speech service is connected. This editable sample transcript uses the same server search.</p><div class="field"><label for="transcript">Review sample transcript</label><textarea id="transcript">Find a self-pay knee MRI near Cincinnati under $500</textarea></div><button id="useTranscript" class="primary">Use transcript</button>');$('useTranscript').onclick=safe(async()=>{const t=$('transcript').value;$('modal').close();await talk(t)})}
async function history(){
  if(state.private)return toast('Exit private mode to access saved conversations.');
  const {conversations:list}=await api('/conversations');
  modal(`<h2>Saved conversations and searches</h2><p class="small">Owned by ${esc(state.member)}. Expires after 90 days without activity. Resuming refreshes the database listings; old messages remain historical.</p>${list.map(c=>`<div class="lead"><strong>${esc(c.title)}</strong><p class="small">Expires ${new Date(c.expires).toLocaleDateString()}</p><button data-resume="${esc(c.id)}">Continue</button> <button data-delete="${esc(c.id)}">Delete</button></div>`).join('')||'<p>No saved conversations or searches yet.</p>'}<div class="actions"><button id="deleteAll">Delete all my conversations</button><button id="deletePref">Delete remembered location</button></div>`);
  document.querySelectorAll('[data-resume]').forEach(b=>b.onclick=safe(async()=>{const c=list.find(x=>x.id===b.dataset.resume);Object.assign(state,c.search,{messages:c.messages,savedId:c.id,private:false,mode:c.messages.length?'agent':'classic'});await loadCatalog();await loadResults();state.searched=!!(state.mod&&state.body.trim()&&state.location.trim());$('modal').close();render();toast(c.version!==currentVersion?'Directory changed since this conversation. Review refreshed prices and restrictions.':'Search refreshed from the current database. Reconfirm published prices with the facility.')}));
  document.querySelectorAll('[data-delete]').forEach(b=>b.onclick=safe(async()=>{await saveQueue.catch(()=>{});await api('/conversations/'+b.dataset.delete,undefined,'DELETE');if(state.savedId===b.dataset.delete){state.savedId=null;state.messages=[]} $('modal').close();await history()}));
  $('deleteAll').onclick=safe(async()=>{await saveQueue.catch(()=>{});await api('/conversations/all',undefined,'DELETE');state.messages=[];state.savedId=null;$('modal').close();await history()});
  $('deletePref').onclick=safe(async()=>{await api('/preferences',undefined,'DELETE');toast('Remembered location deleted.')});
}
function report(o){
  if(state.private)return toast('Exit private mode before submitting a saved correction report.');
  modal(`<h2>Report incorrect information</h2><p>${esc(o.entry.name)}</p><form id="reportForm">${control('reportType','What needs review?','<select id="reportType"><option>Price</option><option>Contact details</option><option>Eligibility or restrictions</option><option>Other</option></select>')}${control('reportText','Describe the issue using synthetic information','<textarea id="reportText" required maxlength="1000"></textarea>')}<button class="primary">Save correction report</button></form><p class="small muted">Saved in the database for reviewer inspection. No facility is contacted and no listing changes automatically.</p>`);
  $('reportForm').onsubmit=e=>{e.preventDefault();safe(async()=>{await api('/corrections',{offer_id:o.id,category:$('reportType').value,description:$('reportText').value});$('modal').close();toast('Correction saved as pending review. Listing unchanged.')})()};
}
function profile(){modal(`<h2>My account</h2><p>${esc(account.name)} · ${esc(account.tenant)}<br>${esc(account.email)}</p><p>Switching accounts requires signing in. Server checks protect each account’s history. Your account belongs to the review app; it is not linked to a health plan.</p><button id="changePassword">Change password</button><button id="logout">Sign out</button>`);$('changePassword').onclick=passwordScreen;$('logout').onclick=safe(async()=>{await saveQueue.catch(()=>{});await api('/logout',{});epoch++;account=null;csrf='';state=defaults();results=[];offers=[];DIRECTORY=[];$('modal').close();welcome()})}
let pendingEntry=null;
function updateNavigation(){['history','directory'].forEach(id=>{$(id).hidden=!account})}
function welcome(){updateNavigation();pageTop('welcome');
  $('app').innerHTML=`<section class="welcome-intro"><div><div class="eyebrow">WELCOME TO MYSELFPAY</div><h1>Understand your self-pay imaging options.</h1><p class="welcome-lead">Find MRI and CT services, compare published prices, and see what is included before you contact a facility.</p><p>You can explore self-pay options whether you have health coverage or are paying entirely yourself. Your facility confirms the exact service, eligibility and final price.</p><div class="actions"><button class="primary" id="welcomeBegin">${'Find imaging options'}</button>${account?'<button id="continueSearch">Continue previous search</button>':''}<button id="welcomeAccount">${account?'My account':'Sign in to your account'}</button></div></div><aside class="welcome-account"><h2>Your own account.<br>Your place to pick up again.</h2><p>Keep your conversations together, remember a preferred location, and return to your search when you are ready.</p><p class="small">You control saved conversations. Delete them at any time, or choose a private session without saved history.</p><span class="badge neutral">${account?'Signed in as '+esc(account.name):'Create an account or sign in'}</span><p class="small">This POC uses accounts. Personal account enrollment will be designed with participating health plans and TPAs.</p></aside></section><section class="welcome-steps" aria-label="How MySelfPay works"><div><span class="step-number">1</span><h3>Tell us what you need</h3><p>Use the service on your order, type a request, or try the sample order scan.</p></div><div><span class="step-number">2</span><h3>Compare the details</h3><p>Review prices, included fees and restrictions for relevant options.</p></div><div><span class="step-number">3</span><h3>Confirm with the facility</h3><p>Use provider links and a question checklist to confirm the exact exam and total.</p></div></section><section class="welcome-paths"><h2>How would you like to begin?</h2><div class="welcome-choices"><button class="journey-card" data-journey="search"><strong>Search for a service</strong><span>Choose your imaging exam and location.</span></button><button class="journey-card" data-journey="agent"><strong>Ask MySelfPay</strong><span>Describe your search in a conversation.</span></button><button class="journey-card" data-journey="scan"><strong>I have a doctor's order</strong><span>Try the sample scan and review the exam details.</span></button></div><button id="welcomeExplore" style="margin-top:16px">I don't have an order</button></section><p class="welcome-note">Starting with MRI and CT. Prices are published references and may change; self-pay is not always cheaper than using coverage. MySelfPay does not decide which test you need or guarantee prices, payment or availability.</p>`;
  if($('continueSearch'))$('continueSearch').onclick=safe(history);
  $('welcomeBegin').onclick=safe(()=>enterJourney('search'));
  $('welcomeAccount').onclick=()=>{pendingEntry=null;account?profile():loginScreen()};
  $('welcomeExplore').onclick=safe(()=>enterJourney('explore'));
  document.querySelectorAll('[data-journey]').forEach(b=>b.onclick=safe(()=>enterJourney(b.dataset.journey)));
}
async function enterJourney(kind){
  if(!account){pendingEntry=kind;loginScreen();return}
  if(!catalogReady){try{await start()}catch(e){loadFailure(e);return}}
  state.mode=kind==='agent'?'agent':'classic';render();
  if(kind==='scan')scan();else if(kind==='explore')explore();
}
function loginScreen(create=false){updateNavigation();pageTop(create?'register':'login');
  $('app').innerHTML=`<section class="panel" style="max-width:570px;margin:50px auto"><h1>${create?'Create your account':'Sign in to MySelfPay'}</h1><p>Save searches and conversations in your own review account.</p><form id="loginForm">${create?control('accountName','Your name','<input id="accountName" autocomplete="name" maxlength="80" required>'):''}${control('email','Email address','<input id="email" type="email" autocomplete="username" maxlength="200" required>')}${control('password','Password',`<input id="password" type="password" autocomplete="${create?'new-password':'current-password'}" ${create?'minlength="8"':''} maxlength="200" required>`)}${create?control('confirmPassword','Confirm password','<input id="confirmPassword" type="password" autocomplete="new-password" minlength="8" maxlength="200" required>'):''}<p class="small">${create?'Use 8–200 characters. A longer unique password is recommended.':'Use your personal password, or a provided demo account and its review password.'}</p><p id="authError" role="alert"></p><button id="authSubmit" class="primary">${create?'Create account':'Sign in'}</button></form><button id="authSwitch">${create?'Already have an account? Sign in':'Create an account'}</button><p class="small muted">Review app: do not enter real medical information or upload medical documents. Email verification and self-service password recovery are not connected yet. Registration does not establish health-plan eligibility.</p></section>`;
  $('authSwitch').onclick=()=>loginScreen(!create);
  $('loginForm').onsubmit=async e=>{e.preventDefault();const button=$('authSubmit');button.disabled=true;$('authError').textContent='';
    try{
      const email=$('email').value.trim(),password=$('password').value;
      if(create){if(password!==$('confirmPassword').value)throw new Error('Passwords do not match');await api('/register',{name:$('accountName').value,email,password});loginScreen();$('email').value=email;$('authError').textContent='Account created. Sign in with your new password.';return}
      const r=await api('/login',{email,password});csrf=r.csrf;account=r.member;const next=pendingEntry;pendingEntry=null;try{await start()}catch(e){loadFailure(e);return}if(next)await enterJourney(next);
    }catch(error){$('authError').textContent=error.message}finally{button.disabled=false}
  };
}
function passwordScreen(){
  modal(`<h2>Change your password</h2><form id="passwordForm">${control('currentPassword','Current password','<input id="currentPassword" type="password" autocomplete="current-password" maxlength="200" required>')}${control('newPassword','New password (at least 8 characters)','<input id="newPassword" type="password" autocomplete="new-password" minlength="8" maxlength="200" required>')}${control('confirmNewPassword','Confirm new password','<input id="confirmNewPassword" type="password" autocomplete="new-password" minlength="8" maxlength="200" required>')}<p id="passwordError" role="alert"></p><button id="passwordSubmit" class="primary">Change password</button></form><p class="small">Changing your password signs this account out on all devices.</p>`);
  $('passwordForm').onsubmit=async e=>{e.preventDefault();const button=$('passwordSubmit');button.disabled=true;try{if($('newPassword').value!==$('confirmNewPassword').value)throw new Error('Passwords do not match');await saveQueue.catch(()=>{});await api('/password',{current_password:$('currentPassword').value,new_password:$('newPassword').value});epoch++;account=null;csrf='';state=defaults();results=[];offers=[];DIRECTORY=[];catalogReady=false;$('modal').close();loginScreen();$('authError').textContent='Password changed. Sign in again.'}catch(error){$('passwordError').textContent=error.message}finally{button.disabled=false}};
}
async function start(){updateNavigation();epoch++;results=[];state=defaults();state.member=`${account.tenant} / ${account.name}`;await loadCatalog();const pref=await api('/preferences');state.location=pref.location||'';welcome()}
$('home').textContent='Welcome';
$('home').onclick=welcome;
$('brandHome').onclick=e=>{if(e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;e.preventDefault();pendingEntry=null;welcome();globalThis.scrollTo?.({top:0,left:0,behavior:'instant'})};
$('history').onclick=safe(async()=>{if(!account)return loginScreen();await history()});
$('directory').onclick=safe(async()=>{if(!account)return loginScreen();await loadCatalog();directory()});
$('profile').onclick=()=>account?profile():loginScreen();
const bootReady=(async()=>{try{const r=await api('/me');account=r.member;csrf=r.csrf;await start()}catch(e){if(account)loadFailure(e);else welcome()}})();
