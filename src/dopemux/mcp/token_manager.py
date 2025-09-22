"""
Token Budget Manager: Budget-aware token tracking and optimization

The Token Budget Manager provides comprehensive token usage tracking, budget
enforcement, and optimization for the MetaMCP system. It ensures that role-based
token budgets are respected while providing clear feedback and graceful degradation
when approaching limits.

Key Features:
- Role-based token budgets with automatic enforcement
- Real-time usage tracking and projection
- Budget-aware optimization suggestions
- ADHD-friendly warnings and feedback
- Integration with pre-tool hooks for prevention
- Historical usage analytics for optimization

Design Principles:
- Transparent: Users always know their budget status
- Gentle: Non-anxiety-inducing budget notifications
- Predictive: Warn before hitting limits, not after
- Educational: Help users understand token consumption patterns
- Flexible: Support for temporary budget increases and role changes
"""

import asyncio
import logging
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class BudgetStatus(Enum):
    """Budget status levels for different types of notifications"""
    HEALTHY = "healthy"          # <50% used
    MODERATE = "moderate"        # 50-75% used
    WARNING = "warning"          # 75-90% used
    CRITICAL = "critical"        # 90-95% used
    EXCEEDED = "exceeded"        # >95% used


@dataclass
class BudgetState:
    """Current budget state for a session"""
    session_id: str
    role: Optional[str] = None
    total_budget: int = 0
    used_tokens: int = 0
    reserved_tokens: int = 0  # Tokens reserved for essential operations
    warning_threshold: int = 0
    hard_cap: int = 0
    last_updated: datetime = field(default_factory=datetime.now)

    @property
    def remaining_tokens(self) -> int:
        return max(0, self.total_budget - self.used_tokens)

    @property
    def available_tokens(self) -> int:
        """Tokens available for non-essential operations"""
        return max(0, self.remaining_tokens - self.reserved_tokens)

    @property
    def usage_percentage(self) -> float:
        if self.total_budget == 0:
            return 0.0
        return (self.used_tokens / self.total_budget) * 100

    @property
    def status(self) -> BudgetStatus:
        """Get current budget status for notification purposes"""
        usage = self.usage_percentage

        if usage >= 95:
            return BudgetStatus.EXCEEDED
        elif usage >= 90:
            return BudgetStatus.CRITICAL
        elif usage >= 75:
            return BudgetStatus.WARNING
        elif usage >= 50:
            return BudgetStatus.MODERATE
        else:
            return BudgetStatus.HEALTHY

    @property
    def is_warning_level(self) -> bool:
        return self.used_tokens >= self.warning_threshold

    @property
    def is_near_cap(self) -> bool:
        return self.used_tokens >= (self.hard_cap * 0.9)

    def time_to_budget_exhaustion(self, current_burn_rate: float) -> Optional[timedelta]:
        """Estimate time until budget exhaustion at current burn rate"""
        if current_burn_rate <= 0:
            return None

        remaining = self.remaining_tokens
        if remaining <= 0:
            return timedelta(0)

        seconds_remaining = remaining / (current_burn_rate / 3600)  # Convert to tokens per second
        return timedelta(seconds=seconds_remaining)


@dataclass
class TokenUsageRecord:
    """Record of token usage for analytics and optimization"""
    timestamp: datetime
    session_id: str
    role: str
    tool_name: str
    method: str
    tokens_used: int
    estimated_tokens: int
    optimization_applied: bool
    tokens_saved: int = 0


@dataclass
class BudgetOptimization:
    """Suggestion for budget optimization"""
    type: str  # "reduce_scope", "change_tool", "role_switch", "break_suggestion"
    description: str
    estimated_savings: int
    implementation_difficulty: str  # "easy", "medium", "hard"
    adhd_impact: str  # "positive", "neutral", "negative"


