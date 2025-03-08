from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

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
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings():
    """
    Get cached settings to avoid loading from environment variables on every request
    """
    return Settings() 