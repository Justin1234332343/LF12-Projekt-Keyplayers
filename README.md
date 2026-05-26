# LF12-Projekt-Keyplayers

Schulungs-Organisations-Tool zur Verwaltung von Seminaren, Teilnehmern, Angeboten und Rechnungen.

## Architektur

| Container | Technologie | Port |
|-----------|-------------|------|
| oracle-23ai-free | Oracle Database 23ai Free | 1521 |
| ords | Oracle REST Data Services | 8181 |
| backend | Python FastAPI | 8000 |
| ollama | Ollama (Mistral LLM) | 11434 |
| frontend | Nginx (Vanilla JS SPA) | 8080 |

## Starten

```bash
docker compose up --build
```

Beim ersten Start lädt Ollama das Mistral-Modell (~4 GB) automatisch herunter. Das dauert einige Minuten.

| URL | Beschreibung |
|-----|--------------|
| http://localhost:8080 | Frontend |
| http://localhost:8000/docs | Backend API (Swagger) |
| http://localhost:8181/ords/projekt_lf12/ | ORDS REST API |

## Troubleshooting

### ORDS-Endpunkte antworten mit 404

Die Custom-Endpunkte unter `/ords/projekt_lf12/api/v1/...` werden manchmal beim ersten Start nicht registriert. Skript manuell ausführen:

```bash
docker exec oracle-23ai-free sqlplus \
  "sys/MeinSicheresPasswort123@localhost:1521/freepdb1 as sysdba" \
  "@/opt/oracle/scripts/startup/40-ords_modules.sql"
```

Danach ORDS neu starten:

```bash
docker compose restart ords
```

---

## Entwicklung

### Backend (Python)

```bash
cd backend_python
pip install -r requirements.txt
pytest tests/
```

### Umgebungsvariablen

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `ORDS_BASE_URL` | `http://ords:8080/ords/projekt_lf12` | ORDS-Basis-URL |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama-URL |
| `OLLAMA_MODEL` | `mistral` | Zu verwendendes LLM |
| `ORACLE_PWD` | — | Oracle DB Passwort |
