from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    APP_NAME: str = "parking-gateway"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_PORT: int = 8300
    
    # Redis connection
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    JWT_SECRET: str = "CHANGE_ME_USE_OPENSSL_RAND_HEX_32"
    JWT_ALGORITHM: str = "HS256"
    AGENT_TOKEN_SECRET: str = "CHANGE_ME_USE_OPENSSL_RAND_HEX_32"
    
    DEVICE_AGENT_TOKEN: str = "CHANGE_ME_DEVICE_AGENT_TOKEN"
    CAMERA_AGENT_TOKEN: str = "CHANGE_ME_CAMERA_AGENT_TOKEN"
    
    # Heartbeat settings
    GATEWAY_HEARTBEAT_INTERVAL: int = 30
    GATEWAY_HEARTBEAT_TIMEOUT: int = 90

settings = Settings()
