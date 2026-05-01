"""
UI TESTER - Module for TLDRDC Interactive UI Testing
=====================================================

This package provides a standalone testing interface for TLDRDC UI components
without modifying the original game files.

Structure:
    mocks.py    - Global state, reactive personaje, mock functions
    parser.py   - Interactive parser for tester commands
    main.py     - Entry point (execute this file)

Usage:
    python main.py
"""

__version__ = "1.0.0"
__phase__ = "1 - Básico (Armas + Parser)"

# Cuando se importe ui_tester como módulo, exponer las clases principales
from .mocks import personaje_global, estado
from .parser import TesterParser

__all__ = ['personaje_global', 'estado', 'TesterParser']
