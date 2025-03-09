from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv
import secrets

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # Setu API credentials
    setu_client_id: str = os.getenv("SETU_CLIENT_ID", "")
    setu_client_secret: str = os.getenv("SETU_CLIENT_SECRET", "")
    setu_product_instance_pan_id: str = os.getenv("SETU_PRODUCT_INSTANCE_PAN_ID", "")
    setu_product_instance_rpd_id: str = os.getenv("SETU_PRODUCT_INSTANCE_RPD_ID", "")
    
    # Setu API base URL (sandbox or production)
    setu_base_url: str = os.getenv("SETU_BASE_URL", "https://dg-sandbox.setu.co")
    
    # Database configuration
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./setu_api.db")
    
    # JWT configuration
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_access_token_expire_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings():
    """
    Get cached settings to avoid loading from environment variables on every request
    """
    return Settings() 