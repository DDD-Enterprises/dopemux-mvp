"""Setup script for interruption-shield package."""

from setuptools import setup, find_packages

setup(
    name="interruption-shield",
    version="0.1.0",
    description="Environmental interruption shield for ADHD developers",
    packages=find_packages(where=".", include=["interruption_shield*"]),
    python_requires=">=3.11",
    install_requires=[
        "aiohttp>=3.9.0",
        "slack-sdk>=3.23.0",
        "redis>=5.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "isort>=5.12.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
            "bandit[toml]>=1.7.5",
        ],
    },
)
