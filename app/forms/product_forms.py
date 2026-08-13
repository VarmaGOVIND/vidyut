from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, NumberRange, Length, Optional

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(max=100)])
    sku = StringField('SKU', validators=[DataRequired(), Length(max=50)])
    category = SelectField('Category', choices=[
        ('Electronics', 'Electronics (01)'),
        ('Food', 'Food & Beverages (02)'),
        ('Grocery', 'Grocery & Staples (03)'),
        ('Furniture', 'Furniture (04)'),
        ('Clothing', 'Clothing & Apparel (05)'),
        ('Home & Kitchen', 'Home & Kitchen (06)'),
        ('Sports', 'Sports & Fitness (07)'),
        ('Books', 'Books & Stationery (08)'),
        ('Health', 'Health & Beauty (09)'),
        ('Others', 'Others (99)')
    ], validators=[DataRequired()])
    category_code = StringField('Category Code', validators=[Length(max=10)])
    cost_price = FloatField('Cost Price', validators=[DataRequired(), NumberRange(min=0)])
    selling_price = FloatField('Selling Price', validators=[DataRequired(), NumberRange(min=0)])
    stock = IntegerField('Stock', validators=[DataRequired(), NumberRange(min=0)])
    min_stock = IntegerField('Min Stock', validators=[DataRequired(), NumberRange(min=0)])
    expiry_date = DateField('Expiry Date', validators=[Optional()], format='%Y-%m-%d')  
    submit = SubmitField('Save Product')