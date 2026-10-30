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
function contactActions(o){const e=o.entry,ph=phoneOf(e),addr=addressOf(e),web=websiteOf(e);if(!ph&&!addr&&!web&&!e.booking_id)return '';return `<div class="card-actions" aria-label="Contact ${esc(e.name)}">${ph?telLink(ph,'call','Call '+ph):''}${web?`<a href="${esc(web)}" target="_blank" rel="noopener noreferrer">Website</a>`:''}${e.booking_id?`<button type="button" data-appointment="${esc(e.booking_id)}" data-booking-offer="${esc(o.id||'')}">Book appointment</button>`:''}${addr?`<a href="https://www.google.com/maps/search/?api=1&amp;query=${esc(encodeURIComponent(String(e.name).split(' — ')[0]+', '+addr))}" target="_blank" rel="noopener noreferrer">Directions</a>`:''}</div>`}
function cardFacts(o){const facts=[`<div class="fact"><strong>Price includes</strong><br>${esc(o.included)}</div>`];if(o.order&&!/^(Review the facility restrictions|Not established in this directory)/i.test(o.order))facts.push(`<div class="fact"><strong>Order requirements</strong><br>${esc(o.order)}</div>`);if(state.budget)facts.push(`<div class="fact"><strong>Budget check</strong><br>${budgetGroup(o)}</div>`);return `<div class="facts">${facts.join('')}</div>`}
function card(o){return `<article class="card">${o.reviewed_alternative?`<div class="notice"><strong>Reviewed alternative · filters differ</strong><p>${esc(o.match_status)}</p><ul>${(o.filter_differences||[]).map(d=>`<li>${esc(d)}</li>`).join('')}</ul></div>`:''}<div class="row between"><span class="badge ${o.type==='fixed'?'':'warn'}">${typeLabel(o)}</span><label class="small"><input style="width:auto" type="checkbox" aria-label="Compare ${esc(o.entry.name)}" data-select="${o.id}" ${state.selected.includes(o.id)?'checked':''}> Compare</label></div><div class="row between" style="margin-top:16px"><div><h3>${esc(o.entry.name)}</h3><div class="muted small">${esc(o.region)} · ${esc(o.entry.entity)}</div><div class="small">${esc(distanceLabel(o))}</div></div><div class="price">${price(o)}</div></div><p class="scope">${esc(o.mod)} · ${esc(o.contrast==='unknown'?'Protocol unconfirmed':(o.contrast==='both'?'Without and with':o.contrast==='without'?'Without':'With')+' contrast')} · ${esc(o.scope)}</p>${cardFacts(o)}${contactActions(o)}<div class="row between"><span class="small muted">Source checked ${o.entry.checked.slice(0,10)} · Reconfirm before arranging care</span><button data-detail="${o.id}">View details</button></div></article>`}
function locationPending(){return !!(state.locationSuggestions?.length||state.locationUnresolved)}
function locationPrompt(){return `<div class="panel" role="status"><h2>${state.locationSuggestions?.length?'Choose your city and state':'Enter a city and state or ZIP code'}</h2><p>${state.locationSuggestions?.length?'More than one location matches your search. Select the correct city beside the location field to find the nearest reviewed offers.':'We could not identify that location. Enter a city with its state, such as Baltimore, MD, or a five-digit ZIP code.'}</p><p>Your city does not need a provider listing in our directory. Once the location is confirmed, we search indexed facilities nationwide and show the nearest options.</p><button id="editLocation" type="button">${state.locationSuggestions?.length?'Choose location':'Update location'}</button></div>`}
function render(){rememberView(state.mode==='agent'?'agent':'search');if(locationPending())state.detailsOpen=true;pageTop('search:'+state.mode);const found=results;$('app').innerHTML=`<div class="row between"><div><div class="eyebrow">SELF-PAY IMAGING</div><h1>Find and compare imaging options</h1><div class="muted">Compare published prices and know what to confirm.</div></div></div><div class="tabs"><button id="classic" class="${state.mode==='classic'?'active':''}">Search & filters</button><button id="agent" class="${state.mode==='agent'?'active':''}">Ask MySelfPay</button></div><div class="row between small"><span>Signed in: ${esc(state.member)}</span><span>${account?.tenant==='guest'?'Private guest preview':'Private search'} · Chat is not saved</span></div>${chips()}<div id="searchNotice" role="status"></div>${state.saveStatus==='failed'?'<p class="notice" role="alert">This search was not saved. Results are still available; try searching again to retry saving.</p>':''}<div class="grid ${state.mode==='agent'?'agent-layout':''}"><div class="stack" style="align-self:start;min-width:0"><aside class="panel"><details ${state.mode==='classic'||state.detailsOpen?'open':''}><summary>Search details</summary><p class="small muted">Choose your location and any optional exam details.</p><form id="searchForm">${searchFields()}<button class="primary" style="width:100%">Find options</button></form></details></aside></div><section class="stack">${state.mode==='agent'?`<div class="panel"><div class="row between"><h3>Ask MySelfPay</h3><span class="badge neutral">Server-guided demo</span></div><p class="small muted">No external AI or speech service is connected. Do not enter real personal or medical information.</p><div class="chat" id="chat">${state.messages.map(m=>`<div class="message ${m.role==='user'?'user':''}">${esc(m.text)}</div>`).join('')||'<div class="message">Hi, I’m MySelfPay. I can help you find imaging listings and understand published self-pay prices. Tell me your exam and location, or try “Find a self-pay knee MRI near Cincinnati under $500.” I will ask about missing procedure details.</div>'}</div>${guestChatControls()}<form id="chatForm" class="row"><label class="sr-only" for="message">Message</label><input id="message" maxlength="500" ${chatDisabled()?'disabled':''} placeholder="Describe your search" style="flex:1;min-width:180px" required><button class="primary" ${chatDisabled()?'disabled':''}>Send</button><button type="button" id="voice" ${chatDisabled()?'disabled':''}>Voice demo</button></form><p class="small" role="status">This conversation is not saved.</p></div>`:''}${!state.searched?initialSearch()+coverageSummary():locationPending()?locationPrompt():`<div class="row between"><h2>${found.length ? `${found.length} reviewed offer${found.length===1?'':'s'}` : (state.nearbyUnpriced?.length ? 'Nearest facilities to contact' : state.programs?.length||state.programEntries?.length ? 'Available programs' : 'Find options for your location')}</h2><select id="sort" ${found.some(o=>Number.isFinite(o.distance_miles))?'disabled title="Location results are sorted by distance"':''} aria-label="Sort results" style="width:auto"><option value="distance" ${state.sort==='distance'?'selected':''}>Nearest first</option><option value="scope" ${state.sort==='scope'?'selected':''}>Source order</option><option value="price" ${state.sort==='price'?'selected':''}>Fixed prices: low to high</option></select></div><p class="small">Select up to 3 options to compare. Confirm the same exam and contrast before comparing prices.</p>${groupedCards(found)||`<div class="panel"><h3>${state.noExamPrice?'No listed facility publishes a price for this exam':state.unlocatedOfferCount?'Distance results are incomplete':'No reviewed match for this search'}</h3>${state.unlocatedOfferCount?'<p>Some matching listings do not yet have verified facility coordinates. This does not mean no services are available. Browse National to review those listings while location data is being updated.</p>':''}<p>We have not changed your procedure. Try National to browse researched examples or view the directory for quote leads. “With contrast” and “without and with contrast” remain separate.</p><button id="widen">Browse National</button><button id="leads">View directory leads</button></div>`}`}${state.selected.length?`<div class="sticky row between"><span>${state.selected.length} option${state.selected.length===1?'':'s'} selected</span><div class="row"><button id="compare">Compare selected</button><button id="clearCompare" type="button" aria-label="Close comparison bar and clear all selections" title="Clear comparison selections">×</button></div></div>`:''}</section></div>`;bind()}
function readFields(){['mod','body','contrast','location','type'].forEach(k=>state[k]=$(k).value);state.budget=Number($('budget').value)||0;state.scope=$('radius').value==='state'?'state':'radius';state.radius=Number($('radius').value)||50}
function modal(html){html=html.replace('<h2>','<h2 id="dialogTitle">');$('modal').setAttribute('aria-labelledby','dialogTitle');$('modal').innerHTML=`<div class="modal-header row between"><span class="eyebrow">MYSELFPAY</span><button id="closeModal" aria-label="Close dialog">Close</button></div><div class="modal-body" id="modalBody">${html}</div>`;$('modal').showModal();$('modalBody').scrollTop=0;$('modalBody').scrollLeft=0;$('closeModal').onclick=closeDialog;$('modal').oncancel=closeDialog}
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
function detail(id){const o=offers.find(x=>x.id===id);if(!o){render();toast('This listing is no longer available. Please search again.');return;}rememberView('facility',id);pageTop('detail:'+id);const where=addressOf(o.entry)||o.entry.coverage;const restrictions=restrictionsOf(o);const more=String(o.entry.additional||'').split(/\s+/).filter(x=>x.startsWith('https://'));$('app').innerHTML=`<button id="back">Back to results</button><div class="detailgrid"><section class="panel"><span class="badge ${o.type==='fixed'?'':'warn'}">${typeLabel(o)}</span><h1>${esc(o.entry.name)}</h1><p class="muted">${esc(where)}</p><div class="price">${price(o)}</div><p>${esc(o.mod)} · ${esc(contrastLabel(o.contrast))} · ${esc(o.scope)}</p><div class="notice">Confirm the exact exam, eligibility and all-in price with the facility. MySelfPay does not guarantee price or availability.</div><h2>What the price includes</h2><p>${esc(o.included)}</p>${restrictions.length?`<h2>Restrictions</h2><ul>${restrictions.map(t=>`<li>${esc(t)}</li>`).join('')}</ul>`:''}<h2>Questions to ask the facility</h2><ul class="checklist">${questions(o).map(q=>`<li>${esc(q)}</li>`).join('')}</ul></section><aside class="panel"><h2>Contact this facility</h2><p>${esc(where)}</p>${contactActions(o)||'<p class="small">Contact details are not available in this listing.</p>'}${more.map((url,i)=>`<p><a href="${esc(url)}" target="_blank" rel="noopener noreferrer">More from this facility${more.length>1?' ('+(i+1)+')':''}</a></p>`).join('')}<p class="small muted">Source checked ${esc(checkedDate(o.entry.checked))}.</p><button id="request" class="primary">Ask for a self-pay price</button>${facilityMap(o.entry)}</aside></div>`;$('back').onclick=render;$('request').onclick=()=>request(o);bindFacilityMap(o.entry)}
function compare(){rememberView('compare');const chosen=state.selected.map(id=>offers.find(o=>o.id===id)).filter(Boolean);const rows=[['Published price',o=>price(o)],['Price status',typeLabel],['Exam',o=>o.mod+' · '+contrastLabel(o.contrast)],['Price scope',o=>o.scope],['Included',o=>o.included],['Requirements',o=>o.order],['Budget',budgetGroup],['Source checked',o=>o.entry.checked.slice(0,10)]];modal(`<h2>Compare selected options</h2><p class="notice">Confirm the same exam and contrast before comparing totals. Published prices are not current quotes.</p><div class="comparison-scroll"><table class="comparison-table"><thead><tr><th scope="col">Details</th>${chosen.map(o=>`<th scope="col">${esc(o.entry.name)}</th>`).join('')}</tr></thead><tbody>${rows.map(([label,value])=>`<tr><th scope="row">${label}</th>${chosen.map(o=>`<td>${esc(value(o))}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`)}
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
function initialSearch(){const q=state.location.trim().toLowerCase();const leads=q&&!/^\d/.test(q)?DIRECTORY.filter(d=>d.area.toLowerCase().includes(q)||d.states.toLowerCase()===q):[];return `<div class="panel"><h2>${state.location?'Browse imaging centers in your state':'Where would you like to search?'}</h2><p>${state.mod&&state.body.trim()?'Your exam details are ready. Enter a city or state to find options.':'Select your state to browse imaging centers. All other filters are optional.'}</p><p class="small" id="catalogStatus" role="status">${esc(catalogStatus())}</p><div class="actions"><button id="sampleSearch">Try sample: knee MRI in Cincinnati</button><button id="browseDirectory">Browse all directory entries</button></div><p class="small">The sample is a demonstration search, not a recommendation for a medical test.</p><p class="small">Search by city or ZIP for approximate straight-line distances to imported facility locations.</p>${leads.length?'<h3>Directory locations in your search area</h3><p class="small">Entries may cover multiple locations. Service availability and exact addresses require confirmation.</p>'+leads.map(d=>`<div class="lead"><strong>${esc(d.name)}</strong><p>${esc(d.area)}</p><a href="${esc(d.source)}" target="_blank" rel="noopener noreferrer">Check provider locations</a></div>`).join(''):''}</div>`}
function groupedCards(found){return (state.resultsHeading?`<h2>${esc(state.resultsHeading)}</h2>`:'')+found.map(card).join('')+((state.programs?.length||state.programEntries?.length)?`<h2>${esc(state.programHeading)}</h2>`+state.programs.map(card).join('')+(state.programEntries||[]).map(e=>`<article class="card"><h3>${esc(e.name)}</h3><p>Confirm service availability and request a quote.</p>${contactActions({entry:e})||`<a href="${esc(e.source)}" target="_blank" rel="noopener noreferrer">Program website</a>`}</article>`).join(''):'')+(state.nearbyUnpriced?.length?'<h2>Facilities to contact for a quote</h2><p>Confirm the ordered exam, eligibility and total directly with the facility.</p>'+state.nearbyUnpriced.map(e=>`<article class="card"><h3>${esc(e.name)}</h3><p>${esc(distanceLabel(e))}</p><strong>Call for a self-pay price</strong>${contactActions({entry:e})}</article>`).join(''):'')}

function request(o){const ph=phoneOf(o.entry),exam=[state.body,o.mod].filter(Boolean).join(' ')||o.mod;modal(`<h2>Ask for a self-pay price</h2><p>${esc(o.entry.name)}</p>${ph?`<p class="card-actions">${telLink(ph,'call','Call '+ph)}</p>`:'<p>Use the facility website to reach them.</p>'}<p>When you call, say you are paying yourself and ask for the all-in price for your ${esc(exam)}${state.contrast&&state.contrast!=='unknown'?` (${esc(contrastLabel(state.contrast).toLowerCase())})`:''}.</p><h3>Questions to ask</h3><ul class="checklist">${questions(o).map(q=>`<li>${esc(q)}</li>`).join('')}</ul><p class="small muted">Published reference: ${price(o)} · ${typeLabel(o)}</p>`)}
function directory(){
  rememberView('directory');
  modal(`<h2>Research directory · ${DIRECTORY.length} entries</h2><p>Entries may represent facilities, branches or programs. ${offers.length} reviewed price offers are mapped for search.</p>${control('dirSearch','Filter directory by name, area or state','<input id="dirSearch" placeholder="e.g. Tellica, OH, Vermont">')}<p id="dirCount" role="status"></p><div id="dirRows"></div><div class="actions"><button id="dirPrev" type="button">Previous</button><button id="dirNext" type="button">Next</button></div>`);
  const indexed=DIRECTORY.map(d=>({d,text:[d.name,d.area,d.states].join(' ').toLowerCase()}));
  $('dirSearch').value=state.directoryQuery||'';
  let page=state.directoryPage||0;
  function show(){
    const q=$('dirSearch').value.trim().toLowerCase();
    const matches=indexed.filter(item=>item.text.includes(q));
    const pages=Math.max(1,Math.ceil(matches.length/50));
    page=Math.min(page,pages-1);
    state.directoryQuery=$('dirSearch').value;state.directoryPage=page;rememberView('directory','',true);
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
const defaults=()=>({mod:'',body:'',contrast:'unknown',location:'',budget:0,type:'all',mode:'classic',selected:[],private:true,messages:[],conversationId:null,usage:{},chatBlocked:false,chatLimitReason:null,member:'',savedId:null,sort:'distance',scope:'state',radius:50,programs:[],nearbyUnpriced:[],resultsHeading:'',directoryQuery:'',directoryPage:0});
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
let catalogTask=null,catalogError='';
function catalogStatus(){return catalogReady?`Directory loaded: ${DIRECTORY.length} researched entries · ${offers.length} mapped price offers. Entries can represent facilities, branches or programs; coverage is limited.`:catalogError?'The full directory is temporarily unavailable. You can still search; choose Browse all directory entries to retry.':'The full directory is loading. You can search now using your city, state or ZIP.'}
function updateCatalogStatus(){const target=$('catalogStatus');if(target)target.textContent=catalogStatus()}
function loadCatalog(){
  if(catalogTask?.epoch===epoch)return catalogTask.promise;
  const started=epoch;catalogError='';
  const task={epoch:started};
  task.promise=(async()=>{
    try{
      const data=await api('/catalog');
      if(started!==epoch)return;
      if(!Array.isArray(data.entries)||!Array.isArray(data.offers)||!data.version)throw new Error('Provider directory is not published yet. Contact the review administrator.');
      DIRECTORY=data.entries;
      // Search responses can arrive first. Preserve their offers and version.
      const byId=new Map(data.offers.map(o=>[o.id,o]));
      [...results,...(state.programs||[])].forEach(o=>byId.set(o.id,o));offers=[...byId.values()];
      if(Array.isArray(data.locations))cityLabels=data.locations;
      if(!currentVersion)currentVersion=data.version;
      catalogReady=true;
    }catch(error){if(started===epoch)catalogError=error.message;throw error}
    finally{if(catalogTask===task)catalogTask=null;if(started===epoch)updateCatalogStatus()}
  })();
  catalogTask=task;return task.promise;
}
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
  document.querySelectorAll('[data-detail]').forEach(b=>b.onclick=()=>detail(b.dataset.detail));
  if($('compare'))$('compare').onclick=compare;
  if($('clearCompare'))$('clearCompare').onclick=safe(async()=>{state.selected=[];render();await save()});
  if($('leads'))$('leads').onclick=safe(async()=>{if(!catalogReady)await loadCatalog();directory()});
  if($('voice'))$('voice').onclick=voice;
  const showDirty=()=>{rememberView(state.mode==='agent'?'agent':'search','',true);if($('searchNotice'))$('searchNotice').textContent=state.dirty?'Search changed—click Find options to update results. Displayed results belong to your previous search.':(/^Distances are approximate straight-line miles\b/.test(state.locationNotice||'')?'':(state.locationNotice||''));document.querySelectorAll('[data-select],[data-detail],#compare').forEach(b=>b.disabled=!!state.dirty)};
  showDirty();
  for(const id of ['mod','body','contrast','location','budget','type','radius'])$(id).oninput=()=>{readFields();if(state.searched)state.dirty=true;showDirty()};
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
  navigationSerial++;
  await saveQueue.catch(()=>{});await api('/logout',{});epoch++;account=null;csrf='';
  state=defaults();results=[];offers=[];DIRECTORY=[];catalogReady=false;pendingEntry=null;
  $('modal').close();welcome();
}
let guestBusy=false;
async function signInGuest(kind='search'){
  if(guestBusy)return;guestBusy=true;$('profile').disabled=true;
  $('app').innerHTML='<section class="panel" role="status" aria-live="polite"><h1>Starting your guest session…</h1><p>Loading imaging options. Please wait.</p></section>';
  try{const r=await api('/guest',{});account=r.member;csrf=r.csrf;
    try{await start()}catch(e){loadFailure(e);$('retrySession').onclick=safe(async()=>{await start();await enterJourney(kind)});return}
    await enterJourney(kind);
  }catch(e){welcome();throw e
  }finally{guestBusy=false;$('profile').disabled=false}
}
let pendingEntry=null;
function updateNavigation(){$('history').hidden=true;$('directory').hidden=!account;$('profile').textContent=account?'Sign out':'Sign in as guest';$('accountLogin').hidden=!!account&&account.tenant!=='guest'}
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
function welcome(){rememberView('home');updateNavigation();pageTop('welcome');
  $('app').innerHTML=`<section class="welcome-intro"><div><div class="eyebrow">WELCOME TO MYSELFPAY</div><h1>Find self-pay MRI and CT near you.</h1><p class="welcome-lead">Compare published prices, see what’s included, and call the facility in one tap.</p><p>You can explore self-pay options whether you have health coverage or are paying entirely yourself. Your facility confirms the exact service, eligibility and final price.</p><div class="actions"><button class="primary" id="welcomeBegin">${'Find imaging options'}</button>${account?'':'<button id="welcomeAccount">Start as a guest</button>'}</div></div><aside class="welcome-account"><h2>Start as a guest.</h2><p>Search and compare prices with no account. Chat with MySelfPay for up to 3 conversations of 5 messages each.</p><p class="small">Your session lasts up to 8 hours. Enter just your exam and city. We keep only usage counts.</p></aside></section><section class="welcome-steps" aria-label="How MySelfPay works"><div><span class="step-number">1</span><h3>Tell us what you need</h3><p>Choose an imaging service and location, or describe your search.</p></div><div><span class="step-number">2</span><h3>Compare the details</h3><p>Review prices, included fees and restrictions for relevant options.</p></div><div><span class="step-number">3</span><h3>Confirm with the facility</h3><p>Use provider links and a question checklist to confirm the exact exam and total.</p></div></section><section class="welcome-paths"><h2>How would you like to begin?</h2><div class="welcome-choices"><button class="journey-card" data-journey="search"><strong>Search for a service</strong><span>Choose your imaging exam and location.</span></button><button class="journey-card" data-journey="agent"><strong>Ask MySelfPay</strong><span>Describe your search in a conversation.</span></button></div></section>${coverageSummary(true)}`;
  void loadPublicCoverage();
  if($('continueSearch'))$('continueSearch').onclick=safe(history);
  $('welcomeBegin').onclick=safe(()=>enterJourney('search'));
  if($('welcomeAccount'))$('welcomeAccount').onclick=safe(()=>signInGuest());
  document.querySelectorAll('[data-journey]').forEach(b=>b.onclick=safe(()=>enterJourney(b.dataset.journey)));
}
async function enterJourney(kind){
  if(!account){await signInGuest(kind);return}
  state.mode=kind==='agent'?'agent':'classic';render();
}
function loginScreen(){welcome()}
async function start(){updateNavigation();epoch++;results=[];state=defaults();state.member=`${account.tenant} / ${account.name}`;catalogReady=false;catalogError='';DIRECTORY=[];offers=[];currentVersion='';void loadCatalog().catch(()=>{});state.usage=(await api('/guest-usage')).usage||{};state.conversationId=Object.keys(state.usage).at(-1)||null;state.location='';welcome()}
$('brandHome').onclick=e=>{if(e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;e.preventDefault();pendingEntry=null;welcome()};
$('history').onclick=safe(async()=>{if(!account)return loginScreen();await history()});
$('directory').onclick=safe(async()=>{if(!account)return loginScreen();await loadCatalog();directory()});
$('profile').onclick=safe(()=>account?signOut():signInGuest());
$('accountLogin').onclick=()=>{location.hash='login'};

const PARTNER_EMAIL='partners@onesmarter.com';
const PAGES={
 'for-imaging-centers':{title:'For imaging centers',body:()=>`<p class="welcome-lead">Self-pay patients compare prices before they call. MySelfPay shows them yours.</p><h2>What patients see today</h2><p>Each of your centers with its distance, phone, website and directions, plus your published self-pay price, or “Price on request.”</p><h2>Show your price</h2><p>Send us your self-pay prices for your most common exams, what each includes, and how long it holds. We publish them, and patients see your number instead of a phone call.</p><h2>Coming next</h2><p>Open times and booking requests that your staff or scheduling system confirms. Patients pay on your own payment page.</p><p><strong>Free during the pilot.</strong></p><div class="actions"><a class="button primary" href="mailto:${PARTNER_EMAIL}?subject=${encodeURIComponent('MySelfPay for our imaging center')}">Talk to us</a><a class="button" href="mailto:${PARTNER_EMAIL}?subject=${encodeURIComponent('Correct our MySelfPay listing')}">Correct your listing</a></div>`},
 'contact':{title:'Contact',body:()=>`<p>MySelfPay is built by One Smarter, Inc. in Dayton, Ohio.</p><p>Questions, corrections or partnership requests: <a href="mailto:${PARTNER_EMAIL}">${PARTNER_EMAIL}</a>.</p><p>Imaging centers: see <a href="#for-imaging-centers">For imaging centers</a>.</p>`},
 'privacy':{title:'Privacy',body:()=>`<p>MySelfPay works without an account. When you search, we use the exam and city you type to find facilities near you. That search location is used for your search only and is not saved.</p><p>Chat messages stay on your page and clear when you refresh it.</p><p>To run guest limits, we store a session cookie for up to 8 hours and counts of how many chats you’ve started.</p><p>If you save an appointment preview, we store your first name, phone and request details. Email delivery is disabled. Do not enter medical records or payment details.</p><p>When you call or visit a facility, its own privacy practices apply.</p><p>Questions: <a href="mailto:${PARTNER_EMAIL}">${PARTNER_EMAIL}</a>.</p>`},
 'terms':{title:'Terms',body:()=>`<p>MySelfPay lists self-pay prices that facilities publish. Prices, eligibility and availability are set by each facility and can change. Confirm them with the facility before your exam.</p><p>MySelfPay doesn’t provide medical advice. Your clinician decides which exam you need.</p><p>Facility names and prices belong to their owners and are shown for comparison.</p><p>Use of the site is at your own discretion.</p>`},
};
function infoPage(key){const page=PAGES[key];if(!page)return false;updateNavigation();pageTop('page:'+key);document.title=`${page.title} · MySelfPay`;$('app').innerHTML=`<article class="panel info-page"><h1>${esc(page.title)}</h1>${page.body()}<p class="actions"><a href="/">Back to MySelfPay</a></p></article>`;return true}
function routeHash(){if(/^#(?:search|agent|facility|directory|compare)(?:\/|$)/.test(globalThis.location?.hash||'')){void restoreNavigation();return true;}if(['#login','#signup'].includes(globalThis.location?.hash)){accountPage(location.hash==='#signup');return true;}if(bookingRoute())return true;if(globalThis.location?.hash==='#booking-test'){openBookingTest().catch(e=>toast(e.message));return true;}const legacy=String(globalThis.location?.hash||'').slice(1);const destinations={privacy:'/privacy-terms',terms:'/privacy-terms',contact:'/contact','for-imaging-centers':'/for-imaging-centers'};if(destinations[legacy]){globalThis.location.replace(destinations[legacy]);return true;}const key=decodeURIComponent(String(globalThis.location?.hash||'').slice(1));if(PAGES[key])return infoPage(key);document.title='MySelfPay · Find self-pay MRI and CT';return false}
globalThis.addEventListener?.('hashchange',()=>{if(navigationReady)void restoreNavigation()});
globalThis.addEventListener?.('popstate',()=>{if(navigationReady)void restoreNavigation()});
// Only allowlisted search preferences enter browser history, never messages,
// passwords, verification codes, appointment forms or capability tokens.
const NAV_FIELDS=['mod','body','contrast','location','budget','type','sort','scope','radius','selected','searched','dirty','directoryQuery','directoryPage'];
let navigationReady=false,navigationRestoring=false,navigationSerial=0;
function navigationSnapshot(view,id=''){
 const query={};for(const key of NAV_FIELDS)query[key]=state[key];
 return {selfpay:1,owner:account?.id||null,expires:Date.now()+8*3600000,view,id,query};
}
function rememberView(view,id='',replace=false){
 if(!navigationReady||navigationRestoring||!globalThis.history?.pushState)return;
 const snapshot=navigationSnapshot(view,id),prior=globalThis.history.state;
 const hash=view==='home'?'':`#${view}${id?'/'+encodeURIComponent(id):''}`;
 if(prior?.selfpay&&prior.owner===snapshot.owner&&prior.view===view&&prior.id===id&&JSON.stringify(prior.query)===JSON.stringify(snapshot.query))replace=true;
 try{globalThis.history[replace?'replaceState':'pushState'](snapshot,'',globalThis.location.pathname+hash)}catch{/* Browsing still works if history storage is unavailable. */}
}
function closeDialog(event){
 event?.preventDefault?.();$('modal').close();
 if(['#compare','#directory'].includes(globalThis.location?.hash))render();
}
async function restoreNavigation(){
 const serial=++navigationSerial;navigationRestoring=true;epoch++;
 const hash=globalThis.location?.hash||'',snapshot=globalThis.history?.state;
 $('modal').close();
 try{
  if(['#login','#signup'].includes(hash)){accountPage(hash==='#signup');return;}
  if(/^#(?:request|clinic)\//.test(hash)||hash==='#booking-test'){routeHash();return;}
  bookingStopPolling();
  const match=/^#(search|agent|facility|directory|compare)(?:\/(.*))?$/.exec(hash);
  if(!match){if(hash&&routeHash())return;welcome();return;}
  if(!account){welcome();return;}
  $('app').innerHTML='<section class="panel" role="status">Restoring your page…</section>';
  const valid=snapshot?.selfpay===1&&snapshot.owner===account.id&&snapshot.expires>Date.now();
  if(valid&&snapshot.query&&typeof snapshot.query==='object'){
   const defaultsQuery=defaults();
   for(const key of NAV_FIELDS){const value=snapshot.query[key];if(key==='selected')state.selected=Array.isArray(value)?value.filter(x=>typeof x==='string').slice(0,3):[];
    else if(typeof value===typeof defaultsQuery[key]||(['searched','dirty'].includes(key)&&typeof value==='boolean'))state[key]=value;}
  }
  state.mode=match[1]==='agent'?'agent':'classic';
  // Never show old results under edited, unsubmitted filters after refresh.
  if(state.dirty){state.searched=false;results=[];}
  if(state.searched&&state.location){await loadResults();if(serial!==navigationSerial)return;}
  if(['facility','directory','compare'].includes(match[1])){await loadCatalog();if(serial!==navigationSerial)return;}
  render();
  if(match[1]==='facility')detail(decodeURIComponent(match[2]||''));
  else if(match[1]==='directory')directory();
  else if(match[1]==='compare')compare();
 }catch(error){if(serial===navigationSerial){render();toast(error.message||'Unable to restore this page. Please search again.');}}
 finally{if(serial===navigationSerial)navigationRestoring=false;}
}
const bootReady=(async()=>{try{const r=await api('/me');account=r.member;csrf=r.csrf;await start()}catch(e){if(account)loadFailure(e);else welcome()}})();
bootReady.then(()=>{navigationReady=true;return restoreNavigation()});

function chatDisabled(){if(account?.tenant!=='guest')return false;return state.chatBlocked||(state.conversationId?(state.usage[state.conversationId]||0)>=5:Object.keys(state.usage).length>=3)}
function guestLimitExplanation(){
 if(state.chatLimitReason==='hourly')return 'Hourly guest chat limit reached. Try again after the next hour begins. Signing out does not reset this limit.';
 if(state.chatLimitReason==='daily')return 'Daily guest chat capacity reached. Please try again tomorrow (UTC).';
 if(state.conversationId&&(state.usage[state.conversationId]||0)>=5&&Object.keys(state.usage).length<3)return 'This conversation has used its 5 messages. You can start another conversation below.';
 return 'This guest session has used its chat allowance. Search and comparison remain available.';
}
function guestChatControls(){
 if(account?.tenant!=='guest')return '<p class="small">Signed in to your account. This conversation stays private and is not saved.</p>';
 const left=Math.max(0,3-Object.keys(state.usage).length);
 const messages=state.conversationId?Math.max(0,5-(state.usage[state.conversationId]||0)):5;
 const prompts=['Knee MRI near Cincinnati under $500','Brain MRI without contrast near Hilo','Knee MRI near Dayton'];
 return `<p role="status">Guest preview: ${left} of 3 conversations left to start · ${messages} messages left in this conversation.</p><div class="actions">${prompts.map(t=>`<button data-starter="${esc(t)}" ${chatDisabled()?'disabled':''}>${esc(t)}</button>`).join('')}</div><button id="newGuestChat" ${left===0||state.chatBlocked?'disabled':''}>Start new conversation</button>${chatDisabled()?'<p role="alert">Guest preview limit reached. Log in using the navigation to continue with an account.</p><p>'+esc(guestLimitExplanation())+'</p>':''}<p class="small">Up to 500 characters per message. Search, filters, directory and compare remain available.</p>`;
}

// Booking details live only in this page until an explicit, consented submission.
const BOOKING_ZONES={'America/New_York':'Eastern','America/Chicago':'Central','America/Denver':'Mountain','America/Phoenix':'Arizona','America/Los_Angeles':'Pacific','America/Anchorage':'Alaska','Pacific/Honolulu':'Hawaii'};
const BOOKING_STATUS={requested:'Request sent',voicemail:'Clinic left a voicemail',scheduled:'Scheduled by clinic',unable:'Clinic cannot accommodate',expired:'Request expired'};
let bookingTimer=null;
function bookingStopPolling(){clearInterval(bookingTimer);bookingTimer=null;}
async function bookingApi(action,data){
 const response=await fetch('/api/booking/'+action,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf||''},body:JSON.stringify(data)});
 const value=await response.json();if(!response.ok)throw new Error(value.error||'Unable to complete this request. Please retry.');return value;
}
function slotLabel(s){return new Date(s.date+'T12:00:00').toLocaleDateString(undefined,{weekday:'short',month:'short',day:'numeric'})+' · '+(s.period==='morning'?'Morning (8 am–12 pm)':'Afternoon (12–5 pm)');}
function bookingSummary(b){return `<dl class="booking-summary"><dt>Clinic</dt><dd>${esc(b.clinic_name)}</dd><dt>Location</dt><dd>${esc(b.location||'Confirm with clinic')}</dd><dt>Exam</dt><dd>${esc([b.service,b.exam].filter(Boolean).join(' · '))} · ${esc(contrastLabel(b.contrast))}</dd><dt>Preferred times</dt><dd>${b.slots.map(s=>esc(slotLabel(s))).join('<br>')}<br>${esc(BOOKING_ZONES[b.timezone])} time</dd><dt>Price</dt><dd>${esc(b.price_text||'Clinic will confirm the exact total.')}</dd></dl>`;}
async function appointmentForm(center,offerId=''){
 bookingStopPolling();modal('<h2>Book appointment</h2><p role="status">Loading request details…</p>');
 try{
  const options=await bookingApi('options',{clinic_id:center.booking_id,offer_id:offerId});
  const draft={clinic_id:center.booking_id,offer_id:offerId,price_text:options.price_text,clinic_name:options.name,location:options.location,slots:[],timezone:'',service:state.mod||'Please contact me',exam:state.body||'',contrast:state.contrast||'unknown',first_name:'',phone:'',email:'',consent:false,idempotency_key:crypto.randomUUID()};
  bookingSlots(draft,options);
 }catch(error){$('modalBody').innerHTML=`<h2>Request unavailable</h2><p role="alert">${esc(error.message)}</p><p>Please close this dialog and try again.</p>`;}
}
function bookingSlots(draft,options){
 modal(`<h2>Request a time</h2><p class="eyebrow">STEP 1 OF 2</p><h3>${esc(draft.clinic_name)}</h3><p>Choose up to 3 preferred times. These are preferences, not available appointments.</p><p class="booking-notice">Testing mode: the clinic will not be emailed. Verification codes are sent to your personal email. Use sample patient details and an inbox you control.</p><form id="bookingSlots"><label>Clinic’s time zone<select id="bookingZone" required><option value="">Choose the clinic’s time zone</option>${Object.entries(BOOKING_ZONES).map(([v,t])=>`<option value="${v}" ${draft.timezone===v?'selected':''}>${t}</option>`).join('')}</select></label><label>Imaging service<select id="bookingService">${['Please contact me','MRI','CT','Other imaging'].map(v=>`<option ${v===draft.service?'selected':''}>${v}</option>`).join('')}</select></label><label>Body part / exam (optional)<input id="bookingExam" maxlength="100" value="${esc(draft.exam)}" placeholder="e.g. Knee"></label><label>Contrast<select id="bookingContrast">${[['unknown','Not sure'],['without','Without contrast'],['with','With contrast'],['both','Without and with contrast']].map(([v,t])=>`<option value="${v}" ${draft.contrast===v?'selected':''}>${t}</option>`).join('')}</select></label><fieldset class="booking-time-picker"><legend>Preferred times</legend><label>Choose a date<input type="date" id="bookingDate"></label><div class="booking-slot-grid"><button type="button" data-add-slot="morning">Add morning · 8 am–12 pm</button><button type="button" data-add-slot="afternoon">Add afternoon · 12–5 pm</button></div><div id="bookingSelected"></div></fieldset><p id="bookingError" role="alert"></p><button type="submit" class="primary">Continue</button></form>`);
 const draw=()=>{
  $('bookingSelected').innerHTML=`<p role="status">${draft.slots.length} of 3 times selected</p>`+draft.slots.map((s,i)=>`<div class="booking-slot"><span>${esc(slotLabel(s))}</span><button type="button" data-remove-slot="${i}" aria-label="Remove ${esc(slotLabel(s))}">Remove</button></div>`).join('');
  document.querySelectorAll('[data-remove-slot]').forEach(b=>b.onclick=()=>{draft.slots.splice(Number(b.dataset.removeSlot),1);draw();});
 };
 const dateBounds=()=>{
  const zone=$('bookingZone').value;
  if(zone){const d=options.today[zone];$('bookingDate').min=d;const max=new Date(d+'T12:00:00Z');max.setUTCDate(max.getUTCDate()+90);$('bookingDate').max=max.toISOString().slice(0,10);}
 };
 $('bookingZone').onchange=dateBounds;dateBounds();draw();
 document.querySelectorAll('[data-add-slot]').forEach(button=>button.onclick=()=>{
  $('bookingError').textContent='';const date=$('bookingDate').value;
  if(!$('bookingZone').value||!date||!$('bookingDate').checkValidity()){$('bookingError').textContent='Choose the clinic’s time zone and a date within the next 90 days.';return;}
  const slot={date,period:button.dataset.addSlot};
  if(draft.slots.some(s=>s.date===date&&s.period===slot.period)){$('bookingError').textContent='That time is already selected.';return;}
  if(draft.slots.length===3){$('bookingError').textContent='Choose at most 3 times. Remove a time to select another.';return;}
  draft.slots.push(slot);draw();
 });
 $('bookingSlots').onsubmit=event=>{
  event.preventDefault();if(!draft.slots.length){$('bookingError').textContent='Select at least one preferred time.';return;}
  if(draft.service!==$('bookingService').value||draft.contrast!==$('bookingContrast').value||draft.exam!==$('bookingExam').value){draft.offer_id='';draft.price_text='Clinic will confirm the exact total for the selected exam.';}Object.assign(draft,{timezone:$('bookingZone').value,service:$('bookingService').value,exam:$('bookingExam').value,contrast:$('bookingContrast').value});bookingContact(draft,options);
 };
}
function bookingContact(draft,options){
 modal(`<h2>Confirm your request</h2><p class="eyebrow">STEP 2 OF 2</p>${bookingSummary(draft)}<p class="booking-notice">Preview only. No clinic will receive this request.</p><form id="bookingContact"><h3>How should the clinic reach you?</h3><label>First name<input id="bookingName" autocomplete="given-name" maxlength="80" value="${esc(draft.first_name)}" required></label><label>Mobile number<input id="bookingPhone" type="tel" autocomplete="tel" maxlength="30" value="${esc(draft.phone)}" required></label><fieldset class="booking-time-picker"><legend>Verify your personal email</legend><label>Email address<input id="bookingEmail" type="email" autocomplete="email" maxlength="254" value="${esc(draft.email)}" required></label><button type="button" id="patientCodeSend">Send verification code</button><p id="patientEmailStatus" role="status">${draft.verification_token?'Email verified. You can submit your request.':''}</p><label>Six-digit email code<input id="patientEmailCode" inputmode="numeric" autocomplete="one-time-code" maxlength="6" pattern="[0-9]{6}"></label><button type="button" id="patientCodeVerify">Verify email</button></fieldset><label class="booking-consent"><input id="bookingConsent" type="checkbox" ${draft.consent?'checked':''} required><span>I agree that ${esc(draft.clinic_name)} may call or text me about this request when delivery is enabled. I understand this preview will not contact the clinic.</span></label><p class="small">We store your email verification and request securely. Do not enter medical records, diagnoses, insurance details or real patient information. Requests are deleted 30 days after closing. <a href="/privacy-terms" target="_blank" rel="noopener">Privacy details</a></p><div class="actions"><button type="button" id="bookingBack">Back</button><button type="submit" id="bookingSubmit" class="primary" ${draft.verification_token?'':'disabled'}>Send request</button></div><p id="bookingError" role="alert"></p></form>`);
 const save=()=>Object.assign(draft,{first_name:$('bookingName').value,phone:$('bookingPhone').value,email:$('bookingEmail').value,consent:$('bookingConsent').checked});
 $('bookingEmail').oninput=()=>{draft.email=$('bookingEmail').value;delete draft.verification_token;delete draft.verification_id;$('bookingSubmit').disabled=true;$('patientEmailStatus').textContent='Verify this email before submitting.';};
 $('patientCodeSend').onclick=async()=>{
  if(!$('bookingEmail').reportValidity())return;
  const email=$('bookingEmail').value;$('patientCodeSend').disabled=true;$('bookingEmail').disabled=true;$('bookingBack').disabled=true;$('patientEmailStatus').textContent='Sending verification code…';
  delete draft.verification_token;$('bookingSubmit').disabled=true;
  try{const result=await bookingApi('email-code',{email});draft.email=email;draft.verification_id=result.verification_id;$('patientEmailStatus').textContent='Code sent. Check your inbox and spam folder. It expires in 10 minutes.';setTimeout(()=>{if($('patientCodeSend'))$('patientCodeSend').disabled=false;},60000);}
  catch(error){$('patientEmailStatus').textContent=error.message;$('patientCodeSend').disabled=false;}
  finally{if($('bookingEmail'))$('bookingEmail').disabled=false;if($('bookingBack'))$('bookingBack').disabled=false;}
 };
 $('patientCodeVerify').onclick=async()=>{
  if(!draft.verification_id){$('patientEmailStatus').textContent='Request a code first.';return;}
  const code=$('patientEmailCode').value;if(!/^[0-9]{6}$/.test(code)){$('patientEmailStatus').textContent='Enter the six-digit code from your email.';return;}
  $('patientCodeVerify').disabled=true;$('bookingEmail').disabled=true;$('bookingBack').disabled=true;
  try{const result=await bookingApi('email-verify',{verification_id:draft.verification_id,code});draft.verification_token=result.verification_token;$('patientEmailStatus').textContent='Email verified. Submit your request within 15 minutes.';$('bookingSubmit').disabled=false;$('patientEmailCode').value='';}
  catch(error){$('patientEmailStatus').textContent=error.message;}
  finally{if($('patientCodeVerify'))$('patientCodeVerify').disabled=false;if($('bookingEmail'))$('bookingEmail').disabled=false;if($('bookingBack'))$('bookingBack').disabled=false;}
 };
 $('bookingBack').onclick=()=>{save();bookingSlots(draft,options);};
 $('bookingContact').onsubmit=async event=>{
  event.preventDefault();save();if(!draft.verification_token){$('bookingError').textContent='Verify your personal email first.';return;}$('bookingSubmit').disabled=true;$('bookingBack').disabled=true;$('bookingError').textContent='Saving request…';
  try{const result=await bookingApi('create',draft);$('modal').close();toast('No email sent to clinic (testing mode)');location.hash=`request/${result.id}/${result.tracking_token}`;}
  catch(error){$('bookingError').textContent=error.message;$('bookingSubmit').disabled=false;$('bookingBack').disabled=false;}
 };
}
function bookingRoute(){
 const match=String(globalThis.location?.hash||'').match(/^#(request|clinic)\/(MSP-[A-F0-9]{16})\/([A-Za-z0-9_-]{40,60})$/);
 if(!match){bookingStopPolling();return false;}
 bookingStopPolling();$('modal').close();
 const [,kind,id,token]=match;const hash=globalThis.location.hash;
 $('app').innerHTML='<section class="panel booking-page"><p role="status">Loading request…</p></section>';
 if(kind==='request'){
  let lastReceipt='';const refresh=async()=>{try{const data=await bookingApi('patient',{id,token});if(location.hash!==hash)return;const signature=JSON.stringify(data);if(signature!==lastReceipt){bookingReceipt(data,token);lastReceipt=signature;}if(['scheduled','unable','expired'].includes(data.status))bookingStopPolling();}catch(error){if(location.hash===hash)$('app').innerHTML=`<section class="panel"><h1>Request unavailable</h1><p role="alert">${esc(error.message)}</p><a href="/">Back to search</a></section>`;bookingStopPolling();}};
  refresh();bookingTimer=setInterval(()=>{if(!document.hidden)refresh();},15000);
 }else{clinicGate(id,token);}
 return true;
}
function bookingReceipt(b,token){
 $('app').innerHTML=`<section class="panel booking-page"><p class="eyebrow">${esc(b.id)}</p><h1>${esc(BOOKING_STATUS[b.status])}</h1><p class="booking-notice">No email sent to clinic (testing mode). This request does not reserve an appointment.</p>${bookingSummary(b)}<ol class="booking-timeline"><li>Request submitted</li><li>${b.status==='requested'?'Awaiting clinic action (preview only)':esc(BOOKING_STATUS[b.status])}</li><li>The clinic confirms the exact appointment directly with you.</li></ol><h2>Keep your request link</h2><p>Bookmark this page to see updates. Treat the link as private. Status refreshes every 15 seconds while the page is open.</p><div class="actions"><button id="copyBookingLink">Copy request link</button><a href="/">Back to search</a>${b.preview_available?'<button id="previewClinic">Preview clinic workflow</button>':''}</div><p id="bookingActionStatus" role="status"></p><div id="clinicPreviewLink"></div></section>`;
 $('copyBookingLink').onclick=async()=>{try{await navigator.clipboard.writeText(location.href);$('bookingActionStatus').textContent='Request link copied.';}catch{$('bookingActionStatus').textContent='Bookmark this page or copy the address from your browser.';}};
 if(b.preview_available)$('previewClinic').onclick=async()=>{
  try{const preview=await bookingApi('preview',{id:b.id,token});$('clinicPreviewLink').innerHTML=`<p class="booking-notice">Local testing only: the clinic link and code preview do not send email.</p><a class="button primary" href="${esc(preview.clinic_url)}" target="_blank" rel="noopener noreferrer">Open clinic preview</a><details><summary>Preview clinic notification (not sent)</summary><pre class="booking-email">${esc(preview.notification)}</pre></details>`;}catch(error){$('bookingActionStatus').textContent=error.message;}
 };
}
function clinicGate(id,token){
 $('app').innerHTML=`<section class="panel booking-page"><p class="eyebrow">FOR IMAGING CENTERS · ${esc(id)}</p><h1>Open appointment request</h1><p>Verify a one-time code before viewing patient contact details. Codes expire after 10 minutes and can be used once.</p><p class="booking-notice">Email is disabled. On this local preview, a test code appears here instead of being emailed.</p><button id="clinicCodeSend">Generate preview code</button><p id="clinicCodeStatus" role="status"></p><form id="clinicVerify"><label>Six-digit code<input id="clinicCode" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6}" maxlength="6" required></label><button class="primary" id="clinicVerifyButton">Open request</button></form><p id="clinicError" role="alert"></p></section>`;
 $('clinicCodeSend').onclick=async()=>{
  $('clinicCodeSend').disabled=true;$('clinicError').textContent='';
  try{const data=await bookingApi('code',{id,token});$('clinicCodeStatus').textContent=data.preview_code?`Preview code: ${data.preview_code}. No email was sent. Expires in 10 minutes. Resend available after 60 seconds.`:'Email delivery is disabled. No code was sent.';setTimeout(()=>{if($('clinicCodeSend'))$('clinicCodeSend').disabled=false;},60000);}
  catch(error){$('clinicError').textContent=error.message;$('clinicCodeSend').disabled=false;}
 };
 $('clinicVerify').onsubmit=async event=>{
  event.preventDefault();$('clinicVerifyButton').disabled=true;
  try{const auth=await bookingApi('verify',{id,token,code:$('clinicCode').value});await clinicView(id,token,auth.session);}
  catch(error){if($('clinicError'))$('clinicError').textContent=error.message;if($('clinicVerifyButton'))$('clinicVerifyButton').disabled=false;}
 };
}
async function clinicView(id,token,session){
 bookingStopPolling();const b=await bookingApi('details',{id,session});
 $('app').innerHTML=`<section class="panel booking-page"><p class="eyebrow">FOR IMAGING CENTERS · ${esc(id)}</p><p id="clinicCountdown" role="timer"></p><h1>${esc(b.first_name)}</h1>${bookingSummary(b)}<a class="button primary" href="tel:${esc(b.phone.replace(/[^+0-9]/g,''))}">Call ${esc(b.phone)}</a><h2>After the call</h2><p id="clinicOutcome" role="status">${esc(BOOKING_STATUS[b.status])}</p><div class="booking-outcomes">${[['scheduled','Scheduled'],['voicemail','Left voicemail'],['unable','Can’t accommodate']].map(([v,t])=>`<button data-booking-status="${v}" ${['scheduled','unable','expired'].includes(b.status)?'disabled':''}>${t}</button>`).join('')}</div><p id="clinicError" role="alert"></p><p class="small">The patient can see updates on their request page. Details are deleted 30 days after the request closes. Voicemail keeps it open until the 72-hour link expires.</p><button id="clinicLock">Lock request</button></section>`;
 const tick=()=>{const left=Math.max(0,Math.ceil(b.expires_at-Date.now()/1000));if(!$('clinicCountdown'))return bookingStopPolling();$('clinicCountdown').textContent=`Session ends in ${Math.floor(left/60)}:${String(left%60).padStart(2,'0')}`;if(!left){bookingStopPolling();clinicGate(id,token);}};tick();bookingTimer=setInterval(tick,1000);
 $('clinicLock').onclick=async()=>{try{await bookingApi('lock',{id,session});bookingStopPolling();clinicGate(id,token);}catch(error){$('clinicError').textContent=error.message;}};
 document.querySelectorAll('[data-booking-status]').forEach(button=>button.onclick=async()=>{
  document.querySelectorAll('[data-booking-status]').forEach(b=>b.disabled=true);
  try{await bookingApi('status',{id,session,status:button.dataset.bookingStatus});await clinicView(id,token,session);}
  catch(error){$('clinicError').textContent=error.message;document.querySelectorAll('[data-booking-status]').forEach(b=>b.disabled=false);}
 });
}
document.addEventListener('click',event=>{
 const button=event.target.closest?.('[data-appointment]');if(!button)return;
 const center=DIRECTORY.find(e=>e.booking_id===button.dataset.appointment)||{booking_id:button.dataset.appointment};
 if(center)appointmentForm(center,button.dataset.bookingOffer||'');
});
async function openBookingTest(){
 if(!account)await signInGuest();
 await loadCatalog();
 const center=DIRECTORY.find(e=>e.booking_id);
 if(center)await appointmentForm(center);
 else modal('<h2>Booking preview</h2><p>No published clinics are available.</p>');
}

function accountPage(signup=false){
 updateNavigation();pageTop(signup?'signup':'login');
 $('app').innerHTML=`<section class="panel account-page"><h1>${signup?'Create an account':'Log in'}</h1><p>${signup?'Enter your basic details to create your MySelfPay account.':'Welcome back. Use your email and password.'}</p><form id="accountForm">
 ${signup?control('accountName','Full name','<input id="accountName" name="name" autocomplete="name" required maxlength="100">'):''}
 ${control('accountEmail','Email address','<input id="accountEmail" name="email" type="email" autocomplete="username" required maxlength="254">')}
 ${signup?control('accountPhone','Phone number (optional)','<input id="accountPhone" name="phone" type="tel" autocomplete="tel" maxlength="30">'):''}
 ${control('accountPassword','Password',`<input id="accountPassword" name="password" type="password" autocomplete="${signup?'new-password':'current-password'}" required ${signup?'minlength="12"':''} maxlength="128">`)}
 ${signup?'<p class="small">Use 12–128 characters. Your email is not verified by signup; appointment requests still require email verification.</p>'+control('accountConfirm','Confirm password','<input id="accountConfirm" type="password" autocomplete="new-password" required minlength="12" maxlength="128">')+'<p class="small">Your name, email, optional phone and a password hash are stored with your account. See <a href="/privacy-terms" target="_blank" rel="noopener">Terms &amp; Privacy</a>.</p>':''}
 <p id="accountError" role="alert" tabindex="-1"></p><button class="primary" id="accountSubmit">${signup?'Create account':'Log in'}</button></form>
 <p>${signup?'Already have an account? <a href="#login">Log in</a>':'Don’t have an account? <a href="#signup">Sign up</a>'}</p>
 <button id="accountGuest" type="button">Sign in as guest</button><p class="small">Forgot your password? Contact <a href="mailto:partners@onesmarter.com">support</a>. Automated password recovery is not available yet.</p></section>`;
 $('accountGuest').onclick=safe(async()=>{globalThis.history.replaceState(null,'',location.pathname);await signInGuest()});
 const form=$('accountForm');form.onsubmit=async event=>{
  event.preventDefault();const error=$('accountError'),button=$('accountSubmit');error.textContent='';
  if(signup&&$('accountPassword').value!==$('accountConfirm').value){error.textContent='Passwords do not match.';error.focus();return;}
  const data={email:$('accountEmail').value,password:$('accountPassword').value};
  if(signup){data.name=$('accountName').value;data.phone=$('accountPhone').value;}
  button.disabled=true;$('accountGuest').disabled=true;
  try{const r=await api(signup?'/register':'/login',data);account=r.member;csrf=r.csrf;form.reset();globalThis.history.replaceState(null,'',location.pathname);await start();await enterJourney('search');toast(signup?'Account created. You are signed in.':'You are signed in.');}
  catch(e){if(error.isConnected){error.textContent=e.message;error.focus();}}
  finally{button.disabled=false;if($('accountGuest'))$('accountGuest').disabled=false;}
 };
 $('accountEmail').focus();
}
