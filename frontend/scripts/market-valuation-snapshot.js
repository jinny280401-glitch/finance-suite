(function (global) {
  'use strict';

  // 指数估值快照 — 数据源：东方财富指数估值接口（自动接通）
  // earnings_yield = 1 / PE(TTM) × 100%（数学恒等）
  // band 分层：按 PE(TTM) 估值温度（hot=相对低估/mid=中性/cool=相对高估）
  // 注：银行螺丝钉自定义指数（中证红利低波动、沪港深红利低波、中证价值、港股红利、中证A50）
  //     东方财富无同名口径，已替换为可对齐的标准指数；不编造缺口数据。

  global.marketValuationSnapshot = {
    snapshot_date: '2026-07-17',
    source_title: '东方财富指数估值（自动接口）',
    source_url: null,
    rows: [
      { name: '中证红利', earnings_yield: '12.12%', pe: '8.25', pb: '0.79', roe: '8.76%', band: 'hot' },
      { name: '恒生指数', earnings_yield: '8.76%', pe: '11.41', pb: '1.19', roe: '10.43%', band: 'hot' },
      { name: '上证180', earnings_yield: '8.50%', pe: '11.77', pb: '1.18', roe: '9.25%', band: 'hot' },
      { name: '沪深300', earnings_yield: '7.15%', pe: '13.99', pb: '1.40', roe: '9.31%', band: 'hot' },
      { name: '深证100', earnings_yield: '3.57%', pe: '28.00', pb: '3.00', roe: '10.35%', band: 'mid' },
      { name: '中证500', earnings_yield: '2.81%', pe: '35.54', pb: '2.35', roe: '6.39%', band: 'mid' },
      { name: '创业板指', earnings_yield: '2.29%', pe: '43.76', pb: '5.87', roe: '13.40%', band: 'cool' },
      { name: '科创50', earnings_yield: '0.48%', pe: '209.90', pb: '8.75', roe: '4.15%', band: 'cool' }
    ],
    _qc: {
      status: 'success',
      source_type: 'provider_api',
      provider: '东方财富',
      provider_state: 'connected',
      blocked_fields: [],
      allowed_use: ['market_portrait_sidebar', 'demo_preview'],
      reviewed: true,
      notes: '数据源已从手工截图切换为东方财富指数估值接口。PE/PB/股息率含5日历史，ROE为最新TTM，盈利收益率由1/PE计算。银行螺丝钉自定义指数（红利低波等）无同名口径已用标准指数替换。band为估值温度描述，不构成买卖建议。'
    }
  };
})(window);
