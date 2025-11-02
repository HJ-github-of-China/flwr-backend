from flask import Blueprint, request, jsonify, send_file, send_from_directory
from app.services.diagnosis_service import DiagnosisService
import io
import os

from app.utils import ResponseUtil

diagnosis_bp = Blueprint('diagnosis', __name__)


@diagnosis_bp.route('/api/diagnosis/submit', methods=['POST'])
def submit_diagnosis():
    """
    提交诊断请求
    """
    try:
        # 检查文件上传
        if 'image' not in request.files:
            return ResponseUtil.error('没有上传影像文件', code=400)

        image_file = request.files['image']
        clinical_info = request.form.get('clinical_info', '').strip()
        model_name = request.form.get('model_name', '').strip()  # 新增的模型名称参数

        if image_file.filename == '':
            return ResponseUtil.error('没有选择文件', code=400)

        if not clinical_info:
            return ResponseUtil.error('临床信息不能为空', code=400)

        # 收集患者信息
        patient_info = {
            'name': request.form.get('patient_name', '').strip(),
            'gender': request.form.get('patient_gender', '').strip(),
            'age': request.form.get('patient_age', '').strip(),
            'medical_record_id': request.form.get('medical_record_id', '').strip()
        }

        # 调用诊断服务
        result = DiagnosisService.process_diagnosis(
            image_file=image_file,
            clinical_info=clinical_info,
            patient_info=patient_info,
            model_name=model_name  # 传递模型名称参数
        )

        return ResponseUtil.success(
            message='诊断完成',
            data=result
        )

    except Exception as e:
        return ResponseUtil.error(message=f'诊断处理失败: {str(e)}', code=500)


@diagnosis_bp.route('/api/diagnosis/download/<diagnosis_id>', methods=['GET'])
def download_report(diagnosis_id):
    """
    下载诊断报告PDF
    """
    try:
        pdf_buffer = DiagnosisService.get_diagnosis_pdf(diagnosis_id)

        if not pdf_buffer:
            return ResponseUtil.error('诊断报告不存在', code=404)

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'diagnosis_report_{diagnosis_id}.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        return ResponseUtil.error(f'下载报告失败: {str(e)}', code=500)


@diagnosis_bp.route('/api/diagnosis/history', methods=['GET'])
def get_diagnosis_history():
    """
    获取诊断历史记录
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        patient_name = request.args.get('patient_name', '').strip()

        result = DiagnosisService.get_diagnosis_history(
            page=page,
            per_page=per_page,
            patient_name=patient_name
        )

        return ResponseUtil.success(
            message='查询成功',
            data=result
        )

    except Exception as e:
        return ResponseUtil.error(f'查询历史记录失败: {str(e)}', code=500)


@diagnosis_bp.route('/api/diagnosis/detail/<diagnosis_id>', methods=['GET'])
def get_diagnosis_detail(diagnosis_id):
    """
    获取诊断详情
    """
    try:
        detail = DiagnosisService.get_diagnosis_detail(diagnosis_id)

        if not detail:
            return ResponseUtil.error('诊断记录不存在', code=404)

        return ResponseUtil.success(
            message='查询成功',
            data=detail
        )

    except Exception as e:
        return ResponseUtil.error(f'查询诊断详情失败: {str(e)}', code=500)


# @diagnosis_bp.route('/docs/<path:filename>')
# def serve_local_pdf(filename):
#     """
#     提供本地PDF文件访问
#     """
#     try:
#         docs_dir = os.path.join(current_app.root_path, '..', 'docs')
#         return send_from_directory(docs_dir, filename, as_attachment=True)
#     except Exception as e:
#         return ResponseUtil.error(f'文件不存在: {str(e)}', code=404)