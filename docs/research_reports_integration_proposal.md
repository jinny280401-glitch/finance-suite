# Finance Suite 投行研报集成方案

**日期**：2026-05-05  
**状态**：待审阅  
**审阅人**：太子

---

## 一、问题背景

### 当前状态
Finance Suite MCP Server 已有 12 个金融工具，覆盖：
- 实时行情（stock_analysis）
- 财报数据（wind_query - financials）
- 宏观数据（macro_snapshot）
- 市场情绪（market_pulse）
- 多平台数据（雪球、知乎、新浪财经、Barchart）

### 缺失维度
**投行研报**：顶级投行（高盛、摩根大通、桥水等）的深度分析报告

### 用户需求
在做个股分析时，能快速引用顶级投行研报，补充：
- 行业趋势分析
- 估值方法论
- 政策解读
- 竞争格局

---

## 二、数据来源调研

### 2.1 用户现有资源

#### 资源 A：微信公众号
- **名称**：Goldman Sachs
- **微信号**：Huaban1925
- **内容**：每日 Pitch + 投行研报汇总
- **更新频率**：每日更新
- **访问方式**：需在微信中搜索公众号关注

#### 资源 B：IMA 知识库
- **名称**：2026年八大顶级投行研报-每日更新3+次
- **链接**：https://ima.qq.com/wiki/?shareId=3c87d42856fecad9a79b2782ceeb11834320752f4467d1ce4309fee45423f6fb
- **内容**：八大顶级投行研报汇总
- **更新频率**：每日 3+ 次
- **访问方式**：需登录 IMA（腾讯 AI 工作台）

---

## 三、技术调研过程

### 3.1 GitHub 开源项目调研

#### 微信公众号爬虫
搜索关键词：`GitHub 微信公众号爬虫 wechat scraper python`

