# Finance Suite — AI 金融分析套件

6大专业分析技能，集成东方财富实时数据 + 双搜索引擎 + YouTube/B站字幕提取。

## 技能列表

| 技能 | 功能 | 数据源 |
|------|------|--------|
| **看票分析** | 个股深度分析（9章+4位投资大师视角） | AkShare + Tavily |
| **宏观内参** | 宏观经济白话解读 | AkShare(GDP/CPI/PMI) + Tavily |
| **麦肯锡报告** | 咨询级战略分析报告 | 用户资料 |
| **视频拆解** | 自动提取字幕+知识结构化 | Supadata + B站API |
| **行业报告** | 行业全景深度研究 | AkShare + Tavily |
| **集合竞价** | 涨停排行+量化选股信号 | AkShare |

## 快速安装

```bash
# 1. 解压到 OpenClaw Skills 目录
tar -xzf finance-suite-skill-v1.0.0.tar.gz -C ~/.qclaw/workspace/skills/

# 2. 安装 Python 依赖
pip install akshare httpx supadata

# 3. 配置 API 密钥（在 ~/.openclaw/.env 中）
TAVILY_KEYS=your-tavily-key
SUPADATA_API_KEY=your-supadata-key  # 可选，YouTube字幕提取
```

详细安装说明见 [INSTALL.md](INSTALL.md)

## 在线版

Web版：[touziagent.com](https://touziagent.com)

## 项目结构

```
finance-suite/
├── SKILL.md              # OpenClaw Skill 主入口
├── INSTALL.md            # 安装指南
├── scripts/              # 数据获取脚本
│   ├── stock_data.py     # 东方财富A股数据
│   ├── macro_data.py     # 宏观经济数据
│   ├── auction_data.py   # 集合竞价/涨停
│   ├── video_data.py     # YouTube/B站字幕
│   └── search.py         # Tavily+Brave搜索
├── prompts/              # 6个分析框架 Prompt
└── references/           # 参考规范
```

## License

MIT
