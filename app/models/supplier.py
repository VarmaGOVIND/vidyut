from app import db
from datetime import datetime

class Supplier(db.Model):
    __tablename__ = 'supplier'
    
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    gstin = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    purchases = db.relationship('Purchase', backref='supplier', lazy=True)
    batches = db.relationship('InventoryBatch', backref='supplier', lazy=True)
    returns = db.relationship('PurchaseReturn', backref='supplier_return', lazy=True)
    shop = db.relationship('Shop', backref='suppliers')