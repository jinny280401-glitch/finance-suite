# assets/ — Vera 视觉资产 SSOT (Vera Visual Asset SSOT)

> **统一命名原则**: `vera-portrait-{view}.png` 格式
> **路径**: 所有 HTML 通过 `assets/vera-portrait-{view}.png` 引用
> **禁止**: 在 HTML 根目录放 PNG;禁止使用旧名 (vera-portrait-main.png 等)

## 人像资产 (Vera portrait)

| 文件 | 视图 | 大小 | 用途 |
|---|---:|---:|---|
| `vera-portrait-closeup.png` | 特写 (closeup) | 1.9 MB | 第 3 页封面 (fig1-cover.html) 大字 + Vera 头像 |
| `vera-portrait-tri-view.png` | 三视图 (正/侧/后) | 1.3 MB | 第 2 页人物介绍 (fig-cover-vera-portraits.html) |
| `vera-portrait-insight.png` | 洞察场景 | 1.9 MB | 备用 — 未来"数据洞察"场景演示 |
| `vera-portrait-online.png` | 在线场景 | 1.9 MB | 备用 — 未来"在线服务"场景演示 |

## 引用示例

```html
<!-- 正确 -->
<img src="assets/vera-portrait-closeup.png" alt="Vera 特写" />

<!-- 错误 -->
<img src="vera-portrait-main.png" />
<img src="./vera-portrait-main.png" />
<img src="/vera-portrait-main.png" />
```

## 维护

| 动作 | 路径 |
|---|---|
| 新增人像 | 放 `assets/` + 命名 `vera-portrait-{view}.png` |
| 删除人像 | 先在 HTML 中替换为 placeholder,确认无引用后再删 |
| 重命名 | 全局搜索 `assets/vera-portrait-` + 同步所有 HTML |
| 跨项目复用 | 同步到 Finance Suite 全局 `assets/`,本目录仅用于路演 PPT |
