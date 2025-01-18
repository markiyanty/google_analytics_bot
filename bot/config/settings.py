from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    tg_bot_api_key: str
    ga_measurement_id: str
    allowed_chats: str
    allowed_users:  str
    ga_credentials: str
    gm_credentials: str
    db_link: str
    jira_base_url: str
    jira_email: str
    jira_api_token: str
    ga_id: str

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()



