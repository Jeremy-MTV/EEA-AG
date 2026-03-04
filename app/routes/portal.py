from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import db, Member, PendingModification, Proxy
from app.utils import generate_otp_for_member, send_otp_email
import json

bp = Blueprint('portal', __name__)

@bp.route('/')
def index():
    return render_template('portal/index.html')

@bp.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'POST':
        # Nouveau membre : "Futur membre"
        new_m = Member(
            nom=request.form.get('nom'),
            prenom=request.form.get('prenom'),
            email=request.form.get('email'),
            telephone=request.form.get('telephone'),
            renouvellement='Non', # Pas encore validé
            adresse=request.form.get('adresse'),
            code_postal=request.form.get('code_postal'),
            ville=request.form.get('ville'),
            date_bapteme=request.form.get('date_bapteme'),
            lieu_bapteme=request.form.get('lieu_bapteme'),
            statut_membre='Futur membre'
        )
        db.session.add(new_m)
        db.session.commit()
        
        # Le mailing de confirmation automatique sera implémenté plus tard
        flash("Inscription enregistrée avec succès. Vous recevrez un email de confirmation prochainement.", "success")
        return redirect(url_for('portal.index'))
        
    return render_template('portal/inscription.html')

@bp.route('/login', methods=['GET', 'POST'])
def login_otp():
    if request.method == 'POST':
        email_or_id = request.form.get('identifiant')
        
        # Recherche par ID ou par Email
        if email_or_id.isdigit():
            m = Member.query.get(int(email_or_id))
        else:
            m = Member.query.filter_by(email=email_or_id).first()
            
        if m and m.email:
            otp_code, totp_obj = generate_otp_for_member(m)
            if send_otp_email(m, otp_code):
                session['verif_member_id'] = m.id
                flash(f"Un code à 6 chiffres a été envoyé à {m.email}.", "success")
                return redirect(url_for('portal.verify_otp'))
            else:
                flash("Erreur lors de l'envoi de l'email. Veuillez réessayer.", "danger")
        else:
            flash("Membre introuvable ou adresse email manquante.", "danger")
            
    return render_template('portal/login_otp.html')

@bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'verif_member_id' not in session:
        return redirect(url_for('portal.login_otp'))
        
    m = Member.query.get(session['verif_member_id'])
    if not m:
        return redirect(url_for('portal.login_otp'))
        
    if request.method == 'POST':
        code = request.form.get('otp_code')
        _, totp_obj = generate_otp_for_member(m)
        
        if totp_obj.verify(code, valid_window=2): # Tolérance de ~30s
            session['portal_member_id'] = m.id
            session.pop('verif_member_id', None)
            flash("Connexion réussie.", "success")
            return redirect(url_for('portal.profil'))
        else:
            flash("Code invalide ou expiré.", "danger")
            
    return render_template('portal/verify_otp.html', email=m.email)

@bp.route('/profil', methods=['GET', 'POST'])
def profil():
    if 'portal_member_id' not in session:
        return redirect(url_for('portal.login_otp'))
        
    m = Member.query.get(session['portal_member_id'])
    
    if request.method == 'POST':
        # Collecter les modifications
        mods = {}
        fields = ['adresse', 'code_postal', 'ville', 'telephone', 'email']
        for f in fields:
            new_val = request.form.get(f)
            if new_val and new_val != getattr(m, f):
                mods[f] = new_val
                
        if mods:
            pending = PendingModification(
                member_id=m.id,
                data_json=json.dumps(mods)
            )
            db.session.add(pending)
            db.session.commit()
            flash("Vos modifications ont été soumises pour validation à l'administration.", "success")
        else:
            flash("Aucune modification détectée.", "info")
            
    return render_template('portal/profil.html', m=m)

@bp.route('/logout')
def logout():
    session.pop('portal_member_id', None)
    return redirect(url_for('portal.index'))

@bp.route('/procuration', methods=['GET', 'POST'])
def procuration():
    if 'portal_member_id' not in session:
        flash("Veuillez vous identifier pour déclarer une procuration.", "info")
        return redirect(url_for('portal.login_otp'))
        
    m = Member.query.get(session['portal_member_id'])
    
    if request.method == 'POST':
        mandataire_id = request.form.get('mandataire_id')
        type_ag = request.form.get('type_ag')
        
        # Vérifions que le mandataire existe et est différent du mandant
        mandataire = Member.query.get(mandataire_id)
        if not mandataire or mandataire.id == m.id:
            flash("Mandataire invalide.", "danger")
            return redirect(url_for('portal.procuration'))
            
        # Règle Métier : Max 2 procurations par mandataire (En attente ou Validée)
        current_proxies = Proxy.query.filter_by(mandataire_id=mandataire.id).count()
        if current_proxies >= 2:
            flash(f"{mandataire.prenom} a déjà atteint la limite légale de 2 procurations.", "warning")
            return redirect(url_for('portal.procuration'))
            
        # Vérifions que le membre ne donne pas 2 fois sa procuration pour le même type
        already_given = Proxy.query.filter_by(mandant_id=m.id).all()
        for p in already_given:
            if p.type_ag == type_ag or p.type_ag == 'DEUX' or type_ag == 'DEUX':
                flash("Vous avez déjà donné une procuration couvrant ce type d'AG.", "danger")
                return redirect(url_for('portal.procuration'))
                
        new_proxy = Proxy(
            mandant_id=m.id,
            mandataire_id=mandataire.id,
            type_ag=type_ag
        )
        db.session.add(new_proxy)
        db.session.commit()
        flash("Votre déclaration de procuration a été enregistrée. Elle sera validée définitivement le jour de l'AG.", "success")
        return redirect(url_for('portal.profil'))
        
    # On récupère les autres membres pour le select
    autres_membres = Member.query.filter(Member.id != m.id, Member.statut_membre == 'Membre année en cours').order_by(Member.nom).all()
    # On récupère les procurations données par le membre
    mes_procurations = Proxy.query.filter_by(mandant_id=m.id).all()
    
    return render_template('portal/procuration.html', m=m, autres_membres=autres_membres, mes_procurations=mes_procurations)

@bp.route('/mentions-legales')
def mentions_legales():
    return render_template('portal/mentions.html')
