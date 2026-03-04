# EEA Manager (V3)

EEA Manager est une application web Python (Flask) d'auto-hébergement conçue spécifiquement pour l'Église En Action. 
Elle permet la gestion complète de l'annuaire des membres, le suivi des renouvellements, la tenue des Assemblées Générales (AG), ainsi que le contrôle par QR Codes et l'enregistrement assisté depuis un lecteur manuel.

## Fonctionnalités Principales :
* **Portail Membre :** Inscriptions, demandes de renouvellement, mise à jour des profils, et système de mandats (Procurations limitées).
* **Gestion Avancée des AG :** Envoi d'e-mails ciblés contenant des QR Codes (anti-spam SMTP), validation dynamique le jour-J, calcul de quorum en temps réel.
* **Architecture Sécurisée :** Split réseau (Interface d'accueil dans une DMZ publique, Administration locale restreinte), authentification par rôle (Admin, Gestion).
* **Conformité & Intégrité des données :** Sauvegardes automatisées 3-2-1 de la base SQLite et des CSV. Export Cloud Google Sheets et Local NAS Synology via un processus fantôme fonctionnant H24.

*Le guide complet de déploiement, d'architecture et du cycle de vie serveur se trouve dans le document technique `server_recap.md` généré en accompagnement.*
