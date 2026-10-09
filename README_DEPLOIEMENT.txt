APICULTURE V1 BÊTA 1.25 — VERSION PWA

Cette version transforme le prototype HTML en vraie application web installable.

Fichiers à mettre dans le dépôt apiculture-sync :
- server.py
- requirements.txt
- dossier web complet

Après le redéploiement Render :
1. Ouvrir https://apiculture-sync.onrender.com
2. Configurer la synchronisation avec le même identifiant et la même clé.
3. Charger la version cloud.
4. Dans Chrome : Installer l’application.

Le service worker garde l’application disponible hors ligne après le premier chargement.

SECURITE AVANT PUBLICATION DEFINITIVE :
- réinitialiser le mot de passe Neon qui a été visible dans d’anciennes captures ;
- mettre à jour DATABASE_URL dans Render ;
- conserver APICULTURE_SYNC_TOKEN long et secret.
