# Window 1 UI Evidence Pack

Date: 2026-06-29 13:24 CST

Owner: CB

Scope: live page UI / Presentation evidence only.

Not in scope:

- Contract consistency
- Production readiness
- Runtime recovery
- Synthetic payload rendering
- Local page substitution

## 1. stock.html Live Page Evidence

URL:

`https://www.touziagent.com/app/stock.html`

Fetch result:

- HTTP 200
- `content-type: text/html`
- `last-modified: Mon, 29 Jun 2026 05:08:27 GMT`
- `content-length: 35332`
- SHA256: `987fb94bf389cfbd89ef97073aa64b371c35e7ef04367cef89532dfad33878bc`

Required markers:

| Check | Evidence | Result |
|---|---|---|
| 可信度说明 | line 993 | PRESENT |
| 数据完整性摘要 | line 1000 | PRESENT |
| `renderTrustPresentation` | lines 909, 915, 984 | PRESENT |
| consumes `data_availability` | lines 964, 968 | PRESENT |
| consumes `section_data_usage` | line 1028 | PRESENT |
| `暂不可用` display logic | lines 942, 946, 952, 958, 1009, 1021 | PRESENT |
| staged loading | line 610, lines 651-655 | PRESENT |

Relevant live HTML snippets:

```text
610: <div class="loading-stage" id="loadingStage">正在匹配股票</div>
909: return renderTrustPresentation(null) + ...
915: let html = renderTrustPresentation(data);
964: return data.trust_presentation || data.presentation || data.data_availability || data._qc?.data_availability || {};
993: <div class="trust-panel__title">可信度说明</div>
1000: <div class="trust-panel__title">数据完整性摘要</div>
1028: return meta.section_data_usage || data?.section_data_usage || data?._qc?.section_data_usage || {};
```

## 2. deep-research.html Live Page Evidence

URL:

`https://www.touziagent.com/app/deep-research.html`

Fetch result:

- HTTP 200
- `content-type: text/html`
- `last-modified: Mon, 29 Jun 2026 05:08:28 GMT`
- `content-length: 30570`
- SHA256: `a2624808c33d669e037d07702872802ba857d0fb11da26bfa13d5b5dbb7a8652`

Required markers:

| Check | Evidence | Result |
|---|---|---|
| 可信度说明 | line 792 | PRESENT |
| 数据完整性摘要 | line 799 | PRESENT |
| `renderTrustPresentation` | lines 721, 733, 783 | PRESENT |
| consumes `data_availability` | lines 763, 767 | PRESENT |
| consumes `section_data_usage` | line 827 | PRESENT |
| `暂不可用` display logic | lines 741, 745, 751, 757, 808, 820 | PRESENT |
| staged loading | line 379, lines 412-416 | PRESENT |

Relevant live HTML snippets:

```text
379: <div class="loading-stage" id="loadingStage">正在匹配股票</div>
721: return renderTrustPresentation(data) + qcBadge + ...
733: return renderTrustPresentation(data) + qcBadge + ...
763: return data.trust_presentation || data.presentation || data.data_availability || data._qc?.data_availability || {};
792: <div class="trust-panel__title">可信度说明</div>
799: <div class="trust-panel__title">数据完整性摘要</div>
827: return meta.section_data_usage || data?.section_data_usage || data?._qc?.section_data_usage || {};
```

## 3. DOM / HTML Evidence Summary

Both live pages contain:

- `可信度说明`
- `数据完整性摘要`
- `data_availability`
- `section_data_usage`
- `暂不可用`
- `renderTrustPresentation`
- `getTrustMeta`

This proves the live page shell now includes the Trust Presentation implementation.

This does not prove real API rendering or Contract consistency.

## 4. Raw Leak Check

Method:

- Fetch live HTML.
- Strip `script`, `style`, and `noscript`.
- Inspect visible DOM text for:
  - `nan`
  - `null`
  - `None`
  - `N/A`

Results:

| Page | nan | null | None | N/A | Result |
|---|---:|---:|---:|---:|---|
| stock.html visible text | false | false | false | false | PASS |
| deep-research.html visible text | false | false | false | false | PASS |

Important note:

The raw HTML source contains these strings inside sanitizer code and regular expressions. Those are not user-visible leaks.

## 5. Traceability Mapping

The live UI code consumes the following fields:

- `data.trust_presentation`
- `data.presentation`
- `data.data_availability`
- `data._qc.data_availability`
- `section_data_usage`
- `data.section_data_usage`
- `data._qc.section_data_usage`

Evidence:

```text
return data.trust_presentation || data.presentation || data.data_availability || data._qc?.data_availability || {};
return meta.section_data_usage || data?.section_data_usage || data?._qc?.section_data_usage || {};
```

No Provider-specific field consumption was observed in the live page shell.

## 6. UI Evidence Verdict

UI Evidence Pack:

PASS

Meaning:

- Live pages now contain Trust Presentation Shell.
- Live visible DOM does not leak raw `nan/null/None/N/A`.
- UI shell consumes Runtime/QC presentation fields.

Not claimed:

- Production Ready
- Contract Consistency
- Acceptance PASS
- Runtime Capability Recovered
- Real 3-case API rendering PASS
