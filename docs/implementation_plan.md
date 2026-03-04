# Plan d'Implémentation - EEA-AG V3.0

Ce document détaille l'architecture modulaire et les étapes de développement pour la version 3.0 de l'application EEA-AG.

## User Review Required
> [!IMPORTANT]
> - **Migration des données** : Nous allons passer de requêtes SQL brutes à **SQLAlchemy**. Un script de migration lira le fichier `eea_ag_v2.db` actuel pour peupler la nouvelle base de données sans perte de données.
> - **Authentification** : Actuellement, les mots de passe sont en dur dans le code (`USERS` dict). Souhaitez-vous que l'on crée une vraie table `User` dans la base de données avec des mots de passe hachés (via `Werkzeug`) pour les administrateurs et gestionnaires ?
> - **Google Sheet Sync** : L'URL du Google Sheet public sera stockée dans le fichier `.env`. Il faudra fournir cette URL lorsque la fonctionnalité sera prête.

---

## 🏗 Architecture Proposée

L'application sera découpée selon une structure modulaire (Flask Application Factory et Blueprints) :

```text
EEA-AG-main/
├── run.py                 # Point d'entrée de l'application
├── config.py              # Configuration (Clés secrètes, URI DB, Mail)
├── .env                   # Variables d'environnement (Mots de passe mail, etc.)
├── requirements.txt       # Dépendances du projet
└── app/
    ├── __init__.py        # Initialisation de Flask, SQLAlchemy, et enregistrement des Blueprints
    ├── models.py          # Modèles de base de données (Membre, Procuration, AuditLog...)
    ├── utils.py           # Fonctions utilitaires (Envoi email, Génération OTP/QR Code, Sync GSheet)
    ├── routes/
    │   ├── admin.py       # Module 1 : Authentification Admin, Tableau de bord, Gestion
    │   ├── portal.py      # Module 2 : Portail Membres DMZ (Inscription, OTP, Procurations)
    │   ├── kiosk.py       # Module 3 : Assistance sur site (Interface simplifiée)
    │   └── scan.py        # Module 3 : Interface de scan au guichet, API pour l'écran TV
    ├── static/
    │   ├── css/
    │   ├── js/
    │   └── img/
    └── templates/
        ├── base.html      # Layout principal
        ├── admin/         # Vues pour le back-office
        ├── portal/        # Vues publiques (DMZ)
        ├── kiosk/         # Vues pour la tablette d'assistance
        └── scan/          # Vues pour le scan et l'écran TV
```

---

## 🗄 Modèles de Base de données (SQLAlchemy)

### 1. `Member` (Évolution de l'existant)
- Ajout de `statut_membre` : Indique si c'est un "Futur membre", "Membre année en cours" ou "Ancien membre".
- Ajout de `qr_code_token` : Un identifiant unique pour générer le QR Code de chaque membre.

### 2. `AuditLog` ([INNOVATION] Module 1)
- `id`, `user` (Admin/Système), `action` (Texte, ex: "Modification Membre #12"), `timestamp`.

### 3. `PendingModification` (Module 2)
- Stocke les modifications demandées via OTP. `member_id`, `data_json` (les champs modifiés), `statut` (En attente, Approuvé, Rejeté).

### 4. `Proxy` (Procuration - Module 2 et 3)
- `id`, `mandant_id` (Qui donne), `mandataire_id` (Qui reçoit), `type_ag` (AGO, AGE, DEUX), `statut` (En attente, Validée).

### 5. `User` (Administrateurs)
- `id`, `username`, `password_hash`, `role` (Admin, Gestion).

---

## 🛠 Étapes de Développement (Modulaire)

### Étape 1 : Fondation et Migration
- [ ] Initialiser la structure de dossiers (`app/`, `routes/`, `templates/`, `static/`).
- [ ] Créer `config.py` et `app/__init__.py`.
- [ ] Créer `models.py` avec SQLAlchemy.
- [ ] Écrire un script (exécution unique) pour migrer `eea_ag_v2.db` vers la nouvelle structure de base de données SQLAlchemy.

