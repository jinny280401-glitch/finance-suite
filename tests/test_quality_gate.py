"""
质量门控 (Quality Gate) 单元测试
覆盖: QualityGate.check()、QualityRules、各规则验证器
"""
import pytest
from backend.engine.quality.core import QualityGate, QualityResult, QualityRule
from backend.engine.quality.rules import QualityRules


# ============================================================
# QualityGate 核心逻辑测试
# ============================================================
class TestQualityGate:
    def setup_method(self):
        self.gate = QualityGate()

    def test_check_passes_with_good_data(self):
        data = {
            "_qc": {
                "status": "success",
                "completeness": 0.95,
                "sources": ["url1", "url2", "url3"],
                "missing_dimensions": [],
                "stale_data": [],
            }
        }
        result = self.gate.check(data, QualityRules.stockData, round=1)
        assert result.passed is True
        assert result.score >= 0.8

    def test_check_fails_missing_qc(self):
        data = {}
        result = self.gate.check(data, QualityRules.stockData, round=1)
        assert result.passed is False
        assert "缺少 _qc 质检字段" in result.reject_reasons[0]

    def test_check_fails_low_completeness(self):
        data = {
            "_qc": {
                "status": "success",
                "completeness": 0.3,
                "sources": ["url1", "url2"],
                "missing_dimensions": ["财报", "估值"],
            }
        }
        result = self.gate.check(data, QualityRules.stockData, round=1)
        assert result.passed is False
        assert any("完整性" in r for r in result.reject_reasons)

    def test_check_fails_on_failure_status(self):
        data = {
            "_qc": {
                "status": "failure",
                "completeness": 0.9,
                "sources": ["url1", "url2"],
            }
        }
        result = self.gate.check(data, QualityRules.stockData, round=1)
        assert result.passed is False
        assert any("失败" in r for r in result.reject_reasons)

    def test_check_fails_insufficient_sources(self):
        data = {
            "_qc": {
                "status": "success",
                "completeness": 0.9,
                "sources": ["url1"],  # Only 1 source, need >= 2
            }
        }
        result = self.gate.check(data, QualityRules.stockData, round=1)
        assert result.passed is False
        assert any("信源" in r for r in result.reject_reasons)

    def test_check_max_rounds_exceeded(self):
        data = {"_qc": {"status": "failure", "completeness": 0, "sources": []}}
        result = self.gate.check(data, QualityRules.stockData, round=3)
        assert result.passed is False
        assert any("最大重试" in r for r in result.reject_reasons)

    def test_check_stale_data_detected(self):
        data = {
            "_qc": {
                "status": "success",
                "completeness": 0.9,
                "sources": ["url1", "url2"],
                "stale_data": ["财报数据(Q1)"],
            }
        }
        result = self.gate.check(data, QualityRules.stockData, round=1)
        assert result.passed is False
        assert any("过期" in r for r in result.reject_reasons)

    def test_finalize_passed(self):
        result = QualityResult(
            passed=True, round=1, score=0.9,
            data={"content": "test report"},
        )
        output = self.gate.finalize(result, lambda d: d["content"])
        assert "test report" in output
        assert "免责声明" in output or "不构成投资建议" in output

    def test_finalize_failed(self):
        result = QualityResult(
            passed=False, round=1, score=0.3,
            reject_reasons=["数据不足", "信源不足"],
        )
        output = self.gate.finalize(result, lambda d: "should not appear")
        assert "数据不足" in output
        assert "should not appear" not in output

    def test_flow_log_recorded(self):
        data = {
            "_qc": {
                "status": "success",
                "completeness": 0.9,
                "sources": ["url1", "url2"],
            }
        }
        self.gate.check(data, QualityRules.stockData, round=1)
        assert len(self.gate.flow_logs) == 1
        log = self.gate.flow_logs[0]
        assert log["from"] == "中书省"
        assert log["to"] == "门下省"
        assert log["round"] == 1


# ============================================================
# QualityRules 预设规则测试
# ============================================================
class TestQualityRules:
    def setup_method(self):
        self.gate = QualityGate()

    def test_stock_data_rule_exists(self):
        assert QualityRules.stockData is not None
        assert QualityRules.stockData.name == "股票数据质检"
        assert QualityRules.stockData.min_score == 0.8

    def test_financial_data_rule_exists(self):
        assert QualityRules.financialData is not None
        assert QualityRules.financialData.min_score == 0.7

    def test_education_content_rule(self):
        assert QualityRules.educationContent is not None
        assert QualityRules.educationContent.min_score == 0.6

    def test_client_advice_higher_threshold(self):
        assert QualityRules.clientAdvice.min_score == 0.9
        assert QualityRules.clientAdvice.min_score > QualityRules.stockData.min_score

    def test_numeric_source_validator_with_sufficient_sources(self):
        from backend.engine.quality.rules import _check_numeric_source
        data = {"_qc": {"sources": ["url1", "url2"]}}
        passed, msg = _check_numeric_source(data)
        assert passed is True

    def test_numeric_source_validator_with_insufficient_sources(self):
        from backend.engine.quality.rules import _check_numeric_source
        data = {"_qc": {"sources": ["url1"]}}
        passed, msg = _check_numeric_source(data)
        assert passed is False
        assert "来源" in msg

    def test_stale_data_validator_clean(self):
        from backend.engine.quality.rules import _check_stale_data
        data = {"_qc": {"stale_data": []}}
        passed, msg = _check_stale_data(data)
        assert passed is True

    def test_stale_data_validator_stale(self):
        from backend.engine.quality.rules import _check_stale_data
        data = {"_qc": {"stale_data": ["Q1财报"]}}
        passed, msg = _check_stale_data(data)
        assert passed is False
        assert "过期" in msg

    def test_custom_validator_integration(self):
        """Test that custom validators are called during check."""
        called = [False]

        def custom_validator(data):
            called[0] = True
            return True, ""

        rule = QualityRule(
            name="custom",
            validators=[custom_validator],
            min_score=0.0,
        )
        data = {"_qc": {"status": "success", "completeness": 1.0, "sources": ["a", "b"]}}
        self.gate.check(data, rule)
        assert called[0] is True
