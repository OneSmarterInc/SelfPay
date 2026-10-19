(function () {
  if (window.myselfpayFlow) return;
  window.myselfpayFlow = true;
  let editing = false;
  let frame;
  function enhance() {
    const app = document.getElementById('app');
    if (!app) return;
    const form = document.getElementById('searchForm');
    const grid = app.querySelector('.grid');
    const section = grid && grid.querySelector(':scope > section');
    const hasResults = !!(section && section.querySelector('#sort'));
    app.classList.toggle('mobile-results', hasResults);
    app.classList.toggle('mobile-editing', hasResults && editing);
    app.classList.toggle('mobile-detail', !!document.getElementById('back'));
    if (form) {
      const details = form.closest('details');
      if (details) details.open = true;
      const panel = form.closest('aside');
      if (panel) panel.classList.add('mobile-search-panel');
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
        form.addEventListener('submit', () => { editing = false; });
      }
    }
    if (hasResults && !document.getElementById('mobileEditSearch')) {
      const edit = document.createElement('button');
      edit.id = 'mobileEditSearch';
      edit.type = 'button';
      edit.textContent = 'Edit search';
      edit.onclick = () => {
        editing = !editing;
        app.classList.toggle('mobile-editing', editing);
        edit.setAttribute('aria-expanded', String(editing));
        if (editing) {
          form?.scrollIntoView({ block: 'start' });
          document.getElementById('mod')?.focus({ preventScroll: true });
        }
      };
      edit.setAttribute('aria-expanded', String(editing));
      grid.before(edit);
      if (!editing) window.scrollTo(0, 0);
    }
    // Keep original prices, protocol wording and qualification notices intact.
    app.querySelectorAll('article.card').forEach(card => {
      if (card.dataset.mobileCompact) return;
      card.dataset.mobileCompact = 'true';
      const detail = card.querySelector('[data-detail]');
      if (!detail) return;
      const facts = card.querySelector('.facts');
      const source = detail.parentElement.querySelector('.small.muted');
      if (facts || source) {
        const extra = document.createElement('details');
        extra.className = 'mobile-card-more';
        extra.innerHTML = '<summary>Includes & requirements</summary>';
        detail.parentElement.before(extra);
        if (facts) extra.appendChild(facts);
        if (source) extra.appendChild(source);
      }
    });
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
