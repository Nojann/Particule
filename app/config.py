from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    API_V1_STR: str = "/api/v1"
    project_name: str = "Particule"
    database_url: str
    

settings = Settings()