import subprocess
import sys
import json
from pathlib import Path
from enum import Enum, auto
from typing import Optional, List, Dict, Any

from .schema import PRState, PRMergeReport, MergeQueueEntry, CITriageCategory, BlockerEvidence, MergeAction, PRMetadataUpdate
from .graphql_client import GraphQLClient
from .triage_engine import TriageEngine
from .scoring import ScoringEngine
from .conflicts import ConflictAnalyzer, ConflictClass
from .feedback_engine import FeedbackIntake, FeedbackClassifier, RemediationPlanner
from .verification_engine import VerificationExtractor, CommandMapper, VerificationExecutor
from .body_engine import BodyParser, BodyEnforcer, MetadataCleaner
from .body_enforcer import PRBodyEnforcer
from .hygiene_engine import MetadataHygieneEngine
from .reply_engine import ReplyEngine
from .ops_engine import OperationalizationEngine
from .queries import GET_PR_DETAILED_STATE, ENQUEUE_PULL_REQUEST, DEQUEUE_PULL_REQUEST


class EngineState(Enum):
    START = auto()
    EVALUATING = auto()
    PENDING_RESOLUTION = auto()
    READY_TO_ENQUEUE = auto()
    ENQUEUED = auto()
    COMPLETED = auto()
    FAILED = auto()


