(function (global) {
  'use strict';

  var STORAGE_KEY = 'fs_sidebar_cards_v1';

  // ── Card Registry ──────────────────────────────────────────────
  // 每张卡片声明 template，决定由哪个 Renderer 渲染。
  // Sidebar Core 不识别任何具体 card key，只按 template 调度。
  var CARD_REGISTRY = {
    market_temperature: {
      key: 'market_temperature',
      title: '市场温度',
      description: '市场结构摘要 · 仅上下文',
      enabled: true,
      order: 10,
      renderable: true,
      template: 'market_temperature'
    },
    meeting_summary: {
      key: 'meeting_summary',
      title: '会议纪要',
      description: '会议 / 访谈 → 结构化报告',
      enabled: true,
      order: 20,
      renderable: true,
      template: 'skill_link',
      skill: 'meeting',
      icon: 'document'
    },
    video_analysis: {
      key: 'video_analysis',
      title: '视频拆解',
      description: '视频 → 字幕 → 知识点',
      enabled: true,
      order: 30,
      renderable: true,
      template: 'skill_link',
      skill: 'video',
      icon: 'video'
    }
  };

  // ── Renderer Registry ──────────────────────────────────────────
  // template -> { html(card), hydrate(card, el) }
  // 渲染逻辑全部从 Sidebar Core 解耦；新增卡片只需注册新 Renderer，
  // 不需要修改本文件的调度流程。
  var RENDERERS = {};

  function registerRenderer(template, renderer) {
    if (!template || !renderer || typeof renderer.html !== 'function') return;
    RENDERERS[template] = renderer;
  }

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function getDefaultConfig() {
    return Object.keys(CARD_REGISTRY).reduce(function (config, key) {
      config[key] = {
        enabled: CARD_REGISTRY[key].enabled,
        order: CARD_REGISTRY[key].order
      };
      return config;
    }, {});
  }

  function normalizeConfig(rawConfig) {
    var defaults = getDefaultConfig();
    var config = clone(defaults);
    var raw = rawConfig && typeof rawConfig === 'object' ? rawConfig : {};

    Object.keys(CARD_REGISTRY).forEach(function (key) {
      var item = raw[key] || {};
      if (typeof item.enabled === 'boolean') config[key].enabled = item.enabled;
      var order = Number(item.order);
      if (Number.isFinite(order)) config[key].order = order;
    });

    return config;
  }

  function loadConfig() {
    try {
      return normalizeConfig(JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'));
    } catch (error) {
      return getDefaultConfig();
    }
  }

  function saveConfig(config) {
    var normalized = normalizeConfig(config);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(normalized));
    return normalized;
  }

  function resetConfig() {
    localStorage.removeItem(STORAGE_KEY);
    return getDefaultConfig();
  }

  function getCards(options) {
    var opts = options || {};
    var config = normalizeConfig(opts.config || loadConfig());
    return Object.keys(CARD_REGISTRY)
      .map(function (key) {
        var card = clone(CARD_REGISTRY[key]);
        card.enabled = config[key].enabled;
        card.order = config[key].order;
        return card;
      })
      .filter(function (card) {
        if (opts.includeDisabled !== true && !card.enabled) return false;
        if (opts.includeReserved !== true && !card.renderable) return false;
        return true;
      })
      .sort(function (a, b) {
        if (a.order !== b.order) return a.order - b.order;
        return a.key.localeCompare(b.key);
      });
  }

  function iconSvg(icon) {
    if (icon === 'video') {
      return '<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="5" width="16" height="14" rx="2"></rect><polygon points="22 7 16 12 22 17 22 7"></polygon></svg>';
    }
    return '<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"></path><polyline points="15 3 15 8 20 8"></polyline></svg>';
  }

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // ── Built-in Renderer: skill_link ──────────────────────────────
  // 通用技能入口卡片。其它卡片不在 Core 内特判。
  registerRenderer('skill_link', {
    html: function (card) {
      return [
        '<a href="#" class="side-item" data-sidebar-card="' + escapeHtml(card.key) + '" data-skill="' + escapeHtml(card.skill || '') + '">',
        '  <span class="side-item__icon" aria-hidden="true">' + iconSvg(card.icon) + '</span>',
        '  <div class="side-item__body">',
        '    <div class="side-item__name">' + escapeHtml(card.title) + '</div>',
        '    <div class="side-item__desc">' + escapeHtml(card.description) + '</div>',
        '  </div>',
        '  <span class="side-item__arrow" aria-hidden="true">→</span>',
        '</a>'
      ].join('');
    }
  });

  // ── Renderer dispatch ──────────────────────────────────────────
  // Sidebar Core 的唯一职责：按 card.template 查表，调 Renderer。
  function renderCardHtml(card) {
    var renderer = RENDERERS[card.template];
    if (!renderer) return '';
    return renderer.html(card) || '';
  }

  function renderSidebar(container, options) {
    var cards = getCards(options);
    if (!container) return cards;

    container.innerHTML = cards
      .map(function (card) { return renderCardHtml(card); })
      .join('');

    // hydrate 阶段：renderer 可在 DOM 插入后填充数据（如 market_temperature）
    cards.forEach(function (card) {
      var renderer = RENDERERS[card.template];
      if (renderer && typeof renderer.hydrate === 'function') {
        var el = container.querySelector('[data-sidebar-card="' + card.key + '"]');
        renderer.hydrate(card, el);
      }
    });

    return cards;
  }

  global.SidebarCards = {
    registry: CARD_REGISTRY,
    storageKey: STORAGE_KEY,
    getDefaultConfig: getDefaultConfig,
    loadConfig: loadConfig,
    saveConfig: saveConfig,
    resetConfig: resetConfig,
    getCards: getCards,
    registerRenderer: registerRenderer,
    renderSidebar: renderSidebar
  };
})(window);
