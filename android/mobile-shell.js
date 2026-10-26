(function(){
 if(window.__myselfpayNativeShell) return;
 window.__myselfpayNativeShell=true;
 const q=(s)=>document.querySelector(s);
 const launchSearch=()=>{close(); if(q('#welcomeBegin'))q('#welcomeBegin').click(); else if(window.myselfpayOpenSearch) window.myselfpayOpenSearch(); else q('#classic')?.click(); };
 let previousFocus=null;
 const close=()=>{
   if(!document.body.classList.contains('native-drawer-open'))return;
   document.body.classList.remove('native-drawer-open');
   document.documentElement.classList.remove('native-drawer-open');
   drawer.setAttribute('aria-hidden','true');
   shell.querySelector('#nativeHamburger').setAttribute('aria-expanded','false');
   if(previousFocus&&previousFocus.isConnected)previousFocus.focus({preventScroll:true});
   previousFocus=null;
 };
 const goHome=()=>{
   close();
   const b=document.querySelector('header a.brand')||document.querySelector('header a[href="/"]');
   if(b)b.click();else location.assign('/');
 };
 const shell=document.createElement('div');shell.id='nativeMobileHeader';
 shell.innerHTML='<button type="button" id="nativeHamburger" aria-label="Open navigation">☰</button><strong id="nativeTitle">MySelfPay</strong><button type="button" id="nativeSearch" aria-label="Search">⌕</button>';
 const drawer=document.createElement('div');drawer.id='nativeMobileDrawer';drawer.setAttribute('role','dialog');drawer.setAttribute('aria-modal','true');
 drawer.innerHTML='<div class="native-menu-top"><strong>MySelfPay</strong><button type="button" id="nativeClose" aria-label="Close navigation">×</button></div><nav id="nativeMenuItems"></nav>';
 const menu=[['Home',goHome],['Search',launchSearch],['About',()=>location.assign('/about.html')],['Contact',()=>location.assign('/contact.html')],['Terms & Privacy',()=>location.assign('/privacy-terms.html')],['For imaging centers',()=>location.assign('/for-imaging-centers.html')],['Sign out',()=>{close();const b=q('#signout')||q('#logout')||q('#signOut');if(b)b.click();else goHome();}]];
 menu.forEach(([label,fn])=>{const b=document.createElement('button');b.type='button';b.textContent=label;b.addEventListener('click',fn);drawer.querySelector('nav').appendChild(b);});
 document.body.append(shell,drawer);
 drawer.setAttribute('aria-hidden','true');
 shell.querySelector('#nativeHamburger').setAttribute('aria-expanded','false');
 shell.querySelector('#nativeHamburger').setAttribute('aria-controls','nativeMobileDrawer');
 q('#nativeHamburger').onclick=()=>{
   previousFocus=document.activeElement;
   document.body.classList.add('native-drawer-open');
   document.documentElement.classList.add('native-drawer-open');
   drawer.setAttribute('aria-hidden','false');
   q('#nativeHamburger').setAttribute('aria-expanded','true');
   q('#nativeClose').focus({preventScroll:true});
 };
 q('#nativeClose').onclick=close;
 q('#nativeSearch').onclick=launchSearch;
 document.addEventListener('keydown',e=>{
  if(!document.body.classList.contains('native-drawer-open'))return;
  if(e.key==='Escape'){e.preventDefault();close();}
  if(e.key==='Tab'){
    const focusable=[...drawer.querySelectorAll('button:not([disabled]),a[href],input:not([disabled])')];
    const first=focusable[0],last=focusable[focusable.length-1];
    if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
    else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
  }
 });
 const state=()=>{
  const a=q('#app');if(!a)return;
  const welcome=!!a.querySelector('.welcome-intro');
  const title=q('#nativeTitle');
  if(title)title.textContent=welcome?'MySelfPay':'Find imaging options';
  a.classList.toggle('native-welcome',welcome);
  if(welcome){
    const intro=a.querySelector('.welcome-intro');
    if(intro && !intro.querySelector('#nativeHomeHero')){
      const hero=document.createElement('div');hero.id='nativeHomeHero';
      hero.innerHTML='<div class="native-home-brand"><img src="/logo.png" alt=""><b>YOUR SELF-PAY SEARCH</b></div><h1>Imaging options.<br>Clearer prices.</h1><p>Find self-pay MRI and CT near you.</p><div class="native-services"><button type="button" data-mod="MRI"><b>MRI</b><span>Magnetic resonance</span></button><button type="button" data-mod="CT"><b>CT</b><span>CT imaging</span></button></div><div class="native-home-links">Search nearby&nbsp; · &nbsp;Compare&nbsp; · &nbsp;Contact</div><button type="button" id="nativeGuest">Sign in as guest</button><div class="native-home-caption">No account needed</div><p class="native-disclaimer">Confirm the exact exam and total with the facility.</p>';
      intro.prepend(hero);
      hero.querySelector('#nativeGuest').onclick=()=>{(q('#welcomeAccount')||q('#welcomeBegin'))?.click();};
      hero.querySelectorAll('[data-mod]').forEach(b=>b.onclick=()=>{launchSearch();const selected=b.dataset.mod;const attempt=()=>{const field=q('#mod');if(field){field.value=selected;field.dispatchEvent(new Event('change',{bubbles:true}));}else setTimeout(attempt,150);};attempt();});
    }
  }
 };
 let pending=false;
 const refresh=()=>{if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;state();});};
 const appRoot=q('#app')||document.body;
 new MutationObserver(refresh).observe(appRoot,{childList:true,subtree:false});
 window.addEventListener('pageshow',refresh);
 window.addEventListener('resize',refresh);
 state();
})();