# DevOps Monitor

FastAPI backend + Streamlit dashboard pour suivre les métriques système
et une liste de serveurs.

## Install

```bash
cd devops-monitor
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Run

Backend :

```bash
uvicorn api.main:app --reload --port 8000
```

Dashboard (autre terminal) :

```bash
streamlit run dashboard/app.py
```

La clé API par défaut est `demo-key`. Pour la changer :
`set API_KEY=ma-cle` (Windows) avant de lancer uvicorn.

## Endpoints

- `GET /health`
- `GET /metrics`
- `WS /ws/metrics`
- `POST /servers` (clé API)
- `GET /servers` (filtre `?status=UP`)
- `GET /servers/{id}`
- `DELETE /servers/{id}` (clé API)
- `POST /servers/{id}/check`

## Tests

```bash
pytest tests/ -v
pytest --cov=api
```
