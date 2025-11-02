from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import enum

"""
对应 Spring Boot 中的 @Entity 实体类和 @Repository 数据访问接口
进行表格和字典的映射配置
"""
db = SQLAlchemy()


class DataType(enum.Enum):
    CHEST_XRAY = 'chest_xray'
    IMAGE = 'image'
    TEXT = 'text'
    STRUCTURED = 'structured'
    CHEST_CT = 'chest_ct'
    MRI = 'mri'
    OTHER = 'other'

    @classmethod
    def _missing_(cls, value):
        """处理未知枚举值"""
        # 可以添加日志记录
        return cls.CHEST_XRAY  # 默认返回chest_xray


class DataStatus(enum.Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'


class DiagnosisRecord(db.Model):
    """诊断记录模型"""
    __tablename__ = 'diagnosis_record'
    
    diagnosis_id = db.Column(db.String(50), primary_key=True, comment='诊断ID')
    patient_name = db.Column(db.String(100), comment='患者姓名')
    patient_gender = db.Column(db.String(10), comment='患者性别')
    patient_age = db.Column(db.String(10), comment='患者年龄')
    medical_record_id = db.Column(db.String(100), comment='病历号')
    clinical_info = db.Column(db.Text, comment='临床信息')
    diagnosis_report = db.Column(db.Text, comment='诊断报告')
    pdf_url = db.Column(db.String(500), comment='PDF报告URL')
    model_name = db.Column(db.String(100), comment='使用的模型名称')
    status = db.Column(db.String(20), default='completed', comment='诊断状态')
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    def to_dict(self):
        """转换为字典"""
        return {
            'diagnosis_id': self.diagnosis_id,
            'patient_name': self.patient_name,
            'patient_gender': self.patient_gender,
            'patient_age': self.patient_age,
            'medical_record_id': self.medical_record_id,
            'clinical_info': self.clinical_info,
            'diagnosis_report': self.diagnosis_report,
            'pdf_url': self.pdf_url,
            'model_name': self.model_name,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class FederatedData(db.Model):
    """联邦学习数据模型"""
    __tablename__ = 'federated_data'

    data_id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='数据ID')
    image_url = db.Column(db.String(500), nullable=False, comment='原始图片URL')
    case_description = db.Column(db.Text, nullable=False, comment='病情描述')
    data_type = db.Column(db.String(20), default='chest_xray', comment='图片类型')
    upload_time = db.Column(db.DateTime, default=datetime.now, nullable=False, comment='上传时间')
    data_status = db.Column(db.String(20), default='pending', comment='数据状态')
    is_deleted = db.Column(db.Boolean, default=False, comment='软删除标记')
    updated_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    def to_dict(self):
        """转换为字典"""
        return {
            'dataId': self.data_id,
            'imageUrl': self.image_url,
            'caseDescription': self.case_description,
            'dataType': self.data_type,
            'uploadTime': self.upload_time.strftime('%Y-%m-%d %H:%M:%S') if self.upload_time else None,
            'dataStatus': self.data_status,
            'updatedTime': self.updated_time.strftime('%Y-%m-%d %H:%M:%S') if self.updated_time else None
        }

    def to_simple_dict(self):
        """简化的字典（用于列表）"""
        return {
            'dataId': self.data_id,
            'caseDescription': self.case_description,
            'uploadTime': self.upload_time.strftime('%Y-%m-%d %H:%M:%S') if self.upload_time else None,
            'dataStatus': self.data_status,
            'imageUrl': self.image_url
        }


class Model(db.Model):
    """模型仓库模型"""
    __tablename__ = 'model'

    model_id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='模型ID')
    model_name = db.Column(db.String(100), nullable=False, comment='模型名称')
    model_version = db.Column(db.String(50), default='1.0.0', comment='模型版本')
    learning_rate = db.Column(db.Float, comment='学习率')
    epochs = db.Column(db.Integer, comment='训练轮次')
    aggregation_strategy = db.Column(db.String(50), comment='聚合策略')
    batch_size = db.Column(db.Integer, comment='批次大小')
    optimizer = db.Column(db.String(50), comment='优化器')
    algorithm = db.Column(db.String(100), comment='算法/程序')
    model_status = db.Column(db.String(20), default='training', comment='模型状态')
    model_path = db.Column(db.String(500), comment='模型文件存储路径')
    description = db.Column(db.Text, comment='模型描述')
    created_time = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    is_deleted = db.Column(db.Boolean, default=False, comment='软删除标记')

    def to_dict(self):
        """转换为字典格式"""
        return {
            'model_id': self.model_id,
            'model_name': self.model_name,
            'model_version': self.model_version,
            'learning_rate': float(self.learning_rate) if self.learning_rate is not None else None,
            'epochs': self.epochs,
            'aggregation_strategy': self.aggregation_strategy,
            'batch_size': self.batch_size,
            'optimizer': self.optimizer,
            'algorithm': self.algorithm,
            'model_status': self.model_status,
            'description': self.description,
        }

    def __repr__(self):
        return f'<Model {self.model_name} v{self.model_version}>'