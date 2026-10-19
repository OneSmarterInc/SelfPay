(function () {
  if (window.myselfpayFlow) return;
  window.myselfpayFlow = true;
  let editing = false;
  let previousResults = false;
  let resultCategory = 'prices';
  let visibleLimit = 10;
  let frame;
  const icon = '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M20 11.5a8 8 0 0 1-8 8H5l-4 3v-11a9.5 9.5 0 0 1 19 0Z" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M6 10h9M6 14h6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';
  window.myselfpayOpenSearch = function () {
    document.getElementById('back')?.click();
    const classic = document.getElementById('classic');
    if (!classic) {
      const welcome = document.getElementById('welcomeBegin');
      if (welcome) {welcome.click();return true;}
      return false;
    }
    if (!classic.classList.contains('active')) classic.click();
    editing = true;
    enhance();
    window.scrollTo(0, 0);
    document.getElementById('mod')?.focus({preventScroll:true});
    return true;
  };
  window.myselfpayCloseOverlay = function () {
    if (document.getElementById('agent')?.classList.contains('active')) {
      document.getElementById('classic')?.click();editing=false;enhance();return true;
    }
    if (editing) {editing=false;enhance();window.scrollTo(0,0);return true;}
    return false;
  };
  function enhance() {
    const app = document.getElementById('app');
    if (!app) return;
    const form = document.getElementById('searchForm');
    const grid = app.querySelector('.grid');
    const section = grid && grid.querySelector(':scope > section');
    const hasResults = !!(section && section.querySelector('#sort'));
    const agentMode = !!document.getElementById('agent')?.classList.contains('active');
    app.classList.toggle('mobile-agent', agentMode);
    const enteringResults = hasResults && !previousResults;
    previousResults = hasResults;
    app.classList.toggle('mobile-results', hasResults);
    app.classList.toggle('mobile-editing', hasResults && editing);
    app.classList.toggle('mobile-searching', !!form && (!hasResults || editing) && !agentMode);
    app.classList.toggle('mobile-detail', !!document.getElementById('back'));
    if (form) {
      const details = form.closest('details');
      if (details && (!agentMode || editing)) details.open = true;
      const panel = form.closest('aside');
      if (panel) {
        panel.classList.add('mobile-search-panel');
        if (!panel.querySelector('.mobile-search-heading')) {
          const heading=document.createElement('div');heading.className='mobile-search-heading';
          heading.innerHTML='<h2>Search & filters</h2>';
          if(hasResults){
            const close=document.createElement('button');close.type='button';close.textContent='Close';
            close.onclick=window.myselfpayCloseOverlay;heading.appendChild(close);
          }
          panel.prepend(heading);
        }
      }
      if (!form.querySelector('.app-extra')) {
        const extra = document.createElement('details');
        extra.className = 'app-extra';
        extra.innerHTML = '<summary>More filters</summary>';
        form.insertBefore(extra, form.querySelector('button.primary'));
        ['radius', 'budget', 'type'].forEach(id => {
          const field = document.getElementById(id)?.closest('.field');
          if (field) extra.appendChild(field);
        });
      }
      if (!form.dataset.mobileBound) {
        form.dataset.mobileBound = 'true';
        form.addEventListener('submit', () => { editing = false;resultCategory='prices';visibleLimit=10; });
      }
    }
    if (!agentMode && form && !document.getElementById('mobileChatButton')) {
      const chat=document.createElement('button');chat.type='button';chat.id='mobileChatButton';
      chat.innerHTML=icon+'<span>Ask MySelfPay</span>';chat.setAttribute('aria-label','Ask MySelfPay chatbot');
      chat.onclick=()=>{editing=false;document.getElementById('agent')?.click();enhance();window.scrollTo(0,0);};
      app.appendChild(chat);
    }
    if (agentMode && section && !document.getElementById('mobileCloseChat')) {
      const close=document.createElement('button');close.id='mobileCloseChat';close.type='button';close.textContent='Back to results';
      close.onclick=window.myselfpayCloseOverlay;section.prepend(close);
    }
    const chatPanel=agentMode && section?.querySelector('.panel:has(#chatForm)');
    if(chatPanel && !chatPanel.dataset.mobileChatReady){
      chatPanel.dataset.mobileChatReady='true';
      const thread=document.getElementById('chat');const composer=document.getElementById('chatForm');
      const options=document.createElement('details');options.className='mobile-chat-options';
      options.innerHTML='<summary>Chat options & limits</summary>';
      while(thread?.nextElementSibling && thread.nextElementSibling!==composer)options.appendChild(thread.nextElementSibling);
      composer?.after(options);
    }
    if (hasResults && enteringResults && !editing && !agentMode) window.scrollTo(0, 0);
    // Keep original prices, protocol wording and qualification notices intact.
    app.querySelectorAll('article.card').forEach(card => {
      if (card.dataset.mobileCompact) return;
      card.dataset.mobileCompact = 'true';
      const detail = card.querySelector('[data-detail]');
      if (!detail) {
        const actions=card.querySelector('.card-actions');
        if(actions){
          card.classList.add('mobile-contact-only');
          const contact=document.createElement('details');contact.className='mobile-card-more';
          contact.innerHTML='<summary>Contact options</summary>';actions.before(contact);contact.appendChild(actions);
        }
        return;
      }
      const facts = card.querySelector('.facts');
      const source = detail.parentElement.querySelector('.small.muted');
      if (facts || source) {
        const extra = document.createElement('details');
        extra.className = 'mobile-card-more';
        extra.innerHTML = '<summary>Includes & requirements</summary>';
        detail.parentElement.before(extra);
        if (facts) extra.appendChild(facts);
        if (source) extra.appendChild(source);
        const scope = card.querySelector('.scope');
        if(scope){
          const fullScope=scope.textContent;
          const protocol=document.createElement('p');protocol.className='small';protocol.textContent=fullScope;extra.prepend(protocol);
          scope.textContent=fullScope.split(' · ').slice(0,2).join(' · ');
        }
        const distance=card.querySelector('.row[style] .small:not(.muted)');
        if(distance && distance.textContent){
          const original=distance.textContent;const miles=original.match(/about (\d+) miles/);
          if(miles){
            const reference=original.includes('city center')?'city reference':original.includes('ZIP-area')?'ZIP reference':'straight-line';
            distance.textContent='≈ '+miles[1]+' mi · '+reference;distance.title=original;
            const distanceNote=document.createElement('p');distanceNote.className='small';distanceNote.textContent=original;extra.appendChild(distanceNote);
          }
        }
      }
    });
    if (hasResults && section) {
      let category='prices';const cards=[];
      Array.from(section.children).forEach(node=>{
        if(node.tagName==='H2'){
          if(/program/i.test(node.textContent))category='programs';
          else if(/facilities to contact/i.test(node.textContent))category='quotes';
          node.classList.add('mobile-group-heading');
        }
        if(node.matches('article.card')){node.dataset.mobileCategory=category;cards.push(node);}
      });
      const counts={prices:0,programs:0,quotes:0};cards.forEach(card=>counts[card.dataset.mobileCategory]++);
      if(!counts[resultCategory])resultCategory=Object.keys(counts).find(key=>counts[key])||'prices';
      let categories=document.getElementById('mobileResultCategories');
      if(!categories){categories=document.createElement('div');categories.id='mobileResultCategories';categories.setAttribute('aria-label','Result categories');section.prepend(categories);}
      const signature=JSON.stringify([counts,resultCategory]);
      if(categories.dataset.signature!==signature){
        categories.dataset.signature=signature;categories.replaceChildren();
        [['prices','Offers'],['programs','Programs'],['quotes','Request quote']].forEach(([key,label])=>{
          if(!counts[key])return;
          const button=document.createElement('button');button.type='button';button.textContent=label+' ('+counts[key]+')';
          button.setAttribute('aria-pressed',String(resultCategory===key));button.onclick=()=>{resultCategory=key;visibleLimit=10;enhance();window.scrollTo(0,0);};categories.appendChild(button);
        });
      }
      let index=0;cards.forEach(card=>{const match=card.dataset.mobileCategory===resultCategory;card.hidden=!match||++index>visibleLimit;});
      let more=document.getElementById('mobileMoreResults');
      if(!more){more=document.createElement('button');more.type='button';more.id='mobileMoreResults';more.onclick=()=>{visibleLimit+=10;enhance();};section.appendChild(more);}
      more.hidden=counts[resultCategory]<=visibleLimit;
      const shown=Math.min(visibleLimit,counts[resultCategory]);
      const label='Show more · '+shown+' of '+counts[resultCategory];if(more.textContent!==label)more.textContent=label;
      const resultHeading=section.querySelector(':scope>.row.between h2');
      if(resultHeading){
        const noun={prices:'offer',programs:'program',quotes:'facility'}[resultCategory];
        const heading=counts[resultCategory]+' '+(counts[resultCategory]===1?noun:resultCategory==='quotes'?'facilities':noun+'s');
        if(resultHeading.textContent!==heading)resultHeading.textContent=heading;
      }
    }
    const detailPanel = app.querySelector('.detailgrid>section');
    if (detailPanel && !detailPanel.dataset.mobileReady) {
      detailPanel.dataset.mobileReady = 'true';
      const contacts = app.querySelector('.detailgrid>aside .card-actions');
      const scope = detailPanel.querySelector('.price')?.nextElementSibling;
      if (contacts && scope) scope.after(contacts);
      const checklist = detailPanel.querySelector('.checklist');
      if (checklist) {
        const heading = checklist.previousElementSibling;
        const questions = document.createElement('details');
        questions.className = 'mobile-card-more';
        const summary = document.createElement('summary');
        summary.textContent = heading?.textContent || 'Questions to ask the facility';
        questions.appendChild(summary);
        checklist.before(questions);
        questions.appendChild(checklist);
        if (heading?.tagName === 'H2') heading.remove();
      }
    }
    const sample = document.getElementById('sampleSearch');
    if (sample) {
      const panel = sample.closest('.panel');
      panel?.classList.add('app-intro');
      panel?.nextElementSibling?.classList.add('app-coverage');
    }
  }
  const observer = new MutationObserver(() => {
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(enhance);
  });
  observer.observe(document.getElementById('app') || document.body, { childList: true, subtree: true });
  enhance();
})();
