# DevOps Monitoring Dashboard

Système de monitoring temps réel en Python : une API FastAPI qui expose les
métriques système (CPU, mémoire, disque) et gère une liste de serveurs, et un
dashboard Streamlit qui les affiche en direct. Containerisé avec Docker et
déployé sur Azure Container Apps via GitHub Actions.

## Architecture

- **api** (FastAPI, port 8000) — métriques, WebSocket, CRUD serveurs, health checks
- **dashboard** (Streamlit, port 8501) — onglet Métriques (KPIs + graphique live) et onglet Serveurs (tableau + formulaire)

Le dashboard joint l'API via la variable `API_BASE`.

## Prérequis

- Python 3.11
- Docker + Docker Compose
- Make

## Lancement local

```bash
cp .env.example .env   # remplir API_KEY
make up                # build + démarre la stack
make test              # lance les tests
make logs              # suit les logs
make down              # arrête la stack
```

- API : http://localhost:8000/docs
- Dashboard : http://localhost:8501

## Variables d'environnement

| Variable | Description |
|----------|-------------|
| `API_KEY` | Clé attendue dans le header `X-API-Key` pour les routes d'écriture |
| `API_BASE` | URL de l'API vue par le dashboard (en Docker : `http://api:8000`) |

## Endpoints

| Méthode | Chemin | Auth | Description |
|---------|--------|------|-------------|
| GET | `/health` | public | `{"status": "ok"}` |
| GET | `/metrics` | public | Snapshot CPU / mémoire / disque |
| WS | `/ws/metrics` | public | Stream JSON toutes les secondes |
| POST | `/servers` | API key | Enregistre un serveur |
| GET | `/servers` | public | Liste les serveurs (filtre `?status=UP`) |
| GET | `/servers/{id}` | public | Un serveur ou 404 |
| DELETE | `/servers/{id}` | API key | Supprime un serveur ou 404 |
| POST | `/servers/{id}/check` | public | Déclenche un health check |

## Tests

```bash
make test    # pytest tests/ -v --cov=api --cov-fail-under=75
make lint    # flake8
```

## Déploiement

Hébergé sur **Azure Container Apps** (région Sweden Central), images stockées
sur **Azure Container Registry**.

CI/CD via [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml) — sur push
`main` :

1. **test** — lint flake8 + pytest avec couverture ≥ 75 %
2. **build** — build des deux images Docker et push vers ACR (tag = SHA du commit)
3. **deploy** — `az containerapp update` sur les deux Container Apps

L'authentification GitHub → Azure se fait par **OIDC** (identité managée +
federated credential), sans secret de mot de passe stocké.

## URLs live

- API : https://devops-monitor-api.whitebay-cb01eb12.swedencentral.azurecontainerapps.io/docs
- Dashboard : https://devops-monitor-dashboard.whitebay-cb01eb12.swedencentral.azurecontainerapps.io
