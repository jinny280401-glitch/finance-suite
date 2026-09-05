"""
核心模块单元测试: config, auth, database, skills
覆盖: 配置管理、密码哈希、JWT 令牌、数据库操作、技能定义
"""
import pytest
from datetime import datetime
from unittest.mock import patch


# ============================================================
# config.py 测试
# ============================================================
class TestConfig:
    def test_settings_loads_from_env(self):
        from backend.app.config import Settings
        s = Settings()
        assert s.APP_NAME == "Finance Suite"
        assert isinstance(s.SECRET_KEY, str)
        assert len(s.SECRET_KEY) > 0

    def test_tavily_key_round_robin(self):
        from backend.app.config import Settings
        s = Settings()
        keys = [s.get_tavily_key() for _ in range(4)]
        # Should cycle through available keys
        assert keys[0] == keys[2]
        assert keys[1] == keys[3]

    def test_brave_key_round_robin(self):
        from backend.app.config import Settings
        s = Settings()
        k1 = s.get_brave_key()
        k2 = s.get_brave_key()
        # Only one key configured, should always return same
        assert k1 == k2

    def test_empty_tavily_keys(self):
        from backend.app.config import Settings
        with patch.dict("os.environ", {"TAVILY_KEYS": ""}):
            s = Settings()
            assert s.get_tavily_key() == ""

    def test_debug_mode(self):
        from backend.app.config import Settings
        s = Settings()
        # conftest sets DEBUG=true
        assert s.DEBUG is True

    def test_access_token_expiry(self):
        from backend.app.config import Settings
        s = Settings()
        assert s.ACCESS_TOKEN_EXPIRE_HOURS > 0


# ============================================================
# auth.py 测试
# ============================================================
class TestAuth:
    def test_hash_password_returns_string(self):
        from backend.app.auth import hash_password
        hashed = hash_password("mypassword")
        assert isinstance(hashed, str)
        assert hashed != "mypassword"

    def test_verify_password_correct(self):
        from backend.app.auth import hash_password, verify_password
        pw = "secure_password_123"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed) is True

    def test_verify_password_incorrect(self):
        from backend.app.auth import hash_password, verify_password
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_create_access_token_returns_string(self):
        from backend.app.auth import create_access_token
        token = create_access_token({"user_id": 1, "username": "test"})
        assert isinstance(token, str)
        assert len(token) > 20

    def test_verify_token_valid(self):
        from backend.app.auth import create_access_token, verify_token
        payload = {"user_id": 42, "username": "alice"}
        token = create_access_token(payload)
        decoded = verify_token(token)
        assert decoded is not None
        assert decoded["user_id"] == 42
        assert decoded["username"] == "alice"

    def test_verify_token_invalid(self):
        from backend.app.auth import verify_token
        result = verify_token("totally.invalid.token")
        assert result is None

    def test_verify_token_expired(self):
        from backend.app.auth import create_access_token, verify_token
        import jwt
        from backend.app.config import settings
        # Create token that expires immediately
        from datetime import datetime, timedelta, timezone
        payload = {"user_id": 1, "exp": datetime.now(timezone.utc) - timedelta(seconds=10)}
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        result = verify_token(token)
        assert result is None

    def test_different_passwords_produce_different_hashes(self):
        from backend.app.auth import hash_password
        h1 = hash_password("password1")
        h2 = hash_password("password2")
        assert h1 != h2

    def test_same_password_different_salt(self):
        from backend.app.auth import hash_password
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        # bcrypt uses random salt, so same input → different output
        assert h1 != h2


