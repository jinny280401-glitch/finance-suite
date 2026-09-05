(function (global) {
  'use strict';

  var ALLOWED_BANDS = { hot: true, mid: true, cool: true };
  var REQUIRED_USE = 'market_portrait_sidebar';

  function canRenderSnapshot(snapshot) {
    if (!snapshot || typeof snapshot !== 'object') return false;
    var qc = snapshot._qc || {};
    var status = String(qc.status || '').toLowerCase();
    var allowedUse = Array.isArray(qc.allowed_use) ? qc.allowed_use : [];
    var sourceType = String(qc.source_type || '').toLowerCase();

    var ALLOWED_SOURCE_TYPES = { manual_screenshot: true, rss_image: true, provider_api: true };
    if (status !== 'success' && status !== 'partial') return false;
    if (allowedUse.indexOf(REQUIRED_USE) === -1) return false;
    if (!ALLOWED_SOURCE_TYPES[sourceType]) return false;
    return Array.isArray(snapshot.rows) && snapshot.rows.length > 0;
  }

  function textCell(value) {
    var cell = document.createElement('span');
    cell.textContent = value == null || value === '' ? '--' : String(value);
    return cell;
  }

  function renderEmpty(container, sourceBadge) {
    var empty = document.createElement('div');
    empty.className = 'heat-empty';
    empty.textContent = '估值快照暂不可用。请先完成截图录入与人工核对。';
    container.replaceChildren(empty);
    if (sourceBadge) sourceBadge.textContent = '数据暂不可用';
  }

  function renderSnapshot(snapshot) {
    var rowsContainer = document.querySelector('[data-valuation-rows]');
    var sourceBadge = document.querySelector('[data-valuation-source]');
    if (!rowsContainer) return;

    if (!canRenderSnapshot(snapshot)) {
      renderEmpty(rowsContainer, sourceBadge);
      return;
    }

    var fragment = document.createDocumentFragment();
    snapshot.rows.forEach(function (item) {
      var row = document.createElement('div');
      var band = ALLOWED_BANDS[item.band] ? item.band : 'mid';
      row.className = 'heat-row ' + band;
      row.appendChild(textCell(item.name));
      row.appendChild(textCell(item.earnings_yield));
      row.appendChild(textCell(item.pe));
      row.appendChild(textCell(item.pb));
      row.appendChild(textCell(item.roe));
      fragment.appendChild(row);
    });
    rowsContainer.replaceChildren(fragment);

    if (sourceBadge) {
      var qc = snapshot._qc || {};
      var srcType = String(qc.source_type || '').toLowerCase();
      if (srcType === 'provider_api') {
        sourceBadge.textContent = (qc.provider || '东方财富') + ' · ' + snapshot.snapshot_date + ' · 自动接口';
      } else {
        sourceBadge.textContent = '手工截图 · ' + snapshot.snapshot_date + ' · 数据源未自动接通';
      }
    }
  }

  global.canRenderMarketValuationSnapshot = canRenderSnapshot;
  global.renderMarketValuationSnapshot = renderSnapshot;

  // Auto-render on load if snapshot available
  if (global.marketValuationSnapshot) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function() {
        renderSnapshot(global.marketValuationSnapshot);
      });
    } else {
      renderSnapshot(global.marketValuationSnapshot);
    }
  }
})(window);
