#!/usr/bin/env bash
# Lance l'API RAG : Docker Compose par défaut, ou Kubernetes + port-forward.
#
# Minikube : eval "$(minikube docker-env)" puis relancer avec --k8s
# (pour que l'image rag-api:local soit visible du cluster).
#
# Usage :
#   chmod +x scripts/run-server.sh
#   ./scripts/run-server.sh
#   ./scripts/run-server.sh --k8s

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ "${1:-}" == "--k8s" ]] || [[ "${1:-}" == "-k" ]]; then
  echo ">>> Construction de l'image rag-api:local ..."
  docker build -t rag-api:local "$ROOT"

  echo ">>> Application des manifests Kubernetes (k8s/) ..."
  kubectl apply -f "$ROOT/k8s"

  echo ">>> Attente du déploiement rag-api ..."
  kubectl rollout status deployment/rag-api --timeout=600s

  echo ">>> Port-forward : http://localhost:8000 (CTRL+C pour arrêter)"
  kubectl port-forward service/rag-api 8000:8000
else
  echo ">>> Démarrage avec Docker Compose (http://localhost:8000) ..."
  docker compose -f "$ROOT/docker-compose.yml" up --build
fi
