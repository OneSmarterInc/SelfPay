let currentPageKey='';
function pageTop(key){if(currentPageKey!==key){currentPageKey=key;globalThis.scrollTo?.({top:0,left:0,behavior:'instant'})}}
let DIRECTORY=[]; let offers=[]; let results=[];
const $=id=>document.getElementById(id),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function toast(t){$('toast').textContent=t;$('toast').classList.remove('hidden');setTimeout(()=>$('toast').classList.add('hidden'),4500)}
function price(o){return (o.type==='conflict'||o.type==='quote'||o.amount==null)?'Ask for a price':o.type==='starting'?`From $${o.amount}`:o.type==='range'?`$${o.amount}–$${o.max}`:o.type==='maximum'?`Up to $${o.amount}`:`$${o.amount}`}
function typeLabel(o){return {quote:'Price on request',average:'Published average · quote needed',fixed:'Published fixed',starting:'Starting price · quote needed',range:'Published range · quote needed',maximum:'Published maximum · quote needed',conflict:'Conflicting prices · quote needed'}[o.type]}
function budgetGroup(o,s=state){if(o.budget_status)return o.budget_status;if(!s.budget)return 'No budget set';if(o.type==='fixed'&&o.amount>s.budget)return 'Above your published-price budget';if(o.type==='conflict'||o.type==='maximum'||o.contrast==='unknown'||o.type==='starting'||(o.type==='range'&&o.max>s.budget))return 'Budget fit unconfirmed';return 'Published amount within budget · exact scope needs confirmation'}
function control(id,label,html){return `<div class="field"><label for="${id}">${label}</label>${html}</div>`}
function searchFields(){return control('radius','Search area',`<select id="radius"><option value="state" ${(state.scope||'state')==='state'?'selected':''}>Entire state</option>${[25,50,100,250].map(n=>`<option value="${n}" ${state.scope==='radius'&&(state.radius||50)===n?'selected':''}>${n} miles</option>`).join('')}</select>`)+control('mod','Imaging service (optional)',`<select id="mod"><option value="">All imaging services</option><option ${state.mod==='MRI'?'selected':''}>MRI</option><option ${state.mod==='CT'?'selected':''}>CT</option></select>`)+control('body','Body part / ordered exam (optional)',`<input id="body" value="${esc(state.body)}" placeholder="e.g. Knee">`)+control('contrast','Contrast requirement (optional)',`<select id="contrast">${[['unknown',"I'm not sure"],['without','Without contrast'],['with','With contrast'],['both','Without and with contrast']].map(([v,t])=>`<option value="${v}" ${state.contrast===v?'selected':''}>${t}</option>`).join('')}</select>`)+control('location','State or city (required)',`<div id="locationPicker" style="position:relative"><div style="display:flex"><input id="location" autocomplete="off" value="${esc(state.location)}" placeholder="e.g. Cincinnati, OH" style="min-width:0;flex:1"><button id="locationToggle" type="button" aria-label="Show all location options" aria-expanded="false" aria-controls="cityChoices">▼</button></div><div id="cityChoices" hidden style="position:absolute;top:100%;left:0;right:0;z-index:20;max-height:260px;overflow-y:auto;background:white;border:1px solid #b9cbd4;border-radius:8px;padding:6px;box-shadow:0 4px 12px #0002"></div></div><div id="locationSuggestions" role="status" aria-live="polite"></div>`)+control('budget','Budget in USD (optional)',`<input id="budget" type="number" min="0" value="${state.budget||''}">`)+control('type','Price status (optional)',`<select id="type">${[['all','All price types'],['fixed','Published fixed'],['starting','Starting prices'],['range','Ranges'],['conflict','Conflicts'],['maximum','Maximums'],['quote','Quote / confirmation required'],['average','Published averages']].map(([v,t])=>`<option value="${v}" ${state.type===v?'selected':''}>${t}</option>`).join('')}</select>`)}
function contrastLabel(v){return {without:'Without contrast',with:'With contrast',both:'Without and with contrast',unknown:'Contrast unconfirmed'}[v]||'Contrast unconfirmed'}
function chips(){const parts=[];if(state.mod)parts.push([state.mod,state.body].filter(Boolean).join(' · '));if(state.mod)parts.push(contrastLabel(state.contrast));if(state.location)parts.push(state.location);if(state.budget)parts.push('Budget $'+state.budget);return '<div class="chips">'+parts.map(t=>'<span class="chip">'+esc(t)+'</span>').join('')+'</div>'}
function distanceLabel(o){return Number.isFinite(o.distance_miles)?`about ${Math.round(o.distance_miles)} miles away${o.distance_precision==='city'?' (distance to city center)':o.distance_precision==='zip'?' (distance to ZIP-area reference point)':''} · straight-line distance`:''}
function phoneOf(e){const m=String(e?.coverage||'').match(/\(?(\d{3})\)?[-. ]?(\d{3})[-. ](\d{4})/);return m?`${m[1]}-${m[2]}-${m[3]}`:''}
function addressOf(e){const c=String(e?.coverage||'').replace(/\(?\d{3}\)?[-. ]?\d{3}[-. ]\d{4}/g,'').replace(/[.\s]+$/,'').trim();return /^\d+\s+\S/.test(c)?c:''}
function websiteOf(e){return /^https:\/\//.test(e?.source||'')?e.source:''}
function telLink(ph,cls,label){return `<a${cls?` class="${cls}"`:''} href="tel:+1${ph.replace(/-/g,'')}">${esc(label||ph)}</a>`}
function contactActions(o){const e=o.entry,ph=phoneOf(e),addr=addressOf(e),web=websiteOf(e);if(!ph&&!addr&&!web&&!appointmentEmail(e))return '';return `<div class="card-actions" aria-label="Contact ${esc(e.name)}">${ph?telLink(ph,'call','Call '+ph):''}${web?`<a href="${esc(web)}" target="_blank" rel="noopener noreferrer">Website</a>`:''}${appointmentEmail(e)?`<button type="button" data-appointment="${esc(e.name)}">Book appointment</button>`:''}${addr?`<a href="https://www.google.com/maps/search/?api=1&amp;query=${esc(encodeURIComponent(String(e.name).split(' — ')[0]+', '+addr))}" target="_blank" rel="noopener noreferrer">Directions</a>`:''}</div>`}
function cardFacts(o){const facts=[`<div class="fact"><strong>Price includes</strong><br>${esc(o.included)}</div>`];if(o.order&&!/^(Review the facility restrictions|Not established in this directory)/i.test(o.order))facts.push(`<div class="fact"><strong>Order requirements</strong><br>${esc(o.order)}</div>`);if(state.budget)facts.push(`<div class="fact"><strong>Budget check</strong><br>${budgetGroup(o)}</div>`);return `<div class="facts">${facts.join('')}</div>`}
function card(o){return `<article class="card">${o.reviewed_alternative?`<div class="notice"><strong>Reviewed alternative · filters differ</strong><p>${esc(o.match_status)}</p><ul>${(o.filter_differences||[]).map(d=>`<li>${esc(d)}</li>`).join('')}</ul></div>`:''}<div class="row between"><span class="badge ${o.type==='fixed'?'':'warn'}">${typeLabel(o)}</span><label class="small"><input style="width:auto" type="checkbox" aria-label="Compare ${esc(o.entry.name)}" data-select="${o.id}" ${state.selected.includes(o.id)?'checked':''}> Compare</label></div><div class="row between" style="margin-top:16px"><div><h3>${esc(o.entry.name)}</h3><div class="muted small">${esc(o.region)} · ${esc(o.entry.entity)}</div><div class="small">${esc(distanceLabel(o))}</div></div><div class="price">${price(o)}</div></div><p class="scope">${esc(o.mod)} · ${esc(o.contrast==='unknown'?'Protocol unconfirmed':(o.contrast==='both'?'Without and with':o.contrast==='without'?'Without':'With')+' contrast')} · ${esc(o.scope)}</p>${cardFacts(o)}${contactActions(o)}<div class="row between"><span class="small muted">Source checked ${o.entry.checked.slice(0,10)} · Reconfirm before arranging care</span><button data-detail="${o.id}">View details</button></div></article>`}
function locationPending(){return !!(state.locationSuggestions?.length||state.locationUnresolved)}
function locationPrompt(){return `<div class="panel" role="status"><h2>${state.locationSuggestions?.length?'Choose your city and state':'Enter a city and state or ZIP code'}</h2><p>${state.locationSuggestions?.length?'More than one location matches your search. Select the correct city beside the location field to find the nearest reviewed offers.':'We could not identify that location. Enter a city with its state, such as Baltimore, MD, or a five-digit ZIP code.'}</p><p>Your city does not need a provider listing in our directory. Once the location is confirmed, we search indexed facilities nationwide and show the nearest options.</p><button id="editLocation" type="button">${state.locationSuggestions?.length?'Choose location':'Update location'}</button></div>`}
function render(){if(locationPending())state.detailsOpen=true;pageTop('search:'+state.mode);const found=results;$('app').innerHTML=`<div class="row between"><div><div class="eyebrow">SELF-PAY IMAGING</div><h1>Find and compare imaging options</h1><div class="muted">Compare published prices and know what to confirm.</div></div><button id="scan">Add your doctor’s order</button></div><div class="tabs"><button id="classic" class="${state.mode==='classic'?'active':''}">Search & filters</button><button id="agent" class="${state.mode==='agent'?'active':''}">Ask MySelfPay</button><button id="explore">I don’t have an order</button></div><div class="row between small"><span>Signed in: ${esc(state.member)}</span><span>Private guest preview · Chat is not saved</span></div>${chips()}<div id="searchNotice" role="status"></div>${state.saveStatus==='failed'?'<p class="notice" role="alert">This search was not saved. Results are still available; try searching again to retry saving.</p>':''}<div class="grid ${state.mode==='agent'?'agent-layout':''}"><div class="stack" style="align-self:start;min-width:0"><aside class="panel"><details ${state.mode==='classic'||state.detailsOpen?'open':''}><summary>Search details</summary><p class="small muted">Use your clinician’s exam wording. You can browse without an order.</p><form id="searchForm">${searchFields()}<button class="primary" style="width:100%">Find options</button></form></details></aside></div><section class="stack">${state.mode==='agent'?`<div class="panel"><div class="row between"><h3>Ask MySelfPay</h3><span class="badge neutral">Server-guided demo</span></div><p class="small muted">No external AI or speech service is connected. Do not enter real personal or medical information.</p><div class="chat" id="chat">${state.messages.map(m=>`<div class="message ${m.role==='user'?'user':''}">${esc(m.text)}</div>`).join('')||'<div class="message">Hi, I’m MySelfPay. I can help you find imaging listings and understand published self-pay prices. Tell me your exam and location, or try “Find a self-pay knee MRI near Cincinnati under $500.” I will ask about missing procedure details.</div>'}</div>${guestChatControls()}<form id="chatForm" class="row"><label class="sr-only" for="message">Message</label><input id="message" maxlength="500" ${chatDisabled()?'disabled':''} placeholder="Describe your search" style="flex:1;min-width:180px" required><button class="primary" ${chatDisabled()?'disabled':''}>Send</button><button type="button" id="voice" ${chatDisabled()?'disabled':''}>Voice demo</button></form><p class="small" role="status">Guest conversation is not saved.</p></div>`:''}${!state.searched?initialSearch()+coverageSummary():locationPending()?locationPrompt():`<div class="row between"><h2>${found.length ? `${found.length} reviewed offer${found.length===1?'':'s'}` : (state.nearbyUnpriced?.length ? 'Nearest facilities to contact' : state.programs?.length||state.programEntries?.length ? 'Available programs' : 'Find options for your location')}</h2><select id="sort" ${found.some(o=>Number.isFinite(o.distance_miles))?'disabled title="Location results are sorted by distance"':''} aria-label="Sort results" style="width:auto"><option value="distance" ${state.sort==='distance'?'selected':''}>Nearest first</option><option value="scope" ${state.sort==='scope'?'selected':''}>Source order</option><option value="price" ${state.sort==='price'?'selected':''}>Fixed prices: low to high</option></select></div><p class="small">Select up to 3 options to compare. Confirm the same exam and contrast before comparing prices.</p>${groupedCards(found)||`<div class="panel"><h3>${state.noExamPrice?'No listed facility publishes a price for this exam':state.unlocatedOfferCount?'Distance results are incomplete':'No reviewed match for this search'}</h3>${state.unlocatedOfferCount?'<p>Some matching listings do not yet have verified facility coordinates. This does not mean no services are available. Browse National to review those listings while location data is being updated.</p>':''}<p>We have not changed your procedure. Try National to browse researched examples or view the directory for quote leads. “With contrast” and “without and with contrast” remain separate.</p><button id="widen">Browse National</button><button id="leads">View directory leads</button></div>`}`}${state.selected.length?`<div class="sticky row between"><span>${state.selected.length} option${state.selected.length===1?'':'s'} selected</span><div class="row"><button id="compare">Compare selected</button><button id="clearCompare" type="button" aria-label="Close comparison bar and clear all selections" title="Clear comparison selections">×</button></div></div>`:''}</section></div>`;bind()}
function readFields(){['mod','body','contrast','location','type'].forEach(k=>state[k]=$(k).value);state.budget=Number($('budget').value)||0;state.scope=$('radius').value==='state'?'state':'radius';state.radius=Number($('radius').value)||50}
function modal(html){html=html.replace('<h2>','<h2 id="dialogTitle">');$('modal').setAttribute('aria-labelledby','dialogTitle');$('modal').innerHTML=`<div class="modal-header row between"><span class="eyebrow">MYSELFPAY</span><button id="closeModal" aria-label="Close dialog">Close</button></div><div class="modal-body" id="modalBody">${html}</div>`;$('modal').showModal();$('modalBody').scrollTop=0;$('modalBody').scrollLeft=0;$('closeModal').onclick=()=>$('modal').close()}
function specificOrder(o){return o.order&&!/^(Review the facility restrictions|Not established in this directory)/i.test(o.order)?String(o.order).replace(/[.\s]+$/,''):''}
function questions(o){const exam=[state.body,o.mod].filter(Boolean).join(' ')||o.mod;const order=specificOrder(o);return [`Does this price apply to my exact ${exam} and the contrast my doctor ordered?`,'What is the all-in amount, including the radiologist, facility, contrast and supplies?','Can I use this self-pay price if I have insurance? Are there any program restrictions?',`Do you need a doctor’s order or referral?${order?` The listing says: ${order}.`:''}`,'Are the report and images included? What are the payment, cancellation and refund terms?']}
function norm(t){return String(t||'').toLowerCase().replace(/[^a-z0-9$]+/g,' ').trim()}
function restrictionsOf(o){const inc=norm(o.included);return String(o.entry.notes||'').split(/;|\.\s+/).map(t=>t.trim().replace(/\.$/,'')).filter(t=>t&&!inc.includes(norm(t)))}
function checkedDate(v){const d=new Date(String(v||'').slice(0,10)+'T12:00:00');return isNaN(d)?String(v||'').slice(0,10):d.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'})}
function facilityMap(entry){
 const locations=(entry.locations||[]).filter(l=>Number.isFinite(l.latitude)&&Math.abs(l.latitude)<=90&&Number.isFinite(l.longitude)&&Math.abs(l.longitude)<=180);
 if(!locations.length)return '<section class="facility-map"><h2>Location map</h2><p>No verified map reference is available. Confirm the address with the facility.</p></section>';
 return '<section class="facility-map"><h2>Location map</h2><p class="small">Map references may show a city or ZIP area rather than the building. Confirm the facility address before travelling.</p><p class="small">Loading a map connects to OpenStreetMap.</p>'+locations.map((l,i)=>`<button type="button" data-map-index="${i}">Load map: ${esc(l.city)}, ${esc(l.state)} (${esc(l.precision)} reference)</button>`).join('')+'<div id="facilityMapCanvas" aria-live="polite"></div></section>';
}
function bindFacilityMap(entry){
 const locations=(entry.locations||[]).filter(l=>Number.isFinite(l.latitude)&&Math.abs(l.latitude)<=90&&Number.isFinite(l.longitude)&&Math.abs(l.longitude)<=180);
 document.querySelectorAll('[data-map-index]').forEach(button=>button.onclick=()=>{
  const l=locations[Number(button.dataset.mapIndex)];if(!l)return;
  const bbox=[Math.max(-180,l.longitude-.04),Math.max(-90,l.latitude-.025),Math.min(180,l.longitude+.04),Math.min(90,l.latitude+.025)];
  const iframe=document.createElement('iframe');iframe.title=`Map reference for ${l.city}, ${l.state}`;iframe.referrerPolicy='no-referrer';iframe.loading='lazy';
  iframe.src='https://www.openstreetmap.org/export/embed.html?bbox='+encodeURIComponent(bbox.join(','))+'&layer=mapnik&marker='+encodeURIComponent(l.latitude+','+l.longitude);
  $('facilityMapCanvas').replaceChildren(iframe);
 });
}
function detail(id){pageTop('detail:'+id);const o=offers.find(x=>x.id===id);const where=addressOf(o.entry)||o.entry.coverage;const restrictions=restrictionsOf(o);const more=String(o.entry.additional||'').split(/\s+/).filter(x=>x.startsWith('https://'));$('app').innerHTML=`<button id="back">Back to results</button><div class="detailgrid"><section class="panel"><span class="badge ${o.type==='fixed'?'':'warn'}">${typeLabel(o)}</span><h1>${esc(o.entry.name)}</h1><p class="muted">${esc(where)}</p><div class="price">${price(o)}</div><p>${esc(o.mod)} · ${esc(contrastLabel(o.contrast))} · ${esc(o.scope)}</p><div class="notice">Confirm the exact exam, eligibility and all-in price with the facility. MySelfPay does not guarantee price or availability.</div><h2>What the price includes</h2><p>${esc(o.included)}</p>${restrictions.length?`<h2>Restrictions</h2><ul>${restrictions.map(t=>`<li>${esc(t)}</li>`).join('')}</ul>`:''}<h2>Questions to ask the facility</h2><ul class="checklist">${questions(o).map(q=>`<li>${esc(q)}</li>`).join('')}</ul></section><aside class="panel"><h2>Contact this facility</h2><p>${esc(where)}</p>${contactActions(o)||'<p class="small">Contact details are not available in this listing.</p>'}${more.map((url,i)=>`<p><a href="${esc(url)}" target="_blank" rel="noopener noreferrer">More from this facility${more.length>1?' ('+(i+1)+')':''}</a></p>`).join('')}<p class="small muted">Source checked ${esc(checkedDate(o.entry.checked))}.</p><button id="request" class="primary">Ask for a self-pay price</button>${facilityMap(o.entry)}</aside></div>`;$('back').onclick=render;$('request').onclick=()=>request(o);bindFacilityMap(o.entry)}
function compare(){const chosen=state.selected.map(id=>offers.find(o=>o.id===id)).filter(Boolean);const rows=[['Published price',o=>price(o)],['Price status',typeLabel],['Exam',o=>o.mod+' · '+contrastLabel(o.contrast)],['Price scope',o=>o.scope],['Included',o=>o.included],['Requirements',o=>o.order],['Budget',budgetGroup],['Source checked',o=>o.entry.checked.slice(0,10)]];modal(`<h2>Compare selected options</h2><p class="notice">Confirm the same exam and contrast before comparing totals. Published prices are not current quotes.</p><div class="comparison-scroll"><table class="comparison-table"><thead><tr><th scope="col">Details</th>${chosen.map(o=>`<th scope="col">${esc(o.entry.name)}</th>`).join('')}</tr></thead><tbody>${rows.map(([label,value])=>`<tr><th scope="row">${label}</th>${chosen.map(o=>`<td>${esc(value(o))}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`)}
function scan(){
 modal(`<h2>Add your doctor’s order</h2><p>We’ll help read the requested exam so you can search for matching services. You’ll review the details before searching.</p><p class="notice">Sample demonstration only. No real upload or OCR is connected; no document is collected or saved.</p><div class="actions"><button disabled>Take a photo · later</button><button disabled>Upload photo or PDF · later</button></div><h3>Try a sample order</h3><button id="clearOrder">Readable sample</button> <button id="badOrder">Unreadable sample</button> <button id="manualOrder">Enter details manually</button><div id="orderPreview"></div>`);
 const show=kind=>{
 const good=kind==='clear';
 $('orderPreview').innerHTML=`<p>${good?'Sample: Left knee MRI without contrast. Review each field.':kind==='bad'?'The sample is unreadable. Enter the details manually or try the readable sample. We will not guess.':'Enter the exam wording you know. Confirm unclear details with your clinician.'}</p>${control('orderMod','Exam','<select id="orderMod"><option value="">Choose exam</option><option '+(good?'selected':'')+'>MRI</option><option>CT</option></select>')}${control('orderBody','Body part','<input id="orderBody" value="'+(good?'Knee':'')+'">')}${control('orderSide','Side','<select id="orderSide"><option value="">Not specified / unsure</option><option '+(good?'selected':'')+'>Left</option><option>Right</option><option>Bilateral</option></select>')}${control('orderContrast','Contrast','<select id="orderContrast"><option value="unknown">Not sure</option><option value="without" '+(good?'selected':'')+'>Without contrast</option><option value="with">With contrast</option><option value="both">Without and with contrast</option></select>')}<button id="confirmOrder" class="primary">Confirm details & continue</button>`;
 $('confirmOrder').onclick=safe(async()=>{if(!$('orderMod').value||!$('orderBody').value.trim())return toast('Enter the exam and body part. Unclear details are not guessed.');state.mod=$('orderMod').value;state.body=[$('orderSide').value,$('orderBody').value.trim()].filter(Boolean).join(' ');state.contrast=$('orderContrast').value;$('modal').close();state.detailsOpen=true;await search();if(!state.location&&$('location'))$('location').focus()});
 };
 $('clearOrder').onclick=()=>show('clear');$('badOrder').onclick=()=>show('bad');$('manualOrder').onclick=()=>show('manual');
}
function explore(){modal(`<h2>I don’t have an order</h2><p>You can explore prices for a known exam. A facility may require a clinician’s order before performing it.</p><div class="stack"><button id="known">I know the imaging exam — browse prices</button><div class="lead"><h3>I want a specialist second opinion</h3><span class="badge neutral">Planned · not available yet</span><p>Find a specialist consultation in a future version.</p></div><div class="lead"><h3>I want my existing images reviewed</h3><span class="badge neutral">Planned · not available yet</span><p>Image-review services are planned for a future version.</p></div></div><p>MySelfPay cannot decide which medical test you need.</p>`);$('known').onclick=()=>{$('modal').close();state.mode='classic';render()}}
function coverageSummary(showPublished=false){
  if(!catalogReady)return showPublished?'<section class="panel" id="publicCoverage" aria-live="polite"><p>Loading directory coverage…</p></section>':'';
  const validStates=new Set('AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split(' '));
  const states=new Set();
  for(const entry of DIRECTORY){
    for(const state of String(entry.states||'').toUpperCase().split(/[;,/|]+/)){if(validStates.has(state.trim()))states.add(state.trim())}
    for(const location of entry.locations||[]){const state=String(location.state||'').toUpperCase().trim();if(validStates.has(state))states.add(state)}
  }
  return `<section class="panel"><p><strong>${DIRECTORY.length.toLocaleString()}</strong> imaging facilities and programs listed so far.</p></section>`;
}
function initialSearch(){const q=state.location.trim().toLowerCase();const leads=q&&!/^\d/.test(q)?DIRECTORY.filter(d=>d.area.toLowerCase().includes(q)||d.states.toLowerCase()===q):[];return `<div class="panel"><h2>${state.location?'Browse imaging centers in your state':'Where would you like to search?'}</h2><p>${state.mod&&state.body.trim()?'Your exam details are ready. Enter a city or state to find options.':'Select your state to browse imaging centers. All other filters are optional.'}</p><p class="small">Directory loaded: ${DIRECTORY.length} researched entries · ${offers.length} mapped price offers. Entries can represent facilities, branches or programs; coverage is limited.</p><div class="actions"><button id="sampleSearch">Try sample: knee MRI in Cincinnati</button><button id="browseDirectory">Browse all directory entries</button></div><p class="small">The sample is a demonstration search, not a recommendation for a medical test.</p><p class="small">Search by city or ZIP for approximate straight-line distances to imported facility locations.</p>${leads.length?'<h3>Directory locations in your search area</h3><p class="small">Entries may cover multiple locations. Service availability and exact addresses require confirmation.</p>'+leads.map(d=>`<div class="lead"><strong>${esc(d.name)}</strong><p>${esc(d.area)}</p><a href="${esc(d.source)}" target="_blank" rel="noopener noreferrer">Check provider locations</a></div>`).join(''):''}</div>`}
function groupedCards(found){return (state.resultsHeading?`<h2>${esc(state.resultsHeading)}</h2>`:'')+found.map(card).join('')+((state.programs?.length||state.programEntries?.length)?`<h2>${esc(state.programHeading)}</h2>`+state.programs.map(card).join('')+(state.programEntries||[]).map(e=>`<article class="card"><h3>${esc(e.name)}</h3><p>Confirm service availability and request a quote.</p>${contactActions({entry:e})||`<a href="${esc(e.source)}" target="_blank" rel="noopener noreferrer">Program website</a>`}</article>`).join(''):'')+(state.nearbyUnpriced?.length?'<h2>Facilities to contact for a quote</h2><p>Confirm the ordered exam, eligibility and total directly with the facility.</p>'+state.nearbyUnpriced.map(e=>`<article class="card"><h3>${esc(e.name)}</h3><p>${esc(distanceLabel(e))}</p><strong>Call for a self-pay price</strong>${contactActions({entry:e})}</article>`).join(''):'')}

function request(o){const ph=phoneOf(o.entry),exam=[state.body,o.mod].filter(Boolean).join(' ')||o.mod;modal(`<h2>Ask for a self-pay price</h2><p>${esc(o.entry.name)}</p>${ph?`<p class="card-actions">${telLink(ph,'call','Call '+ph)}</p>`:'<p>Use the facility website to reach them.</p>'}<p>When you call, say you are paying yourself and ask for the all-in price for your ${esc(exam)}${state.contrast&&state.contrast!=='unknown'?` (${esc(contrastLabel(state.contrast).toLowerCase())})`:''}. Have your doctor’s order nearby.</p><h3>Questions to ask</h3><ul class="checklist">${questions(o).map(q=>`<li>${esc(q)}</li>`).join('')}</ul><p class="small muted">Published reference: ${price(o)} · ${typeLabel(o)}</p>`)}
function directory(){
  modal(`<h2>Research directory · ${DIRECTORY.length} entries</h2><p>Entries may represent facilities, branches or programs. ${offers.length} reviewed price offers are mapped for search.</p>${control('dirSearch','Filter directory by name, area or state','<input id="dirSearch" placeholder="e.g. Tellica, OH, Vermont">')}<p id="dirCount" role="status"></p><div id="dirRows"></div><div class="actions"><button id="dirPrev" type="button">Previous</button><button id="dirNext" type="button">Next</button></div>`);
  const indexed=DIRECTORY.map(d=>({d,text:[d.name,d.area,d.states].join(' ').toLowerCase()}));
  let page=0;
  function show(){
    const q=$('dirSearch').value.trim().toLowerCase();
    const matches=indexed.filter(item=>item.text.includes(q));
    const pages=Math.max(1,Math.ceil(matches.length/50));
    page=Math.min(page,pages-1);
    const start=page*50;
    $('dirCount').textContent=matches.length ? `Showing ${start+1}–${Math.min(start+50,matches.length)} of ${matches.length} matches` : 'No directory entries match.';
    $('dirRows').innerHTML=matches.slice(start,start+50).map(({d})=>`<details class="lead"><summary>${esc(d.name)} · ${esc(d.states)}</summary><span class="badge neutral">${esc(d.category)}</span><p>${esc(d.area)} · ${esc(d.entity)}</p><p><strong>MRI:</strong> ${esc(d.mri)}<br><strong>CT:</strong> ${esc(d.ct)}</p><p><strong>Other imaging:</strong> ${esc(d.other)}</p><p><strong>Location / coverage:</strong> ${esc(d.coverage)}</p><p>${esc(d.notes)}</p><a href="${esc(d.source)}" target="_blank" rel="noopener noreferrer">Provider source</a><p class="small">Checked ${esc(String(d.checked||'').slice(0,10))}</p></details>`).join('');
    $('dirPrev').disabled=page===0;
    $('dirNext').disabled=page>=pages-1;
  }
  $('dirPrev').onclick=()=>{page--;show()};
  $('dirNext').onclick=()=>{page++;show()};
  $('dirSearch').oninput=()=>{page=0;show()};
  show();
}


let cityLabels=['Cincinnati, OH','Louisville, KY','Lexington, KY','Philadelphia, PA','Boise, ID','Lawrenceville, GA','Auburn, WA','Spanish Fork, UT','South Burlington, VT','Wisconsin','National'];
/* Shared server-backed search and account-scoped persistence. No browser storage. */
let csrf='',account=null,currentVersion='',busy=false,saveQueue=Promise.resolve(),epoch=0,catalogReady=false;
const defaults=()=>({mod:'',body:'',contrast:'unknown',location:'',budget:0,type:'all',mode:'classic',selected:[],private:true,messages:[],conversationId:null,usage:{},chatBlocked:false,chatLimitReason:null,member:'',savedId:null,sort:'distance',scope:'state',radius:50,programs:[],nearbyUnpriced:[],resultsHeading:''});
let state=defaults();
async function api(path,data,method){
  const options={method:method||(data?'POST':'GET'),credentials:'same-origin',headers:{}};
  if(options.method!=='GET')options.headers['X-CSRF-Token']=csrf;
  if(data!==undefined){options.headers['Content-Type']='application/json';options.body=JSON.stringify(data)}
  const response=await fetch('/api'+path,options);const body=await response.json();
  if(!response.ok){if(response.status===401&&path!=='/login'){account=null;epoch++;loginScreen()}const error=new Error(body.error||'Request failed');error.status=response.status;error.code=body.code;error.reason=body.reason;error.retryAfter=body.retry_after;throw error}
  return body;
}
function safe(fn){return (...args)=>Promise.resolve().then(()=>fn(...args)).catch(e=>toast(e.message))}
async function loadCatalog(){catalogReady=false;const data=await api('/catalog');if(!Array.isArray(data.entries)||!Array.isArray(data.offers)||!data.version)throw new Error('Provider directory is not published yet. Contact the review administrator.');DIRECTORY=data.entries;offers=data.offers;if(Array.isArray(data.locations))cityLabels=data.locations;currentVersion=data.version;catalogReady=true}
function loadFailure(error){pageTop('load-error');$('app').innerHTML=`<section class="panel"><h1>Unable to load your review session</h1><p role="alert">${esc(error.message)}</p><p>Your search history has not been deleted. Retry to load the provider directory from the database.</p><button id="retrySession" class="primary">Retry loading</button></section>`;$('retrySession').onclick=()=>start().catch(loadFailure)}

async function loadResults(){const started=epoch;const data=await api('/search',state);if(started!==epoch)return null;results=data.offers;state.locationSuggestions=data.location_suggestions||[];state.locationUnresolved=data.resolved_location===null&&!!data.search.location&&data.search.location.toLowerCase()!=='national';state.locationNotice=data.location_notice||'';state.unlocatedOfferCount=data.unlocated_offer_count||0;state.programs=data.programs||[];state.programEntries=data.program_entries||[];state.nearbyUnpriced=data.nearby_unpriced||[];state.noExamPrice=!!data.no_exam_price;state.resultsHeading=data.results_heading||'';state.programHeading=data.program_heading||'';state.dirty=false;currentVersion=data.version;Object.assign(state,data.search);const byId=new Map(offers.map(o=>[o.id,o]));[...results,...state.programs].forEach(o=>byId.set(o.id,o));offers=[...byId.values()];return data}
async function search(){state.searched=!!state.location.trim();if(!state.searched){results=[];state.detailsOpen=true;render();$('searchNotice').textContent=!state.location?'Enter your ZIP, city or state to continue.':'Select a state to browse imaging centers.';return}if(!await loadResults())return;try{await save()}finally{render()}}
function save(){
  if(account?.tenant==='guest'||state.private||(!state.messages.length&&!state.searched)||!account)return Promise.resolve();
  state.saveStatus='saving';const started=epoch;const id=state.savedId||crypto.randomUUID();state.savedId=id;
  const payload=JSON.parse(JSON.stringify({id,private:false,messages:state.messages,search:state}));
  saveQueue=saveQueue.catch(()=>{}).then(async()=>{if(started!==epoch)return;await api('/conversations',payload)});
  return saveQueue.then(()=>{if(started===epoch)state.saveStatus='saved'}).catch(e=>{if(started===epoch)state.saveStatus='failed';toast('Conversation not saved: '+e.message);throw e});
}
function bind(){
  if($('editLocation'))$('editLocation').onclick=()=>{$('location').focus();$('location').scrollIntoView?.({block:'center',behavior:'smooth'})};
  $('scan').onclick=scan;$('explore').onclick=explore;
  document.querySelectorAll('[data-detail]').forEach(b=>b.onclick=()=>detail(b.dataset.detail));
  if($('compare'))$('compare').onclick=compare;
  if($('clearCompare'))$('clearCompare').onclick=safe(async()=>{state.selected=[];render();await save()});
  if($('leads'))$('leads').onclick=directory;
  if($('voice'))$('voice').onclick=voice;
  const showDirty=()=>{if($('searchNotice'))$('searchNotice').textContent=state.dirty?'Search changed—click Find options to update results. Displayed results belong to your previous search.':(/^Distances are approximate straight-line miles\b/.test(state.locationNotice||'')?'':(state.locationNotice||''));document.querySelectorAll('[data-select],[data-detail],#compare').forEach(b=>b.disabled=!!state.dirty)};
  showDirty();
  for(const id of ['mod','body','contrast','location','budget','type','radius'])$(id).oninput=()=>{if(state.searched)state.dirty=true;showDirty()};
  if($('locationSuggestions')){$('locationSuggestions').innerHTML=(state.locationSuggestions||[]).length?'<p class="small"><strong>Which location did you mean?</strong> Choose a city and state to find the nearest offers.</p>'+state.locationSuggestions.map(label=>`<button type="button" data-city="${esc(label)}">${esc(label)}</button>`).join(''):'';document.querySelectorAll('[data-city]').forEach(b=>b.onclick=safe(async()=>{readFields();state.location=b.dataset.city;await search()}))}

  const locationInput=$('location'), locationToggle=$('locationToggle'), locationChoices=$('cityChoices');
  const closeLocations=()=>{locationChoices.hidden=true;locationToggle.setAttribute('aria-expanded','false')};
  const openLocations=(all=false)=>{
    const query=all?'':locationInput.value.trim().toLowerCase();
    const labels=[...new Set(cityLabels)].filter(label=>!query||label.toLowerCase().includes(query));
    locationChoices.innerHTML=labels.length?labels.map(label=>`<button type="button" data-location-choice="${esc(label)}" style="display:block;width:100%;text-align:left;margin:0;border:0">${esc(label)}</button>`).join(''):'<p class="small">No suggestions. You can still search by city or ZIP.</p>';
    locationChoices.hidden=false;locationToggle.setAttribute('aria-expanded','true');
    locationChoices.querySelectorAll('[data-location-choice]').forEach(button=>button.onclick=()=>{locationInput.value=button.dataset.locationChoice;locationInput.dispatchEvent(new Event('input',{bubbles:true}));closeLocations();locationInput.focus()});
  };
  locationToggle.onclick=()=>locationChoices.hidden?openLocations(true):closeLocations();
  const markLocationDirty=locationInput.oninput;
  locationInput.oninput=()=>{markLocationDirty();openLocations()};
  $('locationPicker').onkeydown=e=>{if(e.key==='Escape'){closeLocations();locationInput.focus()}else if(e.key==='ArrowDown'&&e.target===locationInput){e.preventDefault();openLocations(true);locationChoices.querySelector('button')?.focus()}};
  $('locationPicker').onfocusout=e=>{if(!e.currentTarget.contains(e.relatedTarget))closeLocations()};

  // preventDefault must happen during dispatch, not in the asynchronous safe wrapper.
  $('searchForm').onsubmit=e=>{e.preventDefault();safe(async()=>{readFields();await search()})()};
  $('classic').onclick=safe(async()=>{readFields();state.mode='classic';render()});
  $('agent').onclick=safe(async()=>{readFields();state.mode='agent';render()});
  if($('sort'))$('sort').onchange=safe(async e=>{readFields();state.sort=e.target.value;await search()});
  document.querySelectorAll('[data-select]').forEach(b=>b.onchange=safe(async()=>{if(b.checked&&state.selected.length>=3){b.checked=false;return toast('Compare up to three options.')}state.selected=b.checked?[...state.selected,b.dataset.select]:state.selected.filter(x=>x!==b.dataset.select);try{await save()}finally{render()}}));
  if($('sampleSearch'))$('sampleSearch').onclick=safe(async()=>{Object.assign(state,{mod:'MRI',body:'Knee',contrast:'without',location:'Cincinnati, OH',budget:500,type:'all'});await search()});
  if($('browseDirectory'))$('browseDirectory').onclick=safe(async()=>{await loadCatalog();directory()});
  if($('widen'))$('widen').onclick=safe(async()=>{state.location='National';await search()});
  document.querySelectorAll('[data-starter]').forEach(b=>b.onclick=safe(()=>talk(b.dataset.starter)));
  if($('newGuestChat'))$('newGuestChat').onclick=()=>{state.conversationId=null;state.messages=[];render()};
  if($('chatForm')){
    $('chatForm').onsubmit=e=>{e.preventDefault();safe(async()=>{readFields();await talk($('message').value)})()};
    if($('resumeSave'))$('resumeSave').onclick=safe(async()=>{await save();toast(state.private?'Private conversation is not saved.':'Conversation saved to this account.')});
  }
};
async function talk(text){
  if(busy||chatDisabled())return;busy=true;const started=epoch;
  try{
    const data=await api('/agent',{message:text,search:state,private:true,conversation_id:state.conversationId});
    state.conversationId=data.conversation_id;state.usage=data.usage||state.usage;
    if(started!==epoch)return;
    state.messages.push({role:'user',text},{role:'assistant',text:data.reply});
    Object.assign(state,data.search);state.searched=!!state.location.trim();results=data.offers;state.locationSuggestions=data.location_suggestions||[];state.locationUnresolved=data.resolved_location===null&&!!data.search.location&&data.search.location.toLowerCase()!=='national';state.locationNotice=data.location_notice||'';state.unlocatedOfferCount=data.unlocated_offer_count||0;state.programs=data.programs||[];state.programEntries=data.program_entries||[];state.nearbyUnpriced=data.nearby_unpriced||[];state.noExamPrice=!!data.no_exam_price;state.resultsHeading=data.results_heading||'';state.programHeading=data.program_heading||'';state.dirty=false;currentVersion=data.version;
    const byId=new Map(offers.map(o=>[o.id,o]));[...results,...state.programs].forEach(o=>byId.set(o.id,o));offers=[...byId.values()];
    try{await save()}finally{render()};
  }catch(error){if(error.status===429){state.chatBlocked=error.reason!=="characters";state.chatLimitReason=error.reason;render();toast(error.message)}else throw error}finally{busy=false}
}
function voice(){modal('<h2>Voice conversation preview</h2><p>No microphone or speech service is connected. This editable sample transcript uses the same server search.</p><div class="field"><label for="transcript">Review sample transcript</label><textarea id="transcript">Find a self-pay knee MRI near Cincinnati under $500</textarea></div><button id="useTranscript" class="primary">Use transcript</button>');$('useTranscript').onclick=safe(async()=>{const t=$('transcript').value;$('modal').close();await talk(t)})}
async function history(){
  if(state.private)return toast('Exit private mode to access saved conversations.');
  const {conversations:list}=await api('/conversations');
  modal(`<h2>Saved conversations and searches</h2><p class="small">Owned by ${esc(state.member)}. Expires after 90 days without activity. Resuming refreshes the database listings; old messages remain historical.</p>${list.map(c=>`<div class="lead"><strong>${esc(c.title)}</strong><p class="small">Expires ${new Date(c.expires).toLocaleDateString()}</p><button data-resume="${esc(c.id)}">Continue</button> <button data-delete="${esc(c.id)}">Delete</button></div>`).join('')||'<p>No saved conversations or searches yet.</p>'}<div class="actions"><button id="deleteAll">Delete all my conversations</button><button id="deletePref">Delete remembered location</button></div>`);
  document.querySelectorAll('[data-resume]').forEach(b=>b.onclick=safe(async()=>{const c=list.find(x=>x.id===b.dataset.resume);Object.assign(state,c.search,{messages:c.messages,savedId:c.id,private:false,mode:c.messages.length?'agent':'classic'});await loadCatalog();await loadResults();state.searched=!!state.location.trim();$('modal').close();render();toast(c.version!==currentVersion?'Directory changed since this conversation. Review refreshed prices and restrictions.':'Search refreshed from the current database. Reconfirm published prices with the facility.')}));
  document.querySelectorAll('[data-delete]').forEach(b=>b.onclick=safe(async()=>{await saveQueue.catch(()=>{});await api('/conversations/'+b.dataset.delete,undefined,'DELETE');if(state.savedId===b.dataset.delete){state.savedId=null;state.messages=[]} $('modal').close();await history()}));
  $('deleteAll').onclick=safe(async()=>{await saveQueue.catch(()=>{});await api('/conversations/all',undefined,'DELETE');state.messages=[];state.savedId=null;$('modal').close();await history()});
  $('deletePref').onclick=safe(async()=>{await api('/preferences',undefined,'DELETE');toast('Remembered location deleted.')});
}
function report(o){
  if(state.private)return toast('Exit private mode before submitting a saved correction report.');
  modal(`<h2>Report incorrect information</h2><p>${esc(o.entry.name)}</p><form id="reportForm">${control('reportType','What needs review?','<select id="reportType"><option>Price</option><option>Contact details</option><option>Eligibility or restrictions</option><option>Other</option></select>')}${control('reportText','Describe the issue using synthetic information','<textarea id="reportText" required maxlength="1000"></textarea>')}<button class="primary">Save correction report</button></form><p class="small muted">Saved in the database for reviewer inspection. No facility is contacted and no listing changes automatically.</p>`);
  $('reportForm').onsubmit=e=>{e.preventDefault();safe(async()=>{await api('/corrections',{offer_id:o.id,category:$('reportType').value,description:$('reportText').value});$('modal').close();toast('Correction saved as pending review. Listing unchanged.')})()};
}
async function signOut(){
  await saveQueue.catch(()=>{});await api('/logout',{});epoch++;account=null;csrf='';
  state=defaults();results=[];offers=[];DIRECTORY=[];catalogReady=false;pendingEntry=null;
  $('modal').close();welcome();
}
let guestBusy=false;
async function signInGuest(kind='search'){
  if(guestBusy)return;guestBusy=true;$('profile').disabled=true;
  try{const r=await api('/guest',{});account=r.member;csrf=r.csrf;
    try{await start()}catch(e){loadFailure(e);return}
    await enterJourney(kind);
  }finally{guestBusy=false;$('profile').disabled=false}
}
let pendingEntry=null;
function updateNavigation(){$('history').hidden=true;$('directory').hidden=!account;$('profile').textContent=account?'Sign out':'Start searching'}
async function loadPublicCoverage(){
  const target=$('publicCoverage');
  if(!target)return;
  try{
    const response=await fetch('/api/directory-summary',{cache:'no-store',credentials:'omit'});
    if(!response.ok)throw new Error('Summary unavailable');
    const data=await response.json();
    if(!Number.isInteger(data.listing_count)||data.listing_count<0||!Number.isInteger(data.state_count)||data.state_count<0||data.state_count>50)throw new Error('Invalid summary');
    if($('publicCoverage')===target)target.innerHTML=`<p><strong>${data.listing_count.toLocaleString()}</strong> imaging facilities and programs listed so far.</p>`;
  }catch{if($('publicCoverage')===target)target.textContent='Directory coverage is temporarily unavailable.'}
}
function welcome(){updateNavigation();pageTop('welcome');
  $('app').innerHTML=`<section class="welcome-intro"><div><div class="eyebrow">WELCOME TO MYSELFPAY</div><h1>Find self-pay MRI and CT near you.</h1><p class="welcome-lead">Compare published prices, see what’s included, and call the facility in one tap.</p><p>You can explore self-pay options whether you have health coverage or are paying entirely yourself. Your facility confirms the exact service, eligibility and final price.</p><div class="actions"><button class="primary" id="welcomeBegin">${'Find imaging options'}</button>${account?'':'<button id="welcomeAccount">Start as a guest</button>'}</div></div><aside class="welcome-account"><h2>Start as a guest.</h2><p>Search and compare prices with no account. Chat with MySelfPay for up to 3 conversations of 5 messages each.</p><p class="small">Your session lasts up to 8 hours. Enter just your exam and city. We keep only usage counts.</p></aside></section><section class="welcome-steps" aria-label="How MySelfPay works"><div><span class="step-number">1</span><h3>Tell us what you need</h3><p>Use the service on your order, type a request, or try the sample order scan.</p></div><div><span class="step-number">2</span><h3>Compare the details</h3><p>Review prices, included fees and restrictions for relevant options.</p></div><div><span class="step-number">3</span><h3>Confirm with the facility</h3><p>Use provider links and a question checklist to confirm the exact exam and total.</p></div></section><section class="welcome-paths"><h2>How would you like to begin?</h2><div class="welcome-choices"><button class="journey-card" data-journey="search"><strong>Search for a service</strong><span>Choose your imaging exam and location.</span></button><button class="journey-card" data-journey="agent"><strong>Ask MySelfPay</strong><span>Describe your search in a conversation.</span></button><button class="journey-card" data-journey="scan"><strong>I have a doctor's order</strong><span>Try the sample scan and review the exam details.</span></button></div><button id="welcomeExplore" style="margin-top:16px">I don't have an order</button></section>${coverageSummary(true)}`;
  void loadPublicCoverage();
  if($('continueSearch'))$('continueSearch').onclick=safe(history);
  $('welcomeBegin').onclick=safe(()=>enterJourney('search'));
  if($('welcomeAccount'))$('welcomeAccount').onclick=safe(()=>signInGuest());
  $('welcomeExplore').onclick=safe(()=>enterJourney('explore'));
  document.querySelectorAll('[data-journey]').forEach(b=>b.onclick=safe(()=>enterJourney(b.dataset.journey)));
}
async function enterJourney(kind){
  if(!account){await signInGuest(kind);return}
  if(!catalogReady){try{await start()}catch(e){loadFailure(e);return}}
  state.mode=kind==='agent'?'agent':'classic';render();
  if(kind==='scan')scan();else if(kind==='explore')explore();
}
function loginScreen(){welcome()}
async function start(){updateNavigation();epoch++;results=[];state=defaults();state.member=`${account.tenant} / ${account.name}`;await loadCatalog();state.usage=(await api('/guest-usage')).usage||{};state.conversationId=Object.keys(state.usage).at(-1)||null;state.location='';welcome()}
$('brandHome').onclick=e=>{if(e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;e.preventDefault();if(globalThis.location?.hash)globalThis.history?.replaceState?.(null,'',globalThis.location.pathname);pendingEntry=null;welcome();globalThis.scrollTo?.({top:0,left:0,behavior:'instant'})};
$('history').onclick=safe(async()=>{if(!account)return loginScreen();await history()});
$('directory').onclick=safe(async()=>{if(!account)return loginScreen();await loadCatalog();directory()});
$('profile').onclick=safe(()=>account?signOut():signInGuest());

const PARTNER_EMAIL='partners@onesmarter.com';
const PAGES={
 'for-imaging-centers':{title:'For imaging centers',body:()=>`<p class="welcome-lead">Self-pay patients compare prices before they call. MySelfPay shows them yours.</p><h2>What patients see today</h2><p>Each of your centers with its distance, phone, website and directions, plus your published self-pay price, or “Price on request.”</p><h2>Show your price</h2><p>Send us your self-pay prices for your most common exams, what each includes, and how long it holds. We publish them, and patients see your number instead of a phone call.</p><h2>Coming next</h2><p>Open times and booking requests that your staff or scheduling system confirms. Patients pay on your own payment page.</p><p><strong>Free during the pilot.</strong></p><div class="actions"><a class="button primary" href="mailto:${PARTNER_EMAIL}?subject=${encodeURIComponent('MySelfPay for our imaging center')}">Talk to us</a><a class="button" href="mailto:${PARTNER_EMAIL}?subject=${encodeURIComponent('Correct our MySelfPay listing')}">Correct your listing</a></div>`},
 'contact':{title:'Contact',body:()=>`<p>MySelfPay is built by One Smarter, Inc. in Dayton, Ohio.</p><p>Questions, corrections or partnership requests: <a href="mailto:${PARTNER_EMAIL}">${PARTNER_EMAIL}</a>.</p><p>Imaging centers: see <a href="#for-imaging-centers">For imaging centers</a>.</p>`},
 'privacy':{title:'Privacy',body:()=>`<p>MySelfPay works without an account. When you search, we use the exam and city you type to find facilities near you. That search location is used for your search only and is not saved.</p><p>Chat messages stay on your page and clear when you refresh it.</p><p>To run guest limits, we store a session cookie for up to 8 hours and counts of how many chats you’ve started.</p><p>We never collect your name, health records or payment details.</p><p>When you call or visit a facility, its own privacy practices apply.</p><p>Questions: <a href="mailto:${PARTNER_EMAIL}">${PARTNER_EMAIL}</a>.</p>`},
 'terms':{title:'Terms',body:()=>`<p>MySelfPay lists self-pay prices that facilities publish. Prices, eligibility and availability are set by each facility and can change. Confirm them with the facility before your exam.</p><p>MySelfPay doesn’t provide medical advice. Your clinician decides which exam you need.</p><p>Facility names and prices belong to their owners and are shown for comparison.</p><p>Use of the site is at your own discretion.</p>`},
};
function infoPage(key){const page=PAGES[key];if(!page)return false;updateNavigation();pageTop('page:'+key);document.title=`${page.title} · MySelfPay`;$('app').innerHTML=`<article class="panel info-page"><h1>${esc(page.title)}</h1>${page.body()}<p class="actions"><a href="/">Back to MySelfPay</a></p></article>`;return true}
function routeHash(){if(globalThis.location?.hash==='#booking-test'){openBookingTest().catch(e=>toast(e.message));return true;}const legacy=String(globalThis.location?.hash||'').slice(1);const destinations={privacy:'/privacy-terms',terms:'/privacy-terms',contact:'/contact','for-imaging-centers':'/for-imaging-centers'};if(destinations[legacy]){globalThis.location.replace(destinations[legacy]);return true;}const key=decodeURIComponent(String(globalThis.location?.hash||'').slice(1));if(PAGES[key])return infoPage(key);document.title='MySelfPay · Find self-pay MRI and CT';return false}
globalThis.addEventListener?.('hashchange',()=>{if(!routeHash()){if(account&&catalogReady)render();else welcome()}});
const bootReady=(async()=>{try{const r=await api('/me');account=r.member;csrf=r.csrf;await start()}catch(e){if(account)loadFailure(e);else welcome()}})();
bootReady.then(()=>routeHash());

function chatDisabled(){return state.chatBlocked||(state.conversationId?(state.usage[state.conversationId]||0)>=5:Object.keys(state.usage).length>=3)}
function guestLimitExplanation(){
 if(state.chatLimitReason==='hourly')return 'Hourly guest chat limit reached. Try again after the next hour begins. Signing out does not reset this limit.';
 if(state.chatLimitReason==='daily')return 'Daily guest chat capacity reached. Please try again tomorrow (UTC).';
 if(state.conversationId&&(state.usage[state.conversationId]||0)>=5&&Object.keys(state.usage).length<3)return 'This conversation has used its 5 messages. You can start another conversation below.';
 return 'This guest session has used its chat allowance. Search and comparison remain available.';
}
function guestChatControls(){
 const left=Math.max(0,3-Object.keys(state.usage).length);
 const messages=state.conversationId?Math.max(0,5-(state.usage[state.conversationId]||0)):5;
 const prompts=['Knee MRI near Cincinnati under $500','Brain MRI without contrast near Hilo','Knee MRI near Dayton'];
 return `<p role="status">Guest preview: ${left} of 3 conversations left to start · ${messages} messages left in this conversation.</p><div class="actions">${prompts.map(t=>`<button data-starter="${esc(t)}" ${chatDisabled()?'disabled':''}>${esc(t)}</button>`).join('')}</div><button id="newGuestChat" ${left===0||state.chatBlocked?'disabled':''}>Start new conversation</button>${chatDisabled()?'<p role="alert">Guest preview limit reached. Full access is coming with MySelfPay accounts.</p><p>'+esc(guestLimitExplanation())+'</p>':''}<p class="small">Up to 500 characters per message. Search, filters, directory and compare remain available.</p>`;
}







// Compose locally: never transmit form values to the application server.
function appointmentEmail(center){
 const scope=String(center.email_scope||'');
 if(center.appointment_email_approved!==true&&(!/scheduling|appointments?/i.test(scope)||/not (?:intended for |for )?(?:patient |branch |local )?schedul|not intended for prescriptions|billing|financial|business|referral|prescriptions|feedback|advocacy|privacy|media/i.test(scope)))return '';
 const address=String(center.email||'').trim();
 return /^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$/.test(address)&&address.length<=254?address:'';
}
function appointmentDraft(center,values){
 const recipient=appointmentEmail(center);
 if(!recipient)throw new Error('This center has no appointment email. Please contact it directly.');
 const name=String(values.name||'').trim(),phone=String(values.phone||'').trim();
 if(!name||name.length>100||/[\r\n]/.test(name)||!/[0-9]{3}/.test(phone)||phone.length>30)throw new Error('Enter your name and a contact phone number.');
 const date=String(values.date||''),time=String(values.time||''),zone=String(values.zone||'');
 const zones=['Eastern','Central','Mountain','Arizona','Pacific','Alaska','Hawaii'];
 if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||!/^\d{2}:\d{2}$/.test(time)||!zones.includes(zone))throw new Error('Choose a date, time and the center’s time zone.');
 const today=new Date();const localDate=[today.getFullYear(),String(today.getMonth()+1).padStart(2,'0'),String(today.getDate()).padStart(2,'0')].join('-');
 if(date<localDate||!Number.isFinite(Date.parse(date+'T'+time)))throw new Error('Choose a valid date today or later.');
 if(!['MRI','CT','Other imaging','Please contact me'].includes(values.service))throw new Error('Choose a service.');
 const subject=`Appointment request — ${center.name}`;
 const body=`Hello ${center.name},\r\n\r\nI would like to request an imaging appointment.\r\nName: ${name}\r\nPhone: ${phone}\r\nPreferred date: ${date}\r\nPreferred time: ${time} (${zone} time)\r\nService: ${values.service}\r\nLocation: ${center.coverage||center.area||'Please confirm'}\r\n\r\nPlease reply to this email to confirm availability, the location, referral requirements, preparation and total self-pay price. I understand this is a request, not a confirmed booking.\r\n\r\nThank you.\r\n${name}`;
 return {subject,body,uri:`mailto:${encodeURIComponent(recipient)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`};
}
function appointmentForm(center){
 modal(`<h2>Book appointment</h2><p><strong>${esc(center.name)}</strong>${center.test_only?' — TEST ONLY, not a real facility':''}</p><p>Fill in your preferred time. Your email app will open a draft addressed to ${esc(appointmentEmail(center))}. Review it and press Send there. No MySelfPay account is needed.</p><form id="appointmentForm"><label>Your name<input id="appointmentName" autocomplete="name" maxlength="100" required></label><label>Phone<input id="appointmentPhone" type="tel" autocomplete="tel" maxlength="30" required></label><label>Preferred date<input id="appointmentDate" type="date" required></label><label>Preferred time<input id="appointmentTime" type="time" required></label><label>Center’s time zone<select id="appointmentZone" required><option value="">Choose time zone</option>${['Eastern','Central','Mountain','Arizona','Pacific','Alaska','Hawaii'].map(z=>`<option>${z}</option>`).join('')}</select></label><label>Service<select id="appointmentService"><option>Please contact me</option><option>MRI</option><option>CT</option><option>Other imaging</option></select></label><p>Do not include diagnoses, insurance details or medical records. The center must confirm your appointment.</p><button type="submit">Open email app</button><p id="appointmentStatus" role="status"></p><div id="appointmentFallback"></div></form>`);
 $('appointmentForm').onsubmit=event=>{
  event.preventDefault();
  try{
   const draft=appointmentDraft(center,{name:$('appointmentName').value,phone:$('appointmentPhone').value,date:$('appointmentDate').value,time:$('appointmentTime').value,zone:$('appointmentZone').value,service:$('appointmentService').value});
   $('appointmentStatus').textContent='Review the draft in your email app and press Send. MySelfPay cannot confirm whether it was sent. If no app opens, copy the details below into your email.';
   $('appointmentFallback').innerHTML=`<p>To: ${esc(appointmentEmail(center))}</p><p>Subject: ${esc(draft.subject)}</p><label>Email message<textarea rows="10" readonly>${esc(draft.body)}</textarea></label><a href="${esc(draft.uri)}">Open email app again</a>`;
   globalThis.location.href=draft.uri;
  }catch(error){$('appointmentStatus').textContent=error.message;}
 };
}
document.addEventListener('click',event=>{
 const button=event.target.closest?.('[data-appointment]');if(!button)return;
 const center=DIRECTORY.find(e=>e.name===button.dataset.appointment);
 if(center&&appointmentEmail(center))appointmentForm(center);
});
async function openBookingTest(){
 if(!account)await signInGuest();
 const {center}=await api('/booking-test');
 if(!center){modal('<h2>Booking test</h2><p>The test center has not been added to this database yet.</p>');return;}
 appointmentForm(center);
}
