# Dossier `223p`

Ce dossier contient des fichiers et sous-dossiers nécessaires au fonctionnement du projet, mais **ils ne devraient normalement pas être inclus directement dans ce dépôt**. Idéalement, ces fichiers devraient être importés ou récupérés depuis le dépôt officiel `223p`. Cependant, pour des raisons de praticité et afin de faciliter le développement et les tests, ils sont temporairement inclus ici.

## Détail des sous-dossiers et fichiers

- `bin/` : Contient les libraries BOB et SCRATCH (+ ttl_tools) devant être importés pour les agents 223p
- `ref/` : Dossier de référence contenant des standards et du code de référence, notamment :
    - `223standard/` : Référentiel des standards 223p (path requis dans la env var S223_FOLDER lors de la generation du HTML).
    - `code/` : Exemples de code python utilisant les libs BOB et SCRATCH pour modéliser des systèmes, à utiliser comme référence pour la génération de code.
- `run_validation.py` : Script Python permettant de valider ou de traiter les données du dossier `223p`.

## Avertissement

> **Attention :** Ces fichiers et dossiers sont inclus ici uniquement à titre temporaire. À terme, il est recommandé de les gérer via le dépôt officiel `223p` pour garantir la cohérence et la maintenance du projet.

