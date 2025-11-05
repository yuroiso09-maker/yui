#!/usr/bin/env python3
"""
OTIS - Optimization and Transformation Intelligence System
The ultimate Linux performance optimization and Windows compatibility suite
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="otis-optimizer",
    version="1.0.0",
    author="OTIS Development Team",
    author_email="dev@otis-optimizer.com",
    description="Ultimate Linux performance optimization and Windows compatibility suite",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/wilais363-cmd/otis",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Systems Administration",
        "Topic :: System :: Operating System",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "otis=core.main:main",
            "otis-gui=gui.main:main",
            "otis-cli=core.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.json", "*.conf", "*.sh"],
    },
    data_files=[
        ("share/otis/config", ["config/default.yaml"]),
        ("share/otis/scripts", ["scripts/install.sh", "scripts/uninstall.sh"]),
    ],
    zip_safe=False,
)