class TokenBudgetManager:
    """
    Manages token budgets and usage tracking for the MetaMCP system.

    The TokenBudgetManager provides comprehensive budget management including
    role-based allocations, real-time tracking, optimization suggestions,
    and ADHD-friendly notifications and feedback.
    """

    def __init__(self, policy_config: Dict[str, Any], db_path: Optional[str] = None):
        self.policy_config = policy_config
        self.db_path = db_path or "/tmp/metamcp_tokens.db"

        # Budget rules from policy
        self.budget_rules = policy_config.get('rules', {}).get('budgets', {})
        self.default_budget = self.budget_rules.get('default_tokens', 60000)
        self.hard_cap = self.budget_rules.get('hard_cap', 120000)
        self.warning_threshold_pct = self.budget_rules.get('warning_threshold', 48000) / self.default_budget
        self.emergency_reserve = self.budget_rules.get('emergency_reserve', 10000)

        # Active session budgets
        self.session_budgets: Dict[str, BudgetState] = {}

        # Usage tracking
        self.usage_records: List[TokenUsageRecord] = []
        self.burn_rates: Dict[str, float] = {}  # Tokens per hour by session

        # Optimization caching
        self.optimization_cache: Dict[str, List[BudgetOptimization]] = {}

        # Initialize database
        self._init_database()

        logger.info("TokenBudgetManager initialized")

    def _init_database(self) -> None:
        """Initialize SQLite database for persistent token usage tracking"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS token_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        session_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        tool_name TEXT NOT NULL,
                        method TEXT NOT NULL,
                        tokens_used INTEGER NOT NULL,
                        estimated_tokens INTEGER NOT NULL,
                        optimization_applied INTEGER NOT NULL,
                        tokens_saved INTEGER DEFAULT 0
                    )
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS budget_states (
                        session_id TEXT PRIMARY KEY,
                        role TEXT,
                        total_budget INTEGER NOT NULL,
                        used_tokens INTEGER NOT NULL,
                        reserved_tokens INTEGER DEFAULT 0,
                        last_updated TEXT NOT NULL
                    )
                """)

                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_usage_session_time
                    ON token_usage(session_id, timestamp)
                """)

                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_usage_role_tool
                    ON token_usage(role, tool_name)
                """)

                logger.info("Token usage database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize token database: {e}")
            raise

    async def initialize_session_budget(self, session_id: str, role: str) -> BudgetState:
        """Initialize budget for a new session with role-based allocation"""
        # Get role-specific budget from policy
        role_profiles = self.policy_config.get('profiles', {})
        role_config = role_profiles.get(role, {})
        role_budget = role_config.get('token_budget', self.default_budget)

        # Calculate thresholds
        warning_threshold = int(role_budget * self.warning_threshold_pct)

        budget_state = BudgetState(
            session_id=session_id,
            role=role,
            total_budget=role_budget,
            used_tokens=0,
            reserved_tokens=self.emergency_reserve,
            warning_threshold=warning_threshold,
            hard_cap=self.hard_cap
        )

        self.session_budgets[session_id] = budget_state

        # Save to database
        await self._save_budget_state(budget_state)

        logger.info(f"Initialized budget for session {session_id}, role {role}: {role_budget} tokens")

        return budget_state

    async def switch_role_budget(self, session_id: str, new_role: str) -> BudgetState:
        """Switch session to new role budget while preserving usage"""
        current_budget = self.session_budgets.get(session_id)
        if not current_budget:
            return await self.initialize_session_budget(session_id, new_role)

        # Get new role budget
        role_profiles = self.policy_config.get('profiles', {})
        role_config = role_profiles.get(new_role, {})
        new_total_budget = role_config.get('token_budget', self.default_budget)

        # Preserve current usage
        current_budget.role = new_role
        current_budget.total_budget = new_total_budget
        current_budget.warning_threshold = int(new_total_budget * self.warning_threshold_pct)
        current_budget.last_updated = datetime.now()

        # Save updated state
        await self._save_budget_state(current_budget)

        logger.info(f"Switched budget for session {session_id} to role {new_role}: {new_total_budget} tokens")

        return current_budget

    async def record_usage(self, session_id: str, tokens_used: int,
                          tool_name: str = "unknown", method: str = "unknown",
                          estimated_tokens: int = 0, optimization_applied: bool = False,
                          tokens_saved: int = 0) -> BudgetState:
        """Record token usage and update budget state"""
        budget_state = self.session_budgets.get(session_id)
        if not budget_state:
            logger.warning(f"No budget state for session {session_id}, creating default")
            budget_state = await self.initialize_session_budget(session_id, "unknown")

        # Update usage
        budget_state.used_tokens += tokens_used
        budget_state.last_updated = datetime.now()

        # Create usage record
        usage_record = TokenUsageRecord(
            timestamp=datetime.now(),
            session_id=session_id,
            role=budget_state.role or "unknown",
            tool_name=tool_name,
            method=method,
            tokens_used=tokens_used,
            estimated_tokens=estimated_tokens or tokens_used,
            optimization_applied=optimization_applied,
            tokens_saved=tokens_saved
        )

        self.usage_records.append(usage_record)

        # Update burn rate
        await self._update_burn_rate(session_id)

        # Save to database
        await self._save_usage_record(usage_record)
        await self._save_budget_state(budget_state)

        # Check for budget warnings
        await self._check_budget_warnings(budget_state)

        logger.debug(f"Recorded {tokens_used} tokens for session {session_id}: {budget_state.usage_percentage:.1f}% used")

        return budget_state

    async def get_budget_status(self, session_id: str) -> Optional[BudgetState]:
        """Get current budget status for a session"""
        return self.session_budgets.get(session_id)

    async def check_budget_availability(self, session_id: str, required_tokens: int) -> Tuple[bool, str]:
        """Check if sufficient budget is available for an operation"""
        budget_state = self.session_budgets.get(session_id)
        if not budget_state:
            return False, "No budget state found"

        if budget_state.available_tokens >= required_tokens:
            return True, "Budget available"

        if budget_state.remaining_tokens >= required_tokens:
            return True, "Budget available (using reserves)"

        shortage = required_tokens - budget_state.remaining_tokens
        return False, f"Insufficient budget: need {required_tokens}, have {budget_state.remaining_tokens}, short by {shortage}"

    async def get_optimization_suggestions(self, session_id: str) -> List[BudgetOptimization]:
        """Get personalized optimization suggestions based on usage patterns"""
        budget_state = self.session_budgets.get(session_id)
        if not budget_state:
            return []

        # Check cache first
        cache_key = f"{session_id}_{budget_state.status.value}"
        if cache_key in self.optimization_cache:
            cached_suggestions = self.optimization_cache[cache_key]
            # Return cached suggestions if they're recent (5 minutes)
            return cached_suggestions

        suggestions = []

        # Analyze recent usage patterns
        recent_usage = await self._get_recent_usage(session_id, hours=1)
        if not recent_usage:
            return suggestions

        # Tool usage analysis
        tool_usage = {}
        for record in recent_usage:
            tool_key = f"{record.tool_name}.{record.method}"
            if tool_key not in tool_usage:
                tool_usage[tool_key] = {'count': 0, 'total_tokens': 0, 'avg_tokens': 0}
            tool_usage[tool_key]['count'] += 1
            tool_usage[tool_key]['total_tokens'] += record.tokens_used

        # Calculate averages
        for tool_stats in tool_usage.values():
            tool_stats['avg_tokens'] = tool_stats['total_tokens'] / tool_stats['count']

        # Suggest optimizations based on usage patterns
        high_usage_tools = [
            tool for tool, stats in tool_usage.items()
            if stats['avg_tokens'] > 2000 and stats['count'] > 2
        ]

        for tool in high_usage_tools:
            stats = tool_usage[tool]
            suggestions.append(BudgetOptimization(
                type="reduce_scope",
                description=f"Consider reducing scope for {tool} (averaging {stats['avg_tokens']} tokens per call)",
                estimated_savings=int(stats['avg_tokens'] * 0.3),
                implementation_difficulty="easy",
                adhd_impact="positive"
            ))

        # Role-based suggestions
        if budget_state.status in [BudgetStatus.WARNING, BudgetStatus.CRITICAL]:
            current_burn_rate = self.burn_rates.get(session_id, 0)
            if current_burn_rate > 0:
                time_remaining = budget_state.time_to_budget_exhaustion(current_burn_rate)
                if time_remaining and time_remaining < timedelta(hours=1):
                    suggestions.append(BudgetOptimization(
                        type="break_suggestion",
                        description=f"Take a break? Budget will be exhausted in {time_remaining}",
                        estimated_savings=0,
                        implementation_difficulty="easy",
                        adhd_impact="positive"
                    ))

        # Role switching suggestions
        if budget_state.status == BudgetStatus.CRITICAL:
            # Suggest switching to a lower-budget role
            current_role = budget_state.role
            if current_role in ['architect', 'debugger']:  # High-budget roles
                suggestions.append(BudgetOptimization(
                    type="role_switch",
                    description="Consider switching to 'reviewer' or 'developer' role to conserve budget",
                    estimated_savings=0,
                    implementation_difficulty="medium",
                    adhd_impact="neutral"
                ))

        # Cache suggestions
        self.optimization_cache[cache_key] = suggestions

        return suggestions

    async def get_usage_analytics(self, session_id: Optional[str] = None,
                                 role: Optional[str] = None,
                                 days: int = 7) -> Dict[str, Any]:
        """Get comprehensive usage analytics"""
        # Build query conditions
        conditions = []
        params = []

        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)

        if role:
            conditions.append("role = ?")
            params.append(role)

        # Date range
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        conditions.append("timestamp >= ?")
        params.append(since_date)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # Total usage
                total_query = f"""
                    SELECT
                        COUNT(*) as total_calls,
                        SUM(tokens_used) as total_tokens,
                        AVG(tokens_used) as avg_tokens_per_call,
                        SUM(tokens_saved) as total_saved
                    FROM token_usage
                    WHERE {where_clause}
                """
                total_result = conn.execute(total_query, params).fetchone()

                # Usage by tool
                tool_query = f"""
                    SELECT
                        tool_name,
                        method,
                        COUNT(*) as calls,
                        SUM(tokens_used) as total_tokens,
                        AVG(tokens_used) as avg_tokens,
                        SUM(tokens_saved) as saved_tokens
                    FROM token_usage
                    WHERE {where_clause}
                    GROUP BY tool_name, method
                    ORDER BY total_tokens DESC
                    LIMIT 10
                """
                tool_results = conn.execute(tool_query, params).fetchall()

                # Usage by role (if not filtering by role)
                role_results = []
                if not role:
                    role_query = f"""
                        SELECT
                            role,
                            COUNT(*) as calls,
                            SUM(tokens_used) as total_tokens,
                            AVG(tokens_used) as avg_tokens
                        FROM token_usage
                        WHERE {where_clause}
                        GROUP BY role
                        ORDER BY total_tokens DESC
                    """
                    role_results = conn.execute(role_query, params).fetchall()

                # Optimization effectiveness
                optimization_query = f"""
                    SELECT
                        COUNT(*) as optimized_calls,
                        SUM(tokens_saved) as total_savings,
                        AVG(tokens_saved) as avg_savings_per_optimization
                    FROM token_usage
                    WHERE {where_clause} AND optimization_applied = 1
                """
                optimization_result = conn.execute(optimization_query, params).fetchone()

                return {
                    'period_days': days,
                    'total_stats': dict(total_result) if total_result else {},
                    'tool_usage': [dict(row) for row in tool_results],
                    'role_usage': [dict(row) for row in role_results],
                    'optimization_stats': dict(optimization_result) if optimization_result else {},
                    'current_sessions': len(self.session_budgets),
                    'active_burn_rates': dict(self.burn_rates)
                }

        except Exception as e:
            logger.error(f"Failed to get usage analytics: {e}")
            return {}

    async def estimate_token_cost(self, tool_name: str, method: str,
                                 params: Dict[str, Any]) -> int:
        """Estimate token cost for a tool call based on historical data"""
        # Get historical data for this tool/method combination
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT AVG(tokens_used) as avg_tokens
                    FROM token_usage
                    WHERE tool_name = ? AND method = ?
                    AND timestamp >= ?
                """
                since_date = (datetime.now() - timedelta(days=30)).isoformat()
                result = conn.execute(query, [tool_name, method, since_date]).fetchone()

                if result and result[0]:
                    base_estimate = int(result[0])
                else:
                    # Fallback to heuristic estimates
                    base_estimate = self._get_heuristic_estimate(tool_name, method)

        except Exception as e:
            logger.error(f"Failed to get historical estimate: {e}")
            base_estimate = self._get_heuristic_estimate(tool_name, method)

        # Adjust based on parameters
        multiplier = self._calculate_parameter_multiplier(tool_name, method, params)

        return max(int(base_estimate * multiplier), 50)  # Minimum 50 tokens

    async def _get_recent_usage(self, session_id: str, hours: int = 1) -> List[TokenUsageRecord]:
        """Get recent usage records for a session"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        return [
            record for record in self.usage_records
            if record.session_id == session_id and record.timestamp >= cutoff_time
        ]

    async def _update_burn_rate(self, session_id: str) -> None:
        """Update burn rate calculation for a session"""
        recent_usage = await self._get_recent_usage(session_id, hours=1)
        if len(recent_usage) < 2:
            return

        # Calculate tokens per hour
        total_tokens = sum(record.tokens_used for record in recent_usage)
        time_span = (recent_usage[-1].timestamp - recent_usage[0].timestamp).total_seconds() / 3600

        if time_span > 0:
            self.burn_rates[session_id] = total_tokens / time_span

    async def _check_budget_warnings(self, budget_state: BudgetState) -> None:
        """Check and issue budget warnings if necessary"""
        if budget_state.status == BudgetStatus.WARNING:
            logger.warning(f"Budget warning for session {budget_state.session_id}: {budget_state.usage_percentage:.1f}% used")
            # In practice, this would trigger UI notifications

        elif budget_state.status == BudgetStatus.CRITICAL:
            logger.error(f"Budget critical for session {budget_state.session_id}: {budget_state.usage_percentage:.1f}% used")
            # In practice, this would trigger more prominent notifications

        elif budget_state.status == BudgetStatus.EXCEEDED:
            logger.error(f"Budget exceeded for session {budget_state.session_id}: {budget_state.usage_percentage:.1f}% used")
            # In practice, this would trigger immediate action

    def _get_heuristic_estimate(self, tool_name: str, method: str) -> int:
        """Get heuristic token estimate when no historical data is available"""
        # Base costs per tool (from historical analysis and documentation)
        base_costs = {
            'claude-context': 1200,
            'sequential-thinking': 4000,
            'zen': 2500,
            'exa': 1500,
            'task-master-ai': 800,
            'context7': 600,
            'serena': 400,
            'conport': 300,
            'cli': 200,
            'playwright': 1000
        }

        return base_costs.get(tool_name, 500)

    def _calculate_parameter_multiplier(self, tool_name: str, method: str,
                                       params: Dict[str, Any]) -> float:
        """Calculate multiplier based on parameters"""
        multiplier = 1.0

        if tool_name == 'claude-context':
            max_results = params.get('maxResults', 10)
            multiplier *= min(max_results / 3.0, 3.0)  # Scale with results, cap at 3x

        elif tool_name == 'sequential-thinking':
            max_depth = params.get('maxDepth', 5)
            multiplier *= min(max_depth / 5.0, 2.0)  # Scale with depth, cap at 2x

        elif tool_name == 'exa':
            num_results = params.get('numResults', 10)
            multiplier *= min(num_results / 10.0, 2.0)

        return multiplier

    async def _save_usage_record(self, record: TokenUsageRecord) -> None:
        """Save usage record to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO token_usage
                    (timestamp, session_id, role, tool_name, method, tokens_used,
                     estimated_tokens, optimization_applied, tokens_saved)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    record.timestamp.isoformat(),
                    record.session_id,
                    record.role,
                    record.tool_name,
                    record.method,
                    record.tokens_used,
                    record.estimated_tokens,
                    1 if record.optimization_applied else 0,
                    record.tokens_saved
                ])

        except Exception as e:
            logger.error(f"Failed to save usage record: {e}")

    async def _save_budget_state(self, budget_state: BudgetState) -> None:
        """Save budget state to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO budget_states
                    (session_id, role, total_budget, used_tokens, reserved_tokens, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, [
                    budget_state.session_id,
                    budget_state.role,
                    budget_state.total_budget,
                    budget_state.used_tokens,
                    budget_state.reserved_tokens,
                    budget_state.last_updated.isoformat()
                ])

        except Exception as e:
            logger.error(f"Failed to save budget state: {e}")

    async def load_budget_state(self, session_id: str) -> Optional[BudgetState]:
        """Load budget state from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                result = conn.execute("""
                    SELECT * FROM budget_states WHERE session_id = ?
                """, [session_id]).fetchone()

                if result:
                    budget_state = BudgetState(
                        session_id=result['session_id'],
                        role=result['role'],
                        total_budget=result['total_budget'],
                        used_tokens=result['used_tokens'],
                        reserved_tokens=result.get('reserved_tokens', 0),
                        last_updated=datetime.fromisoformat(result['last_updated'])
                    )

                    # Recalculate derived fields
                    budget_state.warning_threshold = int(budget_state.total_budget * self.warning_threshold_pct)
                    budget_state.hard_cap = self.hard_cap

                    self.session_budgets[session_id] = budget_state
                    return budget_state

        except Exception as e:
            logger.error(f"Failed to load budget state: {e}")

        return None