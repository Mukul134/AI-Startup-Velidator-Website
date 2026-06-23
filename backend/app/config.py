import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "AI Startup Validator API"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = Field(..., validation_alias="DATABASE_URL")
    
    # Supabase (Auth and Storage)
    SUPABASE_URL: str = Field(..., validation_alias="SUPABASE_URL")
    SUPABASE_SERVICE_KEY: str = Field(..., validation_alias="SUPABASE_SERVICE_KEY")
    SUPABASE_JWT_SECRET: str = Field(..., validation_alias="SUPABASE_JWT_SECRET")
    
    # LLMs
    OPENAI_API_KEY: str = Field(default="", validation_alias="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str = Field(default="", validation_alias="ANTHROPIC_API_KEY")
    GEMINI_API_KEY: str = Field(default="", validation_alias="GEMINI_API_KEY")
    GOOGLE_API_KEY: str = Field(default="", validation_alias="GOOGLE_API_KEY")
    LLM_PROVIDER: str = Field(default="gemini", validation_alias="LLM_PROVIDER")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash", validation_alias="GEMINI_MODEL")
    OPENAI_MODEL: str = Field(default="gpt-4o", validation_alias="OPENAI_MODEL")
    RAZORPAY_KEY_ID: str = Field(default="", validation_alias="RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET: str = Field(default="", validation_alias="RAZORPAY_KEY_SECRET")
    PAYMENT_CURRENCY: str = Field(default="INR", validation_alias="PAYMENT_CURRENCY")
    
    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings(_env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
