from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    token: str
    admin_id : int
    url_sms_activate: str
    url_api_sms: str

    model_config = SettingsConfigDict(env_file = ".env") 