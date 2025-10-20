import oss2
from flask import current_app
from app.utils import generate_filename


class OSSService:
    """阿里云OSS服务"""

    def __init__(self):
        self.auth = None
        self.bucket = None

    def init_app(self, app):
        """在应用上下文中初始化OSS服务"""
        with app.app_context():
            self.auth = oss2.Auth(
                current_app.config['OSS_ACCESS_KEY_ID'],
                current_app.config['OSS_ACCESS_KEY_SECRET']
            )
            self.bucket = oss2.Bucket(
                self.auth,
                current_app.config['OSS_ENDPOINT'],
                current_app.config['OSS_BUCKET_NAME']
            )

    def upload_image(self, file, data_type):
        """上传图片到OSS"""
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
            return None, None, str(e)

    def upload_pdf(self, pdf_buffer, filename):
        """上传PDF文件到OSS"""
        try:
            # 确保buffer指针在起始位置
            pdf_buffer.seek(0)

            # 上传PDF文件
            result = self.bucket.put_object(filename, pdf_buffer)
            if result.status != 200:
                return None

            pdf_url = f"https://{current_app.config['OSS_BUCKET_NAME']}.{current_app.config['OSS_ENDPOINT']}/{filename}"
            return pdf_url

        except Exception as e:
            return None


# 创建全局OSS服务实例
oss_service = OSSService()