from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    API_V1_STR: str = "/api/v1"
    project_name: str = "Particule"
    database_url: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 2880
    

settings = Settings()