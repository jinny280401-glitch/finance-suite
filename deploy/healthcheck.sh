#!/bin/bash
# Finance Suite 登录与链路健康检查脚本
# 用法:
#   PASSWORD='xxx' ./healthcheck.sh [domain] [backend_port] [username]
# 或
#   ./healthcheck.sh [domain] [backend_port] [username]   # 运行时静默输入密码

set -u

DOMAIN="${1:-touziagent.com}"
BACKEND_PORT="${2:-8000}"
CHECK_USER="${3:-zhuanz}"
EXPECTED_IP="119.28.156.125"
DB_PATH_DEFAULT="/home/ubuntu/finance-suite/finance_suite.db"

# 密码来源：优先环境变量 PASSWORD，否则运行时 read -s
PASSWORD_VALUE="${PASSWORD:-}"
if [ -z "$PASSWORD_VALUE" ]; then
  echo "请输入用于登录检查的密码（不会回显，不会写入历史）:"
  read -s PASSWORD_VALUE
  echo
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

DNS_OK=0
HTTPS_OK=0
NGINX_OK=0
LOCAL_BACKEND_OK=0
API_CHECK_AUTH_OK=0
EXT_LOGIN_CODE="NA"
LOC_LOGIN_CODE="NA"
USER_EXISTS="unknown"
HASH_MATCH="unknown"
ROUTE_PROBLEM=0
PROXY_PROBLEM=0
NETWORK_PROBLEM=0
DB_USER_PROBLEM=0
HASH_PROBLEM=0
SESSION_PROBLEM=0

