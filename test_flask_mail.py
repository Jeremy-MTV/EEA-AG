from app import create_app
from flask_mail import Mail, Message

app = create_app()
with app.app_context():
    print("MAIL_SERVER:", app.config['MAIL_SERVER'])
    print("MAIL_PORT:", app.config['MAIL_PORT'])
    print("MAIL_USERNAME:", app.config['MAIL_USERNAME'])
    print("MAIL_PASSWORD:", len(str(app.config['MAIL_PASSWORD'])) if app.config['MAIL_PASSWORD'] else None)
    print("MAIL_USE_TLS:", app.config['MAIL_USE_TLS'])
    print("MAIL_USE_SSL:", app.config.get('MAIL_USE_SSL', False))

    mail = Mail(app)
    try:
        msg = Message("Test Support", sender=app.config['MAIL_USERNAME'], recipients=[app.config['MAIL_USERNAME']])
        msg.body = "This is a test from flask-mail"
        mail.send(msg)
        print("Flask-Mail Send successful!")
    except Exception as e:
        print("Flask-Mail Error:", type(e), e)
