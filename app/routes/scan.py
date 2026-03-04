from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models import db, Member
from app.routes.admin import admin_required
from datetime import datetime

bp = Blueprint('scan', __name__)

@bp.route('/manager')
@admin_required
def manager_interface():
    # Liste de tous les membres pour la recherche manuelle
    membres = Member.query.order_by(Member.nom).all()
    
    # Statistiques rapides pour le haut de la page
    total = len(membres)
    presents = sum(1 for m in membres if m.is_present)
    
    return render_template('scan/manager.html', membres=membres, stats={"total": total, "presents": presents})

@bp.route('/display')
@admin_required
def tv_display():
    # Utilisé pour l'écran TV projeté dans la salle avec la jauge en direct
    membres = Member.query.all()
    total = len(membres)
    presents = sum(1 for m in membres if m.is_present)
    quorum = (total // 2) + 1 if total > 0 else 0
    percent_quorum = round((presents / quorum * 100), 1) if quorum > 0 else 0
    
    # On limite à 100% visuellement
    if percent_quorum > 100: percent_quorum = 100
    
    stats = {
        'total': total,
        'presents': presents,
        'quorum_target': quorum,
        'quorum_percent': percent_quorum
    }
    return render_template('scan/display.html', stats=stats)

# --- API Endpoints for dynamic scanning ---

@bp.route('/api/preview_scan', methods=['POST'])
@admin_required
def api_preview_scan():
    data = request.get_json()
    member_id = data.get('member_id')
    
    m = Member.query.get(member_id)
    if not m:
        return jsonify({"success": False, "message": "Membre non trouvé."})
        
    if m.is_present:
        return jsonify({"success": False, "message": f"{m.prenom} {m.nom} est DÉJÀ enregistré(e) comme présent(e)."})
        
    if m.is_refused:
        return jsonify({"success": False, "message": f"Accès REFUSÉ pour {m.prenom} {m.nom}. Vérifiez avec l'administration."})
        
    global last_scanned_state
    last_scanned_state = {
        'id': m.id,
        'nom': m.nom,
        'prenom': m.prenom,
        'email': m.email,
        'status': 'verifying',
        'timestamp': datetime.now().timestamp()
    }
    
    return jsonify({
        "success": True, 
        "member_info": {
            "id": m.id,
            "nom": m.nom,
            "prenom": m.prenom,
            "email": m.email,
        }
    })

@bp.route('/api/checkin', methods=['POST'])
@admin_required
def api_checkin():
    data = request.get_json()
    member_id = data.get('member_id')
    
    m = Member.query.get(member_id)
    if not m or m.is_present or m.is_refused:
        return jsonify({"success": False, "message": "Opération invalide."})
        
    m.is_present = True
    m.check_in_time = datetime.now().strftime("%H:%M:%S")
    db.session.commit()
    
    # Mettre à jour l'état global pour dire "Validé"
    global last_scanned_state
    last_scanned_state = {
        'id': m.id,
        'nom': m.nom,
        'prenom': m.prenom,
        'email': m.email,
        'status': 'validated',
        'timestamp': datetime.now().timestamp()
    }
    
    return jsonify({
        "success": True, 
        "message": f"Entrée de {m.prenom} {m.nom} VALIDÉE.",
        "member_name": f"{m.prenom} {m.nom}",
        "time": m.check_in_time
    })

@bp.route('/api/cancel_scan', methods=['POST'])
@admin_required
def api_cancel_scan():
    global last_scanned_state
    last_scanned_state = None
    return jsonify({"success": True})

# --- User Screen Synchronisation ---

# Variable globale pour stocker temporairement le dernier scan
# (Dans un système complexe ou multi-process, utiliser Redis/Memcached)
last_scanned_state = None

@bp.route('/user_screen')
@admin_required
def user_screen():
    return render_template('scan/user_screen.html')

@bp.route('/api/last_scan')
@admin_required
def api_last_scan():
    global last_scanned_state
    if not last_scanned_state:
        return jsonify({'has_scan': False})
        
    # On garde l'affichage actif pendant 7 secondes
    current_time = datetime.now().timestamp()
    if current_time - last_scanned_state['timestamp'] > 7:
        last_scanned_state = None
        return jsonify({'has_scan': False})
        
    return jsonify({
        'has_scan': True,
        'member': last_scanned_state
    })
