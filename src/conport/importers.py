#!/usr/bin/env python3
"""
Memory Importers for Dopemux

Imports conversation histories from Claude Code and Codex CLI into the unified memory graph.
Normalizes different tool outputs into consistent JSONL format for ConPort ingestion.
"""

import json
import logging
import re
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Generator, List, Optional, Any
import hashlib

import asyncpg
import asyncio


logger = logging.getLogger("conport.importers")


class ConPortImporter:
    """Base class for importing data into ConPort memory system."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Connect to ConPort database."""
        self.pool = await asyncpg.create_pool(self.database_url)

    async def start_import_run(self, source: str, file_path: str, total_items: Optional[int] = None) -> str:
        """Start a new import run and return the run ID."""
        run_id = str(uuid.uuid4())
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO import_runs (id, source, file_path, items_total, started_at)
                VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
            """, run_id, source, file_path, total_items)
        return run_id

    async def update_import_progress(self, run_id: str, processed: int, error: Optional[str] = None):
        """Update import run progress."""
        async with self.pool.acquire() as conn:
            if error:
                await conn.execute("""
                    UPDATE import_runs
                    SET items_processed = $2, status = 'failed', error_message = $3, completed_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                """, run_id, processed, error)
            else:
                await conn.execute("""
                    UPDATE import_runs
                    SET items_processed = $2
                    WHERE id = $1
                """, run_id, processed)

    async def complete_import_run(self, run_id: str, processed: int):
        """Mark import run as completed."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE import_runs
                SET items_processed = $2, status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, run_id, processed)

    async def upsert_node(self, node_data: Dict[str, Any]) -> bool:
        """Upsert a node directly to PostgreSQL."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO nodes (id, type, text, metadata, repo, author, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP)
                    ON CONFLICT (id) DO UPDATE SET
                        type = EXCLUDED.type,
                        text = EXCLUDED.text,
                        metadata = EXCLUDED.metadata,
                        repo = EXCLUDED.repo,
                        author = EXCLUDED.author,
                        updated_at = CURRENT_TIMESTAMP
                """,
                node_data["id"],
                node_data["type"],
                node_data["text"],
                json.dumps(node_data.get("metadata", {})),
                node_data.get("repo"),
                node_data.get("author"),
                node_data.get("created_at", datetime.now())
                )
            return True
        except Exception as e:
            logger.error(f"Failed to upsert node {node_data['id']}: {e}")
            return False

    async def create_thread(self, thread_id: str, title: str, repo: str, participants: List[str]):
        """Create a conversation thread."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO conversation_threads (id, title, repo, participants, created_at, updated_at)
                VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    repo = EXCLUDED.repo,
                    participants = EXCLUDED.participants,
                    updated_at = CURRENT_TIMESTAMP
            """, thread_id, title, repo, participants)

    async def upsert_message(self, message_data: Dict[str, Any]) -> bool:
        """Upsert a message to PostgreSQL."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO messages (id, thread_id, role, content, tool_calls, metadata, source, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (id) DO UPDATE SET
                        thread_id = EXCLUDED.thread_id,
                        role = EXCLUDED.role,
                        content = EXCLUDED.content,
                        tool_calls = EXCLUDED.tool_calls,
                        metadata = EXCLUDED.metadata,
                        source = EXCLUDED.source
                """,
                message_data["id"],
                message_data["thread_id"],
                message_data["role"],
                message_data["content"],
                json.dumps(message_data.get("tool_calls")),
                json.dumps(message_data.get("metadata", {})),
                message_data["source"],
                message_data.get("created_at", datetime.now())
                )
            return True
        except Exception as e:
            logger.error(f"Failed to upsert message {message_data['id']}: {e}")
            return False


