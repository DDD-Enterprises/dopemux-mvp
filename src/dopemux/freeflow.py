"""Strict-free LLM routing policy and quota ledger for Dopemux."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
from zoneinfo import ZoneInfo

STRICT_FREE_MODE = "strict_free"
FREEFLOW_LEDGER_ENV = "DOPEMUX_FREEFLOW_LEDGER"
LOCAL_PROVIDERS = {"ollama", "lmstudio"}
HOSTED_FREE_PROVIDERS = {
    "gemini",
    "groq",
    "cerebras",
    "openrouter_free",
    "cloudflare_workers_ai",
    "cohere_trial",
    "mistral_experiment",
    "github_models_poc",
    "hf_credits",
}
PAID_CAP_PROVIDERS = {
    "gemini_paid_cap",
    "openrouter_paid_cap",
}
BLOCKED_PAID_PROVIDERS = {
    "anthropic",
    "deepseek",
    "fireworks",
    "openai",
    "openrouter_paid",
    "together",
    "xai",
}
SENSITIVE_CLASSES = {"sensitive", "memory", "context", "raw_memory", "private"}
NON_SENSITIVE_CLASS = "non_sensitive"
PACIFIC = ZoneInfo("America/Los_Angeles")


PROVIDER_CATALOG: Dict[str, Dict[str, Any]] = {
    "ollama": {
        "kind": "local",
        "zero_cost": True,
        "auth_mode": "none",
        "source_url": "https://docs.ollama.com/api/introduction",
        "last_verified": "2026-05-01",
    },
    "lmstudio": {
        "kind": "local",
        "zero_cost": True,
        "auth_mode": "none",
        "source_url": "https://lmstudio.ai/docs/developer",
        "last_verified": "2026-05-01",
    },
    "gemini": {
        "kind": "hosted_free_tier",
        "zero_cost": True,
        "source_url": "https://ai.google.dev/gemini-api/docs/rate-limits",
        "last_verified": "2026-05-01",
        "limits": {
            "rpm": 15,
            "tpm": 250000,
            "rpd": 1000,
            "day_reset": "pacific_midnight",
        },
        "score": 90,
    },
    "groq": {
        "kind": "hosted_free_tier",
        "zero_cost": True,
        "source_url": "https://console.groq.com/docs/rate-limits",
        "last_verified": "2026-05-01",
        "limits": {"rpm": 30, "tpm": 6000, "rpd": 1000, "tpd": 500000},
        "score": 85,
    },
    "cerebras": {
        "kind": "hosted_free_tier",
        "zero_cost": True,
        "source_url": "https://inference-docs.cerebras.ai/support/rate-limits",
        "last_verified": "2026-05-01",
        "limits": {"rpm": 30, "tpm": 60000, "rpd": 14400, "tpd": 1000000},
        "score": 80,
    },
    "cloudflare_workers_ai": {
        "kind": "hosted_free_allocation",
        "zero_cost": True,
        "source_url": "https://developers.cloudflare.com/workers-ai/platform/pricing/",
        "last_verified": "2026-05-01",
        "limits": {"neurons_per_day": 10000, "day_reset": "utc_midnight"},
        "score": 70,
    },
    "openrouter_free": {
        "kind": "hosted_free_tier",
        "zero_cost": True,
        "source_url": "https://openrouter.ai/pricing",
        "last_verified": "2026-05-01",
        "limits": {"rpm": 20, "rpd": 50, "day_reset": "utc_midnight"},
        "score": 40,
    },
    "cohere_trial": {
        "kind": "trial",
        "zero_cost": True,
        "source_url": "https://docs.cohere.com/v2/docs/rate-limits",
        "last_verified": "2026-05-01",
        "limits": {"rpm": 20, "requests_per_month": 1000},
        "score": 35,
    },
    "mistral_experiment": {
        "kind": "workspace_specific_free_tier",
        "zero_cost": True,
        "source_url": "https://docs.mistral.ai/admin/user-management-finops/tier",
        "last_verified": "2026-05-01",
        "limits": {},
        "score": 30,
    },
    "github_models_poc": {
        "kind": "poc_only",
        "zero_cost": True,
        "source_url": "https://docs.github.com/en/github-models/responsible-use-of-github-models",
        "last_verified": "2026-05-01",
        "limits": {},
        "score": 25,
    },
    "hf_credits": {
        "kind": "monthly_credit",
        "zero_cost": True,
        "source_url": "https://huggingface.co/docs/inference-providers/en/pricing",
        "last_verified": "2026-05-01",
        "limits": {},
        "score": 20,
    },
    "gemini_paid_cap": {
        "kind": "paid_cap",
        "zero_cost": False,
        "source_url": "https://ai.google.dev/gemini-api/docs/pricing",
        "last_verified": "2026-05-01",
        "pricing": {
            "gemini/gemini-2.5-flash-lite": {
                "input_usd_per_million": 0.18,
                "output_usd_per_million": 0.72,
            },
            "gemini/gemini-2.5-flash-lite-preview-09-2025": {
                "input_usd_per_million": 0.10,
                "output_usd_per_million": 0.40,
            },
        },
        "score": 12,
    },
    "openrouter_paid_cap": {
        "kind": "paid_cap",
        "zero_cost": False,
        "source_url": "https://openrouter.ai/qwen/qwen3-coder-next/pricing",
        "last_verified": "2026-05-01",
        "pricing": {
            "openrouter/qwen/qwen3-coder-next": {
                "input_usd_per_million": 0.12,
                "output_usd_per_million": 0.80,
            },
            "openrouter/qwen/qwen3-coder": {
                "input_usd_per_million": 0.22,
                "output_usd_per_million": 1.80,
            },
        },
        "score": 10,
    },
}


@dataclass(frozen=True)
class QuotaCheck:
    allowed: bool
    reason: str
    reset_at: Optional[str] = None


class FreeflowQuotaExceeded(RuntimeError):
    """Raised when strict-free admission control blocks an upstream call."""

    def __init__(self, reason: str, reset_at: Optional[str] = None):
        self.reason = reason
        self.reset_at = reset_at
        suffix = f" reset_at={reset_at}" if reset_at else ""
        super().__init__(f"freeflow quota blocked provider call: {reason}{suffix}")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def isoformat_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_iso_datetime(value: str | None) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
            timezone.utc
        )
    except ValueError:
        return None


def normalize_sensitivity(value: str | None) -> str:
    token = str(value or NON_SENSITIVE_CLASS).strip().lower()
    if token in SENSITIVE_CLASSES:
        return "sensitive"
    return NON_SENSITIVE_CLASS


def estimate_text_tokens(value: str) -> int:
    return max(1, (len(value or "") + 3) // 4)


def default_ledger_path() -> Path:
    override = os.getenv(FREEFLOW_LEDGER_ENV)
    if override:
        return Path(override).expanduser()
    return Path.home() / ".dopemux" / "freeflow" / "quota.sqlite"


def freeflow_policy(config: Dict[str, Any]) -> Dict[str, Any]:
    policy = dict(config.get("freeflow") or {})
    policy.setdefault("enabled", False)
    policy.setdefault("mode", STRICT_FREE_MODE)
    policy.setdefault("privacy_default", "local")
    policy.setdefault("ledger_path_env", FREEFLOW_LEDGER_ENV)
    policy.setdefault("slots", {})
    policy.setdefault("default_fallbacks", [])
    return policy


def paid_cap_policy(config: Dict[str, Any]) -> Dict[str, Any]:
    policy = dict(freeflow_policy(config).get("paid_cap") or {})
    policy.setdefault("enabled", False)
    policy.setdefault("daily_usd", 0.0)
    policy.setdefault("monthly_usd", 0.0)
    policy.setdefault("allowed_models", [])
    policy.setdefault("default_fallbacks", [])
    policy.setdefault("day_reset", "utc_midnight")
    return policy


def strict_free_enabled(config: Dict[str, Any]) -> bool:
    policy = freeflow_policy(config)
    return bool(policy.get("enabled")) and policy.get("mode") == STRICT_FREE_MODE


def paid_cap_enabled(config: Dict[str, Any]) -> bool:
    return strict_free_enabled(config) and bool(paid_cap_policy(config).get("enabled"))


def is_openrouter_free_model(model_id: str) -> bool:
    token = str(model_id or "").lower()
    return token.endswith(":free") or token in {
        "openrouter/openrouter/free",
        "openrouter/free",
    }


def classify_route(provider: str, model_id: str) -> Dict[str, Any]:
    provider_token = str(provider or "").strip().lower()
    model_token = str(model_id or "").strip()
    if provider_token in LOCAL_PROVIDERS:
        return {"allowed": True, "local": True, "reason": "local_zero_cost"}
    if provider_token == "openrouter":
        if is_openrouter_free_model(model_token):
            return {
                "allowed": True,
                "local": False,
                "provider_alias": "openrouter_free",
                "reason": "openrouter_free_variant",
            }
        return {"allowed": False, "local": False, "reason": "paid_openrouter_blocked"}
    if provider_token == "openrouter_free":
        if is_openrouter_free_model(model_token):
            return {
                "allowed": True,
                "local": False,
                "reason": "openrouter_free_variant",
            }
        return {
            "allowed": False,
            "local": False,
            "reason": "openrouter_free_provider_requires_free_model",
        }
    if provider_token in HOSTED_FREE_PROVIDERS:
        return {"allowed": True, "local": False, "reason": "hosted_free_tier"}
    if provider_token in PAID_CAP_PROVIDERS:
        return {
            "allowed": False,
            "local": False,
            "reason": "paid_cap_route_requires_allowlist",
        }
    if provider_token in BLOCKED_PAID_PROVIDERS:
        return {"allowed": False, "local": False, "reason": "paid_provider_blocked"}
    return {"allowed": False, "local": False, "reason": "unknown_provider_blocked"}


def _provider_catalog_key(provider: str, model_id: str) -> str:
    classified = classify_route(provider, model_id)
    return str(classified.get("provider_alias") or provider).strip().lower()


def _safe_json(value: Any) -> str:
    return json.dumps(value or {}, ensure_ascii=True, sort_keys=True)


def estimate_cost_usd(
    pricing: Dict[str, Any], input_tokens: int, output_tokens: int
) -> float:
    input_rate = float(pricing.get("input_usd_per_million") or 0.0)
    output_rate = float(pricing.get("output_usd_per_million") or 0.0)
    cost = (
        max(0, int(input_tokens or 0)) * input_rate
        + max(0, int(output_tokens or 0)) * output_rate
    ) / 1_000_000
    return round(cost, 8)


def _catalog_pricing(catalog_key: str, model_id: str) -> Dict[str, Any]:
    catalog = PROVIDER_CATALOG.get(catalog_key, {})
    pricing = catalog.get("pricing") or {}
    if "input_usd_per_million" in pricing:
        return dict(pricing)
    return dict(pricing.get(model_id) or {})


def _window_start(window: str, now: datetime, day_reset: str | None = None) -> datetime:
    current = now.astimezone(timezone.utc)
    if window == "minute":
        return current.replace(second=0, microsecond=0)
    if window == "month":
        return current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if window == "day" and day_reset == "pacific_midnight":
        pacific_now = current.astimezone(PACIFIC)
        pacific_start = pacific_now.replace(hour=0, minute=0, second=0, microsecond=0)
        return pacific_start.astimezone(timezone.utc)
    return current.replace(hour=0, minute=0, second=0, microsecond=0)


def _window_end(window: str, now: datetime, day_reset: str | None = None) -> datetime:
    start = _window_start(window, now, day_reset)
    if window == "minute":
        return start + timedelta(minutes=1)
    if window == "month":
        year = start.year + (1 if start.month == 12 else 0)
        month = 1 if start.month == 12 else start.month + 1
        return start.replace(year=year, month=month)
    return start + timedelta(days=1)


def _parse_reset_seconds(value: str | None) -> Optional[float]:
    raw = str(value or "").strip().lower()
    if not raw:
        return None
    try:
        return max(0.0, float(raw))
    except ValueError:
        pass
    total = 0.0
    matched = False
    for number, unit in re.findall(r"([0-9]+(?:\.[0-9]+)?)(ms|s|m|h)", raw):
        matched = True
        amount = float(number)
        if unit == "ms":
            total += amount / 1000.0
        elif unit == "s":
            total += amount
        elif unit == "m":
            total += amount * 60.0
        elif unit == "h":
            total += amount * 3600.0
    return total if matched else None


class FreeflowQuotaLedger:
    """SQLite-backed quota ledger with append-only events and window counters."""

    def __init__(self, path: Path | str | None = None):
        self.path = Path(path).expanduser() if path else default_ledger_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS usage_events (
                    event_id TEXT PRIMARY KEY,
                    recorded_at TEXT NOT NULL,
                    route_decision_id TEXT,
                    provider TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    bucket_id TEXT NOT NULL,
                    requests INTEGER NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    neurons INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS spend_events (
                    event_id TEXT PRIMARY KEY,
                    recorded_at TEXT NOT NULL,
                    route_decision_id TEXT,
                    provider TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    bucket_id TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    cost_usd REAL NOT NULL,
                    status TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS route_decisions (
                    decision_id TEXT PRIMARY KEY,
                    decided_at TEXT NOT NULL,
                    sensitivity_class TEXT NOT NULL,
                    selected_provider TEXT,
                    selected_model TEXT,
                    selected_model_id TEXT,
                    decision TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    estimated_input_tokens INTEGER NOT NULL,
                    estimated_output_tokens INTEGER NOT NULL,
                    metadata_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS cooldowns (
                    provider TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    bucket_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    cooldown_until TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (provider, model_name, bucket_id)
                );
                CREATE TABLE IF NOT EXISTS bucket_state (
                    bucket_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    window_name TEXT NOT NULL,
                    window_start TEXT NOT NULL,
                    requests INTEGER NOT NULL DEFAULT 0,
                    input_tokens INTEGER NOT NULL DEFAULT 0,
                    output_tokens INTEGER NOT NULL DEFAULT 0,
                    neurons INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (bucket_id, window_name, window_start)
                );
                """)

    def active_cooldown(
        self,
        provider: str,
        model_name: str,
        bucket_id: str,
        now: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        current = now or now_utc()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT provider, model_name, bucket_id, reason, cooldown_until
                FROM cooldowns
                WHERE provider = ? AND model_name = ? AND bucket_id = ?
                """,
                (provider, model_name, bucket_id),
            ).fetchone()
        if not row:
            return None
        cooldown_until = parse_iso_datetime(row["cooldown_until"])
        if cooldown_until and cooldown_until > current:
            return dict(row)
        return None

    def set_cooldown(
        self,
        provider: str,
        model_name: str,
        bucket_id: str,
        reason: str,
        cooldown_until: datetime,
        now: Optional[datetime] = None,
    ) -> None:
        current = now or now_utc()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO cooldowns (
                    provider, model_name, bucket_id, reason, cooldown_until, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider, model_name, bucket_id)
                DO UPDATE SET
                    reason = excluded.reason,
                    cooldown_until = excluded.cooldown_until,
                    created_at = excluded.created_at
                """,
                (
                    provider,
                    model_name,
                    bucket_id,
                    reason,
                    isoformat_utc(cooldown_until),
                    isoformat_utc(current),
                ),
            )

    def _bucket_usage(
        self, bucket_id: str, window: str, start: datetime
    ) -> Dict[str, int]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT requests, input_tokens, output_tokens, neurons
                FROM bucket_state
                WHERE bucket_id = ? AND window_name = ? AND window_start = ?
                """,
                (bucket_id, window, isoformat_utc(start)),
            ).fetchone()
        if row is None:
            return {"requests": 0, "input_tokens": 0, "output_tokens": 0, "neurons": 0}
        return {key: int(row[key] or 0) for key in row.keys()}

    def _spend_total(
        self,
        *,
        window: str,
        start: datetime,
        now: datetime,
    ) -> float:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(cost_usd), 0.0) AS cost_usd
                FROM spend_events
                WHERE recorded_at >= ?
                  AND recorded_at <= ?
                  AND status != 'voided'
                """,
                (isoformat_utc(start), isoformat_utc(now)),
            ).fetchone()
        return round(float(row["cost_usd"] or 0.0), 8)

    def check_quota(
        self,
        provider: str,
        model_name: str,
        bucket_id: str,
        limits: Dict[str, Any],
        input_tokens: int,
        output_tokens: int,
        neurons: int = 0,
        now: Optional[datetime] = None,
    ) -> QuotaCheck:
        current = now or now_utc()
        cooldown = self.active_cooldown(provider, model_name, bucket_id, current)
        if cooldown:
            return QuotaCheck(
                False, f"cooldown:{cooldown['reason']}", cooldown["cooldown_until"]
            )

        checks = (
            ("minute", "rpm", "requests", 1),
            ("minute", "tpm", "tokens", input_tokens + output_tokens),
            ("day", "rpd", "requests", 1),
            ("day", "tpd", "tokens", input_tokens + output_tokens),
            ("day", "neurons_per_day", "neurons", neurons),
            ("month", "requests_per_month", "requests", 1),
        )
        day_reset = str(limits.get("day_reset") or "")
        for window, limit_key, metric, increment in checks:
            limit = limits.get(limit_key)
            if limit is None or int(limit or 0) <= 0:
                continue
            start = _window_start(window, current, day_reset)
            usage = self._bucket_usage(bucket_id, window, start)
            if metric == "tokens":
                used = usage["input_tokens"] + usage["output_tokens"]
            else:
                used = usage[metric]
            if used + max(0, int(increment or 0)) > int(limit):
                reset_at = isoformat_utc(_window_end(window, current, day_reset))
                return QuotaCheck(False, f"{limit_key}_exhausted", reset_at)
        return QuotaCheck(True, "within_quota")

    def check_paid_cap(
        self,
        cap_policy: Dict[str, Any],
        pricing: Dict[str, Any],
        input_tokens: int,
        output_tokens: int,
        now: Optional[datetime] = None,
    ) -> QuotaCheck:
        current = now or now_utc()
        if not bool(cap_policy.get("enabled")):
            return QuotaCheck(False, "paid_cap_disabled")
        if not pricing:
            return QuotaCheck(False, "paid_pricing_missing")
        estimated_cost = estimate_cost_usd(pricing, input_tokens, output_tokens)
        if estimated_cost <= 0:
            return QuotaCheck(False, "paid_pricing_zero")

        day_reset = str(cap_policy.get("day_reset") or "utc_midnight")
        checks = (
            ("day", "daily_usd", "daily_paid_cap_exhausted"),
            ("month", "monthly_usd", "monthly_paid_cap_exhausted"),
        )
        any_positive_cap = False
        for window, cap_key, reason in checks:
            cap = float(cap_policy.get(cap_key) or 0.0)
            if cap <= 0:
                continue
            any_positive_cap = True
            start = _window_start(window, current, day_reset)
            used = self._spend_total(window=window, start=start, now=current)
            if used + estimated_cost > cap:
                reset_at = isoformat_utc(_window_end(window, current, day_reset))
                return QuotaCheck(False, reason, reset_at)
        if not any_positive_cap:
            return QuotaCheck(False, "paid_cap_limit_missing")
        return QuotaCheck(True, "within_paid_cap")

    def record_route_decision(
        self, decision: Dict[str, Any], now: Optional[datetime] = None
    ) -> str:
        current = now or now_utc()
        decision_id = str(decision.get("decision_id") or uuid.uuid4().hex)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO route_decisions (
                    decision_id, decided_at, sensitivity_class, selected_provider,
                    selected_model, selected_model_id, decision, reason,
                    estimated_input_tokens, estimated_output_tokens, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision_id,
                    isoformat_utc(current),
                    str(decision.get("sensitivity_class") or NON_SENSITIVE_CLASS),
                    decision.get("provider"),
                    decision.get("model_name"),
                    decision.get("model_id"),
                    str(decision.get("decision") or "unknown"),
                    str(decision.get("reason") or "unknown"),
                    int(decision.get("estimated_input_tokens") or 0),
                    int(decision.get("estimated_output_tokens") or 0),
                    _safe_json(decision.get("metadata")),
                ),
            )
        return decision_id

    def record_usage(
        self,
        provider: str,
        model_name: str,
        model_id: str,
        bucket_id: str,
        input_tokens: int,
        output_tokens: int,
        *,
        route_decision_id: str | None = None,
        status: str = "completed",
        neurons: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        now: Optional[datetime] = None,
    ) -> str:
        current = now or now_utc()
        event_id = uuid.uuid4().hex
        windows = ("minute", "day", "month")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO usage_events (
                    event_id, recorded_at, route_decision_id, provider, model_name,
                    model_id, bucket_id, requests, input_tokens, output_tokens,
                    neurons, status, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    isoformat_utc(current),
                    route_decision_id,
                    provider,
                    model_name,
                    model_id,
                    bucket_id,
                    max(0, int(input_tokens or 0)),
                    max(0, int(output_tokens or 0)),
                    max(0, int(neurons or 0)),
                    status,
                    _safe_json(metadata),
                ),
            )
            day_reset = str(
                (PROVIDER_CATALOG.get(provider, {}).get("limits") or {}).get(
                    "day_reset"
                )
                or ""
            )
            for window in windows:
                start = _window_start(
                    window,
                    current,
                    day_reset if window == "day" else None,
                )
                conn.execute(
                    """
                    INSERT INTO bucket_state (
                        bucket_id, provider, model_name, window_name, window_start,
                        requests, input_tokens, output_tokens, neurons, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
                    ON CONFLICT(bucket_id, window_name, window_start)
                    DO UPDATE SET
                        requests = bucket_state.requests + excluded.requests,
                        input_tokens = bucket_state.input_tokens + excluded.input_tokens,
                        output_tokens = bucket_state.output_tokens + excluded.output_tokens,
                        neurons = bucket_state.neurons + excluded.neurons,
                        updated_at = excluded.updated_at
                    """,
                    (
                        bucket_id,
                        provider,
                        model_name,
                        window,
                        isoformat_utc(start),
                        max(0, int(input_tokens or 0)),
                        max(0, int(output_tokens or 0)),
                        max(0, int(neurons or 0)),
                        isoformat_utc(current),
                    ),
                )
        return event_id

    def record_spend(
        self,
        provider: str,
        model_name: str,
        model_id: str,
        bucket_id: str,
        pricing: Dict[str, Any],
        input_tokens: int,
        output_tokens: int,
        *,
        route_decision_id: str | None = None,
        status: str = "reserved",
        metadata: Optional[Dict[str, Any]] = None,
        now: Optional[datetime] = None,
    ) -> str:
        current = now or now_utc()
        event_id = uuid.uuid4().hex
        cost_usd = estimate_cost_usd(pricing, input_tokens, output_tokens)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO spend_events (
                    event_id, recorded_at, route_decision_id, provider, model_name,
                    model_id, bucket_id, input_tokens, output_tokens, cost_usd,
                    status, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    isoformat_utc(current),
                    route_decision_id,
                    provider,
                    model_name,
                    model_id,
                    bucket_id,
                    max(0, int(input_tokens or 0)),
                    max(0, int(output_tokens or 0)),
                    cost_usd,
                    status,
                    _safe_json(metadata),
                ),
            )
        return event_id

    def ingest_response_headers(
        self,
        provider: str,
        model_name: str,
        bucket_id: str,
        headers: Dict[str, Any],
        *,
        status_code: int,
        now: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        current = now or now_utc()
        normalized = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
        retry_after = _parse_reset_seconds(normalized.get("retry-after"))
        reset_requests = _parse_reset_seconds(
            normalized.get("x-ratelimit-reset-requests")
        )
        reset_tokens = _parse_reset_seconds(normalized.get("x-ratelimit-reset-tokens"))
        reason = None
        seconds = None

        if status_code in {402, 429}:
            reason = "insufficient_credits" if status_code == 402 else "rate_limited"
            seconds = retry_after or reset_requests or reset_tokens or 60.0
        elif normalized.get("x-ratelimit-remaining-requests") == "0":
            reason = "requests_remaining_zero"
            seconds = reset_requests or 60.0
        elif normalized.get("x-ratelimit-remaining-tokens") == "0":
            reason = "tokens_remaining_zero"
            seconds = reset_tokens or 60.0

        if reason is None or seconds is None:
            return None
        cooldown_until = current + timedelta(seconds=max(1, int(seconds)))
        self.set_cooldown(
            provider, model_name, bucket_id, reason, cooldown_until, current
        )
        return {
            "provider": provider,
            "model_name": model_name,
            "bucket_id": bucket_id,
            "reason": reason,
            "cooldown_until": isoformat_utc(cooldown_until),
        }

    def quota_summary(self, now: Optional[datetime] = None) -> Dict[str, Any]:
        current = now or now_utc()
        active_starts = {
            "minute": isoformat_utc(_window_start("minute", current)),
            "day": isoformat_utc(_window_start("day", current)),
            "month": isoformat_utc(_window_start("month", current)),
        }
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT bucket_id, provider, model_name, window_name, window_start,
                       requests, input_tokens, output_tokens, neurons, updated_at
                FROM bucket_state
                ORDER BY bucket_id, window_name, window_start
                """).fetchall()
            cooldown_rows = conn.execute("""
                SELECT provider, model_name, bucket_id, reason, cooldown_until
                FROM cooldowns
                ORDER BY provider, model_name, bucket_id
                """).fetchall()
            spend_rows = conn.execute("""
                SELECT event_id, recorded_at, route_decision_id, provider,
                       model_name, model_id, bucket_id, input_tokens,
                       output_tokens, cost_usd, status
                FROM spend_events
                ORDER BY recorded_at, event_id
                """).fetchall()
        spend_summary = {}
        for window in ("day", "month"):
            start = _window_start(window, current)
            spend_summary[window] = {
                "window_start": isoformat_utc(start),
                "cost_usd": self._spend_total(
                    window=window, start=start, now=current
                ),
            }
        return {
            "ledger_path": str(self.path),
            "generated_at": isoformat_utc(current),
            "active_window_starts": active_starts,
            "buckets": [dict(row) for row in rows],
            "cooldowns": [dict(row) for row in cooldown_rows],
            "spend": {
                "summary": spend_summary,
                "events": [dict(row) for row in spend_rows],
            },
        }


class FreeflowRouter:
    """Policy router that selects only local or strict-free hosted routes."""

    def __init__(
        self,
        config: Dict[str, Any],
        ledger: Optional[FreeflowQuotaLedger] = None,
    ) -> None:
        self.config = config
        self.policy = freeflow_policy(config)
        self.ledger = ledger

    def _providers(self) -> Dict[str, Dict[str, Any]]:
        return {
            str(provider.get("name")): provider
            for provider in self.config.get("providers", [])
            if provider.get("name")
        }

    def routes(self) -> list[Dict[str, Any]]:
        providers = self._providers()
        rows: list[Dict[str, Any]] = []
        disabled = set(self.policy.get("disabled_models") or [])
        paid_policy = paid_cap_policy(self.config)
        paid_allowed_names = set(paid_policy.get("allowed_models") or [])
        paid_allowed_names.update(paid_policy.get("allow") or [])
        paid_cap_active = bool(paid_policy.get("enabled"))
        for model in self.config.get("models", []):
            model_name = str(model.get("name") or "")
            provider_name = str(model.get("provider") or "")
            provider = providers.get(provider_name, {})
            model_id = str(model.get("model_id") or model.get("litellm_model") or "")
            classification = classify_route(provider_name, model_id)
            catalog_key = _provider_catalog_key(provider_name, model_id)
            catalog = PROVIDER_CATALOG.get(catalog_key, {})
            local = bool(classification.get("local"))
            paid_provider = catalog_key in PAID_CAP_PROVIDERS
            pricing = _catalog_pricing(catalog_key, model_id)
            paid_cap_allowed = (
                paid_cap_active
                and paid_provider
                and model_name in paid_allowed_names
                and bool(pricing)
            )
            paid_cap_blocked_reason = None
            if paid_provider and not paid_cap_allowed:
                if not paid_cap_active:
                    paid_cap_blocked_reason = "paid_cap_disabled"
                elif model_name not in paid_allowed_names:
                    paid_cap_blocked_reason = "paid_cap_model_not_allowlisted"
                elif not pricing:
                    paid_cap_blocked_reason = "paid_pricing_missing"
            auth_mode = str(
                provider.get("auth_mode") or catalog.get("auth_mode") or "env"
            ).lower()
            api_key_env = provider.get("api_key_env")
            credential_present = (
                True
                if auth_mode in {"none", "ignored"}
                else bool(api_key_env and os.getenv(str(api_key_env)))
            )
            blocked_reason = (
                None
                if classification["allowed"] or paid_cap_allowed or paid_provider
                else classification["reason"]
            )
            enabled = model_name not in disabled and bool(model.get("enabled", True))
            rows.append(
                {
                    "name": model_name,
                    "provider": provider_name,
                    "effective_provider": catalog_key,
                    "model_id": model_id,
                    "bucket_id": f"{catalog_key}:{model_name}",
                    "local": local,
                    "zero_cost": bool(catalog.get("zero_cost", False)) or local,
                    "strict_free_allowed": bool(classification["allowed"]),
                    "paid": paid_provider,
                    "paid_cap_allowed": paid_cap_allowed,
                    "paid_cap_blocked_reason": paid_cap_blocked_reason,
                    "pricing": pricing,
                    "blocked_reason": blocked_reason,
                    "enabled": enabled,
                    "credential_present": credential_present,
                    "api_key_env": api_key_env,
                    "auth_mode": auth_mode,
                    "sensitivity_allowed": (
                        ["sensitive", NON_SENSITIVE_CLASS]
                        if local
                        else [NON_SENSITIVE_CLASS]
                    ),
                    "limits": dict(catalog.get("limits") or {}),
                    "source_url": catalog.get("source_url"),
                    "last_verified": catalog.get("last_verified"),
                    "score": int(catalog.get("score") or (100 if local else 0)),
                }
            )
        return rows

    def choose_route(
        self,
        *,
        sensitivity_class: str | None = None,
        estimated_input_tokens: int = 0,
        estimated_output_tokens: int = 0,
        now: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        sensitivity = normalize_sensitivity(
            sensitivity_class
            or self.policy.get("default_sensitivity")
            or NON_SENSITIVE_CLASS
        )
        current = now or now_utc()

        def route_sort_key(row: Dict[str, Any]) -> tuple[int, str, str]:
            score = int(row["score"])
            if sensitivity == NON_SENSITIVE_CLASS and row["local"]:
                score = 55
            if sensitivity == "sensitive" and row["local"]:
                score = 1000
            return (-score, str(row["provider"]), str(row["name"]))

        candidates = sorted(
            self.routes(),
            key=route_sort_key,
        )
        rejected: list[Dict[str, str]] = []
        for route in candidates:
            if not route["enabled"]:
                rejected.append({"name": route["name"], "reason": "disabled"})
                continue
            if not route["strict_free_allowed"] and not route["paid_cap_allowed"]:
                rejected.append(
                    {
                        "name": route["name"],
                        "reason": str(
                            route["blocked_reason"]
                            or route["paid_cap_blocked_reason"]
                        ),
                    }
                )
                continue
            if sensitivity not in route["sensitivity_allowed"]:
                rejected.append({"name": route["name"], "reason": "sensitivity_policy"})
                continue
            if not route["credential_present"]:
                rejected.append({"name": route["name"], "reason": "missing_credential"})
                continue
            ledger = self.ledger or FreeflowQuotaLedger()
            quota = ledger.check_quota(
                route["effective_provider"],
                route["name"],
                route["bucket_id"],
                route["limits"],
                estimated_input_tokens,
                estimated_output_tokens,
                now=current,
            )
            if not quota.allowed:
                rejected.append({"name": route["name"], "reason": quota.reason})
                continue
            estimated_cost = 0.0
            reason = "strict_free_route_selected"
            if route["paid_cap_allowed"]:
                paid_quota = ledger.check_paid_cap(
                    paid_cap_policy(self.config),
                    route["pricing"],
                    estimated_input_tokens,
                    estimated_output_tokens,
                    now=current,
                )
                if not paid_quota.allowed:
                    rejected.append(
                        {"name": route["name"], "reason": paid_quota.reason}
                    )
                    continue
                estimated_cost = estimate_cost_usd(
                    route["pricing"],
                    estimated_input_tokens,
                    estimated_output_tokens,
                )
                reason = "paid_cap_route_selected"
            decision = {
                "decision_id": uuid.uuid4().hex,
                "decision": "selected",
                "reason": reason,
                "sensitivity_class": sensitivity,
                "provider": route["effective_provider"],
                "model_name": route["name"],
                "model_id": route["model_id"],
                "bucket_id": route["bucket_id"],
                "estimated_input_tokens": int(estimated_input_tokens or 0),
                "estimated_output_tokens": int(estimated_output_tokens or 0),
                "metadata": {
                    "rejected": rejected,
                    "paid": route["paid_cap_allowed"],
                    "estimated_cost_usd": estimated_cost,
                },
            }
            ledger.record_route_decision(decision, current)
            return decision

        local_configured = any(
            route["local"] and route["strict_free_allowed"] and route["enabled"]
            for route in candidates
        )
        reason = (
            "blocked_local_unavailable"
            if sensitivity == "sensitive" and not local_configured
            else "queued_no_free_capacity"
        )
        decision = {
            "decision_id": uuid.uuid4().hex,
            "decision": (
                "queued" if reason != "blocked_local_unavailable" else "blocked"
            ),
            "reason": reason,
            "sensitivity_class": sensitivity,
            "provider": None,
            "model_name": None,
            "model_id": None,
            "estimated_input_tokens": int(estimated_input_tokens or 0),
            "estimated_output_tokens": int(estimated_output_tokens or 0),
            "metadata": {"rejected": rejected},
        }
        ledger = self.ledger or FreeflowQuotaLedger()
        ledger.record_route_decision(decision, current)
        return decision


def validate_freeflow_config(config: Dict[str, Any]) -> None:
    policy = freeflow_policy(config)
    if not policy.get("enabled"):
        return
    if policy.get("mode") != STRICT_FREE_MODE:
        raise ValueError(f"Unsupported freeflow mode: {policy.get('mode')}")
    model_names = {str(model.get("name")) for model in config.get("models", [])}
    slots = policy.get("slots") or {}
    if not isinstance(slots, dict):
        raise ValueError("freeflow.slots must be a dictionary")
    for slot_name, model_name in slots.items():
        if model_name not in model_names:
            raise ValueError(
                f"freeflow slot {slot_name} references unknown model: {model_name}"
            )
    for model_name in policy.get("default_fallbacks") or []:
        if model_name not in model_names:
            raise ValueError(
                f"freeflow default fallback references unknown model: {model_name}"
            )
    paid_policy = paid_cap_policy(config)
    for cap_key in ("daily_usd", "monthly_usd"):
        try:
            cap_value = float(paid_policy.get(cap_key) or 0.0)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"freeflow.paid_cap.{cap_key} must be numeric") from exc
        if cap_value < 0:
            raise ValueError(f"freeflow.paid_cap.{cap_key} must be non-negative")
    for model_name in paid_policy.get("allowed_models") or []:
        if model_name not in model_names:
            raise ValueError(
                f"freeflow paid_cap allowed model references unknown model: {model_name}"
            )
    for model_name in paid_policy.get("default_fallbacks") or []:
        if model_name not in model_names:
            raise ValueError(
                f"freeflow paid_cap fallback references unknown model: {model_name}"
            )


def generate_freeflow_litellm_config(
    config: Dict[str, Any], master_key: str
) -> Dict[str, Any]:
    router = FreeflowRouter(config)
    routes = [
        route
        for route in router.routes()
        if (route["strict_free_allowed"] or route["paid_cap_allowed"])
        and route["enabled"]
    ]
    allowed_names = {route["name"] for route in routes}
    providers = router._providers()
    model_list: list[Dict[str, Any]] = []
    for route in routes:
        provider = providers[route["provider"]]
        litellm_params: Dict[str, Any] = {
            "model": route["model_id"],
            "max_tokens": next(
                (
                    int(model.get("max_tokens", 131072))
                    for model in config.get("models", [])
                    if model.get("name") == route["name"]
                ),
                131072,
            ),
        }
        if route["auth_mode"] in {"none", "ignored"}:
            litellm_params["api_key"] = str(provider.get("api_key") or "local")
        else:
            litellm_params["api_key"] = f"os.environ/{provider['api_key_env']}"
        if provider.get("base_url"):
            litellm_params["api_base"] = provider["base_url"]
        if provider.get("extra_headers"):
            litellm_params["extra_headers"] = provider["extra_headers"]
        model_info = {
            "freeflow_provider": route["effective_provider"],
            "freeflow_model": route["name"],
            "freeflow_bucket_id": route["bucket_id"],
            "quota_bucket": route["bucket_id"],
            "freeflow_limits": route["limits"],
            "sensitivity_class": NON_SENSITIVE_CLASS,
            "selected_fallback_tier": "generated",
            "route_reason": (
                "paid_cap_generated_config"
                if route["paid_cap_allowed"]
                else "strict_free_generated_config"
            ),
            "zero_cost": route["zero_cost"],
            "freeflow_paid": route["paid_cap_allowed"],
            "source_url": route["source_url"],
            "last_verified": route["last_verified"],
        }
        if route["paid_cap_allowed"]:
            paid_policy = paid_cap_policy(config)
            model_info["freeflow_pricing"] = route["pricing"]
            model_info["freeflow_paid_cap"] = {
                "enabled": bool(paid_policy.get("enabled")),
                "daily_usd": float(paid_policy.get("daily_usd") or 0.0),
                "monthly_usd": float(paid_policy.get("monthly_usd") or 0.0),
                "day_reset": paid_policy.get("day_reset") or "utc_midnight",
            }
            model_info["estimated_cost_source_url"] = route["source_url"]
        model_list.append(
            {
                "model_name": route["name"],
                "litellm_params": litellm_params,
                "model_info": model_info,
            }
        )

    policy = freeflow_policy(config)
    freeflow_slots = dict(policy.get("slots") or {})
    fallback_default = next(iter(allowed_names), None)
    default_model = (
        freeflow_slots.get("default")
        if freeflow_slots.get("default") in allowed_names
        else fallback_default
    )

    def resolve_slot(slot_or_model: str) -> str | None:
        if (
            slot_or_model in freeflow_slots
            and freeflow_slots[slot_or_model] in allowed_names
        ):
            return freeflow_slots[slot_or_model]
        if slot_or_model in allowed_names:
            return slot_or_model
        return default_model

    model_alias_map: Dict[str, str] = {}
    for alias, slot_name in (config.get("aliases") or {}).items():
        resolved = resolve_slot(str(slot_name))
        if resolved:
            model_alias_map[str(alias)] = resolved
    for slot_name, model_name in freeflow_slots.items():
        if model_name in allowed_names:
            model_alias_map[str(slot_name)] = str(model_name)

    fallback_dict: Dict[str, list[str]] = {}
    for model_name, fallback_list in (config.get("fallbacks") or {}).items():
        if model_name not in allowed_names:
            continue
        filtered = [
            candidate for candidate in fallback_list if candidate in allowed_names
        ]
        if filtered:
            fallback_dict[model_name] = filtered

    paid_policy = paid_cap_policy(config)
    combined_default_fallbacks = list(policy.get("default_fallbacks") or [])
    combined_default_fallbacks.extend(paid_policy.get("default_fallbacks") or [])
    seen_default_fallbacks: set[str] = set()
    default_fallbacks = []
    for model_name in combined_default_fallbacks:
        if model_name in allowed_names and model_name not in seen_default_fallbacks:
            default_fallbacks.append(model_name)
            seen_default_fallbacks.add(model_name)

    return {
        "model_list": model_list,
        "litellm_settings": {
            "timeout": int(policy.get("timeout_seconds") or 90),
            "max_retries": int(policy.get("max_retries") or 1),
            "drop_params": True,
            "model_alias_map": model_alias_map,
            "fallbacks": fallback_dict,
            "default_fallbacks": default_fallbacks,
        },
        "router_settings": {
            "routing_strategy": "simple-shuffle",
            "enable_pre_call_checks": True,
        },
        "general_settings": {"master_key": master_key},
    }


def build_doctor_report(
    config: Dict[str, Any],
    *,
    offline: bool = True,
    ledger: Optional[FreeflowQuotaLedger] = None,
) -> Dict[str, Any]:
    quota_ledger = ledger or FreeflowQuotaLedger()
    router = FreeflowRouter(config, quota_ledger)
    routes = router.routes()
    blocked = [
        route
        for route in routes
        if not route["strict_free_allowed"] and not route["paid_cap_allowed"]
    ]
    hosted = [
        route for route in routes if route["strict_free_allowed"] and not route["local"]
    ]
    local = [
        route for route in routes if route["strict_free_allowed"] and route["local"]
    ]
    paid = [route for route in routes if route["paid_cap_allowed"]]
    issues = []
    if strict_free_enabled(config) and not local:
        issues.append("strict_free_enabled_without_local_route")
    if any(route for route in hosted if not route["credential_present"]):
        issues.append("hosted_free_credentials_missing")
    if paid_cap_enabled(config) and not paid:
        issues.append("paid_cap_enabled_without_allowed_route")
    if any(route for route in paid if not route["credential_present"]):
        issues.append("paid_cap_credentials_missing")
    paid_policy = paid_cap_policy(config)
    return {
        "mode": freeflow_policy(config).get("mode"),
        "enabled": bool(freeflow_policy(config).get("enabled")),
        "paid_cap": {
            "enabled": bool(paid_policy.get("enabled")),
            "daily_usd": float(paid_policy.get("daily_usd") or 0.0),
            "monthly_usd": float(paid_policy.get("monthly_usd") or 0.0),
            "allowed_models": list(paid_policy.get("allowed_models") or []),
            "default_fallbacks": list(paid_policy.get("default_fallbacks") or []),
        },
        "offline": offline,
        "ledger_path": str(quota_ledger.path),
        "summary": {
            "routes_total": len(routes),
            "local_routes": len(local),
            "hosted_free_routes": len(hosted),
            "paid_cap_routes": len(paid),
            "blocked_paid_or_unknown_routes": len(blocked),
        },
        "issues": sorted(set(issues)),
        "routes": routes,
        "blocked_paid_routes": blocked,
        "quota": quota_ledger.quota_summary(),
        "provider_catalog": PROVIDER_CATALOG,
    }
