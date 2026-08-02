# Playboy Manor Manager V2

Cette version utilise PostgreSQL sur Render. Les nouvelles données restent sauvegardées après les redémarrages et les redéploiements.

## Comptes Direction
- SCOTT
- MARCUS
- KEAVON

Mot de passe temporaire commun : `Manoir2026!`

## Installation sur GitHub et Render
1. Décompresse le ZIP.
2. Sur GitHub, remplace les anciens fichiers par tout le contenu du dossier décompressé.
3. Clique sur `Commit changes`.
4. Dans Render, ouvre le Blueprint `Manoir PlayBoy`.
5. Clique sur `Manual sync`.
6. Render créera automatiquement `playboy-manor-db` et reliera le site avec `DATABASE_URL`.

Les données de l'ancienne base SQLite ne sont pas transférées automatiquement.
