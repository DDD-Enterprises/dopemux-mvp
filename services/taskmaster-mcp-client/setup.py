from setuptools import setup, find_packages

setup(
    name="taskmaster-mcp-client",
    version="1.0.0",
    description="TaskMaster MCP client for Dopemux - connects to stdio and HTTP MCP servers",
    author="Dopemux Team",
    packages=find_packages(),
    install_requires=[
        "mcp>=1.0.0",
        "aiohttp>=3.9.0",
    ],
    entry_points={
        "console_scripts": [
            "taskmaster-mcp=mcp_client.main:cli",
        ],
    },
    python_requires=">=3.11",
)