print_header() {
  echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

ok() {
  echo -e "${GREEN}✅ $1${NC}"
  PASS=$((PASS+1))
}

fail() {
  echo -e "${RED}❌ $1${NC}"
  FAIL=$((FAIL+1))
}

warn() {
  echo -e "${YELLOW}⚠️  $1${NC}"
  WARN=$((WARN+1))
}

has_cmd() {
  command -v "$1" >/dev/null 2>&1
}

http_code() {
  # $1=url
  curl -sS -o /tmp/healthcheck_body.$$ -w "%{http_code}" "$1" --max-time 12 2>/tmp/healthcheck_err.$$ || echo "000"
}

post_login_code() {
  # $1=url
  curl -sS -o /tmp/healthcheck_login_body.$$ -w "%{http_code}" \
    -X POST "$1" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$CHECK_USER\",\"password\":\"$PASSWORD_VALUE\"}" \
    --max-time 12 2>/tmp/healthcheck_login_err.$$ || echo "000"
}

cleanup_tmp() {
  rm -f /tmp/healthcheck_body.$$ /tmp/healthcheck_err.$$ /tmp/healthcheck_login_body.$$ /tmp/healthcheck_login_err.$$ 2>/dev/null || true
}
trap cleanup_tmp EXIT

print_header "1) DNS 检查"
if has_cmd dig; then
  DNS_IPS=$(dig +short "$DOMAIN" | tr '\n' ' ')
  DNS_MAIN=$(echo "$DNS_IPS" | awk '{print $1}')
  echo "DNS 结果: ${DNS_IPS:-<空>}"
  if [ "$DNS_MAIN" = "$EXPECTED_IP" ]; then
    ok "DNS 指向正确: $EXPECTED_IP"
    DNS_OK=1
  elif [ -z "$DNS_MAIN" ]; then
    fail "DNS 无解析结果"
    NETWORK_PROBLEM=1
  else
    fail "DNS 指向错误: 期望 $EXPECTED_IP, 实际 $DNS_MAIN"
    NETWORK_PROBLEM=1
  fi
else
  warn "未安装 dig，跳过 DNS 检查"
fi

print_header "2) 四入口与 HTTPS 检查"
URLS=(
  "http://$DOMAIN"
  "https://$DOMAIN"
  "http://www.$DOMAIN"
  "https://www.$DOMAIN"
)
for u in "${URLS[@]}"; do
  c=$(http_code "$u")
  echo "$u -> HTTP $c"
done

HTTPS_CODE=$(http_code "https://$DOMAIN")
if [ "$HTTPS_CODE" = "200" ] || [ "$HTTPS_CODE" = "301" ]; then
  ok "HTTPS 返回正常: $HTTPS_CODE"
  HTTPS_OK=1
else
  fail "HTTPS 异常: $HTTPS_CODE"
  NETWORK_PROBLEM=1
fi

print_header "3) Nginx 检查"
if has_cmd nginx; then
  if sudo nginx -t >/tmp/nginx_test_out.$$ 2>&1; then
    ok "nginx -t 通过（syntax is ok / test is successful）"
    NGINX_OK=1
  else
    fail "nginx -t 失败"
    cat /tmp/nginx_test_out.$$ | tail -20
    PROXY_PROBLEM=1
  fi
  rm -f /tmp/nginx_test_out.$$ 2>/dev/null || true

  if [ -f /var/log/nginx/error.log ]; then
    echo "最近 nginx error.log（尾部 20 行）:"
    sudo tail -n 20 /var/log/nginx/error.log || true
  else
    warn "未找到 /var/log/nginx/error.log"
  fi
else
  warn "当前环境无 nginx 命令，跳过 nginx 检查"
fi

print_header "4) FastAPI/后端监听 8000 检查"
if has_cmd netstat; then
  LISTEN_LINE=$(netstat -tlnp 2>/dev/null | grep ":$BACKEND_PORT" || true)
elif has_cmd ss; then
  LISTEN_LINE=$(ss -tlnp 2>/dev/null | grep ":$BACKEND_PORT" || true)
else
  LISTEN_LINE=""
  warn "无 netstat/ss，无法检查端口监听"
fi

if [ -n "${LISTEN_LINE:-}" ]; then
  echo "$LISTEN_LINE"
  ok "检测到端口 $BACKEND_PORT 在监听"
  LOCAL_BACKEND_OK=1
else
  fail "未检测到端口 $BACKEND_PORT 监听"
  ROUTE_PROBLEM=1
fi

print_header "5) /api/check-auth 路由检查（外网 + 本机）"
EXT_CHECK_AUTH=$(http_code "https://$DOMAIN/api/check-auth")
LOC_CHECK_AUTH=$(http_code "http://127.0.0.1:$BACKEND_PORT/api/check-auth")
echo "外网 /api/check-auth -> $EXT_CHECK_AUTH"
echo "本机 /api/check-auth -> $LOC_CHECK_AUTH"

if [ "$EXT_CHECK_AUTH" = "200" ] || [ "$EXT_CHECK_AUTH" = "401" ]; then
  ok "外网 /api/check-auth 存在且可访问"
  API_CHECK_AUTH_OK=1
elif [ "$EXT_CHECK_AUTH" = "404" ]; then
  fail "外网 /api/check-auth = 404（后端路由不存在或代理路径错）"
  PROXY_PROBLEM=1
  ROUTE_PROBLEM=1
elif [ "$EXT_CHECK_AUTH" = "502" ] || [ "$EXT_CHECK_AUTH" = "503" ] || [ "$EXT_CHECK_AUTH" = "504" ]; then
  fail "外网 /api/check-auth = $EXT_CHECK_AUTH（nginx 到后端链路失败）"
  PROXY_PROBLEM=1
else
  fail "外网 /api/check-auth 异常: $EXT_CHECK_AUTH"
fi

if [ "$LOC_CHECK_AUTH" = "200" ] || [ "$LOC_CHECK_AUTH" = "401" ]; then
  ok "本机 /api/check-auth 存在且可访问"
elif [ "$LOC_CHECK_AUTH" = "404" ]; then
  fail "本机 /api/check-auth = 404（后端未注册该路由）"
  ROUTE_PROBLEM=1
elif [ "$LOC_CHECK_AUTH" = "000" ]; then
  fail "本机 /api/check-auth 无法连接（后端可能未运行）"
  ROUTE_PROBLEM=1
else
  fail "本机 /api/check-auth 异常: $LOC_CHECK_AUTH"
fi

print_header "6) /api/login 登录接口检查（外网 + 本机）"
EXT_LOGIN_CODE=$(post_login_code "https://$DOMAIN/api/login")
EXT_LOGIN_BODY=$(cat /tmp/healthcheck_login_body.$$ 2>/dev/null || true)
LOC_LOGIN_CODE=$(post_login_code "http://127.0.0.1:$BACKEND_PORT/api/login")
LOC_LOGIN_BODY=$(cat /tmp/healthcheck_login_body.$$ 2>/dev/null || true)

echo "外网 /api/login -> $EXT_LOGIN_CODE"
echo "本机 /api/login -> $LOC_LOGIN_CODE"

# 外网 login code 解释
case "$EXT_LOGIN_CODE" in
  200)
    ok "外网登录返回 200：认证成功，接口可用"
    ;;
  401)
    warn "外网登录返回 401：账号不存在 / 密码错误 / hash 不匹配（重点查数据库与哈希）"
    ;;
  404)
    fail "外网登录返回 404：nginx 代理路径或后端路由缺失"
    PROXY_PROBLEM=1
    ROUTE_PROBLEM=1
    ;;
  500)
    fail "外网登录返回 500：后端代码或数据库异常"
    ROUTE_PROBLEM=1
    ;;
  502|503|504)
    fail "外网登录返回 $EXT_LOGIN_CODE：nginx 到后端不可达"
    PROXY_PROBLEM=1
    ;;
  000)
    fail "外网登录超时/连接失败（网络或证书问题）"
    NETWORK_PROBLEM=1
    ;;
  *)
    warn "外网登录返回非常见状态: $EXT_LOGIN_CODE"
    ;;
