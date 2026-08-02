# Playboy Manor Manager V3 COMPLET

## Comptes Direction
- SCOTT
- MARCUS
- KEAVON

Mot de passe temporaire commun : `Manoir2026!`

## Nouveautés V3
- Factures RP multi-produits
- Menu automatique lié au stock
- Retrait automatique du stock
- Calcul automatique du coût, total et bénéfice
- Restauration du stock lors de la suppression d'une facture
- Planning du personnel
- Statistiques et graphiques
- Top produits et vendeurs
- Exports CSV ouvrables avec Excel
- Droits selon les rôles
- Impression / PDF des factures
- PostgreSQL persistant sur Render

## Installation
1. Décompresse le ZIP.
2. Remplace les fichiers du dépôt GitHub par ceux-ci.
3. Commit changes.
4. Sur Render, Manual sync.

Les tables existantes sont conservées. La V3 ajoute automatiquement la table du planning.


## V4 — Fonds premium
Cette version conserve toutes les fonctions de la V3 et ajoute :
- un fond différent pour le tableau de bord ;
- un fond comptabilité/factures ;
- un fond stocks ;
- un fond événements ;
- un fond personnel/planning ;
- un fond statistiques ;
- un fond connexion/comptes ;
- des panneaux avec effet verre et un voile sombre pour la lisibilité.

Les fonds sont intégrés directement dans `static/backgrounds` et ne dépendent d'aucun site externe.


## V5 — Design néon rose/violet
- Fonds réalistes intégrés directement au projet
- Interface inspirée de la maquette validée
- Boutons et accents rose/violet
- Panneaux noirs effet verre
- Logo NF exact en bas à droite
- Toutes les fonctions de la V4.1 conservées

## V5.2 — Icônes produits et catalogue
- Icônes devant les produits dans le stock
- Aperçu de l'icône dans la facture multi-produits
- Icônes sur les factures RP
- Catalogue ajouté automatiquement avec 100 unités par produit
- Cocktails, mojitos et cocktails sans alcool inclus
- Les nouveaux produits inconnus utilisent une icône générique
- Le remplissage à 100 est effectué une seule fois grâce au marqueur `product_catalog_v52`
