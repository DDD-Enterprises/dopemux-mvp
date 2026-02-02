"""Setup for Dope-Context MCP package."""

from setuptools import setup, find_packages

setup(
    name="dope-context-mcp",
    version="1.0.0",
    description="MCP Server for Dope-Context semantic search",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        # Core dependencies are in root requirements.txt
    ],
)
