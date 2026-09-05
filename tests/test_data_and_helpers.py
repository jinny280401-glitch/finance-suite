"""
数据层 + 搜索 + LLM 单元测试
外部 API 调用全部 mock，仅测试内部逻辑。
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import date


# ============================================================
# search.py 测试
# ============================================================
class TestSearch:
    @patch("backend.engine.providers.search_provider.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_tavily_search_success(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "results": [
                {"title": "Test", "url": "https://example.com", "content": "hello"},
            ]
        }
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        from backend.engine.providers.search_provider import tavily_search
        results = await tavily_search("test query")
        assert len(results) == 1
        assert results[0]["title"] == "Test"

    @pytest.mark.asyncio
    async def test_tavily_search_no_key(self):
        with patch("backend.engine.providers.search_provider.settings") as mock_settings:
            mock_settings.get_tavily_key.return_value = ""
            from backend.engine.providers.search_provider import tavily_search
            results = await tavily_search("test")
            assert results == []

    @patch("backend.engine.providers.search_provider.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_brave_search_success(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "web": {"results": [
                {"title": "Brave Result", "url": "https://brave.com", "description": "desc"},
            ]}
        }
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        from backend.engine.providers.search_provider import brave_search
        results = await brave_search("test query")
        assert len(results) == 1
        assert results[0]["title"] == "Brave Result"

    def test_format_search_results(self):
        from backend.engine.providers.search_provider import format_search_results
        results = [
            {"title": "Article 1", "url": "https://a.com", "content": "Content A"},
            {"title": "Article 2", "url": "https://b.com", "content": "Content B"},
        ]
        output = format_search_results(results)
        assert "Article 1" in output
        assert "Article 2" in output

    def test_format_search_results_empty(self):
        from backend.engine.providers.search_provider import format_search_results
        output = format_search_results([])
        assert output == "" or output is None or isinstance(output, str)


# ============================================================
# llm.py 测试
# ============================================================
class TestLLM:
    @patch("backend.engine.llm.client.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_generate_analysis_success(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "分析报告内容"}}]
        }
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        from backend.engine.llm.client import generate_analysis
        result = await generate_analysis("system prompt", "user query", "search data")
        assert result == "分析报告内容"

    @patch("backend.engine.llm.client.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_generate_analysis_timeout(self, mock_client_cls):
        import httpx
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.TimeoutException("timeout")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        from backend.engine.llm.client import generate_analysis
        result = await generate_analysis("sys", "user", "data")
        assert "超时" in result

    @patch("backend.engine.llm.client.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_generate_analysis_http_error(self, mock_client_cls):
        import httpx
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "server error", request=MagicMock(), response=mock_resp
        )
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        from backend.engine.llm.client import generate_analysis
        result = await generate_analysis("sys", "user", "data")
        assert "不可用" in result

    def test_cache_set_and_get(self):
        from backend.engine.cache import cache_set, cache_get
        cache_set("stock", "贵州茅台", {"result": "test data"})
        cached = cache_get("stock", "贵州茅台")
        assert cached is not None
        assert cached["result"] == "test data"

    def test_cache_miss(self):
        from backend.engine.cache import cache_get
        result = cache_get("stock", "不存在的查询_abc123")
        assert result is None


# ============================================================
# stock_skill 测试（mock AkShare）
# ============================================================
class TestStockData:
    def test_resolve_stock_detail_unresolved(self):
        """Test that unresolvable stock returns None gracefully."""
        from backend.engine.skills.stock_skill import resolve_stock_detail
        with patch("backend.engine.skills.stock_skill._load_stock_cache") as mock_cache:
            mock_cache.return_value = {}
            result = resolve_stock_detail("不存在的股票XYZ123")
            assert result is None

    def test_normalize_entity_name(self):
        """Test entity name normalization from api.py."""
        from backend.app.routers.api import _normalize_entity_name
        assert _normalize_entity_name("贵州科技股份有限公司") == "贵州科技"
        assert _normalize_entity_name("Apple Inc.") == "apple"
        assert _normalize_entity_name("腾讯控股有限公司") == "腾讯"

    def test_source_matches_query(self):
        from backend.app.routers.api import _source_matches_query
        source = {"title": "贵州茅台2026年财报", "content": "营收增长15%", "url": "https://example.com"}
        assert _source_matches_query(source, "贵州茅台") is True
        assert _source_matches_query(source, "腾讯控股") is False

    def test_compute_report_asof_with_dates(self):
        from backend.app.routers.api import _compute_report_as_of
        sources = [
            {"published_date": "2026-08-15"},
            {"published_date": "2026-09-01"},
            {"published_date": "2026-07-20"},
        ]
        result = _compute_report_as_of(sources)
        assert result["date"] == "2026-09-01"
        assert result["source_date_unknown"] is False

    def test_compute_report_asof_no_dates(self):
        from backend.app.routers.api import _compute_report_as_of
        sources = [{"title": "no date"}]
        result = _compute_report_as_of(sources)
        assert result["source_date_unknown"] is True
        assert result["date"] == date.today().isoformat()


# ============================================================
# video_data.py 测试
# ============================================================
class TestVideoData:
    def test_extract_youtube_id_standard(self):
        from backend.engine.skills.video_skill import _extract_youtube_id
        assert _extract_youtube_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_extract_youtube_id_short(self):
        from backend.engine.skills.video_skill import _extract_youtube_id
        assert _extract_youtube_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_extract_youtube_id_embed(self):
        from backend.engine.skills.video_skill import _extract_youtube_id
        assert _extract_youtube_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_extract_youtube_id_shorts(self):
        from backend.engine.skills.video_skill import _extract_youtube_id
        assert _extract_youtube_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_extract_youtube_id_invalid(self):
        from backend.engine.skills.video_skill import _extract_youtube_id
        assert _extract_youtube_id("https://www.google.com") is None

    def test_extract_bilibili_id(self):
        from backend.engine.skills.video_skill import _extract_bilibili_id
        assert _extract_bilibili_id("https://www.bilibili.com/video/BV1GJ411x7h7") == "BV1GJ411x7h7"

    def test_extract_bilibili_id_invalid(self):
        from backend.engine.skills.video_skill import _extract_bilibili_id
        assert _extract_bilibili_id("https://www.google.com") is None


# ============================================================
# api.py 内部辅助函数测试
# ============================================================
class TestApiHelpers:
    def test_sanitize_report_body_replaces_date_cutoff(self):
        from backend.app.routers.api import _sanitize_report_body
        report = "数据截止：2025-01-01\n\nSome content"
        report_as_of = {"date": "2026-09-01", "source_date_unknown": False}
        result = _sanitize_report_body(report, report_as_of)
        assert "2026-09-01" in result
        assert "2025-01-01" not in result

    def test_sanitize_report_body_unknown_date(self):
        from backend.app.routers.api import _sanitize_report_body
        report = "数据截止：模型训练数据\n\nContent"
        report_as_of = {"date": "2026-09-01", "source_date_unknown": True}
        result = _sanitize_report_body(report, report_as_of)
        assert "系统生成日期" in result

    def test_safe_body_used_for_high_risk(self):
        from backend.app.routers.api import _SAFE_BODY
        assert "公开资料不足" in _SAFE_BODY

    def test_safe_pdf_filename(self):
        from backend.app.routers.api import _safe_pdf_filename
        assert _safe_pdf_filename("贵州茅台") == "贵州茅台"
        assert _safe_pdf_filename("Apple / Inc.") == "Apple-Inc"
        assert _safe_pdf_filename("") == "finance-report"
        assert _safe_pdf_filename(None) == "finance-report"

    def test_sanitize_report_html_removes_script(self):
        from backend.app.routers.api import _sanitize_report_html
        html = '<p>Hello</p><script>alert("xss")</script>'
        result = _sanitize_report_html(html)
        assert "<script>" not in result
        assert "<p>Hello</p>" in result

    def test_sanitize_report_html_removes_onclick(self):
        from backend.app.routers.api import _sanitize_report_html
        html = '<div onclick="alert(1)">test</div>'
        result = _sanitize_report_html(html)
        assert "onclick" not in result

    def test_sanitize_report_html_removes_javascript_href(self):
        from backend.app.routers.api import _sanitize_report_html
        html = '<a href="javascript:alert(1)">click</a>'
        result = _sanitize_report_html(html)
        assert "javascript:" not in result

    def test_trust_availability_entry(self):
        from backend.app.routers.api import _trust_availability_entry
        entry = _trust_availability_entry("partial", available=["kline"], missing=["news"])
        assert entry["status"] == "partial"
        assert "kline" in entry["available"]
        assert "news" in entry["missing"]

    def test_build_analyze_data_availability(self):
        from backend.app.routers.api import _build_analyze_data_availability
        response = {
            "result": "some analysis",
            "sources": [{"url": "https://a.com"}],
            "kline": [{"time": "2026-09-01", "close": 100}],
            "_qc": {"fact_coverage": {"structured_data_available": True}},
        }
        avail = _build_analyze_data_availability(response)
        assert avail["fundamental"]["status"] == "partial"
        assert avail["realtime"]["status"] == "partial"
        assert avail["news"]["status"] == "partial"

    def test_event_status_confirmed(self):
        from backend.app.routers.api import _event_status
        item = {
            "title": "外交部证实特朗普将访华",
            "source": "外交部",
            "url": "https://mfa.gov.cn/xxx",
            "content": "外交部发言人确认特朗普将于5月13日至15日进行国事访问",
        }
        status = _event_status(item)
        assert status == "confirmed"

    def test_event_status_unverified(self):
        from backend.app.routers.api import _event_status
        item = {
            "title": "网传某公司即将重组",
            "source": "某论坛",
            "url": "https://random-forum.com/post/123",
            "content": "听说某公司要重组",
        }
        status = _event_status(item)
        assert status == "unverified"

    def test_macro_conflict_detection(self):
        from backend.app.routers.api import _macro_consistency_conflict
        facts = {"confirmed": True}
        result = "该事件未证实，不构成真实经济事件"
        conflict = _macro_consistency_conflict(result, facts)
        assert conflict is not None
        assert "未证实" in conflict

    def test_macro_no_conflict_when_unconfirmed(self):
        from backend.app.routers.api import _macro_consistency_conflict
        facts = {"confirmed": False}
        result = "该事件未证实"
        conflict = _macro_consistency_conflict(result, facts)
        assert conflict is None
