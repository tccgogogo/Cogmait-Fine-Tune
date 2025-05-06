import os
import yaml
from pydantic_settings import BaseSettings

# 日志、模型输出的根路径
CLIENT_CLI_OUTPUT = '/home/tiancongcong/code/cogmait-fine-tune/finetune-output'
# 已发布模型的根目录
MODEL_ROOT_DIR = '/home/tiancongcong/code/cogmait-fine-tune/models/model_repository'

class Settings(BaseSettings):
    redis_url: str = None

def load_settings_from_yaml(path: str):
    if '/' not in path:
        path = os.path.join(os.path.dirname(__file__), path)

    with open(path, "r", encoding="utf-8") as f:
        settings_dict = yaml.safe_load(f)
    for key, value in settings_dict.items():
        if key not in Settings.__fields__.keys():
            raise ValueError(f"Invalid setting: {key}")
    return Settings(**settings_dict)

settings = load_settings_from_yaml("config.yaml")
print(settings)