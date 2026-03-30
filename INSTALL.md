# Finance Suite Skill 安装指南

## 一、安装（3步完成）

### 步骤1：解压到OpenClaw Skills目录

```bash
# 解压安装包到 OpenClaw 的 skills 目录
tar -xzf finance-suite-skill-v1.0.0.tar.gz -C ~/.qclaw/workspace/skills/
```

验证安装：
```bash
ls ~/.qclaw/workspace/skills/finance-suite/SKILL.md
# 如果看到文件路径输出，说明安装成功
```

### 步骤2：安装Python依赖

```bash
pip install akshare httpx supadata
```

### 步骤3：配置API密钥

在 `~/.openclaw/.env` 文件中添加（如果没有这个文件就创建一个）：

```bash
# 必需 — Tavily搜索引擎（注册：https://app.tavily.com）
TAVILY_KEYS=你的tavily-key-1,你的tavily-key-2

# 可选 — Brave搜索（备用引擎，注册：https://api.search.brave.com）
BRAVE_KEYS=你的brave-key

# 可选 — YouTube字幕提取（注册：https://supadata.ai，免费100次/月）
SUPADATA_API_KEY=你的supadata-key
```

完成！重启OpenClaw后即可使用。

---

## 二、使用方式

直接对Agent说以下任意内容，会自动触发对应技能：

| 你说 | 触发技能 | 效果 |
|------|---------|------|
| "帮我分析比亚迪" | 看票分析 | 9章深度报告+4位投资大师视角 |
| "最近经济形势怎么样" | 宏观内参 | GDP/CPI/PMI数据+白话解读 |
| "根据这份会议纪要出报告" | 麦肯锡报告 | 咨询级战略分析报告 |
| "帮我拆解这个视频 [链接]" | 视频拆解 | 自动提取字幕+知识结构化 |
| "分析一下新能源汽车行业" | 行业报告 | 市场规模+竞争格局+趋势 |
| "今日集合竞价分析" | 集合竞价 | 涨停排行+量化选股信号 |

---

## 三、包含内容

```
finance-suite/
├── SKILL.md              # 主入口（6大技能路由）
├── scripts/              # 数据获取脚本
│   ├── stock_data.py     # 东方财富A股数据
│   ├── macro_data.py     # 宏观经济数据（GDP/CPI/PMI/LPR）
│   ├── auction_data.py   # 集合竞价/涨停/异动
│   ├── video_data.py     # YouTube/B站字幕提取
│   └── search.py         # Tavily+Brave双引擎搜索
├── prompts/              # 6个分析框架
│   ├── stock-analyst.md  # 看票分析（含投资大师视角）
│   ├── macro-advisor.md  # 宏观内参
│   ├── mckinsey-report.md
│   ├── video-breakdown.md
│   ├── industry-report.md
│   └── auction-analysis.md
└── references/           # 参考规范
    ├── search-patterns.md
    └── search-guidelines.md
```

---

## 四、常见问题

**Q: 需要什么Python版本？**
A: Python 3.10+（因使用了 `dict | None` 类型语法）

**Q: 没有Tavily Key能用吗？**
A: 看票分析和宏观内参的AkShare数据部分仍然可用（东方财富数据不需要Key），但搜索引擎补充信息不可用。

**Q: YouTube字幕提取一直失败？**
A: 需要配置 `SUPADATA_API_KEY`。部分视频确实没有字幕（UP主未开启），这种情况无法提取。

**Q: 如何卸载？**
A: `rm -rf ~/.qclaw/workspace/skills/finance-suite/`
