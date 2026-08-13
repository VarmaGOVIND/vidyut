import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'vidyut-dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://postgres:postgres@localhost:5432/vidyut_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True      
    SESSION_COOKIE_SAMESITE = 'Lax'     
    SESSION_COOKIE_SECURE = False       
    WTF_CSRF_ENABLED = True             
    
    TRAP_HTTP_EXCEPTIONS = True

    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@vidyut.com'
    SUPER_ADMIN_SECRET_KEY = os.environ.get('SUPER_ADMIN_SECRET_KEY') or 'VIDYUT_SUPER_SECRET_2026'