# ============================================================
# database.py 测试
# ============================================================
class TestDatabase:
    def test_create_user(self, db_session):
        from backend.app.database import User
        user = User(
            username="dbtest",
            email="dbtest@test.com",
            hashed_password="hashed",
            tier="free",
        )
        db_session.add(user)
        db_session.commit()
        assert user.id is not None

    def test_user_default_tier(self, db_session):
        from backend.app.database import User
        user = User(username="tier_test", email="tier@test.com", hashed_password="h")
        db_session.add(user)
        db_session.commit()
        assert user.tier == "free"

    def test_user_default_is_active(self, db_session):
        from backend.app.database import User
        user = User(username="active_test", email="active@test.com", hashed_password="h")
        db_session.add(user)
        db_session.commit()
        # is_active defaults to True
        assert user.is_active is True

    def test_usage_record(self, db_session, test_user):
        from backend.app.database import Usage
        usage = Usage(
            user_id=test_user.id,
            skill_type="stock",
            query="贵州茅台",
        )
        db_session.add(usage)
        db_session.commit()
        assert usage.id is not None

    def test_get_today_usage_count(self, db_session, test_user):
        from backend.app.database import Usage, get_today_usage_count
        for i in range(3):
            db_session.add(Usage(user_id=test_user.id, skill_type="stock", query=f"q{i}"))
        db_session.commit()
        count = get_today_usage_count(db_session, test_user.id)
        assert count == 3

    def test_check_usage_allowed_free_under_limit(self, db_session, test_user):
        from backend.app.database import check_usage_allowed
        allowed, used, limit = check_usage_allowed(db_session, test_user.id, "free")
        assert allowed is True
        assert used == 0
        assert limit == 3

    def test_check_usage_allowed_free_at_limit(self, db_session, test_user):
        from backend.app.database import Usage, check_usage_allowed
        for i in range(3):
            db_session.add(Usage(user_id=test_user.id, skill_type="stock", query=f"q{i}"))
        db_session.commit()
        allowed, used, limit = check_usage_allowed(db_session, test_user.id, "free")
        assert allowed is False
        assert used == 3

    def test_check_usage_allowed_vip_unlimited(self, db_session, test_user):
        from backend.app.database import check_usage_allowed
        allowed, used, limit = check_usage_allowed(db_session, test_user.id, "vip")
        assert allowed is True
        assert limit is None

    def test_user_usage_relationship(self, db_session, test_user):
        from backend.app.database import Usage
        db_session.add(Usage(user_id=test_user.id, skill_type="macro", query="GDP"))
        db_session.commit()
        assert len(test_user.usages) == 1
        assert test_user.usages[0].skill_type == "macro"


# ============================================================
# ScenarioRegistry 测试
# ============================================================
class TestSkills:
    def test_get_skill_stock(self):
        from backend.engine.registry import ScenarioRegistry
        skill = ScenarioRegistry().get_metadata("stock")
        assert skill is not None
        assert skill["name"] == "看票分析"
        assert "prompt_template" in skill

    def test_get_skill_macro(self):
        from backend.engine.registry import ScenarioRegistry
        skill = ScenarioRegistry().get_metadata("macro")
        assert skill is not None
        assert "search_type" in skill

    def test_get_skill_auction(self):
        from backend.engine.registry import ScenarioRegistry
        skill = ScenarioRegistry().get_metadata("auction")
        assert skill is not None

    def test_get_skill_unknown(self):
        from backend.engine.registry import ScenarioRegistry
        skill = ScenarioRegistry().get_metadata("nonexistent_skill")
        assert skill is None

    def test_get_skill_list(self):
        from backend.engine.registry import ScenarioRegistry
        skills = ScenarioRegistry().list_metadata()
        assert isinstance(skills, list)
        assert len(skills) >= 4  # stock, macro, auction, industry at minimum

    def test_normalize_skill_type_valid(self):
        from backend.engine.registry import normalize_scenario_type
        result = normalize_scenario_type("stock")
        assert result == "stock"

    def test_normalize_skill_type_alias(self):
        from backend.engine.registry import normalize_scenario_type
        result = normalize_scenario_type("stock")
        assert result in ("stock", "macro", "auction", "industry", "video", "deep_research")

    def test_normalize_skill_type_unknown(self):
        from backend.engine.registry import normalize_scenario_type
        result = normalize_scenario_type("totally_unknown")
        assert result is not None or result == "totally_unknown"

    def test_get_skill_prompt_returns_string(self):
        from backend.engine.registry import ScenarioRegistry
        scenario = ScenarioRegistry().get("stock")
        assert scenario is not None
        prompt = scenario.prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Prompts are substantial

    def test_all_skills_have_required_fields(self):
        from backend.engine.registry import ScenarioRegistry
        for s in ScenarioRegistry().scenarios.values():
            meta = ScenarioRegistry().get_metadata(s.name)
            assert "name" in meta, f"Skill '{s.name}' missing 'name'"
            assert "description" in meta, f"Skill '{s.name}' missing 'description'"
            assert "prompt_template" in meta, f"Skill '{s.name}' missing 'prompt_template'"
            assert "search_type" in meta, f"Skill '{s.name}' missing 'search_type'"
