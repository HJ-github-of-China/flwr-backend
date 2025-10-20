from flask import Blueprint, request, current_app
from app.services.federated_data_service import FederatedDataService
from app.services.oss_service import oss_service
from app.utils import ResponseUtil, allowed_file
from functools import wraps

federated_data_bp = Blueprint('federated_data', __name__)


# def token_required(f):
#     """Token认证装饰器"""
#
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         token = request.headers.get('Authorization')
#         if not token:
#             return ResponseUtil.error(401, "未授权访问")
#
#         try:
#             # 移除Bearer前缀
#             if token.startswith('Bearer '):
#                 token = token[7:]
#
#             # 验证token
#             jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
#         except jwt.ExpiredSignatureError:
#             return ResponseUtil.error(401, "Token已过期")
#         except jwt.InvalidTokenError:
#             return ResponseUtil.error(401, "无效Token")
#
#         return f(*args, **kwargs)
#
#     return decorated


@federated_data_bp.route('/api/v1/federated-data', methods=['POST'])
# @token_required
def create_data():
    """创建新数据"""
    # 处理文件上传和表单数据
    if 'file' not in request.files:
        return ResponseUtil.error(400, "缺少文件")

    file = request.files['file']
    if file.filename == '':
        return ResponseUtil.error(400, "没有选择文件")

    if not allowed_file(file.filename):
        return ResponseUtil.error(400, "不支持的文件类型")

    # 获取表单数据
    case_description = request.form.get('caseDescription')
    file_size = request.form.get('fileSize')
    data_type = request.form.get('dataType', 'chest_xray')

    if not case_description:
        return ResponseUtil.error(400, "缺少必要字段: caseDescription")

    # 上传图片到OSS
    image_url, error = oss_service.upload_image(file, data_type)
    if error:
        return ResponseUtil.error(500, f"文件上传失败: {error}")

    # 创建数据记录
    data_obj, error = FederatedDataService.create_data(
        case_description=case_description,
        image_url=image_url,
        file_size=file_size,
        data_type=data_type
    )

    if error:
        return ResponseUtil.error(500, error)

    return ResponseUtil.success(data_obj.to_dict(), "数据创建成功")


@federated_data_bp.route('/api/v1/federated-data/<int:data_id>', methods=['DELETE'])
# @token_required
def delete_data(data_id):
    """删除数据"""
    success, error = FederatedDataService.delete_data(data_id)

    if not success:
        return ResponseUtil.error(404 if error == "数据不存在" else 500, error)

    return ResponseUtil.success(message="数据删除成功")


@federated_data_bp.route('/api/v1/federated-data', methods=['GET'])
# @token_required
def get_data_list():
    """获取数据列表（分页）"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', current_app.config['DEFAULT_PAGE_SIZE'], type=int)

    # 限制每页大小
    page_size = min(page_size, current_app.config['MAX_PAGE_SIZE'])

    data_list, pagination = FederatedDataService.get_paginated_data(page, page_size)

    return ResponseUtil.pagination_success(
        [data.to_simple_dict() for data in data_list],
        pagination
    )


@federated_data_bp.route('/api/v1/federated-data/search', methods=['GET'])
# @token_required
def search_data():
    """根据关键词搜索"""
    keyword = request.args.get('keyword')
    if not keyword:
        return ResponseUtil.error(400, "搜索关键词不能为空")

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', current_app.config['DEFAULT_PAGE_SIZE'], type=int)
    page_size = min(page_size, current_app.config['MAX_PAGE_SIZE'])

    data_list, pagination = FederatedDataService.search_by_keyword(keyword, page, page_size)

    return ResponseUtil.pagination_success(
        [data.to_simple_dict() for data in data_list],
        pagination
    )


@federated_data_bp.route('/api/v1/federated-data/by-time', methods=['GET'])
# @token_required
def get_data_by_time():
    """根据时间范围查询"""
    start_time = request.args.get('startTime')
    end_time = request.args.get('endTime')

    if not start_time or not end_time:
        return ResponseUtil.error(400, "开始时间和结束时间不能为空")

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', current_app.config['DEFAULT_PAGE_SIZE'], type=int)
    page_size = min(page_size, current_app.config['MAX_PAGE_SIZE'])

    data_list, pagination = FederatedDataService.get_data_by_time_range(start_time, end_time, page, page_size)

    return ResponseUtil.pagination_success(
        [data.to_simple_dict() for data in data_list],
        pagination
    )


@federated_data_bp.route('/api/v1/federated-data/<int:data_id>', methods=['PUT'])
# @token_required
def update_data(data_id):
    """更新数据"""
    data = request.get_json()

    if not data:
        return ResponseUtil.error(404, "请求参数错误")

    case_description = data.get('caseDescription')
    image_url = data.get('imageUrl')
    data_type = data.get('dataType')

    data_obj, error = FederatedDataService.update_data(
        data_id=data_id,
        case_description=case_description,
        image_url=image_url,
        data_type=data_type
    )

    if error:
        return ResponseUtil.error(404 if error == "数据不存在" else 500, error)

    return ResponseUtil.success(data_obj.to_dict(), "数据更新成功")


@federated_data_bp.route('/api/v1/upload/image', methods=['POST'])
# @token_required
def upload_image():
    """上传图片到OSS"""
    if 'file' not in request.files:
        return ResponseUtil.error(400, "没有文件")

    file = request.files['file']
    data_type = request.form.get('dataType', 'other')

    if file.filename == '':
        return ResponseUtil.error(400, "没有选择文件")

    if not allowed_file(file.filename):
        return ResponseUtil.error(400, "不支持的文件类型")

    image_url, error = oss_service.upload_image(file, data_type)

    if error:
        return ResponseUtil.error(500, f"上传失败: {error}")

    return ResponseUtil.success({
        "imageUrl": image_url,
    }, "文件上传成功")