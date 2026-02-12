"""Entry point for CLI execution via `python -m copilot_transcript_ingester`"""

import sys
from .main import main

if __name__ == "__main__":
    sys.exit(main())
