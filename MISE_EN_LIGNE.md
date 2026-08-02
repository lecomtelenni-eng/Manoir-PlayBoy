# Mise en ligne sur Render

## Comptes intégrés
- SCOTT
- MARCUS
- KEAVON

Mot de passe commun : `Manoir2026!`

## Étape 1 — Créer le dépôt GitHub
1. Crée un compte sur GitHub si nécessaire.
2. Crée un nouveau dépôt privé, par exemple `playboy-manor-manager`.
3. Décompresse ce dossier.
4. Envoie tous les fichiers décompressés dans le dépôt GitHub.

## Étape 2 — Déployer sur Render
1. Crée un compte Render.
2. Clique sur `New`, puis `Blueprint`.
3. Connecte ton compte GitHub.
4. Sélectionne le dépôt `playboy-manor-manager`.
5. Render détectera automatiquement `render.yaml`.
6. Lance le déploiement.
7. À la fin, Render donnera une adresse du type :
   `https://playboy-manor-manager.onrender.com`

Tous les utilisateurs pourront ouvrir ce lien depuis un téléphone ou un ordinateur.

## Important concernant les données
Le plan gratuit de Render sert surtout aux essais. Avec une base SQLite sans disque persistant,
les données peuvent disparaître lors d'un redéploiement ou d'une reconstruction du service.

Pour conserver durablement les comptes et la comptabilité :
- ajoute un disque persistant Render ;
- monte-le sur `/var/data` ;
- ajoute la variable d'environnement `DATA_DIR=/var/data`.

## Sécurité
- Change le mot de passe commun après le premier test.
- Ne partage pas le lien publiquement.
- Garde le dépôt GitHub privé.