class ClaudeCodeImporter(ConPortImporter):
    """Imports Claude Code conversation histories."""

    def __init__(self, database_url: str):
        super().__init__(database_url)

    def parse_claude_code_logs(self, log_path: Path) -> Generator[Dict[str, Any], None, None]:
        """Parse Claude Code logs into normalized format."""
        try:
            # Claude Code typically stores conversations in SQLite
            if log_path.suffix == '.db':
                yield from self._parse_sqlite_logs(log_path)
            elif log_path.suffix == '.jsonl':
                yield from self._parse_jsonl_logs(log_path)
            else:
                logger.warning(f"Unsupported Claude Code log format: {log_path.suffix}")
        except Exception as e:
            logger.error(f"Failed to parse Claude Code logs: {e}")

    def _parse_sqlite_logs(self, db_path: Path) -> Generator[Dict[str, Any], None, None]:
        """Parse SQLite Claude Code conversation database."""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        try:
            # Get conversations
            conversations = conn.execute("""
                SELECT id, title, created_at, metadata
                FROM conversations
                ORDER BY created_at
            """).fetchall()

            for conv in conversations:
                conv_id = f"claude-code-{conv['id']}"

                # Yield thread creation
                yield {
                    "type": "thread",
                    "id": conv_id,
                    "title": conv["title"] or "Claude Code Session",
                    "source": "claude-code",
                    "created_at": datetime.fromisoformat(conv["created_at"]) if conv["created_at"] else datetime.now(),
                    "metadata": json.loads(conv["metadata"]) if conv["metadata"] else {}
                }

                # Get messages for this conversation
                messages = conn.execute("""
                    SELECT id, role, content, tool_calls, created_at, metadata
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY created_at
                """, (conv['id'],)).fetchall()

                for msg in messages:
                    msg_id = f"claude-code-msg-{msg['id']}"

                    # Extract text content
                    content = msg["content"] or ""
                    if isinstance(content, str):
                        try:
                            content_obj = json.loads(content)
                            if isinstance(content_obj, list):
                                content = " ".join([item.get("text", "") for item in content_obj if item.get("type") == "text"])
                        except json.JSONDecodeError:
                            pass  # content is already a string

                    yield {
                        "type": "message",
                        "id": msg_id,
                        "thread_id": conv_id,
                        "role": msg["role"],
                        "content": content,
                        "tool_calls": json.loads(msg["tool_calls"]) if msg["tool_calls"] else None,
                        "source": "claude-code",
                        "created_at": datetime.fromisoformat(msg["created_at"]) if msg["created_at"] else datetime.now(),
                        "metadata": json.loads(msg["metadata"]) if msg["metadata"] else {}
                    }

        finally:
            conn.close()

    def _parse_jsonl_logs(self, jsonl_path: Path) -> Generator[Dict[str, Any], None, None]:
        """Parse JSONL Claude Code logs."""
        with open(jsonl_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())

                    # Convert to normalized format
                    if data.get("type") == "conversation":
                        yield {
                            "type": "thread",
                            "id": f"claude-code-{data['id']}",
                            "title": data.get("title", "Claude Code Session"),
                            "source": "claude-code",
                            "created_at": datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
                            "metadata": data.get("metadata", {})
                        }
                    elif data.get("type") == "message":
                        yield {
                            "type": "message",
                            "id": f"claude-code-msg-{data['id']}",
                            "thread_id": f"claude-code-{data['conversation_id']}",
                            "role": data["role"],
                            "content": data["content"],
                            "tool_calls": data.get("tool_calls"),
                            "source": "claude-code",
                            "created_at": datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
                            "metadata": data.get("metadata", {})
                        }

                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
                except Exception as e:
                    logger.error(f"Error processing line {line_num}: {e}")

    async def import_claude_code_history(self, log_path: Path, repo: str = "unknown") -> bool:
        """Import Claude Code conversation history."""
        logger.info(f"Starting Claude Code import from {log_path}")

        run_id = await self.start_import_run("claude-code", str(log_path))
        processed = 0

        try:
            threads_created = set()

            for item in self.parse_claude_code_logs(log_path):
                if item["type"] == "thread":
                    # Create conversation thread
                    await self.create_thread(
                        item["id"],
                        item["title"],
                        repo,
                        ["user", "assistant"]
                    )
                    threads_created.add(item["id"])

                    # Also create as a node for graph traversal
                    await self.upsert_node({
                        "id": item["id"],
                        "type": "thread",
                        "text": item["title"],
                        "repo": repo,
                        "author": "claude-code",
                        "metadata": item["metadata"],
                        "created_at": item["created_at"]
                    })

                elif item["type"] == "message":
                    # Ensure thread exists
                    if item["thread_id"] not in threads_created:
                        await self.create_thread(
                            item["thread_id"],
                            "Claude Code Session",
                            repo,
                            ["user", "assistant"]
                        )
                        threads_created.add(item["thread_id"])

                    # Store message
                    await self.upsert_message(item)

                    # Also create as node for semantic search
                    await self.upsert_node({
                        "id": item["id"],
                        "type": "message",
                        "text": item["content"][:1000],  # Limit text length
                        "repo": repo,
                        "author": item["role"],
                        "metadata": {
                            "thread_id": item["thread_id"],
                            "role": item["role"],
                            "tool_calls": item.get("tool_calls"),
                            **item.get("metadata", {})
                        },
                        "created_at": item["created_at"]
                    })

                processed += 1
                if processed % 100 == 0:
                    await self.update_import_progress(run_id, processed)
                    logger.info(f"Processed {processed} items...")

            await self.complete_import_run(run_id, processed)
            logger.info(f"Claude Code import completed: {processed} items processed")
            return True

        except Exception as e:
            await self.update_import_progress(run_id, processed, str(e))
            logger.error(f"Claude Code import failed: {e}")
            return False


