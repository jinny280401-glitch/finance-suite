"""Test for UnboundLocalError fix in run_analysis"""
import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch


async def test_industry_no_unbound_error():
    """Test that industry scenario doesn't raise UnboundLocalError"""
    # Mock all dependencies
    with patch('backend.app.services.analyze_service.ScenarioRegistry') as mock_registry, \
         patch('backend.app.services.analyze_service._fetch_industry_data') as mock_fetch, \
         patch('backend.app.services.analyze_service.generate_analysis') as mock_llm, \
         patch('backend.app.services.analyze_service.build_report_qc') as mock_qc, \
         patch('backend.app.services.analyze_service.cache_set') as mock_cache:
        
        # Setup mocks
        mock_registry_instance = MagicMock()
        mock_registry.return_value = mock_registry_instance
        mock_registry_instance.get_metadata.return_value = {
            "search_type": "industry",
            "name": "industry"
        }
        mock_registry_instance.get.return_value = MagicMock(
            prompt="Test prompt",
            dimensions=[],
            cache=MagicMock(ttl=600),
            qc=MagicMock(dimensions={})
        )
        
        mock_fetch.return_value = {
            "search_results_text": "Test search results",
            "sources": [{"url": "http://test.com", "title": "Test"}],
            "has_structured": False
        }
        
        mock_llm.return_value = "Test report content"
        mock_qc.return_value = {
            "status": "success",
            "completeness": 1.0,
            "sources": [],
            "missing_dimensions": [],
            "stale_data": [],
            "hallucination_risk": {"level": "low"}
        }
        
        # Import after mocking
        from backend.app.services.analyze_service import run_analysis
        
        # Call run_analysis with industry skill_type
        result = await run_analysis(
            skill_type="industry",
            query="test query"
        )
        
        # Verify no UnboundLocalError was raised
        assert result is not None
        assert "success" in result or "result" in result
        print("✓ Test passed: industry scenario works without UnboundLocalError")
        return True


async def test_macro_no_unbound_error():
    """Test that macro scenario doesn't raise UnboundLocalError"""
    with patch('backend.app.services.analyze_service.ScenarioRegistry') as mock_registry, \
         patch('backend.app.services.analyze_service._fetch_macro_data') as mock_fetch, \
         patch('backend.app.services.analyze_service.generate_analysis') as mock_llm, \
         patch('backend.app.services.analyze_service.build_report_qc') as mock_qc, \
         patch('backend.app.services.analyze_service.cache_set') as mock_cache:
        
        # Setup mocks
        mock_registry_instance = MagicMock()
        mock_registry.return_value = mock_registry_instance
        mock_registry_instance.get_metadata.return_value = {
            "search_type": "macro",
            "name": "macro"
        }
        mock_registry_instance.get.return_value = MagicMock(
            prompt="Test prompt",
            dimensions=[],
            cache=MagicMock(ttl=600),
            qc=MagicMock(dimensions={})
        )
        
        mock_fetch.return_value = {
            "search_results_text": "Test macro results",
            "sources": [{"url": "http://test.com", "title": "Test"}],
            "has_structured": True,
            "macro_event_facts": None
        }
        
        mock_llm.return_value = "Test macro report"
        mock_qc.return_value = {
            "status": "success",
            "completeness": 1.0,
            "sources": [],
            "missing_dimensions": [],
            "stale_data": [],
            "hallucination_risk": {"level": "low"}
        }
        
        from backend.app.services.analyze_service import run_analysis
        
        result = await run_analysis(
            skill_type="macro",
            query="GDP growth"
        )
        
        assert result is not None
        print("✓ Test passed: macro scenario works without UnboundLocalError")
        return True


