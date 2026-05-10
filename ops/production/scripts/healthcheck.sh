#!/usr/bin/env bash
# Production health check for Finance Suite.
# Designed for manual use, cron, or external monitoring.

set -u

DOMAIN="${DOMAIN:-touziagent.com}"
WWW_DOMAIN="${WWW_DOMAIN:-www.touziagent.com}"
API_DOMAIN="${API_DOMAIN:-api.touziagent.com}"
EXPECTED_ORIGIN_IP="${EXPECTED_ORIGIN_IP:-119.28.156.125}"
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8000}"
SERVICE_NAME="${SERVICE_NAME:-finance-suite.service}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

ok() {
  printf "${GREEN}OK${NC}   %s\n" "$1"
  PASS=$((PASS + 1))
}

fail() {
  printf "${RED}FAIL${NC} %s\n" "$1"
  FAIL=$((FAIL + 1))
}

warn() {
  printf "${YELLOW}WARN${NC} %s\n" "$1"
  WARN=$((WARN + 1))
}

section() {
  printf "\n== %s ==\n" "$1"
}

http_code() {
  local url="$1"
  HTTPS_PROXY= HTTP_PROXY= ALL_PROXY= NO_PROXY='*' \
    curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 8 --max-time 20 "$url" 2>/dev/null || echo "000"
}

check_http_ok() {
  local label="$1"
  local url="$2"
  local code
  code="$(http_code "$url")"
  echo "$label -> HTTP $code"
  case "$code" in
    200|204|301|302|401|405)
      ok "$label reachable"
      ;;
    *)
      fail "$label not healthy"
      ;;
  esac
}

section "DNS A"
if command -v dig >/dev/null 2>&1; then
  WWW_A="$(dig +short "$WWW_DOMAIN" A | tr '\n' ' ')"
  API_A="$(dig +short "$API_DOMAIN" A | tr '\n' ' ')"
  ROOT_A="$(dig +short "$DOMAIN" A | tr '\n' ' ')"

  echo "$DOMAIN A: ${ROOT_A:-<empty>}"
  echo "$WWW_DOMAIN A: ${WWW_A:-<empty>}"
  echo "$API_DOMAIN A: ${API_A:-<empty>}"

  if [ -n "$WWW_A" ]; then
    ok "$WWW_DOMAIN has A records"
  else
    fail "$WWW_DOMAIN has no A record"
  fi

  if echo "$API_A" | grep -q "$EXPECTED_ORIGIN_IP"; then
    ok "$API_DOMAIN points to origin $EXPECTED_ORIGIN_IP"
  elif [ -n "$API_A" ]; then
    warn "$API_DOMAIN A does not include expected origin $EXPECTED_ORIGIN_IP"
  else
    warn "$API_DOMAIN has no A record"
  fi
else
  fail "dig is not installed"
fi

section "HTTPS endpoints"
check_http_ok "homepage" "https://$WWW_DOMAIN/"
check_http_ok "app" "https://$WWW_DOMAIN/app/"

API_CHECK_CODE="$(http_code "https://$WWW_DOMAIN/api/check-auth")"
if [ "$API_CHECK_CODE" = "000" ] || [ "$API_CHECK_CODE" = "404" ]; then
  API_HEALTH_CODE="$(http_code "https://$WWW_DOMAIN/api/health")"
  echo "/api/check-auth -> HTTP $API_CHECK_CODE"
  echo "/api/health -> HTTP $API_HEALTH_CODE"
  case "$API_HEALTH_CODE" in
    200|204|401|405)
      ok "API health endpoint reachable"
      ;;
    *)
      fail "No healthy /api/check-auth or /api/health endpoint"
      ;;
  esac
else
  echo "/api/check-auth -> HTTP $API_CHECK_CODE"
  case "$API_CHECK_CODE" in
    200|204|401|405)
      ok "API check-auth endpoint reachable"
      ;;
    *)
      fail "/api/check-auth unhealthy"
      ;;
  esac
fi

section "Local backend"
check_http_ok "backend root" "$BACKEND_URL/"

LOCAL_CHECK_CODE="$(http_code "$BACKEND_URL/api/check-auth")"
if [ "$LOCAL_CHECK_CODE" = "000" ] || [ "$LOCAL_CHECK_CODE" = "404" ]; then
  LOCAL_HEALTH_CODE="$(http_code "$BACKEND_URL/api/health")"
  echo "local /api/check-auth -> HTTP $LOCAL_CHECK_CODE"
  echo "local /api/health -> HTTP $LOCAL_HEALTH_CODE"
  case "$LOCAL_HEALTH_CODE" in
    200|204|401|405)
      ok "local API health endpoint reachable"
      ;;
    *)
      fail "local API endpoint unhealthy"
      ;;
  esac
else
  echo "local /api/check-auth -> HTTP $LOCAL_CHECK_CODE"
  case "$LOCAL_CHECK_CODE" in
    200|204|401|405)
      ok "local check-auth endpoint reachable"
      ;;
    *)
      fail "local check-auth unhealthy"
      ;;
  esac
fi

section "nginx"
if command -v systemctl >/dev/null 2>&1; then
  if systemctl is-active --quiet nginx; then
    ok "nginx service active"
  else
    fail "nginx service not active"
  fi
else
  warn "systemctl unavailable; cannot check nginx service"
fi

if command -v nginx >/dev/null 2>&1; then
  if sudo nginx -t >/tmp/finance-suite-nginx-check.log 2>&1; then
    ok "nginx -t passed"
  else
    fail "nginx -t failed"
    tail -20 /tmp/finance-suite-nginx-check.log
  fi
else
  warn "nginx command unavailable"
fi
rm -f /tmp/finance-suite-nginx-check.log 2>/dev/null || true

section "systemd service"
if command -v systemctl >/dev/null 2>&1; then
  if systemctl is-active --quiet "$SERVICE_NAME"; then
    ok "$SERVICE_NAME active"
  else
    fail "$SERVICE_NAME not active"
    systemctl status "$SERVICE_NAME" --no-pager | tail -20 || true
  fi
else
  fail "systemctl unavailable"
fi

section "Summary"
echo "PASS=$PASS WARN=$WARN FAIL=$FAIL"

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi

exit 0

