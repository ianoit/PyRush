"""
PyRush - Modern stress testing application for web applications and APIs
"""

__version__ = "1.0.0"
__author__ = "PyRush Team"

# Import main classes for easy access
from .models import RequestResult, TestConfig
from .core import StressTester
from .config import parse_duration
from .cli import main

__all__ = ['RequestResult', 'TestConfig', 'StressTester', 'parse_duration', 'main'] 