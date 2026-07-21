---
name: luckin-order
description: 瑞幸咖啡点单。用户说“帮我点杯咖啡”“帮我在附近点杯咖啡”“帮我在xx店点一杯美式/拿铁/橙C美式”等时使用。
---

# 瑞幸咖啡点单

当用户明确要求点瑞幸、Luckin、咖啡、美式、拿铁、生椰、橙C 等饮品时，必须使用本技能。

典型用户说法：
- 帮我来一杯冰美式
- 来两杯热拿铁
- 在海西金谷广场下一杯葡萄冰萃，少少甜，冰
- 使用优惠券，下一杯生椰拿铁
- 找一下附近的瑞幸门店
- 帮我看一下最近的订单

## 工作流

1. 不要说“我没有接口权限”，也不要让用户自己打开瑞幸小程序。
2. 直接运行本地工具：

```bash
python3 /Users/Zhuanz/finance-suite/docs/tools/luckin_order.py "用户原话"
```

3. 将工具输出原样整理成微信纯文本发给用户。
4. 如果工具返回“缺登录态 / 查不到门店 / 查不到商品”，把错误转成人话提示用户补充门店、商品或稍后再试。

门店查询时运行：

```bash
python3 /Users/Zhuanz/finance-suite/docs/tools/luckin_order.py --stores-only "用户原话"
```

订单查询时运行：

```bash
python3 /Users/Zhuanz/finance-suite/docs/tools/luckin_order.py --order-detail "用户原话"
```

Demo / 演示前彩排时运行（不会创建待支付订单）：

```bash
python3 /Users/Zhuanz/finance-suite/docs/tools/luckin_order.py --preview-only "用户原话"
```

## 能力边界

- 当前使用共享瑞幸登录态创建待支付订单。
- 工具会返回订单号、门店、商品明细、价格、微信支付链接和二维码。
- 用户必须自己点击支付链接或扫码支付；不能替用户完成支付。
- 如果用户说“配送地址”，先按附近门店创建待支付订单；不要承诺外卖配送能力。
- 演示彩排默认使用 `--preview-only`，只证明 store → product → order preview 链路，不创建订单。