class CodexCLIImporter(ConPortImporter):
    """Imports Codex CLI command histories."""

    def __init__(self, database_url: str):
        super().__init__(database_url)

    def parse_codex_history(self, history_path: Path) -> Generator[Dict[str, Any], None, None]:
        """Parse Codex CLI history files."""
        try:
            if history_path.suffix == '.jsonl':
                yield from self._parse_jsonl_history(history_path)
            elif history_path.suffix == '.log':
                yield from self._parse_log_history(history_path)
            else:
                logger.warning(f"Unsupported Codex history format: {history_path.suffix}")
        except Exception as e:
            logger.error(f"Failed to parse Codex history: {e}")

    def _parse_jsonl_history(self, jsonl_path: Path) -> Generator[Dict[str, Any], None, None]:
        """Parse JSONL Codex CLI history."""
        with open(jsonl_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())

                    if data.get("type") == "command":
                        cmd_id = f"codex-cmd-{hashlib.md5(f'{data.get('timestamp', line_num)}-{data.get('command', '')}'.encode()).hexdigest()[:12]}"

                        yield {
                            "type": "run",
                            "id": cmd_id,
                            "command": data["command"],
                            "output": data.get("output", ""),
                            "exit_code": data.get("exit_code", 0),
                            "working_dir": data.get("working_dir", ""),
                            "source": "codex-cli",
                            "created_at": datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
                            "metadata": {
                                "duration": data.get("duration"),
                                "environment": data.get("environment", {}),
                                "exit_code": data.get("exit_code", 0)
                            }
                        }

                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
                except Exception as e:
                    logger.error(f"Error processing line {line_num}: {e}")

    def _parse_log_history(self, log_path: Path) -> Generator[Dict[str, Any], None, None]:
        """Parse plain text Codex CLI history logs."""
        command_pattern = re.compile(r'^\[([^\]]+)\] \$ (.+)$')
        output_pattern = re.compile(r'^\[([^\]]+)\] (.+)$')

        with open(log_path, 'r') as f:
            current_command = None
            output_lines = []

            for line_num, line in enumerate(f, 1):
                line = line.rstrip()

                # Check if this is a command line
                cmd_match = command_pattern.match(line)
                if cmd_match:
                    # Yield previous command if exists
                    if current_command:
                        cmd_id = f"codex-cmd-{hashlib.md5(f'{current_command['timestamp']}-{current_command['command']}'.encode()).hexdigest()[:12]}"
                        yield {
                            "type": "run",
                            "id": cmd_id,
                            "command": current_command["command"],
                            "output": "\n".join(output_lines),
                            "source": "codex-cli",
                            "created_at": current_command["timestamp"],
                            "metadata": {"line_number": current_command["line_num"]}
                        }

                    # Start new command
                    timestamp_str, command = cmd_match.groups()
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str)
                    except ValueError:
                        timestamp = datetime.now()

                    current_command = {
                        "command": command,
                        "timestamp": timestamp,
                        "line_num": line_num
                    }
                    output_lines = []

                # Check if this is output
                elif current_command:
                    output_match = output_pattern.match(line)
                    if output_match:
                        output_lines.append(output_match.group(2))

            # Yield final command
            if current_command:
                cmd_id = f"codex-cmd-{hashlib.md5(f'{current_command['timestamp']}-{current_command['command']}'.encode()).hexdigest()[:12]}"
                yield {
                    "type": "run",
                    "id": cmd_id,
                    "command": current_command["command"],
                    "output": "\n".join(output_lines),
                    "source": "codex-cli",
                    "created_at": current_command["timestamp"],
                    "metadata": {"line_number": current_command["line_num"]}
                }

    async def import_codex_history(self, history_path: Path, repo: str = "unknown") -> bool:
        """Import Codex CLI command history."""
        logger.info(f"Starting Codex CLI import from {history_path}")

        run_id = await self.start_import_run("codex-cli", str(history_path))
        processed = 0

        try:
            for item in self.parse_codex_history(history_path):
                if item["type"] == "run":
                    # Create run node for semantic search
                    text = f"Command: {item['command']}"
                    if item.get('output'):
                        text += f"\nOutput: {item['output'][:500]}"  # Limit output length

                    await self.upsert_node({
                        "id": item["id"],
                        "type": "run",
                        "text": text,
                        "repo": repo,
                        "author": "codex-cli",
                        "metadata": {
                            "command": item["command"],
                            "output": item.get("output", ""),
                            "exit_code": item.get("exit_code"),
                            "working_dir": item.get("working_dir"),
                            **item.get("metadata", {})
                        },
                        "created_at": item["created_at"]
                    })

                processed += 1
                if processed % 50 == 0:
                    await self.update_import_progress(run_id, processed)
                    logger.info(f"Processed {processed} commands...")

            await self.complete_import_run(run_id, processed)
            logger.info(f"Codex CLI import completed: {processed} items processed")
            return True

        except Exception as e:
            await self.update_import_progress(run_id, processed, str(e))
            logger.error(f"Codex CLI import failed: {e}")
            return False


async def main():
    """CLI for running importers."""
    import argparse

    parser = argparse.ArgumentParser(description="Import conversation histories into ConPort memory system")
    parser.add_argument("--database-url", required=True, help="PostgreSQL database URL")
    parser.add_argument("--source", choices=["claude-code", "codex-cli"], required=True, help="Source type")
    parser.add_argument("--file", required=True, help="Path to history file")
    parser.add_argument("--repo", default="unknown", help="Repository name")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    file_path = Path(args.file)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return 1

    try:
        if args.source == "claude-code":
            importer = ClaudeCodeImporter(args.database_url)
            await importer.connect()
            success = await importer.import_claude_code_history(file_path, args.repo)
        elif args.source == "codex-cli":
            importer = CodexCLIImporter(args.database_url)
            await importer.connect()
            success = await importer.import_codex_history(file_path, args.repo)
        else:
            logger.error(f"Unsupported source: {args.source}")
            return 1

        return 0 if success else 1

    except Exception as e:
        logger.error(f"Import failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))