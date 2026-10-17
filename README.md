# Observability API

FastAPI service with a live Prometheus request counter, uptime endpoint, and structured JSON request logs.

## Local run

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
EMAIL_ADDRESS="your-exam-login-email@example.com" python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

## Render deployment

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Set `EMAIL_ADDRESS` to the email used to log into the exam.

Submit the service base URL (do not append an endpoint path).

Endpoints:
- `GET /work?n=K`
- `GET /metrics`
- `GET /healthz`
- `GET /logs/tail?limit=N`

Every HTTP request increments the `http_requests_total` Prometheus counter and produces a structured JSON log entry in the in-memory tail.
