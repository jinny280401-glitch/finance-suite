# Finance Suite Nginx 配置说明

## 架构原则

**关键规则：`/app/` 是静态页面，`/api/` 才转发后端**

### 路由分层

```
/                    → 静态首页（index.html）
/app/                → 静态工作台页面（root 映射）
/app/stock.html      → 静态技能页面
/app/macro.html      → 静态技能页面
/app/*.html          → 所有技能页面都是静态 HTML
/static/             → 静态资源（CSS/JS/图片）
/api/*               → 转发到后端 uvicorn:8000
```

### 配置要点

#### 1. `/app/` 必须用 root 映射静态文件

```nginx
location /app/ {
    root /home/ubuntu/finance-suite-web/static;
    try_files $uri $uri/index.html =404;
    add_header Cache-Control "no-cache, must-revalidate, max-age=0";
}
```

**为什么用 root 而不是 alias？**
- `root` 会把 `/app/stock.html` 映射到 `/home/ubuntu/finance-suite-web/static/app/stock.html`
- `alias` 容易在 `try_files` 中触发路径拼接错误和内部重定向循环

#### 2. `/api/` 才转发后端

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    # ... proxy headers
}
```

#### 3. 不允许把 `/app/` 代理到 FastAPI

**错误配置示例（会导致 404）：**

```nginx
# ❌ 错误：会把所有请求转发到后端
location / {
    proxy_pass http://127.0.0.1:8000;
}
```

这会导致 `/app/stock.html` 被转发到后端，返回 `{"detail":"Not Found"}`。

**正确配置：**

```nginx
# ✅ 正确：先匹配 /app/ 静态文件
location /app/ {
    root /home/ubuntu/finance-suite-web/static;
    try_files $uri $uri/index.html =404;
}

# ✅ 正确：其他请求才转发后端
location / {
    proxy_pass http://127.0.0.1:8000;
}
```

## 部署流程

### 1. 更新配置

```bash
# 备份当前配置
sudo cp /etc/nginx/sites-available/finance-suite \
  /home/ubuntu/backups/nginx-finance-suite-$(date +%F).conf

# 更新配置（从 GitHub 拉取或手动编辑）
sudo cp finance-suite.conf /etc/nginx/sites-available/finance-suite

# 测试配置
sudo nginx -t

# 重载 nginx
sudo systemctl reload nginx
```

### 2. 验证路由

```bash
# 静态页面应返回 200 HTML
curl -I https://www.touziagent.com/app/
curl -I https://www.touziagent.com/app/stock.html

# API 应返回 JSON（405 表示后端在线但方法不对）
curl -I https://www.touziagent.com/api/analyze
```

## 故障排查

### 问题：`/app/stock.html` 返回 `{"detail":"Not Found"}`

**根因：** nginx 把 `/app/` 请求转发到了后端，而后端没有这个路由。

**解决：** 确认 `location /app/` 块在 `location /` 块之前，且使用 `root` 映射静态文件。

### 问题：`/app/` 返回 500 Internal Server Error

**根因：** `try_files` 配置错误，触发内部重定向循环。

**解决：** 使用 `try_files $uri $uri/index.html =404;`，不要用 `/app/index.html` 作为 fallback。

### 问题：nginx 配置漂移

**根因：** 手动修改服务器配置后未同步到 GitHub。

**解决：** 
1. 每次修改后备份到 `/home/ubuntu/backups/`
2. 同步到 GitHub `deploy/nginx/finance-suite.conf`
3. 部署时从 GitHub 拉取，而不是手动编辑

## 服务器信息

- **域名：** touziagent.com, www.touziagent.com
- **服务器：** 腾讯云轻量 119.28.156.125（首尔，Ubuntu-ZjOV）
- **后端：** uvicorn:8000 (Flask/FastAPI)
- **静态文件目录：** `/home/ubuntu/finance-suite-web/static/`
- **nginx 配置：** `/etc/nginx/sites-available/finance-suite`

## 历史问题记录

### 2026-04-29：工程模块页 404 修复

**现象：** 进入 `/app/stock.html` 返回 `{"detail":"Not Found"}`

**根因：** www 站点缺少 `location /app/` 静态映射，所有 `/app/` 请求被 `location /` 转发到后端。

**修复：** 在 www 站点添加 `location /app/` 块，使用 `root` 映射静态文件。

**教训：** 
1. `/app/` 是静态页面，不能代理到后端
2. 使用 `root` 而不是 `alias` 避免路径问题
3. 每次修改后同步到 GitHub 防止配置漂移
