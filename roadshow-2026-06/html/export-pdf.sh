#!/bin/bash

# Vera 路演 PPT 批量导出 PDF
# 使用方法: ./export-pdf.sh

OUTPUT_DIR="./pdf-export"
mkdir -p "$OUTPUT_DIR"

echo "======================================"
echo "Vera 路演 PPT PDF 导出工具"
echo "======================================"
echo ""
echo "导出目录: $OUTPUT_DIR"
echo ""

# 页面列表
declare -a pages=(
  "fig-cover-vera-portraits.html:01-天玑封面"
  "fig-contents.html:02-目录"
  "fig-hook-why-not-trust.html:03-为什么不敢相信AI"
  "fig-pain-triangle.html:04-AI幻觉的成本"
  "fig1-cover.html:05-Vera管理幻觉"
  "fig-general-ai-vs-vera.html:06-通用AI-vs-Vera"
  "fig3-trust-gate-flow.html:07-Trust-Gate"
  "fig-daily-research-loop.html:08-持续研究闭环"
  "fig-company-panorama.html:09-公司拜访速查卡"
  "fig-workbench.html:10-真实工作台"
  "fig2-vera-overall-architecture.html:11-可信如何建成"
  "fig4-research-runtime.html:12-Research-Runtime"
  "fig5-skill-ecosystem.html:13-核心10页Skill"
  "fig-enterprise-architecture-v1.html:14-业务验证与行业开放"
  "fig-multichannel-satellite.html:15-多场景触达"
  "fig7-closing.html:16-收官"
)

echo "请手动完成以下步骤："
echo ""
echo "1. 确保本地服务器运行在 http://localhost:8080"
echo "2. 打开 Chrome 浏览器"
echo "3. 对每个页面执行以下操作："
echo ""

for item in "${pages[@]}"; do
  IFS=':' read -r file name <<< "$item"
  echo "   【${name}】"
  echo "   - 访问: http://localhost:8080/${file}"
  echo "   - 按 Cmd+P"
  echo "   - 目标: 存储为PDF"
  echo "   - 布局: 横向"
  echo "   - 边距: 无"
  echo "   - 取消「页眉和页脚」"
  echo "   - 保存为: ${OUTPUT_DIR}/${name}.pdf"
  echo ""
done

echo "======================================"
echo "或使用快捷方式："
echo "访问 http://localhost:8080/index.html"
echo "用左右箭头键切换页面，对每页按 Cmd+P 导出"
echo "======================================"
