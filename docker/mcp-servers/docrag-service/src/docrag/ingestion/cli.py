"""
CLI tool for document ingestion.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import List

import structlog

from ..config import get_config
from ..models import IngestionRequest
from ..service import DocRAGService

logger = structlog.get_logger(__name__)


async def ingest_single_document(
    service: DocRAGService,
    file_path: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
    force_reindex: bool = False,
    metadata: dict = None,
) -> None:
    """Ingest a single document."""
    request = IngestionRequest(
        source_path=file_path,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        force_reindex=force_reindex,
        metadata=metadata or {},
    )

    try:
        response = await service.ingest_document(request)

        if response.success:
            print(f"✅ Successfully ingested {file_path}")
            print(f"   Chunks created: {response.chunks_created}")
            print(f"   Processing time: {response.processing_time_ms:.1f}ms")
        else:
            print(f"❌ Failed to ingest {file_path}: {response.message}")

    except Exception as e:
        print(f"❌ Error ingesting {file_path}: {str(e)}")


async def ingest_directory(
    service: DocRAGService,
    directory: str,
    recursive: bool = True,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
    force_reindex: bool = False,
    patterns: List[str] = None,
) -> None:
    """Ingest all documents in a directory."""
    config = get_config()
    allowed_extensions = set(config.security.allowed_extensions)

    dir_path = Path(directory)
    if not dir_path.exists():
        print(f"❌ Directory not found: {directory}")
        return

    # Find files to ingest
    files_to_ingest = []

    if recursive:
        for file_path in dir_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in allowed_extensions:
                files_to_ingest.append(file_path)
    else:
        for file_path in dir_path.glob("*"):
            if file_path.is_file() and file_path.suffix.lower() in allowed_extensions:
                files_to_ingest.append(file_path)

    if not files_to_ingest:
        print(f"❌ No supported files found in {directory}")
        return

    print(f"📁 Found {len(files_to_ingest)} files to ingest")

    # Ingest files
    success_count = 0
    for file_path in files_to_ingest:
        try:
            await ingest_single_document(
                service=service,
                file_path=str(file_path),
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                force_reindex=force_reindex,
            )
            success_count += 1

        except Exception as e:
            print(f"❌ Error processing {file_path}: {str(e)}")

    print(f"\\n📊 Ingestion complete: {success_count}/{len(files_to_ingest)} files successful")


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DocRAG document ingestion CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest a single document
  docrag-ingest file.pdf

  # Ingest a directory recursively
  docrag-ingest --directory /path/to/docs

  # Ingest with custom chunk settings
  docrag-ingest file.pdf --chunk-size 1500 --chunk-overlap 150

  # Force reindex existing documents
  docrag-ingest --directory /docs --force-reindex

  # Add custom metadata
  docrag-ingest file.pdf --metadata '{"team": "engineering", "project": "api-docs"}'
        """,
    )

    # Input options
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("file", nargs="?", help="Single file to ingest")
    group.add_argument("--directory", "-d", help="Directory to ingest recursively")

    # Processing options
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Chunk size in characters (default: 1000)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=100,
        help="Chunk overlap in characters (default: 100)",
    )
    parser.add_argument(
        "--force-reindex",
        action="store_true",
        help="Force reindexing of existing documents",
    )
    parser.add_argument(
        "--metadata",
        type=str,
        help="Additional metadata as JSON string",
    )

    # Directory options
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Don't process directory recursively",
    )

    args = parser.parse_args()

    # Parse metadata
    metadata = {}
    if args.metadata:
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError:
            print("❌ Invalid JSON in metadata argument")
            sys.exit(1)

    # Validate chunk settings
    if args.chunk_size < 100 or args.chunk_size > 2000:
        print("❌ Chunk size must be between 100 and 2000")
        sys.exit(1)

    if args.chunk_overlap >= args.chunk_size:
        print("❌ Chunk overlap must be less than chunk size")
        sys.exit(1)

    # Initialize service
    config = get_config()
    service = DocRAGService(config)

    try:
        await service.initialize()
        print("🚀 DocRAG service initialized")

        # Check health
        health = await service.get_health_status()
        if health.status != "healthy":
            print(f"⚠️  Service health: {health.status}")
            if not health.milvus_connected:
                print("❌ Milvus not connected")
                sys.exit(1)

        # Perform ingestion
        if args.file:
            await ingest_single_document(
                service=service,
                file_path=args.file,
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap,
                force_reindex=args.force_reindex,
                metadata=metadata,
            )
        else:
            await ingest_directory(
                service=service,
                directory=args.directory,
                recursive=not args.no_recursive,
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap,
                force_reindex=args.force_reindex,
            )

    except KeyboardInterrupt:
        print("\\n🛑 Ingestion cancelled")
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        sys.exit(1)
    finally:
        await service.shutdown()


def cli_main():
    """Entry point for CLI script."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()