from flask import Flask
from config import Config
from app.models import db, migrate
from flask_mail import Mail

mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    from app.routes.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.routes.portal import bp as portal_bp
    app.register_blueprint(portal_bp) # DMZ à la racine

    from app.routes.scan import bp as scan_bp
    app.register_blueprint(scan_bp) # /manager et /display

    from app.utils import start_weekly_backup_thread
    start_weekly_backup_thread(app)

    return app
