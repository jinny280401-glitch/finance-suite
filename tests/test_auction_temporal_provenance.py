"""Auction Candidate DATA_AS_OF Closure — temporal provenance acceptance tests.

T1 — No provider timestamp: provider rows carry no time field.
     Expected: provider_origin_time=None, fetch_completed_at!=None,
     timestamp_authority="fetch_boundary".
T2 — Provider stamped: provider rows carry a time field.
     Expected: provider_origin_time=actual provider time,
     timestamp_authority="provider_stamped".
T3 — Candidate binding: every golden_pit candidate resolves to its source
     dimension receipt via source_receipt_id.
T4 — No semantic promotion: no code path may promote fetch_completed_at to
     provider_origin_time or to a data_as_of claim; provider_freshness stays
     "unknown" when origin time is absent.

运行：python3 -m unittest tests.test_auction_temporal_provenance -v
"""
import asyncio
import inspect
import unittest
from unittest import mock

from app.auction_data import _build_dimension_receipt, _extract_row_metadata
from app.routers import intel


class T1NoProviderTimestamp(unittest.TestCase):
    """provider row 无 timestamp → origin=null + fetch_boundary + freshness unknown"""

    def test_receipt_fields(self):
        rows = [
            {"代码": "600001", "名称": "测试", "涨跌幅": 5.0},
            {"代码": "600002", "名称": "测试2", "涨跌幅": 3.0},
        ]
        receipt = _build_dimension_receipt(
            "strong_pool", "success_with_data", value=rows,
            elapsed_s=0.5, completed_at="2026-08-13T09:25:15+08:00",
            trace_token="tok1",
        )
        self.assertIsNone(receipt["provider_origin_time"])
        self.assertIsNotNone(receipt["fetch_completed_at"])
        self.assertEqual(receipt["timestamp_authority"], "fetch_boundary")
        self.assertEqual(receipt["provider_freshness"], "unknown")
        self.assertEqual(receipt["receipt_id"], "strong_pool:tok1")
        # no synthetic promotion: origin must not borrow the boundary time
        self.assertNotEqual(receipt["provider_origin_time"], receipt["fetch_completed_at"])


class T2ProviderStamped(unittest.TestCase):
    """provider row 自带时间 → origin=provider time + provider_stamped"""

    def test_receipt_fields(self):
        rows = [
            {"代码": "600001", "时间": "09:25:02", "涨跌幅": 5.0},
        ]
        receipt = _build_dimension_receipt(
            "big_buy", "success_with_data", value=rows,
            elapsed_s=0.4, completed_at="2026-08-13T09:25:15+08:00",
            trace_token="tok2",
        )
        self.assertEqual(receipt["provider_origin_time"], "09:25:02")
        self.assertEqual(receipt["timestamp_authority"], "provider_stamped")
        self.assertNotEqual(receipt["provider_freshness"], "unknown")

    def test_extract_last_row_latest(self):
        rows = [
            {"时间": "09:25:01", "代码": "A"},
            {"时间": "09:25:02", "代码": "B"},
        ]
        meta = _extract_row_metadata(rows)
        self.assertEqual(meta["provider_origin_time"], "09:25:02")


