"""
Setup.py for ADHD Engine package
"""
from setuptools import setup, find_packages

setup(
    name="adhd-engine",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "pydantic",
        "redis",
        "httpx",
        "pytest",
        "pytest-asyncio"
    ],
    python_requires=">=3.9",
)