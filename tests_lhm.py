#!/usr/bin/env python3
"""
LHM Test Suite - pytest tests for core components.
Run with: pytest tests_lhm.py -v
"""

import sys
import os
import pytest
import json
import time
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "Downloads"))

# ======================================================================
# CONFIG TESTS
# ======================================================================

class TestConfig:
    def test_settings_import(self):
        from deepseek_python_20260707_a6bd19 import CONFIG
        assert CONFIG is not None

    def test_nested_stealth_config(self):
        from deepseek_python_20260707_a6bd19 import CONFIG
        assert hasattr(CONFIG, 'stealth')
        assert CONFIG.stealth.tls_impersonate == "chrome120"
        assert CONFIG.stealth.proxy_rotation is True

    def test_nested_risk_config(self):
        from deepseek_python_20260707_a6bd19 import CONFIG
        assert hasattr(CONFIG, 'risk')
        assert 0.0 < CONFIG.risk.kelly_fraction < 1.0
        assert CONFIG.risk.max_drawdown > 0

    def test_nested_data_config(self):
        from deepseek_python_20260707_a6bd19 import CONFIG
        assert hasattr(CONFIG, 'data')
        assert CONFIG.data.db_path == "lhm_prod.db"

    def test_nested_notification_config(self):
        from deepseek_python_20260707_a6bd19 import CONFIG
        assert hasattr(CONFIG, 'notification')
        assert hasattr(CONFIG.notification, 'telegram_token')

    def test_nested_security_config(self):
        from deepseek_python_20260707_a6bd19 import CONFIG
        assert hasattr(CONFIG, 'security')
        assert CONFIG.security.encrypt_secrets is True

    def test_backward_compat_telegram(self):
        from deepseek_python_20260707_a6bd19 import CONFIG
        assert hasattr(CONFIG, 'telegram_token')
        assert hasattr(CONFIG, 'telegram_chat_id')

    def test_backward_compat_use_free_scrapers(self):
        from deepseek_python_20260707_a6bd19 import CONFIG
        assert hasattr(CONFIG, 'use_free_scrapers')
        assert CONFIG.use_free_scrapers is True

    def test_security_warnings(self):
        from deepseek_python_20260707_a6bd19 import CONFIG
        warnings = CONFIG.runtime_security_warnings()
        assert isinstance(warnings, list)

    def test_directories_created(self):
        from deepseek_python_20260707_a6bd19 import CONFIG
        assert os.path.isdir(CONFIG.data.model_dir)


# ======================================================================
# MATH ENGINE TESTS
# ======================================================================

class TestMathEngine:
    def test_calculator_match_probs(self):
        from deepseek_python_20260707_a6bd19 import Calculator
        import numpy as np
        joint = Calculator.match_probs(1.5, 1.5, max_goals=8)
        assert joint is not None
        assert joint.shape == (9, 9)
        assert abs(joint.sum() - 1.0) < 1e-6

    def test_match_probs_sums_to_one(self):
        from deepseek_python_20260707_a6bd19 import Calculator
        joint = Calculator.match_probs(2.0, 1.8, max_goals=10)
        assert abs(joint.sum() - 1.0) < 1e-6

    def test_match_probs_home_away(self):
        from deepseek_python_20260707_a6bd19 import Calculator
        joint = Calculator.match_probs(2.5, 1.0, max_goals=8)
        p_home = float(joint[np.tril_indices_from(joint, k=-1)].sum())
        p_away = float(joint[np.triu_indices_from(joint, k=1)].sum())
        assert p_home > p_away

    def test_kelly_fraction(self):
        from deepseek_python_20260707_a6bd19 import Calculator
        kelly = Calculator.kelly_fraction(0.6, 2.0)
        assert 0 <= kelly <= 1.0

    def test_kelly_fraction_no_edge(self):
        from deepseek_python_20260707_a6bd19 import Calculator
        kelly = Calculator.kelly_fraction(0.5, 2.0)
        assert abs(kelly) < 1e-9

    def test_zero_inflated_probs(self):
        from deepseek_python_20260707_a6bd19 import AdvancedMathEngine
        joint = AdvancedMathEngine.zero_inflated_nbinom_probs(1.5, 1.5, max_goals=6)
        assert abs(joint.sum() - 1.0) < 1e-6

    def test_bivariate_poisson_probs(self):
        from deepseek_python_20260707_a6bd19 import AdvancedMathEngine
        joint = AdvancedMathEngine.bivariate_match_probs(1.5, 1.5, max_goals=6)
        assert abs(joint.sum() - 1.0) < 1e-6

    def test_dynamic_copula_probs(self):
        from deepseek_python_20260707_a6bd19 import AdvancedMathEngine
        joint = AdvancedMathEngine.dynamic_copula_match_probs(1.5, 1.5, max_goals=6)
        assert abs(joint.sum() - 1.0) < 1e-6


