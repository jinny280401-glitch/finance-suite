#!/bin/bash
# Finance Suite 一键部署脚本
# 在腾讯云 Ubuntu-ZjOV 服务器上执行
# 功能：拉取最新页面 + 更新 nginx 配置

set -e

echo "===== 1. 拉取最新页面文件 ====="

# 确保目录存在
mkdir -p /home/ubuntu/finance-suite-web/static/app/

# 拉取工作台首页
curl -sL "https://raw.githubusercontent.com/jinny280401-glitch/finance-suite/main/app/index.html" \
  -o /home/ubuntu/finance-suite-web/static/app/index.html

# 拉取6个技能页面
for page in deep-research stock macro auction meeting video; do
  curl -sL "https://raw.githubusercontent.com/jinny280401-glitch/finance-suite/main/app/${page}.html" \
    -o /home/ubuntu/finance-suite-web/static/app/${page}.html
  echo "  ✓ ${page}.html"
done

# 拉取首页
curl -sL "https://raw.githubusercontent.com/jinny280401-glitch/finance-suite/main/index.html" \
  -o /home/ubuntu/finance-suite-web/static/index.html
echo "  ✓ index.html (首页)"

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

    # SSL 证书（根据实际路径调整）
    ssl_certificate     /etc/nginx/ssl/touziagent.com_bundle.crt;
    ssl_certificate_key /etc/nginx/ssl/touziagent.com.key;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    # ---- 静态首页 ----
    location = / {
        alias /home/ubuntu/finance-suite-web/static/index.html;
        default_type text/html;
    }

    # ---- 工作台 + 技能页面 ----
    location /app/ {
        alias /home/ubuntu/finance-suite-web/static/app/;
        try_files $uri $uri/ /app/index.html;
        default_type text/html;
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
