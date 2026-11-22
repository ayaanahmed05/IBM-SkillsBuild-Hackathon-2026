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

    # IBM watsonx.ai / Granite explanation layer. Keep secrets server-side only.
    watsonx_api_key: str = ''
    watsonx_project_id: str = ''
    watsonx_url: str = 'https://us-south.ml.cloud.ibm.com'
    watsonx_model_id: str = ''
    watsonx_api_version: str = '2024-05-31'
    watsonx_max_tokens: int = Field(default=120, ge=32, le=512)

    @property
    def watsonx_configured(self) -> bool:
        return all([self.watsonx_api_key, self.watsonx_project_id, self.watsonx_url, self.watsonx_model_id])
