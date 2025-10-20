import uuid
from flask import current_app

"""定义响应体"""
def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def generate_filename(original_filename, data_type):
    """生成唯一的文件名"""
    ext = original_filename.rsplit('.', 1)[1].lower()
    filename = f"{data_type}_{uuid.uuid4().hex}.{ext}"
    return filename


class ResponseUtil:
    """响应工具类"""

    @staticmethod
    def success(data=None, message="success"):
        return {
            "code": 200,
            "message": message,
            "data": data
        }

    @staticmethod
    def error(code=500, message="服务器内部错误"):
        return {
            "code": code,
            "message": message,
            "data": None
        }, code

    @staticmethod
    def pagination_success(data_list, pagination):
        return {
            "code": 200,
            "message": "success",
            "data": {
                "list": data_list,
                "pagination": pagination
            }
        }


# 文件工具类
class FileUtil:

    @staticmethod
    def allowed_file(filename, allowed_extensions):
        """检查文件类型"""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in allowed_extensions