# Finance Suite Production Ops Runbook

Updated: 2026-05-10

This runbook covers the current production access issue and the next operational changes. It intentionally does not require frontend, backend, or nginx application code changes.

## 1. Current Diagnosis

The server-side stack is healthy.

- `www.touziagent.com A` resolves to `119.28.156.125`.
- `www.touziagent.com AAAA` is empty, so IPv6 is not the cause.
- On the server, SNI to localhost works:
  - `https://127.0.0.1/` returns `301`.
  - `www.touziagent.com -> 127.0.0.1` returns `HTTP/2 200`.
  - `touziagent.com -> 127.0.0.1` returns `301`.
- On the server, SNI to the public IP also works:
  - `www.touziagent.com -> 119.28.156.125` returns `HTTP/2 200`.
- nginx config has no `ssl_reject_handshake`, `return 444`, or `deny all`.
- `ufw` is inactive, default iptables policies are `ACCEPT`, and fail2ban is not installed.

The failing path is local-network direct IPv4 access:

```bash
HTTPS_PROXY= HTTP_PROXY= ALL_PROXY= NO_PROXY='*' \
  curl -4vk https://www.touziagent.com/ -o /dev/null
```

Observed failure:

```text
Connected to www.touziagent.com (119.28.156.125) port 443
TLS Client hello
Recv failure: Connection reset by peer
```

Hotspot access works. Therefore the immediate cause is the original local broadband path to Tencent Cloud public IP `119.28.156.125:443`, not the application stack.

## 2. Tencent Cloud Console Checklist

Check these before changing server files:

- Lighthouse firewall: allow `80/tcp` and `443/tcp` from `0.0.0.0/0`.
- Security group: allow `80/tcp` and `443/tcp` inbound.
- Cloud Firewall: no block rule for the domain, source region, or local broadband IP.
- WAF: no HTTPS/SNI/domain policy blocking `touziagent.com` or `www.touziagent.com`.
- CC protection: no temporary block, rate policy, or JavaScript challenge affecting normal browser traffic.
- Blacklist/whitelist: local broadband public IP is not denied.
- Region blocking: China mainland regions and local ISP are not blocked.
- Domain security policy: no domain-level policy attached only to `touziagent.com` or `www.touziagent.com`.

## 3. CDN Access Plan

Recommended target:

```text
touziagent.com      CNAME/redirect to www.touziagent.com
www.touziagent.com  CDN accelerated website
api.touziagent.com  direct origin or separate API acceleration
```

CDN origin:

```text
Origin host: 119.28.156.125
Origin protocol: HTTPS
Origin SNI: www.touziagent.com
Origin Host header: www.touziagent.com
```

Recommended CDN cache rules:

```text
/api/*                 no-cache, bypass cache
/                     no-cache
/*.html                no-cache
/app/*                no-cache, or short cache only if HTML is versioned
/static/*             cache 7-30 days
*.js, *.css            cache 7-30 days
*.png, *.jpg, *.webp   cache 7-30 days
```

Required CDN behavior:

- Forward `Host`.
- Forward cookies for `/api/*`.
- Forward query strings for `/api/*`.
- Preserve `Set-Cookie`.
- Do not cache `POST`, `PUT`, `PATCH`, or `DELETE`.
- Enable HTTPS at edge.
- Keep origin HTTPS certificate valid for `www.touziagent.com`.

## 4. API Subdomain Split

Use `www.touziagent.com` for browser pages and static assets.

Use `api.touziagent.com` for API traffic when the frontend is ready to call a separate API host. Until then, keep `/api/*` on `www` as a compatibility path.

Recommended model:

```text
Browser page:
  https://www.touziagent.com/
  https://www.touziagent.com/app/

API:
  https://api.touziagent.com/login
  https://api.touziagent.com/check-auth
  https://api.touziagent.com/analyze

Compatibility:
  https://www.touziagent.com/api/*
```

If cookies are shared across subdomains, set the cookie domain deliberately, for example `.touziagent.com`, and keep `SameSite`/`Secure` settings consistent.

## 5. Cache-Control Policy

Origin/CDN policy:

```text
HTML:
  Cache-Control: no-cache, no-store, must-revalidate, max-age=0

API:
  Cache-Control: no-store

Static hashed assets:
  Cache-Control: public, max-age=604800, immutable
  or public, max-age=2592000, immutable

Unhashed static assets:
  Cache-Control: public, max-age=86400
```

Keep `/api/*` out of CDN cache even if the origin response accidentally lacks `no-store`.

## 6. Deploy Flow

Recommended high-level deploy:

```bash
cd /home/ubuntu/finance-suite-web
git status
git pull origin main

/home/ubuntu/finance-suite-web/venv/bin/python -m compileall app

sudo systemctl restart finance-suite.service
sudo systemctl status finance-suite.service --no-pager

sudo nginx -t
curl -vk --resolve www.touziagent.com:443:127.0.0.1 https://www.touziagent.com/ -o /dev/null
curl -vk --resolve www.touziagent.com:443:119.28.156.125 https://www.touziagent.com/ -o /dev/null
```

Run the lightweight public health check from this repo:

```bash
bash scripts/healthcheck_public.sh
```

## 7. systemd Uvicorn Service

Install the unit template in `deploy/systemd/finance-suite.service` to:

```text
/etc/systemd/system/finance-suite.service
```

Then run:

```bash
sudo systemctl daemon-reload
sudo systemctl enable finance-suite.service
sudo systemctl restart finance-suite.service
sudo systemctl status finance-suite.service --no-pager
```

Logs:

```bash
sudo journalctl -u finance-suite.service -f
```

## 8. Automatic Backups

Use:

```bash
sudo bash scripts/backup_production.sh
```

Recommended daily cron:

```cron
15 3 * * * /usr/bin/sudo /bin/bash /home/ubuntu/finance-suite/ops/production/scripts/backup_production.sh >> /var/log/finance-suite-backup.log 2>&1
```

The backup script keeps recent archives and removes old ones based on retention days.

## 9. Health Check Commands

DNS:

```bash
dig +short touziagent.com A
dig +short touziagent.com AAAA
dig +short www.touziagent.com A
dig +short www.touziagent.com AAAA
```

Direct, no local proxy:

```bash
HTTPS_PROXY= HTTP_PROXY= ALL_PROXY= NO_PROXY='*' \
  curl -4vk https://www.touziagent.com/ -o /dev/null
```

Server-side SNI:

```bash
curl -vk --resolve www.touziagent.com:443:127.0.0.1 https://www.touziagent.com/ -o /dev/null
curl -vk --resolve www.touziagent.com:443:119.28.156.125 https://www.touziagent.com/ -o /dev/null
```
