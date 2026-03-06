"""
Upgrades Commands
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from subprocess import CalledProcessError
from typing import Optional, Dict, List, Sequence

import click
import yaml
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..console import console

@click.group()
def upgrades():
    """Canonical Repo Truth Extractor commands (v4 default, v3 fallback)."""
    pass


