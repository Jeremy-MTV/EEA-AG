from app.models import db, AuditLog
from flask import session

def log_audit_action(action_text):
    """
    Enregistre une action dans la table d'Audit Log.
    Récupère automatiquement l'utilisateur depuis la session Flask.
    """
    user = session.get('username', 'Système')
    log = AuditLog(user=user, action=action_text)
    db.session.add(log)
    db.session.commit()

import pandas as pd
from flask import current_app

def sync_google_sheet():
    url = current_app.config.get('GSHEET_URL')
    if not url:
        return False, "URL du Google Sheet non configurée."
        
    try:
        # On s'attend à un lien d'export CSV Google Sheet
        df = pd.read_csv(url)
        
        # On importe ici pour éviter les imports circulaires
        from app.models import db, Member
        
        count = 0
        for index, row in df.iterrows():
            m_id = row.get('ID')
            if pd.isna(m_id): continue
            
            existing = db.session.get(Member, int(m_id))
            if existing: # Mise à jour sans écraser les présences
                existing.nom = row.get('Nom', existing.nom)
                existing.prenom = row.get('Prénom', existing.prenom)
                existing.email = row.get('Email', existing.email)
                existing.telephone = row.get('Téléphone', existing.telephone)
                existing.renouvellement = row.get('Renouvellement 25/26', existing.renouvellement)
                existing.adresse = row.get('Adresse', existing.adresse)
                existing.code_postal = row.get('Code postal', existing.code_postal)
                existing.ville = row.get('Ville', existing.ville)
            else: # Insert
                new_m = Member(
                    id=int(m_id),
                    nom=row.get('Nom'),
                    prenom=row.get('Prénom'),
                    email=row.get('Email'),
                    telephone=row.get('Téléphone'),
                    renouvellement=row.get('Renouvellement 25/26', 'Non'),
                    adresse=row.get('Adresse'),
                    code_postal=row.get('Code postal'),
                    ville=row.get('Ville')
                )
                db.session.add(new_m)
            count += 1
            
        db.session.commit()
        return True, f"{count} lignes synchronisées avec succès."
        
    except Exception as e:
        return False, f"Erreur de synchronisation : {str(e)}"

import pyotp
from flask_mail import Message

def generate_otp_for_member(member):
    """Génère un OTP à 6 chiffres via PyOTP basé sur l'ID et le secret app."""
    secret = current_app.config['SECRET_KEY'] + str(member.id)
    # PyOTP attend un secret encodé en Base32
    import base64
    b32_secret = base64.b32encode(secret.encode()[:32].ljust(32, b'0')).decode('utf-8')
    totp = pyotp.TOTP(b32_secret, interval=900) # Valide pendant 15 mins (900s)
    return totp.now(), totp

def send_otp_email(member, otp_code):
    """Envoie l'OTP par email."""
    mail = current_app.extensions.get('mail')
    if not mail:
        return False
        
    msg = Message(
        subject="Votre code de connexion - Portail EEA AG",
        sender=current_app.config.get('MAIL_USERNAME', 'noreply@eea.com'),
        recipients=[member.email]
    )
    msg.body = f"Bonjour {member.prenom},\n\nVotre code d'accès unique (valable 15 minutes) est : {otp_code}\n\nL'équipe EEA."
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Erreur d'envoi d'email OTP : {e}")
        return False

import qrcode
import base64
from io import BytesIO
import uuid

