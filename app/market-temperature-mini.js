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

  function normalizeMarketContext(payload) {
    if (!payload || typeof payload !== 'object') return null;

    var metrics = payload.metrics || {};
    var context = payload.context || {};
    var themes = Array.isArray(payload.themes) ? payload.themes : [];
    var qc = payload._qc || {};

    function pickValue() {
      for (var i = 0; i < arguments.length; i += 1) {
        var value = arguments[i];
        if (value !== undefined && value !== null && value !== '') return value;
      }
      return '--';
    }

    var metricItems = [
      { label: '涨停', value: pickValue(metrics.limit_up_count, metrics.limit_up), tone: 'hot' },
      { label: '炸板', value: pickValue(metrics.broken_board_rate, metrics.break_rate) },
      { label: '溢价', value: pickValue(metrics.premium, metrics.open_premium), tone: 'positive' }
    ];

    var themeItems = themes.slice(0, 3).map(function (item) {
      if (typeof item === 'string') return { name: item, count: '--' };
      return {
        name: item.name || item.theme || item.sector || '未命名主线',
        count: pickValue(item.count, item.hot_count, item.score)
      };
    });

    if (!themeItems.length && context.top_sector) {
      themeItems.push({ name: context.top_sector, count: '--' });
    }

    return {
      title: payload.title || '市场温度',
      status: payload.status || payload.conclusion || context.market_preference || '降级显示',
      metrics: metricItems,
      themes: themeItems.length ? themeItems : (global.marketTemperatureFixture || {}).themes || [],
      riskNote: qc.status === 'success' ? '仅市场结构，不含操作建议' : '降级显示，仅作入口占位'
    };
  }

  function withFallbackNote(data) {
    var fallback = data || {};
    return {
      title: fallback.title || '市场温度',
      status: fallback.status || '降级显示',
      metrics: Array.isArray(fallback.metrics) ? fallback.metrics : [],
      themes: Array.isArray(fallback.themes) ? fallback.themes : [],
      riskNote: '降级显示，仅作入口占位'
    };
  }

  function hydrateMarketTemperature(el) {
    renderMarketTemperature(withFallbackNote(global.marketTemperatureFixture), el);

    if (!global.fetch) {
      renderMarketTemperature(withFallbackNote(global.marketTemperatureFixture), el);
      return;
    }
    fetch('/api/intel/market-context', { credentials: 'include' })
      .then(function (response) {
        if (!response.ok) throw new Error('HTTP ' + response.status);
        return response.json();
      })
      .then(function (payload) {
        var normalized = normalizeMarketContext(payload);
        if (normalized) renderMarketTemperature(normalized, el);
      })
      .catch(function () {
        renderMarketTemperature(withFallbackNote(global.marketTemperatureFixture), el);
      });
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
        hydrateMarketTemperature(el);
      }
    });
  }
})(window);
