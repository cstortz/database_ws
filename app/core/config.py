from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # PgBouncer Configuration
    PGBOUNCER_HOST: str = "localhost"
    PGBOUNCER_PORT: int = 5432
    DATABASE_NAME: str = "postgres"
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = "postgres"
    
    # Connection Pool Settings
    MIN_CONNECTIONS: int = 1
    MAX_CONNECTIONS: int = 10
    
    # Application Settings
    DEBUG: bool = True
    
    # Database URL (computed field)
    DATABASE_URL: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Build database URL
        self.DATABASE_URL = f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.PGBOUNCER_HOST}:{self.PGBOUNCER_PORT}/{self.DATABASE_NAME}"

settings = Settings() 