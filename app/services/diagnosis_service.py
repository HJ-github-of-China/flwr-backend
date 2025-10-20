import os
import uuid
import base64
import io
from datetime import datetime
from flask import current_app
import requests
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from app.services.oss_service import OSSService
from app.utils import FileUtil


class DiagnosisService:
    # todo 带完善
    # 内存中存储诊断记录（生产环境应使用数据库）
    _diagnosis_records = {}

    @classmethod
    def process_diagnosis(cls, image_file, clinical_info, patient_info):
        """
        处理诊断请求
        """
        try:
            # 生成诊断ID
            diagnosis_id = f"diag_{uuid.uuid4().hex[:12]}"

            # 验证文件类型
            if not FileUtil.allowed_file(image_file.filename, {'png', 'jpg', 'jpeg', 'bmp'}):
                raise ValueError("不支持的文件类型")

            # 调用大模型API生成诊断报告
            diagnosis_report = cls._call_llm_api(image_file, clinical_info)

            # 生成PDF报告
            pdf_buffer = cls._create_pdf_report(clinical_info, diagnosis_report, patient_info)

            # 上传PDF到OSS（可选）
            pdf_url = None
            if current_app.config.get('ENABLE_OSS'):
                try:
                    pdf_url = OSSService().upload_pdf(pdf_buffer, f"diagnosis/{diagnosis_id}.pdf")
                except Exception as e:
                    print(f"上传PDF到OSS失败: {str(e)}")
                    # 如果上传OSS失败，则保存到本地
                    pdf_url = cls._save_pdf_locally(pdf_buffer, diagnosis_id)

            # 如果没有启用OSS，则保存到本地
            if not pdf_url:
                pdf_url = cls._save_pdf_locally(pdf_buffer, diagnosis_id)

            # 保存诊断记录
            diagnosis_record = {
                'diagnosis_id': diagnosis_id,
                'patient_info': patient_info,
                'clinical_info': clinical_info,
                'diagnosis_report': diagnosis_report,
                'pdf_url': pdf_url,
                'timestamp': datetime.now().isoformat(),
                'status': 'completed'
            }
            cls._diagnosis_records[diagnosis_id] = diagnosis_record

            return {
                'diagnosis_id': diagnosis_id,
                'diagnosis_report': diagnosis_report,
                'timestamp': diagnosis_record['timestamp'],
                'pdf_url': pdf_url,
            }

        except Exception as e:
            raise Exception(f"诊断处理失败: {str(e)}")

    @classmethod
    def _call_llm_api(cls, image_file, clinical_info):
        """
        调用大模型API
        """
        try:
            # 编码图片为base64
            image_data = image_file.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')

            # 构建提示词（可根据实际需求调整）
            prompt = f"""
            你是一位专业的放射科医生，请根据以下肺结核影像和临床信息进行分析：

            临床信息：{clinical_info}

            请提供专业的诊断报告，包括以下部分：
            1.请你先判断是否有病人是否患病 
            2. 影像描述
            3. 影像学表现  
            4. 诊断意见
            5. 建议

            要求：
            1. 使用专业、准确的医学语言进行描述
            2. 报告结尾包含"报告医师：放射科主治医师 AI助手"和"审核医师：放射科副主任医师 AI助手"
            4.  全英文描述
            分段
            """

            # 配置大模型API（这里以通义千问为例）
            api_config = current_app.config.get('LLM_API_CONFIG', {})

            payload = {
                "model": api_config.get('model', 'qwen-vl-plus'),
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                "parameters": {
                    "max_tokens": 2000,
                    "temperature": 0.1
                }
            }

            headers = {
                'Authorization': f'Bearer {api_config.get("api_key")}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                api_config.get('api_url'),
                json=payload,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()

            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                choice = result['choices'][0]
                if 'message' in choice and 'content' in choice['message']:
                    return choice['message']['content']
                else:
                    return "模型返回格式异常，无法生成诊断报告。"
            else:
                return "模型返回格式异常，无法生成诊断报告。"

        except requests.exceptions.RequestException as e:
            raise Exception(f"调用大模型API失败: {str(e)}")
        except Exception as e:
            raise Exception(f"处理模型响应时出错: {str(e)}")

    @classmethod
    def _create_pdf_report(cls, clinical_info, diagnosis_report, patient_info):
        """
        生成PDF诊断报告
        """
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)

            # 样式定义
            styles = getSampleStyleSheet()

            # 添加中文字体支持
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib.fonts import addMapping

            # 注册中文字体（优先使用Noto Serif CJK SC作为备选）
            try:
                pdfmetrics.registerFont(TTFont('NotoSerifCJKSC', 'NotoSerifCJK-Regular.ttc'))  # Noto Serif CJK SC
                pdfmetrics.registerFont(TTFont('SimSun', 'SimSun.ttf'))  # 宋体
                pdfmetrics.registerFont(TTFont('MicrosoftYaHei', 'msyh.ttc'))  # 微软雅黑
                addMapping('NotoSerifCJKSC', 0, 0)  # 设置映射
                addMapping('SimSun', 0, 0)
                addMapping('MicrosoftYaHei', 0, 0)
            except:
                # 如果找不到字体文件，使用默认字体并添加警告
                pass

            # 检查样式是否已存在，避免重复定义
            if 'CustomTitle' not in styles:
                styles.add(ParagraphStyle(
                    name='CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=16,
                    textColor=colors.darkblue,
                    spaceAfter=30,
                    fontName='NotoSerifCJKSC' if 'NotoSerifCJKSC' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
                ))

            if 'CustomBodyText' not in styles:
                styles.add(ParagraphStyle(
                    name='CustomBodyText',
                    parent=styles['BodyText'],
                    fontSize=10,
                    spaceAfter=12,
                    fontName='NotoSerifCJKSC' if 'NotoSerifCJKSC' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
                    wordWrap='CJK',  # 确保中日韩文字换行
                    leading=12  # 调整行距以适应中文
                ))

            # 构建内容
            story = []

            # 标题
            title = Paragraph("肺结核影像诊断报告", styles['CustomTitle'])
            story.append(title)
            story.append(Spacer(1, 0.2 * inch))

            # 患者信息表格
            if any(patient_info.values()):
                patient_data = [
                    ['患者姓名', patient_info.get('name', '未提供')],
                    ['性别', patient_info.get('gender', '未提供')],
                    ['年龄', patient_info.get('age', '未提供')],
                    ['病历号', patient_info.get('medical_record_id', '未提供')],
                    ['报告日期', datetime.now().strftime('%Y年%m月%d日')]
                ]

                patient_table = Table(patient_data, colWidths=[1.5 * inch, 3 * inch])
                patient_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0),
                     'NotoSerifCJKSC' if 'NotoSerifCJKSC' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1),
                     'NotoSerifCJKSC' if 'NotoSerifCJKSC' in pdfmetrics.getRegisteredFontNames() else 'Helvetica')
                ]))
                story.append(patient_table)
                story.append(Spacer(1, 0.3 * inch))

            # 临床信息
            clinical_heading = Paragraph("临床信息", styles['Heading2'])
            story.append(clinical_heading)
            clinical_content = Paragraph(clinical_info, styles['CustomBodyText'])
            story.append(clinical_content)
            story.append(Spacer(1, 0.2 * inch))

            # 诊断报告
            diagnosis_heading = Paragraph("诊断报告", styles['Heading2'])
            story.append(diagnosis_heading)

            # 处理诊断报告内容，确保即使为空也能正常生成PDF
            if diagnosis_report:
                # 尝试处理可能的Markdown格式或特殊字符
                formatted_report = diagnosis_report.replace('\n', '<br/>')
                diagnosis_content = Paragraph(formatted_report, styles['CustomBodyText'])
                story.append(diagnosis_content)
            else:
                diagnosis_content = Paragraph("未能生成有效的诊断报告。", styles['CustomBodyText'])
                story.append(diagnosis_content)

            # 构建PDF
            doc.build(story)
            buffer.seek(0)
            return buffer

        except Exception as e:
            # 记录异常信息，但仍尝试生成一个基本的PDF
            print(f"生成PDF报告时出错: {str(e)}")
            try:
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4)
                styles = getSampleStyleSheet()

                if 'CustomTitle' not in styles:
                    styles.add(ParagraphStyle(
                        name='CustomTitle',
                        parent=styles['Heading1'],
                        fontSize=16,
                        textColor=colors.darkblue,
                        spaceAfter=30,
                        fontName='NotoSerifCJKSC' if 'NotoSerifCJKSC' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
                    ))

                story = []
                title = Paragraph("肺结核影像诊断报告", styles['CustomTitle'])
                story.append(title)
                story.append(Spacer(1, 0.2 * inch))

                error_msg = Paragraph(f"生成诊断报告时发生错误: {str(e)}", styles['BodyText'])
                story.append(error_msg)

                doc.build(story)
                buffer.seek(0)
                return buffer
            except Exception as inner_e:
                raise Exception(f"生成PDF报告失败: {str(inner_e)}")

    @classmethod
    def _save_pdf_locally(cls, pdf_buffer, diagnosis_id):
        """
        将PDF保存到本地
        """
        try:
            # 确保docs目录存在
            docs_dir = os.path.join(current_app.root_path, '..', 'docs')
            os.makedirs(docs_dir, exist_ok=True)
            
            # 生成文件路径
            filename = f"diagnosis_report_{diagnosis_id}.pdf"
            file_path = os.path.join(docs_dir, filename)
            
            # 保存PDF文件
            pdf_buffer.seek(0)
            with open(file_path, 'wb') as f:
                f.write(pdf_buffer.read())
            
            # 返回相对路径URL
            return f"/docs/{filename}"
        except Exception as e:
            print(f"保存PDF到本地失败: {str(e)}")
            return None

    @classmethod
    def get_diagnosis_pdf(cls, diagnosis_id):
        """
        获取诊断PDF报告
        """
        try:
            # 从存储中获取诊断记录
            record = cls._diagnosis_records.get(diagnosis_id)
            if not record:
                return None

            # 重新生成PDF（或从OSS下载）
            pdf_buffer = cls._create_pdf_report(
                record['clinical_info'],
                record['diagnosis_report'],
                record['patient_info']
            )

            return pdf_buffer

        except Exception as e:
            raise Exception(f"获取PDF报告失败: {str(e)}")

    @classmethod
    def get_diagnosis_history(cls, page=1, per_page=10, patient_name=None):
        """
        获取诊断历史记录
        """
        try:
            # 过滤记录
            records = list(cls._diagnosis_records.values())

            if patient_name:
                records = [r for r in records if r['patient_info'].get('name') == patient_name]

            # 排序
            records.sort(key=lambda x: x['timestamp'], reverse=True)

            # 分页
            total = len(records)
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_records = records[start_idx:end_idx]

            # 构建返回数据
            diagnosis_list = []
            for record in paginated_records:
                diagnosis_list.append({
                    'diagnosis_id': record['diagnosis_id'],
                    'patient_name': record['patient_info'].get('name', ''),
                    'clinical_info': record['clinical_info'][:100] + '...' if len(record['clinical_info']) > 100 else
                    record['clinical_info'],
                    'timestamp': record['timestamp'],
                    'status': record['status']
                })

            return {
                'diagnosis_list': diagnosis_list,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }

        except Exception as e:
            raise Exception(f"获取诊断历史失败: {str(e)}")

    @classmethod
    def get_diagnosis_detail(cls, diagnosis_id):
        """
        获取诊断详情
        """
        try:
            record = cls._diagnosis_records.get(diagnosis_id)
            if not record:
                return None

            return {
                'diagnosis_id': record['diagnosis_id'],
                'patient_info': record['patient_info'],
                'clinical_info': record['clinical_info'],
                'diagnosis_report': record['diagnosis_report'],
                'timestamp': record['timestamp'],
                'status': record['status'],
                'pdf_url': record['pdf_url'] or f"/api/diagnosis/download/{diagnosis_id}"
            }

        except Exception as e:
            raise Exception(f"获取诊断详情失败: {str(e)}")