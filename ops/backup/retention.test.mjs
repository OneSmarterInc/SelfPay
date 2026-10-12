import { test } from 'node:test';
import assert from 'node:assert/strict';
import { expiredBackup } from './retention.mjs';
const now = Date.parse('2026-10-12T10:00:00Z');
const pathname = 'selfpay-backups/br-rapid-mouse-b7clh18t/2026-09-01T02-30-00-000Z-123abc.tar.age';
test('retention uses server upload time and strict 14-day boundary', () => {
 assert.equal(expiredBackup({pathname, uploadedAt:new Date(now-14*86400000)},now),false);
 assert.equal(expiredBackup({pathname, uploadedAt:new Date(now-14*86400000-1)},now),true);
 assert.equal(expiredBackup({pathname, uploadedAt:new Date(now)},now),false);
});
test('never delete foreign, plaintext, or malformed objects', () => {
 for (const p of ['other/file.tar.age',pathname.replace('br-rapid-mouse-b7clh18t','br-other'),pathname.replace('.age',''),pathname+'/extra'])
  assert.equal(expiredBackup({pathname:p, uploadedAt:'2020-01-01'},now),false);
 assert.equal(expiredBackup({pathname, uploadedAt:'invalid'},now),false);
});
