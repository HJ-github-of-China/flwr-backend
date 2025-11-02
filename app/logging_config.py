import os
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from flask import Flask


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
    
    # 文件日志处理器 - 按天轮转
    file_handler = TimedRotatingFileHandler(
        os.path.join(logs_dir, 'app.log'),
        when='midnight',
        interval=1,
        backupCount=app.config.get('LOG_FILE_BACKUP_COUNT', 30),
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 错误日志处理器 - 按天轮转
    error_handler = TimedRotatingFileHandler(
        os.path.join(logs_dir, 'error.log'),
        when='midnight',
        interval=1,
        backupCount=app.config.get('LOG_FILE_BACKUP_COUNT', 30),
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
        '%(asctime)s %(remote_addr)s:%(remote_port)s %(request_method)s %(url)s %(status_code)s %(response_time)f'
    )
    access_handler.setFormatter(access_formatter)
    
    # 访问日志控制台处理器
    access_console_handler = logging.StreamHandler()
    access_console_handler.setLevel(logging.INFO)
    access_console_handler.setFormatter(access_formatter)
    
    # 只在非调试模式下添加控制台处理器，避免日志重复
    if not app.debug:
        # 控制台日志处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # 控制台日志处理器（始终添加）
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
    
    @app.after_request
    def after_request(response):
        from flask import request, g
        import time
        # 记录访问日志
        if hasattr(g, 'start_time'):
            response_time = time.time() - g.start_time
        else:
            response_time = 0
        
        # 获取客户端IP地址
        if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
            remote_addr = request.environ.get('REMOTE_ADDR', 'unknown')
        else:
            remote_addr = request.environ.get('HTTP_X_FORWARDED_FOR', 'unknown')
            
        access_info = {
            'remote_addr': remote_addr,
            'remote_port': request.environ.get('REMOTE_PORT', 'unknown'),
            'request_method': request.method,
            'url': request.url,
            'status_code': response.status_code,
            'response_time': response_time
        }
        
        # 直接使用app.logger记录访问信息，确保在控制台可见
        app.logger.info(
            f"{access_info['remote_addr']}:{access_info['remote_port']} "
            f"{access_info['request_method']} {access_info['url']} "
            f"{access_info['status_code']} {access_info['response_time']:.6f}"
        )
        
        # 同时写入访问日志文件
        try:
            access_handler = TimedRotatingFileHandler(
                os.path.join(logs_dir, 'access.log'),
                when='midnight',
                interval=1,
                backupCount=app.config.get('ACCESS_LOG_FILE_BACKUP_COUNT', 30),
                encoding='utf-8'
            )
            access_formatter = logging.Formatter(
                '%(asctime)s %(remote_addr)s:%(remote_port)s %(request_method)s %(url)s %(status_code)s %(response_time)f'
            )
            access_handler.setFormatter(access_formatter)
            access_handler.setLevel(logging.INFO)
            
            access_logger = logging.getLogger('access_logger')
            access_logger.setLevel(logging.INFO)
            access_logger.addHandler(access_handler)
            access_logger.propagate = False
            
            access_logger.info(
                '%(remote_addr)s:%(remote_port)s %(request_method)s %(url)s %(status_code)s %(response_time)f',
                extra=access_info
            )
        except Exception as e:
            app.logger.error(f"无法写入访问日志文件: {e}")
        
        return response
    
    # 记录应用启动日志
    app.logger.info('Flask应用日志系统初始化完成')