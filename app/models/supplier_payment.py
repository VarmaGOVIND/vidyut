from app import db
from datetime import datetime

class SupplierPayment(db.Model):
    __tablename__ = 'supplier_payment'
    
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    method = db.Column(db.String(50))
    note = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20), default='Payment')
    
    supplier = db.relationship('Supplier', backref='payments')
    shop = db.relationship('Shop', backref='supplier_payments')