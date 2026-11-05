from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    database_url: str = 'sqlite:///./momentguard.db'
    frontend_origin: str = 'http://localhost:5173'
    api_token: str = ''
    automatic: bool = False
    risk_threshold: int = Field(default=75, ge=0, le=100)
    safety_buffer_minutes: float = Field(default=0.5, ge=0, le=30)
    agent_timeout_seconds: float = Field(default=12, gt=0, le=120)
