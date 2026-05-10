#!/usr/bin/env bash
# Lightweight public network, DNS, SNI, and origin health check.

set -u

DOMAIN="${DOMAIN:-touziagent.com}"
WWW_DOMAIN="${WWW_DOMAIN:-www.touziagent.com}"
ORIGIN_IP="${ORIGIN_IP:-119.28.156.125}"

PASS=0
FAIL=0
WARN=0

ok() {
  echo "OK   $1"
  PASS=$((PASS + 1))
}

fail() {
  echo "FAIL $1"
  FAIL=$((FAIL + 1))
}

warn() {
  echo "WARN $1"
  WARN=$((WARN + 1))
}

section() {
  echo
  echo "== $1 =="
}

curl_code() {
  HTTPS_PROXY= HTTP_PROXY= ALL_PROXY= NO_PROXY='*' \
    curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 8 --max-time 20 "$1" 2>/tmp/finance-suite-health.err || echo "000"
}

curl_verbose() {
  HTTPS_PROXY= HTTP_PROXY= ALL_PROXY= NO_PROXY='*' \
    curl "$@" 2>&1
}

section "DNS"
if command -v dig >/dev/null 2>&1; then
  A_ROOT="$(dig +short "$DOMAIN" A | tr '\n' ' ')"
  AAAA_ROOT="$(dig +short "$DOMAIN" AAAA | tr '\n' ' ')"
  A_WWW="$(dig +short "$WWW_DOMAIN" A | tr '\n' ' ')"
  AAAA_WWW="$(dig +short "$WWW_DOMAIN" AAAA | tr '\n' ' ')"
  echo "$DOMAIN A: ${A_ROOT:-<empty>}"
  echo "$DOMAIN AAAA: ${AAAA_ROOT:-<empty>}"
  echo "$WWW_DOMAIN A: ${A_WWW:-<empty>}"
  echo "$WWW_DOMAIN AAAA: ${AAAA_WWW:-<empty>}"

  if echo "$A_WWW" | grep -q "$ORIGIN_IP"; then
    ok "$WWW_DOMAIN A includes $ORIGIN_IP"
  else
    fail "$WWW_DOMAIN A does not include $ORIGIN_IP"
  fi

  if [ -z "$AAAA_WWW" ]; then
    ok "$WWW_DOMAIN has no AAAA record"
  else
    warn "$WWW_DOMAIN has AAAA record: $AAAA_WWW"
  fi
else
  warn "dig not installed; skipping DNS checks"
fi

section "Direct IPv4 without proxy"
IPV4_OUTPUT="$(curl_verbose -4vk "https://$WWW_DOMAIN/" -o /dev/null)"
echo "$IPV4_OUTPUT" | tail -40
if echo "$IPV4_OUTPUT" | grep -q 'HTTP/2 200\|HTTP/1.1 200\|HTTP/2 301\|HTTP/1.1 301'; then
  ok "IPv4 direct HTTPS returned HTTP success/redirect"
elif echo "$IPV4_OUTPUT" | grep -qi 'Connection reset by peer\|Recv failure'; then
  fail "IPv4 direct HTTPS reset during connection/TLS"
else
  fail "IPv4 direct HTTPS did not return success"
fi

section "IPv6 without proxy"
IPV6_OUTPUT="$(curl_verbose -6vk "https://$WWW_DOMAIN/" -o /dev/null)"
echo "$IPV6_OUTPUT" | tail -30
if echo "$IPV6_OUTPUT" | grep -q 'HTTP/2 200\|HTTP/1.1 200\|HTTP/2 301\|HTTP/1.1 301'; then
  ok "IPv6 HTTPS returned HTTP success/redirect"
elif echo "$IPV6_OUTPUT" | grep -qi 'Could not resolve host\|No route to host\|Network is unreachable\|Could not resolve proxy\|No address associated'; then
  ok "IPv6 unavailable as expected when no AAAA record exists"
else
  warn "IPv6 result needs review"
fi

section "Origin SNI"
ORIGIN_OUTPUT="$(curl_verbose -vk --resolve "$WWW_DOMAIN:443:$ORIGIN_IP" "https://$WWW_DOMAIN/" -o /dev/null)"
echo "$ORIGIN_OUTPUT" | tail -40
if echo "$ORIGIN_OUTPUT" | grep -q 'HTTP/2 200\|HTTP/1.1 200\|HTTP/2 301\|HTTP/1.1 301'; then
  ok "Origin SNI returned HTTP success/redirect"
elif echo "$ORIGIN_OUTPUT" | grep -qi 'Connection reset by peer\|Recv failure'; then
  fail "Origin SNI reset"
else
  fail "Origin SNI did not return success"
fi

section "Cache headers"
HOME_HEADERS="$(HTTPS_PROXY= HTTP_PROXY= ALL_PROXY= NO_PROXY='*' curl -sSI --connect-timeout 8 --max-time 20 "https://$WWW_DOMAIN/" 2>/dev/null || true)"
API_HEADERS="$(HTTPS_PROXY= HTTP_PROXY= ALL_PROXY= NO_PROXY='*' curl -sSI --connect-timeout 8 --max-time 20 "https://$WWW_DOMAIN/api/login" 2>/dev/null || true)"
echo "--- / ---"
echo "$HOME_HEADERS" | grep -i '^cache-control\|^http/' || true
echo "--- /api/login ---"
echo "$API_HEADERS" | grep -i '^cache-control\|^http/\|^allow' || true

if echo "$HOME_HEADERS" | grep -qi 'cache-control:.*no-cache'; then
  ok "HTML has no-cache header"
else
  warn "HTML cache-control should be reviewed"
fi

if echo "$API_HEADERS" | grep -qi 'cache-control:.*no-store'; then
  ok "API has no-store header"
else
  warn "API cache-control should be reviewed"
fi

section "Summary"
echo "PASS=$PASS WARN=$WARN FAIL=$FAIL"

if [ "$FAIL" -gt 0 ]; then
  echo "SUMMARY status=fail pass=$PASS warn=$WARN fail=$FAIL domain=$WWW_DOMAIN origin=$ORIGIN_IP"
  exit 1
fi

echo "SUMMARY status=ok pass=$PASS warn=$WARN fail=$FAIL domain=$WWW_DOMAIN origin=$ORIGIN_IP"
