import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from app.config import config
from app.models import db
from app.services.oss_service import oss_service
from app.logging_config import setup_logging

load_dotenv()
# 显式告诉SQLAlchemy使用PyMySQL


def create_app(config_name='default'):
    """创建Flask应用"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    CORS(app)

    # 初始化OSS服务
    oss_service.init_app(app)

    # 设置日志系统
    setup_logging(app)

    # 注册蓝图
    from app.routes.auth_routes import auth_bp
    from app.routes.federated_data_routes import federated_data_bp
    from app.routes.model_routes import model_bp
    from app.routes.diagnosis_routes import diagnosis_bp  # 新增导入诊断蓝图
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(federated_data_bp)
    app.register_blueprint(model_bp)
    app.register_blueprint(diagnosis_bp)  # 注册诊断蓝图

    # 创建数据库表
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("数据库表初始化完成")
        except Exception as e:
            app.logger.error(f"数据库表初始化失败: {e}")

    return app