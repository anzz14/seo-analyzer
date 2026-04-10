from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	DATABASE_URL: str
	REDIS_URL: str
	JWT_SECRET_KEY: str
	JWT_ALGORITHM: str = "HS256"
	JWT_EXPIRY_HOURS: int = 24
	UPLOAD_DIR: str = "./storage/uploads"
	MAX_UPLOAD_SIZE_BYTES: int = 5242880
	CELERY_BROKER_URL: str
	CELERY_RESULT_BACKEND: str
	FRONTEND_ORIGIN: str = "http://localhost:3000"

	model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
