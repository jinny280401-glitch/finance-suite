"""
PDF export route — generates PDF reports from HTML content.
Extracted from routers/api.py for separation of concerns.
"""
import re
import html as html_lib
import logging
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from backend.app.auth import get_current_user
from backend.app.database import User

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


class ExportPdfRequest(BaseModel):
    query: str = "Finance Suite 报告"
    html: str = ""


def _safe_pdf_filename(text: str) -> str:
    text = text or "finance-report"
    text = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text)
    text = text.strip("-")
    return text[:60] or "finance-report"


def _sanitize_report_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    cleaned = re.sub(r"(?is)<(script|iframe|object|embed)[^>]*>.*?</\1>", "", raw_html)
    cleaned = re.sub(r"(?is)\s+on[a-z]+\s*=\s*(['\"]).*?\1", "", cleaned)
    cleaned = re.sub(r"(?is)\s+on[a-z]+\s*=\s*[^\s>]+", "", cleaned)
    cleaned = re.sub(r"(?is)(href|src)\s*=\s*(['\"])\s*javascript:.*?\2", r'\1="#"', cleaned)
    return cleaned.strip()


def _build_pdf_html(query: str, body_html: str) -> str:
    safe_query = html_lib.escape(query or "股票分析报告")
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_body = _sanitize_report_html(body_html)

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{safe_query} - Finance Suite 分析报告</title>
  <style>
    @page {{ size: A4; margin: 18mm 16mm; }}
    body {{
      font-family: "Noto Sans CJK SC", "Noto Sans CJK", "Microsoft YaHei", "PingFang SC", sans-serif;
      color: #111827;
      font-size: 12px;
      line-height: 1.72;
      background: #ffffff;
    }}
    h1, h2, h3 {{ color: #0f172a; page-break-after: avoid; }}
    h1 {{ font-size: 24px; margin: 0 0 12px; }}
    h2 {{ font-size: 18px; margin-top: 24px; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; }}
    h3 {{ font-size: 15px; margin-top: 18px; }}
    p {{ margin: 0 0 9px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 11px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f3f4f6; font-weight: 700; }}
    blockquote {{ margin: 12px 0; padding-left: 12px; border-left: 3px solid #2563eb; color: #4b5563; }}
    pre, code {{
      font-family: "Noto Sans Mono CJK SC", "SFMono-Regular", Menlo, monospace;
      background: #f8fafc;
      border-radius: 4px;
    }}
    pre {{ padding: 10px; white-space: pre-wrap; word-break: break-word; }}
    img {{ max-width: 100%; height: auto; }}
    .report-header {{ margin-bottom: 22px; padding-bottom: 12px; border-bottom: 2px solid #111827; }}
    .subtitle {{ color: #6b7280; font-size: 11px; }}
    .disclaimer {{
      margin-top: 28px;
      padding: 12px;
      background: #fffbeb;
      border: 1px solid #fde68a;
      color: #92400e;
      font-size: 11px;
    }}
  </style>
</head>
<body>
  <div class="report-header">
    <h1>{safe_query} - Finance Suite 分析报告</h1>
    <div class="subtitle">生成时间：{generated_at}</div>
  </div>
  <main>{safe_body}</main>
  <div class="disclaimer">
    风险提示：本报告由 Finance Suite 自动生成，仅供研究参考，不构成任何投资建议。市场有风险，投资需谨慎。
  </div>
</body>
</html>"""


def _build_report_pdf(query: str, body_html: str) -> bytes:
    from weasyprint import HTML

    full_html = _build_pdf_html(query, body_html)
    return HTML(string=full_html, base_url=".").write_pdf()


@router.post("/export-pdf")
async def export_pdf(
    req: ExportPdfRequest,
    user: User = Depends(get_current_user),
):
    if not req.html or not req.html.strip():
        raise HTTPException(status_code=400, detail="没有可导出的报告内容")

    try:
        pdf_bytes = _build_report_pdf(req.query or "Finance Suite", req.html)
    except Exception as e:
        logger.exception("export_pdf failed")
        raise HTTPException(status_code=500, detail=f"PDF生成失败: {e}")

    filename = quote(f"finance-report-{_safe_pdf_filename(req.query)}.pdf")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
            "Cache-Control": "no-store",
        },
    )
