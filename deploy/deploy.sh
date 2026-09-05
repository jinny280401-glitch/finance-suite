#!/bin/bash
# Finance Suite 一键部署脚本
# 在腾讯云 Ubuntu-ZjOV 服务器上执行
# 功能：拉取最新页面 + 更新 nginx 配置

set -e

echo "===== 1. 拉取最新页面文件 ====="

# 确保目录存在
mkdir -p /home/ubuntu/finance-suite-web/static/app/

# ---- 场景页面（从 scenarios/*/page.html 拉取）----
declare -A SCENARIO_PAGES=(
  [stock]=scenarios/stock/page.html
  [macro]=scenarios/macro/page.html
  [auction]=scenarios/auction/page.html
  [video]=scenarios/video/page.html
  [meeting]=scenarios/meeting/page.html
  [deep-research]=scenarios/industry/page.html
)
for page in "${!SCENARIO_PAGES[@]}"; do
  src="${SCENARIO_PAGES[$page]}"
  curl -sL "https://raw.githubusercontent.com/jinny280401-glitch/finance-suite/main/${src}" \
    -o /home/ubuntu/finance-suite-web/static/app/${page}.html
  echo  "  ✓ ${page}.html ← ${src}"
done

# ---- 平台级页面（从 frontend/pages/ 拉取）----
for page in index xueqiu-hot market-snapshot market-context market-temperature-mini weekly-recap workbench-config d13_close_brief d13_midday_pulse; do
  curl -sL "https://raw.githubusercontent.com/jinny280401-glitch/finance-suite/main/frontend/pages/${page}.html" \
    -o /home/ubuntu/finance-suite-web/static/app/${page}.html
  echo  "  ✓ ${page}.html"
done

# ---- 共享 JS/CSS ----
# sidebar-registry.js → frontend/shared/
curl -sL "https://raw.githubusercontent.com/jinny280401-glitch/finance-suite/main/frontend/shared/sidebar-registry.js" \
  -o /home/ubuntu/finance-suite-web/static/app/sidebar-registry.js
echo "  ✓ sidebar-registry.js"

# 市场情报 JS → frontend/scripts/
for asset in market-temperature-mini.js market-temperature-fixture.js market-snapshot-valuation.js market-valuation-snapshot.js pe-band-chart.js; do
  curl -sL "https://raw.githubusercontent.com/jinny280401-glitch/finance-suite/main/frontend/scripts/${asset}" \
    -o /home/ubuntu/finance-suite-web/static/app/${asset}
  echo  "  ✓ ${asset}"
done

# CSS → frontend/styles/
curl -sL "https://raw.githubusercontent.com/jinny280401-glitch/finance-suite/main/frontend/styles/market-temperature-mini.css" \
  -o /home/ubuntu/finance-suite-web/static/app/market-temperature-mini.css
echo "  ✓ market-temperature-mini.css"

# 第三方库 → frontend/lib/
curl -sL "https://raw.githubusercontent.com/jinny280401-glitch/finance-suite/main/frontend/lib/marked.min.js" \
  -o /home/ubuntu/finance-suite-web/static/app/marked.min.js
echo "  ✓ marked.min.js"

# ---- 营销首页模板 ----
curl -sL "https://raw.githubusercontent.com/jinny280401-glitch/finance-suite/main/index.html" \
  -o /home/ubuntu/finance-suite-web/templates/index.html
echo "  ✓ index.html (首页模板)"

echo ""
echo "===== 2. 验证文件 ====="
ls -lh /home/ubuntu/finance-suite-web/static/app/
echo ""

echo "===== 3. 备份 nginx 配置 ====="
sudo cp /etc/nginx/sites-available/finance-suite /etc/nginx/sites-available/finance-suite.backup.$(date +%Y%m%d%H%M%S)
echo "  ✓ 备份完成"

echo ""
echo "===== 4. 更新 nginx 配置 ====="
sudo tee /etc/nginx/sites-available/finance-suite > /dev/null << 'NGINX_CONF'
server {
    listen 80;
    server_name touziagent.com www.touziagent.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name touziagent.com www.touziagent.com;

    # SSL 证书（Let's Encrypt，certbot 管理）
    ssl_certificate     /etc/letsencrypt/live/touziagent.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/touziagent.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    root /home/ubuntu/finance-suite-web/static;
    index index.html;

    # ---- 静态首页 ----
    location = / {
        add_header Cache-Control "no-cache, must-revalidate";
        try_files /index.html =404;
    }

    # ---- 工作台 + 技能页面 ----
    location /app/ {
        alias /home/ubuntu/finance-suite-web/static/app/;
        try_files $uri $uri/ /app/index.html;
        default_type text/html;
        add_header Cache-Control "no-cache, must-revalidate, max-age=0";
    }

    # ---- 静态资源 ----
    location /static/ {
        alias /home/ubuntu/finance-suite-web/static/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # ---- API 请求转发到 Flask/uvicorn ----
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 10s;
    }

    # ---- 其他请求也转发到 Flask ----
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
NGINX_CONF
echo "  ✓ nginx 配置已更新"

echo ""
echo "===== 5. 测试 nginx 配置 ====="
sudo nginx -t

echo ""
echo "===== 6. 重载 nginx ====="
sudo systemctl reload nginx
echo "  ✓ nginx 已重载"

echo ""
echo "===== 部署完成！ ====="
echo "首页：   https://touziagent.com/"
echo "工作台： https://touziagent.com/app/"
echo "看票：   https://touziagent.com/app/stock.html"
echo "深度：   https://touziagent.com/app/deep-research.html"
echo "宏观：   https://touziagent.com/app/macro.html"
echo "竞价：   https://touziagent.com/app/auction.html"
echo "会议：   https://touziagent.com/app/meeting.html"
echo "视频：   https://touziagent.com/app/video.html"