esac

# 本机 login code 解释
case "$LOC_LOGIN_CODE" in
  200)
    ok "本机登录返回 200：后端认证逻辑可用"
    ;;
  401)
    warn "本机登录返回 401：后端可达，但账号/密码校验失败"
    ;;
  404)
    fail "本机登录返回 404：后端未注册 /api/login"
    ROUTE_PROBLEM=1
    ;;
  500)
    fail "本机登录返回 500：后端认证流程内部错误"
    ROUTE_PROBLEM=1
    ;;
  000)
    fail "本机登录无法连接：后端未监听或进程挂了"
    ROUTE_PROBLEM=1
    ;;
  *)
    warn "本机登录返回非常见状态: $LOC_LOGIN_CODE"
    ;;
esac

print_header "7) sqlite 用户检查（username='$CHECK_USER'）"
DB_PATH="$DB_PATH_DEFAULT"
if [ -f "$DB_PATH" ] && has_cmd sqlite3; then
  USER_ROW=$(sqlite3 "$DB_PATH" "SELECT id, username, tier FROM users WHERE username='$CHECK_USER' LIMIT 1;" 2>/dev/null || true)
  if [ -n "$USER_ROW" ]; then
    ok "数据库查到用户: $USER_ROW"
    USER_EXISTS="yes"
  else
    fail "数据库未查到 username='$CHECK_USER'"
    USER_EXISTS="no"
    DB_USER_PROBLEM=1
  fi
else
  warn "未找到数据库文件或 sqlite3 不可用（DB_PATH=$DB_PATH）"
fi

