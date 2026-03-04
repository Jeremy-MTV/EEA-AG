# Checklist de Déploiement Final - "To Be Done"

Voici la liste des actions concrètes que vous (ou l'administrateur réseau de l'Église) devez réaliser manuellement pour que tout le système soit finalisé et pleinement opérationnel en production "On-Premises" (Auto-hébergement).

---

## 1. Sécuriser l'Accès Externe (DMZ / OVH / Cloudflare)
L'objectif est d'avoir une adresse professionnelle du type `https://portail.eglisenaction.fr` tout en masquant votre IP fixe et en vous protégeant des piratages.
- [ ] **Box Internet (Église)** : Aller dans l'interface d'administration (ex: 192.168.1.1) et configurer une règle **NAT/PAT**. Faire pointer les ports 80 et 443 vers l'adresse IP locale statique du Mini-PC hébergeant l'application.
- [ ] **OVH (DNS)** : Se connecter au manager OVH. Créer un sous-domaine (ex: `portail.eglisenaction.fr`) avec un enregistrement de type **A** pointant vers l'Adresse IP publique de la box de l'Église.
- [ ] **Cloudflare (Bouclier WAF)** : 
    - Activer Cloudflare gratuitement sur le nom de domaine `eglisenaction.fr`.
    - Passer le sous-domaine `portail` derrière le "Bouton Orange" (Proxy Cloudflare activé).
    - Régler le SSL/TLS sur **Flexible** ou **Complet**.

## 2. Configuration du Serveur (Mini-PC Local)
- [ ] **Déploiement Python** : Cloner ou copier le code source final sur le Mini-PC.
- [ ] **Installation des dépendances** : Exécuter `pip install -r requirements.txt`.
- [ ] **Démarrage au Boot (Daemon)** : Créer un service Linux (`systemd` -> `eea.service`) ou une tâche planifiée Windows pour que la commande `python run.py` se lance automatiquement au démarrage de la machine, même sans session utilisateur ouverte.

## 3. Paramétrage des Sauvegardes (NAS & Cloud)
Toutes ces opérations se configurent en modifiant les valeurs dans le fichier caché **`.env`** du projet.

**A. Sauvegarde Locale sur le NAS Synology**
- [ ] Monter le lecteur réseau partagé du NAS sur le Mini-PC pour qu'il soit vu comme un disque local (ex: Lettre `Z:\` sous Windows, ou point de montage `/mnt/nas/` sous Linux).
- [ ] Ajuster le chemin dans le `.env` pour `NAS_BACKUP_PATH_MEMBERS` et `NAS_BACKUP_PATH_AG`.
- [ ] *Test* : Cliquez sur "Export CSV" dans l'application et vérifiez que le fichier arrive bien instantanément sur le lecteur partagé du NAS.

**B. Sauvegarde Cloud sur Google Sheets**
- [ ] Se connecter avec le compte d'administration Google (`informatique@eglisenaction.fr`) à [Google Cloud Console](https://console.cloud.google.com).
- [ ] Activer les API **Google Sheets** et **Google Drive**.
- [ ] Créer un **Compte de Service** (robot) et générer une clé au format JSON.
- [ ] Renommer le fichier téléchargé en `service_account.json` et le glisser à la racine du projet, à côté de `run.py`.
- [ ] Créer 2 tableaux Google Sheets vierges depuis le bon Drive (un pour les Membres, un pour l'AG).
- [ ] Partager ces feuilles à l'adresse email absurde générée par le "Compte de Service" (en tant qu'Éditeur).
- [ ] Copier les deux URL complètes de ces fichiers Google Sheets et les coller respectivement dans `GSHEET_URL_MEMBERS` et `GSHEET_URL_AG` du `.env`.

## 4. Maintenance de la Boite E-mail
- [ ] S'assurer que le mot de passe du serveur MX Plan OVH pour `informatique@eglisenaction.fr` n'expire pas.
- [ ] S'il est modifié dans le futur, il suffira simplement de mettre à jour le champ `MAIL_PASSWORD` dans le `.env` et de redémarrer l'application.

---
_L'application EEA Manager sera ensuite autonome, sauvegardée H24, et vos administrés pourront se connecter avec le niveau de sécurité d'un véritable logiciel professionnel._
