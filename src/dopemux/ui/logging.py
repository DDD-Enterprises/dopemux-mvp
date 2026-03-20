"""
DØPEMÜX Telemetry Logger Configuration

Customizes the rich.logging.RichHandler to adhere to the brand voice.
"""
import logging
from rich.logging import RichHandler
from rich.text import Text
from .theme import Glyphs

class DopemuxLogHandler(RichHandler):
    """
    A branded Rich log handler that prefixes logs with ritual metadata.
    """
    def render_message(self, record: logging.LogRecord, message: str) -> "ConsoleRenderable":
        """Apply brand styling to the log message based on level."""
        if record.levelno >= logging.ERROR:
            prefix = f"[gremlin.pink][BLOCKER][/gremlin.pink] "
        elif record.levelno >= logging.WARNING:
            prefix = f"[gilt.edge][HAZARD][/gilt.edge] "
        elif record.levelno >= logging.INFO:
            prefix = f"[mint][TELEMETRY][/mint] "
        else:
            prefix = f"[text.dim][SIGNAL][/text.dim] "
            
        return super().render_message(record, prefix + message)

def setup_branded_logging(level=logging.INFO):
    """
    Configures the root logger with the DØPEMÜX brand handler.
    """
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[DopemuxLogHandler(show_path=False, markup=True)]
    )
