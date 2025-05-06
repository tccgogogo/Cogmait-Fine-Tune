import os
import yaml
from pydantic_settings import BaseSettings
from pydantic import validator
from cryptography.fernet import Fernet

# 日志、模型输出的根路径
CLIENT_CLI_OUTPUT = '/home/tiancongcong/code/cogmait-fine-tune/finetune-output'
# 已发布模型的根目录
MODEL_ROOT_DIR = '/home/tiancongcong/code/cogmait-fine-tune/models/model_repository'

secret_key = 'TI31VYJ-ldAq-FXo5QNPKV_lqGTFfp-MIdbK2Hm5F1E='

def encrypt_token(token: str):
    return Fernet(secret_key).encrypt(token.encode())


def decrypt_token(token: str):
    return Fernet(secret_key).decrypt(token).decode()

class Settings(BaseSettings):
    redis_url: str = None

    @validator('redis_url')
    @classmethod
    def set_redis_url(cls, v: str):
        import re
        pattern = r'(?<=:)[^:]+(?=@)'  # 匹配冒号后面到@符号前面的任意字符
        match = re.search(pattern, v)
        if match:
            password = match.group(0)
            new_password = decrypt_token(password)
            new_redis_url = re.sub(pattern, f'{new_password}', v)
            return new_redis_url
        # 无账号密码
        return v
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