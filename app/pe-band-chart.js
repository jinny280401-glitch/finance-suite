(function (global) {
  'use strict';

  // PE 分位带图 — Simply Wall St 风格
  // 纯描述性：只展示当前 PE 在近5年历史区间中的位置，不形成估值结论

  function getNested(obj, path) {
    if (!obj || typeof obj !== 'object') return null;
    var keys = path.split('.');
    var cur = obj;
    for (var i = 0; i < keys.length; i++) {
      if (cur == null || typeof cur !== 'object') return null;
      cur = cur[keys[i]];
    }
    return cur;
  }

  function parseNum(v) {
    if (v === null || v === undefined) return NaN;
    if (typeof v === 'number') return isFinite(v) ? v : NaN;
    if (typeof v === 'string') {
      var n = parseFloat(v.replace(/[,，%％]/g, ''));
      return isFinite(n) ? n : NaN;
    }
    return NaN;
  }

  // 从 API response 中提取 PE 相关数据（多路径兜底）
  function extractPEData(data) {
    if (!data || typeof data !== 'object') return null;

    // 尝试从 markdown 文本中提取 PE 数值
    var text = data.result || data.content || '';
    if (typeof text !== 'string') text = '';

    var peCurrent = null;
    var peHigh = null;
    var peLow = null;
    var pePct = null;
    var peMedian = null;

    // 优先从结构化字段提取
    var candidates = [
      'valuation', 'pe_data', 'pe_band', 'financials',
      'data_availability.valuation', 'trust_presentation.valuation'
    ];
    for (var i = 0; i < candidates.length; i++) {
      var section = getNested(data, candidates[i]);
      if (section && typeof section === 'object') {
        peCurrent = peCurrent || parseNum(section.pe_current) || parseNum(section.pe) || parseNum(section.current);
        peHigh = peHigh || parseNum(section.pe_5yr_high) || parseNum(section.pe_high) || parseNum(section.high);
        peLow = peLow || parseNum(section.pe_5yr_low) || parseNum(section.pe_low) || parseNum(section.low);
        pePct = pePct || parseNum(section.pe_percentile) || parseNum(section.percentile) || parseNum(section.pct);
        peMedian = peMedian || parseNum(section.pe_median) || parseNum(section.median);
      }
    }

    // 兜底：从顶层字段提取
    peCurrent = peCurrent || parseNum(data.pe_current) || parseNum(data.pe) || parseNum(data.current_pe);
    peHigh = peHigh || parseNum(data.pe_5yr_high) || parseNum(data.pe_high);
    peLow = peLow || parseNum(data.pe_5yr_low) || parseNum(data.pe_low);
    pePct = pePct || parseNum(data.pe_percentile);
    peMedian = peMedian || parseNum(data.pe_median);

    // 兜底：从 markdown 文本中解析 PE 数值
    // 匹配 "PE 16.87"、"市盈率 16.87"、"当前 PE：16.87" 等
    if (!peCurrent && text) {
      var peMatch = text.match(/(?:PE|市盈率|当前\s*PE)[：:]\s*([\d.]+)/i);
      if (peMatch) peCurrent = parseNum(peMatch[1]);
    }

    // 从 markdown 解析百分位
    if (!pePct && text) {
      var pctMatch = text.match(/(?:分位|百分位|percentile)[：:：\s]*(\d+\.?\d*)\s*[%％]/i);
      if (pctMatch) pePct = parseNum(pctMatch[1]);
    }

    if (!peCurrent || isNaN(peCurrent)) return null;

    // 计算百分位（如果未提供但区间数据存在）
    if ((!pePct || isNaN(pePct)) && peLow && peHigh && !isNaN(peLow) && !isNaN(peHigh)) {
      if (peHigh > peLow) {
        pePct = ((peCurrent - peLow) / (peHigh - peLow)) * 100;
      }
    }

    return {
      current: peCurrent,
      high: (peHigh && !isNaN(peHigh)) ? peHigh : null,
      low: (peLow && !isNaN(peLow)) ? peLow : null,
      median: (peMedian && !isNaN(peMedian)) ? peMedian : null,
      percentile: (pePct && !isNaN(pePct)) ? pePct : null
    };
  }

  // 检查估值数据是否可用
  function checkAvailability(data) {
    if (!data || typeof data !== 'object') return false;
    var trust = data.trust_presentation || data.presentation || data.data_availability || {};
    var valAvail = trust.valuation || trust;
    if (typeof valAvail === 'object') {
      var status = String(valAvail.status || valAvail.availability || '').toLowerCase();
      if (status === 'unavailable' || status === 'missing' || status === 'not_connected') return false;
    }
    return true;
  }

  function renderPEBandChart(data) {
    if (!data || !checkAvailability(data)) return '';

    var pe = extractPEData(data);
    if (!pe) return '';

    // 生成唯一 ID 避免多次分析冲突
    var id = 'pe-band-' + Date.now();

    var html = [
      '<div class="pe-band-chart" style="background:white;border-radius:14px;padding:24px;margin:16px 0;border:1px solid rgba(0,0,0,0.08);">',
      '  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:8px;">',
      '    <h3 style="margin:0;font-size:17px;font-weight:600;">PE 估值分位</h3>',
      '    <span style="font-size:12px;color:#86868b;">近 5 年历史区间 · 仅展示位置，不构成估值结论</span>',
      '  </div>',
      '  <canvas id="' + id + '" width="720" height="140" style="width:100%;max-width:720px;height:auto;"></canvas>',
      '  <div style="display:flex;justify-content:space-between;margin-top:12px;font-size:12px;color:#69717d;flex-wrap:wrap;">',
      '    <span>当前 PE <strong style="color:#101318;">' + pe.current.toFixed(2) + '</strong></span>',
      pe.percentile !== null ? ('    <span>处于近 5 年第 <strong style="color:#101318;">' + Math.round(pe.percentile) + '</strong> 百分位</span>') : '',
      '  </div>',
      '  <div style="margin-top:8px;font-size:11px;color:#a1a1a6;">数据基于可用估值源，不构成买入/卖出/持有建议。</div>',
      '</div>'
    ].join('');

    // 延迟绘制（DOM 插入后）
    setTimeout(function () {
      drawPEBand(id, pe);
    }, 50);

    return html;
  }

  function drawPEBand(canvasId, pe) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;

    var ctx = canvas.getContext('2d');
    var dpr = window.devicePixelRatio || 1;
    var W = canvas.clientWidth || 720;
    var H = 140;

    canvas.width = W * dpr;
    canvas.height = H * dpr;
    ctx.scale(dpr, dpr);

    var padLeft = 50;
    var padRight = 50;
    var barY = 55;
    var barH = 24;
    var barW = W - padLeft - padRight;
    var barLeft = padLeft;

    // 确定显示范围
    var lo = pe.low || Math.max(0, pe.current * 0.3);
    var hi = pe.high || pe.current * 2.0;
    if (lo >= hi) hi = lo * 2;
    // 扩大显示范围使当前值不贴边
    var range = hi - lo;
    lo = Math.max(0, lo - range * 0.1);
    hi = hi + range * 0.1;
    range = hi - lo;

    function xOf(v) { return barLeft + ((v - lo) / range) * barW; }

    var xCur = xOf(pe.current);

    // 背景色带（绿-黄-红渐变）
    var zones = [
      { stop: 0.35, color: '#e9f8f0' },
      { stop: 0.65, color: '#fff8f0' },
      { stop: 1.0, color: '#fff0ee' }
    ];

    // 背景条
    ctx.fillStyle = '#f5f5f7';
    ctx.beginPath();
    roundRect(ctx, barLeft, barY, barW, barH, 12);
    ctx.fill();

    // 色带分区
    zones.forEach(function (z) {
      var zx = barLeft + z.stop * barW;
      ctx.fillStyle = z.color;
      ctx.beginPath();
      var w = zx - barLeft;
      if (w > 0) roundRect(ctx, barLeft, barY, w, barH, 12);
      ctx.fill();
    });

    // 中位线（如果有）
    if (pe.median !== null) {
      var xMed = xOf(pe.median);
      ctx.strokeStyle = '#86868b';
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(xMed, barY - 6);
      ctx.lineTo(xMed, barY + barH + 6);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = '#86868b';
      ctx.font = '10px -apple-system, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('中位 ' + pe.median.toFixed(1), xMed, barY - 10);
    }

    // 当前 PE 指示器（三角+竖线）
    ctx.fillStyle = '#1d1d1f';
    ctx.beginPath();
    ctx.moveTo(xCur, barY + barH + 20);
    ctx.lineTo(xCur - 8, barY + barH + 8);
    ctx.lineTo(xCur + 8, barY + barH + 8);
    ctx.closePath();
    ctx.fill();

    // 指示线
    ctx.strokeStyle = '#1d1d1f';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(xCur, barY - 2);
    ctx.lineTo(xCur, barY + barH + 8);
    ctx.stroke();

    // 当前 PE 标签
    ctx.fillStyle = '#1d1d1f';
    ctx.font = 'bold 12px -apple-system, sans-serif';
    ctx.textAlign = 'center';
    var labelY = barY + barH + 38;
    ctx.fillText('当前 ' + pe.current.toFixed(2), xCur, labelY);

    // 百分位标签
    if (pe.percentile !== null) {
      ctx.fillStyle = '#69717d';
      ctx.font = '11px -apple-system, sans-serif';
      ctx.fillText('第 ' + Math.round(pe.percentile) + ' 百分位', xCur, labelY + 16);
    }

    // 端点标签
    ctx.fillStyle = '#69717d';
    ctx.font = '11px -apple-system, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(lo.toFixed(1), barLeft, barY + barH + 16);
    ctx.textAlign = 'right';
    ctx.fillText(hi.toFixed(1), barLeft + barW, barY + barH + 16);

    // 区间标签
    ctx.textAlign = 'left';
    ctx.fillText('低估', barLeft, barY - 14);
    ctx.textAlign = 'center';
    ctx.fillText('合理', barLeft + barW * 0.5, barY - 14);
    ctx.textAlign = 'right';
    ctx.fillText('高估', barLeft + barW, barY - 14);
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }

  global.renderPEBandChart = renderPEBand;
})(window);
