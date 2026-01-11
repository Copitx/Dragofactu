from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import bcrypt
import jwt
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from ...models.entities import User, UserRole
from ...models.database import get_db
import os
from functools import wraps


class AuthService:
    def __init__(self):
        self.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')
        self.jwt_expiration_hours = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
    
    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def generate_token(self, user: User) -> str:
        payload = {
            'user_id': str(user.id),
            'username': user.username,
            'role': user.role.value,
            'exp': datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def authenticate(self, db: Session, username: str, password: str) -> Optional[User]:
        user = db.query(User).filter(
            or_(
                User.username == username,
                User.email == username
            ),
            User.is_active == True
        ).first()
        
        if user and self.verify_password(password, str(user.password_hash)):
            # Update last login
            from sqlalchemy import update
            db.execute(
                update(User).where(User.id == user.id).values(last_login=datetime.utcnow())
            )
            db.commit()
            return user
        
        return None
    
    def get_current_user(self, db: Session, token: str) -> Optional[User]:
        payload = self.verify_token(token)
        if not payload:
            return None
        
        user = db.query(User).filter(
            User.id == payload['user_id'],
            User.is_active == True
        ).first()
        
        return user


class PermissionService:
    # Define permissions based on role
    ROLE_PERMISSIONS = {
        'admin': [
            'users.create', 'users.read', 'users.update', 'users.delete',
            'clients.create', 'clients.read', 'clients.update', 'clients.delete',
            'suppliers.create', 'suppliers.read', 'suppliers.update', 'suppliers.delete',
            'products.create', 'products.read', 'products.update', 'products.delete',
            'documents.create', 'documents.read', 'documents.update', 'documents.delete',
            'documents.convert', 'documents.export',
            'inventory.create', 'inventory.read', 'inventory.update', 'inventory.adjust',
            'payments.create', 'payments.read', 'payments.update',
            'diary.create', 'diary.read', 'diary.update', 'diary.delete',
            'workers.create', 'workers.read', 'workers.update', 'workers.delete',
            'reports.generate', 'system.config', 'audit.read'
        ],
        'management': [
            'clients.create', 'clients.read', 'clients.update', 'clients.delete',
            'suppliers.create', 'suppliers.read', 'suppliers.update', 'suppliers.delete',
            'products.read', 'products.update',
            'documents.create', 'documents.read', 'documents.update', 'documents.delete',
            'documents.convert', 'documents.export',
            'inventory.read',
            'payments.create', 'payments.read', 'payments.update',
            'diary.create', 'diary.read', 'diary.update', 'diary.delete',
            'workers.read', 'workers.update',
            'reports.generate', 'audit.read'
        ],
        'warehouse': [
            'clients.read', 'suppliers.read',
            'products.create', 'products.read', 'products.update',
            'documents.read',
            'inventory.create', 'inventory.read', 'inventory.update', 'inventory.adjust',
            'payments.read',
            'reports.generate.inventory'
        ],
        'read_only': [
            'clients.read', 'suppliers.read',
            'products.read', 'documents.read',
            'inventory.read', 'payments.read',
            'diary.read', 'workers.read',
            'reports.read'
        ]
    }
    
    def has_permission(self, user: User, permission: str) -> bool:
        role_value = user.role.value if hasattr(user.role, 'value') else str(user.role)
        user_permissions = self.ROLE_PERMISSIONS.get(role_value, [])
        return permission in user_permissions
    
    def has_any_permission(self, user: User, permissions: List[str]) -> bool:
        role_value = user.role.value if hasattr(user.role, 'value') else str(user.role)
        user_permissions = self.ROLE_PERMISSIONS.get(role_value, [])
        return any(perm in user_permissions for perm in permissions)
    
    def has_all_permissions(self, user: User, permissions: List[str]) -> bool:
        role_value = user.role.value if hasattr(user.role, 'value') else str(user.role)
        user_permissions = self.ROLE_PERMISSIONS.get(role_value, [])
        return all(perm in user_permissions for perm in permissions)


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.auth_service = AuthService()
        self.permission_service = PermissionService()
    
    def create_user(self, username: str, email: str, password: str, 
                   full_name: str, role: UserRole) -> User:
        # Check if user already exists
        existing_user = self.db.query(User).filter(
            or_(User.username == username, User.email == email)
        ).first()
        
        if existing_user:
            raise ValueError("Username or email already exists")
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=self.auth_service.hash_password(password),
            full_name=full_name,
            role=role
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        from sqlalchemy import update
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Handle password update separately
        if 'password' in kwargs:
            kwargs['password_hash'] = self.auth_service.hash_password(kwargs.pop('password'))
        
        # Update allowed fields
        allowed_fields = ['username', 'email', 'full_name', 'role', 'is_active']
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def delete_user(self, user_id: str) -> bool:
        from sqlalchemy import update
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Soft delete - just deactivate
        self.db.execute(
            update(User).where(User.id == user_id).values(is_active=False)
        )
        self.db.commit()
        
        return True
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()
    
    def get_all_users(self, active_only: bool = True) -> List[User]:
        query = self.db.query(User)
        if active_only:
            query = query.filter(User.is_active == True)
        return query.all()
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        from sqlalchemy import update
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        if not self.auth_service.verify_password(old_password, str(user.password_hash)):
            return False
        
        self.db.execute(
            update(User).where(User.id == user_id).values(
                password_hash=self.auth_service.hash_password(new_password)
            )
        )
        self.db.commit()
        
        return True


def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        def wrapper(self, current_user: User, *args, **kwargs):
            permission_service = PermissionService()
            if not permission_service.has_permission(current_user, permission):
                raise PermissionError(f"User lacks required permission: {permission}")
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(permissions: List[str]):
    def decorator(func):
        @wraps(func)
        def wrapper(self, current_user: User, *args, **kwargs):
            permission_service = PermissionService()
            if not permission_service.has_any_permission(current_user, permissions):
                raise PermissionError(f"User lacks any of required permissions: {permissions}")
            return func(self, *args, **kwargs)
        return wrapper
    return decorator