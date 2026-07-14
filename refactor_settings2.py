#!/usr/bin/env python3
"""
Refactor Settings into nested configs.
"""

import re
from pathlib import Path

MAIN = Path(r'C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py')
BACKUP = Path(r'C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py.settings_backup2')

text = MAIN.read_text(encoding='utf-8')

if not BACKUP.exists():
    BACKUP.write_text(text, encoding='utf-8')
    print('Backup created')

# Find the Settings class and everything until CONFIG = Settings()
# We need to replace the entire Settings class definition

# Pattern to find Settings class through CONFIG = Settings()
pattern = r'class Settings\(BaseSettings\):.*?^CONFIG = Settings\(\)'
match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
if not match:
    print('ERROR: Could not find Settings class')
    exit(1)

old_settings_block = match.group(0)
print(f'Found Settings block, length: {len(old_settings_block)}')

# Build new block
new_block = '''class StealthSettings(BaseModel):
    use_stealth_scraping: bool = True
    tls_impersonate: str = "chrome120"
    proxy_rotation: bool = True
    browser_mode: bool = True
    human_behavior: bool = True
    session_lifetime_min: int = 600
    session_lifetime_max: int = 3600
    request_jitter: bool = True
    use_curl_cffi: bool = True
    use_playwright: bool = True
    residential_proxies: bool = False
    proxy_api_key: str = ""
    user_agent_rotation: bool = True
    header_order: bool = True
    mouse_emulation: bool = True
    scroll_emulation: bool = True
    timing_poisson: bool = True


class RiskSettings(BaseModel):
    min_single_edge: float = 0.03
    min_parlay_edge: float = 0.05
    min_correct_score_edge: float = 0.10
    kelly_fraction: float = 0.15
    fractional_kelly_factor: float = 0.25
    non_1x2_xg_discount: float = 1.0
    clv_deadzone_pct: float = 0.02
    sharp_move_threshold: float = 0.03
    sharp_adjustment_threshold: float = 0.02
    max_drawdown: float = 0.20
    max_stake_per_bet: float = 0.018
    min_stake_per_bet: float = 0.001
    daily_loss_limit: float = 0.05
    backtest_commission: float = 0.03
    live_commission: float = 0.02
    execution_slippage: float = 0.006
    bookmaker_daily_limit: float = 800.0
    bookmaker_limit_bets: int = 3
    max_realistic_edge: float = 0.06
    max_bets_per_day: int = 50
    max_stake_per_match: float = 0.05
    exposure_limit_per_league: float = 0.10
    exposure_limit_per_market: float = 0.05
    exposure_limit_per_team: float = 0.03
    exposure_limit_per_bookmaker: float = 0.08
    exposure_limit_per_outcome: float = 0.05
    risk_free_rate: float = 0.01
    max_correlation_exposure: float = 0.15
    swan_threshold: float = 0.10
    swan_duration_hours: int = 72
    exploration_budget: float = 0.05
    correlation_risk_threshold: float = 0.6
    volatility_window: int = 30
    global_volatility_window: int = 30
    enable_portfolio_opt: bool = True
    slippage: float = 0.005
    commission: float = 0.02
    jitter_min_minutes: int = 8
    jitter_max_minutes: int = 15
    pending_bet_timeout_hours: int = 48
    liquidity_split_threshold: float = 0.2
    kyc_lock_hours: int = 48
    parlay_max_legs: int = 5
    parlay_min_legs: int = 3
    parlay_stake_fraction: float = 0.01
    over_line: float = 2.5
    corners_line: float = 9.5
    cards_line: float = 45.0
    elo_k_factor: int = 20
    rejection_loss_threshold: float = 0.6
    bivariate_cov_factor: float = 0.2
    tail_risk_threshold: float = 0.05
    hawkes_alpha: float = 0.3
    hawkes_beta: float = 1.2
    target_state_dim: int = 16
    max_grad_norm: float = 1.0
    drift_threshold_kl: float = 0.5
    ess_min_ratio: float = 0.2
    xi_threshold: float = 0.5
    surrogate_mae_threshold: float = 0.05
    hybrid_surrogate_fraction: float = 0.9
    importance_bias_factor: float = 1.3
    tail_scenarios: int = 200
    online_batch_size: int = 50
    min_samples_train: int = 200
    max_schema_validation_fails: int = 3
    ab_test_min_bets: int = 50
    stop_loss_drawdown: float = 0.15
    hedge_threshold: float = 0.3
    kelly_cov_estimation_window: int = 50
    trailing_stop_pct: float = 0.10
    daily_profit_target_pct: float = 0.05
    weekly_loss_limit: float = 0.10
    monthly_loss_limit: float = 0.20
    max_risk_of_ruin: float = 0.05
    rollback_roi_threshold: float = -0.03
    rollback_bets_threshold: int = 20
    shadow_duration_days: int = 14
    shadow_promotion_threshold_roi: float = 0.03
    shadow_min_bets: int = 100


class DataSettings(BaseModel):
    db_path: str = "lhm_prod.db"
    in_memory_db: bool = False
    historical_data_path: str = "data/historical.csv"
    model_dir: str = "models"
    latest_symlink: str = "models/latest"
    warm_snapshot_path: str = "/dev/shm/lhm_snapshot.pkl"
    snapshot_path_a: str = "lhm_snapshot_A.pkl"
    snapshot_path_b: str = "lhm_snapshot_B.pkl"
    proxy_list: List[str] = []
    external_models: List[str] = []
    ip_whitelist: List[str] = []
    redis_url: str = "redis://localhost:6379/0"
    redis_ttl: int = 3600
    circuit_breaker_fail_threshold: int = 3
    circuit_breaker_recovery_timeout: int = 60
    cache_ttl: int = 300
    retrain_interval_hours: int = 24
    health_check_interval: int = 3600
    tuning_trials: int = 50
    feature_cache_max_size: int = 10000
    fetcher_cache_max_size: int = 5000
    audit_prune_days: int = 90
    drift_prune_days: int = 30
    jitter_prune_days: int = 30
    checkpoint_prune_days: int = 7
    memory_prune_days: int = 90
    log_rotation_mb: int = 100
    shadow_traffic_percent: float = 5.0
    attribution_sample_size: int = 100
    dashboard_port: int = 3000
    otel_endpoint: str = "localhost:4317"
    ssl_verify: bool = True
    tls_enabled: bool = False
    tls_generate_self_signed: bool = False
    tls_certfile: str = "certs/lhm_cert.pem"
    tls_keyfile: str = "certs/lhm_key.pem"
    tls_common_name: str = "localhost"
    max_concurrent_requests: int = 10
    data_freeze_timeout: int = 300
    jitter_concurrent: bool = True
    batch_checkpoint_recovery: bool = True
    migration_retry_attempts: int = 3
    vacuum_interval_hours: int = 24
    archive_interval_days: int = 30
    bookmaker_max_loss_percent: float = 0.02
    bias_alert_threshold: float = 0.15
    imputation_strategy: str = "mean"
    log_missing_data: bool = True
    exchange_type: str = "betfair"
    s3_endpoint: str = ""
    s3_bucket: str = "lhm-models"
    s3_key: str = ""
    s3_secret: str = ""
    backtest_start: str = "2020-01-01"
    backtest_end: str = ""
    flat_stake_pct: float = 0.01
    external_api_url: str = ""
    department_mode: str = "unified"
    state_version: int = 3
    profile_mode: bool = False
    strict_dependencies: bool = False
    websocket_url: str = "wss://stream.betfair.com/"


class ExchangeSettings(BaseModel):
    pinnacle_api_key: str = ""
    pinnacle_api_base_url: str = "https://api.pinnacle.com/v1"
    pinnacle_odds_market: str = "soccer_epl"
    betfair_username: str = ""
    betfair_password: str = ""
    betfair_app_key: str = ""
    exchange_key: str = ""
    exchange_secret: str = ""
    exchange_session_token: str = ""


class NotificationSettings(BaseModel):
    telegram_token: str = Field(default="")
    telegram_chat_id: str = Field(default="")
    telegram_poll_interval_seconds: int = 6
    telegram_allowed_user_ids: str = ""
    enable_telegram_chat_bot: bool = True
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    email_recipients: str = ""
    smtp_use_tls: bool = True
    slack_webhook: str = ""
    discord_webhook: str = ""
    prometheus_port: int = 8001


class SecuritySettings(BaseModel):
    secret_key: str = ""
    encrypt_secrets: bool = True
    encryption_key: str = ""
    rate_limit: int = 100
    active_tactics_limit: int = 100


class MLConfig(BaseModel):
    deepseek_enabled: bool = True
    deepseek_api_key: str = Field(default="")
    deepseek_api_base_url: str = Field(default="https://api.deepseek.com")
    deepseek_model: str = Field(default="deepseek-chat")
    deepseek_timeout: int = Field(default=10, ge=1, le=60)
    deepseek_max_retries: int = Field(default=2, ge=1, le=5)
    ensemble_weights: Dict[str, float] = {"xgb":0.35, "lgb":0.25, "rf":0.20, "lr":0.10, "external":0.10}
    genetic_features: List[str] = []
    enable_genetic_features: bool = False
    enable_advanced_math: bool = True
    enable_negative_binomial: bool = True
    enable_bandit_ensemble: bool = True
    enable_ab_testing: bool = True
    enable_online_learning: bool = True
    enable_quantization: bool = False
    enable_batch_prediction: bool = True
    enable_flat_baseline: bool = True
    enable_unified_engine: bool = True
    enable_x_tactics: bool = True
    enable_redis_distributed_lock: bool = False
    enable_postgres: bool = False
    enable_otel: bool = False
    enable_feature_attribution: bool = False
    enable_dashboard: bool = False
    enable_hyper_tuning: bool = False
    enable_causal_graph: bool = False
    enable_feature_store: bool = False
    enable_purged_cv: bool = True
    enable_bayesian_updater: bool = True
    enable_ensemble_weight_optimizer: bool = True
    enable_causal_selection: bool = True
    enable_market_implied_features: bool = True
    enable_league_regime_scaler: bool = True
    enable_exogenous_encoder: bool = True
    enable_official_feed_gateway: bool = False
    enable_order_book_processor: bool = False
    enable_heartbeat_monitor: bool = True


class RiskHardeningSettings(BaseModel):
    enable_risk_hardening: bool = True
    enable_feature_pruning: bool = True
    max_features_used: int = 35
    enable_slippage_model: bool = True
    slippage_bps: float = 3.0
    enable_market_depth_check: bool = True
    min_market_depth: float = 500.0
    enable_bookmaker_stealth: bool = True
    stake_randomization_pct: float = 0.15
    bookmaker_max_daily_stake: float = 0.02
    bookmaker_cooldown_hours: int = 4
    enable_shadow_validation: bool = True
    shadow_validation_bets: int = 50
    enable_walk_forward: bool = True
    walk_forward_window_days: int = 90
    enable_api_circuit_breaker: bool = True
    api_failure_threshold: int = 5
    api_cooldown_minutes: int = 30
    enable_stake_ratcheting: bool = True
    stake_ratchet_drawdown_limit: float = 0.08
    enable_correlation_filter: bool = True
    max_correlation_between_bets: float = 0.35
    enable_odds_freshness_check: bool = True
    odds_max_age_seconds: int = 120
    enable_commission_netting: bool = True
    commission_rate: float = 0.02
    enable_variance_shrinkage: bool = True
    variance_shrinkage_factor: float = 0.15
    enable_result_audit: bool = True
    audit_log_path: str = "audit/bet_audit.jsonl"
    max_bets_per_hour: int = 10
    max_stake_per_hour: float = 0.05
    enable_stake_decay: bool = True
    stake_decay_factor: float = 0.85
    consecutive_loss_stake_cut: int = 3
    enable_bookmaker_limit_predictor: bool = True
    bookmaker_limit_alert_stake: float = 0.01
    enable_stealth_staking: bool = True
    stealth_stake_variance: float = 0.12


class AutoSettings(BaseModel):
    enable_auto_self_test: bool = True
    auto_self_test_interval_hours: int = 6
    enable_auto_backtest_cycle: bool = True
    auto_backtest_interval_hours: int = 24
    enable_auto_adaptation_cycle: bool = True
    auto_adaptation_interval_hours: int = 24
    enable_auto_vacuum: bool = True
    enable_migration_retry: bool = True
    enable_file_watcher: bool = False
    enable_health_server: bool = True


class MoneyPrintingSettings(BaseModel):
    enable_money_printing: bool = True
    enable_dynamic_edge: bool = True
    enable_iceberg_immediate: bool = True
    enable_lower_league_mode: bool = True
    enable_prematch_backtest: bool = True
    enable_vig_buster: bool = True
    edge_odds_sweet_spot_min: float = 1.6
    edge_odds_sweet_spot_max: float = 2.8
    edge_favorite_min: float = 0.02
    edge_mid_min: float = 0.04
    edge_longshot_min: float = 0.08
    lower_league_sports: str = "soccer_spain_segunda,soccer_brazil_campeonato,soccer_romania_liga1,soccer_poland_ekstraklasa,soccer_czech_league,soccer_croatia_hnl,soccer_serbia_superliga,soccer_bulgaria_league,soccer_hungary_league,soccer_slovakia_league"
    money_printing_interval: int = 60
    model_weights_override: str = '{"xgb":0.55,"poisson":0.35,"lgb":0.10,"rf":0.0,"lr":0.0,"external":0.0}'


class UpgradeSettings(BaseModel):
    enable_liquidity_routing: bool = False
    enable_slippage_predictor: bool = False
    enable_bookmaker_router: bool = False
    enable_atomic_bet_unit: bool = False
    enable_covariance_kelly: bool = True
    enable_dd_kelly: bool = True
    enable_tail_hedge: bool = True
    enable_pnl_attribution: bool = True
    enable_auto_rollback: bool = True
    enable_shadow_tester: bool = False
    enable_drift_telemetry: bool = True
    enable_replay_engine: bool = True
    enable_edge_decay_tracker: bool = True
    lhm_upgrades_initialized: bool = False
    enable_bookmaker_limit_monitoring: bool = True
    enable_possession_data: bool = True
    enable_shot_on_target: bool = True
    enable_big_chances: bool = True
    enable_goalkeeper_saves: bool = False
    enable_red_cards: bool = False
    enable_penalties: bool = False
    enable_substitutions: bool = False
    enable_manager_changes: bool = False
    enable_squad_value: bool = False


class DigestSettings(BaseModel):
    enable_daily_top20_digest: bool = True
    daily_digest_top_n: int = 20
    daily_digest_hour: int = 7
    daily_digest_minute: int = 0
    daily_digest_window_minutes: int = 15
    daily_digest_timezone: str = "Europe/Berlin"


class Settings(BaseSettings):
    db_path: str = "lhm_prod.db"
    in_memory_db: bool = False
    dry_run: bool = False
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    loop_interval: int = 30
    tax_jurisdiction: str = "US"
    stealth_mode: bool = False
    max_retries: int = 3
    timeout: int = 10
    stealth: StealthSettings = StealthSettings()
    risk: RiskSettings = RiskSettings()
    data: DataSettings = DataSettings()
    exchange: ExchangeSettings = ExchangeSettings()
    notification: NotificationSettings = NotificationSettings()
    security: SecuritySettings = SecuritySettings()
    ml: MLConfig = MLConfig()
    risk_hardening: RiskHardeningSettings = RiskHardeningSettings()
    auto: AutoSettings = AutoSettings()
    money_printing: MoneyPrintingSettings = MoneyPrintingSettings()
    upgrades: UpgradeSettings = UpgradeSettings()
    digest: DigestSettings = DigestSettings()
    odds_api_key: str = ""
    api_football_key: str = ""
    odds_api_io_key: str = ""
    weather_api_key: str = ""
    football_api_key: str = ""
    stats_api_key: str = ""
    twitter_bearer_token: str = ""
    news_api_key: str = ""
    external_api_key: str = ""
    betpawa_phone: str = ""
    betpawa_password: str = ""
    betika_phone: str = ""
    betika_password: str = ""
    use_free_scrapers: bool = True
    enable_arbitrage: bool = True
    enable_websocket: bool = False
    enable_extra_time_handling: bool = True
    enable_live_odds: bool = False
    enable_lineup_scraper: bool = True
    enable_sharp_money_scraper: bool = True
    enable_rl_staking: bool = False
    enable_event_sourcing: bool = True
    enable_news_nlp: bool = True
    enable_live_enrichment: bool = True
    enable_prometheus: bool = True
    enable_redis_cache: bool = False
    enable_warm_snapshot: bool = False
    enable_stop_loss: bool = True
    enable_hedging: bool = False
    enable_correlation_adjusted_kelly: bool = True
    enable_trailing_stop: bool = True
    enable_profit_target: bool = True
    enable_risk_of_ruin_check: bool = True
    enable_auto_rollback: bool = True
    enable_benchmark: bool = True
    enable_shadow_mode: bool = False
    enable_archiving: bool = False
    enable_lower_league_mode: bool = True
    first_half_goal_factor: float = 0.46
    enable_research_in_market_rows: bool = True
    max_research_contradiction_penalty: float = 0.12
    public_awareness_blend: float = 0.18
    public_awareness_max_shift: float = 0.12
    public_hype_penalty_factor: float = 0.08
    sharp_public_divergence_factor: float = 0.06
    live_enrichment_timeout: int = 8
    research_snippet_limit: int = 4
    min_data_quality_for_market_expansion: float = 0.72
    min_research_confidence: float = 0.25
    allow_synthetic_market_odds: bool = False
    auto_upgrade_report_path: str = "backups/auto_upgrade_report.json"
    awareness_calibration_refresh_seconds: int = 1800
    min_awareness_calibration_samples: int = 50

    model_config = ConfigDict(
        env_file=".env",
        env_prefix="LHM_",
        case_sensitive=False,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.ml.enable_postgres:
            log.warning("enable_postgres requested but Postgres adapter is not implemented; forcing enable_postgres=False")
            self.ml.enable_postgres = False
        if self.ml.enable_otel:
            log.warning("enable_otel requested but tracing spans are not fully implemented; forcing enable_otel=False")
            self.ml.enable_otel = False
        if self.ml.enable_quantization:
            log.warning("enable_quantization requested but quantization pipeline is not implemented; forcing enable_quantization=False")
            self.ml.enable_quantization = False
        if self.ml.enable_feature_attribution:
            log.warning("enable_feature_attribution requested but attribution backend is unavailable; forcing enable_feature_attribution=False")
            self.ml.enable_feature_attribution = False
        self.data.warm_snapshot_path = self.resolve_snapshot_path(self.data.warm_snapshot_path)
        self.data.snapshot_path_a = self.resolve_snapshot_path(self.data.snapshot_path_a)
        self.data.snapshot_path_b = self.resolve_snapshot_path(self.data.snapshot_path_b)
        self._setup_directories()

    def _setup_directories(self):
        for d in [self.data.model_dir, os.path.dirname(self.data.historical_data_path), "migrations", "logs", "backups", os.path.dirname(self.data.warm_snapshot_path)]:
            if d:
                os.makedirs(d, exist_ok=True)

    def resolve_snapshot_path(self, path: str) -> str:
        if not path:
            return path
        if path == "/dev/shm/lhm_snapshot.pkl" and os.name != "posix":
            fallback_dir = os.path.join(os.getcwd(), "snapshots")
            os.makedirs(fallback_dir, exist_ok=True)
            return os.path.join(fallback_dir, "lhm_snapshot.pkl")
        return path

    def snapshot_paths(self) -> List[str]:
        if not self.data.enable_warm_snapshot:
            return []
        return [self.resolve_snapshot_path(p) for p in [self.data.warm_snapshot_path, self.data.snapshot_path_a, self.data.snapshot_path_b] if p]

    def runtime_security_warnings(self) -> List[str]:
        warnings = []
        if not self.security.secret_key or self.security.secret_key == "change_this_in_production":
            warnings.append("secret_key is still unset or using the default placeholder")
        if self.security.encrypt_secrets and not self.security.encryption_key:
            warnings.append("encrypt_secrets is enabled but encryption_key is empty")
        if self.ml.deepseek_enabled and not self.ml.deepseek_api_key:
            warnings.append("DeepSeek is enabled but no API key is configured")
        return warnings

    @field_validator('risk.max_stake_per_bet', mode='after')
    def validate_max_stake(cls, v, info):
        exposure = info.data.get('risk', {}).get('exposure_limit_per_league', 1) if info else 1
        if v > exposure:
            raise ValueError("max_stake_per_bet cannot exceed exposure_limit_per_league")
        return v

    @field_validator('risk.fractional_kelly_factor', mode='after')
    def validate_fractional_kelly(cls, v, info):
        if v < 0 or v > 1:
            raise ValueError("fractional_kelly_factor must be between 0 and 1")
        return v

    @field_validator('risk.min_single_edge', mode='after')
    def validate_min_edge(cls, v, info):
        if v < -0.1 or v > 0.5:
            raise ValueError("min_single_edge out of bounds")
        return v

    @field_validator('ml.deepseek_api_key', 'ml.deepseek_api_base_url', 'ml.deepseek_model', mode='before')
    def normalize_deepseek_settings(cls, v, info):
        if isinstance(v, str):
            v = v.strip()
            if info and info.field_name == 'deepseek_api_key':
                return v
            if info and info.field_name in {'deepseek_api_base_url', 'deepseek_model'} and not v:
                return info.field_info.default if hasattr(info, 'field_info') else v
        return v

    @field_validator('ml.deepseek_api_key', mode='after')
    def validate_deepseek_api_key(cls, v, info):
        key = str(v or "").strip()
        if not key:
            return key
        if len(key) < 12 or re.search(r"\s", key):
            raise ValueError("deepseek_api_key format appears invalid")
        return key

    @field_validator('data.proxy_list', mode='before')
    def normalize_proxy_list(cls, v, info):
        if v is None:
            return []
        if isinstance(v, str):
            parts = [p.strip() for p in v.split(',') if p.strip()]
        elif isinstance(v, list):
            parts = [str(p).strip() for p in v if str(p).strip()]
        else:
            return []
        valid = []
        for p in parts:
            if re.match(r"^https?://", p, flags=re.IGNORECASE):
                valid.append(p)
            else:
                log.warning(f"Ignoring invalid proxy URL (missing scheme): {p}")
        return valid

    def redacted_dict(self) -> Dict[str, Any]:
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


# Pydantic v2.13 requires an explicit rebuild when `from __future__ import
# annotations` stringizes the `List`/`Dict` field annotations above.
Settings.model_rebuild()

try:
    from dotenv import load_dotenv
    from pathlib import Path
    env_path = Path(__file__).with_name(".env")
    if env_path.exists():
        load_dotenv(env_path, override=True)
except Exception:
    pass

CONFIG = Settings()
'''

new_text = text.replace(old_settings_block, new_block, 1)

if new_text == text:
    print('ERROR: Replacement failed - no changes made')
    # Try to show what's around CONFIG = Settings()
    idx = text.find('CONFIG = Settings()')
    if idx >= 0:
        print('Context around CONFIG:')
        print(text[max(0, idx-200):idx+100])
else:
    MAIN.write_text(new_text, encoding='utf-8')
    print('Settings refactored successfully')
    print(f'Old length: {len(old_settings_block)}, New length: {len(new_block)}')
