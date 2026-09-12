"""Compatibility shim for tools that still invoke `python setup.py ...` directly.

All package metadata lives in pyproject.toml; setuptools reads it from there.
"""
from setuptools import setup

setup()
