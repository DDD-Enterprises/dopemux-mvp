from setuptools import setup, find_packages

setup(
    name="mcp-client-python",
    version="1.0.0",
    description="Custom MCP client for Dopemux in Python",
    author="Dopemux Team",
    packages=find_packages(),
    install_requires=[
        "mcp>=1.0.0",
        "aiohttp>=3.9.0",
    ],
    entry_points={
        "console_scripts": [
            "mcp-client=mcp_client.main:cli",
        ],
    },
    python_requires=">=3.11",
)
