#!/usr/bin/env bash
# D29 Content Consistency Check — for C to run via SSH jump host
# Compares /app/index.html fingerprint between local and production.
# If title, h1, asset list, sha256 all match → same deployed version.

set -uo pipefail
LOCAL=/Users/Zhuanz/finance-suite/app/index.html
REMOTE_PATH=/home/ubuntu/finance-suite-web/static/app/index.html
JUMP='admin@8.138.2.55'

echo "=== LOCAL fingerprint ==="
echo "title: $(grep -oE '<title>[^<]+</title>' "$LOCAL" | head -1)"
echo "h1:    $(grep -oE '<h1[^>]*>[^<]+</h1>' "$LOCAL" | head -1)"
echo "css:   $(grep -oE 'href="[^"]*\.css[^"]*"' "$LOCAL" | sort | tr '\n' ' ')"
echo "js:    $(grep -oE 'src="[^"]*\.js[^"]*"' "$LOCAL" | sort | tr '\n' ' ')"
echo "size:  $(stat -f '%z' "$LOCAL")"
echo "sha:   $(shasum -a 256 "$LOCAL" | awk '{print $1}')"

echo
echo "=== PRODUCTION fingerprint (via jump host) ==="
ssh "$JUMP" ssh ubuntu@119.28.156.125 bash -s <<EOF
echo "title: \$(grep -oE '<title>[^<]+</title>' ${REMOTE_PATH} | head -1)"
echo "h1:    \$(grep -oE '<h1[^>]*>[^<]+</h1>' ${REMOTE_PATH} | head -1)"
echo "css:   \$(grep -oE 'href=\"[^\"]*\\.css[^\"]*\"' ${REMOTE_PATH} | sort | tr '\n' ' ')"
echo "js:    \$(grep -oE 'src=\"[^\"]*\\.js[^\"]*\"' ${REMOTE_PATH} | sort | tr '\n' ' ')"
echo "size:  \$(stat -c '%s' ${REMOTE_PATH})"
echo "sha:   \$(sha256sum ${REMOTE_PATH} | awk '{print \$1}')"
EOF

echo
echo "=== Verdict interpretation ==="
echo "  ALL MATCH (title/h1/css/js/sha) → same deployed version, safe"
echo "  title + h1 match but size differs → version drift, NOT safe for demo"
echo "  size matches but title/h1 differ → same bytes different content (cache?), NOT safe"