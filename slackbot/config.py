import os
from pydantic import BaseModel


class Config(BaseModel):
    slack_token: str
    slack_signing_secret: str
    slack_command: str
    port: int

    class Config:
        extra = "ignore"  # ignore additional keys


env_config = os.environ
config = Config(**env_config)