class T3CandidateBinding(unittest.TestCase):
    """candidate 必须能反查对应 dimension receipt"""

    def test_candidate_carries_provenance_and_resolves_to_receipt(self):
        async def fake_get_auction_data(trace_token=None):
            rows = [{"代码": "600001", "名称": "测试", "涨跌幅": 5.0}]
            return {
                "strong_pool": rows,
                "hot_up": None,
                "previous_zt": None,
                "_dimension_status": {
                    "strong_pool": _build_dimension_receipt(
                        "strong_pool", "success_with_data", value=rows,
                        elapsed_s=0.5, completed_at="2026-08-13T09:25:15+08:00",
                        trace_token=trace_token,
                    ),
                    "hot_up": _build_dimension_receipt(
                        "hot_up", "unavailable", elapsed_s=0.1,
                        completed_at="2026-08-13T09:25:15+08:00", trace_token=trace_token,
                    ),
                    "previous_zt": _build_dimension_receipt(
                        "previous_zt", "unavailable", elapsed_s=0.1,
                        completed_at="2026-08-13T09:25:15+08:00", trace_token=trace_token,
                    ),
                    "top_gainers": _build_dimension_receipt(
                        "top_gainers", "skipped_optional", trace_token=trace_token,
                    ),
                },
                "_trace_token": trace_token,
            }

        with mock.patch.object(intel, "_get_auction_data", fake_get_auction_data):
            response = asyncio.run(intel.golden_pit(limit=10, trace_token="tok3"))

        self.assertTrue(response["data"], "expected at least one candidate")
        candidate = response["data"][0]
        required = {
            "source_bucket", "source_receipt_id", "provider",
            "provider_origin_time", "fetch_completed_at", "timestamp_authority",
        }
        self.assertTrue(required.issubset(candidate.keys()),
                        f"missing provenance keys: {required - candidate.keys()}")

        # 反查 receipt：receipt_id 必须能定位到 dimension receipt
        receipts = response["receipts"]
        receipt = receipts[candidate["source_bucket"]]
        self.assertEqual(receipt["receipt_id"], candidate["source_receipt_id"])
        self.assertEqual(receipt["provider"], candidate["provider"])
        self.assertEqual(receipt["provider_origin_time"], candidate["provider_origin_time"])
        self.assertEqual(receipt["fetch_completed_at"], candidate["fetch_completed_at"])
        self.assertEqual(receipt["timestamp_authority"], candidate["timestamp_authority"])

        # strong_pool rows 无时间戳 → 权威必须是 fetch_boundary，不是 provider_stamped
        self.assertIsNone(candidate["provider_origin_time"])
        self.assertEqual(candidate["timestamp_authority"], "fetch_boundary")


class T4NoSemanticPromotion(unittest.TestCase):
    """禁止 fetch_completed_at → provider_origin_time / data_as_of 的任何提升"""

    def test_no_data_as_of_key_in_receipt_or_candidate(self):
        rows = [{"代码": "600001", "涨跌幅": 5.0}]
        receipt = _build_dimension_receipt(
            "strong_pool", "success_with_data", value=rows,
            elapsed_s=0.5, completed_at="2026-08-13T09:25:15+08:00",
        )
        self.assertNotIn("data_as_of", receipt)

        async def fake_get_auction_data(trace_token=None):
            return {
                "strong_pool": rows,
                "hot_up": None,
                "previous_zt": None,
                "_dimension_status": {
                    "strong_pool": receipt,
                    "hot_up": _build_dimension_receipt("hot_up", "unavailable", trace_token=trace_token),
                    "previous_zt": _build_dimension_receipt("previous_zt", "unavailable", trace_token=trace_token),
                    "top_gainers": _build_dimension_receipt("top_gainers", "skipped_optional", trace_token=trace_token),
                },
                "_trace_token": trace_token,
            }

        with mock.patch.object(intel, "_get_auction_data", fake_get_auction_data):
            response = asyncio.run(intel.golden_pit(limit=10))
        candidate = response["data"][0]
        self.assertNotIn("data_as_of", candidate)
        # freshness 不得从 boundary 推导：origin 缺失时 freshness 恒为 unknown
        self.assertEqual(receipt["provider_freshness"], "unknown")
        self.assertIsNotNone(receipt["fetch_completed_at"])

    def test_no_source_code_promotion_path(self):
        """源码级检查：fetch_completed_at 不能被赋给 provider_origin_time / data_as_of。"""
        for mod in (intel,):
            src = inspect.getsource(mod)
        # receipt 构建器里 origin 与 boundary 必须来自不同变量
        from app import auction_data
        receipt_src = inspect.getsource(auction_data._build_dimension_receipt)
        self.assertNotIn('"data_as_of"', receipt_src)
        self.assertNotIn('"provider_origin_time": completed_at', receipt_src)
        # intel.py candidate 构造不得出现 data_as_of 字段
        gp_src = inspect.getsource(intel.golden_pit)
        self.assertNotIn('"data_as_of"', gp_src)


if __name__ == "__main__":
    unittest.main()
