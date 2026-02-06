"""
Dopemux Profile Manager - Detection Engine

Auto-detects optimal profile based on context signals with ADHD-friendly scoring.
Implements weighted scoring algorithm from design spec.
"""

from typing import Optional, List, Dict, Tuple, Any

import logging

logger = logging.getLogger(__name__)

from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import fnmatch
import subprocess
import os
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from .profile_models import Profile
from .profile_parser import ProfileParser


@dataclass
class DetectionContext:
    """Context information for profile detection"""

    current_dir: Path
    git_branch: Optional[str] = None
    recent_files: List[str] = None
    energy_level: Optional[str] = None
    attention_mode: Optional[str] = None
    current_time: Optional[datetime] = None

    def __post_init__(self):
        if self.recent_files is None:
            self.recent_files = []
        if self.current_time is None:
            self.current_time = datetime.now()


@dataclass
class ProfileMatch:
    """Result of profile detection with scoring breakdown"""

    profile_name: str
    confidence: float  # 0.0 to 1.0
    total_score: float  # 0 to 100
    signal_scores: Dict[str, float]  # Breakdown by signal
    suggestion_level: str  # 'auto', 'prompt', 'none'

    def should_suggest(self) -> bool:
        """Check if confidence is high enough to suggest"""
        return self.confidence >= 0.65


