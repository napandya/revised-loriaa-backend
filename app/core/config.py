"""Application configuration using Pydantic settings."""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field
import json


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://loriaa_user:loriaa_pass@localhost:5432/loriaa_db",
        description="PostgreSQL database URL"
    )
    
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for caching and background tasks"
    )
    
    # Security
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT token generation"
    )
    
    ALGORITHM: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="JWT token expiration time in minutes"
    )
    
    # AI/LLM
    GOOGLE_API_KEY: str = Field(
        default="",
        description="Google API key for Gemini"
    )
    
    GEMINI_MODEL: str = Field(
        default="gemini-2.0-flash-exp",
        description="Gemini model name"
    )
    
    OPENAI_API_KEY: str = Field(
        default="",
        description="OpenAI API key for embeddings (backward compatibility)"
    )
    
    # Vapi Voice
    VAPI_API_KEY: str = Field(
        default="",
        description="Vapi API key"
    )
    
    VAPI_WEBHOOK_SECRET: str = Field(
        default="",
        description="Vapi webhook secret"
    )
    
    VAPI_BASE_URL: str = Field(
        default="https://api.vapi.ai",
        description="Vapi base URL"
    )
    
    ELEVENLABS_API_KEY: str = Field(
        default="",
        description="ElevenLabs API key for premium voices"
    )
    
    # Facebook Ads
    FACEBOOK_APP_ID: str = Field(
        default="",
        description="Facebook App ID"
    )
    
    FACEBOOK_APP_SECRET: str = Field(
        default="",
        description="Facebook App Secret"
    )
    
    FACEBOOK_ACCESS_TOKEN: str = Field(
        default="",
        description="Facebook Access Token"
    )
    
    FACEBOOK_WEBHOOK_VERIFY_TOKEN: str = Field(
        default="",
        description="Facebook Webhook Verify Token"
    )
    
    # Google Ads
    GOOGLE_ADS_DEVELOPER_TOKEN: str = Field(
        default="",
        description="Google Ads Developer Token"
    )
    
    GOOGLE_ADS_CLIENT_ID: str = Field(
        default="",
        description="Google Ads Client ID"
    )
    
    GOOGLE_ADS_CLIENT_SECRET: str = Field(
        default="",
        description="Google Ads Client Secret"
    )
    
    GOOGLE_ADS_REFRESH_TOKEN: str = Field(
        default="",
        description="Google Ads Refresh Token"
    )
    
    GOOGLE_ADS_CUSTOMER_ID: str = Field(
        default="",
        description="Google Ads Customer ID"
    )
    
    # Twilio
    TWILIO_ACCOUNT_SID: str = Field(
        default="",
        description="Twilio Account SID"
    )
    
    TWILIO_AUTH_TOKEN: str = Field(
        default="",
        description="Twilio Auth Token"
    )
    
    TWILIO_PHONE_NUMBER: str = Field(
        default="",
        description="Twilio Phone Number"
    )
    
    # ResMan PMS
    RESMAN_API_KEY: str = Field(
        default="",
        description="ResMan API Key"
    )
    
    RESMAN_INTEGRATION_PARTNER_ID: str = Field(
        default="",
        description="ResMan Integration Partner ID"
    )
    
    RESMAN_BASE_URL: str = Field(
        default="https://api.resman.com",
        description="ResMan base URL"
    )
    
    # Email
    SENDGRID_API_KEY: str = Field(
        default="",
        description="SendGrid API Key"
    )
    
    FROM_EMAIL: str = Field(
        default="noreply@loriaa.ai",
        description="From email address"
    )
    
    # CORS
    CORS_ORIGINS: str = Field(
        default='["http://localhost:5173","http://localhost:3000"]',
        description="CORS allowed origins as JSON array string"
    )
    
    # GCP
    GCP_PROJECT_ID: str = Field(
        default="",
        description="GCP Project ID"
    )
    
    GCP_REGION: str = Field(
        default="us-central1",
        description="GCP Region"
    )
    
    CLOUD_STORAGE_BUCKET: str = Field(
        default="",
        description="Cloud Storage Bucket for documents"
    )
    
    # Monitoring
    SENTRY_DSN: str = Field(
        default="",
        description="Sentry DSN for error tracking"
    )
    
    # Environment
    ENVIRONMENT: str = Field(
        default="development",
        description="Environment (development, staging, production)"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from JSON string to list."""
        try:
            return json.loads(self.CORS_ORIGINS)
        except json.JSONDecodeError:
            return ["http://localhost:5173"]


# Global settings instance
settings = Settings()
