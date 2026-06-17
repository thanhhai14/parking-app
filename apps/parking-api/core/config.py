from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    APP_NAME: str = "parking-api"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    
    # DB connection
    DATABASE_URL: str = "postgresql+psycopg://parking:parking@localhost:5432/parking"
    
    # Redis connection
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # MinIO / S3
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_PUBLIC_ENDPOINT: str = "http://localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "parking-media"
    MINIO_SECURE: bool = False

    
    # JWT settings
    JWT_SECRET: str = "CHANGE_ME_USE_OPENSSL_RAND_HEX_32"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_SECONDS: int = 3600
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

settings = Settings()
