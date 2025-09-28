#!/usr/bin/env python3
"""
Phased Chatlog Extraction CLI

Extracts structured information from chat logs using a step-by-step approach
with detailed status reporting and user confirmation for each phase.

Designed for ADHD-friendly processing with clear checkpoints and progress visibility.
"""

import os
import sys
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.prompt import Confirm, Prompt
from rich.markup import escape

console = Console()

@dataclass
class ExtractionPhase:
    """Represents a single extraction phase."""
    name: str
    description: str
    expected_duration: str
    outputs: List[str]
    dependencies: List[str] = None

@dataclass
class ChatlogMetadata:
    """Metadata about the chatlog being processed."""
    file_path: str
    file_size: int
    line_count: int
    estimated_messages: int
    date_range: Optional[Tuple[str, str]] = None
    participants: List[str] = None

@dataclass
class ExtractionResults:
    """Results from a completed extraction phase."""
    phase_name: str
    success: bool
    processing_time: float
    items_extracted: int
    output_files: List[str]
    errors: List[str] = None
    metadata: Dict[str, Any] = None

class ChatlogExtractor:
    """
    Multi-phase chatlog extraction system with ADHD-optimized processing.

    Breaks down complex extraction into manageable phases with user confirmation
    and detailed status reporting for each step.
    """

    def __init__(self, chatlog_path: str, output_dir: str):
        """Initialize the extractor with input and output paths."""
        self.chatlog_path = Path(chatlog_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Define extraction phases
        self.phases = [
            ExtractionPhase(
                name="Discovery",
                description="Analyze chatlog structure and detect format",
                expected_duration="30-60 seconds",
                outputs=["metadata.json", "format_analysis.txt"],
                dependencies=[]
            ),
            ExtractionPhase(
                name="Parsing",
                description="Extract individual messages and participants",
                expected_duration="1-3 minutes",
                outputs=["messages.jsonl", "participants.json"],
                dependencies=["Discovery"]
            ),
            ExtractionPhase(
                name="Structuring",
                description="Identify conversation threads and topics",
                expected_duration="2-5 minutes",
                outputs=["threads.json", "topics.json"],
                dependencies=["Parsing"]
            ),
            ExtractionPhase(
                name="Enrichment",
                description="Extract decisions, action items, and key insights",
                expected_duration="3-7 minutes",
                outputs=["decisions.json", "action_items.json", "insights.json"],
                dependencies=["Structuring"]
            ),
            ExtractionPhase(
                name="Summarization",
                description="Generate conversation summaries and final report",
                expected_duration="1-2 minutes",
                outputs=["summary.md", "extraction_report.json"],
                dependencies=["Enrichment"]
            )
        ]

        # Track completed phases and results
        self.completed_phases = []
        self.phase_results = {}
        self.total_start_time = None

    def run_extraction(self, start_phase: str = "Discovery", auto_confirm: bool = False) -> Dict[str, Any]:
        """
        Run the complete extraction process with user confirmation.

        Args:
            start_phase: Phase to start from (useful for resuming)
            auto_confirm: Skip user confirmation (for automation)

        Returns:
            Dictionary containing complete extraction results
        """
        console.print(Panel(
            "🔍 [bold blue]Phased Chatlog Extraction[/bold blue]\n\n"
            f"📁 Input: {self.chatlog_path}\n"
            f"📁 Output: {self.output_dir}\n\n"
            "This tool will process your chatlog in 5 phases with detailed status reporting.\n"
            "You can review and confirm each phase before proceeding.",
            title="🚀 Chatlog Extraction Starting",
            border_style="blue"
        ))

        self.total_start_time = time.time()

        # Find starting phase index
        start_index = 0
        for i, phase in enumerate(self.phases):
            if phase.name == start_phase:
                start_index = i
                break

        # Run phases sequentially
        for i in range(start_index, len(self.phases)):
            phase = self.phases[i]

            # Check dependencies
            if not self._check_dependencies(phase):
                console.print(f"[red]❌ Dependencies not met for phase '{phase.name}'[/red]")
                return {"success": False, "error": "Dependencies not met"}

            # Display phase information
            self._display_phase_info(phase, i + 1, len(self.phases))

            # User confirmation (unless auto-confirm)
            if not auto_confirm:
                if not Confirm.ask(f"🤔 Proceed with [yellow]{phase.name}[/yellow] phase?"):
                    console.print("[yellow]⏸️ Extraction paused by user[/yellow]")
                    return {"success": False, "paused_at": phase.name}

            # Execute phase
            console.print(f"[blue]🔄 Starting {phase.name} phase...[/blue]")
            result = self._execute_phase(phase)

            # Store results
            self.phase_results[phase.name] = result
            if result.success:
                self.completed_phases.append(phase.name)

            # Display results
            self._display_phase_results(result)

            # Handle failures
            if not result.success:
                console.print(f"[red]❌ Phase '{phase.name}' failed[/red]")
                if not auto_confirm:
                    if not Confirm.ask("Continue with remaining phases?"):
                        return {"success": False, "failed_at": phase.name}
                else:
                    return {"success": False, "failed_at": phase.name}

        # Generate final report
        total_time = time.time() - self.total_start_time
        final_results = self._generate_final_report(total_time)

        console.print(Panel(
            f"✅ [bold green]Extraction Complete![/bold green]\n\n"
            f"⏱️ Total time: {total_time:.1f} seconds\n"
            f"📊 Phases completed: {len(self.completed_phases)}/{len(self.phases)}\n"
            f"📁 Results saved to: {self.output_dir}",
            title="🎉 Success",
            border_style="green"
        ))

        return final_results

    def _check_dependencies(self, phase: ExtractionPhase) -> bool:
        """Check if phase dependencies are satisfied."""
        if not phase.dependencies:
            return True

        for dep in phase.dependencies:
            if dep not in self.completed_phases:
                return False
        return True

    def _display_phase_info(self, phase: ExtractionPhase, current: int, total: int):
        """Display detailed information about the upcoming phase."""
        table = Table(title=f"📋 Phase {current}/{total}: {phase.name}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Description", phase.description)
        table.add_row("Expected Duration", phase.expected_duration)
        table.add_row("Output Files", ", ".join(phase.outputs))

        if phase.dependencies:
            table.add_row("Dependencies", ", ".join(phase.dependencies))

        console.print(table)

    def _execute_phase(self, phase: ExtractionPhase) -> ExtractionResults:
        """Execute a single extraction phase."""
        start_time = time.time()

        try:
            if phase.name == "Discovery":
                return self._phase_discovery()
            elif phase.name == "Parsing":
                return self._phase_parsing()
            elif phase.name == "Structuring":
                return self._phase_structuring()
            elif phase.name == "Enrichment":
                return self._phase_enrichment()
            elif phase.name == "Summarization":
                return self._phase_summarization()
            else:
                raise ValueError(f"Unknown phase: {phase.name}")

        except Exception as e:
            processing_time = time.time() - start_time
            return ExtractionResults(
                phase_name=phase.name,
                success=False,
                processing_time=processing_time,
                items_extracted=0,
                output_files=[],
                errors=[str(e)]
            )

    def _phase_discovery(self) -> ExtractionResults:
        """Phase 1: Discover chatlog format and extract metadata."""
        start_time = time.time()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Analyzing chatlog structure...", total=100)

            # Read and analyze file
            progress.update(task, advance=20, description="Reading chatlog file...")

            if not self.chatlog_path.exists():
                raise FileNotFoundError(f"Chatlog file not found: {self.chatlog_path}")

            with open(self.chatlog_path, 'r', encoding='utf-8') as f:
                content = f.read()

            progress.update(task, advance=30, description="Detecting format...")

            # Analyze structure
            lines = content.split('\n')
            file_size = len(content)
            line_count = len(lines)

            # Detect format patterns
            format_type = self._detect_format(content)

            progress.update(task, advance=20, description="Estimating message count...")

            # Estimate messages and extract basic info
            estimated_messages = self._estimate_message_count(content, format_type)
            participants = self._extract_participants(content, format_type)
            date_range = self._extract_date_range(content, format_type)

            progress.update(task, advance=30, description="Generating metadata...")

            # Create metadata
            metadata = ChatlogMetadata(
                file_path=str(self.chatlog_path),
                file_size=file_size,
                line_count=line_count,
                estimated_messages=estimated_messages,
                date_range=date_range,
                participants=participants
            )

            # Save metadata
            metadata_file = self.output_dir / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(asdict(metadata), f, indent=2)

            # Save format analysis
            format_file = self.output_dir / "format_analysis.txt"
            with open(format_file, 'w') as f:
                f.write(f"Chatlog Format Analysis\n")
                f.write(f"======================\n\n")
                f.write(f"File: {self.chatlog_path}\n")
                f.write(f"Size: {file_size:,} bytes\n")
                f.write(f"Lines: {line_count:,}\n")
                f.write(f"Detected format: {format_type}\n")
                f.write(f"Estimated messages: {estimated_messages:,}\n")
                f.write(f"Participants: {len(participants) if participants else 'Unknown'}\n")
                f.write(f"Date range: {date_range[0] if date_range else 'Unknown'} to {date_range[1] if date_range else 'Unknown'}\n")

        processing_time = time.time() - start_time

        return ExtractionResults(
            phase_name="Discovery",
            success=True,
            processing_time=processing_time,
            items_extracted=1,  # metadata file
            output_files=["metadata.json", "format_analysis.txt"],
            metadata=asdict(metadata)
        )

    def _phase_parsing(self) -> ExtractionResults:
        """Phase 2: Parse individual messages."""
        start_time = time.time()

        # Load metadata from previous phase
        metadata_file = self.output_dir / "metadata.json"
        if not metadata_file.exists():
            raise FileNotFoundError("Metadata from Discovery phase not found")

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Parsing messages...", total=metadata['estimated_messages'])

            # Read chatlog
            with open(self.chatlog_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse messages based on detected format
            messages = []
            participants = set()

            # This is a simplified parser - would be enhanced based on actual format
            lines = content.split('\n')
            current_msg = {"content": "", "timestamp": None, "author": None}

            for i, line in enumerate(lines):
                progress.update(task, completed=i)

                # Simple message detection (would be format-specific)
                if self._is_message_start(line):
                    # Save previous message
                    if current_msg["content"].strip():
                        messages.append(current_msg.copy())
                        if current_msg["author"]:
                            participants.add(current_msg["author"])

                    # Start new message
                    timestamp, author = self._extract_message_header(line)
                    current_msg = {
                        "id": len(messages),
                        "timestamp": timestamp,
                        "author": author,
                        "content": "",
                        "line_number": i + 1
                    }
                else:
                    current_msg["content"] += line + "\n"

            # Don't forget the last message
            if current_msg["content"].strip():
                messages.append(current_msg)
                if current_msg["author"]:
                    participants.add(current_msg["author"])

            progress.update(task, completed=metadata['estimated_messages'])

            # Save messages
            messages_file = self.output_dir / "messages.jsonl"
            with open(messages_file, 'w') as f:
                for msg in messages:
                    f.write(json.dumps(msg) + "\n")

            # Save participants
            participants_file = self.output_dir / "participants.json"
            with open(participants_file, 'w') as f:
                json.dump({
                    "participants": list(participants),
                    "count": len(participants)
                }, f, indent=2)

        processing_time = time.time() - start_time

        return ExtractionResults(
            phase_name="Parsing",
            success=True,
            processing_time=processing_time,
            items_extracted=len(messages),
            output_files=["messages.jsonl", "participants.json"],
            metadata={"message_count": len(messages), "participant_count": len(participants)}
        )

    def _phase_structuring(self) -> ExtractionResults:
        """Phase 3: Identify conversation threads and topics."""
        start_time = time.time()

        # Load messages from previous phase
        messages_file = self.output_dir / "messages.jsonl"
        if not messages_file.exists():
            raise FileNotFoundError("Messages from Parsing phase not found")

        messages = []
        with open(messages_file, 'r') as f:
            for line in f:
                messages.append(json.loads(line.strip()))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Analyzing conversation structure...", total=len(messages))

            # Simple thread detection (would be enhanced with NLP)
            threads = []
            topics = {}
            current_thread = []

            for i, msg in enumerate(messages):
                progress.update(task, completed=i)

                # Simple thread break detection
                if self._is_thread_break(msg, messages[i-1] if i > 0 else None):
                    if current_thread:
                        threads.append(current_thread.copy())
                        current_thread = []

                current_thread.append(msg["id"])

                # Extract topics (simplified keyword extraction)
                content_topics = self._extract_topics(msg["content"])
                for topic in content_topics:
                    if topic not in topics:
                        topics[topic] = []
                    topics[topic].append(msg["id"])

            # Don't forget the last thread
            if current_thread:
                threads.append(current_thread)

            progress.update(task, completed=len(messages))

            # Save threads
            threads_file = self.output_dir / "threads.json"
            with open(threads_file, 'w') as f:
                json.dump({
                    "threads": threads,
                    "thread_count": len(threads)
                }, f, indent=2)

            # Save topics
            topics_file = self.output_dir / "topics.json"
            with open(topics_file, 'w') as f:
                json.dump({
                    "topics": topics,
                    "topic_count": len(topics)
                }, f, indent=2)

        processing_time = time.time() - start_time

        return ExtractionResults(
            phase_name="Structuring",
            success=True,
            processing_time=processing_time,
            items_extracted=len(threads) + len(topics),
            output_files=["threads.json", "topics.json"],
            metadata={"thread_count": len(threads), "topic_count": len(topics)}
        )

    def _phase_enrichment(self) -> ExtractionResults:
        """Phase 4: Extract decisions, action items, and insights."""
        start_time = time.time()

        # Load messages
        messages_file = self.output_dir / "messages.jsonl"
        messages = []
        with open(messages_file, 'r') as f:
            for line in f:
                messages.append(json.loads(line.strip()))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Extracting insights...", total=len(messages))

            decisions = []
            action_items = []
            insights = []

            for i, msg in enumerate(messages):
                progress.update(task, completed=i)

                content = msg["content"].lower()

                # Extract decisions (pattern-based)
                if any(phrase in content for phrase in ["decided", "we'll", "let's", "agreed"]):
                    decisions.append({
                        "id": len(decisions),
                        "message_id": msg["id"],
                        "author": msg["author"],
                        "timestamp": msg["timestamp"],
                        "decision": msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
                    })

                # Extract action items
                if any(phrase in content for phrase in ["todo", "action", "need to", "should", "will"]):
                    action_items.append({
                        "id": len(action_items),
                        "message_id": msg["id"],
                        "author": msg["author"],
                        "timestamp": msg["timestamp"],
                        "action": msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
                    })

                # Extract insights (questions, important statements)
                if any(phrase in content for phrase in ["important", "key", "issue", "problem", "solution"]):
                    insights.append({
                        "id": len(insights),
                        "message_id": msg["id"],
                        "author": msg["author"],
                        "timestamp": msg["timestamp"],
                        "insight": msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
                    })

            progress.update(task, completed=len(messages))

            # Save extractions
            decisions_file = self.output_dir / "decisions.json"
            with open(decisions_file, 'w') as f:
                json.dump({"decisions": decisions, "count": len(decisions)}, f, indent=2)

            action_items_file = self.output_dir / "action_items.json"
            with open(action_items_file, 'w') as f:
                json.dump({"action_items": action_items, "count": len(action_items)}, f, indent=2)

            insights_file = self.output_dir / "insights.json"
            with open(insights_file, 'w') as f:
                json.dump({"insights": insights, "count": len(insights)}, f, indent=2)

        processing_time = time.time() - start_time

        return ExtractionResults(
            phase_name="Enrichment",
            success=True,
            processing_time=processing_time,
            items_extracted=len(decisions) + len(action_items) + len(insights),
            output_files=["decisions.json", "action_items.json", "insights.json"],
            metadata={
                "decision_count": len(decisions),
                "action_count": len(action_items),
                "insight_count": len(insights)
            }
        )

    def _phase_summarization(self) -> ExtractionResults:
        """Phase 5: Generate summaries and final report."""
        start_time = time.time()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating summary...", total=None)

            # Load all extracted data
            with open(self.output_dir / "metadata.json") as f:
                metadata = json.load(f)

            with open(self.output_dir / "participants.json") as f:
                participants = json.load(f)

            with open(self.output_dir / "threads.json") as f:
                threads = json.load(f)

            with open(self.output_dir / "topics.json") as f:
                topics = json.load(f)

            with open(self.output_dir / "decisions.json") as f:
                decisions = json.load(f)

            with open(self.output_dir / "action_items.json") as f:
                action_items = json.load(f)

            with open(self.output_dir / "insights.json") as f:
                insights = json.load(f)

            # Generate markdown summary
            summary_content = f"""# Chatlog Extraction Summary

## Overview
- **File**: {metadata['file_path']}
- **Processed**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Size**: {metadata['file_size']:,} bytes
- **Messages**: {self.phase_results.get('Parsing', ExtractionResults('Parsing', False, 0, 0, [])).metadata.get('message_count', 0) if self.phase_results.get('Parsing') and self.phase_results.get('Parsing').metadata else 0:,}
- **Participants**: {participants['count']}

## Participants
{chr(10).join(f'- {p}' for p in participants['participants'])}

## Conversation Structure
- **Threads**: {threads['thread_count']}
- **Topics**: {topics['topic_count']}

## Key Extractions
- **Decisions**: {decisions['count']}
- **Action Items**: {action_items['count']}
- **Insights**: {insights['count']}

## Top Topics
{chr(10).join(f'- **{topic}**: {len(msgs)} messages' for topic, msgs in list(topics['topics'].items())[:10])}

## Recent Decisions
{chr(10).join(f'- {d["decision"][:100]}...' for d in decisions['decisions'][:5])}

## Action Items
{chr(10).join(f'- {a["action"][:100]}...' for a in action_items['action_items'][:5])}

## Processing Summary
{chr(10).join(f'- **{phase}**: {result.processing_time:.1f}s ({result.items_extracted} items)' for phase, result in self.phase_results.items())}
"""

            # Save summary
            summary_file = self.output_dir / "summary.md"
            with open(summary_file, 'w') as f:
                f.write(summary_content)

            # Generate final extraction report
            report = {
                "extraction_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "total_processing_time": sum(r.processing_time for r in self.phase_results.values()),
                    "phases_completed": len(self.completed_phases),
                    "total_phases": len(self.phases)
                },
                "phase_results": {name: asdict(result) for name, result in self.phase_results.items()},
                "summary_stats": {
                    "file_size": metadata['file_size'],
                    "message_count": self.phase_results.get('Parsing').metadata.get('message_count', 0) if self.phase_results.get('Parsing') and self.phase_results.get('Parsing').metadata else 0,
                    "participant_count": participants['count'],
                    "thread_count": threads['thread_count'],
                    "topic_count": topics['topic_count'],
                    "decision_count": decisions['count'],
                    "action_count": action_items['count'],
                    "insight_count": insights['count']
                }
            }

            # Save report
            report_file = self.output_dir / "extraction_report.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)

        processing_time = time.time() - start_time

        return ExtractionResults(
            phase_name="Summarization",
            success=True,
            processing_time=processing_time,
            items_extracted=2,  # summary + report
            output_files=["summary.md", "extraction_report.json"]
        )

    def _display_phase_results(self, result: ExtractionResults):
        """Display the results of a completed phase."""
        status_color = "green" if result.success else "red"
        status_icon = "✅" if result.success else "❌"

        table = Table(title=f"{status_icon} Phase Results: {result.phase_name}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style=status_color)

        table.add_row("Success", "Yes" if result.success else "No")
        table.add_row("Processing Time", f"{result.processing_time:.1f} seconds")
        table.add_row("Items Extracted", str(result.items_extracted))
        table.add_row("Output Files", ", ".join(result.output_files))

        if result.errors:
            table.add_row("Errors", ", ".join(result.errors))

        if result.metadata:
            for key, value in result.metadata.items():
                table.add_row(key.replace('_', ' ').title(), str(value))

        console.print(table)

    def _generate_final_report(self, total_time: float) -> Dict[str, Any]:
        """Generate the final extraction report."""
        return {
            "success": True,
            "total_processing_time": total_time,
            "phases_completed": self.completed_phases,
            "phase_results": {name: asdict(result) for name, result in self.phase_results.items()},
            "output_directory": str(self.output_dir)
        }

    # Helper methods for format detection and parsing
    def _detect_format(self, content: str) -> str:
        """Detect the chatlog format."""
        # Simple format detection - would be enhanced
        if "[" in content and "]" in content:
            return "brackets"
        elif ":" in content:
            return "colon_separated"
        else:
            return "unknown"

    def _estimate_message_count(self, content: str, format_type: str) -> int:
        """Estimate the number of messages in the chatlog."""
        lines = content.split('\n')
        if format_type == "brackets":
            return len([line for line in lines if "[" in line and "]" in line])
        elif format_type == "colon_separated":
            return len([line for line in lines if ":" in line and len(line.strip()) > 0])
        else:
            return len([line for line in lines if len(line.strip()) > 0])

    def _extract_participants(self, content: str, format_type: str) -> List[str]:
        """Extract participant names from the chatlog."""
        participants = set()
        lines = content.split('\n')

        for line in lines[:100]:  # Sample first 100 lines
            if format_type == "brackets":
                match = re.search(r'\[([^\]]+)\]', line)
                if match:
                    participants.add(match.group(1))
            elif format_type == "colon_separated":
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        participants.add(parts[0].strip())

        return list(participants)[:20]  # Limit to 20 participants

    def _extract_date_range(self, content: str, format_type: str) -> Optional[Tuple[str, str]]:
        """Extract date range from the chatlog."""
        # Simple date extraction - would be enhanced
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', content)
        if dates:
            return (min(dates), max(dates))
        return None

    def _is_message_start(self, line: str) -> bool:
        """Determine if a line starts a new message."""
        # Simple detection - would be format-specific
        return bool(re.match(r'^[^:]+:', line) or re.match(r'^\[.+\]', line))

    def _extract_message_header(self, line: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract timestamp and author from message header."""
        # Simple extraction - would be enhanced
        if ":" in line:
            parts = line.split(":", 1)
            return None, parts[0].strip()
        return None, None

    def _is_thread_break(self, current_msg: Dict, previous_msg: Optional[Dict]) -> bool:
        """Determine if this message starts a new thread."""
        if not previous_msg:
            return True

        # Simple thread break detection
        if current_msg["author"] != previous_msg["author"]:
            return True

        return False

    def _extract_topics(self, content: str) -> List[str]:
        """Extract topics from message content."""
        # Simple keyword extraction
        words = re.findall(r'\b[A-Z][a-z]+\b', content)
        return list(set(words))[:10]  # Limit to 10 topics per message


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Phased Chatlog Extraction - ADHD-friendly step-by-step processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python chatlog_extractor.py chat.txt output/
  python chatlog_extractor.py --start-phase Parsing --auto-confirm chat.txt output/
  python chatlog_extractor.py --help
        """
    )

    parser.add_argument("chatlog", help="Path to the chatlog file")
    parser.add_argument("output_dir", help="Output directory for extracted data")
    parser.add_argument("--start-phase", choices=["Discovery", "Parsing", "Structuring", "Enrichment", "Summarization"],
                       default="Discovery", help="Phase to start from (for resuming)")
    parser.add_argument("--auto-confirm", action="store_true",
                       help="Skip user confirmation prompts (for automation)")

    args = parser.parse_args()

    try:
        extractor = ChatlogExtractor(args.chatlog, args.output_dir)
        results = extractor.run_extraction(args.start_phase, args.auto_confirm)

        if results["success"]:
            console.print("[bold green]🎉 Extraction completed successfully![/bold green]")
            return 0
        else:
            console.print(f"[red]❌ Extraction failed: {results.get('error', 'Unknown error')}[/red]")
            return 1

    except KeyboardInterrupt:
        console.print("\n[yellow]⏸️ Extraction interrupted by user[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())