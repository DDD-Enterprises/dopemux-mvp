#!/usr/bin/env python3
import argparse
import asyncio
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doc_processor import DocumentProcessor


def main():
    parser = argparse.ArgumentParser(description="Run Dopemux doc processing pipeline")
    parser.add_argument("--input", required=True, help="Input directory to process")
    parser.add_argument("--output", required=True, help="Output directory for results")
    parser.add_argument("--max", type=int, default=None, help="Optional max files to process")
    args = parser.parse_args()

    docs_dir = Path(args.input)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Skip embeddings for speed and sandbox friendliness
    dp = DocumentProcessor(
        docs_directory=str(docs_dir),
        output_directory=str(out_dir),
        skip_embeddings=True,
        max_files=args.max
    )

    results = asyncio.run(dp.process_all_documents())

    # Save a summary file
    summary_path = out_dir / "processing_summary.json"
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)

    print("\n=== Processing Summary ===")
    for k, v in results.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
