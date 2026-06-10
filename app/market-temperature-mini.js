(function (global) {
  'use strict';

  // ── B Line Market Temperature Mini Card ────────────────────────
  // 最小适配：保留原 mt-mini-* 结构与静态 fixture，不接 API / Runtime / Router，
  // 不新增数据源、不改展示规格。仅把渲染逻辑暴露为可被 Sidebar Registry 调用的
  // Renderer（html + hydrate）。

  // 卡片外壳（与原 market-temperature-mini.html 的 .mt-mini-card 结构一致）。
  // 挂 data-sidebar-card 供 Registry hydrate 阶段定位。
  function shellHtml() {
    return [
      '<section class="mt-mini-card" data-sidebar-card="market_temperature" aria-label="市场温度">',
      '  <div class="mt-mini-header">',
      '    <div>',
      '      <p class="mt-mini-kicker">Market Structure</p>',
      '      <h2 class="mt-mini-title">市场温度</h2>',
      '    </div>',
      '    <span class="mt-mini-status" data-mt-status>--</span>',
      '  </div>',
      '  <div class="mt-mini-metrics" data-mt-metrics></div>',
      '  <div class="mt-mini-themes">',
      '    <div class="mt-mini-section-title">主线热度</div>',
      '    <div class="mt-mini-theme-list" data-mt-themes></div>',
      '  </div>',
      '  <div class="mt-mini-footer">',
      '    <span class="mt-mini-risk" data-mt-risk>--</span>',
      '    <a class="mt-mini-link" href="#" aria-label="查看市场画像">查看市场画像 →</a>',
      '  </div>',
      '</section>'
    ].join('');
  }

  // 原 renderMarketTemperature(data)，仅增加可选 root 形参以支持作用域定位。
  // 行为与展示规格不变。
  function renderMarketTemperature(data, root) {
    var scope = root || document;
    var card = (scope.classList && scope.classList.contains('mt-mini-card'))
      ? scope
      : scope.querySelector('.mt-mini-card');
    if (!card || !data) return;

    card.querySelector('[data-mt-status]').textContent = data.status;
    card.querySelector('[data-mt-risk]').textContent = data.riskNote;

    card.querySelector('[data-mt-metrics]').innerHTML = data.metrics.map(function (item) {
      return [
        '<div class="mt-mini-metric">',
        '  <span class="mt-mini-metric-label">' + item.label + '</span>',
        '  <strong class="mt-mini-metric-value ' + (item.tone ? 'mt-mini-metric-value--' + item.tone : '') + '">' + item.value + '</strong>',
        '</div>'
      ].join('');
    }).join('');

    card.querySelector('[data-mt-themes]').innerHTML = data.themes.map(function (item) {
      return [
        '<div class="mt-mini-theme">',
        '  <span class="mt-mini-theme-name">' + item.name + '</span>',
        '  <strong class="mt-mini-theme-count">' + item.count + '</strong>',
        '</div>'
      ].join('');
    }).join('');
  }

  // 暴露函数供独立调用 / 测试。
  global.renderMarketTemperature = renderMarketTemperature;

  // 注册进 Sidebar Registry。template 名与 sidebar-registry.js 中
  // CARD_REGISTRY.market_temperature.template 对应。
  if (global.SidebarCards && typeof global.SidebarCards.registerRenderer === 'function') {
    global.SidebarCards.registerRenderer('market_temperature', {
      html: function () {
        return shellHtml();
      },
      hydrate: function (card, el) {
        renderMarketTemperature(global.marketTemperatureFixture, el);
      }
    });
  }
})(window);
