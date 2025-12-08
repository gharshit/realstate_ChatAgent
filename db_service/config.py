"""
Database Configuration Module.

This module provides configuration settings for the database service,
including PostgreSQL connection URL and CSV data paths.

Environment Variables Required:
    DATABASE_URL: PostgreSQL connection URL (format: postgresql://user:password@host:port/database)
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Configuration class for database service.
    
    Loads and provides access to database connection settings and file paths.
    """
    
    def __init__(self):
        # PostgreSQL connection URL from environment
        self.database_url = os.getenv("DATABASE_URL")
        
        if not self.database_url:
            raise ValueError(
                "DATABASE_URL environment variable is not set. "
                "Please set it in your .env file with format: "
                "postgresql://user:password@host:port/database"
            )
        
        # CSV data path for seeding
        self.csv_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'service', 'ProplensData.csv')
        )
        
        # Recreate database flag (for development only - drops all tables)
        self.recreate_db = os.getenv("RECREATE_DB", "false").lower() == "true"
        
        #jwt_secret_key
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY")
        
        # admin key
        self.admin_key = os.getenv("ADMIN_KEY")


# Global settings instance
settings = Config()
