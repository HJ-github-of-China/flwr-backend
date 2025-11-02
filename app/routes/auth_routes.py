from flask import Blueprint, request, jsonify, g
from app.models import db
from app.models import User, LoginLog
from app.utils.auth import get_client_ip, token_required, roles_required
from app.utils import ResponseUtil
from datetime import datetime, timezone

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.json
        
        # 参数验证
        if not data or 'username' not in data or 'password' not in data:
            return ResponseUtil.error(400, 'Username and password are required')
        
        username = data['username'].strip()
        password = data['password']
        
        # 查找用户
        user = User.query.filter_by(username=username).first()
        
        # 记录登录尝试
        login_log = LoginLog(
            user_id=user.user_id if user else None,
            login_ip=get_client_ip(),
            user_agent=request.headers.get('User-Agent'),
            status='failed',
            failure_reason='User not found' if not user else None
        )
        
        if not user:
            db.session.add(login_log)
            db.session.commit()
            return ResponseUtil.error(401, 'Invalid username or password')
        
        if not user.is_active:
            login_log.failure_reason = 'User inactive'
            db.session.add(login_log)
            db.session.commit()
            return ResponseUtil.error(401, 'Account is disabled')
        
        # 验证密码
        try:
            if not user.check_password(password):
                login_log.failure_reason = 'Invalid password'
                db.session.add(login_log)
                db.session.commit()
                return ResponseUtil.error(401, 'Invalid username or password')
        except Exception as e:
            login_log.failure_reason = 'Password validation error'
            db.session.add(login_log)
            db.session.commit()
            return ResponseUtil.error(500, 'Login failed due to password validation error')
        
        # 登录成功
        try:
            user.last_login = datetime.utcnow()
        except:
            # 处理时间设置可能的异常
            user.last_login = datetime.now(timezone.utc)
        
        login_log.status = 'success'
        login_log.failure_reason = None
        db.session.add(login_log)
        db.session.commit()
        
        # 生成token
        token = user.generate_token()
        
        return ResponseUtil.success({
            'message': 'Login successful',
            'token': token,
            'user': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return ResponseUtil.error(500, f'Login failed: {str(e)}')

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册（仅管理员可创建用户）"""
    try:
        data = request.json
        
        # 必填字段验证
        required_fields = ['username', 'password', 'email', 'full_name']
        for field in required_fields:
            if not data.get(field):
                return ResponseUtil.error(400, f'Field {field} is required')
        
        # 检查用户名和邮箱是否已存在
        if User.query.filter_by(username=data['username']).first():
            return ResponseUtil.error(400, 'Username already exists')
        
        if User.query.filter_by(email=data['email']).first():
            return ResponseUtil.error(400, 'Email already exists')
        
        # 创建新用户
        new_user = User(
            username=data['username'],
            email=data['email'],
            full_name=data['full_name'],
            role=data.get('role', 'doctor'),
            department=data.get('department'),
            phone=data.get('phone')
        )
        
        new_user.set_password(data['password'])
        
        db.session.add(new_user)
        db.session.commit()
        
        return ResponseUtil.success({
            'message': 'User registered successfully',
            'user': new_user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return ResponseUtil.error(500, f'Registration failed: {str(e)}')

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """获取当前用户信息"""
    return ResponseUtil.success({'user': current_user.to_dict()})

@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """更新用户信息"""
    try:
        data = request.json
        
        updatable_fields = ['full_name', 'email', 'department', 'phone', 'avatar_url']
        
        for field in updatable_fields:
            if field in data:
                setattr(current_user, field, data[field])
        
        # 如果修改密码
        if 'password' in data and data['password']:
            current_user.set_password(data['password'])
        
        db.session.commit()
        
        return ResponseUtil.success({
            'message': 'Profile updated successfully',
            'user': current_user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return ResponseUtil.error(500, f'Profile update failed: {str(e)}')

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    """用户登出"""
    # JWT是无状态的，客户端删除token即可
    # 这里可以记录登出日志或加入黑名单（如果需要）
    return ResponseUtil.success({'message': 'Logout successful'})

@auth_bp.route('/users', methods=['GET'])
@token_required
@roles_required('admin')
def get_users(current_user):
    """获取用户列表（仅管理员）"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        role = request.args.get('role', '')
        search = request.args.get('search', '')
        
        query = User.query
        
        if role:
            query = query.filter(User.role == role)
        
        if search:
            query = query.filter(
                db.or_(
                    User.username.like(f'%{search}%'),
                    User.full_name.like(f'%{search}%'),
                    User.email.like(f'%{search}%')
                )
            )
        
        pagination = query.order_by(User.created_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        users_data = {
            'items': [user.to_dict() for user in pagination.items],
            'pagination': {
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        }
        
        return ResponseUtil.success(users_data)
        
    except Exception as e:
        return ResponseUtil.error(500, f'Failed to fetch users: {str(e)}')