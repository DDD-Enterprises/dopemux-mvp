#!/usr/bin/env python3
"""Environment-backed configuration for dashboard backend integration scripts."""

from __future__ import annotations

import os


# Leantime Configuration
LEANTIME_URL = os.getenv("LEANTIME_URL", "http://localhost:8080")
LEANTIME_API_KEY = os.getenv("LEANTIME_API_KEY", "")

# ADHD Engine Configuration
ADHD_ENGINE_URL = os.getenv("ADHD_ENGINE_URL", "http://localhost:8095")
ADHD_API_KEY = os.getenv("ADHD_ENGINE_API_KEY", "")

# User Configuration
USER_ID = os.getenv("USER_ID", "hue")
