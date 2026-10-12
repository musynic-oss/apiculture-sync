APICULTURE V1 BÊTA 1.26

Corrections importantes :
- démarrage hors ligne immédiat depuis le cache : plus d'écran noir pendant le réveil de Render ;
- adresse serveur et identifiant remplis automatiquement ;
- connexion mémorisée avec cookie sécurisé HttpOnly pendant un an ;
- configuration également dupliquée dans IndexedDB ;
- demande de stockage persistant au navigateur.

Déploiement :
remplacer server.py et le dossier web dans le dépôt GitHub, puis laisser Render redéployer.
Après mise à jour, saisir la clé d'accès UNE DERNIÈRE FOIS dans Plus > Synchronisation > Configurer > Enregistrer.
