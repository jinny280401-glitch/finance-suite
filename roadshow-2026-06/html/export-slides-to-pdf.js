const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const slides = [
  {src:"fig-cover-vera-portraits.html",       name:"01-天玑封面"},
  {src:"fig-contents.html",                   name:"02-目录"},
  {src:"fig-hook-why-not-trust.html",         name:"03-为什么不敢相信AI"},
  {src:"fig-pain-triangle.html",              name:"04-AI幻觉的成本"},
  {src:"fig1-cover.html",                     name:"05-Vera管理幻觉"},
  {src:"fig-general-ai-vs-vera.html",         name:"06-通用AI-vs-Vera"},
  {src:"fig3-trust-gate-flow.html",           name:"07-Trust-Gate"},
  {src:"fig-daily-research-loop.html",        name:"08-持续研究闭环"},
  {src:"fig-company-panorama.html",           name:"09-公司拜访速查卡"},
  {src:"fig-workbench.html",                  name:"10-真实工作台"},
  {src:"fig2-vera-overall-architecture.html", name:"11-可信如何建成"},
  {src:"fig4-research-runtime.html",          name:"12-Research-Runtime"},
  {src:"fig5-skill-ecosystem.html",           name:"13-核心10页Skill"},
  {src:"fig-enterprise-architecture-v1.html", name:"14-业务验证与行业开放"},
  {src:"fig-multichannel-satellite.html",     name:"15-多场景触达"},
  {src:"fig7-closing.html",                   name:"16-收官"},
];

const OUTPUT_DIR = path.join(__dirname, 'pdf-export');

(async () => {
  // 创建输出目录
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  console.log(`开始导出 ${slides.length} 页...`);

  for (let i = 0; i < slides.length; i++) {
    const slide = slides[i];
    const url = `http://localhost:8080/${slide.src}`;
    const outputPath = path.join(OUTPUT_DIR, `${slide.name}.pdf`);

    console.log(`[${i + 1}/${slides.length}] 导出: ${slide.name}`);

    try {
      await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });
      await page.waitForTimeout(1000); // 等待动画和字体加载

      await page.pdf({
        path: outputPath,
        width: '1920px',
        height: '1080px',
        printBackground: true,
        preferCSSPageSize: false,
      });

      console.log(`  ✓ 已保存: ${outputPath}`);
    } catch (error) {
      console.error(`  ✗ 导出失败: ${slide.name}`, error.message);
    }
  }

  await browser.close();
  console.log(`\n导出完成！PDF 文件保存在: ${OUTPUT_DIR}`);
  console.log(`\n合并所有 PDF:`);
  console.log(`  cd ${OUTPUT_DIR}`);
  console.log(`  "/System/Library/Automator/Combine PDF Pages.action/Contents/MacOS/join" -o Vera-路演PPT-完整版.pdf *.pdf`);
})();