class ProfileDetector:
    """Auto-detection engine for profile selection"""

    # Scoring weights (total: 100 points)
    WEIGHT_GIT_BRANCH = 30
    WEIGHT_DIRECTORY = 25
    WEIGHT_ADHD_STATE = 20
    WEIGHT_TIME_WINDOW = 15
    WEIGHT_FILE_PATTERNS = 10

    # Confidence thresholds
    THRESHOLD_AUTO = 0.85      # Auto-suggest in statusline
    THRESHOLD_PROMPT = 0.65    # Prompt user with explanation

    def __init__(self, profile_dir: Optional[Path] = None):
        """
        Initialize detector with profile directory.

        Args:
            profile_dir: Directory containing profile YAML files
        """
        from .profile_manager import ProfileManager

        # Get profiles directory
        profiles_directory = profile_dir or ProfileManager().profiles_dir

        # Parse all profiles
        self.parser = ProfileParser(validate_mcps=False)
        self.profiles = self.parser.parse_directory(profiles_directory, pattern="*.yaml")

    def detect(self, context: Optional[DetectionContext] = None) -> ProfileMatch:
        """
        Detect best matching profile for current context.

        Args:
            context: Detection context (auto-detected if None)

        Returns:
            ProfileMatch with confidence and scoring breakdown
        """
        if context is None:
            context = self._gather_context()

        scores: Dict[str, Dict[str, float]] = {}

        for profile in self.profiles.profiles:
            signal_scores = {}

            # Signal 1: Git Branch (30 points)
            if context.git_branch and profile.auto_detection:
                signal_scores['git_branch'] = self._score_git_branch(
                    profile.auto_detection.git_branches,
                    context.git_branch
                )
            else:
                signal_scores['git_branch'] = 0.0

            # Signal 2: Directory Context (25 points)
            if profile.auto_detection:
                signal_scores['directory'] = self._score_directory(
                    profile.auto_detection.directories,
                    context.current_dir
                )
            else:
                signal_scores['directory'] = 0.0

            # Signal 3: ADHD State (20 points) - OPTIONAL
            if context.energy_level and profile.adhd_config:
                signal_scores['adhd_state'] = self._score_adhd_state(
                    profile.adhd_config.energy_preference,
                    profile.adhd_config.attention_mode,
                    context.energy_level,
                    context.attention_mode
                )
            else:
                signal_scores['adhd_state'] = 0.0

            # Signal 4: Time of Day (15 points)
            if profile.auto_detection:
                signal_scores['time_window'] = self._score_time_window(
                    profile.auto_detection.time_windows,
                    context.current_time
                )
            else:
                signal_scores['time_window'] = 0.0

            # Signal 5: Recent Files (10 points)
            if profile.auto_detection and context.recent_files:
                signal_scores['file_patterns'] = self._score_file_patterns(
                    profile.auto_detection.file_patterns,
                    context.recent_files
                )
            else:
                signal_scores['file_patterns'] = 0.0

            total = sum(signal_scores.values())
            scores[profile.name] = {
                'total': total,
                'signals': signal_scores
            }

        # Find best match
        best_name = max(scores, key=lambda k: scores[k]['total'])
        best_score = scores[best_name]['total']
        confidence = best_score / 100.0

        # Determine suggestion level
        if confidence >= self.THRESHOLD_AUTO:
            suggestion_level = 'auto'
        elif confidence >= self.THRESHOLD_PROMPT:
            suggestion_level = 'prompt'
        else:
            suggestion_level = 'none'

        return ProfileMatch(
            profile_name=best_name,
            confidence=confidence,
            total_score=best_score,
            signal_scores=scores[best_name]['signals'],
            suggestion_level=suggestion_level
        )

    def _score_git_branch(self, patterns: List[str], current_branch: str) -> float:
        """Score git branch match (0-30 points)"""
        if not patterns:
            return 0.0

        for pattern in patterns:
            if fnmatch.fnmatch(current_branch, pattern):
                return self.WEIGHT_GIT_BRANCH

        return 0.0

    def _score_directory(self, patterns: List[str], current_dir: Path) -> float:
        """Score directory match (0-25 points)"""
        if not patterns:
            return 0.0

        current_str = str(current_dir)

        for pattern in patterns:
            # Check if current directory contains the pattern
            if pattern in current_str:
                return self.WEIGHT_DIRECTORY

            # Check if any parent directory matches
            for parent in current_dir.parents:
                if pattern.rstrip('/') == parent.name:
                    return self.WEIGHT_DIRECTORY

        return 0.0

    def _score_adhd_state(
        self,
        pref_energy: str,
        pref_attention: str,
        current_energy: Optional[str],
        current_attention: Optional[str]
    ) -> float:
        """Score ADHD state match (0-20 points)"""
        score = 0.0

        # Energy level matching (12 points)
        if current_energy:
            if pref_energy == 'any':
                score += 12
            elif pref_energy == current_energy:
                score += 12
            elif self._energy_compatible(pref_energy, current_energy):
                score += 6  # Partial match

        # Attention mode matching (8 points)
        if current_attention:
            if pref_attention == 'any':
                score += 8
            elif pref_attention == current_attention:
                score += 8
            elif self._attention_compatible(pref_attention, current_attention):
                score += 4  # Partial match

        return score

    def _energy_compatible(self, preferred: str, current: str) -> bool:
        """Check if energy levels are compatible"""
        energy_order = ['low', 'medium', 'high', 'hyperfocus']

        try:
            pref_idx = energy_order.index(preferred)
            curr_idx = energy_order.index(current)
            # Allow +/- 1 level difference
            return abs(pref_idx - curr_idx) == 1
        except ValueError:
            return False

    def _attention_compatible(self, preferred: str, current: str) -> bool:
        """Check if attention modes are compatible"""
        # focused is compatible with hyperfocused, scattered is standalone
        if preferred == 'focused' and current == 'hyperfocused':
            return True
        if preferred == 'hyperfocused' and current == 'focused':
            return True
        return False

    def _score_time_window(self, windows: List[str], current_time: datetime) -> float:
        """Score time window match (0-15 points)"""
        if not windows:
            return 0.0

        current_hm = current_time.strftime("%H:%M")

        for window in windows:
            try:
                start, end = window.split('-')
                if start <= current_hm <= end:
                    return self.WEIGHT_TIME_WINDOW
            except ValueError:
                continue  # Skip malformed window

        return 0.0

    def _score_file_patterns(self, patterns: List[str], recent_files: List[str]) -> float:
        """Score file pattern match (0-10 points)"""
        if not patterns or not recent_files:
            return 0.0

        # Row 2.1.5 requirement: score by match percentage (0-10 points).
        candidates: List[str] = []
        seen = set()
        for file in recent_files[:10]:
            normalized = str(file).strip()
            if not normalized or normalized in seen:
                continue
            candidates.append(normalized)
            seen.add(normalized)

        if not candidates:
            return 0.0

        matches = 0
        for file in candidates:
            file_name = Path(file).name
            for pattern in patterns:
                if fnmatch.fnmatch(file, pattern) or fnmatch.fnmatch(file_name, pattern):
                    matches += 1
                    break  # Count each file once

        match_ratio = matches / len(candidates)
        return self.WEIGHT_FILE_PATTERNS * match_ratio

    def _gather_context(self) -> DetectionContext:
        """Auto-gather detection context from environment"""
        context = DetectionContext(
            current_dir=Path.cwd(),
            current_time=datetime.now()
        )

        # Detect git branch
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=2,
                cwd=context.current_dir
            )
            if result.returncode == 0:
                context.git_branch = result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass  # Git not available or not a git repo

        # Gather recent files from git log (last 7 days)
        try:
            git_log_result = subprocess.run(
                ['git', 'log', '--name-only', '--since="7 days ago"', '--pretty=format:', '--', '.'],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=context.current_dir
            )
            if git_log_result.returncode == 0:
                git_files = set(line.strip() for line in git_log_result.stdout.split('\n') if line.strip())
                # Filter to recent files that exist
                context.recent_files = [f for f in git_files if (context.current_dir / f).exists()][:20]
            else:
                # Fallback to current directory files
                common_extensions = ['*.py', '*.ts', '*.js', '*.go', '*.md', '*.yaml']
                recent = []
                for ext in common_extensions:
                    recent.extend([str(p.name) for p in context.current_dir.glob(ext)][:3])
                context.recent_files = recent[:10]
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            # Fallback to current directory files
            common_extensions = ['*.py', '*.ts', '*.js', '*.go', '*.md', '*.yaml']
            recent = []
            for ext in common_extensions:
                recent.extend([str(p.name) for p in context.current_dir.glob(ext)][:3])
            context.recent_files = recent[:10]

        # Query ADHD Engine for energy and attention states.
        # Row 2.1.3 requirement: query runtime service (5448 default), graceful fallback.
        energy_level, attention_mode = self._fetch_adhd_engine_state()
        if energy_level:
            context.energy_level = energy_level
        if attention_mode:
            context.attention_mode = attention_mode

        return context

    def _adhd_engine_base_urls(self) -> List[str]:
        """
        Build ADHD Engine base URLs in priority order.

        Priority:
        1. DOPMUX_ADHD_ENGINE_BASE_URL if provided.
        2. DOPMUX_ADHD_ENGINE_PORT if provided.
        3. Historical default port 5448.
        4. Current service default port 8095.
        """
        explicit_base = os.getenv("DOPEMUX_ADHD_ENGINE_BASE_URL", "").strip()
        if explicit_base:
            return [explicit_base.rstrip("/")]

        ports: List[int] = []
        env_port = os.getenv("DOPEMUX_ADHD_ENGINE_PORT", "").strip()
        if env_port.isdigit():
            ports.append(int(env_port))

        for fallback in (5448, 8095):
            if fallback not in ports:
                ports.append(fallback)

        return [f"http://localhost:{port}" for port in ports]

    def _read_json_url(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Read JSON payload from an HTTP endpoint.
        """
        req = Request(url=url, headers=headers or {}, method="GET")
        with urlopen(req, timeout=1.5) as resp:
            payload = resp.read().decode("utf-8")
        return json.loads(payload)

    def _fetch_adhd_engine_state(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Fetch energy and attention state from ADHD Engine API.

        Returns:
            (energy_level, attention_mode), lowercased when present.
            (None, None) when service is unavailable.
        """
        user_id = os.getenv("DOPEMUX_ADHD_USER_ID", "default_user").strip() or "default_user"
        api_key = os.getenv("ADHD_ENGINE_API_KEY", "").strip()
        headers: Dict[str, str] = {}
        if api_key:
            headers["X-API-Key"] = api_key

        for base_url in self._adhd_engine_base_urls():
            try:
                energy_data = self._read_json_url(
                    f"{base_url}/api/v1/energy-level/{user_id}",
                    headers=headers,
                )
                attention_data = self._read_json_url(
                    f"{base_url}/api/v1/attention-state/{user_id}",
                    headers=headers,
                )

                raw_energy = energy_data.get("energy_level")
                raw_attention = attention_data.get("attention_state")

                energy_level = raw_energy.lower() if isinstance(raw_energy, str) and raw_energy else None
                attention_mode = raw_attention.lower() if isinstance(raw_attention, str) and raw_attention else None

                if energy_level or attention_mode:
                    return energy_level, attention_mode

            except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError, ValueError) as exc:
                logger.debug("ADHD Engine probe failed at %s: %s", base_url, exc)
                continue
            except Exception as exc:
                logger.debug("Unexpected ADHD Engine probe error at %s: %s", base_url, exc)
                continue

        return None, None

    def get_all_scores(self, context: Optional[DetectionContext] = None) -> Dict[str, ProfileMatch]:
        """
        Get scores for all profiles (useful for debugging/UI).

        Args:
            context: Detection context (auto-detected if None)

        Returns:
            Dictionary of profile_name -> ProfileMatch
        """
        if context is None:
            context = self._gather_context()

        results = {}

        # Calculate scores for each profile individually
        for profile in self.profiles.profiles:
            signal_scores = {}

            # Signal 1: Git Branch (30 points)
            if context.git_branch and profile.auto_detection:
                signal_scores['git_branch'] = self._score_git_branch(
                    profile.auto_detection.git_branches,
                    context.git_branch
                )
            else:
                signal_scores['git_branch'] = 0.0

            # Signal 2: Directory Context (25 points)
            if profile.auto_detection:
                signal_scores['directory'] = self._score_directory(
                    profile.auto_detection.directories,
                    context.current_dir
                )
            else:
                signal_scores['directory'] = 0.0

            # Signal 3: ADHD State (20 points) - OPTIONAL
            if context.energy_level and profile.adhd_config:
                signal_scores['adhd_state'] = self._score_adhd_state(
                    profile.adhd_config.energy_preference,
                    profile.adhd_config.attention_mode,
                    context.energy_level,
                    context.attention_mode
                )
            else:
                signal_scores['adhd_state'] = 0.0

            # Signal 4: Time of Day (15 points)
            if profile.auto_detection:
                signal_scores['time_window'] = self._score_time_window(
                    profile.auto_detection.time_windows,
                    context.current_time
                )
            else:
                signal_scores['time_window'] = 0.0

            # Signal 5: Recent Files (10 points)
            if profile.auto_detection and context.recent_files:
                signal_scores['file_patterns'] = self._score_file_patterns(
                    profile.auto_detection.file_patterns,
                    context.recent_files
                )
            else:
                signal_scores['file_patterns'] = 0.0

            total_score = sum(signal_scores.values())
            confidence = total_score / 100.0

            # Determine suggestion level
            if confidence >= self.THRESHOLD_AUTO:
                suggestion_level = 'auto'
            elif confidence >= self.THRESHOLD_PROMPT:
                suggestion_level = 'prompt'
            else:
                suggestion_level = 'none'

            match = ProfileMatch(
                profile_name=profile.name,
                confidence=confidence,
                total_score=total_score,
                signal_scores=signal_scores,
                suggestion_level=suggestion_level
            )

            results[profile.name] = match

        return results


