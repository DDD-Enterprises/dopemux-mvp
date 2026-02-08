"""
Untracked Work Storage - ConPort Persistence Layer

Stores untracked work items in ConPort for cross-session reminder tracking.
Implements status state machine and reminder frequency management.

Part of Feature 1: Untracked Work Detection
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
import logging
import json
import uuid

logger = logging.getLogger(__name__)


class UntrackedWorkStatus:
    """Status values for untracked work state machine"""
    DETECTED = "detected"
    ACKNOWLEDGED = "acknowledged"
    SNOOZED = "snoozed"
    CONVERTED_TO_TASK = "converted_to_task"
    ABANDONED = "abandoned"


class UntrackedWorkStorage:
    """
    ConPort storage for untracked work items

    Schema (ConPort custom_data):
    - category: "untracked_work"
    - key: "untracked_work_{uuid}"
    - value: {
        untracked_work_id: uuid,
        auto_generated_name: str,
        detected_at: ISO timestamp,
        status: detected|acknowledged|snoozed|converted_to_task|abandoned,
        snooze_until: ISO timestamp (optional),
        reminded_count: int,
        reminded_this_session: bool,
        last_reminded: ISO timestamp (optional),
        detected_sessions: int,
        linked_task_id: int (optional),
        detection_signals: {...},
        user_notes: str
      }
    """

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.category = "untracked_work"

    async def save_detected_work(
        self,
        detection: Dict,
        conport_client
    ) -> str:
        """
        Save newly detected untracked work to ConPort

        Args:
            detection: Result from UntrackedWorkDetector.detect()
            conport_client: ConPort MCP client for storage

        Returns:
            untracked_work_id (UUID string)
        """
        if not conport_client:
            raise ValueError("ConPort client required for storage")

        # Generate unique ID
        work_id = str(uuid.uuid4())
        key = f"untracked_work_{work_id}"

        # Build storage record
        record = {
            "untracked_work_id": work_id,
            "auto_generated_name": detection["work_name"],
            "detected_at": datetime.now().isoformat(),
            "status": UntrackedWorkStatus.DETECTED,
            "snooze_until": None,
            "reminded_count": 0,
            "reminded_this_session": False,
            "last_reminded": None,
            "detected_sessions": 1,
            "linked_task_id": None,
            "detection_signals": detection["detection_signals"],
            "git_summary": detection["git_detection"],
            "user_notes": ""
        }

        # Save to ConPort
        try:
            # Use ConPort MCP: log_custom_data
            await conport_client.log_custom_data(
                workspace_id=self.workspace_id,
                category=self.category,
                key=key,
                value=record
            )

            logger.info(f"Saved untracked work: {work_id} - '{detection['work_name']}'")
            return work_id

        except Exception as e:
            logger.error(f"Failed to save untracked work: {e}")
            raise

    async def get_all_untracked_work(
        self,
        conport_client,
        include_completed: bool = False
    ) -> List[Dict]:
        """
        Get all untracked work items from ConPort

        Args:
            conport_client: ConPort MCP client
            include_completed: Include converted_to_task and abandoned items

        Returns:
            List of untracked work records
        """
        if not conport_client:
            return []

        try:
            # Get all custom_data in untracked_work category
            all_data = await conport_client.get_custom_data(
                workspace_id=self.workspace_id,
                category=self.category
            )

            items = []
            for entry in all_data:
                record = entry.get("value", {})

                # Filter by status
                status = record.get("status")
                if not include_completed:
                    if status in [UntrackedWorkStatus.CONVERTED_TO_TASK, UntrackedWorkStatus.ABANDONED]:
                        continue

                items.append(record)

            return items

        except Exception as e:
            logger.error(f"Failed to get untracked work: {e}")
            return []

    async def update_status(
        self,
        work_id: str,
        new_status: str,
        conport_client,
        extra_fields: Optional[Dict] = None
    ) -> bool:
        """
        Update untracked work status

        Args:
            work_id: Untracked work UUID
            new_status: New status value
            conport_client: ConPort MCP client
            extra_fields: Optional additional fields to update

        Returns:
            True if successful
        """
        if not conport_client:
            return False

        key = f"untracked_work_{work_id}"

        try:
            # Get current record
            current = await conport_client.get_custom_data(
                workspace_id=self.workspace_id,
                category=self.category,
                key=key
            )

            if not current:
                logger.warning(f"Untracked work not found: {work_id}")
                return False

            # Update record
            record = current[0].get("value", {})
            record["status"] = new_status
            record["updated_at"] = datetime.now().isoformat()

            # Add extra fields
            if extra_fields:
                record.update(extra_fields)

            # Save back to ConPort
            await conport_client.log_custom_data(
                workspace_id=self.workspace_id,
                category=self.category,
                key=key,
                value=record
            )

            logger.info(f"Updated untracked work {work_id}: status → {new_status}")
            return True

        except Exception as e:
            logger.error(f"Failed to update status: {e}")
            return False

    async def mark_reminded(
        self,
        work_id: str,
        conport_client
    ) -> bool:
        """
        Mark work as reminded (for reminder frequency tracking)

        Updates:
        - reminded_count += 1
        - last_reminded = now
        - reminded_this_session = true

        Args:
            work_id: Untracked work UUID
            conport_client: ConPort MCP client

        Returns:
            True if successful
        """
        try:
            # Get current record
            key = f"untracked_work_{work_id}"
            current = await conport_client.get_custom_data(
                workspace_id=self.workspace_id,
                category=self.category,
                key=key
            )

            if not current:
                return False

            record = current[0].get("value", {})

            # Update reminder tracking
            record["reminded_count"] = record.get("reminded_count", 0) + 1
            record["last_reminded"] = datetime.now().isoformat()
            record["reminded_this_session"] = True

            # Save
            await conport_client.log_custom_data(
                workspace_id=self.workspace_id,
                category=self.category,
                key=key,
                value=record
            )

            logger.info(f"Marked reminded: {work_id} (count: {record['reminded_count']})")
            return True

        except Exception as e:
            logger.error(f"Failed to mark reminded: {e}")
            return False

    async def snooze_work(
        self,
        work_id: str,
        duration_seconds: int,
        conport_client
    ) -> bool:
        """
        Snooze untracked work for specified duration

        Args:
            work_id: Untracked work UUID
            duration_seconds: Snooze duration (3600=1h, 14400=4h, 86400=1d)
            conport_client: ConPort MCP client

        Returns:
            True if successful
        """
        snooze_until = datetime.now() + timedelta(seconds=duration_seconds)

        return await self.update_status(
            work_id=work_id,
            new_status=UntrackedWorkStatus.SNOOZED,
            conport_client=conport_client,
            extra_fields={
                "snooze_until": snooze_until.isoformat(),
                "snoozed_at": datetime.now().isoformat()
            }
        )

    async def acknowledge_work(
        self,
        work_id: str,
        conport_client
    ) -> bool:
        """
        Mark work as acknowledged (user pressed Enter)

        Status: detected → acknowledged
        Enables exponential backoff reminders

        Args:
            work_id: Untracked work UUID
            conport_client: ConPort MCP client

        Returns:
            True if successful
        """
        return await self.update_status(
            work_id=work_id,
            new_status=UntrackedWorkStatus.ACKNOWLEDGED,
            conport_client=conport_client,
            extra_fields={
                "acknowledged_at": datetime.now().isoformat()
            }
        )

    async def abandon_work(
        self,
        work_id: str,
        conport_client
    ) -> bool:
        """
        Mark work as abandoned (user chose Ignore)

        Status: * → abandoned
        Won't remind again

        Args:
            work_id: Untracked work UUID
            conport_client: ConPort MCP client

        Returns:
            True if successful
        """
        return await self.update_status(
            work_id=work_id,
            new_status=UntrackedWorkStatus.ABANDONED,
            conport_client=conport_client,
            extra_fields={
                "abandoned_at": datetime.now().isoformat()
            }
        )

    async def convert_to_task(
        self,
        work_id: str,
        task_id: int,
        conport_client
    ) -> bool:
        """
        Mark work as converted to ConPort task

        Status: * → converted_to_task
        Links to the created task

        Args:
            work_id: Untracked work UUID
            task_id: ConPort progress_entry ID
            conport_client: ConPort MCP client

        Returns:
            True if successful
        """
        return await self.update_status(
            work_id=work_id,
            new_status=UntrackedWorkStatus.CONVERTED_TO_TASK,
            conport_client=conport_client,
            extra_fields={
                "linked_task_id": task_id,
                "converted_at": datetime.now().isoformat()
            }
        )

    async def auto_close_on_commit(
        self,
        work_id: str,
        commit_info: Dict,
        conport_client
    ) -> bool:
        """
        F2: Auto-close untracked work when files are committed

        Status: * → converted_to_task (with commit info)

        Args:
            work_id: Untracked work UUID
            commit_info: Result from GitWorkDetector.check_files_committed()
            conport_client: ConPort MCP client

        Returns:
            True if successful
        """
        if not commit_info.get("committed"):
            return False

        return await self.update_status(
            work_id=work_id,
            new_status=UntrackedWorkStatus.CONVERTED_TO_TASK,
            conport_client=conport_client,
            extra_fields={
                "auto_closed": True,
                "auto_close_reason": "committed_to_git",
                "commit_sha": commit_info.get("commit_sha"),
                "commit_message": commit_info.get("commit_message"),
                "commit_date": commit_info.get("commit_date"),
                "commit_percentage": commit_info.get("commit_percentage"),
                "closed_at": datetime.now().isoformat()
            }
        )

    async def check_and_close_committed_work(
        self,
        git_detector,
        conport_client,
        max_commits_to_check: int = 5
    ) -> Dict:
        """
        F2: Check all tracked work against recent commits and auto-close

        Runs through recent commits (HEAD~0 to HEAD~max) and checks if any
        tracked work has been committed. Auto-closes matching work.

        Args:
            git_detector: GitWorkDetector instance
            conport_client: ConPort MCP client
            max_commits_to_check: Check last N commits (default: 5)

        Returns:
            {
                "checked_work_items": int,
                "closed_items": int,
                "closed_work": List[Dict],
                "commits_checked": int
            }
        """
        if not conport_client:
            return {
                "checked_work_items": 0,
                "closed_items": 0,
                "closed_work": [],
                "commits_checked": 0,
                "error": "ConPort client required"
            }

        try:
            # Get all tracked work (detected, acknowledged, snoozed)
            all_work = await conport_client.get_custom_data(
                workspace_id=self.workspace_id,
                category=self.category
            )

            if not all_work:
                return {
                    "checked_work_items": 0,
                    "closed_items": 0,
                    "closed_work": [],
                    "commits_checked": 0
                }

            # Filter to active work (not already closed/abandoned)
            active_work = [
                w for w in all_work
                if w.get("value", {}).get("status") not in [
                    UntrackedWorkStatus.CONVERTED_TO_TASK,
                    UntrackedWorkStatus.ABANDONED
                ]
            ]

            closed_work = []
            commits_checked = min(max_commits_to_check, 5)  # Safety limit

            # Check each active work item against recent commits
            for work_item in active_work:
                work_data = work_item.get("value", {})
                work_id = work_data.get("untracked_work_id")
                git_summary = work_data.get("git_summary", {})
                tracked_files = git_summary.get("files", [])

                if not tracked_files:
                    continue

                # Check recent commits
                for i in range(commits_checked):
                    commit_ref = f"HEAD~{i}" if i > 0 else "HEAD"

                    commit_info = await git_detector.check_files_committed(
                        file_list=tracked_files,
                        commit_ref=commit_ref
                    )

                    if commit_info.get("committed"):
                        # 80%+ match found → auto-close
                        success = await self.auto_close_on_commit(
                            work_id=work_id,
                            commit_info=commit_info,
                            conport_client=conport_client
                        )

                        if success:
                            closed_work.append({
                                "work_id": work_id,
                                "work_name": work_data.get("auto_generated_name"),
                                "commit_sha": commit_info.get("commit_sha"),
                                "commit_message": commit_info.get("commit_message"),
                                "commit_percentage": commit_info.get("commit_percentage")
                            })
                            logger.info(
                                f"Auto-closed work '{work_data.get('auto_generated_name')}' "
                                f"({commit_info.get('commit_percentage')*100:.0f}% match with commit {commit_info.get('commit_sha')[:8]})"
                            )

                        break  # Found commit, no need to check older ones

            return {
                "checked_work_items": len(active_work),
                "closed_items": len(closed_work),
                "closed_work": closed_work,
                "commits_checked": commits_checked
            }

        except Exception as e:
            logger.error(f"Failed to check committed work: {e}")
            return {
                "checked_work_items": 0,
                "closed_items": 0,
                "closed_work": [],
                "commits_checked": 0,
                "error": str(e)
            }

    async def auto_track_if_threshold_met(
        self,
        detection: Dict,
        threshold: float,
        conport_client,
        custom_description: Optional[str] = None,
        complexity: Optional[float] = None
    ) -> Optional[Dict]:
        """
        F1: Auto-create ConPort task if confidence >= threshold

        Args:
            detection: Result from UntrackedWorkDetector.detect()
            threshold: Auto-track threshold (default from config: 0.85)
            conport_client: ConPort MCP client for task creation
            custom_description: Optional override for task description
            complexity: Optional override for complexity estimation

        Returns:
            None if below threshold
            Task dict if auto-created: {task_id, description, complexity, work_id}
        """
        confidence = detection.get("confidence_score", 0.0)

        if confidence < threshold:
            return None

        # Confidence >= threshold → auto-track
        logger.info(f"Auto-tracking work (confidence {confidence:.2f} >= threshold {threshold:.2f})")

        # Generate task suggestion (from untracked_work_detector.py)
        work_name = detection.get("work_name", "Untracked work")
        git_detection = detection.get("git_detection", {})
        files = git_detection.get("files", [])
        stats = git_detection.get("stats", {})

        # Calculate complexity if not provided
        if complexity is None:
            file_count = len(files)
            if file_count <= 2:
                complexity = 0.3
            elif file_count <= 5:
                complexity = 0.5
            else:
                complexity = 0.7

        # Build task description
        if custom_description:
            description = custom_description
        else:
            description = work_name

        # Create ConPort task
        try:
            task_result = await conport_client.log_progress(
                workspace_id=self.workspace_id,
                status="IN_PROGRESS",
                description=description,
                linked_item_type="untracked_work_detection",
                linked_item_id=None  # Will update after saving work record
            )

            # Parse task_id from result
            task_id = None
            if isinstance(task_result, dict):
                task_id = task_result.get("id")
            elif isinstance(task_result, str):
                # Try to parse JSON response
                try:
                    task_data = json.loads(task_result)
                    task_id = task_data.get("id")
                except Exception as e:
                    logger.error(f"Error: {e}")
            if task_id:
                logger.info(f"Auto-created task #{task_id}: {description}")

                return {
                    "task_id": task_id,
                    "description": description,
                    "complexity": complexity,
                    "auto_tracked": True,
                    "confidence_score": confidence,
                    "threshold_used": threshold,
                    "file_count": len(files),
                    "stats": stats
                }
            else:
                logger.warning("Task creation succeeded but no ID returned")
                return None

        except Exception as e:
            logger.error(f"Auto-track failed: {e}")
            return None

    async def should_remind_now(
        self,
        work_record: Dict
    ) -> tuple[bool, str]:
        """
        Determine if reminder should be shown NOW (enhanced version)

        Implements full reminder logic from Feature 1 spec:
        1. Never remind more than once per session
        2. Never remind during first detection (session 1)
        3. Check snooze status and expiration
        4. Exponential backoff for acknowledged work
        5. Daily reminder for persistent work (3+ sessions)

        Args:
            work_record: Untracked work record from ConPort

        Returns:
            (should_remind: bool, reason: str)
        """
        status = work_record.get("status", UntrackedWorkStatus.DETECTED)

        # Rule 1: Never remind more than once per session
        if work_record.get("reminded_this_session", False):
            return (False, "already_reminded_this_session")

        # Rule 2: Never remind during first detection
        detected_sessions = work_record.get("detected_sessions", 1)
        if detected_sessions < 2:
            return (False, "needs_persistence_check (session 1)")

        # Rule 3: Check if abandoned
        if status == UntrackedWorkStatus.ABANDONED:
            return (False, "work_abandoned")

        # Rule 4: Check if already converted
        if status == UntrackedWorkStatus.CONVERTED_TO_TASK:
            return (False, "already_converted_to_task")

        # Rule 5: Check snooze status
        if status == UntrackedWorkStatus.SNOOZED:
            snooze_until_str = work_record.get("snooze_until")
            if snooze_until_str:
                snooze_until = datetime.fromisoformat(snooze_until_str)
                if datetime.now() < snooze_until:
                    mins_remaining = round((snooze_until - datetime.now()).total_seconds() / 60)
                    return (False, f"snoozed ({mins_remaining} min remaining)")
                else:
                    # Snooze expired - remind now!
                    return (True, "snooze_expired")

        # Rule 6: Exponential backoff for acknowledged work
        if status == UntrackedWorkStatus.ACKNOWLEDGED:
            last_reminded_str = work_record.get("last_reminded")
            if last_reminded_str:
                last_reminded = datetime.fromisoformat(last_reminded_str)
                hours_since = (datetime.now() - last_reminded).total_seconds() / 3600

                # Exponential backoff: 1h, 2h, 4h, 8h, 16h, ...
                reminded_count = work_record.get("reminded_count", 0)
                remind_interval_hours = 2 ** reminded_count

                if hours_since >= remind_interval_hours:
                    return (True, f"backoff_interval_reached ({remind_interval_hours}h)")
                else:
                    next_in = round(remind_interval_hours - hours_since, 1)
                    return (False, f"within_backoff ({next_in}h remaining)")

        # Rule 7: First reminder for newly detected work (session 2+)
        if status == UntrackedWorkStatus.DETECTED and work_record.get("reminded_count", 0) == 0:
            return (True, "new_detection (session 2+)")

        # Rule 8: Daily reminder for persistent work (3+ sessions)
        if detected_sessions >= 3:
            last_reminded_str = work_record.get("last_reminded")
            if last_reminded_str:
                last_reminded = datetime.fromisoformat(last_reminded_str)
                hours_since = (datetime.now() - last_reminded).total_seconds() / 3600

                if hours_since >= 24:
                    return (True, "persistent_work_daily")

        return (False, "no_criteria_met")

    async def increment_session_count(
        self,
        work_id: str,
        conport_client
    ) -> bool:
        """
        Increment detected_sessions counter

        Call this at session start when work still exists

        Args:
            work_id: Untracked work UUID
            conport_client: ConPort MCP client

        Returns:
            True if successful
        """
        try:
            key = f"untracked_work_{work_id}"
            current = await conport_client.get_custom_data(
                workspace_id=self.workspace_id,
                category=self.category,
                key=key
            )

            if not current:
                return False

            record = current[0].get("value", {})

            # Increment session count
            record["detected_sessions"] = record.get("detected_sessions", 1) + 1
            record["last_detected_at"] = datetime.now().isoformat()

            # Reset session flag
            record["reminded_this_session"] = False

            # Save
            await conport_client.log_custom_data(
                workspace_id=self.workspace_id,
                category=self.category,
                key=key,
                value=record
            )

            logger.info(f"Incremented session count: {work_id} → {record['detected_sessions']}")
            return True

        except Exception as e:
            logger.error(f"Failed to increment session: {e}")
            return False

    async def get_active_reminders(
        self,
        conport_client
    ) -> List[Dict]:
        """
        Get untracked work items that should be reminded NOW

        Filters for:
        - Not reminded this session
        - Past persistence check (session 2+)
        - Not snoozed OR snooze expired
        - Not abandoned/converted
        - Passes reminder frequency rules

        Args:
            conport_client: ConPort MCP client

        Returns:
            List of work records that need reminders
        """
        all_work = await self.get_all_untracked_work(
            conport_client,
            include_completed=False
        )

        active_reminders = []

        for work in all_work:
            should_remind, reason = await self.should_remind_now(work)

            if should_remind:
                # Add reminder metadata
                work["reminder_reason"] = reason
                active_reminders.append(work)

        logger.info(f"Active reminders: {len(active_reminders)} of {len(all_work)} untracked items")
        return active_reminders

    async def find_matching_work(
        self,
        git_detection: Dict,
        conport_client
    ) -> Optional[Dict]:
        """
        Find existing untracked work record matching current git state

        Used to avoid creating duplicates - if work already tracked,
        just increment session count instead

        Args:
            git_detection: Current git detection result
            conport_client: ConPort MCP client

        Returns:
            Matching work record if found, None otherwise
        """
        all_work = await self.get_all_untracked_work(
            conport_client,
            include_completed=False
        )

        # Match based on branch name or file overlap
        current_branch = git_detection.get("branch")
        current_files = set(git_detection.get("files", []))

        for work in all_work:
            work_git = work.get("git_summary", {})
            work_branch = work_git.get("branch")
            work_files = set(work_git.get("files", []))

            # Match if same branch OR significant file overlap (>50%)
            if current_branch and work_branch == current_branch:
                return work

            if current_files and work_files:
                overlap = len(current_files & work_files)
                if overlap > 0 and overlap / len(current_files) > 0.5:
                    return work

        return None

    async def get_user_config(
        self,
        conport_client
    ) -> Dict:
        """
        Get user configuration for Feature 1

        Returns default config if not set

        Returns:
            {
                "enabled": bool,
                "confidence_threshold": float,
                "grace_period_minutes": int,
                "quiet_hours": {...},
                "snooze_durations": {...},
                ...
            }
        """
        if not conport_client:
            return self._default_config()

        try:
            config_data = await conport_client.get_custom_data(
                workspace_id=self.workspace_id,
                category="user_preferences",
                key="untracked_work_config"
            )

            if config_data and len(config_data) > 0:
                return config_data[0].get("value", self._default_config())

        except Exception as e:
            logger.warning(f"Failed to get user config: {e}")

        return self._default_config()

    def _default_config(self) -> Dict:
        """Default Feature 1 configuration from spec"""
        return {
            "enabled": True,
            "confidence_threshold": 0.65,
            "grace_period_minutes": 30,
            "auto_track_threshold": 0.85,  # F1: Auto-track when confidence >= 0.85
            "quiet_hours": {
                "enabled": False,
                "start": "22:00",
                "end": "08:00"
            },
            "snooze_durations": {
                "short": 3600,      # 1 hour
                "medium": 14400,    # 4 hours
                "long": 86400       # 1 day
            },
            "max_reminded_count": 10,
            "auto_abandon_after_days": 30
        }

    async def save_user_config(
        self,
        config: Dict,
        conport_client
    ) -> bool:
        """
        Save user configuration to ConPort

        Args:
            config: Configuration dictionary
            conport_client: ConPort MCP client

        Returns:
            True if successful
        """
        if not conport_client:
            return False

        try:
            await conport_client.log_custom_data(
                workspace_id=self.workspace_id,
                category="user_preferences",
                key="untracked_work_config",
                value=config
            )

            logger.info("Saved user config for untracked work detection")
            return True

        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    def is_quiet_hours(self, config: Dict) -> bool:
        """
        Check if current time is in quiet hours

        Args:
            config: User configuration

        Returns:
            True if in quiet hours (should suppress reminders)
        """
        quiet_hours = config.get("quiet_hours", {})
        if not quiet_hours.get("enabled", False):
            return False

        now = datetime.now()
        current_time = now.time()

        # Parse quiet hours
        try:
            start_str = quiet_hours.get("start", "22:00")
            end_str = quiet_hours.get("end", "08:00")

            start_time = datetime.strptime(start_str, "%H:%M").time()
            end_time = datetime.strptime(end_str, "%H:%M").time()

            # Handle overnight range (e.g., 22:00 - 08:00)
            if start_time > end_time:
                return current_time >= start_time or current_time <= end_time
            else:
                return start_time <= current_time <= end_time

        except Exception as e:
            logger.warning(f"Failed to parse quiet hours: {e}")
            return False
