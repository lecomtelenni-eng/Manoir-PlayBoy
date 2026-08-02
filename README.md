# Playboy Manor Manager

Petit site local de gestion pour le Manoir Playboy.

## Comptes Direction par défaut
- Identifiant : `SCOTT`
- Identifiant : `MARCUS`
- Identifiant : `KEAVON`
- Mot de passe commun : `Manoir2026!`

Les trois comptes ont le rôle `Direction`.
Une page `Comptes` permet à la Direction de créer d'autres accès.

## Installation sous Windows

1. Installe Python 3.11 ou plus récent.
2. Ouvre le dossier du site.
3. Double-clique sur `LANCER_LE_SITE.bat`.
4. Ouvre ton navigateur sur : http://127.0.0.1:5000

Au premier lancement, le site crée automatiquement la base de données `manoir.db`.

## Fonctions incluses
- Connexion par mot de passe
- Tableau de bord
- Recettes et dépenses
- Événements avec bénéfice estimé
- Personnel et salaires
- Stocks, prix d'achat, prix de vente et marge
- Alertes de stock
- Changement de mot de passe
- Données d'exemple déjà intégrées

## Mise en ligne
Pour un hébergement public, change obligatoirement la clé secrète Flask et utilise un hébergeur adapté.


## En cas de page "Ce site est inaccessible"
Le serveur doit rester lancé sur l'ordinateur.

1. Décompresse entièrement le fichier ZIP.
2. Ne lance pas le fichier directement depuis le ZIP.
3. Double-clique sur `LANCER_LE_SITE.bat`.
4. Attends le message `Site prêt`.
5. Le navigateur s'ouvrira automatiquement.

Si le lancement échoue, ouvre `serveur.log` et lis le message d'erreur.
