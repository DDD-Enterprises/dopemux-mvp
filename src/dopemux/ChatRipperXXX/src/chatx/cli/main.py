"""Main CLI entry point for ChatX."""

import logging
from pathlib import Path
from datetime import datetime

import typer
from rich.console import Console

from chatx.utils.logging import setup_logging
from chatx import __version__ as CHATX_VERSION

app = typer.Typer(
    name="chatx",
    help=(
        "Privacy-focused, local-first CLI for chat analysis.\n\n"
        "Examples:\n"
        "  chatx imessage pull --contact \"+15551234567\" --out ./out\n"
        "  chatx imessage pull --contact \"+15551234567\" \\\n+          --from-backup \"~/Library/Application Support/MobileSync/Backup/<UDID>\" --out ./out\n"
        "  chatx instagram pull --zip ./instagram.zip --user \"Your Name\" --out ./out\n"
        "  chatx imessage audit --db ~/Library/Messages/chat.db --out ./out\n"
        "  chatx imessage pdf --pdf ./conversation.pdf --me \"Your Name\" --out ./out\n"
    ),
    add_completion=False,
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"chatx {CHATX_VERSION}")
        raise typer.Exit()


@app.callback()
def main(
    verbose: int = typer.Option(0, "--verbose", "-v", count=True, help="Increase verbosity", rich_help_panel="Global"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress output", rich_help_panel="Global"),
    config: str = typer.Option("", "--config", "-c", help="Configuration file path", rich_help_panel="Global"),
    version: bool = typer.Option(False, "--version", callback=_version_callback, is_eager=True, help="Show version and exit", rich_help_panel="Global"),
) -> None:
    """ChatX - Privacy-focused chat analysis tool."""
    # Set up logging based on verbosity
    log_level = logging.WARNING
    if not quiet:
        if verbose == 1:
            log_level = logging.INFO
        elif verbose >= 2:
            log_level = logging.DEBUG

    setup_logging(log_level)

    # TODO: Fix config parameter bug - currently prints Option object instead of value
    # if config:
    #     console.print(f"Using config: {config}")


@app.command()
def extract(
    source: Path = typer.Argument(..., help="Source path (e.g., iMessage chat.db)"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output directory"),
    platform: str | None = typer.Option(None, "--platform", "-p", help="Platform type"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be extracted"),
    error_format: str = typer.Option("text", "--error-format", help="Error output format (text|json)"),
) -> None:
    """Extract chat data from various platforms.
    
    Supported platforms:
    - imessage: macOS/iOS iMessage (chat.db)
    - instagram: Instagram Direct Messages
    - whatsapp: WhatsApp export files
    - txt: Plain text conversation files
    """
    console.print(f"[bold green]Extracting from:[/bold green] {source}")

    if not source.exists():
        if error_format == "json":
            from chatx.cli_errors import emit_problem
            emit_problem(
                code="INVALID_INPUT",
                title="Source path not found",
                status=1,
                detail=f"Path does not exist: {source}",
                instance=str(source),
            )
        else:
            console.print(f"[bold red]Error:[/bold red] Source path does not exist: {source}")
        raise typer.Exit(1)

    if dry_run:
        console.print("[yellow]Dry run mode - no files will be created[/yellow]")

    # TODO: Implement actual extraction logic
    console.print("[yellow]Extraction not yet implemented[/yellow]")


@app.command()
def transform(
    input_file: Path = typer.Argument(..., help="Input file containing messages (JSON/JSONL)"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
    format_type: str = typer.Option("jsonl", "--format", help="Output format (json, jsonl)"),
    method: str = typer.Option("turns", "--chunk", help="Chunking method (turns, daily, fixed)"),
    contact: str = typer.Option("unknown", "--contact", help="Contact identifier"),
    turns_per_chunk: int = typer.Option(40, "--turns", help="Messages per chunk (turns method)"),
    stride: int = typer.Option(10, "--stride", help="Overlap between chunks (turns method)"),
    char_limit: int = typer.Option(4000, "--char-limit", help="Character limit (fixed method)"),
    validate_schemas: bool = typer.Option(True, "--validate/--no-validate", help="Validate against schemas"),
    error_format: str = typer.Option("text", "--error-format", help="Error output format (text|json)"),
) -> None:
    """Transform extracted messages into conversation chunks.
    
    Examples:
        chatx transform messages.json --contact "friend@example.com" --chunk turns --turns 40 --stride 10
        chatx transform messages.jsonl --chunk daily --contact "+15551234567"
        chatx transform messages.json --chunk fixed --char-limit 3000
    """
    from datetime import datetime
    import json
    from chatx.schemas.message import CanonicalMessage
    from chatx.transformers.pipeline import TransformationPipeline
    from chatx.transformers.chunker import ChunkMethod
    
    console.print(f"[bold green]Transforming:[/bold green] {input_file}")

    if not input_file.exists():
        if error_format == "json":
            from chatx.cli_errors import emit_problem
            emit_problem(
                code="INVALID_INPUT",
                title="Input file not found",
                status=1,
                detail=f"Path does not exist: {input_file}",
                instance=str(input_file),
            )
        else:
            console.print(f"[bold red]Error:[/bold red] Input file does not exist: {input_file}")
        raise typer.Exit(1)

    if method not in ["turns", "daily", "fixed"]:
        if error_format == "json":
            from chatx.cli_errors import emit_problem
            emit_problem(
                code="INVALID_INPUT",
                title="Invalid chunking method",
                status=1,
                detail="Valid methods: turns, daily, fixed",
                instance=method,
            )
        else:
            console.print(f"[bold red]Error:[/bold red] Invalid chunking method: {method}")
            console.print("[blue]Valid methods:[/blue] turns, daily, fixed")
        raise typer.Exit(1)

    try:
        started_at = datetime.now()
        
        # Load messages
        console.print(f"[blue]Loading messages from:[/blue] {input_file}")
        with open(input_file) as f:
            if input_file.suffix == ".jsonl":
                messages_data = [json.loads(line) for line in f if line.strip()]
            else:
                messages_data = json.load(f)
        
        # Convert to CanonicalMessage objects
        messages = [CanonicalMessage(**msg_data) for msg_data in messages_data]
        console.print(f"[blue]Loaded {len(messages)} messages[/blue]")
        
        # Initialize pipeline
        output_dir = output.parent if output else input_file.parent / "out"
        pipeline = TransformationPipeline(
            output_dir=output_dir,
            validate_schemas=validate_schemas,
        )
        
        # Set method-specific parameters
        chunk_params = {}
        if method == "turns":
            chunk_params["turns_per_chunk"] = turns_per_chunk
            chunk_params["stride"] = stride
        elif method == "fixed":
            chunk_params["char_limit"] = char_limit
        
        # Run transformation
        console.print(f"[blue]Chunking method:[/blue] {method}")
        console.print(f"[blue]Contact:[/blue] {contact}")
        if chunk_params:
            param_str = ", ".join(f"{k}={v}" for k, v in chunk_params.items())
            console.print(f"[blue]Parameters:[/blue] {param_str}")
        
        chunks, output_path = pipeline.transform(
            messages=messages,
            method=ChunkMethod(method),
            contact=contact,
            format_type=format_type,
            output_file=output,
            **chunk_params,
        )
        
        finished_at = datetime.now()
        elapsed = (finished_at - started_at).total_seconds()
        
        console.print(f"[bold green]Created {len(chunks)} chunks[/bold green]")
        console.print(f"[bold green]Output saved to:[/bold green] {output_path}")
        console.print(f"[blue]Processing time:[/blue] {elapsed:.2f}s")
        
        # Show chunk statistics
        if chunks:
            total_chars = sum(len(chunk.text) for chunk in chunks)
            avg_chars = total_chars // len(chunks)
            
            date_range = f"{chunks[0].meta.date_start.date()} to {chunks[-1].meta.date_end.date()}"
            console.print(f"[blue]Date range:[/blue] {date_range}")
            console.print(f"[blue]Average chunk size:[/blue] {avg_chars} characters")
            console.print(f"[blue]Total messages processed:[/blue] {sum(len(c.meta.message_ids) for c in chunks)}")
        
    except Exception as e:
        console.print(f"[bold red]Error during transformation:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def redact(
    input_file: Path = typer.Argument(..., help="Input file containing chunks to redact"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
    salt_file: Path | None = typer.Option(None, "--salt-file", help="Salt file for consistent tokenization"),
    threshold: float = typer.Option(0.995, "--threshold", help="Redaction coverage threshold (0.0-1.0)"),
    strict: bool = typer.Option(False, "--strict", help="Enable strict mode (99.9% threshold)"),
    pseudonymize: bool = typer.Option(True, "--pseudonymize/--no-pseudonymize", help="Use consistent pseudonymization"),
    detect_names: bool = typer.Option(True, "--detect-names/--no-detect-names", help="Detect common names as PII"),
    report_file: Path | None = typer.Option(None, "--report", help="Redaction report output file"),
    preflight: bool = typer.Option(False, "--preflight", help="Run preflight check for cloud readiness"),
) -> None:
    """Apply privacy redaction using Policy Shield.
    
    Examples:
        chatx redact chunks.jsonl --threshold 0.995 --salt-file ./salt.key
        chatx redact chunks.json --strict --preflight --report ./redaction_report.json
        chatx redact chunks.jsonl --no-pseudonymize --threshold 0.999
    """
    from datetime import datetime
    import json
    from chatx.redaction.policy_shield import PolicyShield, PrivacyPolicy
    
    console.print(f"[bold green]Redacting:[/bold green] {input_file}")

    if not input_file.exists():
        console.print(f"[bold red]Error:[/bold red] Input file does not exist: {input_file}")
        raise typer.Exit(1)

    if strict:
        console.print("[blue]Using strict redaction mode (99.9% threshold)[/blue]")
    else:
        console.print(f"[blue]Coverage threshold:[/blue] {threshold:.1%}")

    try:
        started_at = datetime.now()
        
        # Load chunks
        console.print(f"[blue]Loading chunks from:[/blue] {input_file}")
        with open(input_file) as f:
            if input_file.suffix == ".jsonl":
                chunks = [json.loads(line) for line in f if line.strip()]
            else:
                chunks = json.load(f)
        
        console.print(f"[blue]Loaded {len(chunks)} chunks[/blue]")
        
        # Create privacy policy
        policy = PrivacyPolicy(
            threshold=threshold,
            strict_mode=strict,
            pseudonymize=pseudonymize,
            detect_names=detect_names,
        )
        
        # Initialize Policy Shield
        shield = PolicyShield(policy=policy, salt_file=salt_file)
        
        # Redact chunks
        console.print("[blue]Starting redaction...[/blue]")
        redacted_chunks, redaction_report = shield.redact_chunks(chunks)
        
        finished_at = datetime.now()
        elapsed = (finished_at - started_at).total_seconds()
        
        # Show results
        console.print("[bold green]Redaction complete![/bold green]")
        console.print(f"[blue]Coverage achieved:[/blue] {redaction_report.coverage:.1%}")
        console.print(f"[blue]Tokens redacted:[/blue] {redaction_report.tokens_redacted}")
        console.print(f"[blue]Processing time:[/blue] {elapsed:.2f}s")
        
        # Show PII type breakdown
        if redaction_report.placeholders:
            pii_summary = ", ".join(f"{k}: {v}" for k, v in redaction_report.placeholders.items())
            console.print(f"[blue]PII types found:[/blue] {pii_summary}")
        
        # Check threshold
        effective_threshold = policy.get_effective_threshold()
        if redaction_report.coverage >= effective_threshold:
            console.print(f"[green]✓ Coverage meets {effective_threshold:.1%} threshold[/green]")
        else:
            console.print(f"[yellow]⚠ Coverage below {effective_threshold:.1%} threshold[/yellow]")
        
        # Check hard-fail
        if redaction_report.hardfail_triggered:
            console.print("[red]⚠ Hard-fail classes detected[/red]")
        
        # Save redacted chunks
        if not output:
            timestamp = started_at.strftime("%Y%m%d_%H%M%S")
            output = input_file.parent / f"redacted_{input_file.stem}_{timestamp}{input_file.suffix}"
        
        output.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output, "w") as f:
            if output.suffix == ".jsonl":
                for chunk in redacted_chunks:
                    f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
            else:
                json.dump(redacted_chunks, f, indent=2, ensure_ascii=False)
        
        console.print(f"[bold green]Redacted chunks saved to:[/bold green] {output}")
        
        # Save redaction report
        if not report_file:
            report_file = output.parent / "redaction_report.json"
        
        shield.save_redaction_report(redaction_report, report_file)
        console.print(f"[blue]Redaction report saved to:[/blue] {report_file}")
        
        # Show tokenizer statistics
        tokenizer_stats = shield.get_tokenizer_stats()
        console.print(f"[blue]Tokenizer stats:[/blue] {tokenizer_stats['total_tokens']} unique tokens")
        
        # Run preflight check if requested
        if preflight:
            console.print("[blue]Running preflight check for cloud readiness...[/blue]")
            passed, issues = shield.preflight_cloud_check(redacted_chunks, redaction_report)
            
            if passed:
                console.print("[green]✓ Preflight check passed - ready for cloud processing[/green]")
            else:
                console.print("[red]✗ Preflight check failed[/red]")
                for issue in issues:
                    console.print(f"[red]  - {issue}[/red]")
                
                if redaction_report.hardfail_triggered or redaction_report.coverage < effective_threshold:
                    console.print("[red]Cloud processing blocked due to policy violations[/red]")
                    raise typer.Exit(1)
        
        # Show warnings
        if redaction_report.notes:
            console.print("[yellow]Warnings:[/yellow]")
            for note in redaction_report.notes[:3]:  # Show first 3 warnings
                console.print(f"[yellow]  - {note}[/yellow]")
            if len(redaction_report.notes) > 3:
                console.print(f"[yellow]  ... and {len(redaction_report.notes) - 3} more warnings[/yellow]")
        
    except Exception as e:
        console.print(f"[bold red]Error during redaction:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def enrich(
    input_file: Path = typer.Argument(..., help="Input file containing redacted chunks"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
    contact: str = typer.Option("unknown", "--contact", help="Contact identifier"),
    backend: str = typer.Option("local", "--backend", help="Enrichment backend (local, cloud, hybrid)"),
    model: str = typer.Option(
        "gemma2:9b-instruct-q4_K_M", "--model", help="Ollama model to use"
    ),
    tau: float = typer.Option(0.7, "--tau", help="Primary confidence threshold (0.0-1.0)"),
    tau_low: float = typer.Option(0.62, "--tau-low", help="Hysteresis low threshold"),
    tau_high: float = typer.Option(0.78, "--tau-high", help="Hysteresis high threshold"),
    batch_size: int = typer.Option(4, "--batch-size", help="Concurrent request limit"),
    max_concurrent: int = typer.Option(4, "--max-concurrent", help="Max concurrent Ollama requests"),
    timeout: int = typer.Option(30, "--timeout", help="Request timeout in seconds"),
    validate_schemas: bool = typer.Option(True, "--validate/--no-validate", help="Validate against schemas"),
    allow_cloud: bool = typer.Option(False, "--allow-cloud", help="Allow cloud processing (hybrid mode)"),
) -> None:
    """Enrich redacted chunks with LLM-generated metadata.
    
    Examples:
        chatx enrich redacted_chunks.jsonl --contact "friend@example.com" --backend local
        chatx enrich redacted_chunks.jsonl --contact "+15551234567" --tau 0.8 --model gemma2:9b
        chatx enrich redacted_chunks.jsonl --backend hybrid --allow-cloud --tau-low 0.6
    """
    import asyncio
    import json
    from datetime import datetime
    from chatx.enrichment.enricher import MessageEnricher, ConfidenceGateConfig
    from chatx.enrichment.ollama_client import ProductionOllamaClient, OllamaModelConfig
    
    console.print(f"[bold green]Enriching:[/bold green] {input_file}")

    if not input_file.exists():
        console.print(f"[bold red]Error:[/bold red] Input file does not exist: {input_file}")
        raise typer.Exit(1)

    if backend not in ["local", "cloud", "hybrid"]:
        console.print(f"[bold red]Error:[/bold red] Invalid backend: {backend}")
        console.print("[blue]Valid backends:[/blue] local, cloud, hybrid")
        raise typer.Exit(1)
        
    if backend in ["cloud", "hybrid"] and not allow_cloud:
        console.print("[bold red]Error:[/bold red] Cloud processing requires --allow-cloud flag")
        raise typer.Exit(1)

    if backend != "local":
        console.print("[yellow]Warning:[/yellow] Cloud and hybrid backends not yet implemented, using local")
        backend = "local"

    try:
        # Validate confidence thresholds
        if not (0.0 <= tau_low <= tau <= tau_high <= 1.0):
            console.print("[bold red]Error:[/bold red] Invalid confidence thresholds")
            console.print("[blue]Must satisfy:[/blue] 0 ≤ tau_low ≤ tau ≤ tau_high ≤ 1")
            raise typer.Exit(1)
        
        started_at = datetime.now()
        
        # Load redacted chunks
        console.print(f"[blue]Loading redacted chunks from:[/blue] {input_file}")
        with open(input_file) as f:
            if input_file.suffix == ".jsonl":
                chunks = [json.loads(line) for line in f if line.strip()]
            else:
                chunks = json.load(f)
        
        console.print(f"[blue]Loaded {len(chunks)} chunks[/blue]")
        
        # Check for redaction metadata
        redacted_count = 0
        for chunk in chunks[:5]:  # Sample first 5
            if 'provenance' in chunk and 'redaction' in chunk.get('provenance', {}):
                redacted_count += 1
        
        if redacted_count == 0:
            console.print("[yellow]Warning:[/yellow] No redaction metadata found - are these redacted chunks?")
        else:
            console.print("[green]✓ Found redaction metadata in chunks[/green]")
        
        # Configure enrichment
        console.print(f"[blue]Backend:[/blue] {backend}")
        console.print(f"[blue]Model:[/blue] {model}")
        console.print(f"[blue]Contact:[/blue] {contact}")
        console.print(f"[blue]Confidence thresholds:[/blue] τ={tau}, τ_low={tau_low}, τ_high={tau_high}")
        console.print(f"[blue]Concurrency:[/blue] {max_concurrent} requests")
        
        # Create configuration objects
        model_config = OllamaModelConfig(
            name=model,
            temperature=0.0,  # Deterministic
            seed=42,
            num_predict=800,
        )
        
        confidence_config = ConfidenceGateConfig(
            tau=tau,
            tau_low=tau_low,
            tau_high=tau_high,
        )
        
        # Run enrichment
        async def run_enrichment():
            ollama_client = ProductionOllamaClient(
                max_concurrent=max_concurrent,
                timeout=timeout,
                model_config=model_config,
            )
            
            enricher = MessageEnricher(
                ollama_client=ollama_client,
                confidence_config=confidence_config,
                output_dir=input_file.parent,
                validate_schemas=validate_schemas,
            )
            
            async with enricher:
                # Check Ollama health first
                console.print("[blue]Checking Ollama health...[/blue]")
                
                enrichments, output_path = await enricher.enrich_chunks(
                    chunks=chunks,
                    contact=contact,
                    output_file=output,
                )
                
                return enrichments, output_path, enricher
        
        # Run the async enrichment
        console.print("[blue]Starting enrichment...[/blue]")
        enrichments, output_path, enricher = asyncio.run(run_enrichment())
        
        finished_at = datetime.now()
        total_time = (finished_at - started_at).total_seconds()
        
        # Show results
        console.print("[bold green]Enrichment complete![/bold green]")
        console.print(f"[bold green]Generated {len(enrichments)} enrichments[/bold green]")
        console.print(f"[bold green]Output saved to:[/bold green] {output_path}")
        console.print(f"[blue]Total processing time:[/blue] {total_time:.2f}s")
        
        if enrichments and total_time > 0:
            throughput = len(enrichments) / total_time
            console.print(f"[blue]Throughput:[/blue] {throughput:.1f} enrichments/s")
            
            # Check if meets NFR target
            if throughput >= 25.0:
                console.print("[green]✓ Meets ≥25 enrichments/s target[/green]")
            else:
                console.print("[yellow]⚠ Below 25 enrichments/s target[/yellow]")
        
        # Get performance report
        performance_report = enricher.get_performance_report()
        
        # Show confidence distribution
        confidence_dist = performance_report.get("enrichment_metrics", {}).get("confidence_distribution", {})
        if any(confidence_dist.values()):
            console.print(f"[blue]Confidence distribution:[/blue] "
                         f"Low: {confidence_dist.get('low', 0)}, "
                         f"Medium: {confidence_dist.get('medium', 0)}, "
                         f"High: {confidence_dist.get('high', 0)}")
        
        # Show Ollama metrics
        ollama_metrics = performance_report.get("ollama_metrics", {})
        if ollama_metrics:
            console.print(f"[blue]Average latency:[/blue] {ollama_metrics.get('average_latency_ms', 0):.1f}ms")
            console.print(f"[blue]Error rate:[/blue] {ollama_metrics.get('error_rate', 0):.1%}")
            
            if ollama_metrics.get('meets_throughput_target'):
                console.print("[green]✓ Ollama throughput target met[/green]")
            if ollama_metrics.get('meets_latency_target'):
                console.print("[green]✓ Ollama latency target met[/green]")
        
        # Save performance report
        report_file = output_path.parent / f"enrichment_report_{started_at.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(performance_report, f, indent=2)
        console.print(f"[blue]Performance report saved to:[/blue] {report_file}")
        
        # Show warnings for low confidence
        low_conf_rate = performance_report.get("enrichment_metrics", {}).get("low_confidence_rate", 0)
        if low_conf_rate > 0.2:  # More than 20% low confidence
            console.print(f"[yellow]Warning:[/yellow] {low_conf_rate:.1%} of enrichments had low confidence")
            console.print("[yellow]Consider adjusting model or prompts for better results[/yellow]")
        
        # Show validation warnings
        validation_errors = performance_report.get("enrichment_metrics", {}).get("validation_errors", 0)
        if validation_errors > 0:
            console.print(f"[yellow]Warning:[/yellow] {validation_errors} validation errors occurred")
            console.print(f"[yellow]Check quarantine directory:[/yellow] {input_file.parent / 'quarantine'}")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Enrichment interrupted by user[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error during enrichment:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def analyze(
    input_file: Path = typer.Argument(..., help="Enriched data file to analyze"),
    output_dir: Path | None = typer.Option(None, "--output", "-o", help="Output directory"),
    analysis_type: str = typer.Option("summary", "--type", help="Analysis type"),
) -> None:
    """Analyze enriched conversation data."""
    console.print(f"[bold green]Analyzing:[/bold green] {input_file}")

    if not input_file.exists():
        console.print(f"[bold red]Error:[/bold red] Input file does not exist: {input_file}")
        raise typer.Exit(1)

    # TODO: Implement analysis logic
    console.print("[yellow]Analysis not yet implemented[/yellow]")


@app.command("enrich-multi")
def enrich_multi_pass(
    input_file: Path = typer.Argument(..., help="Input file containing redacted chunks"),
    contact: str = typer.Option(..., "--contact", help="Contact identifier"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
    model: str = typer.Option("gemma2:9b-instruct-q4_K_M", "--model", help="Ollama model to use"),
    batch_size: int = typer.Option(20, "--batch-size", help="Batch size for processing"),
    taxonomy_file: Path | None = typer.Option(None, "--taxonomy", help="Path to labels.yml taxonomy file"),
    privacy_tier: str = typer.Option("local_only", "--privacy-tier", help="Privacy tier (local_only|cloud_safe)"),
    ollama_url: str = typer.Option("http://localhost:11434", "--ollama-url", help="Ollama server URL"),
) -> None:
    """Comprehensive 4-pass enrichment using sophisticated labels.yml taxonomy.
    
    This command performs deep psychological analysis through 4 passes:
    1. Entity extraction and pattern matching
    2. Communication structure and speech acts analysis  
    3. Psychological and emotional analysis with 150+ labels
    4. Relationship dynamics and temporal patterns
    
    Examples:
        chatx enrich-multi chunks.jsonl --contact "friend@example.com"
        chatx enrich-multi chunks.jsonl --contact "+15551234567" --privacy-tier cloud_safe
        chatx enrich-multi chunks.jsonl --contact "person" --taxonomy ./my_labels.yml
    """
    from chatx.enrichment.multi_pass_pipeline import MultiPassEnrichmentPipeline
    import json
    from datetime import datetime
    
    console.print(f"[bold green]Multi-pass enrichment:[/bold green] {input_file}")
    console.print(f"[blue]Contact:[/blue] {contact}")
    console.print(f"[blue]Model:[/blue] {model}")
    console.print(f"[blue]Privacy tier:[/blue] {privacy_tier}")
    
    if not input_file.exists():
        console.print(f"[bold red]Error:[/bold red] Input file does not exist: {input_file}")
        raise typer.Exit(1)
    
    if privacy_tier not in ["local_only", "cloud_safe"]:
        console.print(f"[bold red]Error:[/bold red] Invalid privacy tier: {privacy_tier}")
        console.print("[blue]Valid options:[/blue] local_only, cloud_safe")
        raise typer.Exit(1)
    
    try:
        started_at = datetime.now()
        
        # Load chunks
        console.print(f"[blue]Loading chunks from:[/blue] {input_file}")
        with open(input_file, 'r') as f:
            if input_file.suffix == '.jsonl':
                chunks = [json.loads(line) for line in f if line.strip()]
            else:
                data = json.load(f)
                chunks = data if isinstance(data, list) else [data]
        
        if not chunks:
            console.print("[yellow]No chunks found in input file[/yellow]")
            return
        
        console.print(f"[blue]Loaded:[/blue] {len(chunks)} chunks")
        
        # Initialize multi-pass pipeline
        console.print("[blue]Initializing 4-pass enrichment pipeline...[/blue]")
        pipeline = MultiPassEnrichmentPipeline(
            taxonomy_file=taxonomy_file,
            local_model=model,
            ollama_base_url=ollama_url
        )
        
        # Run multi-pass enrichment
        console.print("[blue]Starting comprehensive analysis...[/blue]")
        console.print("[dim]Pass 1: Entity extraction and pattern matching[/dim]")
        console.print("[dim]Pass 2: Communication structure and speech acts[/dim]")
        console.print("[dim]Pass 3: Psychological and emotional analysis[/dim]")
        console.print("[dim]Pass 4: Relationship dynamics and temporal patterns[/dim]")
        
        enriched_chunks = pipeline.enrich_chunks_batch(
            chunks=chunks,
            contact=contact,
            batch_size=batch_size
        )
        
        finished_at = datetime.now()
        total_time = (finished_at - started_at).total_seconds()
        
        # Determine output path
        if output:
            output_path = output
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = input_file.parent / f"enriched_multi_{contact}_{timestamp}.jsonl"
        
        # Save enriched chunks
        console.print(f"[blue]Saving to:[/blue] {output_path}")
        with open(output_path, 'w') as f:
            for chunk in enriched_chunks:
                f.write(json.dumps(chunk) + '\n')
        
        # Calculate statistics
        total_labels = 0
        coarse_labels = set()
        fine_labels = set()
        processing_times = []
        
        for chunk in enriched_chunks:
            meta = chunk.get("meta", {})
            enrichment = chunk.get("enrichment", {})
            
            coarse = meta.get("labels_coarse", [])
            fine = meta.get("labels_fine_local", [])
            
            total_labels += len(coarse) + len(fine)
            coarse_labels.update(coarse)
            fine_labels.update(fine)
            
            if "processing_time_ms" in enrichment:
                processing_times.append(enrichment["processing_time_ms"])
        
        # Show comprehensive results
        console.print("[bold green]Multi-pass enrichment complete![/bold green]")
        console.print(f"[green]Processed:[/green] {len(enriched_chunks)} chunks")
        console.print(f"[green]Total labels applied:[/green] {total_labels}")
        console.print(f"[green]Unique coarse labels:[/green] {len(coarse_labels)}")
        console.print(f"[green]Unique fine labels:[/green] {len(fine_labels)}")
        console.print(f"[blue]Total time:[/blue] {total_time:.2f}s")
        
        if processing_times:
            avg_time = sum(processing_times) / len(processing_times)
            console.print(f"[blue]Average processing time per chunk:[/blue] {avg_time:.0f}ms")
        
        if total_time > 0:
            throughput = len(enriched_chunks) / total_time
            console.print(f"[blue]Throughput:[/blue] {throughput:.1f} chunks/s")
        
        console.print(f"[bold green]Output saved to:[/bold green] {output_path}")
        
        # Show top labels applied
        if coarse_labels:
            top_coarse = list(coarse_labels)[:10]
            console.print(f"[blue]Top coarse labels:[/blue] {', '.join(top_coarse)}")
        
        if fine_labels and privacy_tier == "local_only":
            top_fine = list(fine_labels)[:10]
            console.print(f"[blue]Top fine labels (local-only):[/blue] {', '.join(top_fine)}")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Multi-pass enrichment interrupted by user[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error during multi-pass enrichment:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def index(
    input_file: Path = typer.Argument(..., help="Input file containing redacted chunks (JSON/JSONL)"),
    contact: str = typer.Option(..., "--contact", help="Contact identifier"),
    store: str = typer.Option("chroma", "--store", help="Vector store backend (chroma|multi)"),
    collection: str | None = typer.Option(None, "--collection", help="Collection name override"),
    multi_vector: bool = typer.Option(False, "--multi-vector", help="Enable multi-vector psychology-aware indexing"),
    batch_size: int = typer.Option(100, "--batch-size", help="Batch size for indexing"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing collection"),
) -> None:
    """Index conversation chunks for fast retrieval."""
    from chatx.indexing.multi_vector_store import MultiVectorChromaDBStore, MultiVectorConfig
    from chatx.indexing.vector_store import ChromaDBVectorStore, IndexingConfig
    import json
    
    console.print(f"[bold green]Indexing chunks:[/bold green] {input_file}")
    console.print(f"[blue]Contact:[/blue] {contact}")
    console.print(f"[blue]Store:[/blue] {store}")
    
    if multi_vector:
        console.print("[blue]Mode:[/blue] Multi-vector psychology-aware indexing")
    
    if not input_file.exists():
        console.print(f"[bold red]Error:[/bold red] Input file does not exist: {input_file}")
        raise typer.Exit(1)

    try:
        # Load chunks
        chunks = []
        with open(input_file, 'r') as f:
            if input_file.suffix == '.jsonl':
                for line in f:
                    if line.strip():
                        chunks.append(json.loads(line))
            else:
                data = json.load(f)
                if isinstance(data, list):
                    chunks = data
                else:
                    chunks = [data]
        
        if not chunks:
            console.print("[yellow]No chunks found in input file[/yellow]")
            return
        
        console.print(f"[blue]Loaded:[/blue] {len(chunks)} chunks")
        
        # Initialize vector store
        if multi_vector or store == "multi":
            config = MultiVectorConfig(
                collection_prefix=collection or "chatx_multi",
                batch_size=batch_size
            )
            store_impl = MultiVectorChromaDBStore(config)
        else:
            config = IndexingConfig(
                collection_prefix=collection or "chatx",
                batch_size=batch_size
            )
            store_impl = ChromaDBVectorStore(config)
        
        # Index chunks
        with store_impl:
            stats = store_impl.index_chunks(chunks, contact, batch_size=batch_size)
            
            console.print("[bold green]Indexing complete![/bold green]")
            if multi_vector:
                console.print(f"[green]Total indexed:[/green] {stats.get('total_indexed', 0)}")
                console.print(f"[red]Total errors:[/red] {stats.get('total_errors', 0)}")
                
                # Show per-space statistics
                collections_stats = stats.get('collections', {})
                for space_name, space_stats in collections_stats.items():
                    console.print(f"[blue]{space_name}:[/blue] {space_stats.get('indexed', 0)} indexed, {space_stats.get('errors', 0)} errors")
            else:
                console.print(f"[green]Indexed:[/green] {stats.get('indexed', 0)}")
                console.print(f"[red]Errors:[/red] {stats.get('errors', 0)}")
                console.print(f"[blue]Collection:[/blue] {stats.get('collection', 'unknown')}")
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Indexing interrupted by user[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error during indexing:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def query(
    question: str = typer.Argument(..., help="Question to ask about the conversations"),
    contact: str = typer.Option(..., "--contact", help="Contact identifier"),
    k: int = typer.Option(10, "--k", help="Number of results to retrieve"),
    store: str = typer.Option("chroma", "--store", help="Vector store backend (chroma|multi)"),
    multi_vector: bool = typer.Option(False, "--multi-vector", help="Use multi-vector psychology-aware search"),
    psychology_weight: float = typer.Option(0.3, "--psychology-weight", help="Weight for psychological vectors (0.0-1.0)"),
    temporal_weight: float = typer.Option(0.2, "--temporal-weight", help="Weight for temporal vectors (0.0-1.0)"),
    since: str | None = typer.Option(None, "--since", help="Start date filter (ISO format)"),
    until: str | None = typer.Option(None, "--until", help="End date filter (ISO format)"),
    labels_any: list[str] = typer.Option([], "--labels-any", help="Match any of these labels"),
    labels_all: list[str] = typer.Option([], "--labels-all", help="Match all of these labels"),
    labels_not: list[str] = typer.Option([], "--labels-not", help="Exclude these labels"),
    privacy_tier: str | None = typer.Option(None, "--privacy-tier", help="Privacy tier filter (local_only|cloud_safe)"),
    insights: bool = typer.Option(False, "--insights", help="Show psychological insights"),
) -> None:
    """Query conversations with psychology-aware search."""
    from chatx.indexing.multi_vector_store import MultiVectorChromaDBStore, MultiVectorConfig, VectorSpace
    from chatx.indexing.vector_store import ChromaDBVectorStore, IndexingConfig
    from datetime import datetime
    
    console.print(f"[bold green]Querying:[/bold green] {question}")
    console.print(f"[blue]Contact:[/blue] {contact}")
    
    if multi_vector:
        console.print("[blue]Mode:[/blue] Multi-vector psychology-aware search")
        console.print(f"[blue]Psychology weight:[/blue] {psychology_weight}")
        console.print(f"[blue]Temporal weight:[/blue] {temporal_weight}")
    
    try:
        # Build filters
        filters = {}
        if since:
            filters["date_start"] = {"$gte": since}
        if until:
            filters["date_end"] = {"$lte": until}
        if labels_any:
            filters["labels_coarse"] = {"$in": labels_any}
        # TODO: Add support for labels_all and labels_not
        
        # Initialize vector store
        if multi_vector or store == "multi":
            config = MultiVectorConfig()
            store_impl = MultiVectorChromaDBStore(config)
            
            # Set vector weights
            vector_weights = {
                VectorSpace.SEMANTIC: 0.4,
                VectorSpace.PSYCHOLOGICAL: psychology_weight,
                VectorSpace.TEMPORAL: temporal_weight,
                VectorSpace.STRUCTURAL: 0.1
            }
            
            with store_impl:
                results = store_impl.search_multi_vector(
                    query=question,
                    contact=contact,
                    k=k,
                    vector_weights=vector_weights,
                    filters=filters,
                    require_privacy_tier=privacy_tier
                )
                
                if not results:
                    console.print("[yellow]No results found[/yellow]")
                    return
                
                console.print(f"[bold green]Found {len(results)} results:[/bold green]")
                for i, result in enumerate(results, 1):
                    console.print(f"\n[blue]Result {i}:[/blue] (Combined Score: {result.combined_score:.3f})")
                    
                    # Show vector space contributions
                    contributions = []
                    for space, contrib in result.vector_contributions.items():
                        contributions.append(f"{space.value}: {contrib:.3f}")
                    console.print(f"[dim]Vector contributions: {', '.join(contributions)}[/dim]")
                    
                    # Show privacy tier
                    privacy_color = "green" if result.privacy_tier == "cloud_safe" else "yellow"
                    console.print(f"[{privacy_color}]Privacy tier:[/{privacy_color}] {result.privacy_tier}")
                    
                    # Show labels if available
                    metadata = result.metadata
                    labels = metadata.get("labels_coarse", []) + metadata.get("labels_fine_local", [])
                    if labels:
                        console.print(f"[dim]Labels: {', '.join(labels)}[/dim]")
                    
                    # Show text preview
                    text_preview = result.text[:200] + "..." if len(result.text) > 200 else result.text
                    console.print(f"[white]{text_preview}[/white]")
                    
                    # Show message IDs for citation
                    if result.message_ids:
                        console.print(f"[dim]Messages: {', '.join(result.message_ids[:3])}{' ...' if len(result.message_ids) > 3 else ''}[/dim]")
                
                # Show insights if requested
                if insights:
                    console.print("\n[bold blue]Psychological Insights:[/bold blue]")
                    time_range = (since, until) if since and until else None
                    insight_data = store_impl.get_psychology_insights(
                        contact=contact,
                        time_range=time_range,
                        label_focus=labels_any if labels_any else None
                    )
                    
                    if "error" not in insight_data:
                        console.print(f"[blue]Total chunks analyzed:[/blue] {insight_data.get('total_chunks', 0)}")
                        
                        top_labels = insight_data.get('top_labels', [])[:5]
                        if top_labels:
                            console.print(f"[blue]Top labels:[/blue] {', '.join(top_labels)}")
                        
                        privacy_dist = insight_data.get('privacy_distribution', {})
                        console.print(f"[blue]Privacy distribution:[/blue] Local-only: {privacy_dist.get('local_only', 0)}, Cloud-safe: {privacy_dist.get('cloud_safe', 0)}")
        else:
            # Standard single-vector search
            config = IndexingConfig()
            store_impl = ChromaDBVectorStore(config)
            
            with store_impl:
                results = store_impl.search(
                    query=question,
                    contact=contact,
                    k=k,
                    filters=filters
                )
                
                if not results:
                    console.print("[yellow]No results found[/yellow]")
                    return
                
                console.print(f"[bold green]Found {len(results)} results:[/bold green]")
                for i, result in enumerate(results, 1):
                    console.print(f"\n[blue]Result {i}:[/blue] (Score: {result.score:.3f})")
                    text_preview = result.text[:200] + "..." if len(result.text) > 200 else result.text
                    console.print(f"[white]{text_preview}[/white]")
                    
                    if result.message_ids:
                        console.print(f"[dim]Messages: {', '.join(result.message_ids[:3])}{' ...' if len(result.message_ids) > 3 else ''}[/dim]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Query interrupted by user[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error during query:[/bold red] {e}")
        raise typer.Exit(1)


# iMessage Commands
imessage_app = typer.Typer(help="iMessage extraction commands")
app.add_typer(imessage_app, name="imessage")


@imessage_app.command("pull", help="Extract iMessage conversations for a contact.")
def imessage_pull(
    contact: str = typer.Option(..., "--contact", metavar="<ID>", help="Contact identifier (phone, email, or name)", rich_help_panel="Source"),
    db: Path = typer.Option(
        Path.home() / "Library/Messages/chat.db",
        "--db",
        help="Path to Messages database",
        show_default=True,
        metavar="<PATH>",
        rich_help_panel="Source",
    ),
    from_backup: Path | None = typer.Option(
        None,
        "--from-backup",
        help="Path to iPhone backup directory (Finder/iTunes MobileSync)",
        metavar="<BACKUP_DIR>",
        rich_help_panel="Source",
    ),
    backup_password: str | None = typer.Option(
        None,
        "--backup-password",
        help="Password for encrypted backups (input is not echoed)",
        prompt=False,
        hide_input=True,
        rich_help_panel="Source",
    ),
    out: Path = typer.Option(Path("./out"), "--out", help="Output directory", show_default=True, metavar="<DIR>", rich_help_panel="Output"),
    include_attachments: bool = typer.Option(False, "--include-attachments", help="Extract attachment metadata", rich_help_panel="Attachments"),
    copy_binaries: bool = typer.Option(False, "--copy-binaries", help="Copy attachment files to output", rich_help_panel="Attachments"),
    thumbnails: bool = typer.Option(False, "--thumbnails", help="Generate thumbnails for image attachments", rich_help_panel="Attachments"),
    transcribe_audio: str = typer.Option(
        "off",
        "--transcribe-audio",
        help="Audio transcription mode (local|off). Example: --transcribe-audio local",
        show_default=True,
        rich_help_panel="Transcription",
    ),
    report_missing: bool = typer.Option(True, "--report-missing/--no-report-missing", help="Generate missing attachments report", show_default=True, rich_help_panel="Attachments"),
    error_format: str = typer.Option("text", "--error-format", help="Error output format (text|json)", rich_help_panel="Output"),
) -> None:
    """Extract iMessage conversations for a contact.

    Examples:
      chatx imessage pull --contact "+15551234567" --out ./out
      chatx imessage pull --contact "+15551234567" \
        --from-backup "~/Library/Application Support/MobileSync/Backup/<UDID>" --out ./out

    Notes:
      - For backup mode, encrypted backups require a password. We do not bypass or crack it.
      - Grant Full Disk Access to your terminal to read Messages on macOS.
    """
    from chatx.imessage import extract_messages
    from chatx.imessage.backup import (
        ensure_backup_accessible,
        stage_sms_db,
        backup_is_encrypted,
        preflight_backup_structure,
        canonical_mobilesync_hint,
    )
    
    console.print(f"[bold green]Extracting iMessage conversations for:[/bold green] {contact}")
    def _redact_path(p: Path) -> str:
        try:
            home = Path.home()
            s = str(p)
            return s.replace(str(home), "~")
        except Exception:
            return str(p)

    if from_backup:
        console.print(f"[blue]Backup dir:[/blue] {_redact_path(from_backup)}")
    else:
        console.print(f"[blue]Database:[/blue] {db}")
    console.print(f"[blue]Output:[/blue] {out}")
    
    # Preflight
    staged_db_path: Path | None = None
    if from_backup:
        if not from_backup.exists() or not from_backup.is_dir():
            if error_format == "json":
                from chatx.cli_errors import emit_problem
                emit_problem(
                    code="MISSING_BACKUP_DIR",
                    title="Backup directory not found",
                    status=1,
                    detail=f"Backup directory not found: {_redact_path(from_backup)}",
                    instance=str(from_backup),
                )
            else:
                console.print(f"[bold red]Error:[/bold red] Backup directory not found: {_redact_path(from_backup)}")
                console.print(f"[yellow]Hint:[/yellow] {canonical_mobilesync_hint()}")
            raise typer.Exit(1)
        try:
            # Preflight checks (non-fatal info may be derived)
            try:
                preflight_backup_structure(from_backup)
            except FileNotFoundError as e:
                console.print(f"[bold red]Preflight failed:[/bold red] {e}")
                raise typer.Exit(1)

            # Prompt for password if encrypted and none provided
            enc = backup_is_encrypted(from_backup)
            if enc is True and not backup_password:
                if error_format == "json":
                    from chatx.cli_errors import emit_problem
                    emit_problem(
                        code="ENCRYPTED_BACKUP_PASSWORD_REQUIRED",
                        title="Encrypted backup password required",
                        status=1,
                        detail="Provide --backup-password or interactive input.",
                        instance=str(from_backup),
                    )
                    raise typer.Exit(1)
                backup_password = typer.prompt("Encrypted backup password", hide_input=True)

            ensure_backup_accessible(from_backup, backup_password)
        except Exception as e:
            console.print(f"[bold red]Backup validation failed:[/bold red] {e}")
            raise typer.Exit(1)
    else:
        if not db.exists():
            if error_format == "json":
                from chatx.cli_errors import emit_problem
                emit_problem(
                    code="MISSING_DB",
                    title="Messages database not found",
                    status=1,
                    detail=f"Database not found: {db}",
                    instance=str(db),
                )
            else:
                console.print(f"[bold red]Error:[/bold red] Messages database not found: {db}")
                console.print("[yellow]Tip:[/yellow] Grant Full Disk Access to your terminal in System Settings > Privacy & Security")
            raise typer.Exit(1)
    
    # Create output directory
    out.mkdir(parents=True, exist_ok=True)
    
    try:
        started_at = datetime.now()
        # Stage DB if reading from backup, else use provided db
        if from_backup:
            with stage_sms_db(from_backup) as staged_db:
                staged_db_path = staged_db
                messages = list(extract_messages(
                    db_path=staged_db,
                    contact=contact,
                    include_attachments=include_attachments,
                    copy_binaries=copy_binaries,
                    thumbnails=thumbnails,
                    transcribe_audio=transcribe_audio,
                    out_dir=out,
                    backup_dir=from_backup,
                ))
        else:
            messages = list(extract_messages(
                db_path=db,
                contact=contact,
                include_attachments=include_attachments,
                copy_binaries=copy_binaries,
                thumbnails=thumbnails,
                transcribe_audio=transcribe_audio,
                out_dir=out,
            ))
        finished_at = datetime.now()
        
        message_count = len(messages)
        console.print(f"[bold green]Extracted {message_count} messages[/bold green]")
        
        if message_count > 0:
            # Write JSON output with schema validation
            from chatx.utils.json_output import write_messages_with_validation
            
            output_file = out / f"messages_{contact.replace('@', '_at_').replace('+', '_plus_')}.json"
            valid_count, invalid_count = write_messages_with_validation(messages, output_file)
            console.print(f"[bold green]Messages written to:[/bold green] {output_file}")
            # Exit semantics: if zero valid rows, treat as fatal
            if valid_count == 0:
                if error_format == "json":
                    from chatx.cli_errors import emit_problem
                    emit_problem(
                        code="NO_VALID_ROWS",
                        title="No valid rows",
                        status=1,
                        detail="All rows failed schema validation; see quarantine/messages_bad.jsonl",
                        instance=str(output_file),
                    )
                else:
                    console.print("[bold red]No valid rows written (see quarantine/messages_bad.jsonl)[/bold red]")
                raise typer.Exit(1)
            
            # Report transcription statistics if audio transcription was enabled
            if transcribe_audio != "off" and include_attachments:
                from chatx.imessage.transcribe import collect_transcription_stats
                
                stats = collect_transcription_stats(messages)
                total_transcripts = stats["total_transcripts"]
                
                if total_transcripts > 0:
                    console.print(f"[blue]Audio transcription:[/blue] {total_transcripts} voice message(s) transcribed")
                    
                    # Show breakdown by confidence if available
                    confidence_counts = stats["by_confidence"]
                    confidence_breakdown = []
                    for level in ["high", "medium", "low"]:
                        count = confidence_counts.get(level, 0)
                        if count > 0:
                            confidence_breakdown.append(f"{count} {level}")
                    
                    if confidence_breakdown:
                        console.print(f"[blue]Confidence levels:[/blue] {', '.join(confidence_breakdown)}")
                    
                    # Show engines used
                    engines = stats["by_engine"]
                    if engines:
                        engine_list = [f"{count} {engine}" for engine, count in engines.items()]
                        console.print(f"[blue]Engines:[/blue] {', '.join(engine_list)}")
                elif transcribe_audio == "local":
                    console.print("[yellow]No voice messages found to transcribe[/yellow]")
        
        # Generate missing attachments report if requested and attachments enabled
        if report_missing and include_attachments:
            from chatx.imessage.db import copy_db_for_readonly, open_ro
            from chatx.imessage.report import generate_missing_attachments_report
            
            console.print("[blue]Checking for missing attachments...[/blue]")
            
            with copy_db_for_readonly(db) as temp_db:
                conn = open_ro(temp_db)
                try:
                    missing_counts = generate_missing_attachments_report(conn, out, contact)
                    total_missing = sum(missing_counts.values())
                    
                    if total_missing > 0:
                        console.print(f"[yellow]Found {total_missing} missing attachment(s) across {len(missing_counts)} conversation(s)[/yellow]")
                        console.print(f"[yellow]Report written to:[/yellow] {out / 'missing_attachments.json'}")
                    else:
                        console.print("[green]All attachment files found on disk[/green]")
                finally:
                    conn.close()

        # Compute and emit run report + perf soft floor warning
        try:
            from chatx.utils.run_report import write_extract_run_report
            # Compute simple counters
            attachments_total = sum(len(m.attachments) for m in messages)
            image_attachments = [
                att for m in messages for att in m.attachments if att.type == "image"
            ]
            images_total = len(image_attachments)
            unique_hashes = {}
            bytes_copied = 0
            for att in image_attachments:
                h = att.source_meta.get("hash", {}).get("sha256")
                p = att.abs_path
                if h and p and h not in unique_hashes:
                    unique_hashes[h] = p
                    try:
                        bytes_copied += Path(p).stat().st_size
                    except OSError:
                        pass
            images_copied = len(unique_hashes)
            elapsed = max((finished_at - started_at).total_seconds(), 0.0)
            rate = (len(messages) / elapsed * 60.0) if elapsed > 0 else 0.0

            # Artifacts
            artifacts = [str(out / f"messages_{contact.replace('@', '_at_').replace('+', '_plus_')}.json")]
            missing_path = out / 'missing_attachments.json'
            if missing_path.exists():
                artifacts.append(str(missing_path))

            # Optional soft floor warning via env var
            import os
            warn_msgs = []
            soft_floor = os.environ.get("CHATX_SOFT_FLOOR_MSGS_MIN")
            if soft_floor:
                try:
                    floor = float(soft_floor)
                    if rate < floor:
                        warn = f"Throughput below soft floor: {rate:.0f} < {floor:.0f} msgs/min"
                        console.print(f"[yellow]{warn}[/yellow]")
                        warn_msgs.append(warn)
                except ValueError:
                    # Ignore invalid value
                    pass

            report_path = write_extract_run_report(
                out_dir=out,
                started_at=started_at,
                finished_at=finished_at,
                messages_total=len(messages),
                attachments_total=attachments_total,
                images_total=images_total,
                images_copied=images_copied,
                bytes_copied=bytes_copied,
                throughput_msgs_min=rate,
                artifacts=artifacts,
                warnings=warn_msgs,
            )
            console.print(f"[blue]Run report written to:[/blue] {report_path}")

            # Emit metrics JSONL for observability
            try:
                from chatx.utils.run_report import append_metrics_event

                counters = {
                    "messages_total": len(messages),
                    "attachments_total": attachments_total,
                    "images_total": images_total,
                    "images_copied": images_copied,
                    "bytes_copied": bytes_copied,
                    "throughput_msgs_min": rate,
                }
                metrics_path = append_metrics_event(
                    out_dir=out,
                    component="extract",
                    started_at=started_at,
                    finished_at=finished_at,
                    counters=counters,
                    warnings=warn_msgs,
                    errors=[],
                    artifacts=artifacts,
                )
                console.print(f"[blue]Metrics appended:[/blue] {metrics_path}")
            except Exception:
                # Do not fail on metrics write errors
                pass
            # Write manifest for reproducibility (non-fatal)
            try:
                from chatx.obs.run_artifacts import write_manifest
                db_input = staged_db_path if from_backup else db
                manifest_path = write_manifest(out_dir=out, db_path=db_input)
                console.print(f"[blue]Manifest written to:[/blue] {manifest_path}")
            except Exception:
                pass
        except Exception:
            # Do not fail extraction if metrics writing fails
            pass
        
    except Exception as e:
        console.print(f"[bold red]Error during extraction:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def pipeline(
    source: Path = typer.Argument(..., help="Source path to process"),
    output_dir: Path = typer.Argument(..., help="Output directory"),
    platform: str | None = typer.Option(None, "--platform", "-p", help="Platform type"),
    skip_redaction: bool = typer.Option(False, "--skip-redaction", help="Skip privacy redaction"),
    skip_enrichment: bool = typer.Option(False, "--skip-enrichment", help="Skip LLM enrichment"),
    provider: str = typer.Option("local", "--provider", help="LLM provider for enrichment"),
) -> None:
    """Run the complete ChatX pipeline (extract -> transform -> redact -> enrich -> analyze)."""
    console.print(f"[bold green]Running full pipeline on:[/bold green] {source}")

    if not source.exists():
        console.print(f"[bold red]Error:[/bold red] Source path does not exist: {source}")
        raise typer.Exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[blue]Output directory:[/blue] {output_dir}")
    console.print(f"[blue]LLM provider:[/blue] {provider}")

    if skip_redaction:
        console.print("[yellow]Skipping redaction step[/yellow]")
    if skip_enrichment:
        console.print("[yellow]Skipping enrichment step[/yellow]")

    # TODO: Implement full pipeline
    console.print("[yellow]Pipeline not yet implemented[/yellow]")


def cli() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    cli()

# Instagram Commands
instagram_app = typer.Typer(help="Instagram extraction commands")
app.add_typer(instagram_app, name="instagram")


@instagram_app.command("pull", help="Extract Instagram DMs from official ZIP export.")
def instagram_pull(
    zip: Path = typer.Option(..., "--zip", help="Path to Instagram official data ZIP", metavar="<ZIP>"),
    out: Path = typer.Option(Path("./out"), "--out", help="Output directory", show_default=True, metavar="<DIR>"),
    user: str = typer.Option(..., "--user", help="Your Instagram display name (filters threads; also marks is_me)", metavar="<NAME>"),
    author_only: list[str] = typer.Option([], "--author-only", help="Include only messages authored by these usernames (repeatable)", metavar="<NAME>", rich_help_panel="Filters"),
    error_format: str = typer.Option("text", "--error-format", help="Error output format (text|json)"),
) -> None:
    """Extract Instagram DMs from the official data ZIP export.

    Examples:
      chatx instagram pull --zip ./instagram.zip --user "Your Name" --out ./out
      chatx instagram pull --zip ./instagram.zip --user "Your Name" \
        --author-only "FriendA" --out ./out

    Security:
      - ZIP traversal is blocked; media are referenced only, not uploaded.
    """
    from chatx.instagram.extract import extract_messages_from_zip
    from chatx.utils.json_output import write_messages_with_validation

    console.print(f"[bold green]Extracting Instagram from ZIP:[/bold green] {zip}")
    console.print(f"[blue]Output:[/blue] {out}")

    if not zip.exists():
        if error_format == "json":
            from chatx.cli_errors import emit_problem
            emit_problem(
                code="MISSING_ZIP",
                title="ZIP file not found",
                status=1,
                detail=f"ZIP not found: {zip}",
                instance=str(zip),
            )
        else:
            console.print(f"[bold red]Error:[/bold red] ZIP file not found: {zip}")
        raise typer.Exit(1)

    try:
        out.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        if error_format == "json":
            from chatx.cli_errors import emit_problem
            emit_problem(
                code="DIR_CREATION_FAILED",
                title="Failed to create output directory",
                status=1,
                detail=str(e),
                instance=str(out),
            )
        else:
            console.print(f"[bold red]Failed to create output directory:[/bold red] {e}")
        raise typer.Exit(1)

    try:
        messages = extract_messages_from_zip(
            zip_path=zip,
            include_threads_with=[user],
            authors_only=author_only,
            me_username=user,
        )
    except ValueError as e:
        # Likely unsafe ZIP entry (Zip Slip) or similar validation failure
        if error_format == "json":
            from chatx.cli_errors import emit_problem
            emit_problem(
                code="UNSAFE_ZIP_ENTRY",
                title="Unsafe ZIP entry detected",
                status=1,
                detail=str(e),
                instance=str(zip),
            )
        else:
            console.print(f"[bold red]Unsafe ZIP entry detected[/bold red]: {e}")
        raise typer.Exit(1)
    except Exception as e:
        if error_format == "json":
            from chatx.cli_errors import emit_problem
            emit_problem(
                code="INVALID_INPUT",
                title="Failed to parse Instagram ZIP",
                status=1,
                detail=str(e),
                instance=str(zip),
            )
        else:
            console.print(f"[bold red]Failed to parse ZIP:[/bold red] {e}")
        raise typer.Exit(1)

    # Write output with schema validation
    output_file = out / f"messages_instagram_{zip.stem}.json"
    valid_count, invalid_count = write_messages_with_validation(messages, output_file)
    console.print(f"[bold green]Messages written to:[/bold green] {output_file}")
    if valid_count == 0:
        if error_format == "json":
            from chatx.cli_errors import emit_problem
            emit_problem(
                code="NO_VALID_ROWS",
                title="No valid rows",
                status=1,
                detail="All rows failed schema validation; see quarantine/messages_bad.jsonl",
                instance=str(output_file),
            )
        else:
            console.print("[bold red]No valid rows written (see quarantine/messages_bad.jsonl)[/bold red]")
        raise typer.Exit(1)


# iMessage audit command (report-only)
@imessage_app.command("audit", help="Scan DB for missing local attachments; report-only.")
def imessage_audit(
    db: Path = typer.Option(
        Path.home() / "Library/Messages/chat.db",
        "--db",
        help="Path to Messages database",
        show_default=True,
        metavar="<PATH>",
    ),
    out: Path = typer.Option(Path("./out"), "--out", help="Output directory", show_default=True, metavar="<DIR>"),
    contact: str | None = typer.Option(None, "--contact", help="Optional contact filter", metavar="<ID>", rich_help_panel="Filters"),
) -> None:
    """Scan the database for missing/evicted attachment files and produce guidance.

    Examples:
      chatx imessage audit --db ~/Library/Messages/chat.db --out ./out
      chatx imessage audit --db ~/Library/Messages/chat.db --contact "+15551234567" --out ./out

    Notes:
      - Report is written to out/missing_attachments.json and exit code is 0.
      - Guidance reflects Apple’s per-conversation Download button (no automation).
    """
    from chatx.imessage.db import copy_db_for_readonly, open_ro
    from chatx.imessage.report import generate_missing_attachments_report
    from chatx.imessage.backup import canonical_mobilesync_hint

    console.print("[bold green]Auditing iMessage attachments...[/bold green]")
    console.print(f"[blue]Database:[/blue] {db}")
    console.print(f"[blue]Output:[/blue] {out}")

    out.mkdir(parents=True, exist_ok=True)

    if not db.exists():
        # Prefer structured error in json mode; otherwise textual hints
        from chatx.cli_errors import emit_problem
        emit_problem(
            code="MISSING_DB",
            title="Messages database not found",
            status=1,
            detail=f"Database not found: {db}",
            instance=str(db),
        )
        raise typer.Exit(1)

    # Always exit 0 after report generation
    try:
        with copy_db_for_readonly(db) as temp_db:
            conn = open_ro(temp_db)
            try:
                console.print("[blue]Generating missing attachments report...[/blue]")
                counts = generate_missing_attachments_report(conn, out, contact)
                total_missing = sum(counts.values())
                if total_missing > 0:
                    console.print(f"[yellow]Found {total_missing} missing attachment(s) across {len(counts)} conversation(s)[/yellow]")
                    console.print(f"[yellow]Report written to:[/yellow] {out / 'missing_attachments.json'}")
                    console.print("[blue]Guidance:[/blue] In Messages, open the conversation, click Info (i), then use 'Download' to fetch evicted items. There is no bulk API.")
                else:
                    console.print("[green]All attachment files are present on disk.[/green]")
            finally:
                conn.close()
    except Exception as e:
        console.print(f"[bold red]Audit failed:[/bold red] {e}")
        # Exit non-zero on hard failure
        raise typer.Exit(1)
    # Success path (report generated): exit 0
    return


@imessage_app.command("pdf", help="Ingest conversation PDF (text-first; OCR fallback).")
def imessage_pdf(
    pdf: Path = typer.Option(..., "--pdf", help="Path to conversation PDF export", metavar="<PDF>"),
    out: Path = typer.Option(Path("./out"), "--out", help="Output directory", show_default=True, metavar="<DIR>"),
    me: str = typer.Option(..., "--me", help="Your display name as it appears in the PDF", metavar="<NAME>", rich_help_panel="Parsing"),
    ocr: bool = typer.Option(False, "--ocr", help="Enable OCR fallback when no text layer", show_default=True, rich_help_panel="Parsing"),
) -> None:
    """Ingest a conversation PDF (text-first; OCR fallback) to canonical JSON.

    Examples:
      chatx imessage pdf --pdf ./conversation.pdf --me "Your Name" --out ./out
      chatx imessage pdf --pdf ./img_only.pdf --me "Your Name" --ocr --out ./out

    Notes:
      - Prefers text layer when present; optional OCR for image-only PDFs.
    """
    from chatx.pdf_ingest.reader import PDFIngestOptions, extract_messages_from_pdf
    from chatx.utils.json_output import write_messages_with_validation

    console.print(f"[bold green]Ingesting PDF:[/bold green] {pdf}")
    console.print(f"[blue]Output:[/blue] {out}")
    if not pdf.exists():
        console.print(f"[bold red]Error:[/bold red] PDF not found: {pdf}")
        raise typer.Exit(1)

    out.mkdir(parents=True, exist_ok=True)

    try:
        opts = PDFIngestOptions(me_name=me, ocr=ocr)
        messages = extract_messages_from_pdf(pdf, options=opts)
        output_file = out / f"messages_{pdf.stem}.json"
        write_messages_with_validation(messages, output_file)
        console.print(f"[bold green]Messages written to:[/bold green] {output_file}")
    except Exception as e:
        console.print(f"[bold red]PDF ingestion failed:[/bold red] {e}")
        raise typer.Exit(1)
