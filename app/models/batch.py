from app import db
from datetime import datetime

class InventoryBatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    purchase_item_id = db.Column(db.Integer, db.ForeignKey('purchase_item.id'), nullable=False)
    purchase_rate = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=True)
    qty_purchased = db.Column(db.Integer, nullable=False)
    qty_remaining = db.Column(db.Integer, nullable=False)
    expiry_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product', backref='batches', lazy=True)
    purchase_item = db.relationship('PurchaseItem', backref='batch', lazy=True)
    return_items = db.relationship('PurchaseReturnItem', backref='batch_return', lazy=True)