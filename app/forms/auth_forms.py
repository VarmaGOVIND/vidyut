from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError
from app.models.user import User
from app.models.shop import Shop

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(min=5, max=120)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Length(min=5, max=120)])
    shop_name = StringField('Shop Name', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Phone Number', validators=[Length(max=20)])
    address = StringField('Shop Address', validators=[Length(max=200)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Account')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email.')

    def validate_phone(self, phone):
        if phone.data:
            
            from app.models.shop import Shop
            shop = Shop.query.filter_by(phone=phone.data).first()
            if shop:
                raise ValidationError('Phone number already used by another shop. Please use a different phone number.')

    def validate_shop_name(self, shop_name):
        
        shop = Shop.query.filter_by(shop_name=shop_name.data).first()
        if shop:
            raise ValidationError('Shop name already exists. Please choose a different shop name.')