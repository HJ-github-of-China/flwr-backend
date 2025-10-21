import oss2
import logging
from flask import current_app
from app.utils import generate_filename


# 获取日志记录器
logger = logging.getLogger(__name__)

class OSSService:
    """阿里云OSS服务"""

    def __init__(self):
        self.auth = None
        self.bucket = None

    def init_app(self, app):
        """在应用上下文中初始化OSS服务"""
        try:
            # 检查必要配置是否存在
            required_configs = ['OSS_ACCESS_KEY_ID', 'OSS_ACCESS_KEY_SECRET', 'OSS_ENDPOINT', 'OSS_BUCKET_NAME']
            for config_key in required_configs:
                if not app.config.get(config_key):
                    logger.error(f"缺少必要的OSS配置: {config_key}")
                    return

            with app.app_context():
                self.auth = oss2.Auth(
                    app.config['OSS_ACCESS_KEY_ID'],
                    app.config['OSS_ACCESS_KEY_SECRET']
                )
                self.bucket = oss2.Bucket(
                    self.auth,
                    app.config['OSS_ENDPOINT'],
                    app.config['OSS_BUCKET_NAME']
                )
                logger.info("OSS服务初始化成功")
        except Exception as e:
            logger.error(f"OSS服务初始化失败: {str(e)}", exc_info=True)
            self.bucket = None

    def upload_image(self, file, data_type):
        """上传图片到OSS"""
        # 检查服务是否已初始化
        if self.bucket is None:
            logger.error("OSS服务未初始化，无法上传图片")
            return None, None, "OSS服务未初始化"

        try:
            # 生成文件名
            filename = generate_filename(file.filename, data_type)

            # 确保文件指针在起始位置
            file.seek(0)

            # 上传原始图片
            result = self.bucket.put_object(f'images/{filename}', file)
            if result.status != 200:
                return None, None, "上传失败"

            image_url = f"https://{current_app.config['OSS_BUCKET_NAME']}.{current_app.config['OSS_ENDPOINT']}/images/{filename}"

            # # 这里可以添加生成缩略图的逻辑
            # # 暂时使用相同的URL作为缩略图
            # thumbnail_url = image_url

            return image_url, None

        except Exception as e:
            logger.error(f"上传图片到OSS失败: {str(e)}", exc_info=True)
            return None, None, str(e)

    def upload_pdf(self, pdf_buffer, filename):
        """上传PDF文件到OSS"""
        # 检查服务是否已初始化
        if self.bucket is None:
            logger.error("OSS服务未初始化，无法上传PDF")
            return None

        try:
            # 确保buffer指针在起始位置
            pdf_buffer.seek(0)

            # 上传PDF文件
            result = self.bucket.put_object(filename, pdf_buffer)
            if result.status != 200:
                return None

            pdf_url = f"https://{current_app.config['OSS_BUCKET_NAME']}.{current_app.config['OSS_ENDPOINT']}/{filename}"
            logger.info(f"PDF上传成功: {pdf_url}")
            return pdf_url

        except Exception as e:
            logger.error(f"上传PDF到OSS失败: {str(e)}", exc_info=True)
            return None


# 创建全局OSS服务实例
oss_service = OSSService()