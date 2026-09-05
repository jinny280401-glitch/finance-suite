# Deploy Runbook

This runbook is for production operations on the Tencent Cloud server. It does not require modifying frontend, backend, or nginx business logic.

## Paths

```text
Web app:       /home/ubuntu/finance-suite-web
Virtualenv:    /home/ubuntu/finance-suite-web/venv
Service:       finance-suite.service
nginx config:  /etc/nginx/
Backups:       /home/ubuntu/backups
```

## Preflight

```bash
hostname
date
whoami
cd /home/ubuntu/finance-suite-web
git status --short
sudo systemctl status finance-suite.service --no-pager
sudo nginx -t
```

Create a backup before deploy:

```bash
cd /home/ubuntu/finance-suite/ops/production
bash scripts/backup.sh
```

## Deploy Steps

```bash
cd /home/ubuntu/finance-suite-web
git fetch origin
git status --short
git pull origin main
```

Install dependencies if needed:

```bash
/home/ubuntu/finance-suite-web/venv/bin/pip install -r requirements.txt
```

Validate Python imports/syntax:

```bash
/home/ubuntu/finance-suite-web/venv/bin/python -m compileall app
```

Validate nginx:

```bash
sudo nginx -t
```

Restart service:

```bash
sudo systemctl restart finance-suite.service
sudo systemctl status finance-suite.service --no-pager
```

Reload nginx only if nginx config changed:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Verification

Local backend:

```bash
curl -sS -I http://127.0.0.1:8000/ || true
curl -sS -I http://127.0.0.1:8000/api/check-auth || curl -sS -I http://127.0.0.1:8000/api/health
```

Origin SNI:

```bash
curl -vk --resolve www.touziagent.com:443:127.0.0.1 https://www.touziagent.com/ -o /dev/null
curl -vk --resolve www.touziagent.com:443:119.28.156.125 https://www.touziagent.com/ -o /dev/null
```

Public endpoints:

```bash
curl -I https://www.touziagent.com/
curl -I https://www.touziagent.com/app/
curl -I https://www.touziagent.com/api/check-auth || curl -I https://www.touziagent.com/api/health
```

Run the scripted check:

```bash
cd /home/ubuntu/finance-suite/ops/production
bash scripts/healthcheck.sh
```

## Rollback

List backups:

```bash
ls -lh /home/ubuntu/backups
```

Stop service:

```bash
sudo systemctl stop finance-suite.service
```

Restore from a selected archive:

```bash
cd /home/ubuntu
sudo tar -xzf /home/ubuntu/backups/finance-suite-YYYYmmdd-HHMMSS.tar.gz -C /
```

Restart:

```bash
sudo systemctl start finance-suite.service
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl status finance-suite.service --no-pager
```

## Common Faults

### Browser shows `ERR_CONNECTION_RESET`

Check whether the failure is local-network direct access:

```bash
HTTPS_PROXY= HTTP_PROXY= ALL_PROXY= NO_PROXY='*' \
  curl -4vk https://www.touziagent.com/ -o /dev/null
```

If hotspot works but broadband fails, prioritize CDN or network/provider path investigation.

### nginx config failure

```bash
sudo nginx -t
sudo journalctl -u nginx --no-pager --since "30 minutes ago"
```

Do not reload nginx until `nginx -t` passes.

### Backend down

```bash
sudo systemctl status finance-suite.service --no-pager
sudo journalctl -u finance-suite.service --no-pager --since "30 minutes ago"
ss -tlnp | grep 8000 || true
```

### API returns 502/504

Check backend is listening on `127.0.0.1:8000`, then inspect nginx error log:

```bash
curl -I http://127.0.0.1:8000/api/check-auth || curl -I http://127.0.0.1:8000/api/health
sudo tail -100 /var/log/nginx/error.log
```
