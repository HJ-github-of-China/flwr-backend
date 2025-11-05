from flask import Blueprint, request, current_app
from app.services.model_service import ModelService
from app.utils import ResponseUtil
from app.utils.auth import token_required, roles_required

model_bp = Blueprint('model', __name__, url_prefix='/api')


@model_bp.route('/models', methods=['POST'])
@token_required
@roles_required('admin')
def create_model(current_user):
    """创建新模型"""
    data = request.get_json()

    if not data:
        return ResponseUtil.error(400, "请求参数错误")

    # 必填字段验证
    required_fields = ['model_name', 'algorithm']
    for field in required_fields:
        if field not in data or not data[field]:
            return ResponseUtil.error(400, f"缺少必要字段: {field}")

    # 创建模型
    model, error = ModelService.create_model(data)

    if error:
        return ResponseUtil.error(400 if "已存在" in error else 500, error)

    return ResponseUtil.success({
        'model': model.to_dict(),
        'message': '模型创建成功'
    })


@model_bp.route('/models', methods=['GET'])
@token_required
def get_models(current_user):
    """查询模型列表（支持分页、搜索、筛选）"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', current_app.config['DEFAULT_PAGE_SIZE'], type=int)
        page_size = min(page_size, current_app.config['MAX_PAGE_SIZE'])

        model_name = request.args.get('model_name', '').strip()
        model_status = request.args.get('model_status', '')
        sort_by = request.args.get('sort_by', 'created_time')
        sort_order = request.args.get('sort_order', 'desc')

        filters = {
            'model_name': model_name,
            'model_status': model_status,
            'sort_by': sort_by,
            'sort_order': sort_order
        }

        # 获取模型列表
        models, pagination = ModelService.get_paginated_models(page, page_size, filters)

        # 获取选项数据
        status_options = ModelService.get_model_status_options()
        aggregation_options = ModelService.get_aggregation_strategy_options()
        optimizer_options = ModelService.get_optimizer_options()

        response_data = {
            'list': [model.to_dict() for model in models],
            'pagination': pagination,
        }

        return ResponseUtil.success(response_data)

    except Exception as e:
        return ResponseUtil.error(500, f"获取模型列表失败: {str(e)}")


@model_bp.route('/models/<int:model_id>', methods=['GET'])
@token_required
def get_model_detail(current_user, model_id):
    """获取模型详细信息"""
    model = ModelService.get_model_by_id(model_id)

    if not model:
        return ResponseUtil.error(404, "模型不存在")

    return ResponseUtil.success({'model': model.to_dict()})


@model_bp.route('/models/<int:model_id>', methods=['PUT'])
@token_required
@roles_required('admin')
def update_model(current_user, model_id):
    """更新模型参数"""
    data = request.get_json()

    if not data:
        return ResponseUtil.error(400, "请求参数错误")

    model, error = ModelService.update_model(model_id, data)

    if error:
        return ResponseUtil.error(404 if "不存在" in error else 400, error)

    return ResponseUtil.success({
        'model': model.to_dict(),
        'message': '模型更新成功'
    })


@model_bp.route('/models/<int:model_id>', methods=['DELETE'])
@token_required
@roles_required('admin')
def delete_model(current_user, model_id):
    """软删除模型"""
    success, error = ModelService.delete_model(model_id)

    if not success:
        return ResponseUtil.error(404 if "不存在" in error else 500, error)

    return ResponseUtil.success(message="模型删除成功")


@model_bp.route('/models/options', methods=['GET'])
@token_required
def get_model_options(current_user):
    """获取模型相关选项"""
    try:
        options = {
            'model_status': ModelService.get_model_status_options(),
            'aggregation_strategy': ModelService.get_aggregation_strategy_options(),
            'optimizer': ModelService.get_optimizer_options()
        }

        return ResponseUtil.success(options)
    except Exception as e:
        return ResponseUtil.error(500, f"获取选项失败: {str(e)}")