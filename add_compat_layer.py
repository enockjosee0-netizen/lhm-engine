#!/usr/bin/env python3
"""
Add backward-compatible attribute access to Settings class.
"""

from pathlib import Path

MAIN = Path(r'C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py')

text = MAIN.read_text(encoding='utf-8')

# Find the Settings class and add __getattr__ before the model_rebuild() call
# We need to add it after the redacted_dict method

old_redacted = '''    def redacted_dict(self) -> Dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "dry_run": self.dry_run,
            "debug": self.debug,
            "db_path": self.data.db_path,
            "loop_interval": self.loop_interval,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "odds_api_key": "***" if self.odds_api_key else "",
            "api_football_key": "***" if self.api_football_key else "",
            "exchange_key": "***" if self.exchange_key else "",
            "telegram_token": "***" if self.notification.telegram_token else "",
            "telegram_chat_id": "***" if self.notification.telegram_chat_id else "",
            "secret_key": "***" if self.security.secret_key else "",
            "encryption_key": "***" if self.security.encryption_key else "",
            "deepseek_api_key": "***" if self.ml.deepseek_api_key else "",
            "use_free_scrapers": self.use_free_scrapers,
            "dry_run": self.dry_run,
            "stealth": self.stealth.model_dump() if hasattr(self.stealth, 'model_dump') else {},
            "risk": self.risk.model_dump() if hasattr(self.risk, 'model_dump') else {},
        }


# Pydantic v2.13 requires an explicit rebuild'''

