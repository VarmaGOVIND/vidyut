from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.settings import ShopSettings
from app.models.shop import Shop
from app.forms.settings_forms import ShopSettingsForm, ProfileForm, PasswordForm
from app.decorators import admin_required

bp = Blueprint('settings', __name__)

@bp.route('/shop', methods=['GET', 'POST'])
@login_required
@admin_required
def shop_settings():
    settings = ShopSettings.query.first()
    shop = Shop.query.get(current_user.shop_id) if current_user.shop_id else None
    
    if not settings:
        settings = ShopSettings(
            shop_name="My Shop", 
            address="", 
            phone="", 
            gstin="", 
            tax_rate=0.0
        )

    form = ShopSettingsForm(obj=settings)
    
    if form.validate_on_submit():
        if not ShopSettings.query.first():
            db.session.add(settings)
            
        settings.shop_name = form.shop_name.data or "My Shop"
        settings.address = form.address.data or ""
        settings.phone = form.phone.data or ""
        settings.gstin = form.gstin.data or ""
        settings.tax_rate = float(form.tax_rate.data or 0.0)
        
        if shop:
            shop.contact_phone = form.phone.data or shop.phone
            shop.contact_email = current_user.email
        
        db.session.commit()
        flash('Shop settings updated successfully!', 'success')
        return redirect(url_for('settings.shop_settings'))
    
    return render_template('settings/shop.html', form=form, shop=shop)

@bp.route('/shop/maintenance', methods=['POST'])
@login_required
@admin_required
def toggle_maintenance():
    if current_user.shop_id is None:
        flash('No shop found.', 'danger')
        return redirect(url_for('settings.shop_settings'))
    
    shop = Shop.query.get(current_user.shop_id)
    if not shop:
        flash('Shop not found.', 'danger')
        return redirect(url_for('settings.shop_settings'))
    
    shop.is_maintenance = not shop.is_maintenance
    db.session.commit()
    
    status = "enabled" if shop.is_maintenance else "disabled"
    flash(f'Maintenance mode {status} for your shop.', 'success')
    return redirect(url_for('settings.shop_settings'))

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    profile_form = ProfileForm(obj=current_user)
    password_form = PasswordForm()

    if profile_form.validate_on_submit():
        current_user.username = profile_form.username.data
        current_user.email = profile_form.email.data
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('settings.profile'))

    return render_template('settings/profile.html', profile_form=profile_form, password_form=password_form)

@bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    form = PasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password changed successfully!', 'success')
        else:
            flash('Current password is incorrect.', 'danger')
    return redirect(url_for('settings.profile'))