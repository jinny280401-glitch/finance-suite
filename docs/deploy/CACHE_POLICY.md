# Cache Policy

This policy is intended for nginx origin headers and CDN cache rules.

## HTML

HTML must not be cached aggressively because it controls app bootstrapping, login redirects, and script references.

Recommended:

```text
Cache-Control: no-cache, no-store, must-revalidate, max-age=0
Pragma: no-cache
Expires: 0
```

Apply to:

```text
/
/*.html
/app/
/app/*.html
```

## API

API responses must not be cached by CDN or browsers unless explicitly reviewed.

Recommended:

```text
Cache-Control: no-store
```

Apply to:

```text
/api/*
api.touziagent.com/*
```

CDN must bypass cache for `/api/*` even if a response misses the header.

## Static Assets

Long cache is acceptable for assets that are versioned or safe to refresh manually.

Recommended for JS/CSS/images:

```text
Cache-Control: public, max-age=604800, immutable
```

For 30 days:

```text
Cache-Control: public, max-age=2592000, immutable
```

Apply to:

```text
*.js
*.css
*.png
*.jpg
*.jpeg
*.webp
*.gif
*.svg
*.ico
```

If filenames are not content-hashed, prefer 7 days and use CDN refresh after deployment.

## nginx Header Examples

Template only:

```nginx
location = / {
    try_files /index.html =404;
    add_header Cache-Control "no-cache, no-store, must-revalidate, max-age=0" always;
    add_header Pragma "no-cache" always;
    add_header Expires "0" always;
}

location ~* \.html$ {
    add_header Cache-Control "no-cache, no-store, must-revalidate, max-age=0" always;
    add_header Pragma "no-cache" always;
    add_header Expires "0" always;
}

location /api/ {
    add_header Cache-Control "no-store" always;
    proxy_pass http://backend;
}

location ~* \.(js|css|png|jpg|jpeg|webp|gif|svg|ico)$ {
    expires 7d;
    add_header Cache-Control "public, max-age=604800, immutable" always;
}
```

## CDN Refresh Strategy

After each deployment:

1. Refresh URL:
   ```text
   https://www.touziagent.com/
   https://www.touziagent.com/app/
   ```

2. Refresh directory if the CDN supports it:
   ```text
   https://www.touziagent.com/app/
   ```

3. Purge changed unversioned static assets.

4. Avoid full-site purge unless needed. Full purge can create origin traffic spikes.

## Verification

```bash
curl -I https://www.touziagent.com/
curl -I https://www.touziagent.com/app/
curl -I https://www.touziagent.com/api/check-auth
```

Expected:

```text
HTML:  no-cache/no-store
API:   no-store
Static assets: public max-age
```

