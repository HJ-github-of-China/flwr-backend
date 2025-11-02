import jwt
from flask import request, current_app, g
from functools import wraps
from app.models import User

def token_required(f):
    """JWT token验证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从header获取token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return {
                    "code": 401,
                    "message": "Invalid token format",
                    "data": None
                }, 401
        
        if not token:
            return {
                "code": 401,
                "message": "Token is missing",
                "data": None
            }, 401
        
        try:
            # 解码token
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            
            if not current_user or not current_user.is_active:
                return {
                    "code": 401,
                    "message": "User not found or inactive",
                    "data": None
                }, 401
                
        except jwt.ExpiredSignatureError:
            return {
                "code": 401,
                "message": "Token has expired",
                "data": None
            }, 401
        except jwt.InvalidTokenError:
            return {
                "code": 401,
                "message": "Invalid token",
                "data": None
            }, 401
        except Exception as e:
            return {
                "code": 401,
                "message": "Token verification failed",
                "data": None
            }, 401
        
        # 将当前用户存储在全局对象中
        g.current_user = current_user
        return f(current_user, *args, **kwargs)
    
    return decorated

def roles_required(*roles):
    """角色权限验证装饰器"""
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(current_user, *args, **kwargs):
            if current_user.role not in roles:
                return {
                    "code": 403,
                    "message": "Insufficient permissions",
                    "data": None
                }, 403
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator

def get_client_ip():
    """获取客户端IP"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr