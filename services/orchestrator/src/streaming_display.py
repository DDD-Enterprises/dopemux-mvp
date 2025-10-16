"""
Streaming Display - Real-Time Response Visualization
ADHD-optimized progress indication to prevent "is it working?" anxiety

Features:
- Line-by-line streaming with Rich Live
- Visual progress indicators
- Clear error display
- Non-blocking updates (4 FPS)
- Graceful handling of partial content
"""

import time
from typing import Iterator, Optional, Callable
from rich.live import Live
from rich.text import Text
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console

console = Console()


class StreamingDisplay:
    """
    Real-time display of AI responses with ADHD optimization.

    Provides visible progress to prevent anxiety during long responses.
    """

    def __init__(self, agent_name: str):
        """
        Initialize streaming display.

        Args:
            agent_name: Name of AI agent (for display)
        """
        self.agent_name = agent_name
        self.refresh_rate = 4  # 4 FPS (smooth but not overwhelming)

    def stream_response(
        self,
        line_generator: Iterator[str],
        on_line: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Display response lines as they arrive.

        Args:
            line_generator: Iterator yielding response lines
            on_line: Optional callback for each line

        Returns:
            Complete assembled response

        Example:
            >>> display = StreamingDisplay('claude')
            >>> response = display.stream_response(line_generator)
        """
        response_lines = []

        with Live(
            Text(""),
            refresh_per_second=self.refresh_rate,
            console=console
        ) as live:
            for line in line_generator:
                response_lines.append(line)

                # Update display
                display_text = Text('\n'.join(response_lines))
                live.update(display_text)

                # Callback
                if on_line:
                    on_line(line)

        return '\n'.join(response_lines)

    def show_with_progress(
        self,
        task_description: str,
        async_function: Callable
    ) -> str:
        """
        Show spinner while waiting for response.

        Args:
            task_description: What's happening (e.g., "Generating code")
            async_function: Function that returns response

        Returns:
            Response from function

        Use Case:
            When collecting complete response before display

        Example:
            >>> display = StreamingDisplay('gemini')
            >>> response = display.show_with_progress(
            ...     "Researching OAuth2 patterns",
            ...     lambda: get_complete_response()
            ... )
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                f"[cyan]{self.agent_name}[/cyan]: {task_description}",
                total=None
            )

            # Execute function
            response = async_function()

            progress.update(task, completed=True)

        return response

    def show_error(self, error_type: str, error_message: str):
        """
        Display error with clear formatting.

        Args:
            error_type: Error category (timeout, crash, etc.)
            error_message: Human-readable error description

        ADHD Optimization:
            Clear visual distinction (red panel)
            Actionable message (what to do next)
        """
        error_panel = Panel(
            f"[red]Error:[/red] {error_message}\n"
            f"[dim]Type:[/dim] {error_type}\n\n"
            f"[yellow]💡 Suggestion:[/yellow] Try restarting the agent or check logs",
            title=f"❌ {self.agent_name}",
            border_style="red"
        )
        console.print(error_panel)

    def show_success(self, content: str, metadata: Optional[dict] = None):
        """
        Display successful response with metadata.

        Args:
            content: Parsed AI response
            metadata: Optional metadata (processing time, line counts, etc.)
        """
        # Show content
        console.print(Panel(
            content,
            title=f"✅ {self.agent_name}",
            border_style="green"
        ))

        # Show metadata if available
        if metadata:
            meta_text = "  ".join(f"{k}: {v}" for k, v in metadata.items())
            console.print(f"[dim]{meta_text}[/dim]\n")

    def show_partial_success(self, content: str, error_message: str):
        """
        Display partial success (got content but with warning).

        Args:
            content: Partial response content
            error_message: Warning message

        ADHD Optimization:
            Shows content (useful) but warns about issue
        """
        console.print(Panel(
            f"{content}\n\n"
            f"[yellow]⚠️ Warning:[/yellow] {error_message}",
            title=f"⚠️  {self.agent_name} (partial)",
            border_style="yellow"
        ))


def stream_with_progress(
    agent_name: str,
    line_generator: Iterator[str]
) -> str:
    """
    Convenience function for streaming display.

    Args:
        agent_name: AI agent name
        line_generator: Iterator yielding response lines

    Returns:
        Complete response

    Example:
        >>> response = stream_with_progress('claude', line_generator)
    """
    display = StreamingDisplay(agent_name)
    return display.stream_response(line_generator)


if __name__ == "__main__":
    """Test streaming display."""
    import sys

    print("🧪 Testing Streaming Display")
    print("=" * 60)

    # Test 1: Streaming lines
    print("\n1. Testing line-by-line streaming...")

    def sample_line_generator():
        """Simulate AI responding line by line."""
        lines = [
            "To implement authentication,",
            "you should consider:",
            "",
            "1. Use JWT tokens for stateless auth",
            "2. Hash passwords with bcrypt",
            "3. Implement refresh token rotation",
            "",
            "This provides good security while maintaining performance."
        ]
        for line in lines:
            time.sleep(0.1)  # Simulate typing delay
            yield line

    display = StreamingDisplay('claude')
    response = display.stream_response(sample_line_generator())

    print(f"\n✅ Streamed {len(response.split(chr(10)))} lines")

    # Test 2: Progress spinner
    print("\n2. Testing progress spinner...")

    def slow_task():
        time.sleep(2)
        return "Research complete! Found 15 OAuth2 patterns."

    display2 = StreamingDisplay('gemini')
    result = display2.show_with_progress("Researching OAuth2 patterns", slow_task)

    print(f"✅ Got result: {result[:50]}...")

    # Test 3: Error display
    print("\n3. Testing error display...")
    display3 = StreamingDisplay('codex')
    display3.show_error("timeout", "No response within 30 seconds")

    # Test 4: Success with metadata
    print("\n4. Testing success display with metadata...")
    display4 = StreamingDisplay('claude')
    display4.show_success(
        "Authentication implementation complete!",
        metadata={'processing_ms': 1250, 'lines': 15}
    )

    # Test 5: Partial success
    print("\n5. Testing partial success...")
    display5 = StreamingDisplay('gemini')
    display5.show_partial_success(
        "Here's what I found, but...",
        "Rate limit may have truncated response"
    )

    print("\n✅ Streaming display test complete!")
