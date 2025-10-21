import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

class Config:
    """基础配置"""
    SECRET_KEY = os.getenv('SECRET_KEY')

    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True
    }

    # TODO JWT配置
    # JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY') or 'jwt-secret-key'
    # JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # 阿里云OSS配置
    OSS_ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID')
    OSS_ACCESS_KEY_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET')
    OSS_ENDPOINT = os.getenv('OSS_ENDPOINT')
    OSS_BUCKET_NAME = os.getenv('OSS_BUCKET_NAME')

    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

    # 分页配置
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100

    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_FILE_BACKUP_COUNT = 10
    ACCESS_LOG_FILE_BACKUP_COUNT = 30

    ENABLE_OSS = os.getenv('ENABLE_OSS', 'false').lower() == 'true'

    # 大模型API配置
    LLM_API_CONFIG = {
        'api_url': os.getenv('LLM_API_URL'),
        'api_key': os.getenv('LLM_API_KEY'),
        'model': os.getenv('LLM_MODEL', 'qwen-max')
    }


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}