async def test_all_scenarios():
    """Test all scenarios to ensure no UnboundLocalError"""
    scenarios = ["stock", "macro", "auction", "industry", "video", "meeting", "mckinsey"]
    
    for scenario in scenarios:
        try:
            if scenario == "stock":
                await test_stock_no_unbound_error()
            elif scenario == "macro":
                await test_macro_no_unbound_error()
            elif scenario == "industry":
                await test_industry_no_unbound_error()
            else:
                # Generic test for other scenarios
                await test_generic_scenario(scenario)
            print(f"✓ {scenario}: OK")
        except UnboundLocalError as e:
            print(f"✗ {scenario}: FAILED with UnboundLocalError: {e}")
            return False
        except Exception as e:
            print(f"✗ {scenario}: FAILED with {type(e).__name__}: {e}")
            return False
    
    return True


async def test_stock_no_unbound_error():
    """Test stock scenario"""
    with patch('backend.app.services.analyze_service.ScenarioRegistry') as mock_registry, \
         patch('backend.app.services.analyze_service._fetch_stock_data') as mock_fetch, \
         patch('backend.app.services.analyze_service.generate_analysis') as mock_llm, \
         patch('backend.app.services.analyze_service.build_report_qc') as mock_qc, \
         patch('backend.app.services.analyze_service.cache_set') as mock_cache:
        
        mock_registry_instance = MagicMock()
        mock_registry.return_value = mock_registry_instance
        mock_registry_instance.get_metadata.return_value = {
            "search_type": "stock",
            "name": "stock"
        }
        mock_registry_instance.get.return_value = MagicMock(
            prompt="Test prompt",
            dimensions=["financials", "price_history"],
            cache=MagicMock(ttl=600),
            qc=MagicMock(dimensions={})
        )
        
        mock_fetch.return_value = {
            "search_results_text": "Test stock results",
            "sources": [],
            "kline_data": None,
            "has_structured": False,
            "final_dispatch_trace": None,
            "dimension_status": {"financials": "available"},
            "stale_data": []
        }
        
        mock_llm.return_value = "Test stock report"
        mock_qc.return_value = {
            "status": "success",
            "completeness": 1.0,
            "sources": [],
            "missing_dimensions": [],
            "stale_data": [],
            "hallucination_risk": {"level": "low"}
        }
        
        from backend.app.services.analyze_service import run_analysis
        
        result = await run_analysis(
            skill_type="stock",
            query="000001"
        )
        
        assert result is not None
        return True


async def test_generic_scenario(scenario_type):
    """Generic test for any scenario"""
    with patch('backend.app.services.analyze_service.ScenarioRegistry') as mock_registry, \
         patch('backend.app.services.analyze_service._fetch_generic_data') as mock_fetch, \
         patch('backend.app.services.analyze_service.generate_analysis') as mock_llm, \
         patch('backend.app.services.analyze_service.build_report_qc') as mock_qc, \
         patch('backend.app.services.analyze_service.cache_set') as mock_cache:
        
        mock_registry_instance = MagicMock()
        mock_registry.return_value = mock_registry_instance
        mock_registry_instance.get_metadata.return_value = {
            "search_type": scenario_type,
            "name": scenario_type
        }
        mock_registry_instance.get.return_value = MagicMock(
            prompt="Test prompt",
            dimensions=[],
            cache=MagicMock(ttl=600),
            qc=MagicMock(dimensions={})
        )
        
        mock_fetch.return_value = {
            "search_results_text": "Test results",
            "sources": [],
            "has_structured": False
        }
        
        mock_llm.return_value = "Test report"
        mock_qc.return_value = {
            "status": "success",
            "completeness": 1.0,
            "sources": [],
            "missing_dimensions": [],
            "stale_data": [],
            "hallucination_risk": {"level": "low"}
        }
        
        from backend.app.services.analyze_service import run_analysis
        
        result = await run_analysis(
            skill_type=scenario_type,
            query="test"
        )
        
        assert result is not None
        return True


if __name__ == "__main__":
    print("Running UnboundLocalError fix tests...")
    print()
    
    result = asyncio.run(test_all_scenarios())
    
    print()
    if result:
        print("All tests passed!")
        sys.exit(0)
    else:
        print("Some tests failed!")
        sys.exit(1)
