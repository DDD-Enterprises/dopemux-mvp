import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Basic estimates (aligned with prescan cost estimator)
COST_PER_1M_INPUT = 0.15   # Using cheap models baseline
COST_PER_1M_OUTPUT = 0.60

@dataclass
class PhaseSpend:
    phase: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0

@dataclass
class SpendLedgerRecord:
    run_id: str
    global_max_cost_usd: float | None = None
    phases: Dict[str, PhaseSpend] = field(default_factory=dict)
    total_cost_usd: float = 0.0

class SpendLedger:
    def __init__(self, run_dir: Path, run_id: str, max_cost_usd: float | None = None):
        self.ledger_path = run_dir / "spend_ledger.json"
        self.record = SpendLedgerRecord(
            run_id=run_id,
            global_max_cost_usd=max_cost_usd
        )
        self._load()

    def _load(self) -> None:
        if self.ledger_path.exists():
            try:
                data = json.loads(self.ledger_path.read_text(encoding="utf-8"))
                self.record.total_cost_usd = data.get("total_cost_usd", 0.0)
                for phase_name, phase_data in data.get("phases", {}).items():
                    self.record.phases[phase_name] = PhaseSpend(**phase_data)
            except Exception as e:
                logger.warning(f"Could not load existing spend ledger: {e}")

    def _save(self) -> None:
        try:
            self.ledger_path.write_text(json.dumps(asdict(self.record), indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save spend ledger: {e}")

    def accumulate(self, phase: str, input_tokens: int, output_tokens: int) -> None:
        """Add tokens to the ledger and recalculate costs."""
        cost = (input_tokens / 1_000_000 * COST_PER_1M_INPUT) + (output_tokens / 1_000_000 * COST_PER_1M_OUTPUT)
        
        if phase not in self.record.phases:
            self.record.phases[phase] = PhaseSpend(phase=phase)
            
        p = self.record.phases[phase]
        p.input_tokens += input_tokens
        p.output_tokens += output_tokens
        p.estimated_cost_usd += cost
        
        self.record.total_cost_usd += cost
        self._save()
        
    def check_limit(self) -> bool:
        """Returns True if the current total is within the max_cost_usd limit."""
        if self.record.global_max_cost_usd is None:
            return True
        return self.record.total_cost_usd <= self.record.global_max_cost_usd
