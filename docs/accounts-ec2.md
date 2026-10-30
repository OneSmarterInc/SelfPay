# Account login and signup on EC2

The frontend is `static/index.html` and `static/app.js`. The backend is
`accounts.py`, `server.py`, `core.py` and `postgres_store.py`. `aws_server.py`
is an optional explicit production entry point for EC2 behind HTTPS Nginx.
No new email service is needed. Booking email verification remains separate.

Signup stores name, normalized email, optional phone and a salted scrypt password
hash. Passwords are never stored in plaintext. Users log in automatically after
signup; sessions expire after 8 hours. Guest access remains available. Signup does
not verify email ownership and does not activate old guest/review accounts.
No date of birth, postal address, medical or payment data is requested.
Automated forgotten-password recovery is not included in this change.

## Before applying

Use the existing database and application checkout. Do not run `setup_hosted.py`
or seed/import commands. This migration only creates `user_accounts`; existing
members, directory listings, booking tables and data are untouched. Account data
is created automatically when users submit Signup, not inserted manually.

This guide assumes Ubuntu/Debian PostgreSQL with the `postgres` OS account and
peer administrative access. If those are different on your EC2 instance, adjust
with your administrator. The database name and systemd service name cannot be
inferred from the repository. Do not guess them or share `.env` contents.

First deploy/pull the reviewed account feature commit into a separate release
directory using your normal deployment process. From that repository directory:

```bash
read -r -p 'Existing SelfPay database name: ' SELFPAY_DB
read -r -p 'Existing application database role: ' SELFPAY_ROLE
test -n "$SELFPAY_DB" && test -n "$SELFPAY_ROLE"
```

Confirm these are the same database/role in your app's private DATABASE_URL.
Make a restricted backup and verify it in an isolated local database before
changing the application database. Keep it until recovery verification passes;
do not commit real user data into the source repository.

```bash
umask 077
SELFPAY_DUMP="$HOME/selfpay-before-accounts-$(date -u +%Y%m%dT%H%M%SZ).dump"
sudo -u postgres pg_dump --format=custom --dbname="$SELFPAY_DB" > "$SELFPAY_DUMP"
test -s "$SELFPAY_DUMP"
pg_restore --list "$SELFPAY_DUMP" > /dev/null
SELFPAY_REHEARSAL="selfpay_accounts_check_$(date -u +%Y%m%d%H%M%S)"
sudo -u postgres createdb "$SELFPAY_REHEARSAL"
sudo -u postgres pg_restore --exit-on-error --no-owner --no-acl --dbname="$SELFPAY_REHEARSAL" < "$SELFPAY_DUMP"
sudo -u postgres psql -X -1 -v ON_ERROR_STOP=1 --dbname="$SELFPAY_REHEARSAL" < ops/sql/20261030-user-accounts.sql
```

Stop on any error. Inspect the rehearsal, then apply the exact tested additive SQL:

```bash
sudo -u postgres psql -X -1 -v ON_ERROR_STOP=1 --dbname="$SELFPAY_DB" < ops/sql/20261030-user-accounts.sql
sudo -u postgres psql -X -v ON_ERROR_STOP=1 --dbname="$SELFPAY_DB" -v app_role="$SELFPAY_ROLE" <<'SQL'
GRANT SELECT, INSERT, UPDATE, DELETE ON user_accounts TO :"app_role";
SQL
sudo -u postgres psql -X --dbname="$SELFPAY_DB" -c '\d user_accounts'
```

The app role also needs its existing permissions on members, sessions,
guest_usage, settings and login_limits. No superuser role is required by the app.

## Private environment and HTTPS

Keep the existing DATABASE_URL in the application's private `.env` or systemd
EnvironmentFile. Keep it out of shell history, chat and commits. Set APP_ORIGIN
to `https://myselfpay.onesmarter.com` (or your actual public HTTPS origin).

If PostgreSQL is on the same EC2 machine, host must be `127.0.0.1`, `localhost`
or `::1`. The adapter defaults to TLS; only if local PostgreSQL does not support
TLS, append `?sslmode=disable` (or `&sslmode=disable` if a query already exists)
inside that private file. This exception is rejected for remote database hosts.
Keep port 5432 private and PostgreSQL bound to loopback. Do not open it publicly.

For the new `aws_server.py` entry point, configure the existing HTTPS Nginx
location to preserve the public host and overwrite the client IP header:

```nginx
location / {
    proxy_pass http://127.0.0.1:8765;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Use this only inside the existing TLS server block. Preserve your certificate
and HTTP-to-HTTPS redirect. If another load balancer/CDN sits before Nginx, review
trusted proxy/IP configuration first. Do not expose port 8765 publicly.

After installing requirements in the existing virtual environment, the command
for systemd ExecStart is `<absolute-venv-path>/bin/python <absolute-repo-path>/aws_server.py --port 8765`.
Set WorkingDirectory to that release directory, preserve the private environment
file, and keep the existing unprivileged service User. Do not replace the entire
service file. Review `sudo systemctl cat <your-service>` locally (it may include
secrets; do not paste its output). Then:

```bash
read -r -p 'Existing SelfPay systemd service name: ' SELFPAY_SERVICE
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl restart "$SELFPAY_SERVICE"
sudo systemctl is-active "$SELFPAY_SERVICE"
curl --fail --silent --output /dev/null https://myselfpay.onesmarter.com/
```

Run each command only after the previous succeeds. Verify in a browser: guest
search; Signup with your test details; logout; login; refresh preserving login;
wrong password rejection; duplicate email rejection; and appointment email
verification remains required. Never print account rows/password hashes.

The new secure cookie invalidates earlier loopback cookies; users sign in again.
If startup/health fails, restore the previous service ExecStart and previous code
release and restart. Leave the additive table/data intact; do not drop account
rows or restore the full database over newer production data. Keep the backup
and rehearsal until verification succeeds. No database migration, EC2 deployment,
paid service or billing change was performed by preparing this code.
