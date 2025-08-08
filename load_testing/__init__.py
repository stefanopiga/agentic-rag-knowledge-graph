"""
FisioRAG Scalability Testing Suite.

Comprehensive load testing, performance monitoring, and scalability validation.
"""

__version__ = "1.0.0"
__author__ = "FisioRAG Team"

from .config import LoadTestConfig, TestScenario, SCENARIO_CONFIGS

__all__ = [
    "LoadTestConfig",
    "TestScenario", 
    "SCENARIO_CONFIGS"
]
