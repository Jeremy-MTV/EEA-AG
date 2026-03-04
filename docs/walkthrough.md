# EEA Manager - Livraison finale & Walkthrough

Ce document résume toutes les implémentations, les modifications de structure, et les nouvelles fonctionnalités ajoutées à l'application **EEA Manager** (anciennement EEA AG Manager V3) pour répondre au cahier des charges d'évolution.

---

## 🚀 Fonctionnalités Déployées

### 1. Kiosque et Écran Utilisateur en Temps Réel
> [!NOTE]
> L'ancien mode Kiosque autonome a été supprimé pour des raisons de sécurité.  
À la place, une interface de **Validation en 2 étapes** a été mise en place pour les réceptionnistes (`/manager`), coordonnée en temps réel avec un **Écran Utilisateur** (`/user_screen`).

- Lorsqu'un membre passe son QR Code sous la douchette, la carte du membre s'affiche instantanément sur l'écran du réceptionniste pour validation manuelle.
- Simultanément, l'écran de retour (`/user_screen`) tourné vers le membre affiche son "Nom, Prénom et Email", lui confirmant que sa carte a bien été lue.
- La page d'administration globale de l'AG (`/admin/ag`) est aussi mise à jour **en temps réel** grâce à de l'Ajax Polling, faisant progresser la jauge du Quorum sous les yeux de l'administrateur sans qu'il ait besoin de rafraîchir la page.

### 2. Séparation des Rôles et Gestion des Utilisateurs
- Création d'une interface de gestion des administrateurs (`/admin/users`) permettant d'attribuer des emails, de gérer les mots de passe et les rôles.
- **Rôle "Admin"** : Accès total au Back-Office (Gestion des AG, Gestion de la base Membres, Export complet, Sauvegardes manuelles et Configuration Utilisateurs).
- **Rôle "Gestion"** : Accès restreint uniquement à la vue "Gestion de l'Assemblée Générale" le Jour-J (statistiques du quorum, lancer l'écran Utilisateur, lancer l'interface de scan).
- Les boutons d'accès vers les panneaux restreints disparaissent automatiquement de l'écran d'accueil du portail si l'utilisateur n'en possède pas les droits.

### 3. Architecture Serveur, Sauvegardes & Conformité RGPD
> [!IMPORTANT]
> L'application doit désormais tourner sur un réseau interne dans les locaux de l'Église (Mini-PC/ERP). 

- Ajout d'une section dynamique **"Mentions Légales & RGPD"** (`/mentions-legales`) accessible pour les visiteurs et expliquant le cycle de vie et la confidentialité de leurs données.
- Paramétrisation complète du fichier caché `.env` pour éviter tout mot de passe en dur dans le code (Mot de passe OTP de l'Église, chemin NAS et lien de l'API Google Cloud).
- **Synchronisations automatiques en arrière-plan** : 
    - Exporte le fichier vers le **lecteur partagé NAS Synology** `NAS_BACKUP_PATH`.
    - Agit en tant que Compte de Service Google pour injecter le CSV directement dans un GSheet `GSHEET_URL` partagé avec votre compte e-mail principal.
- **Sauvegarde Hebdomadaire (Cron Thread)** : Un daemon interne est démarré au lancement du serveur pour déclencher le lot de sauvegarde complète (DB + CSV vers NAS et GSheet) chaque dimanche à 3h00 du matin, sans utiliser d'outils externes.

### 4. Exports Manuels, Pop-ups de sécurité et Archives Historiques
- La page *"Gestion des Membres"* et *"Gestion des AG"* disposent de boutons `Export DB` et `Export CSV` sécurisés.
- En cliquant sur ces exports, un **Pop-up de confirmation** (Modal) s'ouvre. Au lancement, l'export effectue en réalité 4 actions simultanément : Téléchargement navigateur, Sauvegarde Locale (`/backups/manual/`), Syncro NAS, Synchro GSheet.
- Le système produit des fichiers **séparés** : d'un côté un fichier propre *"Annuaire des Membres"* et de l'autre *"Données de l'AG"*.
- Un bouton visuel rapide **"Non Renouvelés"** trie instantanément le tableau en cours pour faciliter le repérage.
- **Onglets d'Archives** : À chaque Clôture Annuelle de l'AG, un fichier `archive_ag_20[XX].json` est figé. Une interface d'onglets permet de revisiter les AG historiques en 1 clic.
- **Restauration d'Urgence (Import DB)** : Un bouton Administrateur permet d'envoyer (upload) un fichier `.db` existant pour écraser le système actuel en cas de corruption sévère, effectuant au passage un backup de sécurité pré-écrasement.

### 5. Intégration OVH pour l'OTP et les Convocations Ciblées
- Les certificats TLS et l'authentification SMTP ont été adaptés pour cibler directement les serveurs MX Plan d'OVH (`ssl0.ovh.net`), libérant l'Église de la dépendance à Google Workspace.
- **Fiabilité Anti-Spam (Content-ID)** : Les QR codes joints dans les emails sont désormais encodés en dur (`cid:qrcode`) de manière propre pour contourner les blocages par les boîtes mail strictes comme Gmail ou Apple Mail.
- **Interface de Convocations Ciblées** : Fini l'envoi massif incontrôlable ! Un bouton `Convocations` ouvre à présent une fenêtre permettant de cocher unitairement les membres à convoquer, avec une barre de recherche en temps réel et un bouton "Tout sélectionner".

---

## 🛠 Entretien Futur
* **Nouveaux Administrateurs** : Toutes les demandes de "reset de mots de passe" internes de l'application (le portoir `EEA Manager`) s'opèrent désormais grâce au rôle super-Admin dans le menu `/admin/users`.
* **Problèmes Google Sheet** : Vérifiez que l'adresse du `robot` généré sur Google Cloud Console a bien les droits **Éditeur** sur le fichier Sheets mentionné dans le `.env`.
* **Guide d'utilisation embarqué** : Le menu **"Guide"** est disponible à l'intérieur même du Back-Office. Ne pas hésiter à le consulter ou le faire lire à un nouvel arrivant au pôle gestion !

---
L'Application *EEA Manager* est désormais **totalement fonctionnelle, sécurisée, archivée et livrable**. Félicitations à toute l'équipe de l'Église En Action ! 🎉
