"""
Setup script for PyRush stress testing application
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pyrush",
    version="1.0.0",
    author="PyRush Team",
    description="Modern stress testing application for web applications and APIs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Testing",
        "Topic :: Internet :: WWW/HTTP",
    ],
    python_requires=">=3.7",
    install_requires=[
        "aiohttp>=3.8.0",
        "tqdm>=4.64.0",
        "reportlab>=3.6.0",
        "matplotlib>=3.5.0",
        "certifi>=2022.0.0",
    ],
    entry_points={
        "console_scripts": [
            "pyrush=pyrush.cli:main",
        ],
    },
    keywords="stress testing, load testing, performance testing, http, api, web",
    project_urls={
        "Bug Reports": "https://github.com/ianoit/pyrush/issues",
        "Source": "https://github.com/ianoit/pyrush",
    },
) 