print_header "8) 密码 hash 校验检查（401 时关键）"
if [ "$USER_EXISTS" = "yes" ] && [ -f "$DB_PATH" ] && has_cmd sqlite3 && has_cmd python3; then
  DB_HASH=$(sqlite3 "$DB_PATH" "SELECT password_hash FROM users WHERE username='$CHECK_USER' LIMIT 1;" 2>/dev/null || true)
  if [ -n "$DB_HASH" ]; then
    CALC_HASH=$(python3 - <<PY
import hashlib
pwd = '''$PASSWORD_VALUE'''
print(hashlib.sha256(pwd.encode()).hexdigest())
PY
)
    if [ "$DB_HASH" = "$CALC_HASH" ]; then
      ok "密码 hash 一致（sha256）"
      HASH_MATCH="yes"
    else
      fail "密码 hash 不一致（数据库 hash 与输入密码 sha256 不匹配）"
      HASH_MATCH="no"
      HASH_PROBLEM=1
    fi
  else
    warn "未读取到数据库 password_hash 字段"
  fi
else
  warn "跳过 hash 校验（用户不存在或环境不满足）"
fi

print_header "9) login 代码字段检查（username vs email）"
AUTH_FILE_CANDIDATES=(
  "/home/ubuntu/finance-suite/server_scripts/auth.py"
  "/Users/Zhuanz/finance-suite/server_scripts/auth.py"
)
AUTH_FILE=""
for f in "${AUTH_FILE_CANDIDATES[@]}"; do
  if [ -f "$f" ]; then
    AUTH_FILE="$f"
    break
  fi
done

if [ -n "$AUTH_FILE" ]; then
  echo "使用 auth 文件: $AUTH_FILE"
  if grep -q "data.get('username'" "$AUTH_FILE" || grep -q 'data.get("username"' "$AUTH_FILE"; then
    ok "后端 login 从请求体读取 username"
  else
    warn "后端 login 未明显读取 username，需人工确认"
  fi
  if grep -q "data.get('email'" "$AUTH_FILE" || grep -q 'data.get("email"' "$AUTH_FILE"; then
    warn "后端 login 也涉及 email 字段，需确认前端传参一致"
  else
    ok "后端 login 未使用 email 字段（当前逻辑应为 username）"
  fi
else
  warn "未找到 auth.py，无法自动检查 username/email 字段"
fi

print_header "10) 前端传参字段检查（username vs email）"
FRONT_FILE_CANDIDATES=(
  "/home/ubuntu/finance-suite-web/static/index.html"
  "/Users/Zhuanz/finance-suite/index.html"
)
FRONT_FILE=""
for f in "${FRONT_FILE_CANDIDATES[@]}"; do
  if [ -f "$f" ]; then
    FRONT_FILE="$f"
    break
  fi
done

if [ -n "$FRONT_FILE" ]; then
  echo "使用前端文件: $FRONT_FILE"
  if grep -q "username" "$FRONT_FILE"; then
    ok "前端请求体包含 username"
  else
    warn "前端未明显包含 username 字段"
  fi
  if grep -q "email" "$FRONT_FILE"; then
    warn "前端包含 email 字段，需确认后端是否兼容"
  else
    ok "前端未明显传 email（与 username 登录逻辑一致）"
  fi
else
  warn "未找到登录前端文件，无法自动检查字段"
fi

print_header "11) 数据库路径一致性检查"
if [ -n "$AUTH_FILE" ]; then
  if grep -q "finance_suite.db" "$AUTH_FILE"; then
    AUTH_DB_PATH=$(grep -E "DB_PATH\s*=|finance_suite.db" "$AUTH_FILE" | head -n 2)
    echo "auth.py 数据库路径定义片段:"
    echo "$AUTH_DB_PATH"
    if [ -f "$DB_PATH_DEFAULT" ]; then
      ok "默认数据库路径存在: $DB_PATH_DEFAULT"
    else
      warn "默认数据库路径不存在: $DB_PATH_DEFAULT，需核对线上实际路径"
      DB_USER_PROBLEM=1
    fi
  else
    warn "auth.py 未找到 finance_suite.db 定义，需人工核对"
  fi
else
  warn "无 auth.py，跳过数据库路径一致性检查"
fi

