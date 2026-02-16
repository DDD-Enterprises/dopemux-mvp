import time
from dataclasses import dataclass
from typing import Dict, Optional

try:
    from lib.retry import parse_reset_seconds, safe_int
except ImportError:
    from UPGRADES.lib.retry import parse_reset_seconds, safe_int


@dataclass
class ProviderRateConfig:
    rpm: int
    tpm: int
    min_delay_ms: int = 0
    max_inflight: int = 1


@dataclass
class ProviderLimiter:
    config: ProviderRateConfig
    next_request_at: float = 0.0
    token_window_start: float = 0.0
    tokens_used_window: int = 0
    request_pause_until: float = 0.0
    token_pause_until: float = 0.0
    adaptive_min_delay_ms: int = 0
    adaptive_inflight: int = 1

    def __post_init__(self) -> None:
        self.adaptive_min_delay_ms = max(self.config.min_delay_ms, 0)
        self.adaptive_inflight = max(self.config.max_inflight, 1)

    def _reset_token_window_if_needed(self, now_ts: float) -> None:
        if self.token_window_start <= 0:
            self.token_window_start = now_ts
            self.tokens_used_window = 0
            return
        if now_ts - self.token_window_start >= 60.0:
            self.token_window_start = now_ts
            self.tokens_used_window = 0

    def acquire(self, est_tokens: int) -> float:
        sleeps = []
        now_ts = time.time()
        self._reset_token_window_if_needed(now_ts)

        if self.request_pause_until > now_ts:
            sleeps.append(self.request_pause_until - now_ts)
        if self.token_pause_until > now_ts:
            sleeps.append(self.token_pause_until - now_ts)
        if self.next_request_at > now_ts:
            sleeps.append(self.next_request_at - now_ts)
        if self.adaptive_min_delay_ms > 0:
            min_delay_s = self.adaptive_min_delay_ms / 1000.0
            if self.next_request_at > 0:
                sleeps.append(max((self.next_request_at + min_delay_s) - now_ts, 0.0))

        if self.config.tpm > 0 and est_tokens > 0:
            if self.tokens_used_window + est_tokens > self.config.tpm:
                sleeps.append(max((self.token_window_start + 60.0) - now_ts, 0.0))

        sleep_for = max(sleeps) if sleeps else 0.0
        if sleep_for > 0:
            time.sleep(sleep_for)
            now_ts = time.time()
            self._reset_token_window_if_needed(now_ts)

        if self.config.rpm > 0:
            min_interval = 60.0 / float(self.config.rpm)
            self.next_request_at = max(now_ts, self.next_request_at) + min_interval
        else:
            self.next_request_at = now_ts

        if self.config.tpm > 0:
            self.tokens_used_window += max(est_tokens, 0)
        return sleep_for

    def apply_server_feedback(self, provider: str, headers: Dict[str, str]) -> None:
        if provider != "openai":
            return
        remaining_req = safe_int(headers.get("x-ratelimit-remaining-requests"))
        remaining_tok = safe_int(headers.get("x-ratelimit-remaining-tokens"))
        reset_req = parse_reset_seconds(headers.get("x-ratelimit-reset-requests", ""))
        reset_tok = parse_reset_seconds(headers.get("x-ratelimit-reset-tokens", ""))
        now_ts = time.time()

        if remaining_req is not None and remaining_req <= 0 and reset_req is not None:
            self.request_pause_until = max(self.request_pause_until, now_ts + reset_req)
        if remaining_tok is not None and remaining_tok <= 0 and reset_tok is not None:
            self.token_pause_until = max(self.token_pause_until, now_ts + reset_tok)

    def adapt_on_429(self) -> None:
        self.adaptive_min_delay_ms = max(self.adaptive_min_delay_ms * 2, 250)
        self.adaptive_inflight = max(self.adaptive_inflight - 1, 1)

    def export_state(self) -> Dict[str, Optional[int]]:
        return {
            "adaptive_min_delay_ms": self.adaptive_min_delay_ms,
            "adaptive_inflight": self.adaptive_inflight,
        }
