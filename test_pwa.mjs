import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const handlers = {};
const cached = [];
const deleted = [];
const offline = {body: 'offline'};
const context = {
  URL, Request: class extends Request { constructor(url, options) { super(new URL(url, 'https://myselfpay-review.vercel.app'), options); } }, Response,
  self: {location: {origin: 'https://myselfpay-review.vercel.app'},
    addEventListener: (name, fn) => handlers[name] = fn,
    clients: {claim: async () => {}}},
  caches: {
    open: async () => ({add: async request => cached.push(request)}),
    keys: async () => ['other-app', 'myselfpay-offline-v0', 'myselfpay-offline-v1'],
    delete: async key => deleted.push(key),
    match: async () => offline,
  },
  fetch: async () => {throw Error('offline');}
};
vm.runInNewContext(fs.readFileSync('static/sw.js','utf8'), context);
let pending;
handlers.install({waitUntil: promise => pending = promise});
await pending;
assert.deepEqual(cached.map(x => new URL(x.url).pathname), ['/offline.html']);
assert.equal(cached[0].credentials, 'omit');
handlers.activate({waitUntil: promise => pending = promise});
await pending;
assert.deepEqual(deleted, ['myselfpay-offline-v0']);
function dispatch(path, method='GET', mode='navigate') {
  let intercepted=false, response;
  handlers.fetch({request: {url: new URL(path, context.self.location.origin).href, method, mode},
    respondWith: value => {intercepted=true; response=value;}});
  return {intercepted,response};
}
for (const path of ['/api/me','/api/catalog','/api/search','/api/agent','/app.js','https://other.example/']) {
  assert.equal(dispatch(path).intercepted,false,path);
}
assert.equal(dispatch('/', 'POST').intercepted,false);
assert.equal(dispatch('/', 'GET', 'cors').intercepted,false);
assert.equal(await dispatch('/').response,offline);
const online={body:'fresh response'};
context.fetch=async () => online;
assert.equal(await dispatch('/').response,online);
context.fetch=async () => new Response('Server unavailable',{status:503});
assert.equal((await dispatch('/').response).status,503);
console.log('PWA offline and network-only privacy checks passed');
