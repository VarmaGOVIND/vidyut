from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    shop_name = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    is_super_admin = db.Column(db.Boolean, default=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    
    shop_owned = db.relationship('Shop', back_populates='owner', foreign_keys='Shop.owner_id')
    shop_working = db.relationship('Shop', back_populates='staff', foreign_keys='User.shop_id')
    created_users = db.relationship('User', back_populates='creator', foreign_keys='User.created_by')
    creator = db.relationship('User', back_populates='created_users', remote_side='User.id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_staff(self):
        return not self.is_admin and not self.is_super_admin and self.shop_id is not None
    
    def can_manage_shop(self, shop_id):
        if self.is_super_admin:
            return True
        return self.shop_id == shop_id and (self.is_admin or self.is_super_admin)
    
    def __repr__(self):
        return f'<User {self.username}>'