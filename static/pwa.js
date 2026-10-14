const install = document.getElementById('installApp');
const help = document.getElementById('installHelp');
const standalone = window.matchMedia('(display-mode: standalone)');
let deferredPrompt = null;
function refreshInstallVisibility() {
  install.hidden = standalone.matches || window.navigator.standalone === true;
}
refreshInstallVisibility();
standalone.addEventListener?.('change', refreshInstallVisibility);
window.addEventListener('beforeinstallprompt', event => {
  event.preventDefault();
  deferredPrompt = event;
  refreshInstallVisibility();
});
window.addEventListener('appinstalled', () => {
  deferredPrompt = null;
  install.hidden = true;
  help.close();
});
install.addEventListener('click', async () => {
  if (!deferredPrompt) { help.showModal(); return; }
  const prompt = deferredPrompt;
  deferredPrompt = null;
  try {
    await prompt.prompt();
    await prompt.userChoice;
  } catch { help.showModal(); }
});
document.getElementById('closeInstallHelp').addEventListener('click', () => help.close());
if ('serviceWorker' in navigator && window.isSecureContext) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js', {scope: '/', updateViaCache: 'none'})
      .catch(() => { /* Website remains usable if storage/workers are unavailable. */ });
  });
}
