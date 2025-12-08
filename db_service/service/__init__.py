"""
Database Service Module.

This module provides database table creation and data seeding functionality.
"""

from .create_tables import create_all_tables, drop_all_tables
from .insert_data_projects import insert_projects_data

__all__ = [
    'create_all_tables',
    'drop_all_tables',
    'insert_projects_data',
]