### Étape 2 : Module 1 - Cœur & Back-Office
- [ ] Blueprint `admin.py` : Connexion, Déconnexion, Rôles.
- [ ] Tableau de Bord : Intégration de la jauge de Quorum (Chart.js / Bootstrap progress bar).
- [ ] Datatable éditable et filtrable pour les membres.
- [ ] Intégration du système de Log d'Audit invisible.
- [ ] Fonctionnalité de synchronisation avec Google Sheet (Action 0).

### Étape 3 : Module 2 - Portail Membres (DMZ)
- [ ] Blueprint `portal.py` : Formulaire "Nouveau membre" (Statut : Futur membre).
- [ ] Interface de modification de profil : Envoi OTP par email, validation, et enregistrement dans `PendingModification`.
- [ ] Déclaration de procurations en ligne (contrôle max = 2).

### Étape 4 : Module 3 - Gestion sur Site
- [ ] Fonction Admin d'envoi de convocations par email (via `Flask-Mail` et module `qrcode`).
- [ ] Blueprint `kiosk.py` : Grandes interfaces simples pour le renouvellement rapide sur place.
- [ ] Blueprint `scan.py` : Refonte de l'interface `/manager` avec détection clavier douchette.
- [ ] Pop-up de validation des procurations du mandataire entrant.
- [ ] WebSockets ou Polling JS amélioré pour le /display temps réel.

### Étape 5 : Module 4 - Automatisation
- [ ] Route/Bouton Admin pour la "Clôture Annuelle".
- [ ] Script de dump JSON pour l'archivage.
- [ ] Campagne d'email de masse.
- [ ] Page de guide d'utilisation (`/guide`).

#### [MODIFY] [routes/kiosk.py](file:///Users/prodeea/Downloads/EEA-AG-main/app/routes/kiosk.py)
#### [MODIFY] [templates/kiosk/index.html](file:///Users/prodeea/Downloads/EEA-AG-main/app/templates/kiosk/index.html)

## Phase 7: Global Dashboard & Admin Consolidation (NEW)
**Goal:** Separate Member Management from AG Management, and centralize navigation on the main Portal page.

### Proposed Changes
1.  **Global Portal Integration:**
    - Update `templates/base.html` and `templates/portal/index.html` to include a dynamic top navigation bar based on the current user's session (`gestion` or `admin`).
    - Move login logic to be accessible from the main page (a "Connexion Admin" button).
2.  **Separate Member Management:**
    - Rename the current `admin/dashboard.html` to `admin/members.html`.
    - Create a new route `/admin/members` that focuses strictly on the CRUD of members and modifying their profiles/statuses.
3.  **Separate AG Management:**
    - Create a new route `/admin/ag` and template `admin/ag.html`.
    - This page will contain the real-time Quorum gauge, the "Convocations" button, the link to the `/manager` scanner, the `/kiosk`, and the `/display`.
    - The stats shown here will focus on `is_present` and `is_refused`.
4.  **Admin Routing Updates:**
    - Update `routes/admin.py` to reflect these separated routes.

## Phase 8: Real-time User Screen (Replacing Kiosk)
**Goal:** Remove the self-service kiosk and replace it with a customer-facing "User Screen" that dynamically updates when the receptionist scans a QR code.

### Proposed Changes
1.  **Remove Kiosk:**
    - Delete `app/routes/kiosk.py` and `app/templates/kiosk/index.html`.
    - Remove `kiosk_bp` from `app/__init__.py`.
2.  **Add User Screen `/scan/user_screen`:**
    - Create `app/templates/scan/user_screen.html`. This page will display "En attente de scan" by default.
    - It will poll an API endpoint `/api/last_scan` every second via AJAX.
3.  **Real-time State Sync:**
    - In `app/routes/scan.py`, maintain a temporary state (e.g., a global variable or dictionary) holding the `last_scanned_member` (name, prenom, email, photo if any, status) and a timestamp.
    - When the receptionist scans a code on `/manager`, the `api_checkin` function updates this `last_scanned_member` state.
    - The `/user_screen` picks up this state and displays the member's profile nicely for 5-10 seconds before clearing.
