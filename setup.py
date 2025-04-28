"""Setup file for Clara Engine."""

from setuptools import find_packages, setup

setup(
    name="clara_engine",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "tweepy>=4.14.0",
        "supabase>=2.0.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "pytz>=2024.1",
        "tenacity>=8.0.0",
        "structlog>=24.1.0",
    ],
    python_requires=">=3.9.6",
    author="Clara Engine Team",
    description="Multi-tenant AI Twitter Bot Platform",
    license="MIT",
) 