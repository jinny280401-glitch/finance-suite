# CDN Setup

This plan routes the public website through CDN while keeping the API origin separate.

## Target Routing

```text
www.touziagent.com  -> CDN
api.touziagent.com  -> direct origin or separate API protection
origin IP           -> 119.28.156.125
origin protocol     -> HTTPS
```

Do not put `api.touziagent.com` behind the same static-site cache policy as `www.touziagent.com`.

## DNS

Recommended DNS after CDN is created:

```text
www.touziagent.com  CNAME  <cdn-provider-cname>
api.touziagent.com  A      119.28.156.125
touziagent.com      A      119.28.156.125
```

If the CDN provider supports apex acceleration, `touziagent.com` may point to CDN too, but the simpler setup is to keep apex on the origin and redirect it to `www`.

## Origin Settings

```text
Origin address:   119.28.156.125
Origin protocol:  HTTPS
Origin port:      443
Origin Host:      www.touziagent.com
Origin SNI:       www.touziagent.com
```

Keep the Let's Encrypt certificate on the origin valid for:

```text
touziagent.com
www.touziagent.com
api.touziagent.com
```

## Cache Rules

Order matters. Put API and HTML rules before broad static rules.

```text
Path /api/*
  Cache: bypass / no-cache
  Forward cookies: yes
  Forward query string: yes
  Forward method: GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS

Path /
  Cache: no-cache

Path *.html
  Cache: no-cache

Path /app/*
  Cache: no-cache unless the HTML filenames are versioned

Path *.js, *.css
  Cache: 7-30 days

Path *.png, *.jpg, *.jpeg, *.webp, *.gif, *.svg, *.ico
  Cache: 7-30 days
```

Recommended headers:

```text
HTML:             Cache-Control: no-cache, no-store, must-revalidate, max-age=0
API:              Cache-Control: no-store
JS/CSS/images:    Cache-Control: public, max-age=604800, immutable
```

## HTTPS

Enable HTTPS on the CDN edge for `www.touziagent.com`.

Use HTTPS for origin pull. Do not downgrade CDN-to-origin traffic to HTTP.

## Validation

From a client network:

```bash
dig +short www.touziagent.com A
dig +short www.touziagent.com CNAME
curl -I https://www.touziagent.com/
curl -I https://www.touziagent.com/app/
curl -I https://www.touziagent.com/api/check-auth
```

Expected:

```text
www resolves to CDN, not necessarily 119.28.156.125
/ and /app/ return no-cache/no-store HTML headers
/api/* returns no-store and is not cached
```

Origin validation:

```bash
curl -vk --resolve www.touziagent.com:443:119.28.156.125 https://www.touziagent.com/ -o /dev/null
```