print_header "12) journalctl 登录错误检查"
if has_cmd journalctl; then
  echo "最近 80 行服务日志（筛 login/error/auth）:"
  journalctl -u finance-suite-web -n 80 --no-pager 2>/dev/null | grep -Ei "login|auth|error|traceback|sqlite|exception" || echo "(未匹配到关键字)"

  if journalctl -u finance-suite-web -n 120 --no-pager 2>/dev/null | grep -Ei "sqlite|no such table|operationalerror|traceback|exception" >/dev/null; then
    warn "日志中出现数据库/异常关键字"
    ROUTE_PROBLEM=1
  else
    ok "日志未发现明显数据库异常关键字"
  fi
else
  warn "无 journalctl，跳过日志检查"
fi

print_header "13) 401 场景专项判断"
if [ "$EXT_LOGIN_CODE" = "401" ] || [ "$LOC_LOGIN_CODE" = "401" ]; then
  echo "检测到登录 401，执行专项结论："

  if [ "$USER_EXISTS" = "no" ]; then
    fail "401 根因倾向：数据库账号问题（用户不存在）"
    DB_USER_PROBLEM=1
  fi

  if [ "$HASH_MATCH" = "no" ]; then
    fail "401 根因倾向：密码/hash 校验问题（hash 不匹配）"
    HASH_PROBLEM=1
  fi

  if [ "$USER_EXISTS" = "yes" ] && [ "$HASH_MATCH" = "yes" ] && [ "$LOC_LOGIN_CODE" = "401" ]; then
    warn "用户存在且 hash 匹配仍 401：请重点检查 username/email 字段映射、前后端传参、数据库实际路径"
  fi
fi

print_header "最终结论（根因分类）"
echo -e "通过: ${GREEN}$PASS${NC}"
echo -e "警告: ${YELLOW}$WARN${NC}"
echo -e "失败: ${RED}$FAIL${NC}"

# 结论优先级
if [ "$NETWORK_PROBLEM" -eq 1 ] || [ "$DNS_OK" -eq 0 ] || [ "$HTTPS_OK" -eq 0 ]; then
  echo -e "\n${RED}结论: 网络问题${NC}"
fi

if [ "$PROXY_PROBLEM" -eq 1 ] || { [ "$LOC_CHECK_AUTH" = "200" -o "$LOC_CHECK_AUTH" = "401" ] && [ "$EXT_CHECK_AUTH" != "200" ] && [ "$EXT_CHECK_AUTH" != "401" ]; }; then
  echo -e "${RED}结论: nginx 代理问题${NC}"
fi

if [ "$ROUTE_PROBLEM" -eq 1 ] || [ "$LOC_CHECK_AUTH" = "404" ] || [ "$LOC_LOGIN_CODE" = "404" ] || [ "$LOC_LOGIN_CODE" = "500" ]; then
  echo -e "${RED}结论: 后端路由问题${NC}"
fi

if [ "$DB_USER_PROBLEM" -eq 1 ]; then
  echo -e "${RED}结论: 数据库账号问题${NC}"
fi

if [ "$HASH_PROBLEM" -eq 1 ]; then
  echo -e "${RED}结论: 密码/hash 校验问题${NC}"
fi

if [ "$EXT_LOGIN_CODE" = "200" ] && [ "$LOC_LOGIN_CODE" = "200" ]; then
  # 登录成功但用户仍感知失败，多半是 cookie/session
  SESSION_PROBLEM=1
fi
if [ "$SESSION_PROBLEM" -eq 1 ]; then
  echo -e "${YELLOW}结论: session/cookie/secret_key 问题（接口登录成功但会话未保持）${NC}"
fi

if [ "$FAIL" -eq 0 ]; then
  echo -e "\n${GREEN}总体判断: 链路健康，可上线${NC}"
  exit 0
else
  echo -e "\n${YELLOW}总体判断: 存在问题，请按上方分类修复${NC}"
  exit 1
fi
