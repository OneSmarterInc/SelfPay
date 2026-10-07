# Public provider directory exports

This data-only branch is read by trusted `main` code in the Directory sync workflow.
Do not merge it into an application branch. It contains no runnable workflows.
Vercel Git deployments are disabled by `vercel.json` on this branch.

`directory/current.json` must be byte-identical to its immutable versioned archive.
Only the 13 public provider columns and source row numbers are exported from the
canonical workbook. The Library version and workbook SHA-256 identify the source;
this branch is not an independent research source or a place for user information.

Refresh with the trusted main-branch `directory_sync.py export` command after
materializing the latest canonical Library version. Never reuse an older local
workbook. Publish the current file and its new archive together in one commit,
using the current data-branch head as an expected-SHA lease.
