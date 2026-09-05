# Finance Suite 生产部署实施图

> 扫描时间：2026-09-05 08:51 CST
> 服务器：119.28.156.125 (公网) / 10.8.0.4 (内网)

---

## 一、部署拓扑图

```
                        ┌──────────────────────┐
                        │     互联网用户         │
                        └──────────┬───────────┘
                                   │ HTTPS
                                   ▼
┌──────────────────────────────────────────────────────────────┐
│                    腾讯云 (CVM)                               │
│                    119.28.156.125                             │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              Nginx (端口 80/443)                        │  │
│  │                                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │  │
│  │  │ HTTP :80    │  │ HTTPS :443  │  │ SSL证书       │  │  │
│  │  │ → 301 HTTPS │  │ HTTP/2      │  │ Let's Encrypt │  │  │
│  │  └─────────────┘  └──────┬──────┘  │ touziagent.com│  │  │
│  │                          │         └──────────────┘  │  │
│  └──────────────────────────┼───────────────────────────┘  │
│                             │                               │
│              ┌──────────────┼──────────────┐                │
│              │              │              │                │
│              ▼              ▼              ▼                │
│  ┌───────────────┐ ┌──────────────┐ ┌─────────────────┐   │
│  │ 静态文件直出   │ │ FastAPI 代理  │ │ API 子域名代理   │   │
│  │               │ │              │ │                 │   │
│  │ /app/* →      │ │ www 站       │ │ api.touziagent  │   │
│  │ static/app/   │ │ /api/* →     │ │ .com            │   │
│  │               │ │ :8000        │ │ /* → :8000      │   │
│  │ /static/* →   │ │              │ │                 │   │
│  │ static/       │ │              │ │ CORS:           │   │
│  │ (7天缓存)     │ │              │ │ www.touziagent  │   │
│  └───────────────┘ └──────┬───────┘ │ .com            │   │
│                           │         └────────┬────────┘   │
│                           │                  │             │
│                           ▼                  ▼             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Uvicorn (127.0.0.1:8000)                    │  │
│  │           仅本地监听, 不暴露公网                       │  │
│  │                                                      │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │  │
│  │  │ Worker 1 │ │ Worker 2 │ │ Worker 3 │ │Worker 4│  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────┘  │  │
│  │                                                      │  │
│  │  /home/ubuntu/finance-suite-web/                     │  │
│  │  ├── app/main.py          FastAPI 入口               │  │
│  │  ├── app/routers/         路由模块                    │  │
│  │  ├── static/              前端静态文件                 │  │
│  │  ├── templates/           Jinja2 模板                 │  │
│  │  ├── finance_suite.db     SQLite 数据库               │  │
│  │  ├── .env                 环境变量                    │  │
│  │  └── venv/                Python 虚拟环境             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  其他服务                                             │   │
│  │                                                      │   │
│  │  ┌──────────────────┐  ┌──────────────────────────┐  │   │
│  │  │ engram_api.py    │  │ fail2ban-server          │  │   │
│  │  │ :8766 (localhost)│  │ SSH 暴力破解防护          │  │   │
│  │  │ AI 服务           │  │                          │  │   │
│  │  └──────────────────┘  └──────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## 二、域名与 SSL

```
┌─────────────────────────────────────────────────────────────────┐
│  域名体系                                                       │
│                                                                 │
│  touziagent.com ──301──→ www.touziagent.com (主站)              │
│                          ├── /app/*      静态前端                │
│                          ├── /static/*   静态资源 (CDN缓存)      │
│                          ├── /api/*      API 接口                │
│                          └── /*          Jinja2 渲染页面         │
│                                                                 │
│  api.touziagent.com ──────────── (API 直连, 绕过 CDN)           │
│                          └── /*          API 接口                │
│                              CORS: www.touziagent.com            │
│                                                                 │
│  SSL 证书: Let's Encrypt                                        │
│  路径: /etc/letsencrypt/live/touziagent.com/                    │
│  管理: Certbot 自动续期                                          │
│  协议: TLSv1.2 / TLSv1.3                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、Nginx 安全与限速策略

```
┌─────────────────────────────────────────────────────────────────┐
│  安全层                                                         │
│                                                                 │
│  ┌─── 限速规则 ─────────────────────────────────────────────┐   │
│  │  api_limit:   10 req/s per IP, burst=20, nodelay         │   │
│  │  login_limit:  5 req/min per IP, burst=4, nodelay        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─── 安全头 ───────────────────────────────────────────────┐   │
│  │  server_tokens off          (隐藏 Nginx 版本)             │   │
│  │  Cache-Control: no-store    (API 响应不缓存)              │   │
│  │  /openapi.json → 404        (屏蔽 API 文档)               │   │
│  │  /redoc → 404               (屏蔽 API 文档)               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─── fail2ban ─────────────────────────────────────────────┐   │
│  │  防护 SSH 暴力破解                                        │   │
│  │  运行中, 自 2026-05-26                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、Systemd 服务配置

```ini
[Unit]
Description=Finance Suite Web App
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/finance-suite-web
Environment=PATH=/home/ubuntu/finance-suite-web/venv/bin:/usr/bin
ExecStart=/home/ubuntu/finance-suite-web/venv/bin/uvicorn \
    app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 运行用户 | ubuntu | 非 root 运行 |
| 绑定地址 | 127.0.0.1 | 仅本地, Nginx 反代 |
| 工作进程 | 4 | 匹配 CPU 核数 |
| 自动重启 | yes | 5 秒后重启 |
| 服务状态 | ✅ active (running) | 自 2026-08-30 运行 |
| 内存占用 | ~811 MB | 4 workers 总计 |

---

## 五、部署目录结构

```
/home/ubuntu/finance-suite-web/
│
├── app/                          # FastAPI 后端
│   ├── main.py                   # 应用入口
│   ├── config.py                 # 配置管理
│   ├── auth.py                   # 认证逻辑
│   ├── database.py               # 数据库模型
│   ├── llm.py                    # LLM 调用
│   ├── skills.py                 # 技能调度
│   ├── search.py                 # 搜索
│   ├── api.py                    # 旧版 API
│   ├── stock_data.py             # 个股数据
│   ├── auction_data.py           # 竞价数据
│   ├── macro_data.py             # 宏观数据
│   ├── video_data.py             # 视频数据
│   ├── routers/                  # 路由模块
│   │   ├── api.py                # 核心 API (55KB)
│   │   ├── intel.py              # 情报接口 (33KB)
│   │   ├── admin.py              # 管理后台
│   │   ├── pages.py              # 页面渲染
│   │   └── watchlist.py          # 自选股
│   └── quality_gate/             # 质量门控
│       ├── core.py
│       └── rules.py
│
├── static/                       # 前端静态文件
│   ├── index.html                # 营销首页
│   ├── app/                      # 工作台页面 (20+ 文件)
│   ├── css/                      # 样式
│   └── js/                       # 脚本
│
├── templates/                    # Jinja2 模板 (9 文件)
│
├── scripts/                      # 数据脚本
│   ├── auction_data.py
│   ├── ifind_data.py
│   ├── macro_data.py
│   ├── market_context.py
│   └── joinquant_data.py
│
├── server_scripts/               # 运维脚本
│   ├── manage_users.py
│   └── import_accounts.sh
│
├── tests/                        # 测试套件 (6 文件)
│
├── finance_suite.db              # SQLite 数据库
├── .env                          # 环境变量
├── requirements.txt              # 依赖清单
├── mcp_server.py                 # MCP 服务
├── venv/                         # Python 虚拟环境
├── logs/                         # 日志
└── backups/                      # 备份
```

---

## 六、Python 依赖清单 (核心)

| 包 | 版本 | 用途 |
|-----|------|------|
| fastapi | 0.115.0 | Web 框架 |
| uvicorn | — | ASGI 服务器 |
| jinja2 | 3.1.4 | 模板引擎 |
| sqlalchemy | — | ORM |
| pyjwt | — | JWT 认证 |
| bcrypt | 4.2.0 | 密码加密 |
| httpx | 0.27.2 | HTTP 客户端 |
| akshare | 1.18.48 | A 股数据 |
| jqdatasdk | 1.9.8 | 聚宽数据 |
| pandas | 3.0.1 | 数据处理 |
| numpy | 2.4.3 | 数值计算 |
| beautifulsoup4 | 4.14.3 | HTML 解析 |
| lxml | 6.0.2 | XML 解析 |
| openpyxl | 3.1.5 | Excel 处理 |
| reportlab | — | PDF 生成 |
| weasyprint | — | PDF 生成 |

---

## 七、部署时间线

| 时间 | 事件 |
|------|------|
| 2026-03-28 | 项目初始部署 |
| 2026-04-23 | static 目录备份 (前端重构) |
| 2026-05-06 | 用户管理系统完善 |
| 2026-05-10 | PDF 导出功能上线 |
| 2026-06-04 | iFinD HTTP API 集成 |
| 2026-07-05 | 首页 hero 区域更新 |
| 2026-07-17 | 市场温度组件优化 |
| 2026-07-18 | 收盘简报/市场快照上线 |
| 2026-07-31 | Trust Guard + PE 波段图 |
| 2026-08-14 | 竞价数据缓存修复 |
| 2026-08-30 | 最近一次服务重启 (当前运行) |

---

*报告生成时间：2026-09-05*
