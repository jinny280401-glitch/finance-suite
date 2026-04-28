#!/bin/bash
# Finance Suite 线上健康检查脚本
# 用法: ./healthcheck.sh [domain] [backend_port]
# 示例: ./healthcheck.sh touziagent.com 8000

set -e

DOMAIN="${1:-touziagent.com}"
BACKEND_PORT="${2:-8000}"
EXPECTED_IP="119.28.156.125"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 结果统计
PASS=0
FAIL=0
WARN=0

print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASS++))
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((FAIL++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARN++))
}

# ============================================================
# 一、域名解析检查
# ============================================================
print_header "🧩 一、域名解析检查"

DNS_IP=$(dig +short "$DOMAIN" | head -1)
if [ "$DNS_IP" = "$EXPECTED_IP" ]; then
    check_pass "DNS 解析正确: $DNS_IP"
else
    check_fail "DNS 解析错误: 期望 $EXPECTED_IP, 实际 $DNS_IP"
fi

# ============================================================
# 二、HTTPS 访问检查
# ============================================================
print_header "🌐 二、HTTPS 访问检查"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://$DOMAIN" --max-time 10 || echo "000")
if [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    check_pass "HTTP → HTTPS 重定向正常 ($HTTP_CODE)"
elif [ "$HTTP_CODE" = "200" ]; then
    check_warn "HTTP 直接返回 200，建议强制 HTTPS"
else
    check_fail "HTTP 访问异常: $HTTP_CODE"
fi

HTTPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN" --max-time 10 || echo "000")
if [ "$HTTPS_CODE" = "200" ]; then
    check_pass "HTTPS 访问正常 (200)"
else
    check_fail "HTTPS 访问失败: $HTTPS_CODE"
fi

# ============================================================
# 三、SSL 证书检查
# ============================================================
print_header "🔒 三、SSL 证书检查"

SSL_CHECK=$(echo | timeout 5 openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>/dev/null | grep "Verify return code")
if echo "$SSL_CHECK" | grep -q "0 (ok)"; then
    check_pass "SSL 证书有效"
else
    check_fail "SSL 证书问题: $SSL_CHECK"
fi

# ============================================================
# 四、Nginx 配置检查（仅服务器端）
# ============================================================
print_header "🖥 四、Nginx 配置检查"

if command -v nginx &> /dev/null; then
    if sudo nginx -t &> /dev/null; then
        check_pass "Nginx 配置语法正确"
    else
        check_fail "Nginx 配置语法错误"
        sudo nginx -t 2>&1 | tail -5
    fi

    ERROR_COUNT=$(sudo tail -100 /var/log/nginx/error.log 2>/dev/null | grep -c "error" || echo "0")
    if [ "$ERROR_COUNT" -lt 5 ]; then
        check_pass "Nginx 错误日志正常 ($ERROR_COUNT 条)"
    else
        check_warn "Nginx 错误日志较多 ($ERROR_COUNT 条)"
        sudo tail -10 /var/log/nginx/error.log
    fi
else
    check_warn "未检测到 Nginx（可能在本地环境）"
fi

# ============================================================
# 五、API 反向代理检查（核心）
# ============================================================
print_header "🔁 五、API 反向代理检查"

API_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/api/check-auth" --max-time 10 || echo "000")
if [ "$API_CODE" = "200" ]; then
    check_pass "外网 API 可达 (/api/check-auth → 200)"
elif [ "$API_CODE" = "401" ]; then
    check_pass "外网 API 可达 (/api/check-auth → 401 未登录，正常)"
else
    check_fail "外网 API 不可达: $API_CODE"
fi

if command -v curl &> /dev/null && [ -f /proc/net/tcp ]; then
    BACKEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$BACKEND_PORT/api/check-auth" --max-time 5 || echo "000")
    if [ "$BACKEND_CODE" = "200" ] || [ "$BACKEND_CODE" = "401" ]; then
        check_pass "后端服务可达 (127.0.0.1:$BACKEND_PORT → $BACKEND_CODE)"
    else
        check_fail "后端服务不可达: $BACKEND_CODE"
    fi
fi

# ============================================================
# 六、后端进程检查
# ============================================================
print_header "⚙️  六、后端进程检查"

if ps aux | grep -E "python.*app.py|python.*main.py|gunicorn|uvicorn" | grep -v grep > /dev/null; then
    check_pass "后端进程运行中"
    ps aux | grep -E "python.*app.py|python.*main.py|gunicorn|uvicorn" | grep -v grep | head -3
else
    check_fail "后端进程未运行"
fi

if command -v netstat &> /dev/null; then
    if netstat -tlnp 2>/dev/null | grep ":$BACKEND_PORT" > /dev/null; then
        check_pass "后端端口监听正常 (:$BACKEND_PORT)"
    else
        check_fail "后端端口未监听 (:$BACKEND_PORT)"
    fi
fi

# ============================================================
# 七、登录接口检查（核心）
# ============================================================
print_header "🔐 七、登录接口检查"

LOGIN_RESPONSE=$(curl -s -X POST "https://$DOMAIN/api/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' \
    --max-time 10 || echo '{"error":"timeout"}')

if echo "$LOGIN_RESPONSE" | grep -q "success"; then
    if echo "$LOGIN_RESPONSE" | grep -q '"success":true'; then
        check_warn "登录接口返回成功（测试账号可能存在）"
    else
        check_pass "登录接口正常响应（401 预期）"
    fi
elif echo "$LOGIN_RESPONSE" | grep -q "账号或密码"; then
    check_pass "登录接口正常响应（返回错误提示）"
else
    check_fail "登录接口异常: $LOGIN_RESPONSE"
fi

# ============================================================
# 八、数据库检查（仅服务器端）
# ============================================================
print_header "📦 八、数据库检查"

DB_PATH="/home/ubuntu/finance-suite/finance_suite.db"
if [ -f "$DB_PATH" ]; then
    check_pass "数据库文件存在: $DB_PATH"

    USER_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")
    if [ "$USER_COUNT" -gt 0 ]; then
        check_pass "用户表正常 ($USER_COUNT 个用户)"
    else
        check_fail "用户表为空或不存在"
    fi
else
    check_warn "数据库文件不存在（可能在本地环境）"
fi

# ============================================================
# 九、静态资源检查
# ============================================================
print_header "📦 九、静态资源检查"

INDEX_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/" --max-time 10 || echo "000")
if [ "$INDEX_CODE" = "200" ]; then
    check_pass "首页可访问 (200)"
else
    check_fail "首页访问失败: $INDEX_CODE"
fi

APP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/app/" --max-time 10 || echo "000")
if [ "$APP_CODE" = "200" ]; then
    check_pass "工作台可访问 (/app/ → 200)"
else
    check_warn "工作台访问异常: $APP_CODE（可能需要登录）"
fi

# ============================================================
# 十、前端配置检查
# ============================================================
print_header "🧠 十、前端配置检查"

STATIC_DIR="/home/ubuntu/finance-suite-web/static"
if [ -d "$STATIC_DIR" ]; then
    LOCALHOST_COUNT=$(grep -r "localhost" "$STATIC_DIR" 2>/dev/null | grep -v ".git" | wc -l || echo "0")
    if [ "$LOCALHOST_COUNT" -eq 0 ]; then
        check_pass "前端无 localhost 硬编码"
    else
        check_fail "前端存在 localhost 硬编码 ($LOCALHOST_COUNT 处)"
        grep -rn "localhost" "$STATIC_DIR" 2>/dev/null | grep -v ".git" | head -5
    fi
else
    check_warn "静态文件目录不存在（可能在本地环境）"
fi

# ============================================================
# 总结
# ============================================================
print_header "🎯 检查总结"

echo -e "通过: ${GREEN}$PASS${NC}"
echo -e "警告: ${YELLOW}$WARN${NC}"
echo -e "失败: ${RED}$FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ 系统健康，可以上线${NC}"
    exit 0
elif [ $FAIL -le 2 ]; then
    echo -e "${YELLOW}⚠️  存在少量问题，建议修复后上线${NC}"
    exit 1
else
    echo -e "${RED}❌ 存在严重问题，不建议上线${NC}"
    exit 2
fi
