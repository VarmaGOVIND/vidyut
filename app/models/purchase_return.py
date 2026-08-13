from app import db
from datetime import datetime

class PurchaseReturn(db.Model):
    __tablename__ = 'purchase_return'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class PurchaseReturnItem(db.Model):
    __tablename__ = 'purchase_return_item'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    return_id = db.Column(db.Integer, db.ForeignKey('purchase_return.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('inventory_batch.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    return_rate = db.Column(db.Float, nullable=False)