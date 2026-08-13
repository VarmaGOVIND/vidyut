from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
from flask_mail import Mail
from datetime import timedelta

mail = Mail()
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    
    from app.models.user import User
    from app.models.product import Product
    from app.models.sale import Sale, SaleItem
    from app.models.audit import AuditLog
    from app.models.settings import ShopSettings
    from app.models.purchase import Purchase, PurchaseItem
    from app.models.supplier import Supplier
    from app.models.batch import InventoryBatch
    from app.models.expense import Expense
    from app.routes import expenses
    from app.models.return_sale import SaleReturn, SaleReturnItem
    from app.routes import returns
    from app.models.supplier_payment import SupplierPayment
    from app.routes import ledger
    from app.routes.purchase_returns import bp as purchase_returns_bp
    from app.models.shop import Shop
    from app.routes.super_admin import bp as super_admin_bp
    from app.routes.export import bp as export_bp
    from app.routes.import_products import bp as import_products_bp
    from app.routes.gst_reports import bp as gst_reports_bp
    
    
    
    from app.routes.customers import bp as customers_bp
    from app.routes.shop import bp as shop_bp
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    from app.routes import main, auth, products, billing, staff, settings, purchase, reports, suppliers
    
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp, url_prefix='/auth')
    app.register_blueprint(products.bp, url_prefix='/products')
    app.register_blueprint(billing.bp, url_prefix='/billing')
    app.register_blueprint(staff.bp, url_prefix='/staff')
    app.register_blueprint(settings.bp, url_prefix='/settings')
    app.register_blueprint(purchase.bp, url_prefix='/purchase')
    app.register_blueprint(reports.bp, url_prefix='/reports')
    app.register_blueprint(suppliers.bp, url_prefix='/suppliers')
    app.register_blueprint(expenses.bp)
    app.register_blueprint(returns.bp)
    app.register_blueprint(ledger.bp)
    app.register_blueprint(purchase_returns_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(super_admin_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(import_products_bp)
    app.register_blueprint(gst_reports_bp)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365)
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=365)
    
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback() 
        return render_template('errors/500.html'), 500
    
    return app