def generate_qr_bytes(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return buffered.getvalue()

def send_convocation_email(member):
    mail = current_app.extensions.get('mail')
    if not mail or not member.email:
        return False
        
    if not member.qr_code_token:
        member.qr_code_token = str(uuid.uuid4())
        db.session.commit()
        
    qr_bytes = generate_qr_bytes(member.qr_code_token)
    
    msg = Message(
        subject="Convocation à l'Assemblée Générale EEA",
        sender=current_app.config.get('MAIL_USERNAME', 'noreply@eea.com'),
        recipients=[member.email]
    )
    
    msg.html = f"""
    <h3>Bonjour {member.prenom},</h3>
    <p>Vous êtes convoqué(e) à l'Assemblée Générale de l'Église En Action.</p>
    <p>Veuillez présenter le QR Code ci-dessous à l'accueil le jour de l'événement pour faciliter votre enregistrement :</p>
    <br>
    <img src="cid:qrcode" alt="Votre QR Code personnel" width="200" height="200">
    <br><br>
    <p>Identifiant Manuel : {member.id}</p>
    <p>Copie du Jeton : <small>{member.qr_code_token}</small></p>
    <p>L'équipe EEA</p>
    """
    
    # Attach the QR code image inline using Content-ID
    msg.attach("qrcode.png", "image/png", qr_bytes, headers={'Content-ID': '<qrcode>'})
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Erreur d'envoi d'email convocation: {e}")
        return False

import os
import datetime

def get_export_data(export_type='ag'):
    """Prépare les données pour l'export CSV/GSheet selon le type (members ou ag)."""
    from app.models import Member
    membres = Member.query.order_by(Member.nom).all()
    
    data = []
    if export_type == 'members':
        headers = ["ID", "Nom", "Prénom", "Email", "Téléphone", "Renouvellement", "Statut", "Adresse", "Code postal", "Ville"]
        for m in membres:
            data.append([
                m.id, m.nom, m.prenom, m.email or '', m.telephone or '',
                m.renouvellement or 'Non', m.statut_membre or 'Membre année en cours',
                m.adresse or '', m.code_postal or '', m.ville or ''
            ])
    else: # 'ag' par défaut
        headers = ["ID", "Nom", "Prénom", "Email", "Téléphone", "Renouvellement", "Statut", "Est Présent", "Refusé", "Heure Arrivée", "Adresse", "Code postal", "Ville"]
        for m in membres:
            data.append([
                m.id, m.nom, m.prenom, m.email or '', m.telephone or '',
                m.renouvellement or 'Non', m.statut_membre or 'Membre année en cours',
                'Oui' if getattr(m, 'is_present', False) else 'Non',
                'Oui' if getattr(m, 'is_refused', False) else 'Non',
                m.check_in_time.strftime('%Y-%m-%d %H:%M:%S') if getattr(m, 'check_in_time', None) and hasattr(m.check_in_time, 'strftime') else (m.check_in_time if getattr(m, 'check_in_time', None) else ''),
                m.adresse or '', m.code_postal or '', m.ville or ''
            ])
    return headers, data

def backup_to_nas(export_type='ag'):
    """Sauvegarde la table en CSV sur le NAS selon le type (members/ag) si configuré."""
    from flask import current_app
    import pandas as pd
    
    config_key = 'NAS_BACKUP_PATH_MEMBERS' if export_type == 'members' else 'NAS_BACKUP_PATH_AG'
    nas_path = current_app.config.get(config_key)
    
    if not nas_path:
        return False, f"NAS {export_type.upper()} non configuré"
        
    try:
        os.makedirs(nas_path, exist_ok=True)
            
        headers, data = get_export_data(export_type)
        df = pd.DataFrame(data, columns=headers)
        
        prefix = 'members_only' if export_type == 'members' else 'ag_analytics'
        
        # Fichier principal toujours à jour
        primary_file = os.path.join(nas_path, f'{prefix}_latest.csv')
        df.to_csv(primary_file, index=False, encoding='utf-8-sig')
        
        # Historique horodaté
        date_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        history_file = os.path.join(nas_path, f'{prefix}_log_{date_str}.csv')
        df.to_csv(history_file, index=False, encoding='utf-8-sig')
        
        return True, "Succès"
    except Exception as e:
        print(f"Erreur sauvegarde NAS ({export_type}) : {e}")
        return False, str(e)

def export_to_gsheet(export_type='ag'):
    """Exporte la table vers le Google Sheet via gspread selon le type."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        return False, "Librairies manquantes (gspread, google-auth)"
        
    from flask import current_app
    import re
    
    config_key = 'GSHEET_URL_MEMBERS' if export_type == 'members' else 'GSHEET_URL_AG'
    gsheet_url = current_app.config.get(config_key)
    
    if not gsheet_url:
        return False, f"GSHEET URL {export_type.upper()} non défini"
        
    credentials_file = os.path.join(current_app.root_path, '..', 'service_account.json')
    if not os.path.exists(credentials_file):
        return False, "Fichier service_account.json introuvable"
        
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        credentials = Credentials.from_service_account_file(credentials_file, scopes=scopes)
        client = gspread.authorize(credentials)
        
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', gsheet_url)
        if not match:
            return False, "URL Google Sheet invalide"
            
        sheet = client.open_by_key(match.group(1)).sheet1
        
        headers, data = get_export_data(export_type)
        sheet.clear()
        sheet.update(range_name='A1', values=[headers] + data)
        return True, "Export GSheet réussi"
        
    except Exception as e:
        print(f"Erreur Export GSheet ({export_type}) : {e}")
        return False, str(e)

def backup_db_to_nas():
    """Sauvegarde le fichier eea_ag_v3.db complet sur le NAS (dossier AG par défaut)."""
    from flask import current_app
    import shutil
    
    nas_path = current_app.config.get('NAS_BACKUP_PATH_AG')
    if not nas_path:
        return False, "NAS AG non configuré pour la DB"
        
    db_path = os.path.join(current_app.root_path, '..', 'eea_ag_v3.db')
    if not os.path.exists(db_path):
        return False, "Fichier DB introuvable"
        
    try:
        os.makedirs(nas_path, exist_ok=True)
        date_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        dest_file = os.path.join(nas_path, f'eea_ag_v3_backup_{date_str}.db')
        
        shutil.copy2(db_path, dest_file)
        return True, "DB Backup Succès"
    except Exception as e:
        print(f"Erreur sauvegarde DB locale sur NAS : {e}")
        return False, str(e)

def trigger_all_backups(app):
    """Lance les backups NAS (CSV + DB) et GSheet (Members & AG) dans un contexte d'application."""
    with app.app_context():
        backup_to_nas('members')
        backup_to_nas('ag')
        backup_db_to_nas()
        export_to_gsheet('members')
        export_to_gsheet('ag')

def start_weekly_backup_thread(app):
    """Démarre un thread daemon qui exécute les backups une fois par semaine (Le dimanche à 03h00 par exemple)."""
    import threading
    import time
    import datetime
    
    def weekly_job():
        with app.app_context():
            while True:
                now = datetime.datetime.now()
                # Run backup on Sunday (weekday() == 6) at 03:00 AM
                if now.weekday() == 6 and now.hour == 3 and now.minute == 0:
                    try:
                        print(f"[{now}] Exécution de la sauvegarde hebdomadaire automatique...")
                        backup_to_nas('members')
                        backup_to_nas('ag')
                        backup_db_to_nas()
                        export_to_gsheet('members')
                        export_to_gsheet('ag')
                        print("Sauvegarde hebdomadaire terminée.")
                        time.sleep(60) # Sleep 60 seconds to avoid multiple runs in the same minute
                    except Exception as e:
                        print(f"Erreur durant la sauvegarde hebdo : {e}")
                
                # Check every 30 seconds
                time.sleep(30)
                
    thread = threading.Thread(target=weekly_job, daemon=True)
    thread.start()
    print("Thread de sauvegarde hebdomadaire démarré (Dimanche 03h00).")

