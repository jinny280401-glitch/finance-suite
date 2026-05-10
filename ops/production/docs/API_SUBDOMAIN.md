# API Subdomain Split

The goal is to keep page/static delivery on `www.touziagent.com` and API traffic on `api.touziagent.com`.

## Target

```text
www.touziagent.com  website and static assets, CDN enabled
api.touziagent.com  API traffic, direct origin or dedicated API acceleration
```

Keep `/api/*` on `www` during migration if current frontend code still calls relative paths.

## DNS Recommendation

```text
www.touziagent.com  CNAME  <cdn-provider-cname>
api.touziagent.com  A      119.28.156.125
touziagent.com      A      119.28.156.125
```

If `api.touziagent.com` is later protected by an API gateway or WAF, change only that record.

## nginx Server Block Template

This is a template only. Do not overwrite production nginx config without review.

```nginx
upstream finance_suite_backend {
    server 127.0.0.1:8000;
    keepalive 64;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.touziagent.com;

    ssl_certificate     /etc/letsencrypt/live/touziagent.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/touziagent.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    client_max_body_size 20m;

    add_header Access-Control-Allow-Origin      "https://www.touziagent.com" always;
    add_header Access-Control-Allow-Methods     "GET, POST, PUT, PATCH, DELETE, OPTIONS" always;
    add_header Access-Control-Allow-Headers     "Content-Type, Authorization" always;
    add_header Access-Control-Allow-Credentials "true" always;

    location / {
        if ($request_method = OPTIONS) {
            return 204;
        }

        add_header Cache-Control "no-store" always;

        proxy_pass http://finance_suite_backend;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

## Frontend `API_BASE_URL` Notes

Current relative calls such as:

```js
fetch('/api/login')
```

work through `www.touziagent.com/api/*`.

When switching to a dedicated API host, use a reviewed configuration layer:

```text
API_BASE_URL=https://api.touziagent.com
```

Then calls become:

```text
${API_BASE_URL}/login
${API_BASE_URL}/check-auth
${API_BASE_URL}/analyze
```

Migration caution:

- Do not hardcode API URLs in many frontend files.
- Keep a compatibility proxy on `www /api/*` until all clients are updated.
- Confirm browser cookies and CORS before removing the compatibility path.

## Cookie and CORS Notes

If auth cookies must be shared between `www` and `api`, set cookie domain deliberately:

```text
Domain=.touziagent.com
Secure
HttpOnly
SameSite=None
```

If cookies stay host-only, login and auth checks must consistently happen on the same host that owns the cookie.

CORS for browser calls from `www` to `api`:

```text
Access-Control-Allow-Origin: https://www.touziagent.com
Access-Control-Allow-Credentials: true
```

Do not combine credentialed requests with:

```text
Access-Control-Allow-Origin: *
```