# ======================================================================
# STEALTH SCRAPER TESTS
# ======================================================================

class TestStealthScrapers:
    def test_stealth_scraper_import(self):
        from stealth_scraper import BetPawaStealthScraper, BetikaStealthScraper
        assert BetPawaStealthScraper is not None
        assert BetikaStealthScraper is not None

    def test_stealth_config(self):
        from stealth_scraper import StealthConfig
        config = StealthConfig()
        assert config.TLS_IMPERSONATE == "chrome120"
        assert config.PROXY_POOL_SIZE > 0

    def test_human_behavior_delay(self):
        from stealth_scraper import HumanBehavior
        delay = HumanBehavior.poisson_delay(3.0)
        assert delay >= 0.1

    def test_human_behavior_viewport(self):
        from stealth_scraper import HumanBehavior
        w, h = HumanBehavior.get_viewport()
        assert 1024 <= w <= 1920
        assert 768 <= h <= 1080

    def test_human_behavior_headers(self):
        from stealth_scraper import HumanBehavior
        headers = HumanBehavior.get_headers()
        assert "user-agent" in headers
        assert "accept-encoding" in headers

    def test_bezier_move(self):
        from stealth_scraper import HumanBehavior
        points = HumanBehavior.bezier_move(0, 0, 100, 100, 0.5)
        assert len(points) > 0
        assert all(len(p) == 2 for p in points)


# ======================================================================
# SECURE CONFIG TESTS
# ======================================================================

class TestSecureConfig:
    def test_secure_config_import(self):
        from lhm_enhanced import SecureConfigManager
        assert SecureConfigManager is not None

    def test_secure_config_save_load(self):
        from lhm_enhanced import SecureConfigManager
        config = SecureConfigManager()
        config.set("test_key", "test_value_12345")
        assert config.get("test_key") == "test_value_12345"

    def test_telegram_config_persists(self):
        from lhm_enhanced import SecureConfigManager
        config = SecureConfigManager()
        token = config.get("telegram_token")
        chat_id = config.get("telegram_chat_id")
        assert len(token) > 10
        assert len(chat_id) > 5

    def test_secure_config_missing_key(self):
        from lhm_enhanced import SecureConfigManager
        config = SecureConfigManager()
        assert config.get("nonexistent_key", "default") == "default"


# ======================================================================
# INTEGRATION TESTS
# ======================================================================

class TestIntegration:
    def test_free_sources_registry(self):
        from lhm_enhanced import FREE_API_REGISTRY
        assert "odds" in FREE_API_REGISTRY
        assert "fixtures" in FREE_API_REGISTRY
        assert len(FREE_API_REGISTRY.get("odds", [])) > 10

    def test_telegram_bridge_configured(self):
        from lhm_enhanced import SecureConfigManager, SecureTelegramBridge
        config = SecureConfigManager()
        bridge = SecureTelegramBridge(config)
        assert bridge.is_configured() is True

    def test_hosting_manager(self):
        from lhm_enhanced import HostingManager, SecureConfigManager
        config = SecureConfigManager()
        hm = HostingManager(config)
        assert hm.get_best_free_option() is not None


# ======================================================================
# SECURITY TESTS
# ======================================================================

class TestSecurity:
    def test_no_hardcoded_tokens_in_model(self):
        content = Path(r"C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py").read_text(encoding="utf-8", errors="ignore")
        # Should not contain the actual token value in source
        assert "8899227512:AAE7dr-MvhyySbSv2KHcGmuzA4hepE8AHHQ" not in content

    def test_env_file_exists(self):
        env_path = Path(r"C:\Users\enock\Downloads\.env")
        assert env_path.exists()

    def test_encrypted_config_exists(self):
        config_path = Path.home() / ".lhm" / "config.enc"
        assert config_path.exists()

    def test_secret_key_is_set(self):
        from deepseek_python_20260707_a6bd19 import CONFIG
        assert CONFIG.security.secret_key != ""
        assert CONFIG.security.secret_key != "change_this_in_production"

    def test_encryption_key_is_set(self):
        from deepseek_python_20260707_a6bd19 import CONFIG
        assert CONFIG.security.encryption_key != ""


# ======================================================================
# PERFORMANCE TESTS
# ======================================================================

class TestPerformance:
    def test_match_probs_performance(self):
        from deepseek_python_20260707_a6bd19 import Calculator
        import time
        start = time.time()
        for _ in range(100):
            Calculator.match_probs(1.5, 1.5, max_goals=8)
        elapsed = time.time() - start
        assert elapsed < 5.0, f"match_probs too slow: {elapsed:.2f}s for 100 calls"

    def test_joint_matrix_memory(self):
        from deepseek_python_20260707_a6bd19 import Calculator
        import numpy as np
        joint = Calculator.match_probs(2.0, 1.8, max_goals=10)
        assert joint.dtype == np.float64 or joint.dtype == float


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
