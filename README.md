# sys_ges_doc_backend

> Backend de gestion documentaire intelligent basé sur **FastAPI** et une approche **RAG (Retrieval-Augmented Generation)**.  
> Le projet permet de charger, organiser, exploiter et interroger des documents à travers une API Python structurée.

---

## Présentation

`sys_ges_doc_backend` est un backend conçu pour centraliser la gestion des documents et faciliter la recherche d'information dans un ensemble de fichiers grâce à un pipeline RAG complet intégrant vectorisation, stockage sémantique et génération augmentée par un modèle de langage.

---

## Fonctionnalités principales

- 📄 Gestion des documents (upload, liste, visualisation, suppression)
- ⚙️ Chargement et traitement des fichiers (extraction texte, chunking)
- 🌐 Structure API organisée en routes FastAPI
- 🤖 Logique RAG complète (embedding, recherche vectorielle, génération LLM)
- 🧩 Séparation claire des modèles et dépendances
- 🔌 Intégration possible avec une couche de service externe (TypeScript)
- 🔍 Indexation et recherche sémantique via LanceDB

---

## Technologies utilisées

| Technologie | Rôle |
|---|---|
| **Python** | Langage principal |
| **FastAPI** | Framework API REST |
| **Uvicorn** | Serveur ASGI |
| **LanceDB** | Base de données vectorielle |
| **RAG** | Pipeline de génération augmentée par récupération |
| **Docker** | Conteneurisation |
| **Kubernetes** | Orchestration et déploiement |
| **TypeScript** | Service associé dans `api/` |

---

## Structure du projet

```bash
sys_ges_doc_backend/
│
├── api/                        # Module principal de l'API
│   ├── __init__.py
│   ├── main.py                 # Point d'entrée de l'API
│   ├── dependencies.py         # Dépendances communes
│   ├── models.py               # Modèles de données Pydantic
│   ├── routes/                 # Routes de l'application
│   ├── documents/              # Documents accessibles via l'API
│   └── rag.service.ts          # Service TypeScript associé
│
├── documents/                  # Stockage des documents uploadés
├── data/                       # Données brutes ou intermédiaires
├── lance_db/                   # Base vectorielle LanceDB (instance 1)
├── lancedb/                    # Base vectorielle LanceDB (instance 2)
├── scripts/                    # Scripts utilitaires et maintenance
├── k8s/                        # Manifests Kubernetes
│
├── config.py                   # Configuration globale du projet
├── loader.py                   # Chargement et parsing des documents
├── embeddings.py               # Génération des vecteurs d'embedding
├── vectorstore.py              # Stockage et récupération vectorielle
├── llm.py                      # Interface avec le modèle de langage
├── rag.py                      # Orchestration du pipeline RAG
├── rag_system.py               # Logique avancée RAG (prompt, contexte)
├── viewer.py                   # Consultation et affichage des contenus
├── DbReaderApp.py              # Application de lecture de la base
├── LanceDbReader.py            # Lecteur spécialisé LanceDB
├── main.py                     # Point d'entrée alternatif
│
├── Dockerfile                  # Image Docker du projet
├── docker-compose.yml          # Composition multi-conteneurs
├── requirements-docker.txt     # Dépendances pour Docker
├── Requirements.txt            # Dépendances Python
└── Test_installation.py        # Script de vérification de l'installation
```

---

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/SahbiMethnani/sys_ges_doc_backend.git
cd sys_ges_doc_backend
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv
```

### 3. Activer l'environnement

**Sous Windows :**
```bash
venv\Scripts\activate
```

**Sous Linux / macOS :**
```bash
source venv/bin/activate
```

### 4. Installer les dépendances

```bash
pip install -r Requirements.txt
```

---

## Exécution

```bash
python -m api.main
```

---

## Modules principaux

### `api/main.py`
Point d'entrée principal de l'API. Initialise l'application FastAPI et enregistre les routeurs.

### `api/routes/`
Contient l'ensemble des routes de l'application organisées par domaine fonctionnel (documents, recherche, Q&A).

### `api/models.py`
Définit les modèles de données Pydantic utilisés pour la validation des requêtes et réponses.

### `api/dependencies.py`
Regroupe les dépendances communes injectées dans les routes via le système de DI de FastAPI.

### `loader.py`
Gère le chargement et le parsing des documents (PDF, DOCX). Extrait le texte brut et le prépare pour le pipeline RAG.

### `embeddings.py`
Transforme les chunks de texte en vecteurs numériques à l'aide d'un modèle d'embedding.

### `vectorstore.py`
Gère le stockage des vecteurs dans LanceDB et la récupération par similarité cosinus.

### `llm.py`
Encapsule la logique d'appel au modèle de langage (paramètres, tokens, température).

### `rag.py` et `rag_system.py`
Implémentent le pipeline RAG complet : vectorisation de la question, récupération du contexte, construction du prompt augmenté et génération de la réponse.

### `viewer.py`
Permet la consultation ou l'affichage des contenus documentaires.

### `DbReaderApp.py` et `LanceDbReader.py`
Outils d'inspection et de lecture de la base vectorielle LanceDB.

---

## Organisation des documents

Les documents utilisés par le système sont stockés dans les dossiers suivants :

| Dossier | Rôle |
|---|---|
| `documents/` | Documents uploadés par l'utilisateur |
| `api/documents/` | Documents accessibles via l'API |
| `data/` | Données brutes ou intermédiaires |

---

## Conteneurisation

### Build Docker

```bash
docker build -t sys_ges_doc_backend .
```

### Lancement avec Docker Compose

```bash
docker-compose up --build
```

> Les dépendances spécifiques à l'environnement Docker sont définies dans `requirements-docker.txt`.

---

## Déploiement Kubernetes

Le dossier `k8s/` contient les manifests nécessaires au déploiement du projet sur un cluster Kubernetes (pods, services, ingress).

```bash
kubectl apply -f k8s/
```

---

## Vérification de l'installation

```bash
python Test_installation.py
```

---

## Cas d'utilisation

Ce projet peut être utilisé pour :

- 📁 La **gestion documentaire** centralisée
- 🔎 L'**indexation sémantique** de fichiers
- 💬 La **recherche intelligente** dans des corpus documentaires
- 🤖 Un **assistant documentaire** conversationnel basé sur le RAG

---

## Auteur

**Sahbi Methnani**  
🔗 [github.com/SahbiMethnani/sys_ges_doc_backend](https://github.com/SahbiMethnani/sys_ges_doc_backend)