**找到的项目**：
1. **[wechat_spider](https://github.com/15921483570/wechat_spider)** - 只需设置代理，一键爬取历史文章
2. **[weixin_crawler](https://github.com/beimingmaster/weixin_crawler)** - 基于 Scrapy，支持阅读数据
3. **[wechat_spider_go](https://github.com/lyhiving/wechat_spider_go)** - 基于中间人截获
4. **[wechat_spider (轻量级)](https://github.com/lshxiao/wechat_spider)** - 基于搜狗搜索，代码只有几十行

#### IMA 知识库相关
搜索关键词：`GitHub IMA 知识库 腾讯文档 scraper API`

**找到的信息**：
- **[tencent-ima](https://github.com/872601188/tencent-ima)** - 腾讯 IMA 智能个人知识管理平台
- **[CSDN 文章](https://blog.csdn.net/leijmdas/article/details/153316461)** - 如何接入腾讯知识库
  - 方案 1：IMA 知识库 + 公众号菜单（10分钟）
  - 方案 2：腾讯元器（生成智能体，一键发布 API）
  - 方案 3：WeKnora（私有部署，RAG 中台）

### 3.2 实际测试

#### 测试项目：wechat_spider (轻量级)
```bash
git clone https://github.com/lshxiao/wechat_spider.git
cd wechat_spider
pip install -e .
```

**测试结果**：❌ 失败
```
IndexError: list index out of range
```

**失败原因**：
- 项目基于搜狗微信搜索
- 搜狗页面结构已变化
- 项目已过时（最后更新：2018年）

#### WebFetch 测试 IMA 知识库
```python
WebFetch(url="https://ima.qq.com/wiki/?shareId=...")
```

**测试结果**：❌ 失败
- 页面仅返回标题："ima.copilot-腾讯AI工作台"
- 需要登录才能访问内容
- WebFetch 无法处理需要认证的页面

---

## 四、技术可行性分析

### 4.1 微信公众号抓取

| 方案 | 可行性 | 优点 | 缺点 |
|------|--------|------|------|
| **搜狗搜索爬虫** | ❌ 不可行 | 代码简单 | 接口已失效，项目过时 |
| **中间人截获** | ⚠️ 高风险 | 可获取完整数据 | 需要代理设置，可能违反微信条款 |
| **Selenium 模拟** | ⚠️ 高成本 | 理论可行 | 需要维护浏览器自动化，易被检测 |
| **官方 API** | ❌ 不存在 | 稳定可靠 | 微信未提供公众号内容 API |

**结论**：微信公众号内容抓取**技术上可行但不推荐**
- 维护成本高（反爬虫机制频繁变化）
- 合规风险（可能违反微信使用条款）
- 稳定性差（随时可能失效）

### 4.2 IMA 知识库抓取

| 方案 | 可行性 | 优点 | 缺点 |
|------|--------|------|------|
| **WebFetch** | ❌ 不可行 | 简单 | 需要登录，无法获取内容 |
| **腾讯元器 API** | ⚠️ 待验证 | 官方支持 | 需要申请权限，文档不明确 |
| **WeKnora 私有部署** | ⚠️ 高成本 | 完全控制 | 需要部署和维护 RAG 系统 |
| **手动同步** | ✅ 可行 | 简单可靠 | 需要人工操作 |

**结论**：IMA 知识库自动化抓取**需要进一步调研腾讯元器 API**

---

## 五、推荐方案

### 方案 A：轻量级参考入口（推荐）⭐

**核心思路**：不抓取内容，提供快速访问入口 + 精选研报手动维护

#### 实现方式
```python
# research_reports 工具返回格式
{
  "_qc": {
    "status": "success",
    "completeness": 1.0,
    "sources": ["research_reports"],
    "fallback_source": null
  },
  "sources": [
    {
      "type": "wechat",
      "name": "Goldman Sachs",
      "wechat_id": "Huaban1925",
      "description": "每日Pitch + 投行研报汇总",
      "access": "微信搜索公众号关注",
      "qr_code": null
    },
    {
      "type": "ima",
      "name": "IMA知识库",
      "url": "https://ima.qq.com/wiki/?shareId=...",
      "description": "2026年八大顶级投行研报-每日更新3+次",
      "access": "需登录IMA"
    }
  ],
  "featured_reports": [
    {
      "id": 1,
      "title": "高盛：AI行业深度报告",
      "date": "2026-05-04",
      "source": "Goldman Sachs",
      "url": "https://mp.weixin.qq.com/s/xxx",  // 如果有分享链接
      "related_stocks": ["600519.SH"],
      "industries": ["科技", "AI"],
      "tags": ["AI", "估值", "行业趋势"],
      "summary": "深度分析AI行业发展趋势和投资机会"
    }
  ]
}
```

#### 工具操作
```python
# 1. 查询研报来源
research_reports(action="sources")

# 2. 按股票查询（返回精选研报 + 来源入口）
research_reports(action="by-stock", code="600519.SH")

# 3. 按行业查询
research_reports(action="by-industry", industry="白酒")

# 4. 手动添加精选研报
research_reports(
    action="add",
    title="高盛：白酒行业深度报告",
    url="https://mp.weixin.qq.com/s/xxx",
    stocks=["600519.SH", "000568.SZ"],
    industries=["白酒", "消费"],
    tags=["估值", "行业趋势"]
)
```

#### 优势
- ✅ **零维护成本**：不依赖爬虫，不会失效
- ✅ **合规无风险**：不违反任何平台使用条款
- ✅ **快速访问**：直接返回入口链接
- ✅ **精选补充**：手动维护重点研报，提升查询体验

#### 劣势
- ❌ 无法自动获取最新研报列表
- ❌ 需要手动添加精选研报（但可以按需添加）

---

### 方案 B：腾讯元器 API 集成（待验证）

**核心思路**：使用腾讯官方 API 获取 IMA 知识库内容

#### 实施步骤
1. 调研腾讯元器 API 文档
2. 申请 API 权限
3. 开发集成模块
4. 测试数据获取

#### 优势
- ✅ 官方支持，稳定可靠
- ✅ 可自动获取最新研报

#### 劣势
- ❌ 需要申请权限（审批时间未知）
- ❌ API 文档不明确
- ❌ 可能有调用限制

#### 风险
- ⚠️ API 可能不对外开放
- ⚠️ 权限申请可能被拒绝

---

### 方案 C：混合方案（中期目标）

**短期（本周）**：采用方案 A（轻量级参考入口）
**中期（下月）**：调研方案 B（腾讯元器 API）
**长期（按需）**：如果 API 可行，升级为自动化获取

---

## 六、实施计划

### Phase 1：方案 A 实施（1-2 小时）

#### 1.1 修改 `research_reports.py`
- 调整数据结构（sources + featured_reports）
- 实现 add/list/by-stock/by-industry/by-tag/search

#### 1.2 修改 `mcp_server.py`
- 更新 `research_reports` 工具说明
- 调整返回格式

#### 1.3 更新 `docs/MCP_TOOLS_GUIDE.md`
- 更新工具 13 的说明
- 添加使用示例

#### 1.4 测试验证
```bash
# 测试工具调用
python3 scripts/research_reports.py list
python3 scripts/research_reports.py by-stock 600519.SH
```

### Phase 2：腾讯元器 API 调研（待定）

#### 2.1 调研任务
- [ ] 查找腾讯元器官方文档
- [ ] 确认 API 是否对外开放
- [ ] 了解权限申请流程
- [ ] 评估调用限制和成本

#### 2.2 决策点
- 如果 API 可用 → 开发集成模块
- 如果 API 不可用 → 继续使用方案 A

---

## 七、待决策事项

### 决策 1：是否采用方案 A？
- **推荐**：✅ 采用
- **理由**：零维护成本、合规无风险、快速上线

### 决策 2：是否调研腾讯元器 API？
- **推荐**：⏳ 中期调研
- **理由**：不阻塞当前进度，作为优化方向

### 决策 3：精选研报维护策略？
- **选项 A**：按需添加（看到好研报时手动添加）
- **选项 B**：定期维护（每周添加 5-10 篇重点研报）
- **推荐**：选项 A（按需添加）

---

## 八、总结

### 核心结论
1. ❌ **微信公众号自动抓取不可行**（技术可行但不推荐）
2. ⚠️ **IMA 知识库自动化需进一步调研**（腾讯元器 API）
3. ✅ **推荐采用轻量级参考入口方案**（方案 A）

### 下一步行动
1. **太子审阅本方案**
2. **确认是否采用方案 A**
3. **如果通过，1-2 小时内完成实施**

---

**附录：相关链接**
- [wechat_spider (轻量级)](https://github.com/lshxiao/wechat_spider)
- [weixin_crawler (Scrapy)](https://github.com/beimingmaster/weixin_crawler)
- [tencent-ima](https://github.com/872601188/tencent-ima)
- [如何接入腾讯知识库](https://blog.csdn.net/leijmdas/article/details/153316461)

---

_文档生成时间：2026-05-05 00:30_  
_作者：Claude Sonnet 4.6_
