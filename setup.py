"""Setup script for the publication reader package."""

from setuptools import setup, find_packages

setup(
    name="litlum",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "feedparser",
        "requests",
        "rich",
        "pyyaml",
        "ollama",
    ],
    entry_points={
        "console_scripts": [
            "litlum=litlum.__main__:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A scientific publication monitoring and analysis application",
    keywords="scientific, publications, rss, llm, ollama",
    python_requires=">=3.8",
)
