import os
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from flask import Flask


# TODO 修改展示暴露的ip和端口
def setup_logging(app: Flask):
    
    """
    配置Flask应用的日志系统
    """
    # 创建logs目录（如果不存在）
    logs_dir = os.path.join(app.root_path, '..', 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # 设置日志级别
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper(), logging.INFO)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    
    # 文件日志处理器 - 按大小轮转
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'app.log'),
        maxBytes=app.config.get('LOG_FILE_MAX_BYTES', 1024 * 1024 * 10),  # 默认10MB
        backupCount=app.config.get('LOG_FILE_BACKUP_COUNT', 10),
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 错误日志处理器 - 专门记录错误信息
    error_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'error.log'),
        maxBytes=app.config.get('LOG_FILE_MAX_BYTES', 1024 * 1024 * 10),  # 默认10MB
        backupCount=app.config.get('LOG_FILE_BACKUP_COUNT', 10),
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # 按天轮转的访问日志处理器
    access_handler = TimedRotatingFileHandler(
        os.path.join(logs_dir, 'access.log'),
        when='midnight',
        interval=1,
        backupCount=app.config.get('ACCESS_LOG_FILE_BACKUP_COUNT', 30),
        encoding='utf-8'
    )
    access_handler.setLevel(logging.INFO)
    access_formatter = logging.Formatter(
        '%(asctime)s %(remote_addr)s %(url)s %(status_code)s %(response_time)f'
    )
    access_handler.setFormatter(access_formatter)
    
    # 只在非调试模式下添加控制台处理器，避免日志重复
    if not app.debug:
        # 控制台日志处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # 配置Flask应用使用日志
    app.logger.setLevel(log_level)
    
    # 添加访问日志中间件
    @app.before_request
    def before_request():
        from flask import request, g
        import time
        g.start_time = time.time()
        request.environ['REMOTE_ADDR'] = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
    
    @app.after_request
    def after_request(response):
        from flask import request, g
        import time
        # 记录访问日志
        if hasattr(g, 'start_time'):
            response_time = time.time() - g.start_time
        else:
            response_time = 0
        
        access_info = {
            'remote_addr': request.environ.get('REMOTE_ADDR', 'unknown'),
            'url': request.url,
            'status_code': response.status_code,
            'response_time': response_time
        }
        
        # 使用专门的访问日志记录器
        access_logger = logging.getLogger('access')
        access_logger.setLevel(logging.INFO)
        access_logger.addHandler(access_handler)
        access_logger.propagate = False  # 防止传播到根日志记录器
        
        access_logger.info(
            '%(remote_addr)s %(url)s %(status_code)s %(response_time)f',
            access_info,
            extra=access_info
        )
        
        return response
    
    # 记录应用启动日志
    app.logger.info('Flask应用日志系统初始化完成')