4.  **Admin AG Updates:**
    - Update `admin/ag.html` to remove the Kiosk button and instead display "Écran Utilisateur (Synchronisé au Scan)".

## Phase 9: Role Separation & User Management
**Goal:** Differentiate permissions between `admin` and `gestion` roles, add an interface to manage application users, and rename the app to "EEA Manager".

### Proposed Changes
1.  **Role Separation:**
    - `admin` role has full access (Members, AG, Users).
    - `gestion` role is restricted ONLY to the AG Management (`scan.manager_interface`, `scan.tv_display`, `admin.ag_dashboard`) and cannot access `admin.members_dashboard` or `admin.add_member`.
    - Update the Portal Dashboard to hide restricted cards from `gestion` users.
2.  **User Management Interface:**
    - Create a new route `/admin/users` and template `admin/users.html`.
    - Allow adding new users (username, password, role), modifying their passwords, and deleting them.
    - Add a new "Gestion des Utilisateurs" card on the Main Portal (only visible to `admin`).
3.  **Application Renaming:**
    - Search and replace "EEA AG Manager V3" with "EEA Manager" across all templates (`base.html`, `index.html`, etc.).
## Phase 10: Security, Architecture & External Backups
**Goal:** Harden the application for production, comply with GDPR, and ensure member data is continuously backed up to a Synology NAS and a Google Sheet.

### Proposed Changes
1.  **Architecture & Deployment Strategy:**
    - Document the recommended architecture: Hosting the Flask app on a local Mini-PC (e.g., using Gunicorn + Nginx) within the Church's internal LAN.
    - Set up a DMZ or Reverse Proxy with routing rules: Only routes starting with `/` (Portal public home), `/inscription`, `/login_otp`, `/procuration`, and `/mentions-legales` are accessible from the outside. All `/admin` and `/scan` routes are strictly blocked from external IPs and restricted to the internal LAN.
2.  **GDPR Compliance (Mentions Légales):**
    - Create a new route `/mentions-legales` and template `portal/mentions.html`.
    - Add a footer to `base.html` (only visible on public pages) with a link to the GDPR/Mentions Légales page.
3.  **Automated Backups (NAS Synology):**
    - Create a Python job/function that exports the `members` table to a CSV or JSON file.
    - Save this file to a mounted network path (e.g., `/Volumes/AG/Members_List_Log/` on Mac, or a configurable path via `.env` like `NAS_BACKUP_PATH=/path/to/nas/folder`).
    - Trigger this backup automatically whenever a member is added, modified, or approved by an Admin.
4.  **Google Sheet Synchronization:**
    - Use the `gspread` and `google-auth` libraries (if not already fully set up) to push the member list updates to a Google Sheet shared with `musiconnexion@gmail.com`.
    - Provide the User with a clear, step-by-step guide (in the `/guide` page or a separate Markdown file) on how to generate the Google Service Account JSON key, how to construct the NAS path, and how to configure these in the `.env` file.
## Phase 11: Advanced Data Management & Archiving
**Goal:** Create manual backup downloads, separate NAS/GSheet destinations for Members/AG, display historical lists, and facilitate annual renewals.

### Proposed Changes
1.  **Separated Backup Destinations:**
    - Update `config.py` and `.env` to split variables: `NAS_BACKUP_PATH_MEMBERS`, `NAS_BACKUP_PATH_AG`, `GSHEET_URL_MEMBERS`, `GSHEET_URL_AG`.
    - Modify `utils.py` backup functions to export distinct datasets (one with only member details, one with AG analytics) to their respective destinations.
2.  **Manual Backup Buttons:**
    - Add real-time DB download (`.db` SQLite file) and CSV export buttons in `admin/members.html` and `admin/ag.html`.
    - Create routes like `/admin/download_db` and `/admin/export_csv/<type>`.
3.  **Archived Members Tabs:**
    - Update `admin/members.html` to include Bootstrap tabs: "Année en cours" and "Archives Précédentes".
    - In `routes/admin.py`, read the local `backups/archive_ag_*.json` files to dynamically render historical lists from previous years.
