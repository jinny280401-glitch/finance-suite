# Auction Signal Evidence v0.1

Status: `PARTIAL`

Purpose: record a real, reproducible observation chain from the existing auction provider. This is evidence validation, not a trading experiment, profitability test, or recommendation.

## 1. Data Source And Time

| Field | Value |
| --- | --- |
| Retrieval time | 2026-07-24 09:56:51 +08:00 |
| Provider | Eastmoney data exposed through AkShare |
| Existing implementation | `/Users/Zhuanz/finance-suite/scripts/auction_data.py` |
| Provider dimension | `previous_zt` (`ak.stock_zt_pool_previous_em`) |
| Preserved raw capture | `/Users/Zhuanz/finance-suite/docs/signal-validation-v0.1/evidence/auction_signal_snapshot_20260724_095651.json` |
| Raw capture SHA-256 | `4532569999bdd12e9863c1c835893b982f3c2ce95d69ebd9d6520d236263eac0` |
| Production cross-check | `https://www.touziagent.com/api/intel/market-context` at 2026-07-24 09:56:31 +08:00 |
| Preserved cross-check | `/Users/Zhuanz/finance-suite/docs/signal-validation-v0.1/evidence/market_context_crosscheck_20260724_095631.json` |
| Cross-check SHA-256 | `72a17651b6a8885a228c64181ecb9c72e9bab0abc40c4edf01a49e7df1bfbff4` |

The production cross-check returned `_qc.status=partial`, `source_type=real`, and explicitly blocked `previous_zt`, so it is not used as row-level evidence. The row-level samples below come from the local existing provider call and retain that provenance boundary.

## 2. Sampling Rule

The provider returned 116 `previous_zt` rows. To avoid selecting winners after seeing outcomes, the audit sample is deterministic: sort the complete returned set by six-digit stock code ascending and retain the first three rows. No row was removed because its observed return was negative.

Signal definition for this evidence window:

```text
previous trading day limit-up observation
AND provider field 昨日连板数 >= 1
AND provider field 昨日封板时间 is present
```

This is an observational signal object, not a buy instruction. The provider response does not carry an explicit effective-date field; `signal_date=2026-07-23` is inferred from the documented `previous_zt` semantics at the 2026-07-24 retrieval time. That inference keeps this report at `PARTIAL`.

## 3. Signal And Outcome Samples

Outcome label is descriptive only:

- `HIT`: T+1 change at the retrieval timestamp was greater than 0%.
- `MISS`: T+1 change at the retrieval timestamp was less than or equal to 0%.

It does not include fills, transaction costs, tradability, position sizing, or an executable entry price.

| signal_date | symbol | name | source | signal_reason | signal_time | outcome window | outcome evidence | evaluation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-07-23 | 000011 | 深物业A | Eastmoney/AkShare `previous_zt` | Previous-day limit-up; `昨日连板数=1`; `涨停统计=2/2` | 09:53:30 (provider field, date inferred) | T+1 at 2026-07-24 09:56:51 | latest 8.26; change +9.9867%; turnover 4.3914% | HIT |
| 2026-07-23 | 000017 | 深中华A | Eastmoney/AkShare `previous_zt` | Previous-day limit-up; `昨日连板数=1`; `涨停统计=2/1` | 09:50:15 (provider field, date inferred) | T+1 at 2026-07-24 09:56:51 | latest 5.96; change +4.9296%; turnover 2.4988% | HIT |
| 2026-07-23 | 000035 | 中国天楹 | Eastmoney/AkShare `previous_zt` | Previous-day limit-up; `昨日连板数=1`; `涨停统计=2/1` | 11:11:09 (provider field, date inferred) | T+1 at 2026-07-24 09:56:51 | latest 4.77; change -1.2422%; turnover 1.9961% | MISS |

## 4. Complete-Set Check

The deterministic samples above are accompanied by a complete-set check so the report cannot hide unfavorable rows:

| Metric | Observed value |
| --- | ---: |
| Returned rows | 116 |
| Positive at retrieval | 55 |
| Flat at retrieval | 0 |
| Negative at retrieval | 61 |
| Median change | -0.1620% |
| Mean change | +1.3633% |
| Minimum / maximum | -7.8227% / +19.9959% |

These values describe the provider snapshot only. They are not a backtest, win rate, excess return, or evidence that a strategy works.

## 5. Evidence Boundary

Verified:

- A real provider call returned symbol-level `previous_zt` rows.
- Signal reason, provider field time, symbol, and T+1 intraday observation can be retained in one evidence record.
- Both positive and negative outcomes are preserved.

Not verified:

- The response has no explicit provider-side effective date or retrieval identifier.
- The source was queried retrospectively on T+1; there is no immutable T-1 capture proving what the system knew before the outcome.
- T+0 close, T+1 close, executable entry, order, fill, costs, and slippage are absent.
- The production endpoint blocked `previous_zt` in the same time window.
- No strategy effectiveness, profitability, or actionable signal is established.

## 6. Verdict

`Auction Evidence: PARTIAL`

Real rows and a traceable observation mapping exist, but temporal provenance is not strong enough for `PASS` because the signal was not immutably captured before the observed T+1 outcome.