new_redacted = '''    def redacted_dict(self) -> Dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "dry_run": self.dry_run,
            "debug": self.debug,
            "db_path": self.data.db_path,
            "loop_interval": self.loop_interval,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "odds_api_key": "***" if self.odds_api_key else "",
            "api_football_key": "***" if self.api_football_key else "",
            "exchange_key": "***" if self.exchange_key else "",
            "telegram_token": "***" if self.notification.telegram_token else "",
            "telegram_chat_id": "***" if self.notification.telegram_chat_id else "",
            "secret_key": "***" if self.security.secret_key else "",
            "encryption_key": "***" if self.security.encryption_key else "",
            "deepseek_api_key": "***" if self.ml.deepseek_api_key else "",
            "use_free_scrapers": self.use_free_scrapers,
            "dry_run": self.dry_run,
            "stealth": self.stealth.model_dump() if hasattr(self.stealth, 'model_dump') else {},
            "risk": self.risk.model_dump() if hasattr(self.risk, 'model_dump') else {},
        }

    def __getattr__(self, name: str):
        _stealth_fields = {
            'use_stealth_scraping', 'stealth_tls_impersonate', 'stealth_proxy_rotation',
            'stealth_browser_mode', 'stealth_human_behavior', 'stealth_session_lifetime_min',
            'stealth_session_lifetime_max', 'stealth_request_jitter', 'stealth_use_curl_cffi',
            'stealth_use_playwright', 'stealth_residential_proxies', 'stealth_proxy_api_key',
            'stealth_user_agent_rotation', 'stealth_header_order', 'stealth_mouse_emulation',
            'stealth_scroll_emulation', 'stealth_timing_poisson',
        }
        _risk_fields = {
            'min_single_edge', 'min_parlay_edge', 'min_correct_score_edge', 'kelly_fraction',
            'fractional_kelly_factor', 'non_1x2_xg_discount', 'clv_deadzone_pct',
            'sharp_move_threshold', 'sharp_adjustment_threshold', 'max_drawdown',
            'max_stake_per_bet', 'min_stake_per_bet', 'daily_loss_limit', 'backtest_commission',
            'live_commission', 'execution_slippage', 'bookmaker_daily_limit', 'bookmaker_limit_bets',
            'max_realistic_edge', 'max_bets_per_day', 'max_stake_per_match',
            'exposure_limit_per_league', 'exposure_limit_per_market', 'exposure_limit_per_team',
            'exposure_limit_per_bookmaker', 'exposure_limit_per_outcome', 'risk_free_rate',
            'max_correlation_exposure', 'swan_threshold', 'swan_duration_hours',
            'exploration_budget', 'correlation_risk_threshold', 'volatility_window',
            'global_volatility_window', 'enable_portfolio_opt', 'slippage', 'commission',
            'jitter_min_minutes', 'jitter_max_minutes', 'pending_bet_timeout_hours',
            'liquidity_split_threshold', 'kyc_lock_hours', 'parlay_max_legs', 'parlay_min_legs',
            'parlay_stake_fraction', 'over_line', 'corners_line', 'cards_line', 'elo_k_factor',
            'rejection_loss_threshold', 'bivariate_cov_factor', 'tail_risk_threshold',
            'hawkes_alpha', 'hawkes_beta', 'target_state_dim', 'max_grad_norm',
            'drift_threshold_kl', 'ess_min_ratio', 'xi_threshold', 'surrogate_mae_threshold',
            'hybrid_surrogate_fraction', 'importance_bias_factor', 'tail_scenarios',
            'online_batch_size', 'min_samples_train', 'max_schema_validation_fails',
            'ab_test_min_bets', 'stop_loss_drawdown', 'hedge_threshold',
            'kelly_cov_estimation_window', 'trailing_stop_pct', 'daily_profit_target_pct',
            'weekly_loss_limit', 'monthly_loss_limit', 'max_risk_of_ruin',
            'rollback_roi_threshold', 'rollback_bets_threshold', 'shadow_duration_days',
            'shadow_promotion_threshold_roi', 'shadow_min_bets',
        }
        _data_fields = {
            'db_path', 'in_memory_db', 'historical_data_path', 'model_dir', 'latest_symlink',
            'warm_snapshot_path', 'snapshot_path_a', 'snapshot_path_b', 'proxy_list',
            'external_models', 'ip_whitelist', 'redis_url', 'redis_ttl',
            'circuit_breaker_fail_threshold', 'circuit_breaker_recovery_timeout', 'cache_ttl',
            'retrain_interval_hours', 'health_check_interval', 'tuning_trials',
            'feature_cache_max_size', 'fetcher_cache_max_size', 'audit_prune_days',
            'drift_prune_days', 'jitter_prune_days', 'checkpoint_prune_days',
            'memory_prune_days', 'log_rotation_mb', 'shadow_traffic_percent',
            'attribution_sample_size', 'dashboard_port', 'otel_endpoint', 'ssl_verify',
            'tls_enabled', 'tls_generate_self_signed', 'tls_certfile', 'tls_keyfile',
            'tls_common_name', 'max_concurrent_requests', 'data_freeze_timeout',
            'jitter_concurrent', 'batch_checkpoint_recovery', 'migration_retry_attempts',
            'vacuum_interval_hours', 'archive_interval_days', 'bookmaker_max_loss_percent',
            'bias_alert_threshold', 'imputation_strategy', 'log_missing_data', 'exchange_type',
            's3_endpoint', 's3_bucket', 's3_key', 's3_secret', 'backtest_start', 'backtest_end',
            'flat_stake_pct', 'external_api_url', 'department_mode', 'state_version',
            'profile_mode', 'strict_dependencies', 'websocket_url',
        }
        _exchange_fields = {
            'pinnacle_api_key', 'pinnacle_api_base_url', 'pinnacle_odds_market',
            'betfair_username', 'betfair_password', 'betfair_app_key',
            'exchange_key', 'exchange_secret', 'exchange_session_token',
        }
        _notification_fields = {
            'telegram_token', 'telegram_chat_id', 'telegram_poll_interval_seconds',
            'telegram_allowed_user_ids', 'enable_telegram_chat_bot',
            'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 'smtp_from',
            'email_recipients', 'smtp_use_tls', 'slack_webhook', 'discord_webhook',
            'prometheus_port',
        }
        _security_fields = {
            'secret_key', 'encrypt_secrets', 'encryption_key', 'rate_limit', 'active_tactics_limit',
        }
        _ml_fields = {
            'deepseek_enabled', 'deepseek_api_key', 'deepseek_api_base_url', 'deepseek_model',
            'deepseek_timeout', 'deepseek_max_retries', 'ensemble_weights', 'genetic_features',
            'enable_genetic_features', 'enable_advanced_math', 'enable_negative_binomial',
            'enable_bandit_ensemble', 'enable_ab_testing', 'enable_online_learning',
            'enable_quantization', 'enable_batch_prediction', 'enable_flat_baseline',
            'enable_unified_engine', 'enable_x_tactics', 'enable_redis_distributed_lock',
            'enable_postgres', 'enable_otel', 'enable_feature_attribution', 'enable_dashboard',
            'enable_hyper_tuning', 'enable_causal_graph', 'enable_feature_store',
            'enable_purged_cv', 'enable_bayesian_updater', 'enable_ensemble_weight_optimizer',
            'enable_causal_selection', 'enable_market_implied_features', 'enable_league_regime_scaler',
            'enable_exogenous_encoder', 'enable_official_feed_gateway', 'enable_order_book_processor',
            'enable_heartbeat_monitor',
        }
        if name in _stealth_fields:
            return getattr(self.stealth, name)
        if name in _risk_fields:
            return getattr(self.risk, name)
        if name in _data_fields:
            return getattr(self.data, name)
        if name in _exchange_fields:
            return getattr(self.exchange, name)
        if name in _notification_fields:
            return getattr(self.notification, name)
        if name in _security_fields:
            return getattr(self.security, name)
        if name in _ml_fields:
            return getattr(self.ml, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value):
        _stealth_fields = {
            'use_stealth_scraping', 'stealth_tls_impersonate', 'stealth_proxy_rotation',
            'stealth_browser_mode', 'stealth_human_behavior', 'stealth_session_lifetime_min',
            'stealth_session_lifetime_max', 'stealth_request_jitter', 'stealth_use_curl_cffi',
            'stealth_use_playwright', 'stealth_residential_proxies', 'stealth_proxy_api_key',
            'stealth_user_agent_rotation', 'stealth_header_order', 'stealth_mouse_emulation',
            'stealth_scroll_emulation', 'stealth_timing_poisson',
        }
        _risk_fields = {
            'min_single_edge', 'min_parlay_edge', 'min_correct_score_edge', 'kelly_fraction',
            'fractional_kelly_factor', 'non_1x2_xg_discount', 'clv_deadzone_pct',
            'sharp_move_threshold', 'sharp_adjustment_threshold', 'max_drawdown',
            'max_stake_per_bet', 'min_stake_per_bet', 'daily_loss_limit', 'backtest_commission',
            'live_commission', 'execution_slippage', 'bookmaker_daily_limit', 'bookmaker_limit_bets',
            'max_realistic_edge', 'max_bets_per_day', 'max_stake_per_match',
            'exposure_limit_per_league', 'exposure_limit_per_market', 'exposure_limit_per_team',
            'exposure_limit_per_bookmaker', 'exposure_limit_per_outcome', 'risk_free_rate',
            'max_correlation_exposure', 'swan_threshold', 'swan_duration_hours',
            'exploration_budget', 'correlation_risk_threshold', 'volatility_window',
            'global_volatility_window', 'enable_portfolio_opt', 'slippage', 'commission',
            'jitter_min_minutes', 'jitter_max_minutes', 'pending_bet_timeout_hours',
            'liquidity_split_threshold', 'kyc_lock_hours', 'parlay_max_legs', 'parlay_min_legs',
            'parlay_stake_fraction', 'over_line', 'corners_line', 'cards_line', 'elo_k_factor',
            'rejection_loss_threshold', 'bivariate_cov_factor', 'tail_risk_threshold',
            'hawkes_alpha', 'hawkes_beta', 'target_state_dim', 'max_grad_norm',
            'drift_threshold_kl', 'ess_min_ratio', 'xi_threshold', 'surrogate_mae_threshold',
            'hybrid_surrogate_fraction', 'importance_bias_factor', 'tail_scenarios',
            'online_batch_size', 'min_samples_train', 'max_schema_validation_fails',
            'ab_test_min_bets', 'stop_loss_drawdown', 'hedge_threshold',
            'kelly_cov_estimation_window', 'trailing_stop_pct', 'daily_profit_target_pct',
            'weekly_loss_limit', 'monthly_loss_limit', 'max_risk_of_ruin',
            'rollback_roi_threshold', 'rollback_bets_threshold', 'shadow_duration_days',
            'shadow_promotion_threshold_roi', 'shadow_min_bets',
        }
        _data_fields = {
            'db_path', 'in_memory_db', 'historical_data_path', 'model_dir', 'latest_symlink',
            'warm_snapshot_path', 'snapshot_path_a', 'snapshot_path_b', 'proxy_list',
            'external_models', 'ip_whitelist', 'redis_url', 'redis_ttl',
            'circuit_breaker_fail_threshold', 'circuit_breaker_recovery_timeout', 'cache_ttl',
            'retrain_interval_hours', 'health_check_interval', 'tuning_trials',
            'feature_cache_max_size', 'fetcher_cache_max_size', 'audit_prune_days',
            'drift_prune_days', 'jitter_prune_days', 'checkpoint_prune_days',
            'memory_prune_days', 'log_rotation_mb', 'shadow_traffic_percent',
            'attribution_sample_size', 'dashboard_port', 'otel_endpoint', 'ssl_verify',
            'tls_enabled', 'tls_generate_self_signed', 'tls_certfile', 'tls_keyfile',
            'tls_common_name', 'max_concurrent_requests', 'data_freeze_timeout',
            'jitter_concurrent', 'batch_checkpoint_recovery', 'migration_retry_attempts',
            'vacuum_interval_hours', 'archive_interval_days', 'bookmaker_max_loss_percent',
            'bias_alert_threshold', 'imputation_strategy', 'log_missing_data', 'exchange_type',
            's3_endpoint', 's3_bucket', 's3_key', 's3_secret', 'backtest_start', 'backtest_end',
            'flat_stake_pct', 'external_api_url', 'department_mode', 'state_version',
            'profile_mode', 'strict_dependencies', 'websocket_url',
        }
        _exchange_fields = {
            'pinnacle_api_key', 'pinnacle_api_base_url', 'pinnacle_odds_market',
            'betfair_username', 'betfair_password', 'betfair_app_key',
            'exchange_key', 'exchange_secret', 'exchange_session_token',
        }
        _notification_fields = {
            'telegram_token', 'telegram_chat_id', 'telegram_poll_interval_seconds',
            'telegram_allowed_user_ids', 'enable_telegram_chat_bot',
            'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 'smtp_from',
            'email_recipients', 'smtp_use_tls', 'slack_webhook', 'discord_webhook',
            'prometheus_port',
        }
        _security_fields = {
            'secret_key', 'encrypt_secrets', 'encryption_key', 'rate_limit', 'active_tactics_limit',
        }
        _ml_fields = {
            'deepseek_enabled', 'deepseek_api_key', 'deepseek_api_base_url', 'deepseek_model',
            'deepseek_timeout', 'deepseek_max_retries', 'ensemble_weights', 'genetic_features',
            'enable_genetic_features', 'enable_advanced_math', 'enable_negative_binomial',
            'enable_bandit_ensemble', 'enable_ab_testing', 'enable_online_learning',
            'enable_quantization', 'enable_batch_prediction', 'enable_flat_baseline',
            'enable_unified_engine', 'enable_x_tactics', 'enable_redis_distributed_lock',
            'enable_postgres', 'enable_otel', 'enable_feature_attribution', 'enable_dashboard',
            'enable_hyper_tuning', 'enable_causal_graph', 'enable_feature_store',
            'enable_purged_cv', 'enable_bayesian_updater', 'enable_ensemble_weight_optimizer',
            'enable_causal_selection', 'enable_market_implied_features', 'enable_league_regime_scaler',
            'enable_exogenous_encoder', 'enable_official_feed_gateway', 'enable_order_book_processor',
            'enable_heartbeat_monitor',
        }
        if name in _stealth_fields:
            setattr(self.stealth, name, value)
        elif name in _risk_fields:
            setattr(self.risk, name, value)
        elif name in _data_fields:
            setattr(self.data, name, value)
        elif name in _exchange_fields:
            setattr(self.exchange, name, value)
        elif name in _notification_fields:
            setattr(self.notification, name, value)
        elif name in _security_fields:
            setattr(self.security, name, value)
        elif name in _ml_fields:
            setattr(self.ml, name, value)
        else:
            super().__setattr__(name, value)


# Pydantic v2.13 requires an explicit rebuild'''

if old_redacted in text:
    text = text.replace(old_redacted, new_redacted, 1)
    MAIN.write_text(text, encoding='utf-8')
    print('Added backward-compatible __getattr__ and __setattr__ to Settings')
else:
    print('ERROR: Could not find redacted_dict method')
