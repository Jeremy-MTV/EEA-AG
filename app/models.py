from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

db = SQLAlchemy()
migrate = Migrate()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), nullable=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='gestion') # 'admin' or 'gestion'

class Member(db.Model):
    __tablename__ = 'members'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100))
    prenom = db.Column(db.String(100))
    email = db.Column(db.String(120))
    telephone = db.Column(db.String(20))
    renouvellement = db.Column(db.String(10)) # 'Oui' ou 'Non'
    
    # Présence AG
    is_present = db.Column(db.Boolean, default=False)
    is_refused = db.Column(db.Boolean, default=False)
    check_in_time = db.Column(db.String(20)) # Heure format HH:MM:SS
    
    # Infos persos
    adresse = db.Column(db.String(200))
    code_postal = db.Column(db.String(20))
    ville = db.Column(db.String(100))
    date_naissance = db.Column(db.String(20))
    civilite = db.Column(db.String(20))
    nationalite = db.Column(db.String(50))
    metier = db.Column(db.String(100))
    date_bapteme = db.Column(db.String(50))
    lieu_bapteme = db.Column(db.String(100))

    # [Nouveau] Statut : Futur membre, Membre année en cours, Ancien membre
    statut_membre = db.Column(db.String(50), default="Membre année en cours")
    
    # [Nouveau] Jeton pour le QR Code
    qr_code_token = db.Column(db.String(100), unique=True)
    
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(64))
    action = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class PendingModification(db.Model):
    __tablename__ = 'pending_modifications'
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'))
    data_json = db.Column(db.Text) # JSON des modifications demandées
    statut = db.Column(db.String(20), default='En attente') # 'En attente', 'Approuvé', 'Rejeté'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    member = db.relationship('Member', backref='pending_modifications')

class Proxy(db.Model):
    __tablename__ = 'proxies'
    id = db.Column(db.Integer, primary_key=True)
    mandant_id = db.Column(db.Integer, db.ForeignKey('members.id'))
    mandataire_id = db.Column(db.Integer, db.ForeignKey('members.id'))
    type_ag = db.Column(db.String(50)) # 'AGO', 'AGE', 'DEUX'
    statut = db.Column(db.String(20), default='En attente') # 'En attente', 'Validée'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    mandant = db.relationship('Member', foreign_keys=[mandant_id], backref='procurations_donnees')
    mandataire = db.relationship('Member', foreign_keys=[mandataire_id], backref='procurations_recues')