def format_match_summary(match: ProfileMatch) -> str:
    """
    Format detection match for display (ADHD-friendly).

    Args:
        match: ProfileMatch result

    Returns:
        Formatted summary string
    """
    lines = []

    # Header with confidence indicator
    conf_emoji = "✅" if match.confidence >= 0.85 else "⚠️" if match.confidence >= 0.65 else "❓"
    lines.append(f"{conf_emoji} Profile Match: {match.profile_name} ({match.confidence:.0%} confidence)")

    # Score breakdown
    lines.append(f"\nScore Breakdown ({match.total_score:.0f}/100 points):")

    for signal, score in match.signal_scores.items():
        if score > 0:
            bar = "█" * int(score / 5) + "░" * (20 - int(score / 5))
            lines.append(f"  {signal:15s} {bar} {score:5.1f}")

    # Suggestion
    if match.suggestion_level == 'auto':
        lines.append(f"\n💡 Auto-suggested (high confidence)")
    elif match.suggestion_level == 'prompt':
        lines.append(f"\n💡 Consider switching? (moderate confidence)")
    else:
        lines.append(f"\n🤷 Low confidence, manual selection recommended")

    return "\n".join(lines)


if __name__ == "__main__":
    # Quick test
    logger.info("Testing profile detector...")

    try:
        detector = ProfileDetector(Path("profiles"))

        # Test with auto-gathered context
        logger.info("\n--- Auto-Detection (current context) ---")
        match = detector.detect()
        logger.info(format_match_summary(match))

        # Test with custom context
        logger.info("\n--- Custom Context (feature branch + src/ dir) ---")
        custom_context = DetectionContext(
            current_dir=Path.cwd() / "src",
            git_branch="feature/auth",
            recent_files=["auth.py", "test_auth.py", "models.py"],
            energy_level="medium",
            attention_mode="focused"
        )
        match_custom = detector.detect(custom_context)
        logger.info(format_match_summary(match_custom))

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
