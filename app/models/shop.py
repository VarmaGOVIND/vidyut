from app import db
from datetime import datetime

class Shop(db.Model):
    __tablename__ = 'shop'
    
    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(100), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    gst_number = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    is_maintenance = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    block_reason = db.Column(db.Text, nullable=True)
    blocked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    blocked_at = db.Column(db.DateTime, nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    contact_email = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner = db.relationship('User', back_populates='shop_owned', foreign_keys='Shop.owner_id')
    staff = db.relationship('User', back_populates='shop_working', foreign_keys='User.shop_id')
    blocked_by_user = db.relationship('User', foreign_keys='Shop.blocked_by')
    
    def is_accessible(self, user=None):
        if self.is_blocked:
            return False
        if self.is_maintenance:
            if user and (user.is_super_admin or user.is_admin or user.shop_id == self.id):
                return True
            return False
        return True
    
    def get_block_message(self):
        if self.is_blocked:
            return "🚫 This shop has been blocked. Please contact the system administrator."
        if self.is_maintenance:
            return "🚧 This shop is currently under maintenance. Please try again later."
        return None
    
    def __repr__(self):
        return f'<Shop {self.shop_name}>'