4.    - Add visual quick-filters (e.g., button to show only "Non Renouvelés") in `admin/members.html` table.

## Phase 12: Final Verification & Delivery
**Goal:** Test and deliver the requested features ensuring zero regressions.

## Phase 13: DB Restoration & Final Server Documentation
**Goal:** Provide an emergency DB restore feature from the UI and deliver a comprehensive recap guide for hosting and security.

### Proposed Changes
1.  **Emergency DB Restore Feature:**
    - Add a file upload form (accepting `.db` files) next to the "Export DB" button in `admin/members.html`.
    - Create a secure route `/admin/restore_db` that accepts the uploaded `.db` file.
    - Validate the file, replace the current `eea_ag_v3.db`, and restart the Flask application correctly or redirect to login.
2.  **Comprehensive Recap Document:**
    - Generate a final markdown artifact (`server_recap.md`) detailing:
        - All deployed features and architecture (App + DB + Reverse Proxy).
        - Backup mechanisms (NAS + GSheet) and their locations.
        - Security best practices (DMZ, WAF, Cloudflare, OVH usage).
        - Response to the user's specific question regarding hosting the DMZ under a subdomain of the existing OVH site.

## Phase 14: Scheduled Backups & Enhanced Export Feedback
**Goal:** Automate weekly backups and provide clear feedback to the user regarding the destination of manually exported files.

### Proposed Changes
1.  **Weekly Scheduled Backups:**
    - Use a background thread in `app/__init__.py` to run weekly backups (DB and CSVs to NAS and GSheet) without requiring `cron` or external tools.
2.  **Enhanced Manual Exports (Popups & Routing):**
    - Create a Bootstrap Modal in `admin/members.html` and `admin/ag.html` that shows up when clicking "Export DB" or "Export CSV".
    - The Modal will explain: "The file will be downloaded locally, saved on the server in `/backups/manual`, synchronized on the NAS, and updated on Google Sheets."
    - Update `utils.py` to copy the `.db` file to the NAS (currently only CSVs are sent to NAS).
    - Update the `/export/db` and `/export/csv/<type>` routes to save a copy in the local `backups/manual/` directory.
    - Call the backup functions to NAS/GSheet inside these routes simultaneously while returning the file for download.

## Phase 15: Targeted Convocations Interface
**Goal:** Replace the 1-click bulk send button with a Modal popup allowing the Admin to select exactly which members should receive the Convocation email.

### Proposed Changes
1.  **UI Updates (`admin/ag.html`):**
    - Change the current `send_convocations` submit button into a button that opens a new `#convocationsModal`.
    - Build a Modal containing a `<form action="{{ url_for('admin.send_convocations') }}" method="POST">`.
    - Inside the modal, loop through the `membres` list to display a checklist (Nom, Prénom, Email).
    - Add a "Sélectionner Tous" JavaScript button to quickly check all members.
2.  **Backend Updates (`admin.py`):**
    - Modify the `send_convocations` route to process `request.form.getlist('selected_members')`.
    - If the list is empty, flash a warning. 
    - Loop over the selected member IDs to generate their QR codes and send their emails.
    - Make sure to update the Dashboard context in `admin.ag_dashboard` so it passes `membres=Member.query.all()` to the template if it isn't already doing so.

## ✅ Plan de Vérification

1. **Automated / Unit Testing**
   - Nous pourrons écrire quelques tests de base (pytest) pour valider des règles de gestion, notamment la limite de 2 procurations maximum par mandataire, ou la génération correcte des OTP.
2. **Manual Verification**
   - L'utilisateur devra tester le scan (même avec un clavier en tapant l'ID + Entrée) pour simuler la douchette de code-barres.
   - Envoyer de vrais emails sur une adresse de test afin de valider Flask-Mail, et générer un OTP puis vérifier qu'on peut l'insérer sur la page de DMZ pour modifier son profil.
   - Les modifications DMZ devront apparaître correctement dans l'interface Admin pour validation ou rejet.
   - On vérifiera que l'interface `/display` réagit instantanément aux scans réalisés dans `/manager`.
