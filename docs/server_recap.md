# Documentation de Déploiement & Architecture Serveur - EEA Manager

Ce document sert de référence technique pour comprendre l'architecture, les paramètres de sécurité, et les méthodes de sauvegarde implantées dans l'application *EEA Manager V3*, conçue pour être auto-hébergée par l'Église En Action d'Argenteuil.

---

## 1. Architecture Générale & Auto-Hébergement
L'application a été conçue pour fonctionner avec un niveau de sécurité optimal, tout en répondant aux exigences du RGPD pour protéger les données de la communauté.

**Le Serveur "Mini-PC" (Central) :**
- L'application Flask (Python) et sa base de données SQLite3 (`eea_ag_v3.db`) tournent en local sur le Mini-PC.
- Cet ordinateur n'a pas besoin (et ne doit pas) exposer son port interne (ex: 5001) publiquement sur la box internet du réseau de l'Église.
- La base de données est contenue dans un seul fichier, ce qui rend l'Hébergement extrêmement portable.

### Sécurisation & Bloquage Interne
L'application gère de façon stricte les droits d'accès :
- Tous les modules commençant par `/admin` (Back-office de Membre, Paramètres système, Historiques) et `/scan` (Interfaces des réceptionnistes) **ne sont accessibles qu'aux comptes avec des rôles validés** (`admin` et `gestion`).
- Seules les pages du portail public (`/` , `/inscription`, `/procuration`, `/mentions-legales`) sont accessibles aux visiteurs non-authentifiés.

---

## 2. Hébergement de la DMZ avec le sous-domaine OVH
>❓ **Avis sur la question :** "Mettre la DMZ sur un sous-domaine du site internet eglisenaction.fr chez OVH serait-il une bonne idée ?"

**✅ C'est non seulement une excellente idée, mais c'est la MEILLEURE chose à faire !**

C'est d'ailleurs le standard en architecture réseau moderne. Voici exactement comment tu dois structurer la chose pour éviter toutes les attaques DDOS / Intrusions :
1. Sur le réseau interne (Livebox de l'Église ou Pare-Feu interne), tu fais une règle NAT qui redirige le port web (ex: 443) vers ton mini-PC local en interne.
2. Chez OVH (ton DNS `eglisenaction.fr`), tu crées un sous-domaine `membres.eglisenaction.fr` (ou `portail.eglisenaction.fr`) de type `A` pointant vers l'Adresse IP Publique Fixe de l'Église.
3. **Le Bouclier Anti-DDoS : Cloudflare**. Il est **impératif** pour t'éviter toute attaque de brancher le nom de domaine sur un compte Cloudflare gratuit. C'est le pare-feu de Cloudflare (WAF) qui fera office de **Reverse Proxy** pour encaisser toutes les attaques du web. 
4. Tu obtiendras un Cadenas Vert HTTPS validé pour ce sous-domaine, rendant le traitement des OTP et le profil des membres 100% sécurisés aux yeux de la loi.

---

## 3. Topologie des Backups (Sauvegardes)
Le pire cauchemar d'un ERP "On-Premise" (auto-hébergé chez soi) est qu'en cas de sinistre du "Mini-PC" (vol, casse, disque dur grillé), toutes les données soient perdues. Nous avons donc mis en place la fameuse technique du Backup `3-2-1` intégrée dans le code source (*3 copies, 2 supports différents, 1 copie hors-site*).

### A. La Base de données brute
- Le fichier `eea_ag_v3.db` gère toute l'application. 
- Il peut à présent être téléchargé (`Export DB`) directement depuis le tableau de bord Admin pour être manipulé.
- Un bouton `Restaurer Backup` a été ajouté au Back-Office pour envoyer une disquette `.db` en urgence et écraser le système corrompu si une catastrophe survient. (Lorsqu'on écrase, le système crée quand même un backup local du fichier corrompu `pre_restore_2026.db` par sécurité).

### B. Les Archives JSON Intrapolables
- Lors de chaque **Clôture Annuelle** (généralement réalisée après l'AG), le système gèle la base de donnée sous le format JSON (`archive_ag_2026.json`). 
- Cela fige la liste exacte de cette année-là et ces fichiers servent à alimenter dynamiquement l'onglet *"Archives Précédentes"* de l'interface des Membres.

### C. La Synchronisation Cloud Automatisée (Cold Storage)
Lorsqu'un administrateur valide ou ajoute une ligne, l'application génère **deux types de fichiers CSV :**
1. Un rapport "Membres_Only" (Nom, mails, adresses) -> Exporté sur le paramètre `NAS_BACKUP_PATH_MEMBERS` et `GSHEET_URL_MEMBERS`
2. Un rapport "Analytics AG" (Heure Scan, Présences, Statut) -> Exporté sur `NAS_BACKUP_PATH_AG` et `GSHEET_URL_AG`

**Déclenchement des sauvegardes :**
- **À chaque événement :** Ces fichiers sont téléversés **silencieusement** et automatiquement en Threading lors d'actions clés (ajout, clôture).
- **Planification Hebdomadaire (NOUVEAU) :** Un processus d'arrière-plan tourne 24h/24 dans le serveur et se réveille toutes les semaines (le Dimanche à 03h00) pour envoyer sans intervention humaine une copie de la `.db` et des `CSV` au NAS et à Google Sheets.
- **Exports Manuels (NOUVEAU) :** Lorsqu'un bouton "Export DB" ou "Export CSV" est cliqué, l'application enregistre désormais une copie dans `backups/manual/`, téléverse au NAS/GSheet, et télécharge le fichier sur le navigateur Web, garantissant la règle du 3-2-1 instantanément.

---

## 4. Maintenance / Résolution de Bugs Fréquents

1. **Erreur SMTP (`L'Envoi du mail a échoué`)**
   - Causée par le changement de mot de passe du serveur mail (`informatique@eglisenaction.fr`).
   - S'il y a un changement, le fichier `.env` doit être mis à jour au niveau de `MAIL_PASSWORD` puis l'application relancée (`python run.py`)
2. **"Token OTP Expiré" alors que le délai de 5min n'est pas écoulé**
   - Causée par une désynchronisation de l'heure. Le Mini-PC hébergeant l'application doit être réglé sur les serveurs NTP automatiques pour avoir l'heure exacte.
3. **Le Tableau de Quart n'est pas à jour après la Clôture Annuelle**
   - Vider le cache du navigateur `Ctrl + F5` si de vieux "Non Renouvelés" ou présents à l'AG persistent.