class QueueManager:
    """Manages the PR lifecycle state machine for Merge Queue operations."""

    def __init__(self, client: GraphQLClient, triage_engine: TriageEngine, scoring_engine: ScoringEngine, conflict_analyzer: ConflictAnalyzer, ops_engine: Optional[OperationalizationEngine] = None):
        self.client = client
        self.triage_engine = triage_engine
        self.scoring_engine = scoring_engine
        self.conflict_analyzer = conflict_analyzer
        self.ops_engine = ops_engine
        self.feedback_intake = FeedbackIntake(FeedbackClassifier())
        self.remediation_planner = RemediationPlanner()
        self.verification_extractor = VerificationExtractor()
        self.command_mapper = CommandMapper()
        self.body_parser = BodyParser()
        self.body_enforcer = BodyEnforcer()
        self.metadata_cleaner = MetadataCleaner()
        self.pr_body_enforcer = PRBodyEnforcer()
        self.hygiene_engine = MetadataHygieneEngine()
        self.reply_engine = ReplyEngine()
        self.state = EngineState.START
        self._owner, self._repo = self._resolve_repo()

    def _resolve_repo(self) -> tuple[str, str]:
        """Determine owner and repo from gh repo view."""
        cmd = ["gh", "repo", "view", "--json", "owner,name"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            return "", ""
        data = json.loads(res.stdout)
        return data["owner"]["login"], data["name"]

    def process_pr(self, pr_id: str, run_id: str) -> PRMergeReport:
        """Execute the state machine for a single PR."""
        self.state = EngineState.EVALUATING
        
        # 1. Fetch current PR state via GraphQL
        variables = {
            "owner": self._owner,
            "repo": self._repo,
            "prNumber": int(pr_id)
        }
        data = self.client.query(GET_PR_DETAILED_STATE, variables)
        pr_node = data["repository"]["pullRequest"]
        
        pr_state, raw_checks = self._map_data_to_state(pr_node)
        
        # New: Ingest and Plan Feedback
        feedback_items = self.feedback_intake.normalize(pr_node)
        remediation_plan = self.remediation_planner.plan(feedback_items)
        
        # New: Body and Metadata Handling (Tranche 3)
        checklists = self.body_parser.parse_checklists(pr_node.get("body", ""))
        metadata_update_suggestion = self.metadata_cleaner.clean(pr_node["title"], pr_node.get("body", ""))
        
        # Metadata Hygiene Linting
        commits_raw = pr_node.get("commits", {}).get("nodes", [])
        metadata_hygiene_report = self.hygiene_engine.lint_metadata(pr_node["title"], pr_node.get("body", ""), commits_raw)
        
        # New: Extract and Map Verification Requests
        verif_requests = self.verification_extractor.extract(feedback_items)
        verif_plan = self.command_mapper.map_requests(verif_requests)
        
        # New: Resolve conflict class early for planning
        conflict_class = ConflictClass.MECHANICAL
        if not pr_state.mergeable:
            conflict_class = self.conflict_analyzer.classify_conflict(pr_state)

        # New: Execute Verification if requested
        verif_results = []
        if verif_plan.executable:
            # For TP-014, we only execute in a real run
            verif_executor = VerificationExecutor(Path("proof/pr_merge") / f"PR-{pr_id}" / run_id / "verification")
            verif_results = verif_executor.execute(verif_plan)
        
        # New: Generate enforced body
        body_mutation_plan = self.pr_body_enforcer.plan_mutations(
            pr_node.get("body", ""), 
            checklists, 
            verif_results, 
            remediation_plan.code_changes
        )
        
        metadata_update = PRMetadataUpdate(
            old_title=pr_node["title"],
            new_title=metadata_update_suggestion.new_title,
            old_body=pr_node.get("body", ""),
            new_body=body_mutation_plan["new_body"],
            hygiene_applied=metadata_update_suggestion.hygiene_applied
        )
        
        # New: Reply and Resolution Planning (TP-017)
        reply_plan, resolution_reports = self.reply_engine.plan_replies(
            feedback_items, 
            verif_results, 
            conflict_class.name
        )

        # 2. Idempotency and Queue Health check
        if pr_state.is_in_merge_queue:
            mq = pr_state.merge_queue_entry
            if mq.state not in ["QUEUED", "AWAITING_CHECKS", "MERGING"]:
                self.state = EngineState.FAILED
                return PRMergeReport(
                    run_id=run_id,
                    pr_id=pr_id,
                    initial_state=pr_state,
                    status="blocked",
                    status_reason=f"PR is in an unhealthy queue state: {mq.state} at position {mq.position}. Escalation required."
                )
            
            self.state = EngineState.ENQUEUED
            return PRMergeReport(
                run_id=run_id,
                pr_id=pr_id,
                initial_state=pr_state,
                status="merged", # Status 'merged' used for already enqueued
                status_reason=f"PR is already in merge queue at position {mq.position}."
            )

        # 3. Check for blocking conditions
        blockers = []
        if not pr_state.all_threads_resolved:
            blockers.append(BlockerEvidence(
                type="COMMENTS",
                description=f"Found {pr_state.unresolved_thread_count} unresolved review threads."
            ))

        if not pr_state.mergeable:
            if not self.conflict_analyzer.is_auto_resolvable(conflict_class):
                blockers.append(BlockerEvidence(
                    type="CONFLICTS",
                    description=f"PR has unsafe conflicts classified as {conflict_class.name}."
                ))

        # 4. Triage CI and Score
        triage_results = self.triage_engine.triage(raw_checks)
        score = self.scoring_engine.calculate_score(pr_state)
        
        if pr_state.ci_status == "FAILURE":
            is_retryable = self.triage_engine.is_retryable(triage_results)
            blockers.append(BlockerEvidence(
                type="CI_FAIL",
                description=f"CI failed. Retryable: {is_retryable}. Details: {triage_results}"
            ))
        
        # New: Elevate remediation items to blockers if mandatory
        for item in remediation_plan.code_changes + remediation_plan.test_work + remediation_plan.escalations:
            blockers.append(BlockerEvidence(
                type="COMMENTS",
                description=f"Actionable feedback ({item.intent}) from {item.author}: {item.text[:50]}..."
            ))
            
        # New: Elevate pending verification to blockers
        for v in verif_plan.executable + verif_plan.manual:
            # Check if execution already failed
            matching_result = next((r for r in verif_results if r.request_id == v.id), None)
            if matching_result and matching_result.exit_code != 0:
                blockers.append(BlockerEvidence(
                    type="CI_FAIL",
                    description=f"Verification failed: {v.command_intent} (Exit {matching_result.exit_code})"
                ))
            elif not matching_result:
                 blockers.append(BlockerEvidence(
                    type="POLICY_BLOCK",
                    description=f"Pending verification: {v.command_intent} ({v.status})"
                ))

        # Elevate section gaps to blockers
        for gap in body_mutation_plan["gaps"]:
            blockers.append(BlockerEvidence(
                type="POLICY_BLOCK",
                description=f"Missing required section: {gap}"
            ))
        
        # Elevate metadata errors to blockers
        if metadata_hygiene_report["summary"]["errors"] > 0:
            for issue in metadata_hygiene_report["issues"]:
                if issue["severity"] == "error":
                    blockers.append(BlockerEvidence(
                        type="POLICY_BLOCK",
                        description=f"Metadata Hygiene Error: {issue['reason']}"
                    ))

        if blockers:
            self.state = EngineState.PENDING_RESOLUTION
            return PRMergeReport(
                run_id=run_id,
                pr_id=pr_id,
                initial_state=pr_state,
                blockers=blockers,
                triage_results=triage_results,
                feedback_items=feedback_items,
                remediation_plan=remediation_plan,
                verification_requests=verif_requests,
                verification_plan=verif_plan,
                verification_results=verif_results,
                checklists=checklists,
                metadata_update=metadata_update,
                review_reply_plan=reply_plan,
                resolution_guard_reports=resolution_reports,
                status="blocked",
                status_reason=f"Blocked by {len(blockers)} conditions. Conflict Class: {conflict_class.name}. Score: {score:.2f}.",
                telemetry={"score": score, "conflict_class": conflict_class.name}
            )

        # 5. Ready to Enqueue
        self.state = EngineState.READY_TO_ENQUEUE
        
        return PRMergeReport(
            run_id=run_id,
            pr_id=pr_id,
            initial_state=pr_state,
            triage_results=triage_results,
            feedback_items=feedback_items,
            remediation_plan=remediation_plan,
            verification_requests=verif_requests,
            verification_plan=verif_plan,
            verification_results=verif_results,
            checklists=checklists,
            metadata_update=metadata_update,
            review_reply_plan=reply_plan,
            resolution_guard_reports=resolution_reports,
            status="merge_ready",
            status_reason=f"All checks passed and threads resolved. Score: {score:.2f}.",
            telemetry={"score": score, "conflict_class": conflict_class.name}
        )

    def _fetch_detailed_state(self, pr_id: str) -> PRState:
        """Fetch detailed PR state using GraphQL client."""
        variables = {
            "owner": self._owner,
            "repo": self._repo,
            "prNumber": int(pr_id)
        }
        data = self.client.query(GET_PR_DETAILED_STATE, variables)
        pr_node = data["repository"]["pullRequest"]
        state, _ = self._map_data_to_state(pr_node)
        return state

    def _map_data_to_state(self, pr_data: Dict[str, Any]) -> tuple[PRState, List[Dict[str, Any]]]:
        mq_data = pr_data.get("mergeQueueEntry")
        mq_entry = None
        if mq_data:
            mq_entry = MergeQueueEntry(
                position=mq_data["position"],
                state=mq_data["state"],
                estimated_time_to_merge_seconds=mq_data.get("estimatedTimeToMerge")
            )
            
        threads = pr_data.get("reviewThreads", {}).get("nodes", [])
        unresolved = [t for t in threads if not t.get("isResolved")]
        
        # Get checks
        commits = pr_data.get("commits", {}).get("nodes", [])
        check_runs = []
        if commits:
            rollup = commits[0].get("commit", {}).get("statusCheckRollup", {})
            if rollup:
                check_runs = rollup.get("contexts", {}).get("nodes", [])
                
        ci_status = "SUCCESS"
        if any(c.get("conclusion") in ["FAILURE", "TIMED_OUT", "ACTION_REQUIRED"] for c in check_runs):
            ci_status = "FAILURE"
        elif any(c.get("status") == "IN_PROGRESS" for c in check_runs):
            ci_status = "PENDING"

        state = PRState(
            pr_id=str(pr_data["number"]),
            title=pr_data["title"],
            author=pr_data["author"]["login"],
            state=pr_data["state"],
            ci_status=ci_status,
            mergeable=pr_data["mergeable"] == "MERGEABLE",
            labels=[l["name"] for l in pr_data.get("labels", {}).get("nodes", [])],
            updated_at=pr_data["updatedAt"],
            is_in_merge_queue=mq_entry is not None,
            merge_queue_entry=mq_entry,
            unresolved_thread_count=len(unresolved),
            all_threads_resolved=len(unresolved) == 0
        )
        return state, check_runs
