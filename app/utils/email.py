import os
import requests
from flask import url_for, current_app

def send_reset_email(user):
    token = user.reset_token
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    subject = 'VIDYUT - Reset Your Password'
    html_body = f'''
    <html>
    <body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 30px;">
        <div style="max-width: 500px; margin: auto; background: #ffffff; border-radius: 12px; padding: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h2 style="color: #1e293b;">🔐 Reset Your Password</h2>
            <p style="color: #475569;">Hi {user.username},</p>
            <p style="color: #475569;">You requested to reset your password. Click the button below to set a new password.</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" style="background: #2563eb; color: #ffffff; padding: 12px 30px; border-radius: 8px; text-decoration: none; font-weight: 600;">Reset Password</a>
            </div>
            <p style="color: #94a3b8; font-size: 12px;">This link will expire in 1 hour. If you did not request this, please ignore this email.</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0;">
            <p style="color: #94a3b8; font-size: 12px; text-align: center;">&copy; 2026 VIDYUT — Smart Billing System</p>
        </div>
    </body>
    </html>
    '''

    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "api-key": os.environ.get("BREVO_API_KEY"),
            "Content-Type": "application/json"
        },
        json={
            "sender": {"name": "VIDYUT", "email": "vidyut.offical@gmail.com"},
            "to": [{"email": user.email}],
            "subject": subject,
            "htmlContent": html_body
        },
        timeout=20
    )
    current_app.logger.info(f"Brevo API response: {response.status_code} {response.text}")
    response.raise_for_status()