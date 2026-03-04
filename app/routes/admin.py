from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file, current_app, jsonify
from werkzeug.security import check_password_hash
from app.models import db, User, Member, PendingModification, Proxy, AuditLog
import json, os
from datetime import datetime
from app.utils import log_audit_action, sync_google_sheet, send_convocation_email, trigger_all_backups
import threading

def run_backups():
    app = current_app._get_current_object()
    threading.Thread(target=trigger_all_backups, args=[app]).start()
from flask_mail import Message
from functools import wraps

bp = Blueprint('admin', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash("Accès non autorisé.", "danger")
            return redirect(url_for('portal.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('portal.index'))
        else:
            flash("Identifiants incorrects.", "danger")
            
    return render_template('admin/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin.login'))

@bp.route('/members')
@admin_required
def members_dashboard():
    membres = Member.query.order_by(Member.nom.asc()).all()
    stats = {'total': len(membres)}
    
    archives = []
    import glob
    backup_dir = os.path.join(current_app.root_path, '..', 'backups')
    if os.path.exists(backup_dir):
        # Trie par ordre décroissant (plus récent en premier)
        for f in sorted(glob.glob(os.path.join(backup_dir, 'archive_ag_*.json')), reverse=True):
            try:
                filename = os.path.basename(f)
                dt_str = filename.replace('archive_ag_', '').replace('.json', '')
                try:
                    dt_obj = datetime.strptime(dt_str, '%Y%m%d_%H%M%S')
                    year_label = dt_obj.strftime('%Y')
                except:
                    year_label = filename
                    
                with open(f, 'r') as file:
                    data = json.load(file)
                    archives.append({'year': year_label, 'filename': filename, 'data': data})
            except Exception as e:
                print(f"Erreur d'archivage: {e}")

    return render_template('admin/members.html', membres=membres, stats=stats, archives=archives)

@bp.route('/ag')
@login_required
def ag_dashboard():
    membres = Member.query.order_by(Member.is_present.desc(), Member.is_refused.desc(), Member.nom.asc()).all()
    total = len(membres)
    presents = sum(1 for m in membres if m.is_present)
    percent = round((presents/total*100), 1) if total > 0 else 0
    stats = {'total': total, 'presents': presents, 'percent': percent}
    return render_template('admin/ag.html', membres=membres, stats=stats)

@bp.route('/api/ag_stats')
@login_required
def api_ag_stats():
    membres = Member.query.order_by(Member.is_present.desc(), Member.is_refused.desc(), Member.nom.asc()).all()
    total = len(membres)
    presents = sum(1 for m in membres if m.is_present)
    percent = round((presents/total*100), 1) if total > 0 else 0
    
    members_data = [{
        'id': m.id,
        'nom': m.nom,
        'prenom': m.prenom,
        'email': m.email,
        'is_present': m.is_present,
        'is_refused': m.is_refused,
        'check_in_time': m.check_in_time
    } for m in membres]
    
    return jsonify({
        'total': total,
        'presents': presents,
        'percent': percent,
        'membres': members_data
    })

@bp.route('/add_member', methods=['POST'])
@admin_required
def add_member():
    new_m = Member(
        nom=request.form.get('nom'),
        prenom=request.form.get('prenom'),
        email=request.form.get('email'),
        telephone=request.form.get('telephone'),
        renouvellement=request.form.get('renouvellement'),
        adresse=request.form.get('adresse'),
        code_postal=request.form.get('code_postal'),
        ville=request.form.get('ville'),
        date_naissance=request.form.get('date_naissance'),
        civilite=request.form.get('civilite'),
        nationalite=request.form.get('nationalite'),
        metier=request.form.get('metier'),
        date_bapteme=request.form.get('date_bapteme'),
        lieu_bapteme=request.form.get('lieu_bapteme'),
        statut_membre=request.form.get('statut_membre', 'Membre année en cours')
    )
    db.session.add(new_m)
    db.session.commit()
    run_backups()
    log_audit_action(f"Création du nouveau membre {new_m.prenom} {new_m.nom} (ID: {new_m.id})")
    flash("Membre ajouté avec succès.", "success")
    return redirect(url_for('admin.members_dashboard'))

@bp.route('/edit/<int:member_id>', methods=['GET', 'POST'])
@admin_required
def edit_member(member_id):
    m = Member.query.get_or_404(member_id)
    if request.method == 'POST':
        m.nom = request.form.get('nom')
        m.prenom = request.form.get('prenom')
        m.email = request.form.get('email')
        m.telephone = request.form.get('telephone')
        m.renouvellement = request.form.get('renouvellement')
        m.adresse = request.form.get('adresse')
        m.code_postal = request.form.get('code_postal')
        m.ville = request.form.get('ville')
        m.date_naissance = request.form.get('date_naissance')
        m.civilite = request.form.get('civilite')
        m.nationalite = request.form.get('nationalite')
        m.metier = request.form.get('metier')
        m.date_bapteme = request.form.get('date_bapteme')
        m.lieu_bapteme = request.form.get('lieu_bapteme')
        m.statut_membre = request.form.get('statut_membre')
        
        # AG Status
        statut_ag = request.form.get('statut_ag')
        if statut_ag == 'present':
            m.is_present = True
            m.is_refused = False
        elif statut_ag == 'refused':
            m.is_present = False
            m.is_refused = True
        else:
            m.is_present = False
            m.is_refused = False
            
        db.session.commit()
        run_backups()
        log_audit_action(f"Modification du membre {m.prenom} {m.nom} (ID: {m.id})")
        flash("Membre mis à jour avec succès.", "success")
        return redirect(url_for('admin.members_dashboard'))
        
    return render_template('admin/edit_member.html', m=m)

@bp.route('/sync_gsheet', methods=['POST'])
@admin_required
def sync_gsheet():
    success, message = sync_google_sheet()
    if success:
        log_audit_action("Synchronisation Google Sheet réussie")
        flash(message, "success")
    else:
        log_audit_action(f"Échec synchro Google Sheet : {message}")
        flash(message, "danger")
@bp.route('/modifications')
@admin_required
def view_modifications():
    pending = PendingModification.query.filter_by(statut='En attente').all()
    # On parse le JSON pour l'affichage
    for p in pending:
        p.parsed_data = json.loads(p.data_json)
    return render_template('admin/modifications.html', pending=pending)

@bp.route('/modifications/<int:mod_id>/<action>', methods=['POST'])
@admin_required
def action_modification(mod_id, action):
    mod = PendingModification.query.get_or_404(mod_id)
    if mod.statut != 'En attente':
        flash("Cette modification a déjà été traitée.", "warning")
        return redirect(url_for('admin.view_modifications'))
        
    m = mod.member
    if action == 'approve':
        data = json.loads(mod.data_json)
        for key, value in data.items():
            if hasattr(m, key):
                setattr(m, key, value)
        mod.statut = 'Approuvé'
        log_audit_action(f"Approbation des modifications du profil de {m.prenom} {m.nom} (ID: {m.id})")
        flash("Modifications approuvées et appliquées.", "success")
    elif action == 'reject':
        mod.statut = 'Rejeté'
        log_audit_action(f"Rejet des modifications du profil de {m.prenom} {m.nom} (ID: {m.id})")
        flash("Modifications rejetées.", "info")
        
    db.session.commit()
    if action == 'approve':
        run_backups()
        
    return redirect(url_for('admin.view_modifications'))

@bp.route('/send_convocations', methods=['POST'])
@admin_required
def send_convocations():
    # Only get the members selected from the Modal checklist
    selected_ids = request.form.getlist('selected_members')
    
    if not selected_ids:
        flash("Aucun membre n'a été sélectionné pour l'envoi de convocations.", "warning")
        return redirect(url_for('admin.ag_dashboard'))
        
    membres = Member.query.filter(Member.id.in_(selected_ids)).all()
    count = 0
    if current_app.extensions.get('mail'): 
        for m in membres:
            if m.email:
                if send_convocation_email(m):
                    count += 1
                
    log_audit_action(f"Envoi sélectif de convocations à {count} membres choisis.")
    flash(f"Convocations envoyées avec succès à {count} membres sélectionnés.", "success")
    return redirect(url_for('admin.ag_dashboard'))

@bp.route('/guide')
@admin_required
def guide():
    return render_template('admin/guide.html')

# --- USER MANAGEMENT ---
@bp.route('/users')
@admin_required
def users_dashboard():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@bp.route('/add_user', methods=['POST'])
@admin_required
def add_user():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role', 'gestion')
    
    if User.query.filter_by(username=username).first():
        flash("Ce nom d'utilisateur existe déjà.", "danger")
    else:
        from werkzeug.security import generate_password_hash
        new_user = User(
            username=username, 
            email=email,
            password_hash=generate_password_hash(password, method='pbkdf2:sha256'), 
            role=role
        )
        db.session.add(new_user)
        db.session.commit()
        log_audit_action(f"Création de l'utilisateur {username} ({role})")
        flash("Utilisateur ajouté avec succès.", "success")
        
    return redirect(url_for('admin.users_dashboard'))

@bp.route('/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id == session.get('user_id'):
        flash("Vous ne pouvez pas supprimer votre propre compte.", "danger")
        return redirect(url_for('admin.users_dashboard'))
        
    user = User.query.get_or_404(user_id)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    log_audit_action(f"Suppression de l'utilisateur {username}")
    flash(f"L'utilisateur {username} a été supprimé.", "success")
    return redirect(url_for('admin.users_dashboard'))

@bp.route('/edit_user/<int:user_id>', methods=['POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')
    
    if email is not None:
        user.email = email
    if role and user_id != session.get('user_id'):  # Empêcher de changer son propre rôle
        user.role = role
    if password:
        from werkzeug.security import generate_password_hash
        user.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
    db.session.commit()
    log_audit_action(f"Modification de l'utilisateur {user.username}")
    flash("Utilisateur mis à jour avec succès.", "success")
    return redirect(url_for('admin.users_dashboard'))

@bp.route('/dev/reset_db_annual', methods=['POST'])
@admin_required
def reset_db_annual():
    # Création du backup JSON (Archivage)
    if not os.path.exists('backups'):
        os.makedirs('backups')
        
    membres = Member.query.all()
    archive_data = []
    for m in membres:
        archive_data.append({
            "id": m.id, "nom": m.nom, "prenom": m.prenom, "email": m.email,
            "statut_membre": m.statut_membre, "renouvellement": m.renouvellement,
            "is_present": m.is_present, "date_bapteme": m.date_bapteme
        })
        
        # Reset des variables éphémères de l'AG passée
        m.is_present = False
        m.is_refused = False
        m.check_in_time = None
        m.qr_code_token = None
    
    # Suppression des procurations et pending mods révolues
    Proxy.query.delete()
    PendingModification.query.delete()
    db.session.commit()
    run_backups()
    
    filename = f"backups/archive_ag_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(archive_data, f)
        
    log_audit_action("ARCHIVAGE & RÉINITIALISATION ANNUELLE DE LA BASE DE DONNÉES.")
    flash(f"L'année a été clôturée. Archive sauvegardée sous {filename}.", "success")
    return redirect(url_for('admin.members_dashboard'))

@bp.route('/send_campaign_renewal', methods=['POST'])
@admin_required
def send_campaign_renewal():
    membres = Member.query.filter_by(renouvellement='Non').all()
    mail = current_app.extensions.get('mail')
    count = 0
    if mail:
        for m in membres:
            if m.email:
                msg = Message(
                    subject="Rappel : Renouvellement de votre adhésion EEA",
                    sender=current_app.config.get('MAIL_USERNAME', 'noreply@eea.com'),
                    recipients=[m.email]
                )
                msg.body = f"Bonjour {m.prenom},\n\nVotre adhésion n'est pas à jour. Rendez-vous sur le portail pour modifier votre profil.\n\nL'équipe EEA."
                try:
                    mail.send(msg)
                    count += 1
                except:
                    pass
                    
    log_audit_action(f"Campagne de mails de renouvellement envoyée à {count} membres.")
    flash(f"Campagne de relance envoyée à {count} membres non-renouvelés.", "info")
    return redirect(url_for('admin.members_dashboard'))

@bp.route('/export/db')
@admin_required
def export_db():
    db_path = os.path.join(current_app.root_path, '..', 'eea_ag_v3.db')
    if os.path.exists(db_path):
        log_audit_action("Téléchargement manuel de la base de données (.db) et sauvegarde déclenchée")
        
        # 1. Copie locale dans backups/manual/
        manual_dir = os.path.join(current_app.root_path, '..', 'backups', 'manual')
        os.makedirs(manual_dir, exist_ok=True)
        import shutil
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        local_backup = os.path.join(manual_dir, f"eea_ag_v3_{timestamp}.db")
        shutil.copy2(db_path, local_backup)
        
        # 2. Déclenchement de la synchro NAS complète (DB incluse)
        run_backups()
        
        return send_file(db_path, as_attachment=True, download_name=f"EEA_Manager_{datetime.now().strftime('%Y%m%d')}.db")
    flash("Fichier de base de données introuvable.", "danger")
    return redirect(url_for('admin.members_dashboard'))

@bp.route('/restore_db', methods=['POST'])
@admin_required
def restore_db():
    if 'db_file' not in request.files:
        flash("Aucun fichier sélectionné.", "danger")
        return redirect(url_for('admin.members_dashboard'))
        
    file = request.files['db_file']
    if file.filename == '':
        flash("Aucun fichier sélectionné.", "danger")
        return redirect(url_for('admin.members_dashboard'))
        
    if file and file.filename.endswith('.db'):
        db_path = os.path.join(current_app.root_path, '..', 'eea_ag_v3.db')
        
        try:
            # On ferme proprement les sessions en cours avant écrasement
            db.session.remove()
            db.engine.dispose()
            
            # Sauvegarde de sécurité juste avant écrasement
            if os.path.exists(db_path):
                backup_path = os.path.join(current_app.root_path, '..', 'backups', f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
                os.rename(db_path, backup_path)
            
            # Sauvegarder le nouveau fichier
            file.save(db_path)
            
            # Reconnexion forcée
            db.engine.connect()
            
            log_audit_action("RESTAURATION DE LA BASE DE DONNÉES EFFECTUÉE DEPUIS UN FICHIER.")
            flash("La base de données a été restaurée avec succès. L'application utilise maintenant les nouvelles données.", "success")
            
        except Exception as e:
            flash(f"Erreur lors de la restauration : {str(e)}", "danger")
            
    else:
        flash("Seuls les fichiers .db SQLite sont autorisés.", "danger")
        
    return redirect(url_for('admin.members_dashboard'))

@bp.route('/export/csv/<export_type>')
@admin_required
def export_csv(export_type):
    from flask import Response
    import csv, io
    from app.utils import get_export_data
    
    if export_type not in ['members', 'ag']:
        flash("Type d'export invalide.", "danger")
        if request.referrer and 'ag' in request.referrer:
            return redirect(url_for('admin.ag_dashboard'))
        return redirect(url_for('admin.members_dashboard'))
        
    headers, data = get_export_data(export_type)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f"EEA_{export_type.upper()}_{timestamp}.csv"
    
    output = io.StringIO()
    # UTF-8 BOM pour l'ouverture facile sous Excel
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    writer.writerow(headers)
    writer.writerows(data)
    
    csv_content = output.getvalue()
    
    # 1. Copie locale dans backups/manual/
    manual_dir = os.path.join(current_app.root_path, '..', 'backups', 'manual')
    os.makedirs(manual_dir, exist_ok=True)
    local_backup = os.path.join(manual_dir, filename)
    with open(local_backup, 'w', encoding='utf-8-sig') as f:
        f.write(csv_content)
        
    # 2. Déclenchement de la synchro GSheet et NAS
    run_backups()
    
    log_audit_action(f"Téléchargement manuel CSV ({export_type.upper()}) et sauvegarde déclenchée")
    
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
