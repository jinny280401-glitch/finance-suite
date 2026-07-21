# Webroot 冲突定夺 (G/Codex Decision)

**日期**：2026-07-17  
**定夺人**：G/Codex  
**背景**：D13 三窗口 HTML + 4176 跳转阻塞问题（webroot 约定冲突）

---

## 定夺结果：选方案 1

**不改 `/app/` 链接（本次 D13 任务涉及的文件范围内的 `<a href="/app/...">` 链接）**

---

## 理由

1. **生产标准**：nginx、deploy.sh、SSOT 文档都把 `/app/` 作为正式公共路由
2. **本地应镜像生产**：本地服务应镜像生产 URI 结构，避免环境差异
3. **规范启动方式**：
   ```bash
   python3 -m http.server 4176 \
     --bind 127.0.0.1 \
     --directory /Users/Zhuanz/finance-suite
   ```
4. **规范入口**：`http://127.0.0.1:4176/app/index.html`
5. **入口多一层可接受**：`/index.html` 不是上线契约

---

## 执行规则

- ✅ 保持所有 `/app/` 路径不变
- ✅ 从仓库根目录启动 http.server
- ❌ 不要触碰 C 的 audit 文件
- ❌ 不要为了"本地方便"改生产路由

---

## 影响范围

- 本地预览入口：`http://127.0.0.1:4176/app/index.html`（多一层 `/app/`）
- 生产部署：无影响（保持现有路由）
- 内部链接：本次 D13 任务范围内的 `<a href="/app/...">` 链接无需修改（全仓约 35 处导航引用，37 个 `/app/` 字面量，仅涉及本次改动文件范围）

---

**状态**：CLOSED  
**记录人**：Claude Opus 4.8  
**相关文档**：[[project_d13_three_window_html_20260717]] ← 详见 Memory：`/Users/Zhuanz/.claude/projects/-Users-Zhuanz/memory/project_d13_three_window_html_20260717.md`
