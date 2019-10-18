import logging
from redis import StrictRedis

class Config(object):
    """ 项目配置"""
    SECRET_KEY = "iECgbYWReMNxkRprrzMo5KAQYnb2UeZ3bwvReTSt+VSESW0OB8zbglT+6rEcDW9X"
    #　为数据库库添加配置
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://lgl:123456@127.0.0.1:3306/flask_project"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 在请求结束的时候,如果指定此配置为True,那么SQLALchemy会自动执行一次db.session.commit()操作
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    # Redis的配置
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379
    # Session保存配置
    SESSION_TYPE = 'redis'
    # 开启session签名
    SESSION_USE_SIGNER = True
    # 指定 Session 保存的 redis
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # 设置需要过期
    SESSION_PERMANENT = False
    # 设置过期时间
    PERMANENT_SESSION_LIFETIME = 86400 * 7
    # 设置日志等级
    LOG_LEVEL = logging.DEBUG
class DevelopmentConfig(Config):
    """开发环境"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境"""
    DEBUG = False
    LOG_LEVEL = logging.WARNING


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


