from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, NumberRange, EqualTo, ValidationError
from app.models.user import User
from flask_login import current_user

class ShopSettingsForm(FlaskForm):
    shop_name = StringField('Shop Name', validators=[DataRequired(), Length(max=100)])
    address = TextAreaField('Address', validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=20)])
    gstin = StringField('GSTIN', validators=[Length(max=20)])
    tax_rate = FloatField('Tax Rate (%)', validators=[NumberRange(min=0, max=100)])
    submit = SubmitField('Save Settings')

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Length(min=5, max=120)])
    submit = SubmitField('Update Profile')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username already taken.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email already registered.')

class PasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')