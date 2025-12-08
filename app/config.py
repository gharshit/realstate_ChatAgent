##Imports
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Configuration class for the FastAPI app.

    Loads configuration from environment variables.
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

        # Max iterations from environment (default: 5)
        self.max_iterations = int(os.getenv("MAX_ITERATIONS", "5"))

        # Recreate database flag (for development only)
        self.recreate_db = os.getenv("RECREATE_DB", "false").lower() == "true"

        # API Key for authentication
        self.ADMIN_KEY = os.getenv("ADMIN_KEY")
        if not self.ADMIN_KEY:
            raise ValueError(
                "ADMIN_KEY environment variable is not set. "
                "Please set it in your .env file."
            )

        # JWT Secret Key for token signing
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY")
        if not self.jwt_secret_key:
            raise ValueError(
                "JWT_SECRET_KEY environment variable is not set. "
                "Please set it in your .env file (should be a secure random string)."
            )

        # JWT Token expiration time in hours (default: 1 hour)
        self.jwt_token_expiry_hours = int(os.getenv("JWT_TOKEN_EXPIRY_HOURS", "1"))


settings = Config()
print("\n  --- Settings loaded successfully! --- \n")