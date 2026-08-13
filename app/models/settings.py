from app import db

class ShopSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    gstin = db.Column(db.String(20))
    tax_rate = db.Column(db.Float, default=0.0)