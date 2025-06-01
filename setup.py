"""Setup script for the LitLum package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="litlum",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Scientific publication monitoring and analysis application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/litlum",
    packages=find_packages(),
    package_data={
        'litlum.config': ['default-config.yaml'],
    },
    install_requires=[
        'PyYAML>=6.0',
        'requests>=2.25.0',
        'feedparser>=6.0.0',
        'python-dateutil>=2.8.0',
        'rich>=10.0.0',
    ],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'litlum=litlum:main',
        ],
    },
)
