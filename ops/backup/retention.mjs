export function expiredBackup(blob, now = Date.now()) {
  return /^selfpay-backups\/br-rapid-mouse-b7clh18t\/\d{4}-\d{2}-\d{2}T[\d-]+Z-[a-f0-9-]+\.tar\.age$/.test(blob.pathname)
    && Number.isFinite(new Date(blob.uploadedAt).getTime())
    && new Date(blob.uploadedAt).getTime() < now - 14 * 86400000;
}
