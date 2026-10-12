import { createReadStream } from 'node:fs';
import { createHash, randomUUID } from 'node:crypto';
import { put, get, list, del } from '@vercel/blob';

import { expiredBackup } from './retention.mjs';
async function digest(stream) {
  const hash = createHash('sha256');
  for await (const chunk of stream) hash.update(chunk);
  return hash.digest('hex');
}
async function main() {
  const token = process.env.BLOB_READ_WRITE_TOKEN;
  if (!token || process.env.BACKUP_DATA_CLASS !== 'synthetic') throw new Error('Backup configuration missing');
  const prefix = 'selfpay-backups/br-rapid-mouse-b7clh18t/';
  const filename = process.argv[2];
  if (!filename?.endsWith('.tar.age')) throw new Error('Encrypted file required');
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const pathname = `${prefix}${timestamp}-${randomUUID()}.tar.age`;
  const expected = await digest(createReadStream(filename));
  const uploaded = await put(pathname, createReadStream(filename), {
    token, access: 'private', addRandomSuffix: false, allowOverwrite: false,
    contentType: 'application/octet-stream', multipart: true,
  });
  const copy = await get(uploaded.pathname, { token, access: 'private', useCache: false });
  if (!copy || copy.statusCode !== 200 || await digest(copy.stream) !== expected) {
    throw new Error('Read-back verification failed');
  }
  // Clean only this job's namespace, and only after a new verified upload.
  const expired = [];
  let cursor;
  do {
    const page = await list({ token, prefix, cursor, limit: 1000 });
    for (const blob of page.blobs) if (expiredBackup(blob)) expired.push(blob.url);
    cursor = page.hasMore ? page.cursor : undefined;
  } while (cursor);
  for (const url of expired) await del(url, { token });
  console.log(`Verified encrypted upload; expired backups removed: ${expired.length}`);
}
main().catch(() => { console.error('Private backup storage operation failed.'); process.exitCode = 1; });
