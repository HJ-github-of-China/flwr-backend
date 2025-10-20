from app.models import db, Model
from datetime import datetime


class ModelService:
    """模型服务类"""

    @staticmethod
    def create_model(model_data):
        """创建新模型"""
        try:
            # 检查模型名称和版本是否重复
            existing_model = Model.query.filter_by(
                model_name=model_data['model_name'],
                model_version=model_data.get('model_version', '1.0.0'),
                is_deleted=False
            ).first()

            if existing_model:
                return None, "模型名称和版本已存在"

            # 创建新模型
            model = Model(
                model_name=model_data['model_name'],
                model_version=model_data.get('model_version', '1.0.0'),
                learning_rate=model_data.get('learning_rate'),
                epochs=model_data.get('epochs'),
                aggregation_strategy=model_data.get('aggregation_strategy'),
                batch_size=model_data.get('batch_size'),
                optimizer=model_data.get('optimizer'),
                algorithm=model_data['algorithm'],
                model_status=model_data.get('model_status', 'training'),
                model_path=model_data.get('model_path'),
                description=model_data.get('description'),
                created_time=datetime.now()
            )

            db.session.add(model)
            db.session.commit()

            return model, None

        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def delete_model(model_id):
        """软删除模型"""
        try:
            model = Model.query.filter_by(model_id=model_id, is_deleted=False).first()
            if not model:
                return False, "模型不存在"

            model.is_deleted = True
            model.updated_time = datetime.now()
            db.session.commit()

            return True, None

        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def update_model(model_id, update_data):
        """更新模型"""
        try:
            model = Model.query.filter_by(model_id=model_id, is_deleted=False).first()
            if not model:
                return None, "模型不存在"

            # 检查名称和版本是否重复（排除自身）
            if 'model_name' in update_data or 'model_version' in update_data:
                existing_model = Model.query.filter(
                    Model.model_name == update_data.get('model_name', model.model_name),
                    Model.model_version == update_data.get('model_version', model.model_version),
                    Model.model_id != model_id,
                    Model.is_deleted == False
                ).first()

                if existing_model:
                    return None, "模型名称和版本已存在"

            # 更新字段
            updatable_fields = [
                'model_name', 'model_version', 'learning_rate', 'epochs',
                'aggregation_strategy', 'batch_size', 'optimizer', 'algorithm',
                'model_status', 'model_path', 'description'
            ]

            for field in updatable_fields:
                if field in update_data:
                    setattr(model, field, update_data[field])

            model.updated_time = datetime.now()
            db.session.commit()

            return model, None

        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def get_model_by_id(model_id):
        """根据ID获取模型"""
        return Model.query.filter_by(model_id=model_id, is_deleted=False).first()



    # TODO 修改一下 能不能解耦呀
    @staticmethod
    def get_paginated_models(page=1, page_size=10, filters=None):
        """获取分页模型列表"""
        if filters is None:
            filters = {}

        query = Model.query.filter_by(is_deleted=False)

        # 模型名称模糊搜索
        model_name = filters.get('model_name', '').strip()
        if model_name:
            query = query.filter(Model.model_name.like(f'%{model_name}%'))

        # 模型状态筛选
        model_status = filters.get('model_status', '')
        if model_status:
            query = query.filter(Model.model_status == model_status)

        # 排序处理
        sort_by = filters.get('sort_by', 'created_time')
        sort_order = filters.get('sort_order', 'desc')

        if sort_by == 'model_name':
            order_field = Model.model_name.asc() if sort_order == 'asc' else Model.model_name.desc()
        else:
            order_field = Model.created_time.asc() if sort_order == 'asc' else Model.created_time.desc()

        query = query.order_by(order_field)

        # 分页查询
        total_count = query.count()
        total_pages = (total_count + page_size - 1) // page_size

        models = query.offset((page - 1) * page_size).limit(page_size).all()

        pagination = {
            "currentPage": page,
            "pageSize": page_size,
            "totalCount": total_count,
            "totalPages": total_pages,
            "hasPrev": page > 1,
            "hasNext": page < total_pages
        }

        return models, pagination

    @staticmethod
    def get_model_status_options():
        """获取模型状态选项"""
        return ['training', 'completed', 'failed', 'stopped']

    @staticmethod
    def get_aggregation_strategy_options():
        """获取聚合策略选项"""
        return ['FedAvg', 'FedMA', 'FedProx', 'FedNova', 'SCAFFOLD']

    @staticmethod
    def get_optimizer_options():
        """获取优化器选项"""
        return ['SGD', 'Adam', 'AdamW', 'RMSprop', 'Adagrad']