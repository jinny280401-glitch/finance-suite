(function (global) {
  'use strict';

  // ── B-Line Morning Brief Mini Card ──────────────────────────────────
  // 最小适配：保持与 market-temperature-mini.js 完全一致的渲染器协议
  //（IIFE + var, SidebarCards.registerRenderer, shellHtml / hydrate），
  // 因此工作台核心调度不需要任何修改。
  //
  // 数据来源：brief-payload-builder.py 产出的
  //   /data/morning_brief/latest.json
  // 该 JSON 本身是 Codex automation 9:25 落盘 markdown / HTML 之后的镜像，
  // 本卡不再调 MCP，零网络开销（除一次同源 GET）。

  var PAYLOAD_URL = '/data/morning_brief/latest.json';
  var FETCH_TIMEOUT_MS = 5000;
  var STATE_LABELS = {
    fresh: '今日 09:25',
    stale: '缓存中',
    empty: '暂无数据'
  };

  function shellHtml() {
    return [
      '<section class="mb-mini-card" data-sidebar-card="morning_brief" aria-label="今日简报">',
      '  <div class="mb-mini-header">',
      '    <div>',
      '      <p class="mb-mini-kicker">D13 · Morning Brief</p>',
      '      <h2 class="mb-mini-title">今日简报</h2>',
      '    </div>',
      '    <span class="mb-mini-status" data-mb-status>--</span>',
      '  </div>',
      '  <p class="mb-mini-verdict" data-mb-verdict>暂无简报</p>',
      '  <div class="mb-mini-drivers" data-mb-drivers></div>',
      '  <div class="mb-mini-footer">',
      '    <span class="mb-mini-meta" data-mb-meta>--</span>',
      '    <button type="button" class="mb-mini-link" data-mb-open-brief>',
      '      打开完整简报 <span aria-hidden="true">→</span>',
      '    </button>',
      '  </div>',
      '</section>'
    ].join('');
  }

  // ── Normalizer ─────────────────────────────────────────────────────
  function normalizeBriefPayload(payload) {
    if (!payload || typeof payload !== 'object' || !Array.isArray(payload.drivers)) {
      return emptyFallbackState('数据格式异常');
    }

    var rawStatus = String(payload.status || '').toLowerCase();
    if (rawStatus !== 'fresh' && rawStatus !== 'stale' && rawStatus !== 'empty') {
      return emptyFallbackState('未知状态');
    }

    return {
      status: rawStatus,
      statusLabel: STATE_LABELS[rawStatus],
      verdict: payload.verdict || '暂无简报内容',
      drivers: payload.drivers.map(function (d) {
        return {
          key: d.key || 'unknown',
          label: d.label || '--',
          value: d.value || '--',
          tone: d.tone || 'muted'
        };
      }),
      meta: payload.generated_at
        ? '生成于 ' + payload.generated_at
        : ''
    };
  }

  function emptyFallbackState(reason) {
    return {
      status: 'empty',
      statusLabel: STATE_LABELS.empty,
      verdict: reason || '今日暂无 Morning Brief · 等待 09:25 自动化',
      drivers: [
        { key: 'pmi_official', label: 'CN PMI 官方',  value: '--', tone: 'muted' },
        { key: 'pmi_private',  label: 'CN PMI RatingDog', value: '--', tone: 'muted' },
        { key: 'brent',        label: 'Brent 油价',  value: '--', tone: 'muted' },
        { key: 'us_jobs',      label: '今晚关键事件', value: '--', tone: 'muted' }
      ],
      meta: '降级显示 · ' + (reason || 'payload 不可用')
    };
  }

  // ── Hydrate: fetch with timeout, fall back to empty ────────────────
  function hydrateMorningBrief(el) {
    renderMorningBrief(emptyFallbackState('加载中…'), el);

    if (!global.fetch) {
      renderMorningBrief(emptyFallbackState('当前浏览器不支持 fetch'), el);
      return;
    }

    var controller = (typeof AbortController === 'function') ? new AbortController() : null;
    var timeoutId = null;
    if (controller) {
      timeoutId = setTimeout(function () { controller.abort(); }, FETCH_TIMEOUT_MS);
    }

    fetch(PAYLOAD_URL, { signal: controller ? controller.signal : undefined })
      .then(function (response) {
        if (!response.ok) throw new Error('HTTP ' + response.status);
        return response.json();
      })
      .then(function (payload) {
        var normalized = normalizeBriefPayload(payload);
        renderMorningBrief(normalized, el);
      })
      .catch(function (error) {
        var reason = error && error.name === 'AbortError'
          ? '加载超时（' + (FETCH_TIMEOUT_MS / 1000) + 's）'
          : '暂时无法访问简报缓存';
        renderMorningBrief(emptyFallbackState(reason), el);
      })
      .then(function () {
        if (timeoutId) clearTimeout(timeoutId);
      });
  }

  // ── Render ─────────────────────────────────────────────────────────
  function renderMorningBrief(data, root) {
    var scope = root || document;
    var card = (scope.classList && scope.classList.contains('mb-mini-card'))
      ? scope
      : scope.querySelector('.mb-mini-card');
    if (!card || !data) return;

    // Status badge: status 决定状态色（fresh = 琥珀, stale = 灰, empty = 灰）
    var statusEl = card.querySelector('[data-mb-status]');
    statusEl.textContent = data.statusLabel;
    statusEl.dataset.mbStatus = data.status;

    // Verdict
    card.querySelector('[data-mb-verdict]').textContent = data.verdict;

    // Drivers: 4 个数据格
    card.querySelector('[data-mb-drivers]').innerHTML = data.drivers.map(function (item) {
      var toneClass = item.tone ? ' mb-mini-driver-value--' + item.tone : '';
      return [
        '<div class="mb-mini-driver" title="' + escapeAttr(item.label) + '">',
        '  <span class="mb-mini-driver-label">' + escapeText(item.label) + '</span>',
        '  <strong class="mb-mini-driver-value' + toneClass + '">',
                  escapeText(item.value) + '</strong>',
        '</div>'
      ].join('');
    }).join('');

    // Meta footer text
    card.querySelector('[data-mb-meta]').textContent = data.meta || '';

    // Open-brief button — pushState routing
    var openBtn = card.querySelector('[data-mb-open-brief]');
    if (openBtn && !openBtn.dataset.mbBound) {
      openBtn.dataset.mbBound = '1';
      openBtn.addEventListener('click', function (event) {
        event.preventDefault();
        // 防御性 fallback：如果浏览器不支持 history.pushState，
        // 至少还能让 hash 变（触发 hashchange 监听器）。
        if (global.history && typeof global.history.pushState === 'function') {
          global.history.pushState(
            { modal: 'morning-brief' },
            '',
            '#/morning-brief'
          );
        } else {
          global.location.hash = '#/morning-brief';
        }
        // 直接触发显示（pushState 不一定让 inline listener 立刻收到 event）
        if (global.MorningBriefModal && typeof global.MorningBriefModal.show === 'function') {
          global.MorningBriefModal.show();
        }
      });
    }
  }

  function escapeText(value) {
    return String(value == null ? '' : value);
  }
  function escapeAttr(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .replace(/</g, '&lt;');
  }

  // 暴露给独立测试 / 调试
  global.renderMorningBrief = renderMorningBrief;
  global.normalizeBriefPayload = normalizeBriefPayload;

  // ── Register renderer ──────────────────────────────────────────────
  if (global.SidebarCards && typeof global.SidebarCards.registerRenderer === 'function') {
    global.SidebarCards.registerRenderer('morning_brief', {
      html: function () { return shellHtml(); },
      hydrate: function (card, el) { hydrateMorningBrief(el); }
    });
  }
})(window);
