from app.models import db, FederatedData, DataType, DataStatus
from sqlalchemy import or_, and_
from datetime import datetime

"""像service层和mapper层融合在一起"""

class FederatedDataService:
    """数据管理"""

    @staticmethod
    def create_data(case_description, image_url, file_size, data_type= "chest_xray"):
        """创建新数据"""
        try:

            data = FederatedData(
                case_description=case_description,
                image_url=image_url,
                file_size=file_size,
                data_type=data_type,
                upload_time=datetime.now()
            )

            db.session.add(data)
            db.session.commit()
            return data, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def delete_data(data_id):
        """软删除数据"""
        try:
            data = FederatedData.query.filter_by(data_id=data_id, is_deleted=False).first()
            if not data:
                return False, "数据不存在"

            data.is_deleted = True
            data.updated_time = datetime.now()
            db.session.commit()

            return True, None
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def update_data(data_id, case_description=None, image_url=None, data_type=None):
        """更新数据"""
        try:
            data = FederatedData.query.filter_by(data_id=data_id, is_deleted=False).first()
            if not data:
                return None, "数据不存在"

            if case_description is not None:
                data.case_description = case_description
            if image_url is not None:
                data.image_url = image_url
            if data_type is not None:
                data.data_type = data_type

            data.updated_time = datetime.now()
            db.session.commit()
            return data, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def get_data_by_id(data_id):
        """根据ID获取数据"""
        return FederatedData.query.filter_by(data_id=data_id, is_deleted=False).first()

    @staticmethod
    def get_paginated_data(page=1, page_size=10):
        """获取分页数据"""
        query = FederatedData.query.filter_by(is_deleted=False)

        # 计算分页
        total_count = query.count()
        total_pages = (total_count + page_size - 1) // page_size

        data_list = query.order_by(FederatedData.upload_time.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()

        pagination = {
            "currentPage": page,
            "pageSize": page_size,
            "totalCount": total_count,
            "totalPages": total_pages
        }

        return data_list, pagination

    @staticmethod
    def search_by_keyword(keyword, page=1, page_size=10):
        """根据关键词搜索"""
        query = FederatedData.query.filter_by(is_deleted=False) \
            .filter(FederatedData.case_description.like(f'%{keyword}%'))

        total_count = query.count()
        total_pages = (total_count + page_size - 1) // page_size

        data_list = query.order_by(FederatedData.upload_time.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()

        pagination = {
            "currentPage": page,
            "pageSize": page_size,
            "totalCount": total_count,
            "totalPages": total_pages
        }

        return data_list, pagination

    @staticmethod
    def get_data_by_time_range(start_time, end_time, page=1, page_size=10):
        """根据时间范围查询"""
        start_date = datetime.strptime(start_time, '%Y-%m-%d')
        end_date = datetime.strptime(end_time, '%Y-%m-%d')

        query = FederatedData.query.filter_by(is_deleted=False) \
            .filter(FederatedData.upload_time.between(start_date, end_date))

        total_count = query.count()
        total_pages = (total_count + page_size - 1) // page_size

        data_list = query.order_by(FederatedData.upload_time.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()

        pagination = {
            "currentPage": page,
            "pageSize": page_size,
            "totalCount": total_count,
            "totalPages": total_pages
        }

        return data_list, pagination